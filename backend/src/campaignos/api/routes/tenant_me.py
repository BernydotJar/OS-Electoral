"""Tenant-scoped authenticated identity and server-owned authorization projection."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from campaignos.api.dependencies import CurrentPrincipal, CurrentTenantAuthorization
from campaignos.api.rate_limits import enforce_rate_limit, rate_limit_policy
from campaignos.identity.authorization import EffectiveMembership
from campaignos.security import RateLimitPolicyClass

router = APIRouter(tags=["identity"])


class TenantMeResponse(BaseModel):
    """Verified identity plus current server-owned tenant authorization."""

    model_config = ConfigDict(extra="forbid")

    principal_id: UUID
    tenant_id: UUID
    subject: str
    issuer: str
    display_name: str | None
    email: str | None
    authenticated_at: datetime
    evaluated_at: datetime
    application_memberships: tuple[EffectiveMembership, ...]
    authorization_status: Literal["LOADED"]


@router.get(
    "/tenants/{tenant_id}/me",
    response_model=TenantMeResponse,
    summary="Current tenant identity and authorization",
)
@rate_limit_policy(RateLimitPolicyClass.READ)
def tenant_me(
    request: Request,
    tenant_id: UUID,
    principal: CurrentPrincipal,
    authorization: CurrentTenantAuthorization,
) -> TenantMeResponse:
    enforce_rate_limit(
        request,
        tenant_id=tenant_id,
        principal_id=authorization.principal_id,
        policy_class=RateLimitPolicyClass.READ,
    )
    return TenantMeResponse(
        principal_id=authorization.principal_id,
        tenant_id=tenant_id,
        subject=principal.subject,
        issuer=principal.issuer,
        display_name=principal.display_name,
        email=principal.email,
        authenticated_at=principal.authenticated_at,
        evaluated_at=authorization.evaluated_at,
        application_memberships=authorization.memberships,
        authorization_status="LOADED",
    )
