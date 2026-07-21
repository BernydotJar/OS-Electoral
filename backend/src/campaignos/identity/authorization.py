"""Server-owned tenant membership and exact-grant authorization loading."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError

from campaignos.data.database import Database
from campaignos.data.models import (
    Campaign,
    Membership,
    PermissionGrant,
    Principal,
    RoleAssignment,
    Tenant,
    Workspace,
)
from campaignos.identity.models import AuthenticatedPrincipal


class TenantAccessDenied(PermissionError):
    """The verified principal has no active access to the requested tenant."""


class AuthorizationDirectoryUnavailable(RuntimeError):
    """The server-owned membership directory cannot currently be queried."""


class AuthorizationDataError(RuntimeError):
    """Persisted authorization data violates a fail-closed scope invariant."""


class EffectivePermissionGrant(BaseModel):
    """One exact, active server-owned permission grant."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    grant_id: UUID
    campaign_id: UUID | None
    workspace_id: UUID | None
    action: str = Field(min_length=1, max_length=100)
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: str = Field(min_length=1, max_length=255)
    purpose: str = Field(min_length=1, max_length=255)
    approval_receipt_id: str = Field(min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        if self.workspace_id is not None and self.campaign_id is None:
            raise ValueError("workspace-scoped grants require campaign scope")
        return self

    def permits(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str,
        purpose: str,
        campaign_id: UUID | None,
        workspace_id: UUID | None,
    ) -> bool:
        """Match every operation, resource, purpose, and scope field exactly."""
        return (
            self.action == action
            and self.resource_type == resource_type
            and self.resource_id == resource_id
            and self.purpose == purpose
            and self.campaign_id == campaign_id
            and self.workspace_id == workspace_id
        )


class EffectiveMembership(BaseModel):
    """One active membership and its current server-owned authorization data."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    membership_id: UUID
    campaign_id: UUID | None
    roles: tuple[str, ...]
    grants: tuple[EffectivePermissionGrant, ...]

    @model_validator(mode="after")
    def validate_grant_scope(self) -> Self:
        if self.campaign_id is not None and any(
            grant.campaign_id != self.campaign_id for grant in self.grants
        ):
            raise ValueError("campaign membership grants must remain in campaign scope")
        return self


class TenantAuthorizationContext(BaseModel):
    """Trusted application authorization context for one tenant request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    principal_id: UUID
    tenant_id: UUID
    evaluated_at: datetime
    memberships: tuple[EffectiveMembership, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_evaluation_time(self) -> Self:
        if self.evaluated_at.utcoffset() is None:
            raise ValueError("authorization evaluation time must include a timezone")
        return self

    def permits(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str,
        purpose: str,
        campaign_id: UUID | None = None,
        workspace_id: UUID | None = None,
    ) -> bool:
        """Authorize only an exact active grant; role labels never imply access."""
        return any(
            grant.permits(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                purpose=purpose,
                campaign_id=campaign_id,
                workspace_id=workspace_id,
            )
            for membership in self.memberships
            for grant in membership.grants
        )


class MembershipDirectory(Protocol):
    """Load current authorization from a server-owned persistence boundary."""

    def load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        *,
        evaluated_at: datetime | None = None,
    ) -> TenantAuthorizationContext:
        """Return active membership data or fail closed."""


class UnavailableMembershipDirectory:
    """Fail-closed directory used before persistence is configured."""

    def load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        *,
        evaluated_at: datetime | None = None,
    ) -> TenantAuthorizationContext:
        del tenant_id, principal, evaluated_at
        raise AuthorizationDirectoryUnavailable("Membership authorization is unavailable")


