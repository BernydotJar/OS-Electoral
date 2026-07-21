from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.campaigns import (
    CampaignCreate,
    CampaignCreateConflict,
    CampaignCreateEvidence,
    CampaignCreateIdempotencyConflict,
    CampaignCreateUnavailable,
    CampaignProjection,
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
SCOPED_CAMPAIGN_ID = UUID("66666666-6666-4666-8666-666666666666")
WORKSPACE_ID = UUID("77777777-7777-4777-8777-777777777777")
GRANT_ID = UUID("88888888-8888-4888-8888-888888888888")
AUDIT_ID = UUID("99999999-9999-4999-8999-999999999999")
OUTBOX_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
PURPOSE = "Create tenant campaign"


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105 - deterministic fixture.
        return AuthenticatedPrincipal(
            subject="campaign-creator",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            session_id="session-campaign-create",
            authenticated_at=datetime(2026, 7, 21, tzinfo=UTC),
        )

    def readiness(self) -> tuple[bool, str]:
        return True, "ready"


class Directory:
    def __init__(
        self,
        *,
        include_grant: bool = True,
        action: str = "create",
        resource_type: str = "campaign_collection",
        resource_id: str | None = None,
        purpose: str = PURPOSE,
        campaign_id: UUID | None = None,
        workspace_id: UUID | None = None,
    ) -> None:
        self.include_grant = include_grant
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id or str(TENANT_ID)
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
                    approval_receipt_id="approval-campaign-create",
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


class Creator:
    def __init__(
        self,
        *,
        failure: Exception | None = None,
        tenant_id: UUID = TENANT_ID,
        overrides: dict[str, object] | None = None,
    ) -> None:
        self.failure = failure
        self.tenant_id = tenant_id
        self.overrides = overrides or {}
        self.calls: list[tuple[UUID, dict[str, Any]]] = []

    def create(self, tenant_id: UUID, **kwargs: Any) -> CampaignCreateEvidence:
        self.calls.append((tenant_id, kwargs))
        if self.failure is not None:
            raise self.failure
        campaign_request = kwargs["request"]
        assert isinstance(campaign_request, CampaignCreate)
        projection = {
            "id": CAMPAIGN_ID,
            "tenant_id": self.tenant_id,
            "slug": campaign_request.slug,
            "name": campaign_request.name,
            "jurisdiction": campaign_request.jurisdiction,
            "stage": campaign_request.stage,
            "status": "DRAFT",
            "version": 1,
        }
        projection.update(self.overrides)
        return CampaignCreateEvidence(
            campaign=CampaignProjection.model_validate(projection),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )


def settings() -> Settings:
    return Settings(environment=Environment.TEST, expose_api_docs=True)


def client(directory: Directory, creator: Creator) -> TestClient:
    return TestClient(
        create_app(
            settings(),
            token_verifier=Verifier(),
            membership_directory=directory,
            campaign_creator=creator,
        )
    )


def payload() -> dict[str, str]:
    return {
        "slug": " Municipal-2028 ",
        "name": " Municipal   Campaign 2028 ",
        "jurisdiction": " Antigua   Guatemala ",
        "stage": " PRECAMPAIGN ",
    }


def test_create_requires_exact_collection_grant_and_forwards_normalized_binding() -> None:
    creator = Creator()
    with client(Directory(), creator) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns",
            headers={
                "Authorization": "Bearer valid-token",
                "Idempotency-Key": "  campaign-create-1  ",
                "X-Correlation-ID": "campaign-create-api-1",
            },
            json=payload(),
        )

    assert response.status_code == 201
    assert response.headers["location"] == (f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}")
    assert response.headers["etag"] == '"1"'
    assert response.json()["campaign"] == {
        "id": str(CAMPAIGN_ID),
        "tenant_id": str(TENANT_ID),
        "slug": "municipal-2028",
        "name": "Municipal Campaign 2028",
        "jurisdiction": "Antigua Guatemala",
        "stage": "PRECAMPAIGN",
        "status": "DRAFT",
        "version": 1,
    }
    assert response.json()["audit_event_id"] == str(AUDIT_ID)
    assert response.json()["outbox_event_id"] == str(OUTBOX_ID)
    assert len(creator.calls) == 1
    tenant_id, kwargs = creator.calls[0]
    assert tenant_id == TENANT_ID
    assert kwargs == {
        "request": CampaignCreate.model_validate(payload()),
        "principal_id": PRINCIPAL_ID,
        "authorization_grant_id": GRANT_ID,
        "approval_receipt_id": "approval-campaign-create",
        "authorization_purpose": PURPOSE,
        "correlation_id": "campaign-create-api-1",
        "idempotency_key": "campaign-create-1",
    }


