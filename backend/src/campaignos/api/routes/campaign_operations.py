"""Exact-authorized campaign roadmap and Daily War Room routes."""

from __future__ import annotations

from typing import Annotated, NoReturn, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

from campaignos.api.dependencies import CurrentTenantAuthorization
from campaignos.api.errors import ProblemException
from campaignos.identity.authorization import EffectivePermissionGrant, TenantAuthorizationContext
from campaignos.operations import (
    CampaignOperationsService,
    CampaignRoadmapConflict,
    CampaignRoadmapCreate,
    CampaignRoadmapCreateEvidence,
    CampaignRoadmapEvidenceConflict,
    CampaignRoadmapIdempotencyConflict,
    CampaignRoadmapNotFound,
    CampaignRoadmapPrerequisiteConflict,
    CampaignRoadmapReadEvidence,
    CampaignRoadmapUnavailable,
    CampaignRoadmapUpdate,
    CampaignRoadmapUpdateEvidence,
    CampaignRoadmapVersionConflict,
    WarRoomSnapshotConflict,
    WarRoomSnapshotCreate,
    WarRoomSnapshotEvidence,
    WarRoomSnapshotNotFound,
    WarRoomSnapshotReadEvidence,
)

router = APIRouter(tags=["campaign operations"])
CREATE_ROADMAP_PURPOSE = "Create campaign operations roadmap"
READ_ROADMAP_PURPOSE = "Review campaign operations roadmap"
UPDATE_ROADMAP_PURPOSE = "Maintain campaign operations roadmap"
CREATE_SNAPSHOT_PURPOSE = "Create daily campaign war room snapshot"
READ_SNAPSHOT_PURPOSE = "Review daily campaign war room snapshot"


def campaign_operations_service(request: Request) -> CampaignOperationsService:
    return cast(CampaignOperationsService, request.app.state.campaign_operations_service)


OperationsDependency = Annotated[CampaignOperationsService, Depends(campaign_operations_service)]


def _exact_grant(
    authorization: TenantAuthorizationContext,
    *,
    campaign_id: UUID,
    action: str,
    resource_type: str,
    purpose: str,
) -> EffectivePermissionGrant | None:
    for membership in authorization.memberships:
        for grant in membership.grants:
            if grant.permits(
                action=action,
                resource_type=resource_type,
                resource_id=str(campaign_id),
                purpose=purpose,
                campaign_id=campaign_id,
                workspace_id=None,
            ):
                return grant
    return None


def _required_idempotency_key(request: Request, value: str | None) -> str:
    values = request.headers.getlist("idempotency-key")
    if len(values) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one Idempotency-Key header is required",
        )
    if value is None or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Idempotency-Key is required for campaign operations writes",
        )
    normalized = value.strip()
    if len(normalized) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must not exceed 255 characters",
        )
    return normalized


def _expected_version(if_match: str | None) -> int:
    if if_match is None or not if_match.strip():
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="If-Match is required for campaign operations writes",
        )
    value = if_match.strip()
    if value.startswith('W/"') or not (value.startswith('"') and value.endswith('"')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="If-Match must contain one quoted positive roadmap version",
        )
    value = value[1:-1]
    if not value.isdigit() or int(value) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="If-Match must contain one quoted positive roadmap version",
        )
    return int(value)


