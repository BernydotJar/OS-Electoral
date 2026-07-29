from __future__ import annotations

import inspect
from datetime import UTC, datetime
from types import ModuleType
from uuid import UUID

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.api.rate_limits import declared_rate_limit_policy
from campaignos.api.routes import (
    agent_runs,
    campaign_operations,
    campaigns,
    candidate_workspace,
    guided_intake,
    health,
    identity_lifecycle,
    me,
    strategy_workspace,
    team_workspace,
    tenant_me,
    workspaces,
)
from campaignos.config import Environment, Settings
from campaignos.identity.authorization import (
    EffectiveMembership,
    EffectivePermissionGrant,
    TenantAuthorizationContext,
)
from campaignos.identity.models import AuthenticatedPrincipal
from campaignos.security import (
    RateLimitDecision,
    RateLimitPolicyClass,
)
from campaignos.security.rate_limits import PREAUTH_SCOPE_TENANT_ID

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
PRINCIPAL_ID = UUID("22222222-2222-4222-8222-222222222222")
MEMBERSHIP_ID = UUID("33333333-3333-4333-8333-333333333333")
CAMPAIGN_ID = UUID("44444444-4444-4444-8444-444444444444")
GRANT_ID = UUID("55555555-5555-4555-8555-555555555555")

PROTECTED_MODULES: tuple[ModuleType, ...] = (
    agent_runs,
    campaign_operations,
    campaigns,
    candidate_workspace,
    guided_intake,
    identity_lifecycle,
    me,
    strategy_workspace,
    team_workspace,
    tenant_me,
    workspaces,
)

