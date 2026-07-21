"""Exact-authorized candidate evidence workspace endpoints."""

from __future__ import annotations

from typing import Annotated, NoReturn, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

from campaignos.api.dependencies import CurrentTenantAuthorization
from campaignos.api.errors import ProblemException
from campaignos.candidates import (
    CandidateSectionApprovalRequest,
    CandidateWorkspaceApprovalEvidence,
    CandidateWorkspaceCreate,
    CandidateWorkspaceCreateEvidence,
    CandidateWorkspaceReadEvidence,
    CandidateWorkspaceService,
    CandidateWorkspaceUpdate,
    CandidateWorkspaceUpdateEvidence,
)
from campaignos.candidates.service import (
    CandidateWorkspaceApprovalConflict,
    CandidateWorkspaceConflict,
    CandidateWorkspaceEvidenceConflict,
    CandidateWorkspaceIdempotencyConflict,
    CandidateWorkspaceNotFound,
    CandidateWorkspacePrerequisiteConflict,
    CandidateWorkspaceUnavailable,
    CandidateWorkspaceVersionConflict,
)
from campaignos.identity.authorization import (
    EffectivePermissionGrant,
    TenantAuthorizationContext,
)

router = APIRouter(tags=["candidate workspace"])

CREATE_CANDIDATE_WORKSPACE_PURPOSE = "Create candidate evidence workspace"
READ_CANDIDATE_WORKSPACE_PURPOSE = "Review candidate evidence workspace"
UPDATE_CANDIDATE_WORKSPACE_PURPOSE = "Maintain candidate evidence workspace"
APPROVE_CANDIDATE_SECTION_PURPOSE = "Approve candidate evidence section"


def candidate_workspace_service(request: Request) -> CandidateWorkspaceService:
    return cast(CandidateWorkspaceService, request.app.state.candidate_workspace_service)


CandidateWorkspaceServiceDependency = Annotated[
    CandidateWorkspaceService,
    Depends(candidate_workspace_service),
]


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
                resource_type="candidate_workspace",
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
                "Exactly one If-Match header with the current candidate workspace "
                "version is required"
            ),
        )
    normalized = value.strip()
    if len(normalized) >= 2 and normalized[0] == normalized[-1] == '"':
        normalized = normalized[1:-1]
    if not normalized.isdigit() or int(normalized) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="If-Match must contain a positive candidate workspace version",
        )
    return int(normalized)


def _raise_candidate_error(exc: Exception) -> NoReturn:
    if isinstance(exc, CandidateWorkspaceIdempotencyConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Idempotency conflict",
            detail="Idempotency key conflicts with a previous candidate workspace request",
            code="IDEMPOTENCY_CONFLICT",
        ) from exc
    if isinstance(exc, CandidateWorkspacePrerequisiteConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Campaign not ready",
            detail="Guided campaign intake must be ready before candidate workspace creation",
            code="CAMPAIGN_NOT_READY",
        ) from exc
    if isinstance(
        exc,
        (
            CandidateWorkspaceApprovalConflict,
            CandidateWorkspaceConflict,
            CandidateWorkspaceEvidenceConflict,
        ),
    ):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Candidate workspace conflict",
            detail="Candidate workspace evidence or approval state conflicts with this operation",
            code="CANDIDATE_WORKSPACE_CONFLICT",
        ) from exc
    if isinstance(exc, CandidateWorkspaceVersionConflict):
        raise ProblemException(
            status=status.HTTP_412_PRECONDITION_FAILED,
            title="Candidate workspace version conflict",
            detail="Candidate workspace version has changed",
            code="VERSION_CONFLICT",
        ) from exc
    if isinstance(exc, CandidateWorkspaceNotFound):
        raise ProblemException(
            status=status.HTTP_404_NOT_FOUND,
            title="Resource not found",
            detail="Candidate workspace was not found",
            code="RESOURCE_NOT_FOUND",
        ) from exc
    if isinstance(exc, CandidateWorkspaceUnavailable):
        raise ProblemException(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Service unavailable",
            detail="Candidate workspace is temporarily unavailable",
            code="AUTHORIZATION_UNAVAILABLE",
        ) from exc
    raise exc


def _verify_scope(
    *,
    tenant_id: UUID,
    campaign_id: UUID,
    evidence: (
        CandidateWorkspaceCreateEvidence
        | CandidateWorkspaceReadEvidence
        | CandidateWorkspaceUpdateEvidence
        | CandidateWorkspaceApprovalEvidence
    ),
) -> None:
    workspace = evidence.workspace
    if workspace.tenant_id != tenant_id or workspace.campaign_id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Candidate workspace is temporarily unavailable",
        )


