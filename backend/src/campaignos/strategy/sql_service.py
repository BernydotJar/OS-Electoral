"""Durable tenant-scoped strategy workspace adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from campaignos.data import Database
from campaignos.data.audit import (
    AuditScopeUnavailable,
    append_audit_event,
    lock_tenant_audit_stream,
)
from campaignos.data.idempotency import lock_idempotency_key
from campaignos.data.models import (
    Campaign,
    CandidateWorkspace,
    IdempotencyRecord,
    OutboxEvent,
    StrategyDecisionReceipt,
    StrategyWorkspace,
    TeamWorkspace,
)
from campaignos.strategy.contracts import (
    StrategyDecision,
    StrategyDecisionEvidence,
    StrategyDecisionRequest,
    StrategyWorkspaceAssessmentInput,
    StrategyWorkspaceCreate,
    StrategyWorkspaceCreateEvidence,
    StrategyWorkspaceProjection,
    StrategyWorkspaceReadEvidence,
    StrategyWorkspaceUpdate,
    StrategyWorkspaceUpdateEvidence,
    assess_strategy_workspace,
)
from campaignos.strategy.service import (
    InMemoryStrategyWorkspaceService,
    StrategyWorkspaceConflict,
    StrategyWorkspaceEvidenceConflict,
    StrategyWorkspaceIdempotencyConflict,
    StrategyWorkspaceNotFound,
    StrategyWorkspacePrerequisiteConflict,
    StrategyWorkspaceUnavailable,
    StrategyWorkspaceVersionConflict,
)

CREATE_OPERATION = "strategy_workspace.create"
UPDATE_OPERATION = "strategy_workspace.update"
DECIDE_OPERATION = "strategy_workspace.decide"


def _as_utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _constraint_name(exc: IntegrityError) -> str | None:
    diagnostic = getattr(exc.orig, "diag", None)
    value = getattr(diagnostic, "constraint_name", None)
    return value if isinstance(value, str) else None


def _campaign_status(value: str) -> Literal["DRAFT", "ACTIVE"]:
    if value not in {"DRAFT", "ACTIVE"}:
        raise StrategyWorkspaceConflict("Campaign is not active for strategy work")
    return cast(Literal["DRAFT", "ACTIVE"], value)


def _role_ids(team: TeamWorkspace) -> tuple[UUID, ...]:
    roles = team.roles or []
    result: list[UUID] = []
    try:
        for role in roles:
            result.append(UUID(str(role["id"])))
    except (KeyError, TypeError, ValueError) as exc:
        raise StrategyWorkspaceUnavailable("Team role evidence is unavailable") from exc
    if not result or len(result) != len(set(result)):
        raise StrategyWorkspaceEvidenceConflict(
            "Strategy workspace requires unique Team Builder roles"
        )
    return tuple(result)


def _load_prerequisites(
    session: Session,
    tenant_id: UUID,
    campaign_id: UUID,
) -> tuple[Campaign, CandidateWorkspace, TeamWorkspace, tuple[UUID, ...]]:
    campaign = session.scalar(
        select(Campaign).where(
            Campaign.tenant_id == tenant_id,
            Campaign.id == campaign_id,
        )
    )
    candidate = session.scalar(
        select(CandidateWorkspace).where(
            CandidateWorkspace.tenant_id == tenant_id,
            CandidateWorkspace.campaign_id == campaign_id,
        )
    )
    team = session.scalar(
        select(TeamWorkspace).where(
            TeamWorkspace.tenant_id == tenant_id,
            TeamWorkspace.campaign_id == campaign_id,
        )
    )
    if campaign is None:
        raise StrategyWorkspaceNotFound("Campaign strategy prerequisites are unavailable")
    if candidate is None or team is None:
        raise StrategyWorkspacePrerequisiteConflict(
            "Candidate and team workspaces are required before strategy"
        )
    _campaign_status(campaign.status)
    return campaign, candidate, team, _role_ids(team)


def _workspace(
    session: Session,
    tenant_id: UUID,
    campaign_id: UUID,
    *,
    for_update: bool = False,
) -> StrategyWorkspace | None:
    statement = select(StrategyWorkspace).where(
        StrategyWorkspace.tenant_id == tenant_id,
        StrategyWorkspace.campaign_id == campaign_id,
    )
    if for_update:
        statement = statement.with_for_update()
    return session.scalar(statement)


def _decision(
    session: Session,
    tenant_id: UUID,
    workspace_id: UUID,
    workspace_version: int,
) -> StrategyDecision | None:
    row = session.scalar(
        select(StrategyDecisionReceipt).where(
            StrategyDecisionReceipt.tenant_id == tenant_id,
            StrategyDecisionReceipt.strategy_workspace_id == workspace_id,
            StrategyDecisionReceipt.workspace_version == workspace_version,
        )
    )
    if row is None:
        return None
    return StrategyDecision(
        id=row.id,
        workspace_version=row.workspace_version,
        selected_option_id=row.selected_option_id,
        reason=row.reason,
        human_role_id=row.human_role_id,
        approval_receipt_id=row.approval_receipt_id,
        decided_at=_as_utc(row.decided_at),
    )


def _assessment(
    session: Session,
    row: StrategyWorkspace,
    campaign: Campaign,
) -> StrategyWorkspaceAssessmentInput:
    return StrategyWorkspaceAssessmentInput.model_validate(
        {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "campaign_id": row.campaign_id,
            "campaign_version": row.campaign_version,
            "campaign_status": _campaign_status(campaign.status),
            "campaign_name": campaign.name,
            "candidate_workspace_version": row.candidate_workspace_version,
            "team_workspace_version": row.team_workspace_version,
            "known_role_ids": tuple(UUID(value) for value in row.known_role_ids),
            "title": row.title,
            "evidence": row.evidence,
            "assumptions": row.assumptions,
            "hypotheses": row.hypotheses,
            "options": row.options,
            "objectives": row.objectives,
            "contradictions": row.contradictions,
            "red_team_findings": row.red_team_findings,
            "decision": _decision(session, row.tenant_id, row.id, row.version),
            "version": row.version,
            "created_at": _as_utc(row.created_at),
            "updated_at": _as_utc(row.updated_at),
        }
    )


def _projection(
    session: Session,
    row: StrategyWorkspace,
    campaign: Campaign,
) -> StrategyWorkspaceProjection:
    try:
        return assess_strategy_workspace(_assessment(session, row, campaign))
    except (ValidationError, ValueError) as exc:
        raise StrategyWorkspaceEvidenceConflict(str(exc)) from exc


def _replay[EvidenceT: BaseModel](
    session: Session,
    *,
    tenant_id: UUID,
    operation: str,
    idempotency_key: str,
    request_digest: str,
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
    if existing.request_digest != request_digest:
        raise StrategyWorkspaceIdempotencyConflict(
            "Idempotency key was already used with different request or authority"
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


def _request_digest(
    *,
    operation: str,
    body: dict[str, object],
    principal_id: UUID,
    authorization_grant_id: UUID,
    approval_receipt_id: str,
    authorization_purpose: str,
) -> str:
    return InMemoryStrategyWorkspaceService._digest(
        operation=operation,
        body=body,
        principal_id=principal_id,
        authorization_grant_id=authorization_grant_id,
        approval_receipt_id=approval_receipt_id,
        authorization_purpose=authorization_purpose,
    )


class SqlAlchemyStrategyWorkspaceService:
    """Durable strategy boundary with exact replay and append-only decisions."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: StrategyWorkspaceCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> StrategyWorkspaceCreateEvidence:
        digest = _request_digest(
            operation=CREATE_OPERATION,
            body=request.model_dump(mode="json"),
            principal_id=principal_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id=approval_receipt_id,
            authorization_purpose=authorization_purpose,
        )
        try:
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
                    request_digest=digest,
                    evidence_type=StrategyWorkspaceCreateEvidence,
                )
                if replay is not None:
                    return replay
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                operation_at = audit_lock.acquired_at
                campaign, candidate, team, role_ids = _load_prerequisites(
                    session, tenant_id, campaign_id
                )
                if _workspace(session, tenant_id, campaign_id, for_update=True) is not None:
                    raise StrategyWorkspaceConflict("Strategy workspace already exists")
                row = StrategyWorkspace(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    campaign_version=campaign.version,
                    candidate_workspace_version=candidate.version,
                    team_workspace_version=team.version,
                    known_role_ids=[str(value) for value in role_ids],
                    title=request.title,
                    evidence=None,
                    assumptions=None,
                    hypotheses=None,
                    options=None,
                    objectives=None,
                    contradictions=None,
                    red_team_findings=None,
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
                    event_type="strategy_workspace.created",
                    resource_type="strategy_workspace",
                    resource_id=str(row.id),
                    payload={
                        "workspace_version": row.version,
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
                        topic="strategy.workspace.created",
                        payload={
                            "strategy_workspace_id": str(row.id),
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
                response = StrategyWorkspaceCreateEvidence(
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
                    response=response,
                    created_at=operation_at,
                )
                session.flush()
                return response
        except StrategyWorkspaceConflict:
            raise
        except IntegrityError as exc:
            if _constraint_name(exc) == "uq_strategy_workspaces_tenant_campaign":
                raise StrategyWorkspaceConflict("Strategy workspace already exists") from exc
            raise StrategyWorkspaceUnavailable("Strategy workspace is unavailable") from exc
        except (
            StrategyWorkspaceEvidenceConflict,
            StrategyWorkspaceIdempotencyConflict,
            StrategyWorkspaceNotFound,
            StrategyWorkspacePrerequisiteConflict,
            StrategyWorkspaceUnavailable,
        ):
            raise
        except (AuditScopeUnavailable, SQLAlchemyError, ValidationError, ValueError) as exc:
            raise StrategyWorkspaceUnavailable("Strategy workspace is unavailable") from exc

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
    ) -> StrategyWorkspaceReadEvidence:
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                campaign = session.scalar(
                    select(Campaign).where(
                        Campaign.tenant_id == tenant_id,
                        Campaign.id == campaign_id,
                    )
                )
                row = _workspace(session, tenant_id, campaign_id)
                if campaign is None or row is None:
                    raise StrategyWorkspaceNotFound("Strategy workspace was not found")
                projection = _projection(session, row, campaign)
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="strategy_workspace.read",
                    resource_type="strategy_workspace",
                    resource_id=str(row.id),
                    payload={
                        "workspace_version": row.version,
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "authority_effect": "NONE",
                        "external_effects": "NONE",
                    },
                )
                response = StrategyWorkspaceReadEvidence(
                    workspace=projection,
                    audit_event_id=audit.event_id,
                )
                session.flush()
                return response
        except (
            StrategyWorkspaceEvidenceConflict,
            StrategyWorkspaceNotFound,
            StrategyWorkspaceUnavailable,
        ):
            raise
        except (AuditScopeUnavailable, SQLAlchemyError, ValidationError, ValueError) as exc:
            raise StrategyWorkspaceUnavailable("Strategy workspace is unavailable") from exc

    def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: StrategyWorkspaceUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> StrategyWorkspaceUpdateEvidence:
        digest = _request_digest(
            operation=UPDATE_OPERATION,
            body={
                "expected_version": expected_version,
                "changes": changes.model_dump(mode="json", exclude_unset=True),
            },
            principal_id=principal_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id=approval_receipt_id,
            authorization_purpose=authorization_purpose,
        )
        try:
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
                    request_digest=digest,
                    evidence_type=StrategyWorkspaceUpdateEvidence,
                )
                if replay is not None:
                    return replay
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                operation_at = audit_lock.acquired_at
                campaign, candidate, team, role_ids = _load_prerequisites(
                    session, tenant_id, campaign_id
                )
                row = _workspace(session, tenant_id, campaign_id, for_update=True)
                if row is None:
                    raise StrategyWorkspaceNotFound("Strategy workspace was not found")
                if row.version != expected_version:
                    raise StrategyWorkspaceVersionConflict("Strategy workspace version is stale")
                previous_version = row.version
                decision_invalidated = (
                    _decision(session, tenant_id, row.id, row.version) is not None
                )
                for field_name, value in changes.model_dump(
                    mode="json", exclude_unset=True
                ).items():
                    setattr(row, field_name, value)
                row.campaign_version = campaign.version
                row.candidate_workspace_version = candidate.version
                row.team_workspace_version = team.version
                row.known_role_ids = [str(value) for value in role_ids]
                row.version += 1
                row.updated_at = operation_at
                session.flush()
                projection = _projection(session, row, campaign)
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="strategy_workspace.updated",
                    resource_type="strategy_workspace",
                    resource_id=str(row.id),
                    payload={
                        "before_version": previous_version,
                        "after_version": row.version,
                        "changed_fields": sorted(changes.model_fields_set),
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "decision_invalidated": decision_invalidated,
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
                        topic="strategy.workspace.updated",
                        payload={
                            "strategy_workspace_id": str(row.id),
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
                response = StrategyWorkspaceUpdateEvidence(
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
                    response=response,
                    created_at=operation_at,
                )
                session.flush()
                return response
        except (
            StrategyWorkspaceEvidenceConflict,
            StrategyWorkspaceIdempotencyConflict,
            StrategyWorkspaceNotFound,
            StrategyWorkspaceUnavailable,
            StrategyWorkspaceVersionConflict,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise StrategyWorkspaceUnavailable("Strategy workspace is unavailable") from exc

    def decide(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        request: StrategyDecisionRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> StrategyDecisionEvidence:
        digest = _request_digest(
            operation=DECIDE_OPERATION,
            body={
                "expected_version": expected_version,
                "request": request.model_dump(mode="json"),
            },
            principal_id=principal_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id=approval_receipt_id,
            authorization_purpose=authorization_purpose,
        )
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                lock_idempotency_key(
                    session,
                    tenant_id=tenant_id,
                    operation=DECIDE_OPERATION,
                    idempotency_key=idempotency_key,
                )
                replay = _replay(
                    session,
                    tenant_id=tenant_id,
                    operation=DECIDE_OPERATION,
                    idempotency_key=idempotency_key,
                    request_digest=digest,
                    evidence_type=StrategyDecisionEvidence,
                )
                if replay is not None:
                    return replay
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                operation_at = audit_lock.acquired_at
                campaign = session.scalar(
                    select(Campaign).where(
                        Campaign.tenant_id == tenant_id,
                        Campaign.id == campaign_id,
                    )
                )
                row = _workspace(session, tenant_id, campaign_id, for_update=True)
                if campaign is None or row is None:
                    raise StrategyWorkspaceNotFound("Strategy workspace was not found")
                if row.version != expected_version:
                    raise StrategyWorkspaceVersionConflict("Strategy workspace version is stale")
                if _decision(session, tenant_id, row.id, row.version) is not None:
                    raise StrategyWorkspaceConflict(
                        "Current strategy workspace version already has a decision"
                    )
                decision = StrategyDecision(
                    id=uuid4(),
                    workspace_version=row.version,
                    selected_option_id=request.selected_option_id,
                    reason=request.reason,
                    human_role_id=request.human_role_id,
                    approval_receipt_id=approval_receipt_id,
                    decided_at=operation_at,
                )
                assessment = _assessment(session, row, campaign).model_copy(
                    update={"decision": decision}
                )
                try:
                    projection = assess_strategy_workspace(assessment)
                except (ValidationError, ValueError) as exc:
                    raise StrategyWorkspaceEvidenceConflict(str(exc)) from exc
                receipt = StrategyDecisionReceipt(
                    id=decision.id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    strategy_workspace_id=row.id,
                    workspace_version=row.version,
                    selected_option_id=request.selected_option_id,
                    human_role_id=request.human_role_id,
                    approval_receipt_id=approval_receipt_id,
                    reason=request.reason,
                    decided_at=operation_at,
                    created_at=operation_at,
                    updated_at=operation_at,
                )
                session.add(receipt)
                session.flush()
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="strategy_workspace.decision_recorded",
                    resource_type="strategy_workspace",
                    resource_id=str(row.id),
                    payload={
                        "workspace_version": row.version,
                        "decision_id": str(decision.id),
                        "selected_option_id": str(request.selected_option_id),
                        "human_role_id": str(request.human_role_id),
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "authority_effect": "INTERNAL_DECISION_ONLY",
                        "external_effects": "NONE",
                    },
                )
                outbox_id = uuid4()
                session.add(
                    OutboxEvent(
                        id=outbox_id,
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        topic="strategy.option.decided",
                        payload={
                            "strategy_workspace_id": str(row.id),
                            "decision_id": str(decision.id),
                            "audit_event_id": str(audit.event_id),
                            "workspace_version": row.version,
                            "selected_option_id": str(request.selected_option_id),
                            "authority_effect": "INTERNAL_DECISION_ONLY",
                            "external_effects": "NONE",
                        },
                        status="PENDING",
                        attempts=0,
                        available_at=operation_at,
                        created_at=operation_at,
                    )
                )
                response = StrategyDecisionEvidence(
                    workspace=projection,
                    decision=decision,
                    audit_event_id=audit.event_id,
                    outbox_event_id=outbox_id,
                )
                _store_replay(
                    session,
                    tenant_id=tenant_id,
                    principal_id=principal_id,
                    operation=DECIDE_OPERATION,
                    idempotency_key=idempotency_key,
                    request_digest=digest,
                    response=response,
                    created_at=operation_at,
                )
                session.flush()
                return response
        except (
            StrategyWorkspaceConflict,
            StrategyWorkspaceEvidenceConflict,
            StrategyWorkspaceIdempotencyConflict,
            StrategyWorkspaceNotFound,
            StrategyWorkspaceUnavailable,
            StrategyWorkspaceVersionConflict,
        ):
            raise
        except IntegrityError as exc:
            if _constraint_name(exc) == "uq_strategy_decisions_workspace_version":
                raise StrategyWorkspaceConflict(
                    "Current strategy workspace version already has a decision"
                ) from exc
            raise StrategyWorkspaceUnavailable("Strategy workspace is unavailable") from exc
        except (AuditScopeUnavailable, SQLAlchemyError, ValidationError, ValueError) as exc:
            raise StrategyWorkspaceUnavailable("Strategy workspace is unavailable") from exc