EXPECTED_POLICIES: dict[tuple[str, str], RateLimitPolicyClass] = {
    ("GET", "/metrics"): RateLimitPolicyClass.EXPENSIVE_READ,
    ("GET", "/me"): RateLimitPolicyClass.READ,
    ("GET", "/tenants/{tenant_id}/me"): RateLimitPolicyClass.READ,
    ("POST", "/tenants/{tenant_id}/campaigns"): RateLimitPolicyClass.MUTATION,
    ("GET", "/tenants/{tenant_id}/campaigns"): RateLimitPolicyClass.READ,
    ("GET", "/tenants/{tenant_id}/campaigns/{campaign_id}"): RateLimitPolicyClass.READ,
    (
        "GET",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/readiness",
    ): RateLimitPolicyClass.EXPENSIVE_READ,
    ("PATCH", "/tenants/{tenant_id}/campaigns/{campaign_id}"): RateLimitPolicyClass.MUTATION,
    (
        "POST",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/workspaces",
    ): RateLimitPolicyClass.MUTATION,
    (
        "POST",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/guided-intake",
    ): RateLimitPolicyClass.MUTATION,
    (
        "GET",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/guided-intake",
    ): RateLimitPolicyClass.READ,
    (
        "PATCH",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/guided-intake",
    ): RateLimitPolicyClass.MUTATION,
    (
        "POST",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace",
    ): RateLimitPolicyClass.MUTATION,
    (
        "GET",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace",
    ): RateLimitPolicyClass.EXPENSIVE_READ,
    (
        "PATCH",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace",
    ): RateLimitPolicyClass.MUTATION,
    (
        "POST",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace/section-approvals",
    ): RateLimitPolicyClass.MUTATION,
    (
        "POST",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace",
    ): RateLimitPolicyClass.MUTATION,
    (
        "GET",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace",
    ): RateLimitPolicyClass.EXPENSIVE_READ,
    (
        "POST",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace/template-preview",
    ): RateLimitPolicyClass.EXPENSIVE_READ,
    (
        "POST",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace/template-apply",
    ): RateLimitPolicyClass.MUTATION,
    (
        "PATCH",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace",
    ): RateLimitPolicyClass.MUTATION,
    (
        "POST",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace",
    ): RateLimitPolicyClass.MUTATION,
    (
        "GET",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace",
    ): RateLimitPolicyClass.EXPENSIVE_READ,
    (
        "PATCH",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace",
    ): RateLimitPolicyClass.MUTATION,
    (
        "POST",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace/decision",
    ): RateLimitPolicyClass.MUTATION,
    (
        "POST",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap",
    ): RateLimitPolicyClass.MUTATION,
    (
        "GET",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap",
    ): RateLimitPolicyClass.EXPENSIVE_READ,
    (
        "PATCH",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap",
    ): RateLimitPolicyClass.MUTATION,
    (
        "GET",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap/war-room-snapshots/latest",
    ): RateLimitPolicyClass.EXPENSIVE_READ,
    (
        "POST",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap/war-room-snapshots",
    ): RateLimitPolicyClass.MUTATION,
    (
        "POST",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/agent-runs",
    ): RateLimitPolicyClass.GOVERNED_AGENT,
    (
        "GET",
        "/tenants/{tenant_id}/campaigns/{campaign_id}/agent-runs/{run_id}",
    ): RateLimitPolicyClass.GOVERNED_AGENT,
    ("POST", "/tenants/{tenant_id}/identity/invitations"): RateLimitPolicyClass.IDENTITY_LIFECYCLE,
    (
        "POST",
        "/tenants/{tenant_id}/identity/invitations/{invitation_id}/accept",
    ): RateLimitPolicyClass.IDENTITY_LIFECYCLE,
    (
        "POST",
        "/tenants/{tenant_id}/identity/invitations/{invitation_id}/revoke",
    ): RateLimitPolicyClass.IDENTITY_LIFECYCLE,
    (
        "POST",
        "/tenants/{tenant_id}/identity/sessions/current",
    ): RateLimitPolicyClass.IDENTITY_LIFECYCLE,
    (
        "POST",
        "/tenants/{tenant_id}/identity/sessions/{session_id}/revoke",
    ): RateLimitPolicyClass.IDENTITY_LIFECYCLE,
    (
        "POST",
        "/tenants/{tenant_id}/identity/memberships/{membership_id}/revoke",
    ): RateLimitPolicyClass.IDENTITY_LIFECYCLE,
    (
        "POST",
        "/tenants/{tenant_id}/identity/support-access",
    ): RateLimitPolicyClass.IDENTITY_LIFECYCLE,
    (
        "POST",
        "/tenants/{tenant_id}/identity/support-access/{support_request_id}/approve",
    ): RateLimitPolicyClass.IDENTITY_LIFECYCLE,
    (
        "POST",
        "/tenants/{tenant_id}/identity/support-access/{support_request_id}/revoke",
    ): RateLimitPolicyClass.IDENTITY_LIFECYCLE,
}


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105 - deterministic fixture.
        return AuthenticatedPrincipal(
            subject="rate-limit-user",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            authenticated_at=datetime(2026, 7, 29, tzinfo=UTC),
        )

    def readiness(self) -> tuple[bool, str]:
        return True, "ready"


class Directory:
    def __init__(self, *, authorized: bool) -> None:
        self.authorized = authorized

    def load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        *,
        evaluated_at: datetime | None = None,
    ) -> TenantAuthorizationContext:
        del principal, evaluated_at
        grants: tuple[EffectivePermissionGrant, ...] = ()
        if self.authorized:
            grants = (
                EffectivePermissionGrant(
                    grant_id=GRANT_ID,
                    campaign_id=CAMPAIGN_ID,
                    workspace_id=None,
                    action="read",
                    resource_type="campaign",
                    resource_id=str(CAMPAIGN_ID),
                    purpose="Operate assigned campaign",
                    approval_receipt_id="approval-rate-limit",
                ),
            )
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=datetime(2026, 7, 29, tzinfo=UTC),
            memberships=(
                EffectiveMembership(
                    membership_id=MEMBERSHIP_ID,
                    campaign_id=CAMPAIGN_ID,
                    roles=("operator",),
                    grants=grants,
                ),
            ),
        )


class DenyLimiter:
    def __init__(self) -> None:
        self.calls: list[tuple[UUID, UUID, RateLimitPolicyClass]] = []

    def consume(
        self,
        tenant_id: UUID,
        principal_id: UUID,
        policy_class: RateLimitPolicyClass,
    ) -> RateLimitDecision:
        self.calls.append((tenant_id, principal_id, policy_class))
        return RateLimitDecision(
            allowed=False,
            policy_class=policy_class,
            retry_after_seconds=23,
            policy_version=1,
        )


