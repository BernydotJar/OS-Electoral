"""Tenant-scoped persistence service for resumable guided campaign intake."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select
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
    GuidedIntake,
    IdempotencyRecord,
    OutboxEvent,
    Workspace,
)
from campaignos.onboarding.contracts import (
    GuidedIntakeAssessmentInput,
    GuidedIntakeProjection,
    GuidedIntakeReadEvidence,
    GuidedIntakeStartEvidence,
    GuidedIntakeUpdate,
    GuidedIntakeUpdateEvidence,
    assess_guided_intake,
)

START_OPERATION = "guided_intake.start"
UPDATE_OPERATION = "guided_intake.update"
_LIST_FIELDS = {"current_team", "current_assets", "known_unknowns", "evidence_requirements"}


class GuidedIntakeNotFound(LookupError):
    """The campaign or intake is unavailable in the selected tenant."""


class GuidedIntakePrerequisiteConflict(RuntimeError):
    """A new intake cannot start before campaign operational setup is complete."""

    def __init__(self, missing_requirements: tuple[str, ...]) -> None:
        super().__init__("Campaign setup is not ready for guided intake")
        self.missing_requirements = missing_requirements


class GuidedIntakeVersionConflict(RuntimeError):
    """The intake changed after the caller's observed version."""


class GuidedIntakeIdempotencyConflict(RuntimeError):
    """An idempotency key was reused with different intent or authority."""


class GuidedIntakeUnavailable(RuntimeError):
    """The guided intake boundary cannot safely complete."""


class GuidedIntakeService(Protocol):
    def start(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> GuidedIntakeStartEvidence: ...

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
    ) -> GuidedIntakeReadEvidence: ...

    def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: GuidedIntakeUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> GuidedIntakeUpdateEvidence: ...


