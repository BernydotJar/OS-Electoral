"""Protected tenant campaign projections."""

from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status

from campaignos.api.dependencies import CurrentTenantAuthorization
from campaignos.api.errors import ProblemException
from campaignos.campaigns import (
    CampaignCreate,
    CampaignCreateConflict,
    CampaignCreateEvidence,
    CampaignCreateIdempotencyConflict,
    CampaignCreateUnavailable,
    CampaignCreator,
    CampaignDirectory,
    CampaignDirectoryUnavailable,
    CampaignIdempotencyConflict,
    CampaignMutationNotFound,
    CampaignNotFound,
    CampaignPage,
    CampaignProjection,
    CampaignReadinessEvidence,
    CampaignReadinessNotFound,
    CampaignReadinessReader,
    CampaignReadinessUnavailable,
    CampaignUpdate,
    CampaignWriteConflict,
    CampaignWriteEvidence,
    CampaignWriter,
    CampaignWriteUnavailable,
)
from campaignos.identity.authorization import (
    EffectivePermissionGrant,
    TenantAuthorizationContext,
)

router = APIRouter(tags=["campaigns"])
CREATE_CAMPAIGN_PURPOSE = "Create tenant campaign"
READ_CAMPAIGN_PURPOSE = "Operate assigned campaign"
READ_CAMPAIGN_READINESS_PURPOSE = "Assess assigned campaign readiness"


def campaign_creator(request: Request) -> CampaignCreator:
    return cast(CampaignCreator, request.app.state.campaign_creator)


CampaignCreatorDependency = Annotated[CampaignCreator, Depends(campaign_creator)]


def _create_grant(
    authorization: TenantAuthorizationContext,
    tenant_id: UUID,
) -> EffectivePermissionGrant | None:
    for membership in authorization.memberships:
        for grant in membership.grants:
            if grant.permits(
                action="create",
                resource_type="campaign_collection",
                resource_id=str(tenant_id),
                purpose=CREATE_CAMPAIGN_PURPOSE,
                campaign_id=None,
                workspace_id=None,
            ):
                return grant
    return None


@router.post(
    "/tenants/{tenant_id}/campaigns",
    response_model=CampaignCreateEvidence,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "headers": {
                "Location": {
                    "description": "Canonical tenant campaign resource path",
                    "schema": {"type": "string"},
                },
                "ETag": {
                    "description": "Quoted optimistic-concurrency version",
                    "schema": {"type": "string"},
                },
            }
        }
    },
    summary="Create an internal draft campaign",
    description=(
        "Creates only a tenant-scoped DRAFT campaign plus atomic audit, internal "
        "outbox, and idempotency evidence. It does not approve strategy, spending, "
        "publication, outreach, mobilization, or production use."
    ),
)
def create_campaign(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign: CampaignCreate,
    authorization: CurrentTenantAuthorization,
    creator: CampaignCreatorDependency,
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            description="Required stable key for one tenant campaign-create intent",
        ),
    ],
) -> CampaignCreateEvidence:
    """Create one draft campaign after exact tenant collection authorization."""
    grant = _create_grant(authorization, tenant_id)
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Campaign creation is not authorized",
        )
    raw_idempotency_values = request.headers.getlist("idempotency-key")
    if len(raw_idempotency_values) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one Idempotency-Key header is required",
        )
    normalized_key = idempotency_key.strip()
    if not normalized_key:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Idempotency-Key is required for campaign creation",
        )
    if len(normalized_key) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must not exceed 255 characters",
        )
    try:
        evidence = creator.create(
            tenant_id,
            request=campaign,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=getattr(request.state, "correlation_id", "unknown"),
            idempotency_key=normalized_key,
        )
    except CampaignCreateIdempotencyConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key conflicts with a previous request",
        ) from exc
    except CampaignCreateConflict as exc:
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Resource conflict",
            detail="Campaign slug is already reserved",
            code="RESOURCE_CONFLICT",
        ) from exc
    except CampaignCreateUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign creation is temporarily unavailable",
        ) from exc
    created_campaign = evidence.campaign
    if (
        created_campaign.tenant_id != tenant_id
        or created_campaign.slug != campaign.slug
        or created_campaign.name != campaign.name
        or created_campaign.jurisdiction != campaign.jurisdiction
        or created_campaign.stage != campaign.stage
        or created_campaign.status != "DRAFT"
        or created_campaign.version != 1
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign creation is temporarily unavailable",
        )
    response.headers["Location"] = f"/api/v1/tenants/{tenant_id}/campaigns/{evidence.campaign.id}"
    response.headers["ETag"] = f'"{evidence.campaign.version}"'
    return evidence