class DirectoryMustNotRun:
    def list_authorized(self, *args: object, **kwargs: object) -> object:
        raise AssertionError("domain read must not run after a denied budget")

    def get(self, *args: object, **kwargs: object) -> object:
        raise AssertionError("domain read must not run after a denied budget")


def test_every_protected_route_has_exact_policy_and_consumption() -> None:
    observed: dict[tuple[str, str], RateLimitPolicyClass] = {}
    for module in PROTECTED_MODULES:
        for route in module.router.routes:
            assert isinstance(route, APIRoute)
            assert route.methods is not None and len(route.methods) == 1
            method = next(iter(route.methods))
            declared = declared_rate_limit_policy(route.endpoint)
            assert declared is not None, f"missing policy: {method} {route.path}"
            source = inspect.getsource(route.endpoint)
            assert "enforce_rate_limit(" in source or "enforce_pre_auth_rate_limit(" in source
            observed[(method, route.path)] = declared

    health_routes = {
        route.path: route for route in health.router.routes if isinstance(route, APIRoute)
    }
    assert declared_rate_limit_policy(health_routes["/health"].endpoint) is None
    assert declared_rate_limit_policy(health_routes["/ready"].endpoint) is None
    metrics_route = health_routes["/metrics"]
    metrics_policy = declared_rate_limit_policy(metrics_route.endpoint)
    assert metrics_policy is RateLimitPolicyClass.EXPENSIVE_READ
    assert "enforce_rate_limit(" in inspect.getsource(metrics_route.endpoint)
    observed[("GET", "/metrics")] = metrics_policy

    assert observed == EXPECTED_POLICIES
    assert len(observed) == 41


def test_authorization_denial_does_not_consume_another_budget() -> None:
    limiter = DenyLimiter()
    settings = Settings(environment=Environment.TEST, expose_api_docs=True)
    with TestClient(
        create_app(
            settings,
            token_verifier=Verifier(),
            membership_directory=Directory(authorized=False),
            campaign_directory=DirectoryMustNotRun(),
            rate_limiter=limiter,
        )
    ) as client:
        response = client.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 403
    assert limiter.calls == []


def test_authorized_request_is_denied_before_domain_execution() -> None:
    limiter = DenyLimiter()
    settings = Settings(environment=Environment.TEST, expose_api_docs=True)
    with TestClient(
        create_app(
            settings,
            token_verifier=Verifier(),
            membership_directory=Directory(authorized=True),
            campaign_directory=DirectoryMustNotRun(),
            rate_limiter=limiter,
        )
    ) as client:
        response = client.get(
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 429
    assert response.headers["retry-after"] == "23"
    assert limiter.calls == [(TENANT_ID, PRINCIPAL_ID, RateLimitPolicyClass.READ)]


def test_me_uses_internal_preauthorization_scope() -> None:
    limiter = DenyLimiter()
    settings = Settings(environment=Environment.TEST, expose_api_docs=True)
    with TestClient(
        create_app(settings, token_verifier=Verifier(), rate_limiter=limiter)
    ) as client:
        response = client.get(
            "/api/v1/me",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 429
    assert len(limiter.calls) == 1
    tenant_id, principal_id, policy_class = limiter.calls[0]
    assert tenant_id == PREAUTH_SCOPE_TENANT_ID
    assert principal_id not in {TENANT_ID, PRINCIPAL_ID}
    assert policy_class is RateLimitPolicyClass.READ


def test_metrics_authentication_precedes_operational_budget() -> None:
    limiter = DenyLimiter()
    token = "campaignos-metrics-test-token"  # noqa: S105 - deterministic fixture.
    settings = Settings(
        environment=Environment.TEST,
        expose_api_docs=True,
        metrics_bearer_token=token,
    )
    with TestClient(create_app(settings, rate_limiter=limiter)) as client:
        missing = client.get("/api/v1/metrics")
        denied = client.get(
            "/api/v1/metrics",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert missing.status_code == 401
    assert limiter.calls == [
        (
            PREAUTH_SCOPE_TENANT_ID,
            UUID("00000000-0000-5000-8000-000000000002"),
            RateLimitPolicyClass.EXPENSIVE_READ,
        )
    ]
    assert denied.status_code == 429
    assert denied.headers["retry-after"] == "23"
