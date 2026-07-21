from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.campaigns import CampaignPage, CampaignProjection
from campaignos.config import Environment, Settings
from campaignos.identity.authorization import (
    EffectiveMembership,
    EffectivePermissionGrant,
    TenantAuthorizationContext,
)
from campaignos.identity.models import AuthenticatedPrincipal

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
PRINCIPAL_ID = UUID("22222222-2222-4222-8222-222222222222")
MEMBERSHIP_ID = UUID("33333333-3333-4333-8333-333333333333")
CAMPAIGN_A = UUID("44444444-4444-4444-8444-444444444444")
CAMPAIGN_B = UUID("55555555-5555-4555-8555-555555555555")
FOREIGN_CAMPAIGN = UUID("66666666-6666-4666-8666-666666666666")


class FakeVerifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105 - deterministic fixture.
        return AuthenticatedPrincipal(
            subject="user-123",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            display_name="Test User",
            email="user@example.test",
            session_id="session-1",
            authenticated_at=datetime(2026, 7, 20, tzinfo=UTC),
        )

    def readiness(self) -> tuple[bool, str]:
        return True, "ready"


class FakeMembershipDirectory:
    def load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        *,
        evaluated_at: datetime | None = None,
    ) -> TenantAuthorizationContext:
        del principal, evaluated_at
        grants = tuple(
            EffectivePermissionGrant(
                grant_id=UUID(int=index + 10),
                campaign_id=campaign_id,
                workspace_id=None,
                action="read",
                resource_type="campaign",
                resource_id=str(campaign_id),
                purpose="Operate assigned campaign",
                approval_receipt_id=f"approval-{index}",
            )
            for index, campaign_id in enumerate((CAMPAIGN_A, CAMPAIGN_B))
        )
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=datetime(2026, 7, 20, tzinfo=UTC),
            memberships=(
                EffectiveMembership(
                    membership_id=MEMBERSHIP_ID,
                    campaign_id=None,
                    roles=("operator",),
                    grants=grants,
                ),
            ),
        )


class FakeCampaignDirectory:
    def __init__(self, *, leak_foreign: bool = False) -> None:
        self.leak_foreign = leak_foreign
        self.calls: list[tuple[tuple[UUID, ...], int, UUID | None]] = []

    def get(self, tenant_id: UUID, campaign_id: UUID) -> CampaignProjection:
        raise AssertionError("get is not expected")

    def list_authorized(
        self,
        tenant_id: UUID,
        campaign_ids: tuple[UUID, ...],
        *,
        limit: int,
        cursor: UUID | None,
    ) -> CampaignPage:
        self.calls.append((campaign_ids, limit, cursor))
        selected_id = FOREIGN_CAMPAIGN if self.leak_foreign else CAMPAIGN_A
        return CampaignPage(
            items=(
                CampaignProjection(
                    id=selected_id,
                    tenant_id=tenant_id,
                    slug="campaign-a",
                    name="Campaign A",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=1,
                ),
            ),
            next_cursor=CAMPAIGN_A,
        )


def settings() -> Settings:
    return Settings(environment=Environment.TEST, expose_api_docs=True)


def test_list_campaigns_passes_only_exact_authorized_ids_and_pagination() -> None:
    directory = FakeCampaignDirectory()
    with TestClient(
        create_app(
            settings(),
            token_verifier=FakeVerifier(),
            membership_directory=FakeMembershipDirectory(),
            campaign_directory=directory,
        )
    ) as client:
        response = client.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns?limit=1&cursor={UUID(int=7)}",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == str(CAMPAIGN_A)
    assert directory.calls == [((CAMPAIGN_A, CAMPAIGN_B), 1, UUID(int=7))]


def test_list_campaigns_rejects_directory_scope_leak() -> None:
    with TestClient(
        create_app(
            settings(),
            token_verifier=FakeVerifier(),
            membership_directory=FakeMembershipDirectory(),
            campaign_directory=FakeCampaignDirectory(leak_foreign=True),
        )
    ) as client:
        response = client.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 503
    assert response.json()["code"] == "AUTHORIZATION_UNAVAILABLE"


def test_list_campaigns_validates_limit_and_cursor() -> None:
    directory = FakeCampaignDirectory()
    with TestClient(
        create_app(
            settings(),
            token_verifier=FakeVerifier(),
            membership_directory=FakeMembershipDirectory(),
            campaign_directory=directory,
        )
    ) as client:
        too_large = client.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns?limit=101",
            headers={"Authorization": "Bearer valid-token"},
        )
        bad_cursor = client.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns?cursor=not-a-uuid",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert too_large.status_code == 422
    assert bad_cursor.status_code == 422
    assert directory.calls == []
