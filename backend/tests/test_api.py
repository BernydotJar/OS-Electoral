from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.config import Environment, Settings
from campaignos.identity.models import AuthenticatedPrincipal


class FakeVerifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        if token != "valid-token":  # noqa: S105 - deterministic non-secret fixture.
            raise AssertionError("unexpected token")
        return AuthenticatedPrincipal(
            subject="user-123",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            display_name="Test User",
            email="user@example.test",
            session_id="session-1",
            authenticated_at=datetime(2026, 7, 18, tzinfo=UTC),
        )

    def readiness(self) -> tuple[bool, str]:
        return True, "test verifier ready"


class FakeDatabase:
    def readiness(self) -> tuple[bool, str]:
        return True, "test database ready"

    def dispose(self) -> None:
        return None


def settings() -> Settings:
    return Settings(environment=Environment.TEST, expose_api_docs=True)


def test_health_is_public_and_returns_security_headers() -> None:
    with TestClient(create_app(settings())) as client:
        response = client.get("/api/v1/health", headers={"X-Correlation-ID": "test-123"})

    assert response.status_code == 200
    assert response.json()["status"] == "UP"
    assert response.headers["x-correlation-id"] == "test-123"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_readiness_fails_closed_without_identity_configuration() -> None:
    with TestClient(create_app(settings())) as client:
        response = client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "NOT_READY"
    assert response.json()["checks"][0]["ready"] is False


def test_readiness_checks_verifier_dependency() -> None:
    with TestClient(
        create_app(
            settings(),
            token_verifier=FakeVerifier(),
            database=FakeDatabase(),
        )
    ) as client:
        response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "READY"
    assert response.json()["checks"] == [
        {"name": "identity", "ready": True, "detail": "test verifier ready"},
        {"name": "database", "ready": True, "detail": "test database ready"},
    ]


def test_missing_session_returns_structured_problem() -> None:
    with TestClient(create_app(settings(), token_verifier=FakeVerifier())) as client:
        response = client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "AUTHENTICATION_REQUIRED"
    assert body["correlation_id"] == response.headers["x-correlation-id"]


def test_me_uses_verified_identity_and_never_token_roles() -> None:
    with TestClient(create_app(settings(), token_verifier=FakeVerifier())) as client:
        response = client.get(
            "/api/v1/me",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["principal_id"] == "human:user-123"
    assert body["application_memberships"] == []
    assert body["authorization_status"] == "NOT_LOADED"
    assert "roles" not in body
    assert "tenant_id" not in body


def test_invalid_correlation_id_is_not_reflected() -> None:
    supplied = "bad\nheader"
    with TestClient(create_app(settings())) as client:
        response = client.get("/api/v1/health", headers={"X-Correlation-ID": supplied})

    assert response.status_code == 200
    assert response.headers["x-correlation-id"] != supplied


def test_openapi_declares_bearer_auth_for_me() -> None:
    with TestClient(create_app(settings(), token_verifier=FakeVerifier())) as client:
        document = client.get("/api/v1/openapi.json").json()

    security = document["paths"]["/api/v1/me"]["get"]["security"]
    assert security == [{"OIDC bearer token": []}]
