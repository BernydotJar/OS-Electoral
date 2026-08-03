"""Exact-authorized governed Training Academy endpoints."""

from __future__ import annotations

from typing import Annotated, NoReturn, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status

from campaignos.api.dependencies import CurrentTenantAuthorization
from campaignos.api.errors import ProblemException
from campaignos.api.rate_limits import enforce_rate_limit, rate_limit_policy
from campaignos.identity.authorization import EffectivePermissionGrant, TenantAuthorizationContext
from campaignos.security import RateLimitPolicyClass
from campaignos.training.contracts import (
    Locale,
    TrainingAssignmentCreate,
    TrainingAssignmentCreateEvidence,
    TrainingAssignmentEvidence,
    TrainingAssignmentListEvidence,
    TrainingAttemptEvidence,
    TrainingAttemptRequest,
    TrainingCatalogProjection,
    TrainingModuleStartRequest,
    TrainingReceiptListEvidence,
)
from campaignos.training.service import (
    TrainingAccessConflict,
    TrainingConflict,
    TrainingIdempotencyConflict,
    TrainingLimitConflict,
    TrainingNotFound,
    TrainingService,
    TrainingUnavailable,
    TrainingVersionConflict,
)

router = APIRouter(tags=["training academy"])
CATALOG_PURPOSE = "Review approved training catalog"
SELF_READ_PURPOSE = "Review own campaign training"
SELF_COMPLETE_PURPOSE = "Complete assigned campaign training"
MANAGE_PURPOSE = "Assign campaign learning path"
ADMIN_READ_PURPOSE = "Review campaign training assignment"


def training_service(request: Request) -> TrainingService:
    return cast(TrainingService, request.app.state.training_service)


TrainingServiceDependency = Annotated[TrainingService, Depends(training_service)]


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
                resource_type="training_academy",
                resource_id=str(campaign_id),
                purpose=purpose,
                campaign_id=campaign_id,
                workspace_id=None,
            ):
                return grant
    return None


def _require_grant(
    authorization: TenantAuthorizationContext,
    *,
    campaign_id: UUID,
    action: str,
    purpose: str,
) -> EffectivePermissionGrant:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action=action,
        purpose=purpose,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Training Academy operation is not authorized",
        )
    return grant


def _idempotency_key(request: Request, value: str | None) -> str:
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


def _correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", "unknown"))


def _raise_training_error(exc: Exception) -> NoReturn:
    if isinstance(exc, TrainingIdempotencyConflict):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key conflicts with a previous training request",
        ) from exc
    if isinstance(exc, TrainingVersionConflict):
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Training assignment, module, or catalog version has changed",
        ) from exc
    if isinstance(exc, TrainingLimitConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Training limit reached",
            detail="The bounded Training Academy limit has been reached",
            code="TRAINING_LIMIT_REACHED",
        ) from exc
    if isinstance(exc, (TrainingConflict, TrainingAccessConflict)):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Training state conflict",
            detail="The training operation conflicts with the current assignment state",
            code="TRAINING_STATE_CONFLICT",
        ) from exc
    if isinstance(exc, TrainingNotFound):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training resource was not found",
        ) from exc
    if isinstance(exc, TrainingUnavailable):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Training Academy is temporarily unavailable",
        ) from exc
    raise exc


def _verify_assignment_scope(
    *,
    tenant_id: UUID,
    campaign_id: UUID,
    evidence: TrainingAssignmentEvidence
    | TrainingAssignmentCreateEvidence
    | TrainingAttemptEvidence,
    expected_principal_id: UUID | None = None,
) -> None:
    assignment = evidence.assignment
    if assignment.tenant_id != tenant_id or assignment.campaign_id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Training Academy is temporarily unavailable",
        )
    if expected_principal_id is not None and assignment.principal_id != expected_principal_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Training Academy is temporarily unavailable",
        )
    if assignment.authority_effect != "NONE" or assignment.external_effects != "NONE":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Training Academy is temporarily unavailable",
        )


@router.get(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/training/catalog",
    response_model=TrainingCatalogProjection,
    summary="Read approved Training Academy catalog",
)
@rate_limit_policy(RateLimitPolicyClass.EXPENSIVE_READ)
def get_training_catalog(
    request: Request,
    tenant_id: UUID,
    campaign_id: UUID,
    authorization: CurrentTenantAuthorization,
    service: TrainingServiceDependency,
    locale: Annotated[Locale, Query()] = "es",
) -> TrainingCatalogProjection:
    _require_grant(
        authorization,
        campaign_id=campaign_id,
        action="training.catalog.read",
        purpose=CATALOG_PURPOSE,
    )
    enforce_rate_limit(
        request,
        tenant_id=tenant_id,
        principal_id=authorization.principal_id,
        policy_class=RateLimitPolicyClass.EXPENSIVE_READ,
    )
    try:
        projection = service.catalog(locale)
    except TrainingUnavailable as exc:
        _raise_training_error(exc)
    if (
        projection.locale != locale
        or projection.authority_effect != "NONE"
        or projection.external_effects != "NONE"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Training Academy is temporarily unavailable",
        )
    return projection


