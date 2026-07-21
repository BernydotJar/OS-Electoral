"""Tenant-scoped persistence service for evidence-governed candidate workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from campaignos.candidates.contracts import (
    CandidateSectionApproval as CandidateSectionApprovalProjection,
)
from campaignos.candidates.contracts import (
    CandidateSectionApprovalRequest,
    CandidateWorkspaceApprovalEvidence,
    CandidateWorkspaceAssessmentInput,
    CandidateWorkspaceContractError,
    CandidateWorkspaceCreate,
    CandidateWorkspaceCreateEvidence,
    CandidateWorkspaceProjection,
    CandidateWorkspaceReadEvidence,
    CandidateWorkspaceUpdate,
    CandidateWorkspaceUpdateEvidence,
    assess_candidate_workspace,
)
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
    CandidateSectionApproval,
    CandidateWorkspace,
    GuidedIntake,
    IdempotencyRecord,
    OutboxEvent,
    Workspace,
)
from campaignos.onboarding.contracts import (
    GuidedIntakeAssessmentInput,
    assess_guided_intake,
)

CREATE_OPERATION = "candidate_workspace.create"
UPDATE_OPERATION = "candidate_workspace.update"
APPROVE_OPERATION = "candidate_workspace.approve_section"


class CandidateWorkspaceNotFound(LookupError):
    """The campaign or candidate workspace is unavailable in the selected tenant."""


class CandidateWorkspacePrerequisiteConflict(RuntimeError):
    """Guided intake is not ready for a candidate evidence workspace."""


class CandidateWorkspaceConflict(RuntimeError):
    """A candidate workspace already exists for the campaign."""


class CandidateWorkspaceVersionConflict(RuntimeError):
    """The candidate workspace changed after the caller's observed version."""


class CandidateWorkspaceIdempotencyConflict(RuntimeError):
    """An idempotency key was reused with different intent or authority."""


class CandidateWorkspaceEvidenceConflict(RuntimeError):
    """The proposed candidate evidence document violates a domain invariant."""


class CandidateWorkspaceApprovalConflict(RuntimeError):
    """The requested section cannot be approved for the current workspace version."""


class CandidateWorkspaceUnavailable(RuntimeError):
    """The candidate workspace boundary cannot safely complete."""


