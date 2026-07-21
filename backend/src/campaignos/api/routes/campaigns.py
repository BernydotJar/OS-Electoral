"""Protected tenant campaign projections."""

from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from campaignos.api.dependencies import CurrentTenantAuthorization
from campaignos.campaigns import (
    CampaignDirectory,
    CampaignDirectoryUnavailable,
    CampaignMutationNotFound,
    CampaignNotFound,
    CampaignPage,
    CampaignProjection,
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
READ_CAMPAIGN_PURPOSE = "Operate assigned campaign"


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
) -> CampaignWriteEvidence:
    """Update bounded campaign fields with exact authorization and version matching."""
    grant = _update_grant(authorization, campaign_id)
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Campaign update is not authorized",
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
        )
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
