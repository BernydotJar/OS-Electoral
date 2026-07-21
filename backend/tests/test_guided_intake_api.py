from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.config import Environment, Settings
from campaignos.identity.authorization import (
    EffectiveMembership,
    EffectivePermissionGrant,
    TenantAuthorizationContext,
)
from campaignos.identity.models import AuthenticatedPrincipal
from campaignos.onboarding import (
    GuidedIntakeAssessmentInput,
    GuidedIntakeReadEvidence,
    GuidedIntakeStartEvidence,
    GuidedIntakeUpdate,
    GuidedIntakeUpdateEvidence,
    assess_guided_intake,
)
from campaignos.onboarding.service import (
    GuidedIntakeIdempotencyConflict,
    GuidedIntakeNotFound,
    GuidedIntakePrerequisiteConflict,
    GuidedIntakeUnavailable,
    GuidedIntakeVersionConflict,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
FOREIGN_CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
PRINCIPAL_ID = UUID("44444444-4444-4444-8444-444444444444")
MEMBERSHIP_ID = UUID("55555555-5555-4555-8555-555555555555")
GRANT_ID = UUID("66666666-6666-4666-8666-666666666666")
INTAKE_ID = UUID("77777777-7777-4777-8777-777777777777")
AUDIT_ID = UUID("88888888-8888-4888-8888-888888888888")
OUTBOX_ID = UUID("99999999-9999-4999-8999-999999999999")
START_PURPOSE = "Begin guided campaign intake"
READ_PURPOSE = "Review guided campaign intake"
UPDATE_PURPOSE = "Maintain guided campaign intake"


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105 - deterministic fixture.
        return AuthenticatedPrincipal(
            subject="guided-intake-operator",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            authenticated_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
        )

    def readiness(self) -> tuple[bool, str]:
        return True, "ready"


class Database:
    def readiness(self) -> tuple[bool, str]:
        return True, "ready"

    def dispose(self) -> None:
        return None


class Directory:
    def __init__(
        self,
        *,
        include_grant: bool = True,
        action: str = "create",
        purpose: str = START_PURPOSE,
        resource_type: str = "guided_intake",
        resource_id: str = str(CAMPAIGN_ID),
        campaign_id: UUID | None = CAMPAIGN_ID,
        workspace_id: UUID | None = None,
    ) -> None:
        self.include_grant = include_grant
        self.action = action
        self.purpose = purpose
        self.resource_type = resource_type
        self.resource_id = resource_id
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
        grants: tuple[EffectivePermissionGrant, ...] = ()
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
                    approval_receipt_id="approval-guided-intake",
                ),
            )
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
            memberships=(
                EffectiveMembership(
                    membership_id=MEMBERSHIP_ID,
                    campaign_id=self.campaign_id,
                    roles=("operator",),
                    grants=grants,
                ),
            ),
        )


def projection(*, version: int = 1, tenant_id: UUID = TENANT_ID, campaign_id: UUID = CAMPAIGN_ID):
    return assess_guided_intake(
        GuidedIntakeAssessmentInput(
            id=INTAKE_ID,
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            campaign_version=2,
            campaign_status="ACTIVE",
            campaign_name="Campaign",
            jurisdiction="Antigua Guatemala",
            stage="PRECAMPAIGN",
            active_workspace_count=1,
            office="Alcaldía Municipal" if version > 1 else None,
            candidate_project=None,
            current_team=None,
            current_assets=None,
            budget_status="NOT_ASSESSED",
            known_unknowns=None,
            evidence_requirements=None,
            version=version,
            created_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
            updated_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
        )
    )


