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
from campaignos.strategy import (
    StrategyDecision,
    StrategyDecisionEvidence,
    StrategyDecisionRequest,
    StrategyWorkspaceAssessmentInput,
    StrategyWorkspaceCreateEvidence,
    StrategyWorkspaceProjection,
    StrategyWorkspaceReadEvidence,
    StrategyWorkspaceUpdate,
    StrategyWorkspaceUpdateEvidence,
    assess_strategy_workspace,
)
from campaignos.strategy.service import (
    StrategyWorkspaceEvidenceConflict,
    StrategyWorkspaceVersionConflict,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("12121212-1212-4212-8212-121212121212")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
FOREIGN_CAMPAIGN_ID = UUID("23232323-2323-4232-8232-232323232323")
PRINCIPAL_ID = UUID("33333333-3333-4333-8333-333333333333")
MEMBERSHIP_ID = UUID("44444444-4444-4444-8444-444444444444")
GRANT_ID = UUID("55555555-5555-4555-8555-555555555555")
WORKSPACE_ID = UUID("66666666-6666-4666-8666-666666666666")
ROLE_ID = UUID("77777777-7777-4777-8777-777777777777")
OPTION_ID = UUID("88888888-8888-4888-8888-888888888888")
DECISION_ID = UUID("99999999-9999-4999-8999-999999999999")
AUDIT_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
OUTBOX_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
NOW = datetime(2026, 7, 21, 12, tzinfo=UTC)

CREATE_PURPOSE = "Create campaign strategy workspace"
READ_PURPOSE = "Review campaign strategy workspace"
UPDATE_PURPOSE = "Maintain campaign strategy workspace"
DECIDE_PURPOSE = "Approve internal campaign strategy option"


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105 - synthetic test token.
        return AuthenticatedPrincipal(
            subject="strategy-operator",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            authenticated_at=NOW,
        )

    def readiness(self) -> tuple[bool, str]:
        return (True, "ready")


class Database:
    def readiness(self) -> tuple[bool, str]:
        return (True, "ready")

    def dispose(self) -> None:
        return None


class Directory:
    def __init__(
        self,
        *,
        include_grant: bool = True,
        action: str = "create",
        purpose: str = CREATE_PURPOSE,
        resource_type: str = "strategy_workspace",
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
                    approval_receipt_id="approval-strategy-workspace",
                ),
            )
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=NOW,
            memberships=(
                EffectiveMembership(
                    membership_id=MEMBERSHIP_ID,
                    campaign_id=self.campaign_id,
                    roles=("director_label_only",),
                    grants=grants,
                ),
            ),
        )


def projection(*, version: int = 1) -> StrategyWorkspaceProjection:
    return assess_strategy_workspace(
        StrategyWorkspaceAssessmentInput(
            id=WORKSPACE_ID,
            tenant_id=TENANT_ID,
            campaign_id=CAMPAIGN_ID,
            campaign_version=5,
            campaign_status="ACTIVE",
            campaign_name="Campaign",
            candidate_workspace_version=2,
            team_workspace_version=3,
            known_role_ids=(ROLE_ID,),
            title="Evidence-first strategy room",
            version=version,
            created_at=NOW,
            updated_at=NOW,
        )
    )


def decided_projection(version: int) -> tuple[StrategyWorkspaceProjection, StrategyDecision]:
    decision = StrategyDecision(
        id=DECISION_ID,
        workspace_version=version,
        selected_option_id=OPTION_ID,
        reason="Authorized human decision after evidence review.",
        human_role_id=ROLE_ID,
        approval_receipt_id="approval-strategy-decision",
        decided_at=NOW,
    )
    workspace = projection(version=version).model_copy(
        update={
            "decision": decision,
            "status": "DECIDED_INTERNAL",
            "next_action": "REVALIDATE_DECISION",
            "human_decision_required": False,
        }
    )
    return workspace, decision


