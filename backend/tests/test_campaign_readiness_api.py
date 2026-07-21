from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.campaigns import (
    CampaignReadinessEvidence,
    CampaignReadinessInput,
    CampaignReadinessNotFound,
    CampaignReadinessUnavailable,
    assess_campaign_readiness,
)
from campaignos.config import Environment, Settings
from campaignos.identity.authorization import (
    EffectiveMembership,
    EffectivePermissionGrant,
    TenantAccessDenied,
    TenantAuthorizationContext,
)
from campaignos.identity.models import AuthenticatedPrincipal

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
FOREIGN_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
PRINCIPAL_ID = UUID("33333333-3333-4333-8333-333333333333")
MEMBERSHIP_ID = UUID("44444444-4444-4444-8444-444444444444")
CAMPAIGN_ID = UUID("55555555-5555-4555-8555-555555555555")
FOREIGN_CAMPAIGN_ID = UUID("66666666-6666-4666-8666-666666666666")
WORKSPACE_ID = UUID("77777777-7777-4777-8777-777777777777")
GRANT_ID = UUID("88888888-8888-4888-8888-888888888888")
AUDIT_ID = UUID("99999999-9999-4999-8999-999999999999")
PURPOSE = "Assess assigned campaign readiness"


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105 - deterministic fixture.
        return AuthenticatedPrincipal(
            subject="readiness-user",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            session_id="session-readiness",
            authenticated_at=datetime(2026, 7, 21, tzinfo=UTC),
        )

    def readiness(self) -> tuple[bool, str]:
        return True, "ready"


class Directory:
    def __init__(
        self,
        *,
        include_grant: bool = True,
        action: str = "read",
        resource_type: str = "campaign_readiness",
        resource_id: str | None = None,
        purpose: str = PURPOSE,
        campaign_id: UUID = CAMPAIGN_ID,
        workspace_id: UUID | None = None,
    ) -> None:
        self.include_grant = include_grant
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id or str(campaign_id)
        self.purpose = purpose
        self.campaign_id = campaign_id
        self.workspace_id = workspace_id

    def load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        *,
        evaluated_at: datetime | None = None,
    ) -> TenantAuthorizationContext:
        del principal, evaluated_at
        if tenant_id != TENANT_ID:
            raise TenantAccessDenied("foreign tenant")
        grants: tuple[EffectivePermissionGrant, ...]
        if self.include_grant:
            grants = (
                EffectivePermissionGrant(
                    grant_id=GRANT_ID,
                    campaign_id=self.campaign_id,
                    workspace_id=self.workspace_id,
                    action=self.action,
                    resource_type=self.resource_type,
                    resource_id=self.resource_id,
                    purpose=self.purpose,
                    approval_receipt_id="approval-readiness",
                ),
            )
        else:
            grants = ()
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=datetime(2026, 7, 21, tzinfo=UTC),
            memberships=(
                EffectiveMembership(
                    membership_id=MEMBERSHIP_ID,
                    campaign_id=self.campaign_id,
                    roles=("operator",),
                    grants=grants,
                ),
            ),
        )


class Reader:
    def __init__(
        self,
        *,
        failure: Exception | None = None,
        tenant_id: UUID = TENANT_ID,
        campaign_id: UUID = CAMPAIGN_ID,
    ) -> None:
        self.failure = failure
        self.tenant_id = tenant_id
        self.campaign_id = campaign_id
        self.calls: list[tuple[UUID, UUID, dict[str, Any]]] = []

    def get(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        **kwargs: Any,
    ) -> CampaignReadinessEvidence:
        self.calls.append((tenant_id, campaign_id, kwargs))
        if self.failure is not None:
            raise self.failure
        return CampaignReadinessEvidence(
            readiness=assess_campaign_readiness(
                CampaignReadinessInput(
                    tenant_id=self.tenant_id,
                    campaign_id=self.campaign_id,
                    campaign_version=2,
                    campaign_status="ACTIVE",
                    name="Campaign A",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    active_workspace_count=1,
                )
            ),
            audit_event_id=AUDIT_ID,
        )


def settings() -> Settings:
    return Settings(environment=Environment.TEST, expose_api_docs=True)


def client(directory: Directory, reader: Reader) -> TestClient:
    return TestClient(
        create_app(
            settings(),
            token_verifier=Verifier(),
            membership_directory=directory,
            campaign_readiness_reader=reader,
        )
    )