class Service:
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
        self.calls: list[tuple[str, tuple[object, ...], dict[str, Any]]] = []

    def start(self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any) -> GuidedIntakeStartEvidence:
        self.calls.append(("start", (tenant_id, campaign_id), kwargs))
        if self.failure is not None:
            raise self.failure
        return GuidedIntakeStartEvidence(
            intake=projection(tenant_id=self.tenant_id, campaign_id=self.campaign_id),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
            created=True,
        )

    def get(self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any) -> GuidedIntakeReadEvidence:
        self.calls.append(("get", (tenant_id, campaign_id), kwargs))
        if self.failure is not None:
            raise self.failure
        return GuidedIntakeReadEvidence(
            intake=projection(tenant_id=self.tenant_id, campaign_id=self.campaign_id),
            audit_event_id=AUDIT_ID,
        )

    def update(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> GuidedIntakeUpdateEvidence:
        self.calls.append(("update", (tenant_id, campaign_id), kwargs))
        if self.failure is not None:
            raise self.failure
        return GuidedIntakeUpdateEvidence(
            intake=projection(
                version=int(kwargs["expected_version"]) + 1,
                tenant_id=self.tenant_id,
                campaign_id=self.campaign_id,
            ),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )


def settings() -> Settings:
    return Settings(environment=Environment.TEST, expose_api_docs=True)


def client(directory: Directory, service: Service) -> TestClient:
    return TestClient(
        create_app(
            settings(),
            token_verifier=Verifier(),
            database=Database(),
            membership_directory=directory,
            guided_intake_service=service,
        )
    )


def headers(*, idempotency_key: str | None = None, if_match: str | None = None) -> dict[str, str]:
    values = {"Authorization": "Bearer valid-token", "X-Correlation-ID": "guided-intake-api"}
    if idempotency_key is not None:
        values["Idempotency-Key"] = idempotency_key
    if if_match is not None:
        values["If-Match"] = if_match
    return values


def test_start_requires_exact_grant_and_forwards_authority() -> None:
    service = Service()
    with client(Directory(), service) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/guided-intake",
            headers=headers(idempotency_key="  guided-intake-start  "),
        )

    assert response.status_code == 201
    assert response.headers["location"].endswith(f"/campaigns/{CAMPAIGN_ID}/guided-intake")
    assert response.headers["etag"] == '"1"'
    assert response.json()["intake"]["id"] == str(INTAKE_ID)
    assert len(service.calls) == 1
    operation, scope, kwargs = service.calls[0]
    assert operation == "start"
    assert scope == (TENANT_ID, CAMPAIGN_ID)
    assert kwargs == {
        "principal_id": PRINCIPAL_ID,
        "authorization_grant_id": GRANT_ID,
        "approval_receipt_id": "approval-guided-intake",
        "authorization_purpose": START_PURPOSE,
        "correlation_id": "guided-intake-api",
        "idempotency_key": "guided-intake-start",
    }


@pytest.mark.parametrize(
    "directory",
    [
        Directory(include_grant=False),
        Directory(action="read"),
        Directory(purpose="Different purpose"),
        Directory(resource_type="campaign"),
        Directory(resource_id=str(FOREIGN_CAMPAIGN_ID)),
        Directory(campaign_id=FOREIGN_CAMPAIGN_ID),
        Directory(workspace_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")),
    ],
)
def test_start_denies_mismatched_grant_before_service(directory: Directory) -> None:
    service = Service()
    with client(directory, service) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/guided-intake",
            headers=headers(idempotency_key="guided-intake-denied"),
        )
    assert response.status_code == 403
    assert service.calls == []


def test_start_requires_exactly_one_bounded_idempotency_key() -> None:
    for request_headers, expected_status in (
        ([("Authorization", "Bearer valid-token")], 428),
        (
            [
                ("Authorization", "Bearer valid-token"),
                ("Idempotency-Key", "one"),
                ("Idempotency-Key", "two"),
            ],
            428,
        ),
        (
            [
                ("Authorization", "Bearer valid-token"),
                ("Idempotency-Key", "x" * 256),
            ],
            400,
        ),
    ):
        service = Service()
        with client(Directory(), service) as api:
            response = api.post(
                f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/guided-intake",
                headers=request_headers,
            )
        assert response.status_code == expected_status
        assert service.calls == []


@pytest.mark.parametrize(
    ("failure", "status_code", "code"),
    [
        (GuidedIntakeIdempotencyConflict("private"), 409, "IDEMPOTENCY_CONFLICT"),
        (GuidedIntakePrerequisiteConflict(("private",)), 409, "CAMPAIGN_NOT_READY"),
        (GuidedIntakeNotFound("private"), 404, "RESOURCE_NOT_FOUND"),
        (GuidedIntakeUnavailable("private"), 503, "AUTHORIZATION_UNAVAILABLE"),
    ],
)
def test_start_maps_failures_without_private_details(
    failure: Exception, status_code: int, code: str
) -> None:
    with client(Directory(), Service(failure=failure)) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/guided-intake",
            headers=headers(idempotency_key="guided-intake-failure"),
        )
    assert response.status_code == status_code
    assert response.json()["code"] == code
    assert "private" not in response.text


def test_read_requires_read_grant_and_returns_etag() -> None:
    service = Service()
    directory = Directory(action="read", purpose=READ_PURPOSE)
    with client(directory, service) as api:
        response = api.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/guided-intake",
            headers=headers(),
        )
    assert response.status_code == 200
    assert response.headers["etag"] == '"1"'
    assert service.calls[0][0] == "get"
    assert service.calls[0][2]["authorization_purpose"] == READ_PURPOSE


