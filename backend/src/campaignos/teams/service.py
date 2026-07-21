"""Tenant-scoped persistence service for campaign team workspaces."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from campaignos.data.audit import (
    AuditScopeUnavailable,
    append_audit_event,
    canonical_hash,
    lock_tenant_audit_stream,
)
from campaignos.data.database import Database
from campaignos.data.idempotency import lock_idempotency_key
from campaignos.data.models import (
    Campaign,
    CandidateWorkspace,
    IdempotencyRecord,
    OutboxEvent,
    TeamWorkspace,
    Workspace,
)
from campaignos.teams.contracts import (
    TeamAccessRecommendation,
    TeamWorkspaceAssessmentInput,
    TeamWorkspaceContractError,
    TeamWorkspaceCreate,
    TeamWorkspaceCreateEvidence,
    TeamWorkspaceProjection,
    TeamWorkspaceReadEvidence,
    TeamWorkspaceUpdate,
    TeamWorkspaceUpdateEvidence,
    assess_team_workspace,
)

CREATE_OPERATION = "team_workspace.create"
UPDATE_OPERATION = "team_workspace.update"


class TeamWorkspaceNotFound(LookupError):
    """The campaign or team workspace is unavailable in the selected tenant."""


class TeamWorkspacePrerequisiteConflict(RuntimeError):
    """The candidate workspace prerequisite is missing."""


class TeamWorkspaceConflict(RuntimeError):
    """A team workspace already exists for the campaign."""


class TeamWorkspaceVersionConflict(RuntimeError):
    """The team workspace changed after the caller's observed version."""


class TeamWorkspaceIdempotencyConflict(RuntimeError):
    """An idempotency key was reused with different team intent or authority."""


class TeamWorkspaceEvidenceConflict(RuntimeError):
    """The proposed team document violates an organizational invariant."""


class TeamWorkspaceUnavailable(RuntimeError):
    """The team workspace boundary cannot safely complete."""


