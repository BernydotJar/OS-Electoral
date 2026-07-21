"""Tenant-scoped persistent governed recommendation run adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from campaignos.agents.contracts import (
    OUTPUT_SCHEMA_VERSION,
    POLICY_ID,
    POLICY_VERSION,
    PROMPT_TEMPLATE_VERSIONS,
    AgentEvidenceItem,
    AgentOptionContext,
    AgentRunCreateEvidence,
    AgentRunProjection,
    AgentRunReadEvidence,
    AgentRunRequest,
    AgentStrategyContext,
)
from campaignos.agents.runtime import AgentRuntime, canonical_digest
from campaignos.agents.service import (
    AgentRunIdempotencyConflict,
    AgentRunNotFound,
    AgentRunStrategyConflict,
    AgentRunUnavailable,
)
from campaignos.data import Database
from campaignos.data.audit import (
    AuditScopeUnavailable,
    append_audit_event,
    lock_tenant_audit_stream,
)
from campaignos.data.idempotency import lock_idempotency_key
from campaignos.data.models import (
    AgentRun,
    Campaign,
    IdempotencyRecord,
    OutboxEvent,
    StrategyDecisionReceipt,
    StrategyWorkspace,
)
from campaignos.strategy.contracts import (
    StrategyDecision,
    StrategyWorkspaceAssessmentInput,
    StrategyWorkspaceProjection,
    assess_strategy_workspace,
)

CREATE_OPERATION = "agent_run.create"


def _as_utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _campaign_status(value: str) -> Literal["DRAFT", "ACTIVE"]:
    if value not in {"DRAFT", "ACTIVE"}:
        raise AgentRunStrategyConflict("Campaign is not eligible for agent recommendations")
    return cast(Literal["DRAFT", "ACTIVE"], value)


def _decision(
    session: Session,
    tenant_id: UUID,
    workspace_id: UUID,
    version: int,
) -> StrategyDecision | None:
    row = session.scalar(
        select(StrategyDecisionReceipt).where(
            StrategyDecisionReceipt.tenant_id == tenant_id,
            StrategyDecisionReceipt.strategy_workspace_id == workspace_id,
            StrategyDecisionReceipt.workspace_version == version,
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


def _strategy_projection(
    session: Session,
    row: StrategyWorkspace,
    campaign: Campaign,
) -> StrategyWorkspaceProjection:
    try:
        value = StrategyWorkspaceAssessmentInput.model_validate(
            {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "campaign_id": row.campaign_id,
                "campaign_version": row.campaign_version,
                "campaign_status": _campaign_status(campaign.status),
                "campaign_name": campaign.name,
                "candidate_workspace_version": row.candidate_workspace_version,
                "team_workspace_version": row.team_workspace_version,
                "known_role_ids": tuple(UUID(item) for item in row.known_role_ids),
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
        return assess_strategy_workspace(value)
    except (ValidationError, ValueError) as exc:
        raise AgentRunStrategyConflict("Strategy evidence is not eligible") from exc


def _strategy_context(projection: StrategyWorkspaceProjection) -> AgentStrategyContext:
    if projection.status not in {"READY_FOR_HUMAN_DECISION", "DECIDED_INTERNAL"}:
        raise AgentRunStrategyConflict(
            "Strategy workspace is not eligible for agent recommendations"
        )
    evidence = tuple(
        AgentEvidenceItem(
            id=item.id,
            classification=item.classification,
            status=item.status,
            statement=item.statement,
            source_reference=item.source_reference,
        )
        for item in (projection.evidence or ())
        if item.status != "REJECTED"
    )
    options = tuple(
        AgentOptionContext(
            id=item.id,
            title=item.title,
            summary=item.summary,
            evidence_refs=item.evidence_refs,
        )
        for item in (projection.options or ())
    )
    return AgentStrategyContext(
        workspace_id=projection.id,
        tenant_id=projection.tenant_id,
        campaign_id=projection.campaign_id,
        workspace_version=projection.version,
        status=cast(Literal["READY_FOR_HUMAN_DECISION", "DECIDED_INTERNAL"], projection.status),
        evidence=evidence,
        options=options,
        limitation_codes=projection.limitation_codes,
    )


def _run_projection(row: AgentRun) -> AgentRunProjection:
    return AgentRunProjection.model_validate(
        {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "campaign_id": row.campaign_id,
            "strategy_workspace_id": row.strategy_workspace_id,
            "strategy_workspace_version": row.strategy_workspace_version,
            "purpose": row.purpose,
            "instruction_digest": row.instruction_digest,
            "policy_id": row.policy_id,
            "policy_version": row.policy_version,
            "prompt_template_id": row.prompt_template_id,
            "prompt_template_version": row.prompt_template_version,
            "output_schema_version": row.output_schema_version,
            "prompt_digest": row.prompt_digest,
            "provider": row.provider,
            "model": row.model,
            "status": row.status,
            "refusal_code": row.refusal_code,
            "refusal_detail": row.refusal_detail,
            "recommendation": row.recommendation,
            "evidence_refs": tuple(UUID(value) for value in row.evidence_refs),
            "option_refs": tuple(UUID(value) for value in row.option_refs),
            "prompt_tokens": row.prompt_tokens,
            "output_tokens": row.output_tokens,
            "latency_ms": row.latency_ms,
            "cost_micros": row.cost_micros,
            "human_disposition": row.human_disposition,
            "authority_effect": row.authority_effect,
            "external_effects": row.external_effects,
            "created_at": _as_utc(row.created_at),
        }
    )


def _replay[EvidenceT: BaseModel](
    session: Session,
    *,
    tenant_id: UUID,
    idempotency_key: str,
    request_digest: str,
    evidence_type: type[EvidenceT],
) -> EvidenceT | None:
    existing = session.scalar(
        select(IdempotencyRecord)
        .where(
            IdempotencyRecord.tenant_id == tenant_id,
            IdempotencyRecord.operation == CREATE_OPERATION,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
        .with_for_update()
    )
    if existing is None:
        return None
    if existing.request_digest != request_digest:
        raise AgentRunIdempotencyConflict(
            "Idempotency key was already used with different request or authority"
        )
    return evidence_type.model_validate(existing.response_payload)


def _store_replay(
    session: Session,
    *,
    tenant_id: UUID,
    principal_id: UUID,
    idempotency_key: str,
    request_digest: str,
    response: BaseModel,
    created_at: datetime,
) -> None:
    session.add(
        IdempotencyRecord(
            tenant_id=tenant_id,
            principal_id=principal_id,
            operation=CREATE_OPERATION,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            response_payload=response.model_dump(mode="json"),
            created_at=created_at,
        )
    )


def _request_digest(
    *,
    request: AgentRunRequest,
    principal_id: UUID,
    authorization_grant_id: UUID,
    approval_receipt_id: str,
    authorization_purpose: str,
) -> str:
    return canonical_digest(
        {
            "operation": CREATE_OPERATION,
            "request": request.model_dump(mode="json"),
            "principal_id": str(principal_id),
            "authorization_grant_id": str(authorization_grant_id),
            "approval_receipt_id": approval_receipt_id,
            "authorization_purpose": authorization_purpose,
        }
    )


class SqlAlchemyAgentRunService:
    """Persist one no-effect recommendation or refusal under exact Strategy scope."""

    def __init__(self, database: Database, runtime: AgentRuntime) -> None:
        self.database = database
        self.runtime = runtime

    def create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: AgentRunRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> AgentRunCreateEvidence:
        digest = _request_digest(
            request=request,
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
                    idempotency_key=idempotency_key,
                    request_digest=digest,
                    evidence_type=AgentRunCreateEvidence,
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
                workspace = session.scalar(
                    select(StrategyWorkspace)
                    .where(
                        StrategyWorkspace.tenant_id == tenant_id,
                        StrategyWorkspace.campaign_id == campaign_id,
                    )
                    .with_for_update()
                )
                if campaign is None or workspace is None:
                    raise AgentRunNotFound("Strategy workspace was not found")
                if workspace.version != request.strategy_workspace_version:
                    raise AgentRunStrategyConflict("Strategy workspace version is stale")
                context = _strategy_context(_strategy_projection(session, workspace, campaign))
                result = self.runtime.execute(context, request)
                template_id, template_version = PROMPT_TEMPLATE_VERSIONS[request.purpose]
                run_id = uuid4()
                recommendation = (
                    result.recommendation.model_dump(mode="json")
                    if result.recommendation is not None
                    else None
                )
                row = AgentRun(
                    id=run_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    strategy_workspace_id=context.workspace_id,
                    strategy_workspace_version=context.workspace_version,
                    principal_id=principal_id,
                    purpose=request.purpose,
                    instruction_digest=canonical_digest(request.instruction),
                    policy_id=POLICY_ID,
                    policy_version=POLICY_VERSION,
                    prompt_template_id=template_id,
                    prompt_template_version=template_version,
                    output_schema_version=OUTPUT_SCHEMA_VERSION,
                    prompt_digest=result.prompt_digest,
                    provider=result.provider,
                    model=result.model,
                    status=result.status,
                    refusal_code=result.refusal_code,
                    refusal_detail=result.refusal_detail,
                    recommendation=recommendation,
                    evidence_refs=[str(item.id) for item in context.evidence],
                    option_refs=[str(item.id) for item in context.options],
                    prompt_tokens=result.prompt_tokens,
                    output_tokens=result.output_tokens,
                    latency_ms=result.latency_ms,
                    cost_micros=result.cost_micros,
                    human_disposition="PENDING",
                    authority_effect="NONE",
                    external_effects="NONE",
                    created_at=operation_at,
                )
                session.add(row)
                session.flush()
                projection = _run_projection(row)
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="agent.run.recorded",
                    resource_type="agent_run",
                    resource_id=str(run_id),
                    payload={
                        "strategy_workspace_id": str(context.workspace_id),
                        "strategy_workspace_version": context.workspace_version,
                        "status": result.status,
                        "refusal_code": result.refusal_code,
                        "provider": result.provider,
                        "model": result.model,
                        "prompt_digest": result.prompt_digest,
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "human_disposition": "PENDING",
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
                        topic="agent.run.recorded",
                        payload={
                            "agent_run_id": str(run_id),
                            "audit_event_id": str(audit.event_id),
                            "tenant_id": str(tenant_id),
                            "campaign_id": str(campaign_id),
                            "version": context.workspace_version,
                            "status": result.status,
                            "human_disposition": "PENDING",
                            "authority_effect": "NONE",
                            "external_effects": "NONE",
                        },
                        status="PENDING",
                        attempts=0,
                        available_at=operation_at,
                        created_at=operation_at,
                    )
                )
                response = AgentRunCreateEvidence(
                    run=projection,
                    audit_event_id=audit.event_id,
                    outbox_event_id=outbox_id,
                )
                _store_replay(
                    session,
                    tenant_id=tenant_id,
                    principal_id=principal_id,
                    idempotency_key=idempotency_key,
                    request_digest=digest,
                    response=response,
                    created_at=operation_at,
                )
                session.flush()
                return response
        except (
            AgentRunIdempotencyConflict,
            AgentRunNotFound,
            AgentRunStrategyConflict,
            AgentRunUnavailable,
        ):
            raise
        except (AuditScopeUnavailable, SQLAlchemyError, ValidationError, ValueError) as exc:
            raise AgentRunUnavailable("Agent run service is unavailable") from exc

    def get(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        run_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> AgentRunReadEvidence:
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                row = session.scalar(
                    select(AgentRun).where(
                        AgentRun.tenant_id == tenant_id,
                        AgentRun.campaign_id == campaign_id,
                        AgentRun.id == run_id,
                    )
                )
                if row is None:
                    raise AgentRunNotFound("Agent run was not found")
                projection = _run_projection(row)
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="agent_run.read",
                    resource_type="agent_run",
                    resource_id=str(run_id),
                    payload={
                        "strategy_workspace_id": str(row.strategy_workspace_id),
                        "strategy_workspace_version": row.strategy_workspace_version,
                        "status": row.status,
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "human_disposition": "PENDING",
                        "authority_effect": "NONE",
                        "external_effects": "NONE",
                    },
                )
                response = AgentRunReadEvidence(run=projection, audit_event_id=audit.event_id)
                session.flush()
                return response
        except (AgentRunNotFound, AgentRunUnavailable):
            raise
        except (AuditScopeUnavailable, SQLAlchemyError, ValidationError, ValueError) as exc:
            raise AgentRunUnavailable("Agent run service is unavailable") from exc
