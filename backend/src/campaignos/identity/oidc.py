"""Standards-based OIDC JWT validation with a fixed algorithm allow-list."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

import jwt
from jwt import PyJWKClient
from pydantic import ValidationError

from campaignos.config import Settings
from campaignos.identity.models import AuthenticatedPrincipal


class AuthenticationError(ValueError):
    """A sanitized authentication failure safe to expose as a 401 response."""


class TokenVerifier(Protocol):
    def verify(self, token: str) -> AuthenticatedPrincipal:
        """Verify a bearer token and return a trusted minimal principal."""

    def readiness(self) -> tuple[bool, str]:
        """Check whether the verifier's signing-key dependency is available."""


class UnavailableTokenVerifier:
    """Fail-closed verifier used when local OIDC configuration is absent."""

    def verify(self, token: str) -> AuthenticatedPrincipal:
        del token
        raise AuthenticationError("Identity service is not configured")

    def readiness(self) -> tuple[bool, str]:
        return False, "OIDC is not configured"


class OidcTokenVerifier:
    """Validate issuer, audience, signature, time and token-use claims."""

    def __init__(self, settings: Settings) -> None:
        if not settings.oidc_configured:
            raise ValueError("OIDC verifier requires complete identity configuration")
        self._settings = settings
        self._jwks = PyJWKClient(
            settings.oidc_jwks_url or "",
            cache_keys=True,
            cache_jwk_set=True,
            lifespan=settings.oidc_jwks_cache_seconds,
            timeout=settings.oidc_jwks_timeout_seconds,
        )

    def readiness(self) -> tuple[bool, str]:
        try:
            self._jwks.get_jwk_set(refresh=False)
        except Exception:  # Dependency health must fail closed without leaking provider details.
            return False, "OIDC signing keys are unavailable"
        return True, "OIDC signing keys are available"

    def verify(self, token: str) -> AuthenticatedPrincipal:
        if not token or len(token) > 16_384:
            raise AuthenticationError("Invalid bearer token")

        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != self._settings.oidc_algorithm:
                raise AuthenticationError("Token signing algorithm is not allowed")
            if not isinstance(header.get("kid"), str) or not header["kid"]:
                raise AuthenticationError("Token signing key identifier is missing")

            signing_key = self._jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=[self._settings.oidc_algorithm],
                audience=self._settings.oidc_audience,
                issuer=self._settings.oidc_issuer,
                leeway=self._settings.oidc_clock_skew_seconds,
                options={
                    "require": ["sub", "iss", "aud", "exp", "iat"],
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                    "verify_iss": True,
                    "verify_aud": True,
                },
            )

            expected_use = self._settings.oidc_token_use
            if claims.get("token_use") != expected_use:
                raise AuthenticationError("Token use is not allowed")

            audience_claim = claims["aud"]
            if isinstance(audience_claim, list):
                if not audience_claim or not all(isinstance(item, str) for item in audience_claim):
                    raise AuthenticationError("Invalid bearer token")
                if len(audience_claim) > 1 and claims.get("azp") != self._settings.oidc_audience:
                    raise AuthenticationError("Token authorized party is not allowed")
            elif not isinstance(audience_claim, str):
                raise AuthenticationError("Invalid bearer token")
            audience = self._settings.oidc_audience or ""
            return AuthenticatedPrincipal(
                subject=claims["sub"],
                issuer=claims["iss"],
                audience=audience,
                display_name=claims.get("name"),
                email=claims.get("email"),
                session_id=claims.get("jti"),
                authenticated_at=datetime.now(UTC),
            )
        except AuthenticationError:
            raise
        except (jwt.PyJWTError, ValidationError, KeyError, TypeError, ValueError) as exc:
            raise AuthenticationError("Invalid bearer token") from exc