def _raise_operations_error(exc: Exception) -> NoReturn:
    if isinstance(exc, CampaignRoadmapIdempotencyConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Idempotency conflict",
            detail="Idempotency key conflicts with a previous campaign operations request",
            code="IDEMPOTENCY_CONFLICT",
        ) from exc
    if isinstance(exc, CampaignRoadmapPrerequisiteConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Campaign operations prerequisite missing",
            detail="Campaign operations prerequisites are incomplete",
            code="CAMPAIGN_NOT_READY",
        ) from exc
    if isinstance(exc, (CampaignRoadmapConflict, CampaignRoadmapEvidenceConflict)):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Campaign roadmap conflict",
            detail="Campaign roadmap state conflicts with this operation",
            code="ROADMAP_CONFLICT",
        ) from exc
    if isinstance(exc, WarRoomSnapshotConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Daily War Room conflict",
            detail="A Daily War Room snapshot already exists for this date",
            code="WAR_ROOM_SNAPSHOT_CONFLICT",
        ) from exc
    if isinstance(exc, CampaignRoadmapVersionConflict):
        raise ProblemException(
            status=status.HTTP_412_PRECONDITION_FAILED,
            title="Campaign roadmap version conflict",
            detail="Campaign roadmap version has changed",
            code="VERSION_CONFLICT",
        ) from exc
    if isinstance(exc, (CampaignRoadmapNotFound, WarRoomSnapshotNotFound)):
        raise ProblemException(
            status=status.HTTP_404_NOT_FOUND,
            title="Campaign roadmap not found",
            detail="Campaign roadmap was not found",
            code="RESOURCE_NOT_FOUND",
        ) from exc
    if isinstance(exc, CampaignRoadmapUnavailable):
        raise ProblemException(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Campaign operations unavailable",
            detail="Campaign operations are temporarily unavailable",
            code="AUTHORIZATION_UNAVAILABLE",
        ) from exc
    raise exc


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


@router.post(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap",
    response_model=CampaignRoadmapCreateEvidence,
    status_code=status.HTTP_201_CREATED,
    summary="Create an internal campaign operations roadmap",
    description=(
        "Creates one campaign-scoped roadmap with audit and internal no-effect outbox evidence. "
        "No task, political action, contact, publication, spending or mobilization is executed."
    ),
)
def create_roadmap(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    payload: CampaignRoadmapCreate,
    authorization: CurrentTenantAuthorization,
    service: OperationsDependency,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> CampaignRoadmapCreateEvidence:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action="create",
        resource_type="campaign_roadmap",
        purpose=CREATE_ROADMAP_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Campaign roadmap creation is not authorized",
        )
    try:
        evidence = service.create_roadmap(
            tenant_id,
            campaign_id,
            request=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
            idempotency_key=_required_idempotency_key(request, idempotency_key),
        )
    except Exception as exc:
        _raise_operations_error(exc)
    if (
        evidence.roadmap.tenant_id != tenant_id
        or evidence.roadmap.campaign_id != campaign_id
        or evidence.roadmap.version != 1
        or evidence.roadmap.authority_effect != "NONE"
        or evidence.roadmap.external_effects != "NONE"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign operations are temporarily unavailable",
        )
    response.headers["Location"] = (
        f"/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap"
    )
    response.headers["ETag"] = f'"{evidence.roadmap.version}"'
    return evidence


@router.get(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap",
    response_model=CampaignRoadmapReadEvidence,
    summary="Read the campaign operations roadmap",
)
def read_roadmap(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    authorization: CurrentTenantAuthorization,
    service: OperationsDependency,
) -> CampaignRoadmapReadEvidence:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action="read",
        resource_type="campaign_roadmap",
        purpose=READ_ROADMAP_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Campaign roadmap read is not authorized",
        )
    try:
        evidence = service.get_roadmap(
            tenant_id,
            campaign_id,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
        )
    except Exception as exc:
        _raise_operations_error(exc)
    if (
        evidence.roadmap.tenant_id != tenant_id
        or evidence.roadmap.campaign_id != campaign_id
        or evidence.roadmap.authority_effect != "NONE"
        or evidence.roadmap.external_effects != "NONE"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign operations are temporarily unavailable",
        )
    response.headers["ETag"] = f'"{evidence.roadmap.version}"'
    return evidence


