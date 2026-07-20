"""Identity verification and server-owned authorization boundaries."""

from campaignos.identity.authorization import (
    AuthorizationDataError,
    AuthorizationDirectoryUnavailable,
    EffectiveMembership,
    EffectivePermissionGrant,
    MembershipDirectory,
    SqlAlchemyMembershipDirectory,
    TenantAccessDenied,
    TenantAuthorizationContext,
    UnavailableMembershipDirectory,
)
from campaignos.identity.models import AuthenticatedPrincipal
from campaignos.identity.oidc import AuthenticationError, OidcTokenVerifier, TokenVerifier

__all__ = [
    "AuthenticatedPrincipal",
    "AuthenticationError",
    "AuthorizationDataError",
    "AuthorizationDirectoryUnavailable",
    "EffectiveMembership",
    "EffectivePermissionGrant",
    "MembershipDirectory",
    "OidcTokenVerifier",
    "SqlAlchemyMembershipDirectory",
    "TenantAccessDenied",
    "TenantAuthorizationContext",
    "TokenVerifier",
    "UnavailableMembershipDirectory",
]
