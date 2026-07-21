from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.config import Environment, Settings
from campaignos.identity.authorization import (
    EffectiveMembership,
    EffectivePermissionGrant,
    TenantAuthorizationContext,
)
from campaignos.identity.models import AuthenticatedPrincipal
from campaignos.workspaces import WorkspaceProjection, WorkspaceWriteEvidence

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
PRINCIPAL_ID = UUID("22222222-2222-4222-8222-222222222222")
MEMBERSHIP_ID = UUID("33333333-3333-4333-8333-333333333333")
CAMPAIGN_ID = UUID("44444444-4444-4444-8444-444444444444")
WORKSPACE_ID = UUID("55555555-5555-4555-8555-555555555555")
GRANT_ID = UUID("66666666-6666-4666-8666-666666666666")
AUDIT_ID = UUID("77777777-7777-4777-8777-777777777777")
OUTBOX_ID = UUID("88888888-8888-4888-8888-888888888888")


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105
        return AuthenticatedPrincipal(
            subject="user-1",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            authenticated_at=datetime(2026, 7, 21, tzinfo=UTC),
        )

    def readiness(self) -> tuple[bool, str]:
        return True, "ready"


class Database:
    def readiness(self) -> tuple[bool, str]:
        return True, "ready"

    def dispose(self) -> None:
        return None


class Directory:
    def __init__(self, action: str = "create") -> None:
        self.action = action

    def load(
        self, tenant_id: UUID, principal: AuthenticatedPrincipal, **_: object
    ) -> TenantAuthorizationContext:
        del principal
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=datetime(2026, 7, 21, tzinfo=UTC),
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
                            resource_type="workspace",
                            resource_id=f"campaign:{CAMPAIGN_ID}:workspaces",
                            purpose="Configure assigned campaign workspace",
                            approval_receipt_id="approval-workspace-1",
                        ),
                    ),
                ),
            ),
        )


class Writer:
    def __init__(self) -> None:
        self.called = False
        self.key: str | None = None

    def create(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> WorkspaceWriteEvidence:
        assert tenant_id == TENANT_ID
        assert campaign_id == CAMPAIGN_ID
        self.called = True
        self.key = str(kwargs["idempotency_key"])
        return WorkspaceWriteEvidence(
            workspace=WorkspaceProjection(
                id=WORKSPACE_ID,
                tenant_id=TENANT_ID,
                campaign_id=CAMPAIGN_ID,
                slug="war-room",
                name="War Room",
                status="ACTIVE",
                version=1,
            ),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )


def client(directory: Directory, writer: Writer) -> TestClient:
    return TestClient(
        create_app(
            Settings(environment=Environment.TEST, expose_api_docs=True),
            token_verifier=Verifier(),
            database=Database(),
            membership_directory=directory,
            workspace_writer=writer,
        )
    )


def test_create_workspace_requires_exact_grant() -> None:
    writer = Writer()
    with client(Directory(action="read"), writer) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/workspaces",
            headers={"Authorization": "Bearer valid-token", "Idempotency-Key": "workspace-1"},
            json={"slug": "war-room", "name": "War Room"},
        )
    assert response.status_code == 403
    assert writer.called is False


def test_create_workspace_requires_idempotency_after_authorization() -> None:
    writer = Writer()
    with client(Directory(), writer) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/workspaces",
            headers={"Authorization": "Bearer valid-token"},
            json={"slug": "war-room", "name": "War Room"},
        )
    assert response.status_code == 428
    assert writer.called is False


def test_create_workspace_returns_transactional_evidence() -> None:
    writer = Writer()
    with client(Directory(), writer) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/workspaces",
            headers={
                "Authorization": "Bearer valid-token",
                "Idempotency-Key": "workspace-create-1",
                "X-Correlation-ID": "workspace-correlation-1",
            },
            json={"slug": "war-room", "name": "War Room"},
        )
    assert response.status_code == 201
    assert writer.key == "workspace-create-1"
    assert response.json()["workspace"]["id"] == str(WORKSPACE_ID)
    assert response.json()["audit_event_id"] == str(AUDIT_ID)
    assert response.json()["outbox_event_id"] == str(OUTBOX_ID)
