"""Exact-authorized campaign strategy workspace endpoints."""

from __future__ import annotations

from typing import Annotated, NoReturn, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

from campaignos.api.dependencies import CurrentTenantAuthorization
from campaignos.api.errors import ProblemException
from campaignos.identity.authorization import (
    EffectivePermissionGrant,
    TenantAuthorizationContext,
)
from campaignos.strategy import (
    StrategyDecisionEvidence,
    StrategyDecisionRequest,
    StrategyWorkspaceCreate,
    StrategyWorkspaceCreateEvidence,
    StrategyWorkspaceReadEvidence,
    StrategyWorkspaceService,
    StrategyWorkspaceUpdate,
    StrategyWorkspaceUpdateEvidence,
)
from campaignos.strategy.service import (
    StrategyWorkspaceConflict,
    StrategyWorkspaceEvidenceConflict,
    StrategyWorkspaceIdempotencyConflict,
    StrategyWorkspaceNotFound,
    StrategyWorkspacePrerequisiteConflict,
    StrategyWorkspaceUnavailable,
    StrategyWorkspaceVersionConflict,
)

router = APIRouter(tags=["strategy workspace"])

CREATE_STRATEGY_PURPOSE = "Create campaign strategy workspace"
READ_STRATEGY_PURPOSE = "Review campaign strategy workspace"
UPDATE_STRATEGY_PURPOSE = "Maintain campaign strategy workspace"
DECIDE_STRATEGY_PURPOSE = "Approve internal campaign strategy option"


def strategy_workspace_service(request: Request) -> StrategyWorkspaceService:
    return cast(StrategyWorkspaceService, request.app.state.strategy_workspace_service)


StrategyWorkspaceServiceDependency = Annotated[
    StrategyWorkspaceService,
    Depends(strategy_workspace_service),
]

StrategyEvidence = (
    StrategyWorkspaceCreateEvidence
    | StrategyWorkspaceReadEvidence
    | StrategyWorkspaceUpdateEvidence
    | StrategyDecisionEvidence
)


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
                resource_type="strategy_workspace",
                resource_id=str(campaign_id),
                purpose=purpose,
                campaign_id=campaign_id,
                workspace_id=None,
            ):
                return grant
    return None


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


def _expected_version(request: Request, value: str | None) -> int:
    values = request.headers.getlist("if-match")
    if len(values) != 1 or value is None:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail=(
                "Exactly one If-Match header with the current strategy "
                "workspace version is required"
            ),
        )
    normalized = value.strip()
    if len(normalized) >= 2 and normalized[0] == normalized[-1] == '"':
        normalized = normalized[1:-1]
    if not normalized.isdigit() or int(normalized) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="If-Match must contain a positive strategy workspace version",
        )
    return int(normalized)


def _raise_strategy_error(exc: Exception) -> NoReturn:
    if isinstance(exc, StrategyWorkspaceIdempotencyConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Idempotency conflict",
            detail="The idempotency key conflicts with an earlier strategy request",
            code="IDEMPOTENCY_CONFLICT",
        ) from exc
    if isinstance(exc, StrategyWorkspacePrerequisiteConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Strategy prerequisites required",
            detail="Candidate and team workspaces are required before strategy work",
            code="STRATEGY_PREREQUISITES_REQUIRED",
        ) from exc
    if isinstance(exc, StrategyWorkspaceConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Strategy workspace conflict",
            detail="The strategy workspace conflicts with the requested operation",
            code="RESOURCE_CONFLICT",
        ) from exc
    if isinstance(exc, StrategyWorkspaceEvidenceConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Strategy evidence conflict",
            detail="Strategy evidence conflicts with deterministic governance rules",
            code="STRATEGY_EVIDENCE_CONFLICT",
        ) from exc
    if isinstance(exc, StrategyWorkspaceVersionConflict):
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Strategy workspace version has changed",
        ) from exc
    if isinstance(exc, StrategyWorkspaceNotFound):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy workspace was not found",
        ) from exc
    if isinstance(exc, StrategyWorkspaceUnavailable):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Strategy workspace is temporarily unavailable",
        ) from exc
    raise exc


def _verify_scope(
    *,
    tenant_id: UUID,
    campaign_id: UUID,
    evidence: StrategyEvidence,
) -> None:
    workspace = evidence.workspace
    if workspace.tenant_id != tenant_id or workspace.campaign_id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Strategy workspace is temporarily unavailable",
        )
    if workspace.authority_effect != "NONE" or workspace.external_effects != "NONE":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Strategy workspace is temporarily unavailable",
        )
    if isinstance(evidence, StrategyDecisionEvidence):
        if evidence.decision.workspace_version != workspace.version:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Strategy workspace is temporarily unavailable",
            )


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