class TeamWorkspaceService(Protocol):
    def create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: TeamWorkspaceCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TeamWorkspaceCreateEvidence: ...

    def get(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> TeamWorkspaceReadEvidence: ...

    def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: TeamWorkspaceUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TeamWorkspaceUpdateEvidence: ...


class UnavailableTeamWorkspaceService:
    def create(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> TeamWorkspaceCreateEvidence:
        del tenant_id, campaign_id, kwargs
        raise TeamWorkspaceUnavailable("Team workspace is unavailable")

    def get(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> TeamWorkspaceReadEvidence:
        del tenant_id, campaign_id, kwargs
        raise TeamWorkspaceUnavailable("Team workspace is unavailable")

    def update(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> TeamWorkspaceUpdateEvidence:
        del tenant_id, campaign_id, kwargs
        raise TeamWorkspaceUnavailable("Team workspace is unavailable")


def _as_utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _campaign(session: Session, tenant_id: UUID, campaign_id: UUID) -> Campaign:
    campaign = session.scalar(
        select(Campaign).where(
            Campaign.tenant_id == tenant_id,
            Campaign.id == campaign_id,
            Campaign.status.in_(("DRAFT", "ACTIVE")),
        )
    )
    if campaign is None:
        raise TeamWorkspaceNotFound("Team workspace was not found")
    return campaign


def _require_candidate(session: Session, tenant_id: UUID, campaign_id: UUID) -> None:
    candidate_id = session.scalar(
        select(CandidateWorkspace.id).where(
            CandidateWorkspace.tenant_id == tenant_id,
            CandidateWorkspace.campaign_id == campaign_id,
        )
    )
    if candidate_id is None:
        raise TeamWorkspacePrerequisiteConflict("Candidate workspace is required")


def _validate_access_workspace_ownership(
    session: Session,
    *,
    tenant_id: UUID,
    campaign_id: UUID,
    recommendations: object,
    persisted: bool = False,
) -> None:
    if recommendations is None:
        return
    if not isinstance(recommendations, Sequence) or isinstance(
        recommendations, (str, bytes, bytearray)
    ):
        if persisted:
            raise TeamWorkspaceUnavailable("Team workspace is unavailable")
        raise TeamWorkspaceEvidenceConflict("Team access recommendations are invalid")
    try:
        parsed = tuple(TeamAccessRecommendation.model_validate(item) for item in recommendations)
    except ValidationError as exc:
        if persisted:
            raise TeamWorkspaceUnavailable("Team workspace is unavailable") from exc
        raise TeamWorkspaceEvidenceConflict("Team access recommendations are invalid") from exc
    for recommendation in parsed:
        if recommendation.workspace_id is None:
            continue
        workspace_id = session.scalar(
            select(Workspace.id).where(
                Workspace.tenant_id == tenant_id,
                Workspace.campaign_id == campaign_id,
                Workspace.id == recommendation.workspace_id,
                Workspace.status == "ACTIVE",
            )
        )
        if workspace_id is None:
            if persisted:
                raise TeamWorkspaceUnavailable("Team workspace is unavailable")
            raise TeamWorkspaceEvidenceConflict(
                "Access recommendation workspace is outside the campaign scope"
            )


def _projection(row: TeamWorkspace, campaign: Campaign) -> TeamWorkspaceProjection:
    return assess_team_workspace(
        TeamWorkspaceAssessmentInput.model_validate(
            {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "campaign_id": row.campaign_id,
                "campaign_version": campaign.version,
                "campaign_status": campaign.status,
                "campaign_name": campaign.name,
                "organization_template": row.organization_template,
                "roles": row.roles,
                "work_items": row.work_items,
                "training_requirements": row.training_requirements,
                "access_recommendations": row.access_recommendations,
                "version": row.version,
                "created_at": _as_utc(row.created_at),
                "updated_at": _as_utc(row.updated_at),
            }
        )
    )


def _replay[EvidenceT: BaseModel](
    session: Session,
    *,
    tenant_id: UUID,
    operation: str,
    idempotency_key: str,
    digest: str,
    evidence_type: type[EvidenceT],
) -> EvidenceT | None:
    existing = session.scalar(
        select(IdempotencyRecord)
        .where(
            IdempotencyRecord.tenant_id == tenant_id,
            IdempotencyRecord.operation == operation,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
        .with_for_update()
    )
    if existing is None:
        return None
    if existing.request_digest != digest:
        raise TeamWorkspaceIdempotencyConflict(
            "Idempotency key conflicts with a previous team workspace request"
        )
    return evidence_type.model_validate(existing.response_payload)


def _store_replay(
    session: Session,
    *,
    tenant_id: UUID,
    principal_id: UUID,
    operation: str,
    idempotency_key: str,
    request_digest: str,
    response: BaseModel,
    created_at: datetime,
) -> None:
    session.add(
        IdempotencyRecord(
            tenant_id=tenant_id,
            principal_id=principal_id,
            operation=operation,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            response_payload=response.model_dump(mode="json"),
            created_at=created_at,
        )
    )


@dataclass(slots=True)
class SqlAlchemyTeamWorkspaceService:
    database: Database

    def create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: TeamWorkspaceCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TeamWorkspaceCreateEvidence:
        try:
            return self._create(
                tenant_id,
                campaign_id,
                request=request,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        except (
            TeamWorkspaceConflict,
            TeamWorkspaceIdempotencyConflict,
            TeamWorkspaceNotFound,
            TeamWorkspacePrerequisiteConflict,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            TeamWorkspaceContractError,
            ValidationError,
            ValueError,
        ) as exc:
            raise TeamWorkspaceUnavailable("Team workspace is unavailable") from exc

    def _create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: TeamWorkspaceCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TeamWorkspaceCreateEvidence:
        digest = canonical_hash(
            {
                "tenant_id": str(tenant_id),
                "campaign_id": str(campaign_id),
                "request": request.model_dump(mode="json"),
                "principal_id": str(principal_id),
                "authorization_grant_id": str(authorization_grant_id),
                "approval_receipt_id": approval_receipt_id,
                "authorization_purpose": authorization_purpose,
            }
        )
        with self.database.tenant_transaction(tenant_id) as session:
            lock_idempotency_key(
                session,
                tenant_id=tenant_id,
                operation=CREATE_OPERATION,
                idempotency_key=idempotency_key,
            )
            replay = _replay(
                session,
                tenant_id=tenant_id,
                operation=CREATE_OPERATION,
                idempotency_key=idempotency_key,
                digest=digest,
                evidence_type=TeamWorkspaceCreateEvidence,
            )
            if replay is not None:
                return replay
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            operation_at = audit_lock.acquired_at
            campaign = _campaign(session, tenant_id, campaign_id)
            _require_candidate(session, tenant_id, campaign_id)
            existing = session.scalar(
                select(TeamWorkspace.id)
                .where(
                    TeamWorkspace.tenant_id == tenant_id,
                    TeamWorkspace.campaign_id == campaign_id,
                )
                .with_for_update()
            )
            if existing is not None:
                raise TeamWorkspaceConflict("Team workspace already exists")
            row = TeamWorkspace(
                id=uuid4(),
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                organization_template=request.organization_template,
                roles=None,
                work_items=None,
                training_requirements=None,
                access_recommendations=None,
                version=1,
                created_at=operation_at,
                updated_at=operation_at,
            )
            session.add(row)
            session.flush()
            projection = _projection(row, campaign)
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="team_workspace.created",
                resource_type="team_workspace",
                resource_id=str(row.id),
                payload={
                    "workspace_version": row.version,
                    "workspace_status": projection.status,
                    "organization_template": row.organization_template,
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "authority_effect": "NONE",
                    "external_effects": "NONE",
                },
            )
            outbox_id = uuid4()
            session.add(
                OutboxEvent(
                    id=outbox_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    topic="team_workspace.created",
                    payload={
                        "team_workspace_id": str(row.id),
                        "audit_event_id": str(audit.event_id),
                        "version": row.version,
                        "authority_effect": "NONE",
                        "external_effects": "NONE",
                    },
                    status="PENDING",
                    attempts=0,
                    available_at=operation_at,
                    created_at=operation_at,
                )
            )
            evidence = TeamWorkspaceCreateEvidence(
                workspace=projection,
                audit_event_id=audit.event_id,
                outbox_event_id=outbox_id,
            )
            _store_replay(
                session,
                tenant_id=tenant_id,
                principal_id=principal_id,
                operation=CREATE_OPERATION,
                idempotency_key=idempotency_key,
                request_digest=digest,
                response=evidence,
                created_at=operation_at,
            )
            session.flush()
        return evidence

    def get(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> TeamWorkspaceReadEvidence:
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                campaign = _campaign(session, tenant_id, campaign_id)
                row = session.scalar(
                    select(TeamWorkspace).where(
                        TeamWorkspace.tenant_id == tenant_id,
                        TeamWorkspace.campaign_id == campaign_id,
                    )
                )
                if row is None:
                    raise TeamWorkspaceNotFound("Team workspace was not found")
                _validate_access_workspace_ownership(
                    session,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    recommendations=row.access_recommendations,
                    persisted=True,
                )
                projection = _projection(row, campaign)
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="team_workspace.read",
                    resource_type="team_workspace",
                    resource_id=str(row.id),
                    payload={
                        "workspace_version": row.version,
                        "workspace_status": projection.status,
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "authority_effect": "NONE",
                        "external_effects": "NONE",
                    },
                )
                evidence = TeamWorkspaceReadEvidence(
                    workspace=projection,
                    audit_event_id=audit.event_id,
                )
                session.flush()
            return evidence
        except TeamWorkspaceNotFound:
            raise
        except (
            AuditScopeUnavailable,
            SQLAlchemyError,
            TeamWorkspaceContractError,
            ValidationError,
            ValueError,
        ) as exc:
            raise TeamWorkspaceUnavailable("Team workspace is unavailable") from exc

    def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: TeamWorkspaceUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TeamWorkspaceUpdateEvidence:
        try:
            return self._update(
                tenant_id,
                campaign_id,
                expected_version=expected_version,
                changes=changes,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        except (
            TeamWorkspaceEvidenceConflict,
            TeamWorkspaceIdempotencyConflict,
            TeamWorkspaceNotFound,
            TeamWorkspaceVersionConflict,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise TeamWorkspaceUnavailable("Team workspace is unavailable") from exc

    def _update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: TeamWorkspaceUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TeamWorkspaceUpdateEvidence:
        digest = canonical_hash(
            {
                "tenant_id": str(tenant_id),
                "campaign_id": str(campaign_id),
                "expected_version": expected_version,
                "changes": changes.model_dump(mode="json", exclude_unset=True),
                "principal_id": str(principal_id),
                "authorization_grant_id": str(authorization_grant_id),
                "approval_receipt_id": approval_receipt_id,
                "authorization_purpose": authorization_purpose,
            }
        )
        with self.database.tenant_transaction(tenant_id) as session:
            lock_idempotency_key(
                session,
                tenant_id=tenant_id,
                operation=UPDATE_OPERATION,
                idempotency_key=idempotency_key,
            )
            replay = _replay(
                session,
                tenant_id=tenant_id,
                operation=UPDATE_OPERATION,
                idempotency_key=idempotency_key,
                digest=digest,
                evidence_type=TeamWorkspaceUpdateEvidence,
            )
            if replay is not None:
                return replay
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            operation_at = audit_lock.acquired_at
            campaign = _campaign(session, tenant_id, campaign_id)
            row = session.scalar(
                select(TeamWorkspace)
                .where(
                    TeamWorkspace.tenant_id == tenant_id,
                    TeamWorkspace.campaign_id == campaign_id,
                )
                .with_for_update()
            )
            if row is None:
                raise TeamWorkspaceNotFound("Team workspace was not found")
            if row.version != expected_version:
                raise TeamWorkspaceVersionConflict("Team workspace version is stale")
            changed_fields = sorted(changes.model_fields_set)
            serialized = changes.model_dump(mode="json", exclude_unset=True)
            if "access_recommendations" in changes.model_fields_set:
                _validate_access_workspace_ownership(
                    session,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    recommendations=serialized.get("access_recommendations"),
                )
            for field_name in changed_fields:
                setattr(row, field_name, serialized[field_name])
            row.version += 1
            row.updated_at = operation_at
            session.flush()
            try:
                projection = _projection(row, campaign)
            except TeamWorkspaceContractError as exc:
                raise TeamWorkspaceEvidenceConflict(
                    "Team document conflicts with organizational invariants"
                ) from exc
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="team_workspace.updated",
                resource_type="team_workspace",
                resource_id=str(row.id),
                payload={
                    "workspace_version": row.version,
                    "workspace_status": projection.status,
                    "changed_fields": changed_fields,
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "authority_effect": "NONE",
                    "external_effects": "NONE",
                },
            )
            outbox_id = uuid4()
            session.add(
                OutboxEvent(
                    id=outbox_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    topic="team_workspace.updated",
                    payload={
                        "team_workspace_id": str(row.id),
                        "audit_event_id": str(audit.event_id),
                        "version": row.version,
                        "status": projection.status,
                        "authority_effect": "NONE",
                        "external_effects": "NONE",
                    },
                    status="PENDING",
                    attempts=0,
                    available_at=operation_at,
                    created_at=operation_at,
                )
            )
            evidence = TeamWorkspaceUpdateEvidence(
                workspace=projection,
                audit_event_id=audit.event_id,
                outbox_event_id=outbox_id,
            )
            _store_replay(
                session,
                tenant_id=tenant_id,
                principal_id=principal_id,
                operation=UPDATE_OPERATION,
                idempotency_key=idempotency_key,
                request_digest=digest,
                response=evidence,
                created_at=operation_at,
            )
            session.flush()
        return evidence
