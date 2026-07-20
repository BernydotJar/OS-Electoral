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


def current_principal(
    request: Request,
    credentials: BearerCredentials,
) -> AuthenticatedPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid session is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        verifier = cast(TokenVerifier, request.app.state.token_verifier)
        return verifier.verify(credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        ) from exc


CurrentPrincipal = Annotated[AuthenticatedPrincipal, Depends(current_principal)]


def current_tenant_authorization(
    request: Request,
    tenant_id: UUID,
    principal: CurrentPrincipal,
) -> TenantAuthorizationContext:
    """Resolve current server-owned authorization for the selected tenant."""
    directory = cast(MembershipDirectory, request.app.state.membership_directory)
    try:
        authorization = directory.load(tenant_id, principal)
        if authorization.tenant_id != tenant_id:
            raise AuthorizationDataError(
                "Membership directory returned a mismatched tenant context"
            )
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


CurrentTenantAuthorization = Annotated[
    TenantAuthorizationContext, Depends(current_tenant_authorization)
]
