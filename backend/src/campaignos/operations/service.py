"""Tenant-scoped persistence for campaign roadmaps and War Room snapshots."""

from __future__ import annotations

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
    CampaignRoadmap,
    IdempotencyRecord,
    OutboxEvent,
    TeamWorkspace,
    WarRoomSnapshot,
)
from campaignos.operations.contracts import (
    CampaignRoadmapAssessmentInput,
    CampaignRoadmapContractError,
    CampaignRoadmapCreate,
    CampaignRoadmapCreateEvidence,
    CampaignRoadmapProjection,
    CampaignRoadmapReadEvidence,
    CampaignRoadmapUpdate,
    CampaignRoadmapUpdateEvidence,
    WarRoomSnapshotCreate,
    WarRoomSnapshotEvidence,
    WarRoomSnapshotProjection,
    WarRoomSnapshotReadEvidence,
    assess_campaign_roadmap,
    build_war_room_snapshot,
)
from campaignos.teams.contracts import TeamRoleCard

CREATE_ROADMAP_OPERATION = "campaign_roadmap.create"
UPDATE_ROADMAP_OPERATION = "campaign_roadmap.update"
CREATE_SNAPSHOT_OPERATION = "war_room_snapshot.create"


class CampaignRoadmapNotFound(LookupError):
    """The campaign roadmap is unavailable in the selected tenant."""


class CampaignRoadmapPrerequisiteConflict(RuntimeError):
    """The campaign Team Workspace prerequisite is missing."""


class CampaignRoadmapConflict(RuntimeError):
    """A campaign roadmap already exists."""


class CampaignRoadmapVersionConflict(RuntimeError):
    """The roadmap version changed after the caller observed it."""


class CampaignRoadmapIdempotencyConflict(RuntimeError):
    """An idempotency key was reused with different intent or authority."""


class CampaignRoadmapEvidenceConflict(RuntimeError):
    """The proposed roadmap violates a graph or ownership invariant."""


class WarRoomSnapshotConflict(RuntimeError):
    """A daily snapshot already exists for the campaign and date."""


class WarRoomSnapshotNotFound(LookupError):
    """No Daily War Room snapshot exists for the selected campaign."""


class CampaignRoadmapUnavailable(RuntimeError):
    """The campaign operations boundary cannot safely complete."""