def campaign_directory(request: Request) -> CampaignDirectory:
    return cast(CampaignDirectory, request.app.state.campaign_directory)


CampaignDirectoryDependency = Annotated[CampaignDirectory, Depends(campaign_directory)]


def _authorized_campaign_ids(authorization: TenantAuthorizationContext) -> tuple[UUID, ...]:
    campaign_ids: set[UUID] = set()
    for membership in authorization.memberships:
        for grant in membership.grants:
            if (
                grant.action == "read"
                and grant.resource_type == "campaign"
                and grant.purpose == READ_CAMPAIGN_PURPOSE
                and grant.campaign_id is not None
                and grant.workspace_id is None
                and grant.resource_id == str(grant.campaign_id)
            ):
                campaign_ids.add(grant.campaign_id)
    return tuple(sorted(campaign_ids))


@router.get(
    "/tenants/{tenant_id}/campaigns",
    response_model=CampaignPage,
)
def list_campaigns(
    tenant_id: UUID,
    authorization: CurrentTenantAuthorization,
    directory: CampaignDirectoryDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    cursor: UUID | None = None,
) -> CampaignPage:
    """List only campaigns covered by exact current grants, without total counts."""
    campaign_ids = _authorized_campaign_ids(authorization)
    try:
        page = directory.list_authorized(
            tenant_id,
            campaign_ids,
            limit=limit,
            cursor=cursor,
        )
    except CampaignDirectoryUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign data is temporarily unavailable",
        ) from exc

    if any(item.tenant_id != tenant_id or item.id not in campaign_ids for item in page.items):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign data is temporarily unavailable",
        )
    return page


@router.get(
    "/tenants/{tenant_id}/campaigns/{campaign_id}",
    response_model=CampaignProjection,
)
def get_campaign(
    tenant_id: UUID,
    campaign_id: UUID,
    authorization: CurrentTenantAuthorization,
    directory: CampaignDirectoryDependency,
) -> CampaignProjection:
    """Return one campaign only when an exact current grant permits the read."""
    if not authorization.permits(
        action="read",
        resource_type="campaign",
        resource_id=str(campaign_id),
        purpose=READ_CAMPAIGN_PURPOSE,
        campaign_id=campaign_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Campaign access is not authorized",
        )
    try:
        projection = directory.get(tenant_id, campaign_id)
    except CampaignNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign was not found",
        ) from exc
    except CampaignDirectoryUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign data is temporarily unavailable",
        ) from exc
    if projection.tenant_id != tenant_id or projection.id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign data is temporarily unavailable",
        )
    return projection


def campaign_readiness_reader(request: Request) -> CampaignReadinessReader:
    return cast(CampaignReadinessReader, request.app.state.campaign_readiness_reader)


CampaignReadinessReaderDependency = Annotated[
    CampaignReadinessReader, Depends(campaign_readiness_reader)
]


def _readiness_grant(
    authorization: TenantAuthorizationContext, campaign_id: UUID
) -> EffectivePermissionGrant | None:
    for membership in authorization.memberships:
        for grant in membership.grants:
            if grant.permits(
                action="read",
                resource_type="campaign_readiness",
                resource_id=str(campaign_id),
                purpose=READ_CAMPAIGN_READINESS_PURPOSE,
                campaign_id=campaign_id,
                workspace_id=None,
            ):
                return grant
    return None