class Service:
    def __init__(self, *, failure: Exception | None = None, drift: bool = False) -> None:
        self.failure = failure
        self.drift = drift
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _check(self) -> None:
        if self.failure is not None:
            raise self.failure

    def create(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> StrategyWorkspaceCreateEvidence:
        del tenant_id, campaign_id
        self.calls.append(("create", kwargs))
        self._check()
        workspace = projection()
        if self.drift:
            workspace = workspace.model_copy(update={"tenant_id": OTHER_TENANT_ID})
        return StrategyWorkspaceCreateEvidence(
            workspace=workspace,
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )

    def get(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> StrategyWorkspaceReadEvidence:
        del tenant_id, campaign_id
        self.calls.append(("get", kwargs))
        self._check()
        workspace = projection()
        if self.drift:
            workspace = workspace.model_copy(update={"campaign_id": FOREIGN_CAMPAIGN_ID})
        return StrategyWorkspaceReadEvidence(workspace=workspace, audit_event_id=AUDIT_ID)

    def update(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> StrategyWorkspaceUpdateEvidence:
        del tenant_id, campaign_id
        self.calls.append(("update", kwargs))
        self._check()
        return StrategyWorkspaceUpdateEvidence(
            workspace=projection(version=int(kwargs["expected_version"]) + 1),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )

    def decide(self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any) -> StrategyDecisionEvidence:
        del tenant_id, campaign_id
        self.calls.append(("decide", kwargs))
        self._check()
        workspace, decision = decided_projection(int(kwargs["expected_version"]))
        return StrategyDecisionEvidence(
            workspace=workspace,
            decision=decision,
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )


def client(directory: Directory, service: Service) -> TestClient:
    settings = Settings(environment=Environment.TEST, expose_api_docs=True)
    return TestClient(
        create_app(
            settings,
            token_verifier=Verifier(),
            database=Database(),
            membership_directory=directory,
            strategy_workspace_service=service,
        )
    )


def headers(*, key: str | None = None, version: str | None = None) -> dict[str, str]:
    result = {
        "Authorization": "Bearer valid-token",
        "X-Correlation-ID": "strategy-api",
    }
    if key is not None:
        result["Idempotency-Key"] = key
    if version is not None:
        result["If-Match"] = version
    return result


def path(suffix: str = "") -> str:
    return f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/strategy-workspace{suffix}"


def test_create_authorizes_before_idempotency() -> None:
    service = Service()
    with client(Directory(action="read", purpose=READ_PURPOSE), service) as api:
        response = api.post(path(), json={"title": "Strategy"}, headers=headers())
    assert response.status_code == 403
    assert service.calls == []


@pytest.mark.parametrize(
    "directory",
    [
        Directory(action="create", purpose="Wrong purpose"),
        Directory(action="create", resource_type="campaign"),
        Directory(action="create", resource_id=str(FOREIGN_CAMPAIGN_ID)),
        Directory(action="create", campaign_id=FOREIGN_CAMPAIGN_ID),
        Directory(action="create", workspace_id=WORKSPACE_ID),
        Directory(include_grant=False),
    ],
)
def test_create_rejects_non_exact_authority(directory: Directory) -> None:
    service = Service()
    with client(directory, service) as api:
        response = api.post(
            path(),
            json={"title": "Strategy"},
            headers=headers(key="create-strategy"),
        )
    assert response.status_code == 403
    assert service.calls == []


def test_create_requires_key_and_returns_location_etag() -> None:
    service = Service()
    with client(Directory(), service) as api:
        missing = api.post(path(), json={"title": "Strategy"}, headers=headers())
        created = api.post(
            path(),
            json={"title": "Strategy"},
            headers=headers(key="create-strategy"),
        )
    assert missing.status_code == 428
    assert created.status_code == 201
    assert created.headers["location"] == path()
    assert created.headers["etag"] == '"1"'
    operation, kwargs = service.calls[0]
    assert operation == "create"
    assert kwargs["authorization_purpose"] == CREATE_PURPOSE
    assert kwargs["idempotency_key"] == "create-strategy"


def test_read_requires_exact_grant_and_returns_etag() -> None:
    service = Service()
    with client(Directory(action="read", purpose=READ_PURPOSE), service) as api:
        response = api.get(path(), headers=headers())
    assert response.status_code == 200
    assert response.headers["etag"] == '"1"'
    assert service.calls[0][0] == "get"
    assert service.calls[0][1]["authorization_purpose"] == READ_PURPOSE


def test_update_authorizes_before_if_match_and_binds_version() -> None:
    denied = Service()
    with client(Directory(action="read", purpose=READ_PURPOSE), denied) as api:
        response = api.patch(path(), json={"title": "Updated"}, headers=headers())
    assert response.status_code == 403
    assert denied.calls == []

    service = Service()
    directory = Directory(action="update", purpose=UPDATE_PURPOSE)
    with client(directory, service) as api:
        missing = api.patch(
            path(),
            json={"title": "Updated"},
            headers=headers(key="update-strategy"),
        )
        updated = api.patch(
            path(),
            json={"title": "Updated"},
            headers=headers(key="update-strategy", version='"1"'),
        )
    assert missing.status_code == 428
    assert updated.status_code == 200
    assert updated.headers["etag"] == '"2"'
    _, kwargs = service.calls[0]
    assert kwargs["expected_version"] == 1
    assert kwargs["changes"] == StrategyWorkspaceUpdate(title="Updated")


def test_decision_requires_exact_human_grant_and_version() -> None:
    service = Service()
    payload = {
        "selected_option_id": str(OPTION_ID),
        "reason": "Authorized human decision after evidence review.",
        "human_role_id": str(ROLE_ID),
    }
    directory = Directory(action="approve", purpose=DECIDE_PURPOSE)
    with client(directory, service) as api:
        response = api.post(
            path("/decision"),
            json=payload,
            headers=headers(key="decide-strategy", version='"2"'),
        )
    assert response.status_code == 200
    assert response.headers["etag"] == '"2"'
    body = response.json()
    assert body["workspace"]["status"] == "DECIDED_INTERNAL"
    assert body["workspace"]["authority_effect"] == "NONE"
    assert body["workspace"]["external_effects"] == "NONE"
    operation, kwargs = service.calls[0]
    assert operation == "decide"
    assert kwargs["expected_version"] == 2
    assert kwargs["authorization_purpose"] == DECIDE_PURPOSE
    assert kwargs["request"] == StrategyDecisionRequest.model_validate(payload)


def test_decision_denial_precedes_preconditions_and_service() -> None:
    service = Service()
    directory = Directory(action="approve", purpose="Wrong purpose")
    payload = {
        "selected_option_id": str(OPTION_ID),
        "reason": "Authorized human decision after evidence review.",
        "human_role_id": str(ROLE_ID),
    }
    with client(directory, service) as api:
        response = api.post(path("/decision"), json=payload, headers=headers())
    assert response.status_code == 403
    assert service.calls == []


def test_errors_are_sanitized_and_scope_drift_fails_closed() -> None:
    directory = Directory(action="update", purpose=UPDATE_PURPOSE)
    failure = Service(failure=StrategyWorkspaceVersionConflict("private detail"))
    with client(directory, failure) as api:
        stale = api.patch(
            path(),
            json={"title": "Updated"},
            headers=headers(key="stale", version='"1"'),
        )
    assert stale.status_code == 412
    assert "private detail" not in stale.text

    conflict_service = Service(failure=StrategyWorkspaceEvidenceConflict("private evidence"))
    with client(directory, conflict_service) as api:
        conflict = api.patch(
            path(),
            json={"title": "Updated"},
            headers=headers(key="conflict", version='"1"'),
        )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "STRATEGY_EVIDENCE_CONFLICT"
    assert "private evidence" not in conflict.text

    with client(Directory(action="read", purpose=READ_PURPOSE), Service(drift=True)) as api:
        drift = api.get(path(), headers=headers())
    assert drift.status_code == 503


def test_openapi_declares_security_preconditions_and_internal_boundary() -> None:
    with client(Directory(), Service()) as api:
        schema = api.get("/api/v1/openapi.json").json()
    workspace = schema["paths"][
        "/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace"
    ]
    decision = schema["paths"][
        "/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace/decision"
    ]["post"]
    operations = (workspace["post"], workspace["get"], workspace["patch"], decision)
    assert all(item["security"] == [{"OIDC bearer token": []}] for item in operations)
    post_headers = {item["name"] for item in workspace["post"]["parameters"]}
    patch_headers = {item["name"] for item in workspace["patch"]["parameters"]}
    decision_headers = {item["name"] for item in decision["parameters"]}
    assert "Idempotency-Key" in post_headers
    assert {"Idempotency-Key", "If-Match"} <= patch_headers
    assert {"Idempotency-Key", "If-Match"} <= decision_headers
    description = decision["description"].lower()
    assert "internal" in description
    assert "publication" in description
    assert "targeting" in description