@dataclass(slots=True)
class SqlAlchemyMembershipDirectory:
    """Load active memberships, roles, and grants inside a tenant-scoped transaction."""

    database: Database

    def load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        *,
        evaluated_at: datetime | None = None,
    ) -> TenantAuthorizationContext:
        now = evaluated_at or datetime.now(UTC)
        if now.utcoffset() is None:
            raise AuthorizationDataError("Authorization evaluation time must include a timezone")
        now = now.astimezone(UTC)
        try:
            return self._load(tenant_id, principal, now)
        except ValidationError as exc:
            raise AuthorizationDataError("Persisted authorization data is invalid") from exc
        except SQLAlchemyError as exc:
            raise AuthorizationDirectoryUnavailable(
                "Membership authorization is unavailable"
            ) from exc

    def _load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        evaluated_at: datetime,
    ) -> TenantAuthorizationContext:
        with self.database.tenant_transaction(tenant_id) as session:
            active_tenant = session.scalar(
                select(Tenant.id).where(Tenant.id == tenant_id, Tenant.status == "ACTIVE")
            )
            if active_tenant is None:
                raise TenantAccessDenied("Tenant access is not authorized")

            application_principal = session.scalar(
                select(Principal).where(
                    Principal.issuer == principal.issuer,
                    Principal.subject == principal.subject,
                    Principal.disabled_at.is_(None),
                )
            )
            if application_principal is None:
                raise TenantAccessDenied("Tenant access is not authorized")

            memberships = list(
                session.scalars(
                    select(Membership)
                    .outerjoin(
                        Campaign,
                        and_(
                            Campaign.tenant_id == Membership.tenant_id,
                            Campaign.id == Membership.campaign_id,
                        ),
                    )
                    .where(
                        Membership.tenant_id == tenant_id,
                        Membership.principal_id == application_principal.id,
                        Membership.status == "ACTIVE",
                        Membership.valid_from <= evaluated_at,
                        Membership.revoked_at.is_(None),
                        or_(
                            Membership.expires_at.is_(None),
                            Membership.expires_at > evaluated_at,
                        ),
                        or_(
                            Membership.campaign_id.is_(None),
                            Campaign.status.in_(("DRAFT", "ACTIVE")),
                        ),
                    )
                    .order_by(Membership.id)
                )
            )
            if not memberships:
                raise TenantAccessDenied("Tenant access is not authorized")

            membership_ids = [membership.id for membership in memberships]
            role_rows = list(
                session.scalars(
                    select(RoleAssignment)
                    .where(
                        RoleAssignment.tenant_id == tenant_id,
                        RoleAssignment.membership_id.in_(membership_ids),
                        or_(
                            RoleAssignment.expires_at.is_(None),
                            RoleAssignment.expires_at > evaluated_at,
                        ),
                    )
                    .order_by(RoleAssignment.membership_id, RoleAssignment.role)
                )
            )
            grant_rows = list(
                session.scalars(
                    select(PermissionGrant)
                    .outerjoin(
                        Campaign,
                        and_(
                            Campaign.tenant_id == PermissionGrant.tenant_id,
                            Campaign.id == PermissionGrant.campaign_id,
                        ),
                    )
                    .outerjoin(
                        Workspace,
                        and_(
                            Workspace.tenant_id == PermissionGrant.tenant_id,
                            Workspace.campaign_id == PermissionGrant.campaign_id,
                            Workspace.id == PermissionGrant.workspace_id,
                        ),
                    )
                    .where(
                        PermissionGrant.tenant_id == tenant_id,
                        PermissionGrant.membership_id.in_(membership_ids),
                        PermissionGrant.status == "ACTIVE",
                        PermissionGrant.valid_from <= evaluated_at,
                        or_(
                            PermissionGrant.expires_at.is_(None),
                            PermissionGrant.expires_at > evaluated_at,
                        ),
                        or_(
                            PermissionGrant.campaign_id.is_(None),
                            Campaign.status.in_(("DRAFT", "ACTIVE")),
                        ),
                        or_(
                            PermissionGrant.workspace_id.is_(None),
                            Workspace.status == "ACTIVE",
                        ),
                    )
                    .order_by(
                        PermissionGrant.membership_id,
                        PermissionGrant.action,
                        PermissionGrant.resource_type,
                        PermissionGrant.resource_id,
                        PermissionGrant.id,
                    )
                )
            )

        roles_by_membership: dict[UUID, list[str]] = {
            membership.id: [] for membership in memberships
        }
        grants_by_membership: dict[UUID, list[EffectivePermissionGrant]] = {
            membership.id: [] for membership in memberships
        }
        membership_by_id = {membership.id: membership for membership in memberships}
        for role in role_rows:
            roles_by_membership[role.membership_id].append(role.role)
        for grant in grant_rows:
            membership = membership_by_id[grant.membership_id]
            if membership.campaign_id is not None and grant.campaign_id != membership.campaign_id:
                raise AuthorizationDataError(
                    "Campaign-scoped membership contains an out-of-scope permission grant"
                )
            grants_by_membership[grant.membership_id].append(
                EffectivePermissionGrant(
                    grant_id=grant.id,
                    campaign_id=grant.campaign_id,
                    workspace_id=grant.workspace_id,
                    action=grant.action,
                    resource_type=grant.resource_type,
                    resource_id=grant.resource_id,
                    purpose=grant.purpose,
                    approval_receipt_id=grant.approval_receipt_id,
                )
            )

        return TenantAuthorizationContext(
            principal_id=application_principal.id,
            tenant_id=tenant_id,
            evaluated_at=evaluated_at,
            memberships=tuple(
                EffectiveMembership(
                    membership_id=membership.id,
                    campaign_id=membership.campaign_id,
                    roles=tuple(roles_by_membership[membership.id]),
                    grants=tuple(grants_by_membership[membership.id]),
                )
                for membership in memberships
            ),
        )
