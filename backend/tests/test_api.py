from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.config import Environment, Settings
from campaignos.identity.authorization import (
    AuthorizationDataError,
    AuthorizationDirectoryUnavailable,
    EffectiveMembership,
    EffectivePermissionGrant,
    TenantAccessDenied,
    TenantAuthorizationContext,
)
from campaignos.identity.models import AuthenticatedPrincipal

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
APPLICATION_PRINCIPAL_ID = UUID("22222222-2222-4222-8222-222222222222")
MEMBERSHIP_ID = UUID("33333333-3333-4333-8333-333333333333")
CAMPAIGN_ID = UUID("44444444-4444-4444-8444-444444444444")
GRANT_ID = UUID("55555555-5555-4555-8555-555555555555")


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


class FakeMembershipDirectory:
    def __init__(self, failure: Exception | None = None) -> None:
        self.failure = failure

    def load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        *,
        evaluated_at: datetime | None = None,
    ) -> TenantAuthorizationContext:
        del evaluated_at
        if self.failure is not None:
            raise self.failure
        assert tenant_id == TENANT_ID
        assert principal.subject == "user-123"
        evaluated = datetime(2026, 7, 19, tzinfo=UTC)
        return TenantAuthorizationContext(
            principal_id=APPLICATION_PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=evaluated,
            memberships=(
                EffectiveMembership(
                    membership_id=MEMBERSHIP_ID,
                    campaign_id=CAMPAIGN_ID,
                    roles=("operator",),
                    grants=(
                        EffectivePermissionGrant(
                            grant_id=GRANT_ID,
                            campaign_id=CAMPAIGN_ID,
                            workspace_id=None,
                            action="read",
                            resource_type="campaign",
                            resource_id=str(CAMPAIGN_ID),
                            purpose="Operate assigned campaign",
                            approval_receipt_id="approval-123",
                        ),
                    ),
                ),
            ),
        )


class MismatchedTenantDirectory(FakeMembershipDirectory):
    def load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        *,
        evaluated_at: datetime | None = None,
    ) -> TenantAuthorizationContext:
        context = super().load(
            tenant_id,
            principal,
            evaluated_at=evaluated_at,
        )
        return context.model_copy(update={"tenant_id": UUID(int=0)})


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


def test_tenant_me_requires_authenticated_session() -> None:
    with TestClient(
        create_app(
            settings(),
            token_verifier=FakeVerifier(),
            membership_directory=FakeMembershipDirectory(),
        )
    ) as client:
        response = client.get(f"/api/v1/tenants/{TENANT_ID}/me")

    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"