@pytest.mark.parametrize(
    "directory",
    [
        Directory(include_grant=False),
        Directory(action="read"),
        Directory(resource_type="campaign"),
        Directory(resource_id=str(FOREIGN_TENANT_ID)),
        Directory(purpose="Operate tenant campaign portfolio"),
        Directory(campaign_id=SCOPED_CAMPAIGN_ID),
        Directory(campaign_id=SCOPED_CAMPAIGN_ID, workspace_id=WORKSPACE_ID),
    ],
    ids=[
        "revoked-or-absent-grant",
        "wrong-action",
        "wrong-resource-type",
        "wrong-resource-id",
        "wrong-purpose",
        "campaign-scoped-grant",
        "workspace-scoped-grant",
    ],
)
def test_create_denies_mismatched_or_absent_grants_before_persistence(
    directory: Directory,
) -> None:
    creator = Creator()
    with client(directory, creator) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns",
            headers={
                "Authorization": "Bearer valid-token",
                "Idempotency-Key": "campaign-create-denied",
            },
            json=payload(),
        )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_DENIED"
    assert creator.calls == []


def test_create_denies_foreign_tenant_before_persistence() -> None:
    creator = Creator()
    with client(Directory(), creator) as api:
        response = api.post(
            f"/api/v1/tenants/{FOREIGN_TENANT_ID}/campaigns",
            headers={
                "Authorization": "Bearer valid-token",
                "Idempotency-Key": "campaign-create-foreign",
            },
            json=payload(),
        )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_DENIED"
    assert creator.calls == []


@pytest.mark.parametrize(
    ("idempotency_key", "status_code"),
    [
        (None, 428),
        ("   ", 428),
        ("x" * 256, 400),
    ],
    ids=["missing", "blank", "too-long"],
)
def test_create_requires_bounded_idempotency_key_after_authorization(
    idempotency_key: str | None,
    status_code: int,
) -> None:
    creator = Creator()
    headers = {"Authorization": "Bearer valid-token"}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    with client(Directory(), creator) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns",
            headers=headers,
            json=payload(),
        )

    assert response.status_code == status_code
    assert creator.calls == []


def test_create_rejects_duplicate_idempotency_headers_before_persistence() -> None:
    creator = Creator()
    with client(Directory(), creator) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns",
            headers=[
                ("Authorization", "Bearer valid-token"),
                ("Idempotency-Key", "campaign-create-a"),
                ("Idempotency-Key", "campaign-create-b"),
            ],
            json=payload(),
        )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert response.json()["detail"] == "Exactly one Idempotency-Key header is required"
    assert creator.calls == []


@pytest.mark.parametrize(
    ("failure", "code", "detail"),
    [
        (
            CampaignCreateIdempotencyConflict("private prior digest"),
            "IDEMPOTENCY_CONFLICT",
            "Idempotency key conflicts with a previous request",
        ),
        (
            CampaignCreateConflict("private tenant slug state"),
            "RESOURCE_CONFLICT",
            "Campaign slug is already reserved",
        ),
    ],
)
def test_create_distinguishes_idempotency_and_resource_conflicts(
    failure: Exception,
    code: str,
    detail: str,
) -> None:
    with client(Directory(), Creator(failure=failure)) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns",
            headers={
                "Authorization": "Bearer valid-token",
                "Idempotency-Key": "campaign-create-conflict",
            },
            json=payload(),
        )

    assert response.status_code == 409
    assert response.json()["code"] == code
    assert response.json()["detail"] == detail
    assert "private" not in response.text


