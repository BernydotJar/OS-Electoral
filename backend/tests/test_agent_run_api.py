from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from campaignos.agents import (
    AgentClaim,
    AgentRecommendation,
    AgentRunCreateEvidence,
    AgentRunProjection,
    AgentRunReadEvidence,
)
from campaignos.agents.service import (
    AgentRunIdempotencyConflict,
    AgentRunNotFound,
    AgentRunStrategyConflict,
    AgentRunUnavailable,
)
from campaignos.api.app import create_app
from campaignos.api.routes.agent_runs import (
    CREATE_AGENT_RUN_PURPOSE,
    READ_AGENT_RUN_PURPOSE,
)
from campaignos.config import Environment, Settings
from campaignos.identity.authorization import (
    EffectiveMembership,
    EffectivePermissionGrant,
    TenantAuthorizationContext,
)
from campaignos.identity.models import AuthenticatedPrincipal

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("12121212-1212-4212-8212-121212121212")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
FOREIGN_CAMPAIGN_ID = UUID("23232323-2323-4232-8232-232323232323")
PRINCIPAL_ID = UUID("33333333-3333-4333-8333-333333333333")
MEMBERSHIP_ID = UUID("44444444-4444-4444-8444-444444444444")
GRANT_ID = UUID("55555555-5555-4555-8555-555555555555")
RUN_ID = UUID("66666666-6666-4666-8666-666666666666")
STRATEGY_ID = UUID("77777777-7777-4777-8777-777777777777")
EVIDENCE_ID = UUID("88888888-8888-4888-8888-888888888888")
OPTION_ID = UUID("99999999-9999-4999-8999-999999999999")
AUDIT_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
OUTBOX_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
NOW = datetime(2026, 7, 21, 23, 45, tzinfo=UTC)


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105 - synthetic fixture.
        return AuthenticatedPrincipal(
            subject="agent-operator",
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
        purpose: str = CREATE_AGENT_RUN_PURPOSE,
        resource_type: str = "agent_run",
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
                    approval_receipt_id="approval-agent-run",
                ),
            )
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=NOW,
            memberships=(
                EffectiveMembership(
                    membership_id=MEMBERSHIP_ID,
                    campaign_id=CAMPAIGN_ID,
                    roles=("operator",),
                    grants=grants,
                ),
            ),
        )


def projection() -> AgentRunProjection:
    recommendation = AgentRecommendation(
        summary="Internal comparison based on accepted evidence.",
        claims=(
            AgentClaim(
                statement="The options rely on accepted evidence.",
                classification="SUPPORTED",
                evidence_refs=(EVIDENCE_ID,),
            ),
        ),
        option_refs=(OPTION_ID,),
        risks=("Human review remains required.",),
        uncertainties=("No outcome is guaranteed.",),
    )
    return AgentRunProjection(
        id=RUN_ID,
        tenant_id=TENANT_ID,
        campaign_id=CAMPAIGN_ID,
        strategy_workspace_id=STRATEGY_ID,
        strategy_workspace_version=3,
        purpose="OPTION_COMPARISON",
        instruction_digest="a" * 64,
        policy_id="campaignos.agent.internal-recommendation",
        policy_version="1.0",
        prompt_template_id="agent.option-comparison",
        prompt_template_version="1.0",
        output_schema_version="1.0",
        prompt_digest="b" * 64,
        provider="fixture-provider",
        model="fixture-model",
        status="COMPLETED",
        recommendation=recommendation,
        evidence_refs=(EVIDENCE_ID,),
        option_refs=(OPTION_ID,),
        prompt_tokens=100,
        output_tokens=120,
        latency_ms=50,
        cost_micros=25,
        created_at=NOW,
    )


class Service:
    def __init__(self, failure: Exception | None = None) -> None:
        self.failure = failure
        self.create_calls: list[dict[str, Any]] = []
        self.get_calls: list[dict[str, Any]] = []
        self.create_evidence = AgentRunCreateEvidence(
            run=projection(),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )
        self.read_evidence = AgentRunReadEvidence(run=projection(), audit_event_id=AUDIT_ID)

    def create(self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any) -> AgentRunCreateEvidence:
        self.create_calls.append({"tenant_id": tenant_id, "campaign_id": campaign_id, **kwargs})
        if self.failure is not None:
            raise self.failure
        return self.create_evidence

    def get(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        run_id: UUID,
        **kwargs: Any,
    ) -> AgentRunReadEvidence:
        self.get_calls.append(
            {"tenant_id": tenant_id, "campaign_id": campaign_id, "run_id": run_id, **kwargs}
        )
        if self.failure is not None:
            raise self.failure
        return self.read_evidence


def settings() -> Settings:
    return Settings(environment=Environment.TEST, expose_api_docs=True)


def client(service: Service, directory: Directory) -> TestClient:
    return TestClient(
        create_app(
            settings(),
            token_verifier=Verifier(),
            database=Database(),
            membership_directory=directory,
            agent_run_service=service,
        )
    )


def payload() -> dict[str, object]:
    return {
        "strategy_workspace_version": 3,
        "purpose": "OPTION_COMPARISON",
        "instruction": "Compare documented options for internal human review.",
        "output_token_limit": 400,
        "timeout_ms": 1000,
        "cost_ceiling_micros": 100,
    }


def headers(*, key: str | None = "agent-run-key") -> dict[str, str]:
    values = {"Authorization": "Bearer valid-token"}
    if key is not None:
        values["Idempotency-Key"] = key
    return values


