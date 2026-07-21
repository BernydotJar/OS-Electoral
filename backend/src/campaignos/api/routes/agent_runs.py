"""Exact-authorized governed internal recommendation run endpoints."""

from __future__ import annotations

from typing import Annotated, NoReturn, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

from campaignos.agents import (
    AgentRunCreateEvidence,
    AgentRunReadEvidence,
    AgentRunRequest,
    AgentRunService,
)
from campaignos.agents.service import (
    AgentRunIdempotencyConflict,
    AgentRunNotFound,
    AgentRunStrategyConflict,
    AgentRunUnavailable,
)
from campaignos.api.dependencies import CurrentTenantAuthorization
from campaignos.api.errors import ProblemException
from campaignos.identity.authorization import (
    EffectivePermissionGrant,
    TenantAuthorizationContext,
)

router = APIRouter(tags=["governed agent runs"])

CREATE_AGENT_RUN_PURPOSE = "Create internal governed recommendation run"
READ_AGENT_RUN_PURPOSE = "Review internal governed recommendation run"


def agent_run_service(request: Request) -> AgentRunService:
    return cast(AgentRunService, request.app.state.agent_run_service)


AgentRunServiceDependency = Annotated[AgentRunService, Depends(agent_run_service)]
AgentRunEvidence = AgentRunCreateEvidence | AgentRunReadEvidence


def _exact_grant(
    authorization: TenantAuthorizationContext,
    *,
    campaign_id: UUID,
    action: str,
    purpose: str,
) -> EffectivePermissionGrant | None:
    for membership in authorization.memberships:
        for grant in membership.grants:
            if grant.permits(
                action=action,
                resource_type="agent_run",
                resource_id=str(campaign_id),
                purpose=purpose,
                campaign_id=campaign_id,
                workspace_id=None,
            ):
                return grant
    return None


def _grant_or_forbid(
    authorization: TenantAuthorizationContext,
    *,
    campaign_id: UUID,
    action: str,
    purpose: str,
    detail: str,
) -> EffectivePermissionGrant:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action=action,
        purpose=purpose,
    )
    if grant is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
    return grant


def _required_idempotency_key(request: Request, value: str | None) -> str:
    values = request.headers.getlist("idempotency-key")
    if len(values) != 1 or value is None or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Exactly one non-empty Idempotency-Key header is required",
        )
    normalized = value.strip()
    if len(normalized) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must not exceed 255 characters",
        )
    return normalized


def _raise_agent_error(exc: Exception) -> NoReturn:
    if isinstance(exc, AgentRunIdempotencyConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Idempotency conflict",
            detail="The idempotency key conflicts with an earlier agent run request",
            code="IDEMPOTENCY_CONFLICT",
        ) from exc
    if isinstance(exc, AgentRunStrategyConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Strategy snapshot conflict",
            detail="The exact Strategy snapshot is stale or not eligible",
            code="AGENT_STRATEGY_CONFLICT",
        ) from exc
    if isinstance(exc, AgentRunNotFound):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run was not found",
        ) from exc
    if isinstance(exc, AgentRunUnavailable):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent run service is temporarily unavailable",
        ) from exc
    raise exc


def _verify_scope(
    *,
    tenant_id: UUID,
    campaign_id: UUID,
    evidence: AgentRunEvidence,
) -> None:
    run = evidence.run
    if run.tenant_id != tenant_id or run.campaign_id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent run service is temporarily unavailable",
        )
    if (
        run.human_disposition != "PENDING"
        or run.authority_effect != "NONE"
        or run.external_effects != "NONE"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent run service is temporarily unavailable",
        )


@router.post(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/agent-runs",
    response_model=AgentRunCreateEvidence,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Internal governed recommendation run recorded",
            "headers": {"Location": {"schema": {"type": "string"}}},
        }
    },
    summary="Create an internal governed recommendation run",
    description=(
        "Records a structured recommendation or deterministic refusal for human review. "
        "Tools, network access, publication, targeting, contact, spending, grant changes, "
        "deployment and mobilization are disabled."
    ),
)
def create_agent_run(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    payload: AgentRunRequest,
    authorization: CurrentTenantAuthorization,
    service: AgentRunServiceDependency,
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", description="Required stable agent run key"),
    ] = None,
) -> AgentRunCreateEvidence:
    grant = _grant_or_forbid(
        authorization,
        campaign_id=campaign_id,
        action="create",
        purpose=CREATE_AGENT_RUN_PURPOSE,
        detail="Agent run creation is not authorized",
    )
    try:
        evidence = service.create(
            tenant_id,
            campaign_id,
            request=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=getattr(request.state, "correlation_id", "unknown"),
            idempotency_key=_required_idempotency_key(request, idempotency_key),
        )
    except Exception as exc:
        _raise_agent_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    response.headers["Location"] = f"{request.url.path}/{evidence.run.id}"
    return evidence


@router.get(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/agent-runs/{run_id}",
    response_model=AgentRunReadEvidence,
    summary="Read an internal governed recommendation run",
)
def get_agent_run(
    request: Request,
    tenant_id: UUID,
    campaign_id: UUID,
    run_id: UUID,
    authorization: CurrentTenantAuthorization,
    service: AgentRunServiceDependency,
) -> AgentRunReadEvidence:
    grant = _grant_or_forbid(
        authorization,
        campaign_id=campaign_id,
        action="read",
        purpose=READ_AGENT_RUN_PURPOSE,
        detail="Agent run read is not authorized",
    )
    try:
        evidence = service.get(
            tenant_id,
            campaign_id,
            run_id,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=getattr(request.state, "correlation_id", "unknown"),
        )
    except Exception as exc:
        _raise_agent_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    return evidence