class CampaignOperationsService(Protocol):
    def create_roadmap(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: CampaignRoadmapCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CampaignRoadmapCreateEvidence: ...

    def get_roadmap(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> CampaignRoadmapReadEvidence: ...

    def update_roadmap(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: CampaignRoadmapUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CampaignRoadmapUpdateEvidence: ...

    def create_snapshot(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_roadmap_version: int,
        request: WarRoomSnapshotCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> WarRoomSnapshotEvidence: ...

    def get_latest_snapshot(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> WarRoomSnapshotReadEvidence: ...


class UnavailableCampaignOperationsService:
    def create_roadmap(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> CampaignRoadmapCreateEvidence:
        del tenant_id, campaign_id, kwargs
        raise CampaignRoadmapUnavailable("Campaign operations are unavailable")

    def get_roadmap(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> CampaignRoadmapReadEvidence:
        del tenant_id, campaign_id, kwargs
        raise CampaignRoadmapUnavailable("Campaign operations are unavailable")

    def update_roadmap(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> CampaignRoadmapUpdateEvidence:
        del tenant_id, campaign_id, kwargs
        raise CampaignRoadmapUnavailable("Campaign operations are unavailable")

    def create_snapshot(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> WarRoomSnapshotEvidence:
        del tenant_id, campaign_id, kwargs
        raise CampaignRoadmapUnavailable("Campaign operations are unavailable")

    def get_latest_snapshot(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> WarRoomSnapshotReadEvidence:
        del tenant_id, campaign_id, kwargs
        raise CampaignRoadmapUnavailable("Campaign operations are unavailable")


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
        raise CampaignRoadmapNotFound("Campaign roadmap was not found")
    return campaign


def _filled_team_role_ids(session: Session, tenant_id: UUID, campaign_id: UUID) -> tuple[UUID, ...]:
    team = session.scalar(
        select(TeamWorkspace).where(
            TeamWorkspace.tenant_id == tenant_id,
            TeamWorkspace.campaign_id == campaign_id,
        )
    )
    if team is None:
        raise CampaignRoadmapPrerequisiteConflict("Team Workspace is required")
    try:
        roles = tuple(TeamRoleCard.model_validate(item) for item in team.roles or ())
    except ValidationError as exc:
        raise CampaignRoadmapUnavailable("Campaign operations are unavailable") from exc
    role_ids = tuple(role.id for role in roles if role.status == "FILLED")
    if not role_ids:
        raise CampaignRoadmapPrerequisiteConflict("At least one filled team role is required")
    return role_ids


def _projection(
    row: CampaignRoadmap,
    campaign: Campaign,
    team_role_ids: tuple[UUID, ...],
) -> CampaignRoadmapProjection:
    return assess_campaign_roadmap(
        CampaignRoadmapAssessmentInput.model_validate(
            {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "campaign_id": row.campaign_id,
                "campaign_version": campaign.version,
                "campaign_status": campaign.status,
                "campaign_name": campaign.name,
                "title": row.title,
                "team_role_ids": team_role_ids,
                "phases": row.phases,
                "workstreams": row.workstreams,
                "milestones": row.milestones,
                "tasks": row.tasks,
                "blockers": row.blockers,
                "decisions": row.decisions,
                "follow_up_items": row.follow_up_items,
                "learning_notes": row.learning_notes,
                "version": row.version,
                "created_at": _as_utc(row.created_at),
                "updated_at": _as_utc(row.updated_at),
            }
        )
    )


def _snapshot_projection(row: WarRoomSnapshot) -> WarRoomSnapshotProjection:
    return WarRoomSnapshotProjection.model_validate(
        {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "campaign_id": row.campaign_id,
            "roadmap_id": row.roadmap_id,
            "roadmap_version": row.roadmap_version,
            "snapshot_date": row.snapshot_date,
            "priorities": row.priorities,
            "ready_task_ids": row.ready_task_ids,
            "blocked_task_ids": row.blocked_task_ids,
            "required_decision_ids": row.required_decision_ids,
            "follow_up_notes": row.follow_up_notes,
            "learning_note_ids": row.learning_note_ids,
            "authority_effect": "NONE",
            "external_effects": "NONE",
            "created_at": _as_utc(row.created_at),
        }
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
        raise CampaignRoadmapIdempotencyConflict(
            "Idempotency key conflicts with a previous campaign operations request"
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
class SqlAlchemyCampaignOperationsService:
    database: Database

    def create_roadmap(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: CampaignRoadmapCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CampaignRoadmapCreateEvidence:
        try:
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
                    operation=CREATE_ROADMAP_OPERATION,
                    idempotency_key=idempotency_key,
                )
                replay = _replay(
                    session,
                    tenant_id=tenant_id,
                    operation=CREATE_ROADMAP_OPERATION,
                    idempotency_key=idempotency_key,
                    digest=digest,
                    evidence_type=CampaignRoadmapCreateEvidence,
                )
                if replay is not None:
                    return replay
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                operation_at = audit_lock.acquired_at
                campaign = _campaign(session, tenant_id, campaign_id)
                role_ids = _filled_team_role_ids(session, tenant_id, campaign_id)
                existing = session.scalar(
                    select(CampaignRoadmap.id)
                    .where(
                        CampaignRoadmap.tenant_id == tenant_id,
                        CampaignRoadmap.campaign_id == campaign_id,
                    )
                    .with_for_update()
                )
                if existing is not None:
                    raise CampaignRoadmapConflict("Campaign roadmap already exists")
                row = CampaignRoadmap(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    title=request.title,
                    phases=None,
                    workstreams=None,
                    milestones=None,
                    tasks=None,
                    blockers=None,
                    decisions=None,
                    follow_up_items=None,
                    learning_notes=None,
                    version=1,
                    created_at=operation_at,
                    updated_at=operation_at,
                )
                session.add(row)
                session.flush()
                projection = _projection(row, campaign, role_ids)
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="campaign_roadmap.created",
                    resource_type="campaign_roadmap",
                    resource_id=str(row.id),
                    payload={
                        "roadmap_version": row.version,
                        "roadmap_status": projection.status,
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
                        topic="campaign_roadmap.created",
                        payload={
                            "roadmap_id": str(row.id),
                            "roadmap_version": row.version,
                            "audit_event_id": str(audit.event_id),
                            "authority_effect": "NONE",
                            "external_effects": "NONE",
                        },
                        status="PENDING",
                        attempts=0,
                        available_at=operation_at,
                        created_at=operation_at,
                    )
                )
                evidence = CampaignRoadmapCreateEvidence(
                    roadmap=projection,
                    audit_event_id=audit.event_id,
                    outbox_event_id=outbox_id,
                )
                _store_replay(
                    session,
                    tenant_id=tenant_id,
                    principal_id=principal_id,
                    operation=CREATE_ROADMAP_OPERATION,
                    idempotency_key=idempotency_key,
                    request_digest=digest,
                    response=evidence,
                    created_at=operation_at,
                )
                session.flush()
            return evidence
        except (
            CampaignRoadmapConflict,
            CampaignRoadmapIdempotencyConflict,
            CampaignRoadmapNotFound,
            CampaignRoadmapPrerequisiteConflict,
        ):
            raise
        except (
            AuditScopeUnavailable,
            CampaignRoadmapContractError,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise CampaignRoadmapUnavailable("Campaign operations are unavailable") from exc

    def get_roadmap(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> CampaignRoadmapReadEvidence:
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                campaign = _campaign(session, tenant_id, campaign_id)
                role_ids = _filled_team_role_ids(session, tenant_id, campaign_id)
                row = session.scalar(
                    select(CampaignRoadmap).where(
                        CampaignRoadmap.tenant_id == tenant_id,
                        CampaignRoadmap.campaign_id == campaign_id,
                    )
                )
                if row is None:
                    raise CampaignRoadmapNotFound("Campaign roadmap was not found")
                projection = _projection(row, campaign, role_ids)
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="campaign_roadmap.read",
                    resource_type="campaign_roadmap",
                    resource_id=str(row.id),
                    payload={
                        "roadmap_version": row.version,
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "authority_effect": "NONE",
                        "external_effects": "NONE",
                    },
                )
                evidence = CampaignRoadmapReadEvidence(
                    roadmap=projection,
                    audit_event_id=audit.event_id,
                )
                session.flush()
            return evidence
        except (CampaignRoadmapNotFound, CampaignRoadmapPrerequisiteConflict):
            raise
        except (
            AuditScopeUnavailable,
            CampaignRoadmapContractError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise CampaignRoadmapUnavailable("Campaign operations are unavailable") from exc

    def update_roadmap(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: CampaignRoadmapUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CampaignRoadmapUpdateEvidence:
        try:
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
                    operation=UPDATE_ROADMAP_OPERATION,
                    idempotency_key=idempotency_key,
                )
                replay = _replay(
                    session,
                    tenant_id=tenant_id,
                    operation=UPDATE_ROADMAP_OPERATION,
                    idempotency_key=idempotency_key,
                    digest=digest,
                    evidence_type=CampaignRoadmapUpdateEvidence,
                )
                if replay is not None:
                    return replay
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                operation_at = audit_lock.acquired_at
                campaign = _campaign(session, tenant_id, campaign_id)
                role_ids = _filled_team_role_ids(session, tenant_id, campaign_id)
                row = session.scalar(
                    select(CampaignRoadmap)
                    .where(
                        CampaignRoadmap.tenant_id == tenant_id,
                        CampaignRoadmap.campaign_id == campaign_id,
                    )
                    .with_for_update()
                )
                if row is None:
                    raise CampaignRoadmapNotFound("Campaign roadmap was not found")
                if row.version != expected_version:
                    raise CampaignRoadmapVersionConflict("Campaign roadmap version is stale")
                changed_fields = sorted(changes.model_fields_set)
                serialized = changes.model_dump(mode="json", exclude_unset=True)
                for field_name in changed_fields:
                    setattr(row, field_name, serialized[field_name])
                row.version += 1
                row.updated_at = operation_at
                session.flush()
                try:
                    projection = _projection(row, campaign, role_ids)
                except CampaignRoadmapContractError as exc:
                    raise CampaignRoadmapEvidenceConflict(
                        "Campaign roadmap conflicts with graph invariants"
                    ) from exc
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="campaign_roadmap.updated",
                    resource_type="campaign_roadmap",
                    resource_id=str(row.id),
                    payload={
                        "roadmap_version": row.version,
                        "roadmap_status": projection.status,
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
                        topic="campaign_roadmap.updated",
                        payload={
                            "roadmap_id": str(row.id),
                            "roadmap_version": row.version,
                            "audit_event_id": str(audit.event_id),
                            "authority_effect": "NONE",
                            "external_effects": "NONE",
                        },
                        status="PENDING",
                        attempts=0,
                        available_at=operation_at,
                        created_at=operation_at,
                    )
                )
                evidence = CampaignRoadmapUpdateEvidence(
                    roadmap=projection,
                    audit_event_id=audit.event_id,
                    outbox_event_id=outbox_id,
                )
                _store_replay(
                    session,
                    tenant_id=tenant_id,
                    principal_id=principal_id,
                    operation=UPDATE_ROADMAP_OPERATION,
                    idempotency_key=idempotency_key,
                    request_digest=digest,
                    response=evidence,
                    created_at=operation_at,
                )
                session.flush()
            return evidence
        except (
            CampaignRoadmapEvidenceConflict,
            CampaignRoadmapIdempotencyConflict,
            CampaignRoadmapNotFound,
            CampaignRoadmapPrerequisiteConflict,
            CampaignRoadmapVersionConflict,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise CampaignRoadmapUnavailable("Campaign operations are unavailable") from exc

    def get_latest_snapshot(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> WarRoomSnapshotReadEvidence:
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                _campaign(session, tenant_id, campaign_id)
                _filled_team_role_ids(session, tenant_id, campaign_id)
                row = session.scalar(
                    select(WarRoomSnapshot)
                    .where(
                        WarRoomSnapshot.tenant_id == tenant_id,
                        WarRoomSnapshot.campaign_id == campaign_id,
                    )
                    .order_by(
                        WarRoomSnapshot.snapshot_date.desc(),
                        WarRoomSnapshot.created_at.desc(),
                    )
                    .limit(1)
                )
                if row is None:
                    raise WarRoomSnapshotNotFound("Daily War Room snapshot was not found")
                projection = _snapshot_projection(row)
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="war_room_snapshot.read",
                    resource_type="war_room_snapshot",
                    resource_id=str(row.id),
                    payload={
                        "roadmap_id": str(row.roadmap_id),
                        "roadmap_version": row.roadmap_version,
                        "snapshot_date": row.snapshot_date.isoformat(),
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "authority_effect": "NONE",
                        "external_effects": "NONE",
                    },
                )
                evidence = WarRoomSnapshotReadEvidence(
                    snapshot=projection,
                    audit_event_id=audit.event_id,
                )
                session.flush()
            return evidence
        except (
            CampaignRoadmapNotFound,
            CampaignRoadmapPrerequisiteConflict,
            WarRoomSnapshotNotFound,
        ):
            raise
        except (
            AuditScopeUnavailable,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise CampaignRoadmapUnavailable("Campaign operations are unavailable") from exc

    def create_snapshot(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_roadmap_version: int,
        request: WarRoomSnapshotCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> WarRoomSnapshotEvidence:
        try:
            digest = canonical_hash(
                {
                    "tenant_id": str(tenant_id),
                    "campaign_id": str(campaign_id),
                    "expected_roadmap_version": expected_roadmap_version,
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
                    operation=CREATE_SNAPSHOT_OPERATION,
                    idempotency_key=idempotency_key,
                )
                replay = _replay(
                    session,
                    tenant_id=tenant_id,
                    operation=CREATE_SNAPSHOT_OPERATION,
                    idempotency_key=idempotency_key,
                    digest=digest,
                    evidence_type=WarRoomSnapshotEvidence,
                )
                if replay is not None:
                    return replay
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                operation_at = audit_lock.acquired_at
                campaign = _campaign(session, tenant_id, campaign_id)
                role_ids = _filled_team_role_ids(session, tenant_id, campaign_id)
                roadmap = session.scalar(
                    select(CampaignRoadmap)
                    .where(
                        CampaignRoadmap.tenant_id == tenant_id,
                        CampaignRoadmap.campaign_id == campaign_id,
                    )
                    .with_for_update()
                )
                if roadmap is None:
                    raise CampaignRoadmapNotFound("Campaign roadmap was not found")
                if roadmap.version != expected_roadmap_version:
                    raise CampaignRoadmapVersionConflict("Campaign roadmap version is stale")
                existing = session.scalar(
                    select(WarRoomSnapshot.id)
                    .where(
                        WarRoomSnapshot.tenant_id == tenant_id,
                        WarRoomSnapshot.campaign_id == campaign_id,
                        WarRoomSnapshot.snapshot_date == request.snapshot_date,
                    )
                    .with_for_update()
                )
                if existing is not None:
                    raise WarRoomSnapshotConflict("Daily War Room snapshot already exists")
                roadmap_projection = _projection(roadmap, campaign, role_ids)
                snapshot_projection = build_war_room_snapshot(
                    roadmap_projection,
                    request=request,
                    snapshot_id=uuid4(),
                    created_at=operation_at,
                )
                row = WarRoomSnapshot(
                    id=snapshot_projection.id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    roadmap_id=roadmap.id,
                    roadmap_version=roadmap.version,
                    snapshot_date=request.snapshot_date,
                    priorities=list(request.priorities),
                    ready_task_ids=[str(item) for item in snapshot_projection.ready_task_ids],
                    blocked_task_ids=[str(item) for item in snapshot_projection.blocked_task_ids],
                    required_decision_ids=[
                        str(item) for item in snapshot_projection.required_decision_ids
                    ],
                    follow_up_notes=list(request.follow_up_notes),
                    learning_note_ids=[str(item) for item in snapshot_projection.learning_note_ids],
                    created_at=operation_at,
                    updated_at=operation_at,
                )
                session.add(row)
                session.flush()
                projection = _snapshot_projection(row)
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="war_room_snapshot.created",
                    resource_type="war_room_snapshot",
                    resource_id=str(row.id),
                    payload={
                        "roadmap_id": str(roadmap.id),
                        "roadmap_version": roadmap.version,
                        "snapshot_date": request.snapshot_date.isoformat(),
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
                        topic="war_room_snapshot.created",
                        payload={
                            "snapshot_id": str(row.id),
                            "roadmap_id": str(roadmap.id),
                            "roadmap_version": roadmap.version,
                            "audit_event_id": str(audit.event_id),
                            "authority_effect": "NONE",
                            "external_effects": "NONE",
                        },
                        status="PENDING",
                        attempts=0,
                        available_at=operation_at,
                        created_at=operation_at,
                    )
                )
                evidence = WarRoomSnapshotEvidence(
                    snapshot=projection,
                    audit_event_id=audit.event_id,
                    outbox_event_id=outbox_id,
                )
                _store_replay(
                    session,
                    tenant_id=tenant_id,
                    principal_id=principal_id,
                    operation=CREATE_SNAPSHOT_OPERATION,
                    idempotency_key=idempotency_key,
                    request_digest=digest,
                    response=evidence,
                    created_at=operation_at,
                )
                session.flush()
            return evidence
        except (
            CampaignRoadmapIdempotencyConflict,
            CampaignRoadmapNotFound,
            CampaignRoadmapPrerequisiteConflict,
            CampaignRoadmapVersionConflict,
            WarRoomSnapshotConflict,
        ):
            raise
        except (
            AuditScopeUnavailable,
            CampaignRoadmapContractError,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise CampaignRoadmapUnavailable("Campaign operations are unavailable") from exc