def test_create_requires_exact_grant_before_idempotency() -> None:
    service = Service()
    with client(service, Directory(include_grant=False)) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/agent-runs",
            json=payload(),
            headers=headers(key=None),
        )
    assert response.status_code == 403
    assert service.create_calls == []


@pytest.mark.parametrize(
    "directory",
    [
        Directory(action="read"),
        Directory(purpose="Different purpose"),
        Directory(resource_type="strategy_workspace"),
        Directory(resource_id=str(FOREIGN_CAMPAIGN_ID)),
        Directory(workspace_id=UUID(int=9)),
    ],
)
def test_create_rejects_near_miss_grants(directory: Directory) -> None:
    service = Service()
    with client(service, directory) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/agent-runs",
            json=payload(),
            headers=headers(),
        )
    assert response.status_code == 403
    assert service.create_calls == []


def test_create_returns_internal_evidence_and_location() -> None:
    service = Service()
    with client(service, Directory()) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/agent-runs",
            json=payload(),
            headers=headers(),
        )
    assert response.status_code == 201
    assert response.headers["location"].endswith(f"/agent-runs/{RUN_ID}")
    body = response.json()
    assert body["run"]["status"] == "COMPLETED"
    assert body["run"]["human_disposition"] == "PENDING"
    assert body["run"]["authority_effect"] == "NONE"
    assert body["run"]["external_effects"] == "NONE"
    call = service.create_calls[0]
    assert call["idempotency_key"] == "agent-run-key"
    assert call["authorization_grant_id"] == GRANT_ID
    assert call["authorization_purpose"] == CREATE_AGENT_RUN_PURPOSE


@pytest.mark.parametrize(
    ("key", "expected"),
    [(None, 428), ("   ", 428), ("x" * 256, 400)],
)
def test_create_validates_idempotency_after_authorization(key: str | None, expected: int) -> None:
    service = Service()
    with client(service, Directory()) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/agent-runs",
            json=payload(),
            headers=headers(key=key),
        )
    assert response.status_code == expected
    assert service.create_calls == []


def test_create_rejects_duplicate_idempotency_headers() -> None:
    service = Service()
    with client(service, Directory()) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/agent-runs",
            json=payload(),
            headers=[
                ("Authorization", "Bearer valid-token"),
                ("Idempotency-Key", "one"),
                ("Idempotency-Key", "two"),
            ],
        )
    assert response.status_code == 428
    assert service.create_calls == []


@pytest.mark.parametrize(
    ("failure", "status_code", "code"),
    [
        (AgentRunIdempotencyConflict("internal-idempotency-detail"), 409, "IDEMPOTENCY_CONFLICT"),
        (AgentRunStrategyConflict("internal-strategy-detail"), 409, "AGENT_STRATEGY_CONFLICT"),
        (AgentRunNotFound("internal-missing-detail"), 404, "RESOURCE_NOT_FOUND"),
        (AgentRunUnavailable("internal-down-detail"), 503, "AUTHORIZATION_UNAVAILABLE"),
    ],
)
def test_create_maps_domain_errors(failure: Exception, status_code: int, code: str) -> None:
    service = Service(failure)
    with client(service, Directory()) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/agent-runs",
            json=payload(),
            headers=headers(),
        )
    assert response.status_code == status_code
    assert response.json()["code"] == code
    assert str(failure) not in response.text


def test_create_rejects_adapter_scope_or_authority_drift() -> None:
    service = Service()
    service.create_evidence = service.create_evidence.model_copy(
        update={"run": projection().model_copy(update={"tenant_id": OTHER_TENANT_ID})}
    )
    with client(service, Directory()) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/agent-runs",
            json=payload(),
            headers=headers(),
        )
    assert response.status_code == 503

    service = Service()
    service.create_evidence = service.create_evidence.model_copy(
        update={"run": projection().model_copy(update={"external_effects": "NETWORK"})}
    )
    with client(service, Directory()) as api:
        response = api.post(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/agent-runs",
            json=payload(),
            headers=headers(),
        )
    assert response.status_code == 503


def test_read_requires_exact_read_grant_and_returns_evidence() -> None:
    service = Service()
    directory = Directory(action="read", purpose=READ_AGENT_RUN_PURPOSE)
    with client(service, directory) as api:
        response = api.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/agent-runs/{RUN_ID}",
            headers={"Authorization": "Bearer valid-token"},
        )
    assert response.status_code == 200
    assert response.json()["run"]["id"] == str(RUN_ID)
    call = service.get_calls[0]
    assert call["run_id"] == RUN_ID
    assert call["authorization_purpose"] == READ_AGENT_RUN_PURPOSE


def test_read_rejects_wrong_grant_before_service() -> None:
    service = Service()
    with client(service, Directory(action="create")) as api:
        response = api.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/agent-runs/{RUN_ID}",
            headers={"Authorization": "Bearer valid-token"},
        )
    assert response.status_code == 403
    assert service.get_calls == []


def test_openapi_documents_governed_no_effect_boundary() -> None:
    service = Service()
    with client(service, Directory()) as api:
        document = api.get("/api/v1/openapi.json").json()
    path = document["paths"]["/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/agent-runs"]
    operation = path["post"]
    assert operation["responses"]["201"]
    assert operation["requestBody"]["required"] is True
    description = operation["description"].lower()
    assert "tools" in description
    assert "publication" in description
    assert "targeting" in description
    assert "contact" in description
    assert "spending" in description
    assert "mobilization" in description
