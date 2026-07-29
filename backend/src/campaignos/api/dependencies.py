"""HTTP dependencies for authenticated identity."""

from __future__ import annotations

from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from campaignos.identity.authorization import (
    AuthorizationDataError,
    AuthorizationDirectoryUnavailable,
    MembershipDirectory,
    TenantAccessDenied,
    TenantAuthorizationContext,
)
from campaignos.identity.models import AuthenticatedPrincipal
from campaignos.identity.oidc import AuthenticationError, TokenVerifier

bearer = HTTPBearer(auto_error=False, scheme_name="OIDC bearer token")
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Security(bearer)]


def authenticated_principal_from_request(request: Request) -> AuthenticatedPrincipal:
    """Verify the bearer token once and cache only the trusted principal on the request."""
    cached = getattr(request.state, "authenticated_principal", None)
    if isinstance(cached, AuthenticatedPrincipal):
        return cached
    authorization = request.headers.get("authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid session is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        verifier = cast(TokenVerifier, request.app.state.token_verifier)
        principal = verifier.verify(token.strip())
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        ) from exc
    request.state.authenticated_principal = principal
    return principal


def current_principal(
    request: Request,
    credentials: BearerCredentials,
) -> AuthenticatedPrincipal:
    del credentials
    return authenticated_principal_from_request(request)


CurrentPrincipal = Annotated[AuthenticatedPrincipal, Depends(current_principal)]


def tenant_authorization_from_request(
    request: Request,
    tenant_id: UUID,
    principal: AuthenticatedPrincipal,
) -> TenantAuthorizationContext:
    """Load and cache one exact server-owned tenant authorization context."""
    cached = getattr(request.state, "tenant_authorization", None)
    if isinstance(cached, TenantAuthorizationContext) and cached.tenant_id == tenant_id:
        return cached
    directory = cast(MembershipDirectory, request.app.state.membership_directory)
    try:
        authorization = directory.load(tenant_id, principal)
        if authorization.tenant_id != tenant_id:
            raise AuthorizationDataError(
                "Membership directory returned a mismatched tenant context"
            )
        request.state.tenant_authorization = authorization
        return authorization
    except TenantAccessDenied as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access is not authorized",
        ) from exc
    except AuthorizationDirectoryUnavailable as exc:
        request.app.state.logger.warning(
            "authorization_directory_unavailable",
            extra={
                "correlation_id": getattr(request.state, "correlation_id", "unknown"),
                "tenant_id": str(tenant_id),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant authorization is temporarily unavailable",
        ) from exc
    except AuthorizationDataError as exc:
        request.app.state.logger.error(
            "authorization_data_invariant_failed",
            extra={
                "correlation_id": getattr(request.state, "correlation_id", "unknown"),
                "tenant_id": str(tenant_id),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant authorization is temporarily unavailable",
        ) from exc


def current_tenant_authorization(
    request: Request,
    tenant_id: UUID,
    principal: CurrentPrincipal,
) -> TenantAuthorizationContext:
    """Resolve current server-owned authorization for the selected tenant."""
    return tenant_authorization_from_request(request, tenant_id, principal)


CurrentTenantAuthorization = Annotated[
    TenantAuthorizationContext, Depends(current_tenant_authorization)
]
