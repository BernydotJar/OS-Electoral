from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from campaignos.config import Environment, Settings
from campaignos.identity.oidc import (
    AuthenticationError,
    DevelopmentTokenVerifier,
    OidcTokenVerifier,
)

ISSUER = "https://identity.example.test/"
AUDIENCE = "campaignos-test"


def settings() -> Settings:
    return Settings(
        environment=Environment.TEST,
        oidc_issuer=ISSUER,
        oidc_audience=AUDIENCE,
        oidc_jwks_url=f"{ISSUER}.well-known/jwks.json",
        oidc_clock_skew_seconds=0,
    )


def token(private_key: object, **overrides: object) -> str:
    now = datetime.now(UTC)
    claims: dict[str, object] = {
        "sub": "user-123",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "token_use": "id",
        "jti": "session-123",
        "name": "Test User",
        "email": "user@example.test",
        "email_verified": True,
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "key-1"})


def verifier_with_key(private_key: object) -> OidcTokenVerifier:
    verifier = OidcTokenVerifier(settings())
    verifier._jwks.get_signing_key_from_jwt = lambda _: SimpleNamespace(  # type: ignore[method-assign]
        key=private_key.public_key()
    )
    return verifier


def test_valid_oidc_token_produces_minimal_principal() -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    principal = verifier_with_key(key).verify(token(key))

    assert principal.principal_id == "human:user-123"
    assert principal.session_id == "session-123"
    assert principal.email == "user@example.test"
    assert principal.email_verified is True
    assert principal.authenticated_at < principal.expires_at  # type: ignore[operator]
    assert not hasattr(principal, "roles")


def test_multiple_audiences_require_matching_authorized_party() -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    principal = verifier_with_key(key).verify(
        token(key, aud=[AUDIENCE, "another-client"], azp=AUDIENCE)
    )
    assert principal.audience == AUDIENCE

    for azp in (None, "another-client"):
        with pytest.raises(AuthenticationError, match="authorized party"):
            verifier_with_key(key).verify(token(key, aud=[AUDIENCE, "another-client"], azp=azp))


def test_readiness_checks_jwks_dependency_without_leaking_error() -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = verifier_with_key(key)
    verifier._jwks.get_jwk_set = lambda **_: object()  # type: ignore[method-assign]
    assert verifier.readiness() == (True, "OIDC signing keys are available")

    def unavailable(**_: object) -> object:
        raise OSError("sensitive provider detail")

    verifier._jwks.get_jwk_set = unavailable  # type: ignore[method-assign]
    assert verifier.readiness() == (False, "OIDC signing keys are unavailable")


@pytest.mark.parametrize(
    ("claim", "value"),
    [
        ("iss", "https://attacker.example/"),
        ("aud", "different-audience"),
        ("token_use", "access"),
    ],
)
def test_wrong_security_claim_is_rejected(claim: str, value: str) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(AuthenticationError):
        verifier_with_key(key).verify(token(key, **{claim: value}))


@pytest.mark.parametrize(
    ("claim", "value"),
    [
        ("email", 123),
        ("email_verified", "true"),
    ],
)
def test_malformed_identity_claim_is_rejected(claim: str, value: object) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(AuthenticationError):
        verifier_with_key(key).verify(token(key, **{claim: value}))


def test_expired_token_is_rejected() -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    expired = datetime.now(UTC) - timedelta(minutes=1)
    with pytest.raises(AuthenticationError):
        verifier_with_key(key).verify(token(key, exp=expired))


def test_token_without_kid_is_rejected_before_key_fetch() -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(UTC)
    encoded = jwt.encode(
        {
            "sub": "user-123",
            "iss": ISSUER,
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "token_use": "id",
        },
        key,
        algorithm="RS256",
    )
    with pytest.raises(AuthenticationError, match="identifier"):
        OidcTokenVerifier(settings()).verify(encoded)


def test_development_verifier_accepts_only_the_configured_local_token() -> None:
    local_settings = Settings(
        environment=Environment.DEVELOPMENT,
        development_access_token="campaignos-local-development-token",  # noqa: S106
        development_principal_subject="local-operator",
        development_principal_display_name="Operador local",
        development_principal_email="operator@localhost",
    )
    verifier = DevelopmentTokenVerifier(local_settings)

    principal = verifier.verify("campaignos-local-development-token")

    assert principal.subject == "local-operator"
    assert principal.issuer == "urn:campaignos:development"
    assert principal.audience == "campaignos-local"
    assert principal.display_name == "Operador local"
    assert principal.email == "operator@localhost"
    assert principal.email_verified is True
    assert principal.session_id is not None
    assert "campaignos-local-development-token" not in principal.session_id
    assert not hasattr(principal, "roles")
    assert verifier.readiness() == (True, "Development identity is configured")

    with pytest.raises(AuthenticationError, match="Invalid bearer token"):
        verifier.verify("wrong-development-token")