@router.patch(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap",
    response_model=CampaignRoadmapUpdateEvidence,
    summary="Update the campaign operations roadmap",
)
def update_roadmap(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    payload: CampaignRoadmapUpdate,
    authorization: CurrentTenantAuthorization,
    service: OperationsDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> CampaignRoadmapUpdateEvidence:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action="update",
        resource_type="campaign_roadmap",
        purpose=UPDATE_ROADMAP_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Campaign roadmap update is not authorized",
        )
    expected = _expected_version(if_match)
    try:
        evidence = service.update_roadmap(
            tenant_id,
            campaign_id,
            expected_version=expected,
            changes=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
            idempotency_key=_required_idempotency_key(request, idempotency_key),
        )
    except Exception as exc:
        _raise_operations_error(exc)
    if (
        evidence.roadmap.tenant_id != tenant_id
        or evidence.roadmap.campaign_id != campaign_id
        or evidence.roadmap.version != expected + 1
        or evidence.roadmap.authority_effect != "NONE"
        or evidence.roadmap.external_effects != "NONE"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign operations are temporarily unavailable",
        )
    response.headers["ETag"] = f'"{evidence.roadmap.version}"'
    return evidence


@router.get(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap/war-room-snapshots/latest",
    response_model=WarRoomSnapshotReadEvidence,
    summary="Read the latest Daily War Room snapshot",
    description=(
        "Returns the latest immutable Daily War Room snapshot after exact authorization. "
        "The read is audited and has no authority or external effect."
    ),
)
def read_latest_war_room_snapshot(
    request: Request,
    tenant_id: UUID,
    campaign_id: UUID,
    authorization: CurrentTenantAuthorization,
    service: OperationsDependency,
) -> WarRoomSnapshotReadEvidence:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action="read",
        resource_type="war_room_snapshot",
        purpose=READ_SNAPSHOT_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Daily War Room snapshot read is not authorized",
        )
    try:
        evidence = service.get_latest_snapshot(
            tenant_id,
            campaign_id,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
        )
    except Exception as exc:
        _raise_operations_error(exc)
    if (
        evidence.snapshot.tenant_id != tenant_id
        or evidence.snapshot.campaign_id != campaign_id
        or evidence.snapshot.authority_effect != "NONE"
        or evidence.snapshot.external_effects != "NONE"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign operations are temporarily unavailable",
        )
    return evidence


@router.post(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap/war-room-snapshots",
    response_model=WarRoomSnapshotEvidence,
    status_code=status.HTTP_201_CREATED,
    summary="Create an immutable Daily War Room snapshot",
    description=(
        "Captures priorities, ready work, blockers and required human decisions from an exact "
        "roadmap version. It does not execute or authorize any task."
    ),
)
def create_war_room_snapshot(
    request: Request,
    response: Response,
    tenant_id: UUID,
    campaign_id: UUID,
    payload: WarRoomSnapshotCreate,
    authorization: CurrentTenantAuthorization,
    service: OperationsDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> WarRoomSnapshotEvidence:
    grant = _exact_grant(
        authorization,
        campaign_id=campaign_id,
        action="create",
        resource_type="war_room_snapshot",
        purpose=CREATE_SNAPSHOT_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Daily War Room snapshot creation is not authorized",
        )
    expected = _expected_version(if_match)
    try:
        evidence = service.create_snapshot(
            tenant_id,
            campaign_id,
            expected_roadmap_version=expected,
            request=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
            idempotency_key=_required_idempotency_key(request, idempotency_key),
        )
    except Exception as exc:
        _raise_operations_error(exc)
    if (
        evidence.snapshot.tenant_id != tenant_id
        or evidence.snapshot.campaign_id != campaign_id
        or evidence.snapshot.roadmap_version != expected
        or evidence.snapshot.authority_effect != "NONE"
        or evidence.snapshot.external_effects != "NONE"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Campaign operations are temporarily unavailable",
        )
    response.headers["Location"] = (
        f"/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap/"
        f"war-room-snapshots/{evidence.snapshot.id}"
    )
    return evidence