@router.post(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace",
    response_model=CandidateWorkspaceCreateEvidence,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "headers": {
                "Location": {"schema": {"type": "string"}},
                "ETag": {"schema": {"type": "string"}},
            }
        }
    },
    summary="Create candidate evidence workspace",
    description=(
        "Creates one internal candidate evidence workspace after guided intake is ready. "
        "The result remains blocked for public use and has no external effects."
    ),
)
def create_candidate_workspace(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    payload: CandidateWorkspaceCreate,
    authorization: CurrentTenantAuthorization,
    service: CandidateWorkspaceServiceDependency,
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description="Required stable key for one candidate workspace create intent",
        ),
    ] = None,
) -> CandidateWorkspaceCreateEvidence:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action="create",
        purpose=CREATE_CANDIDATE_WORKSPACE_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate workspace creation is not authorized",
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
    except (
        CandidateWorkspaceConflict,
        CandidateWorkspaceIdempotencyConflict,
        CandidateWorkspaceNotFound,
        CandidateWorkspacePrerequisiteConflict,
        CandidateWorkspaceUnavailable,
    ) as exc:
        _raise_candidate_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    response.headers["Location"] = request.url.path
    response.headers["ETag"] = f'"{evidence.workspace.version}"'
    return evidence


@router.get(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace",
    response_model=CandidateWorkspaceReadEvidence,
    responses={status.HTTP_200_OK: {"headers": {"ETag": {"schema": {"type": "string"}}}}},
    summary="Read candidate evidence workspace",
)
def get_candidate_workspace(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    authorization: CurrentTenantAuthorization,
    service: CandidateWorkspaceServiceDependency,
) -> CandidateWorkspaceReadEvidence:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action="read",
        purpose=READ_CANDIDATE_WORKSPACE_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate workspace read is not authorized",
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
    except (CandidateWorkspaceNotFound, CandidateWorkspaceUnavailable) as exc:
        _raise_candidate_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    response.headers["ETag"] = f'"{evidence.workspace.version}"'
    return evidence


@router.patch(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace",
    response_model=CandidateWorkspaceUpdateEvidence,
    responses={status.HTTP_200_OK: {"headers": {"ETag": {"schema": {"type": "string"}}}}},
    summary="Update candidate evidence workspace",
)
def update_candidate_workspace(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    changes: CandidateWorkspaceUpdate,
    authorization: CurrentTenantAuthorization,
    service: CandidateWorkspaceServiceDependency,
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
            description="Required stable key for one candidate workspace update intent",
        ),
    ] = None,
) -> CandidateWorkspaceUpdateEvidence:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action="update",
        purpose=UPDATE_CANDIDATE_WORKSPACE_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate workspace update is not authorized",
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
    except (
        CandidateWorkspaceEvidenceConflict,
        CandidateWorkspaceIdempotencyConflict,
        CandidateWorkspaceNotFound,
        CandidateWorkspaceUnavailable,
        CandidateWorkspaceVersionConflict,
    ) as exc:
        _raise_candidate_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    if evidence.workspace.version != expected_version + 1:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Candidate workspace is temporarily unavailable",
        )
    response.headers["ETag"] = f'"{evidence.workspace.version}"'
    return evidence


@router.post(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace/section-approvals",
    response_model=CandidateWorkspaceApprovalEvidence,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_201_CREATED: {"headers": {"ETag": {"schema": {"type": "string"}}}}},
    summary="Approve one candidate evidence section for the current version",
    description=(
        "Appends one exact version-bound internal section receipt. It does not approve "
        "public positioning, strategy, publication or any external effect."
    ),
)
def approve_candidate_section(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    payload: CandidateSectionApprovalRequest,
    authorization: CurrentTenantAuthorization,
    service: CandidateWorkspaceServiceDependency,
    if_match: Annotated[
        str | None,
        Header(
            alias="If-Match",
            description="Required quoted current candidate workspace version",
        ),
    ] = None,
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            description="Required stable key for one section approval intent",
        ),
    ] = None,
) -> CandidateWorkspaceApprovalEvidence:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action="approve",
        purpose=APPROVE_CANDIDATE_SECTION_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate section approval is not authorized",
        )
    expected_version = _expected_version(request, if_match)
    try:
        evidence = service.approve_section(
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
    except (
        CandidateWorkspaceApprovalConflict,
        CandidateWorkspaceIdempotencyConflict,
        CandidateWorkspaceNotFound,
        CandidateWorkspaceUnavailable,
        CandidateWorkspaceVersionConflict,
    ) as exc:
        _raise_candidate_error(exc)
    _verify_scope(tenant_id=tenant_id, campaign_id=campaign_id, evidence=evidence)
    if evidence.workspace.version != expected_version:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Candidate workspace is temporarily unavailable",
        )
    response.headers["ETag"] = f'"{evidence.workspace.version}"'
    return evidence