@router.post(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace",
    response_model=StrategyWorkspaceCreateEvidence,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Campaign strategy workspace created",
            "headers": {
                "Location": {"schema": {"type": "string"}},
                "ETag": {"schema": {"type": "string"}},
            },
        }
    },
    summary="Create campaign strategy workspace",
    description=(
        "Creates an internal evidence-first Decision Room. It grants no political, "
        "publication, spending, mobilization, targeting or contact authority."
    ),
)
def create_strategy_workspace(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    payload: StrategyWorkspaceCreate,
    authorization: CurrentTenantAuthorization,
    service: StrategyWorkspaceServiceDependency,
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", description="Required stable creation key"),
    ] = None,
) -> StrategyWorkspaceCreateEvidence:
    grant = _grant_or_forbid(
        authorization,
        campaign_id=campaign_id,
        action="create",
        purpose=CREATE_STRATEGY_PURPOSE,
        detail="Strategy workspace creation is not authorized",
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
        _raise_strategy_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    response.headers["Location"] = request.url.path
    response.headers["ETag"] = f'"{evidence.workspace.version}"'
    return evidence


@router.get(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace",
    response_model=StrategyWorkspaceReadEvidence,
    responses={status.HTTP_200_OK: {"headers": {"ETag": {"schema": {"type": "string"}}}}},
    summary="Read campaign strategy workspace",
)
def get_strategy_workspace(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    authorization: CurrentTenantAuthorization,
    service: StrategyWorkspaceServiceDependency,
) -> StrategyWorkspaceReadEvidence:
    grant = _grant_or_forbid(
        authorization,
        campaign_id=campaign_id,
        action="read",
        purpose=READ_STRATEGY_PURPOSE,
        detail="Strategy workspace read is not authorized",
    )
    try:
        evidence = service.get(
            tenant_id,
            campaign_id,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=getattr(request.state, "correlation_id", "unknown"),
        )
    except Exception as exc:
        _raise_strategy_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    response.headers["ETag"] = f'"{evidence.workspace.version}"'
    return evidence


@router.patch(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace",
    response_model=StrategyWorkspaceUpdateEvidence,
    responses={status.HTTP_200_OK: {"headers": {"ETag": {"schema": {"type": "string"}}}}},
    summary="Update campaign strategy workspace",
)
def update_strategy_workspace(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    changes: StrategyWorkspaceUpdate,
    authorization: CurrentTenantAuthorization,
    service: StrategyWorkspaceServiceDependency,
    if_match: Annotated[
        str | None,
        Header(alias="If-Match", description="Required current workspace version"),
    ] = None,
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", description="Required stable update key"),
    ] = None,
) -> StrategyWorkspaceUpdateEvidence:
    grant = _grant_or_forbid(
        authorization,
        campaign_id=campaign_id,
        action="update",
        purpose=UPDATE_STRATEGY_PURPOSE,
        detail="Strategy workspace update is not authorized",
    )
    expected_version = _expected_version(request, if_match)
    try:
        evidence = service.update(
            tenant_id,
            campaign_id,
            expected_version=expected_version,
            changes=changes,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=getattr(request.state, "correlation_id", "unknown"),
            idempotency_key=_required_idempotency_key(request, idempotency_key),
        )
    except Exception as exc:
        _raise_strategy_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    if evidence.workspace.version != expected_version + 1:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Strategy workspace is temporarily unavailable",
        )
    response.headers["ETag"] = f'"{evidence.workspace.version}"'
    return evidence


@router.post(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace/decision",
    response_model=StrategyDecisionEvidence,
    summary="Record an internal human strategy decision",
    description=(
        "Records an append-only human choice for the exact workspace version. "
        "Acceptance remains internal and authorizes no publication, targeting, "
        "contact, spending or mobilization."
    ),
)
def decide_strategy_workspace(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    payload: StrategyDecisionRequest,
    authorization: CurrentTenantAuthorization,
    service: StrategyWorkspaceServiceDependency,
    if_match: Annotated[
        str | None,
        Header(alias="If-Match", description="Required current workspace version"),
    ] = None,
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", description="Required stable decision key"),
    ] = None,
) -> StrategyDecisionEvidence:
    grant = _grant_or_forbid(
        authorization,
        campaign_id=campaign_id,
        action="approve",
        purpose=DECIDE_STRATEGY_PURPOSE,
        detail="Internal strategy decision is not authorized",
    )
    expected_version = _expected_version(request, if_match)
    try:
        evidence = service.decide(
            tenant_id,
            campaign_id,
            expected_version=expected_version,
            request=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=getattr(request.state, "correlation_id", "unknown"),
            idempotency_key=_required_idempotency_key(request, idempotency_key),
        )
    except Exception as exc:
        _raise_strategy_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    if evidence.workspace.version != expected_version:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Strategy workspace is temporarily unavailable",
        )
    response.headers["ETag"] = f'"{evidence.workspace.version}"'
    return evidence