def test_update_requires_exact_grant_headers_and_forwards_normalized_patch() -> None:
    service = Service()
    directory = Directory(action="update", purpose=UPDATE_PURPOSE)
    with client(directory, service) as api:
        response = api.patch(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/guided-intake",
            headers=headers(idempotency_key="guided-intake-update", if_match='"1"'),
            json={"office": "  Alcaldía   Municipal  ", "current_assets": []},
        )
    assert response.status_code == 200
    assert response.headers["etag"] == '"2"'
    operation, _, kwargs = service.calls[0]
    assert operation == "update"
    assert kwargs["expected_version"] == 1
    assert kwargs["changes"] == GuidedIntakeUpdate(office="Alcaldía Municipal", current_assets=[])
    assert kwargs["idempotency_key"] == "guided-intake-update"


def test_update_denies_wrong_grant_before_preconditions_or_service() -> None:
    service = Service()
    with client(Directory(action="read", purpose=READ_PURPOSE), service) as api:
        response = api.patch(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/guided-intake",
            headers=headers(),
            json={"office": "Alcaldía"},
        )
    assert response.status_code == 403
    assert service.calls == []


@pytest.mark.parametrize(
    ("request_headers", "expected_status"),
    [
        ({"Idempotency-Key": "key"}, 428),
        ({"If-Match": '"1"'}, 428),
        ({"Idempotency-Key": "key", "If-Match": "invalid"}, 400),
    ],
)
def test_update_requires_version_and_idempotency_preconditions(
    request_headers: dict[str, str], expected_status: int
) -> None:
    service = Service()
    merged_headers = {"Authorization": "Bearer valid-token", **request_headers}
    with client(Directory(action="update", purpose=UPDATE_PURPOSE), service) as api:
        response = api.patch(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/guided-intake",
            headers=merged_headers,
            json={"office": "Alcaldía"},
        )
    assert response.status_code == expected_status
    assert service.calls == []


@pytest.mark.parametrize(
    ("failure", "status_code", "code"),
    [
        (GuidedIntakeVersionConflict("private"), 412, "VERSION_CONFLICT"),
        (GuidedIntakeIdempotencyConflict("private"), 409, "IDEMPOTENCY_CONFLICT"),
        (GuidedIntakeNotFound("private"), 404, "RESOURCE_NOT_FOUND"),
        (GuidedIntakeUnavailable("private"), 503, "AUTHORIZATION_UNAVAILABLE"),
    ],
)
def test_update_maps_failures_safely(failure: Exception, status_code: int, code: str) -> None:
    directory = Directory(action="update", purpose=UPDATE_PURPOSE)
    with client(directory, Service(failure=failure)) as api:
        response = api.patch(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/guided-intake",
            headers=headers(idempotency_key="key", if_match='"1"'),
            json={"office": "Alcaldía"},
        )
    assert response.status_code == status_code
    assert response.json()["code"] == code
    assert "private" not in response.text


@pytest.mark.parametrize("operation", ["start", "get", "update"])
def test_adapter_scope_drift_fails_closed(operation: str) -> None:
    service = Service(tenant_id=TENANT_ID, campaign_id=FOREIGN_CAMPAIGN_ID)
    if operation == "start":
        directory = Directory()
        method = "post"
        request_kwargs: dict[str, object] = {"headers": headers(idempotency_key="key")}
    elif operation == "get":
        directory = Directory(action="read", purpose=READ_PURPOSE)
        method = "get"
        request_kwargs = {"headers": headers()}
    else:
        directory = Directory(action="update", purpose=UPDATE_PURPOSE)
        method = "patch"
        request_kwargs = {
            "headers": headers(idempotency_key="key", if_match='"1"'),
            "json": {"office": "Alcaldía"},
        }
    with client(directory, service) as api:
        response = getattr(api, method)(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/guided-intake",
            **request_kwargs,
        )
    assert response.status_code == 503


def test_openapi_declares_security_and_precondition_headers() -> None:
    with client(Directory(), Service()) as api:
        schema = api.get("/api/v1/openapi.json").json()
    path = schema["paths"]["/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/guided-intake"]
    assert path["post"]["security"] == [{"OIDC bearer token": []}]
    assert path["get"]["security"] == [{"OIDC bearer token": []}]
    assert path["patch"]["security"] == [{"OIDC bearer token": []}]
    post_headers = {item["name"] for item in path["post"]["parameters"]}
    patch_headers = {item["name"] for item in path["patch"]["parameters"]}
    assert "Idempotency-Key" in post_headers
    assert {"Idempotency-Key", "If-Match"} <= patch_headers