class UnavailableGuidedIntakeService:
    def start(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> GuidedIntakeStartEvidence:
        del tenant_id, campaign_id, kwargs
        raise GuidedIntakeUnavailable("Guided intake is unavailable")

    def get(self, tenant_id: UUID, campaign_id: UUID, **kwargs: object) -> GuidedIntakeReadEvidence:
        del tenant_id, campaign_id, kwargs
        raise GuidedIntakeUnavailable("Guided intake is unavailable")

    def update(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> GuidedIntakeUpdateEvidence:
        del tenant_id, campaign_id, kwargs
        raise GuidedIntakeUnavailable("Guided intake is unavailable")


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
        raise GuidedIntakeNotFound("Guided intake was not found")
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


def _missing_start_requirements(campaign: Campaign, active_workspace_count: int) -> tuple[str, ...]:
    missing: list[str] = []
    if not campaign.name.strip():
        missing.append("campaign_name")
    if not campaign.jurisdiction.strip():
        missing.append("jurisdiction")
    if not campaign.stage.strip():
        missing.append("campaign_stage")
    if active_workspace_count < 1:
        missing.append("active_workspace")
    return tuple(missing)


def _projection(
    row: GuidedIntake,
    campaign: Campaign,
    active_workspace_count: int,
) -> GuidedIntakeProjection:
    return assess_guided_intake(
        GuidedIntakeAssessmentInput.model_validate(
            {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "campaign_id": row.campaign_id,
                "campaign_version": campaign.version,
                "campaign_status": campaign.status,
                "campaign_name": campaign.name,
                "jurisdiction": campaign.jurisdiction,
                "stage": campaign.stage,
                "active_workspace_count": active_workspace_count,
                "office": row.office,
                "candidate_project": row.candidate_project,
                "current_team": row.current_team,
                "current_assets": row.current_assets,
                "budget_status": row.budget_status,
                "known_unknowns": row.known_unknowns,
                "evidence_requirements": row.evidence_requirements,
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
        raise GuidedIntakeIdempotencyConflict(
            "Idempotency key conflicts with a previous guided intake request"
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
class SqlAlchemyGuidedIntakeService:
    database: Database

    def start(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> GuidedIntakeStartEvidence:
        try:
            return self._start(
                tenant_id,
                campaign_id,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        except (
            GuidedIntakeIdempotencyConflict,
            GuidedIntakeNotFound,
            GuidedIntakePrerequisiteConflict,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise GuidedIntakeUnavailable("Guided intake is unavailable") from exc

    def _start(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> GuidedIntakeStartEvidence:
        digest = canonical_hash(
            {
                "tenant_id": str(tenant_id),
                "campaign_id": str(campaign_id),
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
                operation=START_OPERATION,
                idempotency_key=idempotency_key,
            )
            replay = _replay(
                session,
                tenant_id=tenant_id,
                operation=START_OPERATION,
                idempotency_key=idempotency_key,
                digest=digest,
                evidence_type=GuidedIntakeStartEvidence,
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
            row = session.scalar(
                select(GuidedIntake)
                .where(
                    GuidedIntake.tenant_id == tenant_id,
                    GuidedIntake.campaign_id == campaign_id,
                )
                .with_for_update()
            )
            created = row is None
            if row is None:
                missing = _missing_start_requirements(campaign, active_workspace_count)
                if missing:
                    raise GuidedIntakePrerequisiteConflict(missing)
                row = GuidedIntake(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    status="IN_PROGRESS",
                    budget_status="NOT_ASSESSED",
                    version=1,
                    created_at=operation_at,
                    updated_at=operation_at,
                )
                session.add(row)
                session.flush()

            event_type = "guided_intake.started" if created else "guided_intake.resumed"
            projection = _projection(row, campaign, active_workspace_count)
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type=event_type,
                resource_type="guided_intake",
                resource_id=str(row.id),
                payload={
                    "intake_version": row.version,
                    "intake_status": projection.status,
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "external_effects": "NONE",
                },
            )
            outbox_event_id: UUID | None = None
            if created:
                outbox_event_id = uuid4()
                session.add(
                    OutboxEvent(
                        id=outbox_event_id,
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        topic="guided_intake.started",
                        payload={
                            "guided_intake_id": str(row.id),
                            "audit_event_id": str(audit.event_id),
                            "version": row.version,
                            "external_effects": "NONE",
                        },
                        status="PENDING",
                        attempts=0,
                        available_at=operation_at,
                        created_at=operation_at,
                    )
                )
            evidence = GuidedIntakeStartEvidence(
                intake=projection,
                audit_event_id=audit.event_id,
                outbox_event_id=outbox_event_id,
                created=created,
            )
            _store_replay(
                session,
                tenant_id=tenant_id,
                principal_id=principal_id,
                operation=START_OPERATION,
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
    ) -> GuidedIntakeReadEvidence:
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                campaign, active_workspace_count = _campaign_context(
                    session,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                )
                row = session.scalar(
                    select(GuidedIntake).where(
                        GuidedIntake.tenant_id == tenant_id,
                        GuidedIntake.campaign_id == campaign_id,
                    )
                )
                if row is None:
                    raise GuidedIntakeNotFound("Guided intake was not found")
                projection = _projection(row, campaign, active_workspace_count)
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="guided_intake.read",
                    resource_type="guided_intake",
                    resource_id=str(row.id),
                    payload={
                        "intake_version": row.version,
                        "intake_status": projection.status,
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "external_effects": "NONE",
                    },
                )
                evidence = GuidedIntakeReadEvidence(
                    intake=projection,
                    audit_event_id=audit.event_id,
                )
                session.flush()
            return evidence
        except GuidedIntakeNotFound:
            raise
        except (
            AuditScopeUnavailable,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise GuidedIntakeUnavailable("Guided intake is unavailable") from exc

    def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: GuidedIntakeUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> GuidedIntakeUpdateEvidence:
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
            GuidedIntakeIdempotencyConflict,
            GuidedIntakeNotFound,
            GuidedIntakeVersionConflict,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise GuidedIntakeUnavailable("Guided intake is unavailable") from exc

    def _update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: GuidedIntakeUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> GuidedIntakeUpdateEvidence:
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
                evidence_type=GuidedIntakeUpdateEvidence,
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
            row = session.scalar(
                select(GuidedIntake)
                .where(
                    GuidedIntake.tenant_id == tenant_id,
                    GuidedIntake.campaign_id == campaign_id,
                )
                .with_for_update()
            )
            if row is None:
                raise GuidedIntakeNotFound("Guided intake was not found")
            if row.version != expected_version:
                raise GuidedIntakeVersionConflict("Guided intake version is stale")

            changed_fields = sorted(changes.model_fields_set)
            for field_name in changed_fields:
                value = getattr(changes, field_name)
                if field_name in _LIST_FIELDS and value is not None:
                    value = list(value)
                setattr(row, field_name, value)
            row.version += 1
            row.updated_at = operation_at
            projection = _projection(row, campaign, active_workspace_count)
            row.status = (
                "READY_FOR_RESEARCH" if projection.status == "READY_FOR_RESEARCH" else "IN_PROGRESS"
            )
            session.flush()
            projection = _projection(row, campaign, active_workspace_count)
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="guided_intake.updated",
                resource_type="guided_intake",
                resource_id=str(row.id),
                payload={
                    "intake_version": row.version,
                    "intake_status": projection.status,
                    "changed_fields": changed_fields,
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "external_effects": "NONE",
                },
            )
            outbox_event_id = uuid4()
            session.add(
                OutboxEvent(
                    id=outbox_event_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    topic="guided_intake.updated",
                    payload={
                        "guided_intake_id": str(row.id),
                        "audit_event_id": str(audit.event_id),
                        "version": row.version,
                        "status": projection.status,
                        "external_effects": "NONE",
                    },
                    status="PENDING",
                    attempts=0,
                    available_at=operation_at,
                    created_at=operation_at,
                )
            )
            evidence = GuidedIntakeUpdateEvidence(
                intake=projection,
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
