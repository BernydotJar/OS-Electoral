"""Protected workspace mutation endpoints."""

from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from campaignos.api.dependencies import CurrentTenantAuthorization
from campaignos.identity.authorization import EffectivePermissionGrant, TenantAuthorizationContext
from campaignos.workspaces import (
    WorkspaceCreate,
    WorkspaceIdempotencyConflict,
    WorkspaceMutationNotFound,
    WorkspaceWriteEvidence,
    WorkspaceWriter,
    WorkspaceWriteUnavailable,
)

router = APIRouter(tags=["workspaces"])
CREATE_WORKSPACE_PURPOSE = "Configure assigned campaign workspace"


def workspace_writer(request: Request) -> WorkspaceWriter:
    return cast(WorkspaceWriter, request.app.state.workspace_writer)


WorkspaceWriterDependency = Annotated[WorkspaceWriter, Depends(workspace_writer)]


def _create_grant(
    authorization: TenantAuthorizationContext, campaign_id: UUID
) -> EffectivePermissionGrant | None:
    resource_id = f"campaign:{campaign_id}:workspaces"
    for membership in authorization.memberships:
        for grant in membership.grants:
            if grant.permits(
                action="create",
                resource_type="workspace",
                resource_id=resource_id,
                purpose=CREATE_WORKSPACE_PURPOSE,
                campaign_id=campaign_id,
                workspace_id=None,
            ):
                return grant
    return None


@router.post(
    "/tenants/{tenant_id}/campaigns/{campaign_id}/workspaces",
    response_model=WorkspaceWriteEvidence,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace(
    request: Request,
    tenant_id: UUID,
    campaign_id: UUID,
    payload: WorkspaceCreate,
    authorization: CurrentTenantAuthorization,
    writer: WorkspaceWriterDependency,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> WorkspaceWriteEvidence:
    """Create one workspace only with an exact campaign-scoped grant."""
    grant = _create_grant(authorization, campaign_id)
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace creation is not authorized",
        )
    if idempotency_key is None or not idempotency_key.strip():
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Idempotency-Key is required for workspace writes",
        )
    if len(idempotency_key) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must not exceed 255 characters",
        )
    try:
        evidence = writer.create(
            tenant_id,
            campaign_id,
            request=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            correlation_id=getattr(request.state, "correlation_id", "unknown"),
            idempotency_key=idempotency_key.strip(),
        )
    except WorkspaceIdempotencyConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key conflicts with a previous request",
        ) from exc
    except WorkspaceMutationNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign was not found",
        ) from exc
    except WorkspaceWriteUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Workspace write is temporarily unavailable",
        ) from exc
    if evidence.workspace.tenant_id != tenant_id or evidence.workspace.campaign_id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Workspace write is temporarily unavailable",
        )
    return evidence