@router.get(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/training/me",
    response_model=TrainingAssignmentListEvidence,
    summary="Read current principal training assignments",
)
@rate_limit_policy(RateLimitPolicyClass.EXPENSIVE_READ)
def get_own_training_assignments(
    request: Request,
    tenant_id: UUID,
    campaign_id: UUID,
    authorization: CurrentTenantAuthorization,
    service: TrainingServiceDependency,
) -> TrainingAssignmentListEvidence:
    grant = _require_grant(
        authorization,
        campaign_id=campaign_id,
        action="training.self.read",
        purpose=SELF_READ_PURPOSE,
    )
    enforce_rate_limit(
        request,
        tenant_id=tenant_id,
        principal_id=authorization.principal_id,
        policy_class=RateLimitPolicyClass.EXPENSIVE_READ,
    )
    try:
        evidence = service.list_self(
            tenant_id,
            campaign_id,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
        )
    except (TrainingNotFound, TrainingUnavailable) as exc:
        _raise_training_error(exc)
    if evidence.authority_effect != "NONE" or any(
        item.tenant_id != tenant_id
        or item.campaign_id != campaign_id
        or item.principal_id != authorization.principal_id
        or item.authority_effect != "NONE"
        or item.external_effects != "NONE"
        for item in evidence.assignments
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Training Academy is temporarily unavailable",
        )
    return evidence