@router.get(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/readiness",
    response_model=CampaignReadinessEvidence,
    summary="Assess operational campaign setup readiness",
    description=(
        "Returns an audited operational setup projection. It is not a political, legal, "
        "financial, security, publication, production, or other human approval."
    ),
)
def get_campaign_readiness(
    request: Request,
    tenant_id: UUID,
    campaign_id: UUID,
    authorization: CurrentTenantAuthorization,
    reader: CampaignReadinessReaderDependency,
) -> CampaignReadinessEvidence:
    """Return deterministic setup readiness only after exact current authorization."""
    grant = _readiness_grant(authorization, campaign_id)
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Campaign readiness access is not authorized",
        )
    try:
        evidence = reader.get(
            tenant_id,
            campaign_id,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=getattr(request.state, "correlation_id", "unknown"),
        )
    except CampaignReadinessNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign was not found",
        ) from exc
    except CampaignReadinessUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign readiness is temporarily unavailable",
        ) from exc
    if evidence.readiness.tenant_id != tenant_id or evidence.readiness.campaign_id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign readiness is temporarily unavailable",
        )
    return evidence


# Write operations are deliberately separate from read authorization semantics.
UPDATE_CAMPAIGN_PURPOSE = "Maintain assigned campaign"


def campaign_writer(request: Request) -> CampaignWriter:
    return cast(CampaignWriter, request.app.state.campaign_writer)


CampaignWriterDependency = Annotated[CampaignWriter, Depends(campaign_writer)]


def _update_grant(
    authorization: TenantAuthorizationContext, campaign_id: UUID
) -> EffectivePermissionGrant | None:
    for membership in authorization.memberships:
        for grant in membership.grants:
            if grant.permits(
                action="update",
                resource_type="campaign",
                resource_id=str(campaign_id),
                purpose=UPDATE_CAMPAIGN_PURPOSE,
                campaign_id=campaign_id,
                workspace_id=None,
            ):
                return grant
    return None


def _expected_version(if_match: str | None) -> int:
    if if_match is None:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="If-Match with the current campaign version is required",
        )
    value = if_match.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        value = value[1:-1]
    if not value.isdigit() or int(value) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="If-Match must contain a positive campaign version",
        )
    return int(value)


@router.patch(
    "/tenants/{tenant_id}/campaigns/{campaign_id}",
    response_model=CampaignWriteEvidence,
)
def update_campaign(
    request: Request,
    tenant_id: UUID,
    campaign_id: UUID,
    changes: CampaignUpdate,
    authorization: CurrentTenantAuthorization,
    writer: CampaignWriterDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> CampaignWriteEvidence:
    """Update bounded campaign fields with exact authorization and version matching."""
    grant = _update_grant(authorization, campaign_id)
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Campaign update is not authorized",
        )
    if idempotency_key is None or not idempotency_key.strip():
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Idempotency-Key is required for campaign writes",
        )
    if len(idempotency_key) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must not exceed 255 characters",
        )
    try:
        evidence = writer.update(
            tenant_id,
            campaign_id,
            expected_version=_expected_version(if_match),
            changes=changes,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            correlation_id=getattr(request.state, "correlation_id", "unknown"),
            idempotency_key=idempotency_key.strip(),
        )
    except CampaignIdempotencyConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key conflicts with a previous request",
        ) from exc
    except CampaignMutationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign was not found",
        ) from exc
    except CampaignWriteConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Campaign version has changed",
        ) from exc
    except CampaignWriteUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign write is temporarily unavailable",
        ) from exc
    if evidence.campaign.tenant_id != tenant_id or evidence.campaign.id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign write is temporarily unavailable",
        )
    return evidence
