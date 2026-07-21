from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.campaigns import CampaignProjection, CampaignWriteEvidence
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
CAMPAIGN_ID = UUID("44444444-4444-4444-8444-444444444444")
GRANT_ID = UUID("55555555-5555-4555-8555-555555555555")
AUDIT_ID = UUID("66666666-6666-4666-8666-666666666666")
OUTBOX_ID = UUID("77777777-7777-4777-8777-777777777777")


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105 - deterministic non-secret fixture.
        return AuthenticatedPrincipal(
            subject="user-1",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            authenticated_at=datetime(2026, 7, 20, tzinfo=UTC),
        )

    def readiness(self) -> tuple[bool, str]:
        return True, "ready"


class Database:
    def readiness(self) -> tuple[bool, str]:
        return True, "ready"

    def dispose(self) -> None:
        return None


class Directory:
    def __init__(self, action: str = "update") -> None:
        self.action = action

    def load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        *,
        evaluated_at: datetime | None = None,
    ) -> TenantAuthorizationContext:
        del principal, evaluated_at
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=datetime(2026, 7, 20, tzinfo=UTC),
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
                            action=self.action,
                            resource_type="campaign",
                            resource_id=str(CAMPAIGN_ID),
                            purpose="Maintain assigned campaign",
                            approval_receipt_id="approval-1",
                        ),
                    ),
                ),
            ),
        )


class Writer:
    def __init__(self) -> None:
        self.expected_version: int | None = None

    def update(self, tenant_id: UUID, campaign_id: UUID, **kwargs: object) -> CampaignWriteEvidence:
        assert tenant_id == TENANT_ID
        assert campaign_id == CAMPAIGN_ID
        self.expected_version = int(kwargs["expected_version"])
        return CampaignWriteEvidence(
            campaign=CampaignProjection(
                id=CAMPAIGN_ID,
                tenant_id=TENANT_ID,
                slug="campaign",
                name="Updated",
                jurisdiction="Antigua Guatemala",
                stage="PRECAMPAIGN",
                status="ACTIVE",
                version=self.expected_version + 1,
            ),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )


def settings() -> Settings:
    return Settings(environment=Environment.TEST, expose_api_docs=True)


def client(directory: Directory, writer: Writer) -> TestClient:
    return TestClient(
        create_app(
            settings(),
            token_verifier=Verifier(),
            database=Database(),
            membership_directory=directory,
            campaign_writer=writer,
        )
    )


def test_patch_requires_exact_update_grant() -> None:
    writer = Writer()
    with client(Directory(action="read"), writer) as api:
        response = api.patch(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}",
            headers={"Authorization": "Bearer valid-token", "If-Match": '"1"'},
            json={"name": "Updated"},
        )
    assert response.status_code == 403
    assert writer.expected_version is None


def test_patch_requires_version_precondition() -> None:
    writer = Writer()
    with client(Directory(), writer) as api:
        response = api.patch(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}",
            headers={"Authorization": "Bearer valid-token"},
            json={"name": "Updated"},
        )
    assert response.status_code == 428
    assert response.json()["code"] == "VERSION_REQUIRED"


def test_patch_returns_transactional_evidence() -> None:
    writer = Writer()
    with client(Directory(), writer) as api:
        response = api.patch(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}",
            headers={
                "Authorization": "Bearer valid-token",
                "If-Match": '"3"',
                "X-Correlation-ID": "write-1",
            },
            json={"name": "Updated", "status": "ACTIVE"},
        )
    assert response.status_code == 200
    assert writer.expected_version == 3
    assert response.json()["campaign"]["version"] == 4
    assert response.json()["audit_event_id"] == str(AUDIT_ID)
    assert response.json()["outbox_event_id"] == str(OUTBOX_ID)
