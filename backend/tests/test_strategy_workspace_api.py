from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
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
from campaignos.strategy import (
    StrategyWorkspaceAssessmentInput,
    StrategyWorkspaceCreateEvidence,
    StrategyWorkspaceReadEvidence,
    StrategyWorkspaceUpdate,
    StrategyWorkspaceUpdateEvidence,
    assess_strategy_workspace,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
FOREIGN_CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
PRINCIPAL_ID = UUID("44444444-4444-4444-8444-444444444444")
MEMBERSHIP_ID = UUID("55555555-5555-4555-8555-555555555555")
GRANT_ID = UUID("66666666-6666-4666-8666-666666666666")
TEAM_ID = UUID("77777777-7777-4777-8777-777777777777")
AUDIT_ID = UUID("88888888-8888-4888-8888-888888888888")
OUTBOX_ID = UUID("99999999-9999-4999-8999-999999999999")
CREATE_PURPOSE = "Create campaign strategy workspace"
READ_PURPOSE = "Review campaign strategy workspace"
UPDATE_PURPOSE = "Maintain campaign strategy workspace"
from datetime import date

from campaignos.strategy import (
    StrategyAssumption,
    StrategyEvidence,
    StrategyHypothesis,
    StrategyObjective,
    StrategyOption,
)


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"
        return AuthenticatedPrincipal(
            subject="team-operator",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            authenticated_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
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
            evaluated_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
            memberships=(
                EffectiveMembership(
                    membership_id=MEMBERSHIP_ID,
                    campaign_id=self.campaign_id,
                    roles=("director_label_only",),
                    grants=grants,
                ),
            ),
        )


def projection(*, version: int = 1, tenant_id: UUID = TENANT_ID, campaign_id: UUID = CAMPAIGN_ID):
    return assess_strategy_workspace(
        StrategyWorkspaceAssessmentInput(
            id=TEAM_ID,
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            campaign_version=4,
            campaign_status="ACTIVE",
            campaign_name="Campaign",
            organization_template="LEAN_CAMPAIGN",
            roles=None,
            work_items=None,
            training_requirements=None,
            access_recommendations=None,
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

    def create(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> StrategyWorkspaceCreateEvidence:
        self.calls.append(("create", (tenant_id, campaign_id), kwargs))
        if self.failure is not None:
            raise self.failure
        return StrategyWorkspaceCreateEvidence(
            workspace=projection(tenant_id=self.tenant_id, campaign_id=self.campaign_id),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )

    def get(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> StrategyWorkspaceReadEvidence:
        self.calls.append(("get", (tenant_id, campaign_id), kwargs))
        if self.failure is not None:
            raise self.failure
        return StrategyWorkspaceReadEvidence(
            workspace=projection(tenant_id=self.tenant_id, campaign_id=self.campaign_id),
            audit_event_id=AUDIT_ID,
        )

    def update(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> StrategyWorkspaceUpdateEvidence:
        self.calls.append(("update", (tenant_id, campaign_id), kwargs))
        if self.failure is not None:
            raise self.failure
        return StrategyWorkspaceUpdateEvidence(
            workspace=projection(
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
            strategy_workspace_service=service,
        )
    )


def headers(*, idempotency_key: str | None = None, if_match: str | None = None) -> dict[str, str]:
    values = {"Authorization": "Bearer valid-token", "X-Correlation-ID": "team-api"}
    if idempotency_key is not None:
        values["Idempotency-Key"] = idempotency_key
    if if_match is not None:
        values["If-Match"] = if_match
    return values


def path() -> str:
    return f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/strategy-workspace"


def _strategy_ready_update() -> StrategyWorkspaceUpdate:
    evidence_id = UUID("66666666-6666-4666-8666-666666666666")
    assumption_id = UUID("77777777-7777-4777-8777-777777777777")
    hypothesis_a = UUID("88888888-8888-4888-8888-888888888881")
    hypothesis_b = UUID("88888888-8888-4888-8888-888888888882")
    option_a = UUID("99999999-9999-4999-8999-999999999991")
    option_b = UUID("99999999-9999-4999-8999-999999999992")
    evidence = StrategyEvidence(
        id=evidence_id,
        classification="VERIFIED",
        statement="Public record confirms context.",
        source_reference="https://example.test/public-record",
        authority="Public authority",
        jurisdiction="Guatemala",
        status="ACCEPTED",
        collected_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
    )
    assumption = StrategyAssumption(
        id=assumption_id,
        statement="The team can sustain the operating cadence.",
        evidence_refs=(evidence_id,),
        invalidation_signals=("Capacity falls below threshold",),
    )
    return StrategyWorkspaceUpdate(
        evidence=(evidence,),
        assumptions=(assumption,),
        hypotheses=(
            StrategyHypothesis(
                id=hypothesis_a,
                title="Evidence consolidation",
                statement="Evidence consolidation improves internal decisions.",
                evidence_refs=(evidence_id,),
                assumption_refs=(assumption_id,),
                invalidation_signals=("Decision quality does not improve",),
                status="IN_REVIEW",
            ),
            StrategyHypothesis(
                id=hypothesis_b,
                title="Capacity sequencing",
                statement="Capacity sequencing reduces internal blockers.",
                evidence_refs=(evidence_id,),
                assumption_refs=(assumption_id,),
                invalidation_signals=("Blockers increase",),
                status="IN_REVIEW",
            ),
        ),
        options=(
            StrategyOption(
                id=option_a,
                title="Option A",
                summary="Consolidate evidence first.",
                hypothesis_refs=(hypothesis_a,),
                evidence_refs=(evidence_id,),
                benefits=("Preserves provenance",),
                risks=("Requires review time",),
                tradeoffs=("Delays downstream planning",),
            ),
            StrategyOption(
                id=option_b,
                title="Option B",
                summary="Sequence by capacity.",
                hypothesis_refs=(hypothesis_b,),
                evidence_refs=(evidence_id,),
                benefits=("Surfaces constraints",),
                risks=("May defer evidence",),
                tradeoffs=("Prioritizes capacity",),
            ),
        ),
        objectives=(
            StrategyObjective(
                id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
                outcome="Complete evidence review.",
                metric="Accepted evidence records",
                baseline="1",
                target="10",
                deadline=date(2026, 8, 15),
                owner_role_id=ROLE_ID,
                evidence_refs=(evidence_id,),
            ),
        ),
        contradictions=(),
        red_team_findings=(),
    )


def test_read_requires_read_grant_and_returns_etag() -> None:
    service = Service()
    with client(Directory(action="read", purpose=READ_PURPOSE), service) as api:
        response = api.get(path(), headers=headers())
    assert response.status_code == 200
    assert response.headers["etag"] == '"1"'
    assert service.calls[0][0] == "get"
    assert service.calls[0][2]["authorization_purpose"] == READ_PURPOSE


def test_openapi_declares_security_and_precondition_headers() -> None:
    with client(Directory(), Service()) as api:
        schema = api.get("/api/v1/openapi.json").json()
    operation = schema["paths"][
        "/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace"
    ]
    assert operation["post"]["security"] == [{"OIDC bearer token": []}]
    assert operation["get"]["security"] == [{"OIDC bearer token": []}]
    assert operation["patch"]["security"] == [{"OIDC bearer token": []}]
    post_headers = {item["name"] for item in operation["post"]["parameters"]}
    patch_headers = {item["name"] for item in operation["patch"]["parameters"]}
    assert "Idempotency-Key" in post_headers
    assert {"Idempotency-Key", "If-Match"} <= patch_headers
