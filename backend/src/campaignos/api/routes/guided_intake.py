"""Exact-authorized guided campaign intake endpoints."""

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
from campaignos.onboarding import (
    GuidedIntakeReadEvidence,
    GuidedIntakeService,
    GuidedIntakeStartEvidence,
    GuidedIntakeUpdate,
    GuidedIntakeUpdateEvidence,
)
from campaignos.onboarding.service import (
    GuidedIntakeIdempotencyConflict,
    GuidedIntakeNotFound,
    GuidedIntakePrerequisiteConflict,
    GuidedIntakeUnavailable,
    GuidedIntakeVersionConflict,
)

router = APIRouter(tags=["guided intake"])

START_GUIDED_INTAKE_PURPOSE = "Begin guided campaign intake"
READ_GUIDED_INTAKE_PURPOSE = "Review guided campaign intake"
UPDATE_GUIDED_INTAKE_PURPOSE = "Maintain guided campaign intake"


def guided_intake_service(request: Request) -> GuidedIntakeService:
    return cast(GuidedIntakeService, request.app.state.guided_intake_service)


GuidedIntakeServiceDependency = Annotated[GuidedIntakeService, Depends(guided_intake_service)]


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
                resource_type="guided_intake",
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
            detail="Exactly one If-Match header with the current intake version is required",
        )
    normalized = value.strip()
    if len(normalized) >= 2 and normalized[0] == normalized[-1] == '"':
        normalized = normalized[1:-1]
    if not normalized.isdigit() or int(normalized) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="If-Match must contain a positive guided intake version",
        )
    return int(normalized)


def _raise_intake_error(exc: Exception) -> NoReturn:
    if isinstance(exc, GuidedIntakeIdempotencyConflict):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key conflicts with a previous request",
        ) from exc
    if isinstance(exc, GuidedIntakePrerequisiteConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Campaign not ready",
            detail="Campaign operational setup must be completed before guided intake",
            code="CAMPAIGN_NOT_READY",
        ) from exc
    if isinstance(exc, GuidedIntakeVersionConflict):
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Guided intake version has changed",
        ) from exc
    if isinstance(exc, GuidedIntakeNotFound):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guided intake was not found",
        ) from exc
    if isinstance(exc, GuidedIntakeUnavailable):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Guided intake is temporarily unavailable",
        ) from exc
    raise exc


def _verify_scope(
    *,
    tenant_id: UUID,
    campaign_id: UUID,
    evidence: GuidedIntakeStartEvidence | GuidedIntakeReadEvidence | GuidedIntakeUpdateEvidence,
) -> None:
    if evidence.intake.tenant_id != tenant_id or evidence.intake.campaign_id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Guided intake is temporarily unavailable",
        )


@router.post(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/guided-intake",
    response_model=GuidedIntakeStartEvidence,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_200_OK: {
            "description": "Existing guided intake resumed",
            "headers": {
                "Location": {"schema": {"type": "string"}},
                "ETag": {"schema": {"type": "string"}},
            },
        },
        status.HTTP_201_CREATED: {
            "description": "Guided intake created",
            "headers": {
                "Location": {"schema": {"type": "string"}},
                "ETag": {"schema": {"type": "string"}},
            },
        },
    },
    summary="Start or resume guided campaign intake",
    description=(
        "Creates or resumes one tenant/campaign intake with audit and internal no-effect "
        "evidence. It does not generate strategy, approve a candidate or trigger outreach."
    ),
)
def start_guided_intake(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    authorization: CurrentTenantAuthorization,
    service: GuidedIntakeServiceDependency,
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description="Required stable key for one guided-intake start or resume intent",
        ),
    ] = None,
) -> GuidedIntakeStartEvidence:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action="create",
        purpose=START_GUIDED_INTAKE_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guided intake start is not authorized",
        )
    try:
        evidence = service.start(
            tenant_id,
            campaign_id,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=getattr(request.state, "correlation_id", "unknown"),
            idempotency_key=_required_idempotency_key(request, idempotency_key),
        )
    except (
        GuidedIntakeIdempotencyConflict,
        GuidedIntakeNotFound,
        GuidedIntakePrerequisiteConflict,
        GuidedIntakeUnavailable,
    ) as exc:
        _raise_intake_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    response.status_code = status.HTTP_201_CREATED if evidence.created else status.HTTP_200_OK
    response.headers["Location"] = request.url.path
    response.headers["ETag"] = f'"{evidence.intake.version}"'
    return evidence


@router.get(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/guided-intake",
    response_model=GuidedIntakeReadEvidence,
    responses={status.HTTP_200_OK: {"headers": {"ETag": {"schema": {"type": "string"}}}}},
    summary="Read guided campaign intake",
)
def get_guided_intake(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    authorization: CurrentTenantAuthorization,
    service: GuidedIntakeServiceDependency,
) -> GuidedIntakeReadEvidence:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action="read",
        purpose=READ_GUIDED_INTAKE_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guided intake read is not authorized",
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
    except (GuidedIntakeNotFound, GuidedIntakeUnavailable) as exc:
        _raise_intake_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    response.headers["ETag"] = f'"{evidence.intake.version}"'
    return evidence


@router.patch(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/guided-intake",
    response_model=GuidedIntakeUpdateEvidence,
    responses={status.HTTP_200_OK: {"headers": {"ETag": {"schema": {"type": "string"}}}}},
    summary="Update guided campaign intake",
)
def update_guided_intake(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    changes: GuidedIntakeUpdate,
    authorization: CurrentTenantAuthorization,
    service: GuidedIntakeServiceDependency,
    if_match: Annotated[
        str | None,
        Header(
            alias="If-Match",
            description="Required quoted optimistic-concurrency version",
        ),
    ] = None,
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description="Required stable key for one guided-intake update intent",
        ),
    ] = None,
) -> GuidedIntakeUpdateEvidence:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action="update",
        purpose=UPDATE_GUIDED_INTAKE_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guided intake update is not authorized",
        )
    try:
        evidence = service.update(
            tenant_id,
            campaign_id,
            expected_version=_expected_version(request, if_match),
            changes=changes,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=getattr(request.state, "correlation_id", "unknown"),
            idempotency_key=_required_idempotency_key(request, idempotency_key),
        )
    except (
        GuidedIntakeIdempotencyConflict,
        GuidedIntakeNotFound,
        GuidedIntakeUnavailable,
        GuidedIntakeVersionConflict,
    ) as exc:
        _raise_intake_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    if evidence.intake.version != _expected_version(request, if_match) + 1:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Guided intake is temporarily unavailable",
        )
    response.headers["ETag"] = f'"{evidence.intake.version}"'
    return evidence