def test_readiness_requires_exact_grant_and_forwards_audit_binding() -> None:
    reader = Reader()
    with client(Directory(), reader) as api:
        response = api.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/readiness",
            headers={
                "Authorization": "Bearer valid-token",
                "X-Correlation-ID": "readiness-api-1",
            },
        )

    assert response.status_code == 200
    assert response.json()["readiness"]["status"] == "READY_FOR_GUIDED_INTAKE"
    assert response.json()["readiness"]["readiness_scope"] == "OPERATIONAL_SETUP_ONLY"
    assert response.json()["readiness"]["limitation_codes"] == [
        "NOT_A_HUMAN_APPROVAL",
        "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT",
    ]
    assert response.json()["audit_event_id"] == str(AUDIT_ID)
    assert len(reader.calls) == 1
    tenant_id, campaign_id, kwargs = reader.calls[0]
    assert tenant_id == TENANT_ID
    assert campaign_id == CAMPAIGN_ID
    assert kwargs == {
        "principal_id": PRINCIPAL_ID,
        "authorization_grant_id": GRANT_ID,
        "approval_receipt_id": "approval-readiness",
        "authorization_purpose": PURPOSE,
        "correlation_id": "readiness-api-1",
    }


@pytest.mark.parametrize(
    ("directory", "campaign_id"),
    [
        (Directory(include_grant=False), CAMPAIGN_ID),
        (Directory(action="update"), CAMPAIGN_ID),
        (Directory(resource_type="campaign"), CAMPAIGN_ID),
        (Directory(resource_id=str(FOREIGN_CAMPAIGN_ID)), CAMPAIGN_ID),
        (Directory(purpose="Operate assigned campaign"), CAMPAIGN_ID),
        (Directory(campaign_id=FOREIGN_CAMPAIGN_ID), CAMPAIGN_ID),
        (Directory(workspace_id=WORKSPACE_ID), CAMPAIGN_ID),
        (Directory(), FOREIGN_CAMPAIGN_ID),
    ],
    ids=[
        "revoked-or-absent-grant",
        "wrong-action",
        "wrong-resource-type",
        "wrong-resource-id",
        "wrong-purpose",
        "wrong-campaign-scope",
        "wrong-workspace-scope",
        "bola-foreign-campaign",
    ],
)
def test_readiness_denies_mismatched_or_absent_grants_before_persistence(
    directory: Directory,
    campaign_id: UUID,
) -> None:
    reader = Reader()
    with client(directory, reader) as api:
        response = api.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{campaign_id}/readiness",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_DENIED"
    assert reader.calls == []


def test_readiness_denies_foreign_tenant_before_persistence() -> None:
    reader = Reader()
    with client(Directory(), reader) as api:
        response = api.get(
            f"/api/v1/tenants/{FOREIGN_TENANT_ID}/campaigns/{CAMPAIGN_ID}/readiness",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_DENIED"
    assert reader.calls == []


@pytest.mark.parametrize(
    ("failure", "status_code", "code"),
    [
        (CampaignReadinessNotFound("private campaign detail"), 404, "RESOURCE_NOT_FOUND"),
        (
            CampaignReadinessUnavailable("private database detail"),
            503,
            "AUTHORIZATION_UNAVAILABLE",
        ),
    ],
)
def test_readiness_sanitizes_persistence_failures(
    failure: Exception,
    status_code: int,
    code: str,
) -> None:
    reader = Reader(failure=failure)
    with client(Directory(), reader) as api:
        response = api.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/readiness",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == status_code
    assert response.json()["code"] == code
    assert "private" not in response.text
    assert len(reader.calls) == 1


@pytest.mark.parametrize(
    ("tenant_id", "campaign_id"),
    [
        (FOREIGN_TENANT_ID, CAMPAIGN_ID),
        (TENANT_ID, FOREIGN_CAMPAIGN_ID),
    ],
)
def test_readiness_rejects_adapter_scope_leak(
    tenant_id: UUID,
    campaign_id: UUID,
) -> None:
    reader = Reader(tenant_id=tenant_id, campaign_id=campaign_id)
    with client(Directory(), reader) as api:
        response = api.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/readiness",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 503
    assert response.json()["code"] == "AUTHORIZATION_UNAVAILABLE"
    assert len(reader.calls) == 1


def test_openapi_exposes_typed_audited_readiness_with_bearer_security() -> None:
    with client(Directory(), Reader()) as api:
        document = api.get("/api/v1/openapi.json").json()

    path = "/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/readiness"
    operation = document["paths"][path]["get"]
    assert operation["security"] == [{"OIDC bearer token": []}]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/CampaignReadinessEvidence"
    }
    assert (
        "not a political, legal, financial, security, publication, production"
        in operation["description"]
    )