def test_create_sanitizes_unavailable_boundary() -> None:
    with client(
        Directory(),
        Creator(failure=CampaignCreateUnavailable("private database detail")),
    ) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns",
            headers={
                "Authorization": "Bearer valid-token",
                "Idempotency-Key": "campaign-create-unavailable",
            },
            json=payload(),
        )

    assert response.status_code == 503
    assert response.json()["code"] == "AUTHORIZATION_UNAVAILABLE"
    assert "private" not in response.text


@pytest.mark.parametrize(
    "creator",
    [
        Creator(tenant_id=FOREIGN_TENANT_ID),
        Creator(overrides={"slug": "different-slug"}),
        Creator(overrides={"name": "Different name"}),
        Creator(overrides={"jurisdiction": "Different jurisdiction"}),
        Creator(overrides={"stage": "DIFFERENT"}),
        Creator(overrides={"status": "ACTIVE"}),
        Creator(overrides={"version": 2}),
    ],
    ids=[
        "foreign-tenant",
        "different-slug",
        "different-name",
        "different-jurisdiction",
        "different-stage",
        "active-status",
        "wrong-version",
    ],
)
def test_create_rejects_adapter_contract_drift(creator: Creator) -> None:
    with client(Directory(), creator) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns",
            headers={
                "Authorization": "Bearer valid-token",
                "Idempotency-Key": "campaign-create-scope-leak",
            },
            json=payload(),
        )

    assert response.status_code == 503
    assert response.json()["code"] == "AUTHORIZATION_UNAVAILABLE"
    assert len(creator.calls) == 1


@pytest.mark.parametrize(
    "extra",
    [
        {"status": "ACTIVE"},
        {"version": 99},
        {"campaign_id": str(CAMPAIGN_ID)},
    ],
    ids=["caller-status", "caller-version", "caller-id"],
)
def test_create_rejects_server_owned_fields(extra: dict[str, object]) -> None:
    creator = Creator()
    body: dict[str, object] = {**payload()}
    body.update(extra)
    with client(Directory(), creator) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns",
            headers={
                "Authorization": "Bearer valid-token",
                "Idempotency-Key": "campaign-create-server-owned",
            },
            json=body,
        )

    assert response.status_code == 422
    assert creator.calls == []


def test_openapi_exposes_typed_create_response_headers_and_bearer_security() -> None:
    with client(Directory(), Creator()) as api:
        document = api.get("/api/v1/openapi.json").json()

    path = "/api/v1/tenants/{tenant_id}/campaigns"
    operation = document["paths"][path]["post"]
    assert operation["security"] == [{"OIDC bearer token": []}]
    assert operation["responses"]["201"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/CampaignCreateEvidence"
    }
    assert set(operation["responses"]["201"]["headers"]) == {"Location", "ETag"}
    idempotency_parameter = next(
        parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "header" and parameter["name"] == "Idempotency-Key"
    )
    assert idempotency_parameter["required"] is True
    assert "Required stable key" in idempotency_parameter["description"]
    assert "does not approve strategy, spending, publication" in operation["description"]


def test_create_app_without_persistence_creator_fails_closed() -> None:
    with TestClient(
        create_app(
            settings(),
            token_verifier=Verifier(),
            membership_directory=Directory(),
        )
    ) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns",
            headers={
                "Authorization": "Bearer valid-token",
                "Idempotency-Key": "campaign-create-no-persistence",
            },
            json=payload(),
        )

    assert response.status_code == 503
    assert response.json()["code"] == "AUTHORIZATION_UNAVAILABLE"
    assert response.json()["detail"] == "Campaign creation is temporarily unavailable"