class CandidateWorkspaceService(Protocol):
    def create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: CandidateWorkspaceCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CandidateWorkspaceCreateEvidence: ...

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
    ) -> CandidateWorkspaceReadEvidence: ...

    def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: CandidateWorkspaceUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CandidateWorkspaceUpdateEvidence: ...

    def approve_section(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        request: CandidateSectionApprovalRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CandidateWorkspaceApprovalEvidence: ...


class UnavailableCandidateWorkspaceService:
    def create(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> CandidateWorkspaceCreateEvidence:
        del tenant_id, campaign_id, kwargs
        raise CandidateWorkspaceUnavailable("Candidate workspace is unavailable")

    def get(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> CandidateWorkspaceReadEvidence:
        del tenant_id, campaign_id, kwargs
        raise CandidateWorkspaceUnavailable("Candidate workspace is unavailable")

    def update(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> CandidateWorkspaceUpdateEvidence:
        del tenant_id, campaign_id, kwargs
        raise CandidateWorkspaceUnavailable("Candidate workspace is unavailable")

    def approve_section(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> CandidateWorkspaceApprovalEvidence:
        del tenant_id, campaign_id, kwargs
        raise CandidateWorkspaceUnavailable("Candidate workspace is unavailable")


def _as_utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _campaign_context(
    session: Session,
    *,
    tenant_id: UUID,
    campaign_id: UUID,
) -> tuple[Campaign, int]:
    campaign = session.scalar(
        select(Campaign).where(
            Campaign.tenant_id == tenant_id,
            Campaign.id == campaign_id,
            Campaign.status.in_(("DRAFT", "ACTIVE")),
        )
    )
    if campaign is None:
        raise CandidateWorkspaceNotFound("Candidate workspace was not found")
    active_workspace_count = int(
        session.scalar(
            select(func.count())
            .select_from(Workspace)
            .where(
                Workspace.tenant_id == tenant_id,
                Workspace.campaign_id == campaign_id,
                Workspace.status == "ACTIVE",
            )
        )
        or 0
    )
    return campaign, active_workspace_count


def _require_ready_guided_intake(
    session: Session,
    *,
    tenant_id: UUID,
    campaign: Campaign,
    active_workspace_count: int,
) -> GuidedIntake:
    intake = session.scalar(
        select(GuidedIntake).where(
            GuidedIntake.tenant_id == tenant_id,
            GuidedIntake.campaign_id == campaign.id,
        )
    )
    if intake is None:
        raise CandidateWorkspacePrerequisiteConflict("Guided intake is not ready")
    projection = assess_guided_intake(
        GuidedIntakeAssessmentInput.model_validate(
            {
                "id": intake.id,
                "tenant_id": intake.tenant_id,
                "campaign_id": intake.campaign_id,
                "campaign_version": campaign.version,
                "campaign_status": campaign.status,
                "campaign_name": campaign.name,
                "jurisdiction": campaign.jurisdiction,
                "stage": campaign.stage,
                "active_workspace_count": active_workspace_count,
                "office": intake.office,
                "candidate_project": intake.candidate_project,
                "current_team": intake.current_team,
                "current_assets": intake.current_assets,
                "budget_status": intake.budget_status,
                "known_unknowns": intake.known_unknowns,
                "evidence_requirements": intake.evidence_requirements,
                "version": intake.version,
                "created_at": _as_utc(intake.created_at),
                "updated_at": _as_utc(intake.updated_at),
            }
        )
    )
    if projection.status != "READY_FOR_RESEARCH":
        raise CandidateWorkspacePrerequisiteConflict("Guided intake is not ready")
    return intake


def _approval_projection(row: CandidateSectionApproval) -> CandidateSectionApprovalProjection:
    return CandidateSectionApprovalProjection.model_validate(
        {
            "id": row.id,
            "section": row.section,
            "approved_version": row.approved_version,
            "principal_id": row.principal_id,
            "authorization_grant_id": row.authorization_grant_id,
            "approval_receipt_id": row.approval_receipt_id,
            "reason": row.reason,
            "approved_at": _as_utc(row.approved_at),
        }
    )


def _projection(
    session: Session,
    row: CandidateWorkspace,
    campaign: Campaign,
) -> CandidateWorkspaceProjection:
    approvals = tuple(
        _approval_projection(approval)
        for approval in session.scalars(
            select(CandidateSectionApproval)
            .where(
                CandidateSectionApproval.tenant_id == row.tenant_id,
                CandidateSectionApproval.campaign_id == row.campaign_id,
                CandidateSectionApproval.candidate_workspace_id == row.id,
            )
            .order_by(
                CandidateSectionApproval.approved_version,
                CandidateSectionApproval.section,
                CandidateSectionApproval.id,
            )
        )
    )
    return assess_candidate_workspace(
        CandidateWorkspaceAssessmentInput.model_validate(
            {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "campaign_id": row.campaign_id,
                "campaign_version": campaign.version,
                "campaign_status": campaign.status,
                "campaign_name": campaign.name,
                "jurisdiction": campaign.jurisdiction,
                "candidate_id": row.candidate_id,
                "display_name": row.display_name,
                "evidence": row.evidence,
                "identity": row.identity,
                "biography": row.biography,
                "purpose": row.purpose,
                "values": row.values,
                "attributes": row.attributes,
                "contradictions": row.contradictions,
                "development_goals": row.development_goals,
                "reputation_risks": row.reputation_risks,
                "approvals": approvals,
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
        raise CandidateWorkspaceIdempotencyConflict(
            "Idempotency key conflicts with a previous candidate workspace request"
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
class SqlAlchemyCandidateWorkspaceService:
    database: Database

    def create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: CandidateWorkspaceCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CandidateWorkspaceCreateEvidence:
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
            CandidateWorkspaceConflict,
            CandidateWorkspaceIdempotencyConflict,
            CandidateWorkspaceNotFound,
            CandidateWorkspacePrerequisiteConflict,
        ):
            raise
        except (
            AuditScopeUnavailable,
            CandidateWorkspaceContractError,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise CandidateWorkspaceUnavailable("Candidate workspace is unavailable") from exc

    def _create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: CandidateWorkspaceCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CandidateWorkspaceCreateEvidence:
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
                evidence_type=CandidateWorkspaceCreateEvidence,
            )
            if replay is not None:
                return replay

            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            operation_at = audit_lock.acquired_at
            campaign, active_workspace_count = _campaign_context(
                session,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
            )
            _require_ready_guided_intake(
                session,
                tenant_id=tenant_id,
                campaign=campaign,
                active_workspace_count=active_workspace_count,
            )
            existing = session.scalar(
                select(CandidateWorkspace.id)
                .where(
                    CandidateWorkspace.tenant_id == tenant_id,
                    CandidateWorkspace.campaign_id == campaign_id,
                )
                .with_for_update()
            )
            if existing is not None:
                raise CandidateWorkspaceConflict("Candidate workspace already exists")

            row = CandidateWorkspace(
                id=uuid4(),
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                candidate_id=uuid4(),
                display_name=request.display_name,
                evidence=[],
                identity=None,
                biography=None,
                purpose=None,
                values=None,
                attributes=None,
                contradictions=None,
                development_goals=None,
                reputation_risks=None,
                version=1,
                created_at=operation_at,
                updated_at=operation_at,
            )
            session.add(row)
            session.flush()
            projection = _projection(session, row, campaign)
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="candidate_workspace.created",
                resource_type="candidate_workspace",
                resource_id=str(row.id),
                payload={
                    "candidate_id": str(row.candidate_id),
                    "workspace_version": row.version,
                    "workspace_status": projection.status,
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "public_use_status": "BLOCKED",
                    "external_effects": "NONE",
                },
            )
            outbox_event_id = uuid4()
            session.add(
                OutboxEvent(
                    id=outbox_event_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    topic="candidate_workspace.created",
                    payload={
                        "candidate_workspace_id": str(row.id),
                        "candidate_id": str(row.candidate_id),
                        "audit_event_id": str(audit.event_id),
                        "version": row.version,
                        "public_use_status": "BLOCKED",
                        "external_effects": "NONE",
                    },
                    status="PENDING",
                    attempts=0,
                    available_at=operation_at,
                    created_at=operation_at,
                )
            )
            evidence = CandidateWorkspaceCreateEvidence(
                workspace=projection,
                audit_event_id=audit.event_id,
                outbox_event_id=outbox_event_id,
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
    ) -> CandidateWorkspaceReadEvidence:
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                campaign, _ = _campaign_context(
                    session,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                )
                row = session.scalar(
                    select(CandidateWorkspace).where(
                        CandidateWorkspace.tenant_id == tenant_id,
                        CandidateWorkspace.campaign_id == campaign_id,
                    )
                )
                if row is None:
                    raise CandidateWorkspaceNotFound("Candidate workspace was not found")
                projection = _projection(session, row, campaign)
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="candidate_workspace.read",
                    resource_type="candidate_workspace",
                    resource_id=str(row.id),
                    payload={
                        "workspace_version": row.version,
                        "workspace_status": projection.status,
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "public_use_status": "BLOCKED",
                        "external_effects": "NONE",
                    },
                )
                evidence = CandidateWorkspaceReadEvidence(
                    workspace=projection,
                    audit_event_id=audit.event_id,
                )
                session.flush()
            return evidence
        except CandidateWorkspaceNotFound:
            raise
        except (
            AuditScopeUnavailable,
            CandidateWorkspaceContractError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise CandidateWorkspaceUnavailable("Candidate workspace is unavailable") from exc

    def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: CandidateWorkspaceUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CandidateWorkspaceUpdateEvidence:
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
            CandidateWorkspaceEvidenceConflict,
            CandidateWorkspaceIdempotencyConflict,
            CandidateWorkspaceNotFound,
            CandidateWorkspaceVersionConflict,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise CandidateWorkspaceUnavailable("Candidate workspace is unavailable") from exc

    def _update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: CandidateWorkspaceUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CandidateWorkspaceUpdateEvidence:
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
                evidence_type=CandidateWorkspaceUpdateEvidence,
            )
            if replay is not None:
                return replay

            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            operation_at = audit_lock.acquired_at
            campaign, _ = _campaign_context(
                session,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
            )
            row = session.scalar(
                select(CandidateWorkspace)
                .where(
                    CandidateWorkspace.tenant_id == tenant_id,
                    CandidateWorkspace.campaign_id == campaign_id,
                )
                .with_for_update()
            )
            if row is None:
                raise CandidateWorkspaceNotFound("Candidate workspace was not found")
            if row.version != expected_version:
                raise CandidateWorkspaceVersionConflict("Candidate workspace version is stale")

            changed_fields = sorted(changes.model_fields_set)
            serialized = changes.model_dump(mode="json", exclude_unset=True)
            for field_name in changed_fields:
                setattr(row, field_name, serialized[field_name])
            row.version += 1
            row.updated_at = operation_at
            session.flush()
            try:
                projection = _projection(session, row, campaign)
            except CandidateWorkspaceContractError as exc:
                raise CandidateWorkspaceEvidenceConflict(
                    "Candidate evidence conflicts with workspace invariants"
                ) from exc

            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="candidate_workspace.updated",
                resource_type="candidate_workspace",
                resource_id=str(row.id),
                payload={
                    "workspace_version": row.version,
                    "workspace_status": projection.status,
                    "changed_fields": changed_fields,
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "public_use_status": "BLOCKED",
                    "external_effects": "NONE",
                },
            )
            outbox_event_id = uuid4()
            session.add(
                OutboxEvent(
                    id=outbox_event_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    topic="candidate_workspace.updated",
                    payload={
                        "candidate_workspace_id": str(row.id),
                        "audit_event_id": str(audit.event_id),
                        "version": row.version,
                        "status": projection.status,
                        "public_use_status": "BLOCKED",
                        "external_effects": "NONE",
                    },
                    status="PENDING",
                    attempts=0,
                    available_at=operation_at,
                    created_at=operation_at,
                )
            )
            evidence = CandidateWorkspaceUpdateEvidence(
                workspace=projection,
                audit_event_id=audit.event_id,
                outbox_event_id=outbox_event_id,
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

    def approve_section(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        request: CandidateSectionApprovalRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CandidateWorkspaceApprovalEvidence:
        try:
            return self._approve_section(
                tenant_id,
                campaign_id,
                expected_version=expected_version,
                request=request,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        except (
            CandidateWorkspaceApprovalConflict,
            CandidateWorkspaceIdempotencyConflict,
            CandidateWorkspaceNotFound,
            CandidateWorkspaceVersionConflict,
        ):
            raise
        except (
            AuditScopeUnavailable,
            CandidateWorkspaceContractError,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise CandidateWorkspaceUnavailable("Candidate workspace is unavailable") from exc

    def _approve_section(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        request: CandidateSectionApprovalRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CandidateWorkspaceApprovalEvidence:
        digest = canonical_hash(
            {
                "tenant_id": str(tenant_id),
                "campaign_id": str(campaign_id),
                "expected_version": expected_version,
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
                operation=APPROVE_OPERATION,
                idempotency_key=idempotency_key,
            )
            replay = _replay(
                session,
                tenant_id=tenant_id,
                operation=APPROVE_OPERATION,
                idempotency_key=idempotency_key,
                digest=digest,
                evidence_type=CandidateWorkspaceApprovalEvidence,
            )
            if replay is not None:
                return replay

            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            operation_at = audit_lock.acquired_at
            campaign, _ = _campaign_context(
                session,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
            )
            row = session.scalar(
                select(CandidateWorkspace)
                .where(
                    CandidateWorkspace.tenant_id == tenant_id,
                    CandidateWorkspace.campaign_id == campaign_id,
                )
                .with_for_update()
            )
            if row is None:
                raise CandidateWorkspaceNotFound("Candidate workspace was not found")
            if row.version != expected_version:
                raise CandidateWorkspaceVersionConflict("Candidate workspace version is stale")

            before = _projection(session, row, campaign)
            if request.section not in before.approvable_sections:
                raise CandidateWorkspaceApprovalConflict(
                    "Candidate section is not ready for approval"
                )
            if request.section in before.current_approved_sections:
                raise CandidateWorkspaceApprovalConflict(
                    "Candidate section already has a current approval"
                )

            approval_row = CandidateSectionApproval(
                id=uuid4(),
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                candidate_workspace_id=row.id,
                section=request.section,
                approved_version=row.version,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                reason=request.reason,
                approved_at=operation_at,
            )
            session.add(approval_row)
            session.flush()
            projection = _projection(session, row, campaign)
            approval = _approval_projection(approval_row)
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="candidate_workspace.section_approved",
                resource_type="candidate_workspace",
                resource_id=str(row.id),
                payload={
                    "section": request.section,
                    "workspace_version": row.version,
                    "workspace_status": projection.status,
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "public_use_status": "BLOCKED",
                    "external_effects": "NONE",
                },
            )
            outbox_event_id = uuid4()
            session.add(
                OutboxEvent(
                    id=outbox_event_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    topic="candidate_workspace.section_approved",
                    payload={
                        "candidate_workspace_id": str(row.id),
                        "approval_id": str(approval_row.id),
                        "section": request.section,
                        "approved_version": row.version,
                        "audit_event_id": str(audit.event_id),
                        "public_use_status": "BLOCKED",
                        "external_effects": "NONE",
                    },
                    status="PENDING",
                    attempts=0,
                    available_at=operation_at,
                    created_at=operation_at,
                )
            )
            evidence = CandidateWorkspaceApprovalEvidence(
                workspace=projection,
                approval=approval,
                audit_event_id=audit.event_id,
                outbox_event_id=outbox_event_id,
            )
            _store_replay(
                session,
                tenant_id=tenant_id,
                principal_id=principal_id,
                operation=APPROVE_OPERATION,
                idempotency_key=idempotency_key,
                request_digest=digest,
                response=evidence,
                created_at=operation_at,
            )
            session.flush()
        return evidence
