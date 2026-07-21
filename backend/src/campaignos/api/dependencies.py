"""HTTP dependencies for authenticated identity."""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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
