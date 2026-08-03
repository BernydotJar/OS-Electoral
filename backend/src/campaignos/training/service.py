"""Tenant-scoped Training Academy persistence and assessment service."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError
from sqlalchemy import func, or_, select
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
    IdempotencyRecord,
    Membership,
    OutboxEvent,
    TrainingAssignment,
    TrainingCompletionReceipt,
    TrainingModuleProgress,
)
from campaignos.training.catalog import (
    CATALOG_DIGEST,
    grade_attempt,
    module_by_ref,
    path_by_ref,
    project_catalog,
)
from campaignos.training.contracts import (
    Locale,
    TrainingAssignmentCreate,
    TrainingAssignmentCreateEvidence,
    TrainingAssignmentEvidence,
    TrainingAssignmentListEvidence,
    TrainingAssignmentProjection,
    TrainingAttemptEvidence,
    TrainingAttemptRequest,
    TrainingCatalogProjection,
    TrainingCompletionReceiptProjection,
    TrainingModuleProgressProjection,
    TrainingModuleStartRequest,
    TrainingReceiptListEvidence,
)

CREATE_OPERATION = "training.assignment.create"
START_OPERATION = "training.module.start"
ATTEMPT_OPERATION = "training.module.attempt"
MAX_ACTIVE_ASSIGNMENTS_PER_PRINCIPAL = 25
MAX_ACTIVE_ASSIGNMENTS_PER_CAMPAIGN = 200
MAX_ATTEMPTS_PER_MODULE = 10


class TrainingNotFound(LookupError):
    """The requested campaign, assignment, module, or learner is unavailable."""


class TrainingConflict(RuntimeError):
    """The requested training state conflicts with existing evidence."""


class TrainingVersionConflict(RuntimeError):
    """The assignment or module changed after the caller observed it."""


class TrainingIdempotencyConflict(RuntimeError):
    """An idempotency key was reused with different training intent."""


class TrainingLimitConflict(RuntimeError):
    """A bounded Training Academy limit would be exceeded."""


class TrainingAccessConflict(RuntimeError):
    """The operation is not valid for the requested learner."""


class TrainingUnavailable(RuntimeError):
    """The Training Academy boundary cannot safely complete."""


class TrainingService(Protocol):
    def catalog(self, locale: Locale) -> TrainingCatalogProjection: ...

    def create_assignment(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: TrainingAssignmentCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TrainingAssignmentCreateEvidence: ...

    def list_self(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> TrainingAssignmentListEvidence: ...

    def get_assignment(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        assignment_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> TrainingAssignmentEvidence: ...

    def start_module(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        assignment_id: UUID,
        module_id: str,
        *,
        request: TrainingModuleStartRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TrainingAssignmentEvidence: ...

    def submit_attempt(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        assignment_id: UUID,
        module_id: str,
        *,
        request: TrainingAttemptRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TrainingAttemptEvidence: ...

    def list_receipts(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        assignment_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> TrainingReceiptListEvidence: ...


class UnavailableTrainingService:
    def catalog(self, locale: Locale) -> TrainingCatalogProjection:
        del locale
        raise TrainingUnavailable("Training Academy is unavailable")

    def __getattr__(self, name: str) -> object:
        del name
        raise TrainingUnavailable("Training Academy is unavailable")


def _as_utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _campaign(session: Session, tenant_id: UUID, campaign_id: UUID) -> Campaign:
    row = session.scalar(
        select(Campaign).where(
            Campaign.tenant_id == tenant_id,
            Campaign.id == campaign_id,
            Campaign.status.in_(("DRAFT", "ACTIVE")),
        )
    )
    if row is None:
        raise TrainingNotFound("Training campaign was not found")
    return row


def _require_active_learner(
    session: Session, *, tenant_id: UUID, campaign_id: UUID, principal_id: UUID
) -> None:
    now = datetime.now(UTC)
    membership_id = session.scalar(
        select(Membership.id).where(
            Membership.tenant_id == tenant_id,
            Membership.principal_id == principal_id,
            Membership.status == "ACTIVE",
            Membership.valid_from <= now,
            or_(Membership.expires_at.is_(None), Membership.expires_at > now),
            or_(Membership.campaign_id.is_(None), Membership.campaign_id == campaign_id),
        )
    )
    if membership_id is None:
        raise TrainingNotFound("Training learner was not found")


def _assignment(
    session: Session,
    *,
    tenant_id: UUID,
    campaign_id: UUID,
    assignment_id: UUID,
    lock: bool = False,
) -> TrainingAssignment:
    statement = select(TrainingAssignment).where(
        TrainingAssignment.tenant_id == tenant_id,
        TrainingAssignment.campaign_id == campaign_id,
        TrainingAssignment.id == assignment_id,
    )
    if lock:
        statement = statement.with_for_update()
    row = session.scalar(statement)
    if row is None:
        raise TrainingNotFound("Training assignment was not found")
    return row


def _progress_rows(
    session: Session,
    *,
    tenant_id: UUID,
    campaign_id: UUID,
    assignment_id: UUID,
    lock: bool = False,
) -> tuple[TrainingModuleProgress, ...]:
    statement = (
        select(TrainingModuleProgress)
        .where(
            TrainingModuleProgress.tenant_id == tenant_id,
            TrainingModuleProgress.campaign_id == campaign_id,
            TrainingModuleProgress.assignment_id == assignment_id,
        )
        .order_by(TrainingModuleProgress.created_at, TrainingModuleProgress.module_id)
    )
    if lock:
        statement = statement.with_for_update()
    return tuple(session.scalars(statement))


def _progress(
    session: Session,
    *,
    tenant_id: UUID,
    campaign_id: UUID,
    assignment_id: UUID,
    module_id: str,
    lock: bool = False,
) -> TrainingModuleProgress:
    statement = select(TrainingModuleProgress).where(
        TrainingModuleProgress.tenant_id == tenant_id,
        TrainingModuleProgress.campaign_id == campaign_id,
        TrainingModuleProgress.assignment_id == assignment_id,
        TrainingModuleProgress.module_id == module_id,
    )
    if lock:
        statement = statement.with_for_update()
    row = session.scalar(statement)
    if row is None:
        raise TrainingNotFound("Training module assignment was not found")
    return row


def _progress_projection(row: TrainingModuleProgress) -> TrainingModuleProgressProjection:
    return TrainingModuleProgressProjection.model_validate(
        {
            "id": row.id,
            "module_id": row.module_id,
            "module_version": row.module_version,
            "status": row.status,
            "attempt_count": row.attempt_count,
            "latest_result": row.latest_result,
            "started_at": None if row.started_at is None else _as_utc(row.started_at),
            "completed_at": None if row.completed_at is None else _as_utc(row.completed_at),
            "version": row.version,
        }
    )


def _assignment_projection(
    row: TrainingAssignment,
    progress: tuple[TrainingModuleProgress, ...],
) -> TrainingAssignmentProjection:
    if not progress:
        raise TrainingUnavailable("Training assignment has no module progress")
    completed = sum(item.status == "COMPLETED" for item in progress)
    next_module = next((item.module_id for item in progress if item.status != "COMPLETED"), None)
    return TrainingAssignmentProjection.model_validate(
        {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "campaign_id": row.campaign_id,
            "principal_id": row.principal_id,
            "path_id": row.path_id,
            "path_version": row.path_version,
            "role_slug": row.role_slug,
            "status": row.status,
            "modules": tuple(_progress_projection(item) for item in progress),
            "completed_modules": completed,
            "total_modules": len(progress),
            "next_module_id": next_module,
            "catalog_digest": row.catalog_digest,
            "version": row.version,
            "assigned_at": _as_utc(row.assigned_at),
            "due_at": None if row.due_at is None else _as_utc(row.due_at),
            "completed_at": None if row.completed_at is None else _as_utc(row.completed_at),
        }
    )


def _receipt_projection(row: TrainingCompletionReceipt) -> TrainingCompletionReceiptProjection:
    return TrainingCompletionReceiptProjection(
        id=row.id,
        assignment_id=row.assignment_id,
        module_progress_id=row.module_progress_id,
        principal_id=row.principal_id,
        module_id=row.module_id,
        module_version=row.module_version,
        result="PASS",
        completed_at=_as_utc(row.completed_at),
        catalog_digest=row.catalog_digest,
        audit_event_id=row.audit_event_id,
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
        raise TrainingIdempotencyConflict(
            "Idempotency key conflicts with a previous training request"
        )
    return evidence_type.model_validate_json(json.dumps(existing.response_payload))


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


def _guard[ResultT](operation: Callable[[], ResultT]) -> ResultT:
    try:
        return operation()
    except (
        TrainingAccessConflict,
        TrainingConflict,
        TrainingIdempotencyConflict,
        TrainingLimitConflict,
        TrainingNotFound,
        TrainingVersionConflict,
    ):
        raise
    except (
        AuditScopeUnavailable,
        IntegrityError,
        KeyError,
        SQLAlchemyError,
        ValidationError,
        ValueError,
    ) as exc:
        raise TrainingUnavailable("Training Academy is unavailable") from exc


@dataclass(slots=True)
class SqlAlchemyTrainingService:
    database: Database

    def catalog(self, locale: Locale) -> TrainingCatalogProjection:
        return project_catalog(locale)

    def create_assignment(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: TrainingAssignmentCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TrainingAssignmentCreateEvidence:
        return _guard(
            lambda: self._create_assignment(
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
        )

    def _create_assignment(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: TrainingAssignmentCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TrainingAssignmentCreateEvidence:
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
                evidence_type=TrainingAssignmentCreateEvidence,
            )
            if replay is not None:
                return replay
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            operation_at = audit_lock.acquired_at
            _campaign(session, tenant_id, campaign_id)
            if request.catalog_digest != CATALOG_DIGEST:
                raise TrainingVersionConflict("Training catalog changed before assignment")
            path = path_by_ref(request.path_id, request.path_version)
            if request.role_slug is not None and request.role_slug not in path.role_slugs:
                raise TrainingConflict("Training role is not eligible for this learning path")
            _require_active_learner(
                session,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                principal_id=request.principal_id,
            )
            active_statuses = ("ASSIGNED", "IN_PROGRESS")
            principal_count = session.scalar(
                select(func.count(TrainingAssignment.id)).where(
                    TrainingAssignment.tenant_id == tenant_id,
                    TrainingAssignment.campaign_id == campaign_id,
                    TrainingAssignment.principal_id == request.principal_id,
                    TrainingAssignment.status.in_(active_statuses),
                )
            )
            campaign_count = session.scalar(
                select(func.count(TrainingAssignment.id)).where(
                    TrainingAssignment.tenant_id == tenant_id,
                    TrainingAssignment.campaign_id == campaign_id,
                    TrainingAssignment.status.in_(active_statuses),
                )
            )
            if int(principal_count or 0) >= MAX_ACTIVE_ASSIGNMENTS_PER_PRINCIPAL:
                raise TrainingLimitConflict("Learner active assignment limit reached")
            if int(campaign_count or 0) >= MAX_ACTIVE_ASSIGNMENTS_PER_CAMPAIGN:
                raise TrainingLimitConflict("Campaign active assignment limit reached")
            assignment = TrainingAssignment(
                id=uuid4(),
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                principal_id=request.principal_id,
                assigned_by_principal_id=principal_id,
                path_id=path.path_id,
                path_version=path.version,
                role_slug=request.role_slug,
                status="ASSIGNED",
                catalog_digest=CATALOG_DIGEST,
                assigned_at=operation_at,
                due_at=request.due_at,
                completed_at=None,
                version=1,
                created_at=operation_at,
                updated_at=operation_at,
            )
            session.add(assignment)
            progress_rows: list[TrainingModuleProgress] = []
            for path_module in path.modules:
                module = module_by_ref(path_module.module_id, path_module.version)
                if module.status != "APPROVED":
                    raise TrainingConflict("Training path contains a retired module")
                progress = TrainingModuleProgress(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    assignment_id=assignment.id,
                    module_id=module.module_id,
                    module_version=module.version,
                    status="NOT_STARTED",
                    attempt_count=0,
                    latest_result=None,
                    started_at=None,
                    completed_at=None,
                    version=1,
                    created_at=operation_at,
                    updated_at=operation_at,
                )
                session.add(progress)
                progress_rows.append(progress)
            session.flush()
            projection = _assignment_projection(assignment, tuple(progress_rows))
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="training.assignment.created",
                resource_type="training_assignment",
                resource_id=str(assignment.id),
                payload={
                    "learner_principal_id": str(request.principal_id),
                    "path_id": path.path_id,
                    "path_version": path.version,
                    "module_count": len(path.modules),
                    "catalog_digest": CATALOG_DIGEST,
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
                    topic="training.assignment.created",
                    payload={
                        "training_assignment_id": str(assignment.id),
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
            evidence = TrainingAssignmentCreateEvidence(
                assignment=projection,
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
            return evidence

    def list_self(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> TrainingAssignmentListEvidence:
        return _guard(
            lambda: self._list_self(
                tenant_id,
                campaign_id,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
            )
        )

    def _list_self(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> TrainingAssignmentListEvidence:
        with self.database.tenant_transaction(tenant_id) as session:
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            _campaign(session, tenant_id, campaign_id)
            _require_active_learner(
                session,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                principal_id=principal_id,
            )
            rows = tuple(
                session.scalars(
                    select(TrainingAssignment)
                    .where(
                        TrainingAssignment.tenant_id == tenant_id,
                        TrainingAssignment.campaign_id == campaign_id,
                        TrainingAssignment.principal_id == principal_id,
                    )
                    .order_by(TrainingAssignment.assigned_at.desc())
                )
            )
            projections = tuple(
                _assignment_projection(
                    row,
                    _progress_rows(
                        session,
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        assignment_id=row.id,
                    ),
                )
                for row in rows
            )
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="training.assignments.read",
                resource_type="training_assignment_collection",
                resource_id=str(campaign_id),
                payload={
                    "assignment_count": len(projections),
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "authority_effect": "NONE",
                },
            )
            return TrainingAssignmentListEvidence(
                assignments=projections,
                audit_event_id=audit.event_id,
            )

    def get_assignment(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        assignment_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> TrainingAssignmentEvidence:
        return _guard(
            lambda: self._get_assignment(
                tenant_id,
                campaign_id,
                assignment_id,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
            )
        )

    def _get_assignment(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        assignment_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> TrainingAssignmentEvidence:
        with self.database.tenant_transaction(tenant_id) as session:
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            _campaign(session, tenant_id, campaign_id)
            row = _assignment(
                session,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                assignment_id=assignment_id,
            )
            projection = _assignment_projection(
                row,
                _progress_rows(
                    session,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    assignment_id=assignment_id,
                ),
            )
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="training.assignment.read",
                resource_type="training_assignment",
                resource_id=str(assignment_id),
                payload={
                    "learner_principal_id": str(row.principal_id),
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "authority_effect": "NONE",
                },
            )
            return TrainingAssignmentEvidence(
                assignment=projection,
                audit_event_id=audit.event_id,
            )

    def start_module(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        assignment_id: UUID,
        module_id: str,
        *,
        request: TrainingModuleStartRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TrainingAssignmentEvidence:
        return _guard(
            lambda: self._start_module(
                tenant_id,
                campaign_id,
                assignment_id,
                module_id,
                request=request,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        )

    def _start_module(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        assignment_id: UUID,
        module_id: str,
        *,
        request: TrainingModuleStartRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TrainingAssignmentEvidence:
        digest = canonical_hash(
            {
                "tenant_id": str(tenant_id),
                "campaign_id": str(campaign_id),
                "assignment_id": str(assignment_id),
                "module_id": module_id,
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
                operation=START_OPERATION,
                idempotency_key=idempotency_key,
            )
            replay = _replay(
                session,
                tenant_id=tenant_id,
                operation=START_OPERATION,
                idempotency_key=idempotency_key,
                digest=digest,
                evidence_type=TrainingAssignmentEvidence,
            )
            if replay is not None:
                return replay
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            operation_at = audit_lock.acquired_at
            _campaign(session, tenant_id, campaign_id)
            row = _assignment(
                session,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                assignment_id=assignment_id,
                lock=True,
            )
            if row.principal_id != principal_id:
                raise TrainingAccessConflict("Only the assigned learner can start a module")
            progress = _progress(
                session,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                assignment_id=assignment_id,
                module_id=module_id,
                lock=True,
            )
            if request.catalog_digest != row.catalog_digest or row.catalog_digest != CATALOG_DIGEST:
                raise TrainingVersionConflict("Training catalog changed before module start")
            if row.version != request.expected_assignment_version:
                raise TrainingVersionConflict("Training assignment changed before module start")
            if progress.version != request.expected_progress_version:
                raise TrainingVersionConflict("Training module changed before module start")
            if row.status == "COMPLETED" or progress.status != "NOT_STARTED":
                raise TrainingConflict("Training module cannot be started from its current state")
            module_by_ref(progress.module_id, progress.module_version)
            progress.status = "IN_PROGRESS"
            progress.started_at = operation_at
            progress.version += 1
            progress.updated_at = operation_at
            row.status = "IN_PROGRESS"
            row.version += 1
            row.updated_at = operation_at
            session.flush()
            projection = _assignment_projection(
                row,
                _progress_rows(
                    session,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    assignment_id=assignment_id,
                    lock=True,
                ),
            )
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="training.module.started",
                resource_type="training_module_progress",
                resource_id=str(progress.id),
                payload={
                    "training_assignment_id": str(assignment_id),
                    "module_id": progress.module_id,
                    "module_version": progress.module_version,
                    "catalog_digest": CATALOG_DIGEST,
                    "assignment_version": row.version,
                    "progress_version": progress.version,
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "authority_effect": "NONE",
                    "external_effects": "NONE",
                },
            )
            evidence = TrainingAssignmentEvidence(
                assignment=projection,
                audit_event_id=audit.event_id,
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
            return evidence

    def submit_attempt(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        assignment_id: UUID,
        module_id: str,
        *,
        request: TrainingAttemptRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TrainingAttemptEvidence:
        return _guard(
            lambda: self._submit_attempt(
                tenant_id,
                campaign_id,
                assignment_id,
                module_id,
                request=request,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        )

    def _submit_attempt(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        assignment_id: UUID,
        module_id: str,
        *,
        request: TrainingAttemptRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> TrainingAttemptEvidence:
        digest = canonical_hash(
            {
                "tenant_id": str(tenant_id),
                "campaign_id": str(campaign_id),
                "assignment_id": str(assignment_id),
                "module_id": module_id,
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
                operation=ATTEMPT_OPERATION,
                idempotency_key=idempotency_key,
            )
            replay = _replay(
                session,
                tenant_id=tenant_id,
                operation=ATTEMPT_OPERATION,
                idempotency_key=idempotency_key,
                digest=digest,
                evidence_type=TrainingAttemptEvidence,
            )
            if replay is not None:
                return replay
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            operation_at = audit_lock.acquired_at
            _campaign(session, tenant_id, campaign_id)
            row = _assignment(
                session,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                assignment_id=assignment_id,
                lock=True,
            )
            if row.principal_id != principal_id:
                raise TrainingAccessConflict("Only the assigned learner can submit an attempt")
            progress = _progress(
                session,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                assignment_id=assignment_id,
                module_id=module_id,
                lock=True,
            )
            if request.catalog_digest != row.catalog_digest or row.catalog_digest != CATALOG_DIGEST:
                raise TrainingVersionConflict("Training catalog changed before assessment")
            if row.version != request.expected_assignment_version:
                raise TrainingVersionConflict("Training assignment changed before assessment")
            if progress.version != request.expected_progress_version:
                raise TrainingVersionConflict("Training module changed before assessment")
            if progress.status != "IN_PROGRESS" or row.status == "COMPLETED":
                raise TrainingConflict("Training module cannot be assessed from its current state")
            if progress.attempt_count >= MAX_ATTEMPTS_PER_MODULE:
                raise TrainingLimitConflict("Training module attempt limit reached")
            module = module_by_ref(progress.module_id, progress.module_version)
            if module.status != "APPROVED":
                raise TrainingConflict("Retired training modules cannot receive attempts")
            outcome = grade_attempt(module, locale=request.locale, answers=request.answers)
            progress.attempt_count += 1
            progress.latest_result = outcome.result
            progress.version += 1
            progress.updated_at = operation_at
            receipt_id: UUID | None = None
            if outcome.result == "PASS":
                progress.status = "COMPLETED"
                progress.completed_at = operation_at
                receipt_id = uuid4()
            all_progress = _progress_rows(
                session,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                assignment_id=assignment_id,
                lock=True,
            )
            if all(item.status == "COMPLETED" for item in all_progress):
                row.status = "COMPLETED"
                row.completed_at = operation_at
            else:
                row.status = "IN_PROGRESS"
            row.version += 1
            row.updated_at = operation_at
            session.flush()
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="training.module.attempted",
                resource_type="training_module_progress",
                resource_id=str(progress.id),
                payload={
                    "training_assignment_id": str(assignment_id),
                    "module_id": progress.module_id,
                    "module_version": progress.module_version,
                    "result": outcome.result,
                    "correct_count": outcome.correct_count,
                    "total_questions": outcome.total_questions,
                    "attempt_count": progress.attempt_count,
                    "completion_receipt_id": None if receipt_id is None else str(receipt_id),
                    "catalog_digest": CATALOG_DIGEST,
                    "assignment_version": row.version,
                    "progress_version": progress.version,
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "authority_effect": "NONE",
                    "external_effects": "NONE",
                },
            )
            receipt_row: TrainingCompletionReceipt | None = None
            if receipt_id is not None:
                receipt_row = TrainingCompletionReceipt(
                    id=receipt_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    assignment_id=assignment_id,
                    module_progress_id=progress.id,
                    principal_id=principal_id,
                    module_id=progress.module_id,
                    module_version=progress.module_version,
                    result="PASS",
                    completed_at=operation_at,
                    catalog_digest=CATALOG_DIGEST,
                    audit_event_id=audit.event_id,
                    authority_effect="NONE",
                    external_effects="NONE",
                )
                session.add(receipt_row)
                session.flush()
            projection = _assignment_projection(row, all_progress)
            evidence = TrainingAttemptEvidence(
                assignment=projection,
                outcome=outcome,
                receipt=None if receipt_row is None else _receipt_projection(receipt_row),
                audit_event_id=audit.event_id,
            )
            _store_replay(
                session,
                tenant_id=tenant_id,
                principal_id=principal_id,
                operation=ATTEMPT_OPERATION,
                idempotency_key=idempotency_key,
                request_digest=digest,
                response=evidence,
                created_at=operation_at,
            )
            return evidence

    def list_receipts(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        assignment_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> TrainingReceiptListEvidence:
        return _guard(
            lambda: self._list_receipts(
                tenant_id,
                campaign_id,
                assignment_id,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
            )
        )

    def _list_receipts(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        assignment_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> TrainingReceiptListEvidence:
        with self.database.tenant_transaction(tenant_id) as session:
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            _campaign(session, tenant_id, campaign_id)
            assignment = _assignment(
                session,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                assignment_id=assignment_id,
            )
            if assignment.principal_id != principal_id:
                raise TrainingAccessConflict(
                    "Only the assigned learner can read completion receipts"
                )
            receipts = tuple(
                session.scalars(
                    select(TrainingCompletionReceipt)
                    .where(
                        TrainingCompletionReceipt.tenant_id == tenant_id,
                        TrainingCompletionReceipt.campaign_id == campaign_id,
                        TrainingCompletionReceipt.assignment_id == assignment_id,
                    )
                    .order_by(TrainingCompletionReceipt.completed_at)
                )
            )
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="training.receipts.read",
                resource_type="training_completion_receipt_collection",
                resource_id=str(assignment_id),
                payload={
                    "receipt_count": len(receipts),
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "authority_effect": "NONE",
                },
            )
            return TrainingReceiptListEvidence(
                receipts=tuple(_receipt_projection(row) for row in receipts),
                audit_event_id=audit.event_id,
            )