@router.post(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/training/assignments",
    response_model=TrainingAssignmentCreateEvidence,
    status_code=status.HTTP_201_CREATED,
    summary="Assign an approved campaign learning path",
)
@rate_limit_policy(RateLimitPolicyClass.MUTATION)
def create_training_assignment(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    payload: TrainingAssignmentCreate,
    authorization: CurrentTenantAuthorization,
    service: TrainingServiceDependency,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> TrainingAssignmentCreateEvidence:
    grant = _require_grant(
        authorization,
        campaign_id=campaign_id,
        action="training.assignment.manage",
        purpose=MANAGE_PURPOSE,
    )
    enforce_rate_limit(
        request,
        tenant_id=tenant_id,
        principal_id=authorization.principal_id,
        policy_class=RateLimitPolicyClass.MUTATION,
    )
    try:
        evidence = service.create_assignment(
            tenant_id,
            campaign_id,
            request=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
            idempotency_key=_idempotency_key(request, idempotency_key),
        )
    except (
        TrainingConflict,
        TrainingIdempotencyConflict,
        TrainingLimitConflict,
        TrainingNotFound,
        TrainingUnavailable,
        TrainingVersionConflict,
    ) as exc:
        _raise_training_error(exc)
    _verify_assignment_scope(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        evidence=evidence,
        expected_principal_id=payload.principal_id,
    )
    response.headers["Location"] = (
        f"/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/training/assignments/"
        f"{evidence.assignment.id}"
    )
    response.headers["ETag"] = f'"{evidence.assignment.version}"'
    return evidence


@router.get(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/training/assignments/{assignment_id}",
    response_model=TrainingAssignmentEvidence,
    summary="Read one campaign training assignment",
)
@rate_limit_policy(RateLimitPolicyClass.EXPENSIVE_READ)
def get_training_assignment(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    assignment_id: UUID,
    authorization: CurrentTenantAuthorization,
    service: TrainingServiceDependency,
) -> TrainingAssignmentEvidence:
    grant = _require_grant(
        authorization,
        campaign_id=campaign_id,
        action="training.assignment.read",
        purpose=ADMIN_READ_PURPOSE,
    )
    enforce_rate_limit(
        request,
        tenant_id=tenant_id,
        principal_id=authorization.principal_id,
        policy_class=RateLimitPolicyClass.EXPENSIVE_READ,
    )
    try:
        evidence = service.get_assignment(
            tenant_id,
            campaign_id,
            assignment_id,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
        )
    except (TrainingNotFound, TrainingUnavailable) as exc:
        _raise_training_error(exc)
    _verify_assignment_scope(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        evidence=evidence,
    )
    response.headers["ETag"] = f'"{evidence.assignment.version}"'
    return evidence


@router.post(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/training/assignments/"
    "{assignment_id}/modules/{module_id}/start",
    response_model=TrainingAssignmentEvidence,
    summary="Start one assigned training module",
)
@rate_limit_policy(RateLimitPolicyClass.MUTATION)
def start_training_module(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    assignment_id: UUID,
    module_id: str,
    payload: TrainingModuleStartRequest,
    authorization: CurrentTenantAuthorization,
    service: TrainingServiceDependency,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> TrainingAssignmentEvidence:
    grant = _require_grant(
        authorization,
        campaign_id=campaign_id,
        action="training.self.complete",
        purpose=SELF_COMPLETE_PURPOSE,
    )
    enforce_rate_limit(
        request,
        tenant_id=tenant_id,
        principal_id=authorization.principal_id,
        policy_class=RateLimitPolicyClass.MUTATION,
    )
    try:
        evidence = service.start_module(
            tenant_id,
            campaign_id,
            assignment_id,
            module_id,
            request=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
            idempotency_key=_idempotency_key(request, idempotency_key),
        )
    except (
        TrainingAccessConflict,
        TrainingConflict,
        TrainingIdempotencyConflict,
        TrainingNotFound,
        TrainingUnavailable,
        TrainingVersionConflict,
    ) as exc:
        _raise_training_error(exc)
    _verify_assignment_scope(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        evidence=evidence,
        expected_principal_id=authorization.principal_id,
    )
    response.headers["ETag"] = f'"{evidence.assignment.version}"'
    return evidence


@router.post(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/training/assignments/"
    "{assignment_id}/modules/{module_id}/attempts",
    response_model=TrainingAttemptEvidence,
    summary="Submit one bounded training assessment attempt",
)
@rate_limit_policy(RateLimitPolicyClass.MUTATION)
def submit_training_attempt(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    assignment_id: UUID,
    module_id: str,
    payload: TrainingAttemptRequest,
    authorization: CurrentTenantAuthorization,
    service: TrainingServiceDependency,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> TrainingAttemptEvidence:
    grant = _require_grant(
        authorization,
        campaign_id=campaign_id,
        action="training.self.complete",
        purpose=SELF_COMPLETE_PURPOSE,
    )
    enforce_rate_limit(
        request,
        tenant_id=tenant_id,
        principal_id=authorization.principal_id,
        policy_class=RateLimitPolicyClass.MUTATION,
    )
    try:
        evidence = service.submit_attempt(
            tenant_id,
            campaign_id,
            assignment_id,
            module_id,
            request=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
            idempotency_key=_idempotency_key(request, idempotency_key),
        )
    except (
        TrainingAccessConflict,
        TrainingConflict,
        TrainingIdempotencyConflict,
        TrainingLimitConflict,
        TrainingNotFound,
        TrainingUnavailable,
        TrainingVersionConflict,
    ) as exc:
        _raise_training_error(exc)
    _verify_assignment_scope(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        evidence=evidence,
        expected_principal_id=authorization.principal_id,
    )
    if evidence.receipt is not None and evidence.receipt.principal_id != authorization.principal_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Training Academy is temporarily unavailable",
        )
    response.headers["ETag"] = f'"{evidence.assignment.version}"'
    return evidence


@router.get(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/training/me/assignments/{assignment_id}/receipts",
    response_model=TrainingReceiptListEvidence,
    summary="Read current principal training completion receipts",
)
@rate_limit_policy(RateLimitPolicyClass.EXPENSIVE_READ)
def get_own_training_receipts(
    request: Request,
    tenant_id: UUID,
    campaign_id: UUID,
    assignment_id: UUID,
    authorization: CurrentTenantAuthorization,
    service: TrainingServiceDependency,
) -> TrainingReceiptListEvidence:
    grant = _require_grant(
        authorization,
        campaign_id=campaign_id,
        action="training.receipt.read",
        purpose=SELF_READ_PURPOSE,
    )
    enforce_rate_limit(
        request,
        tenant_id=tenant_id,
        principal_id=authorization.principal_id,
        policy_class=RateLimitPolicyClass.EXPENSIVE_READ,
    )
    try:
        evidence = service.list_receipts(
            tenant_id,
            campaign_id,
            assignment_id,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
        )
    except (TrainingAccessConflict, TrainingNotFound, TrainingUnavailable) as exc:
        _raise_training_error(exc)
    if evidence.authority_effect != "NONE" or any(
        receipt.principal_id != authorization.principal_id
        or receipt.authority_effect != "NONE"
        or receipt.external_effects != "NONE"
        for receipt in evidence.receipts
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Training Academy is temporarily unavailable",
        )
    return evidence