def test_tenant_me_returns_server_owned_authorization() -> None:
    with TestClient(
        create_app(
            settings(),
            token_verifier=FakeVerifier(),
            membership_directory=FakeMembershipDirectory(),
        )
    ) as client:
        response = client.get(
            f"/api/v1/tenants/{TENANT_ID}/me",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["principal_id"] == str(APPLICATION_PRINCIPAL_ID)
    assert body["tenant_id"] == str(TENANT_ID)
    assert body["subject"] == "user-123"
    assert body["authorization_status"] == "LOADED"
    assert body["application_memberships"] == [
        {
            "membership_id": str(MEMBERSHIP_ID),
            "campaign_id": str(CAMPAIGN_ID),
            "roles": ["operator"],
            "grants": [
                {
                    "grant_id": str(GRANT_ID),
                    "campaign_id": str(CAMPAIGN_ID),
                    "workspace_id": None,
                    "action": "read",
                    "resource_type": "campaign",
                    "resource_id": str(CAMPAIGN_ID),
                    "purpose": "Operate assigned campaign",
                    "approval_receipt_id": "approval-123",
                }
            ],
        }
    ]


def test_tenant_me_denial_is_structured_and_does_not_enumerate_state() -> None:
    directory = FakeMembershipDirectory(TenantAccessDenied("internal reason"))
    with TestClient(
        create_app(
            settings(),
            token_verifier=FakeVerifier(),
            membership_directory=directory,
        )
    ) as client:
        response = client.get(
            f"/api/v1/tenants/{TENANT_ID}/me",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_DENIED"
    assert response.json()["detail"] == "Tenant access is not authorized"
    assert "internal reason" not in response.text


@pytest.mark.parametrize(
    "failure",
    [
        AuthorizationDirectoryUnavailable("database details"),
        AuthorizationDataError("corrupt grant details"),
    ],
)
def test_tenant_me_authorization_failures_are_safe_and_retryable(failure: Exception) -> None:
    with TestClient(
        create_app(
            settings(),
            token_verifier=FakeVerifier(),
            membership_directory=FakeMembershipDirectory(failure),
        )
    ) as client:
        response = client.get(
            f"/api/v1/tenants/{TENANT_ID}/me",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 503
    assert response.json()["code"] == "AUTHORIZATION_UNAVAILABLE"
    assert response.json()["detail"] == "Tenant authorization is temporarily unavailable"
    assert str(failure) not in response.text


def test_tenant_me_rejects_mismatched_directory_scope() -> None:
    with TestClient(
        create_app(
            settings(),
            token_verifier=FakeVerifier(),
            membership_directory=MismatchedTenantDirectory(),
        )
    ) as client:
        response = client.get(
            f"/api/v1/tenants/{TENANT_ID}/me",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 503
    assert response.json()["code"] == "AUTHORIZATION_UNAVAILABLE"


def test_tenant_me_rejects_invalid_tenant_uuid() -> None:
    with TestClient(
        create_app(
            settings(),
            token_verifier=FakeVerifier(),
            membership_directory=FakeMembershipDirectory(),
        )
    ) as client:
        response = client.get(
            "/api/v1/tenants/not-a-uuid/me",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_openapi_declares_bearer_auth_for_tenant_me() -> None:
    with TestClient(create_app(settings(), token_verifier=FakeVerifier())) as client:
        document = client.get("/api/v1/openapi.json").json()

    security = document["paths"]["/api/v1/tenants/{tenant_id}/me"]["get"]["security"]
    assert security == [{"OIDC bearer token": []}]


class FakeCampaignDirectory:
    def __init__(self, failure: Exception | None = None) -> None:
        self.failure = failure

    def get(self, tenant_id: UUID, campaign_id: UUID):
        from campaignos.campaigns import CampaignProjection

        if self.failure is not None:
            raise self.failure
        return CampaignProjection(
            id=campaign_id,
            tenant_id=tenant_id,
            slug="antigua-2027",
            name="Antigua 2027",
            jurisdiction="Antigua Guatemala",
            stage="PRECAMPAIGN",
            status="ACTIVE",
            version=1,
        )


def test_campaign_read_requires_exact_server_owned_grant() -> None:
    with TestClient(
        create_app(
            settings(),
            token_verifier=FakeVerifier(),
            membership_directory=FakeMembershipDirectory(),
            campaign_directory=FakeCampaignDirectory(),
        )
    ) as client:
        response = client.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}",
            headers={"Authorization": "Bearer valid-token"},
        )
        denied = client.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{UUID(int=9)}",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 200
    assert response.json()["id"] == str(CAMPAIGN_ID)
    assert denied.status_code == 403
    assert denied.json()["code"] == "AUTHORIZATION_DENIED"


def test_campaign_read_sanitizes_missing_and_unavailable_data() -> None:
    from campaignos.campaigns import CampaignDirectoryUnavailable, CampaignNotFound

    for failure, expected_status, expected_code in (
        (CampaignNotFound("private"), 404, "RESOURCE_NOT_FOUND"),
        (CampaignDirectoryUnavailable("private"), 503, "AUTHORIZATION_UNAVAILABLE"),
    ):
        with TestClient(
            create_app(
                settings(),
                token_verifier=FakeVerifier(),
                membership_directory=FakeMembershipDirectory(),
                campaign_directory=FakeCampaignDirectory(failure),
            )
        ) as client:
            response = client.get(
                f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}",
                headers={"Authorization": "Bearer valid-token"},
            )
        assert response.status_code == expected_status
        assert response.json()["code"] == expected_code
        assert "private" not in response.text
