from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import ValidationError

from campaignos.api.errors import install_exception_handlers
from campaignos.api.rate_limits import enforce_rate_limit, rate_limit_policy
from campaignos.config import Environment, Settings
from campaignos.identity.models import AuthenticatedPrincipal
from campaignos.observability import MetricsRegistry, configure_json_logger
from campaignos.security import (
    DisabledRateLimiter,
    RateLimitDecision,
    RateLimitPolicy,
    RateLimitPolicyCatalog,
    RateLimitPolicyClass,
    RateLimitStoreUnavailable,
    UnavailableRateLimiter,
    policy_catalog_from_settings,
    preauth_principal_id,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
PRINCIPAL_ID = UUID("22222222-2222-4222-8222-222222222222")


class FixedLimiter:
    def __init__(self, decision: RateLimitDecision) -> None:
        self.decision = decision
        self.calls: list[tuple[UUID, UUID, RateLimitPolicyClass]] = []

    def consume(
        self,
        tenant_id: UUID,
        principal_id: UUID,
        policy_class: RateLimitPolicyClass,
    ) -> RateLimitDecision:
        self.calls.append((tenant_id, principal_id, policy_class))
        return self.decision


def complete_catalog() -> RateLimitPolicyCatalog:
    return RateLimitPolicyCatalog(
        policies=tuple(
            RateLimitPolicy(
                policy_class=policy_class,
                version=1,
                request_limit=10,
                window_seconds=60,
            )
            for policy_class in RateLimitPolicyClass
        )
    )


def test_policy_catalog_is_complete_unique_and_server_owned() -> None:
    catalog = policy_catalog_from_settings(Settings())

    assert {policy.policy_class for policy in catalog.policies} == set(RateLimitPolicyClass)
    assert catalog.policy_for(RateLimitPolicyClass.GOVERNED_AGENT).request_limit == 10
    assert catalog.policy_for(RateLimitPolicyClass.IDENTITY_LIFECYCLE).window_seconds == 300

    with pytest.raises(ValidationError, match="cover every reviewed operation class"):
        RateLimitPolicyCatalog(policies=catalog.policies[:-1])
    with pytest.raises(ValidationError, match="must be unique"):
        RateLimitPolicyCatalog(policies=(*catalog.policies, catalog.policies[0]))


def test_disabled_limiter_is_explicit_and_unavailable_limiter_fails_closed() -> None:
    disabled = DisabledRateLimiter(complete_catalog())
    decision = disabled.consume(TENANT_ID, PRINCIPAL_ID, RateLimitPolicyClass.MUTATION)
    assert decision.allowed is True
    assert decision.retry_after_seconds == 0

    with pytest.raises(RateLimitStoreUnavailable):
        UnavailableRateLimiter().consume(TENANT_ID, PRINCIPAL_ID, RateLimitPolicyClass.READ)


def test_preauth_identity_is_stable_and_excludes_display_fields() -> None:
    original = AuthenticatedPrincipal(
        subject="subject-1",
        issuer="https://identity.example.test/",
        audience="campaignos",
        display_name="Original",
        email="original@example.test",
        email_verified=True,
        authenticated_at=datetime(2026, 7, 29, tzinfo=UTC),
    )
    changed_profile = original.model_copy(
        update={"display_name": "Changed", "email": "changed@example.test"}
    )
    other_subject = original.model_copy(update={"subject": "subject-2"})

    assert preauth_principal_id(original) == preauth_principal_id(changed_profile)
    assert preauth_principal_id(original) != preauth_principal_id(other_subject)
    assert "subject" not in str(preauth_principal_id(original))
    assert "example" not in str(preauth_principal_id(original))


def test_shared_environments_require_rate_limiting() -> None:
    shared = {
        "environment": Environment.STAGING,
        "expose_api_docs": False,
        "database_url": "postgresql+psycopg://campaignos:secret@postgres/campaignos",
        "oidc_issuer": "https://identity.example.test/",
        "oidc_audience": "campaignos",
        "oidc_jwks_url": "https://identity.example.test/.well-known/jwks.json",
        "metrics_bearer_token": "campaignos-metrics-test-token",
    }
    with pytest.raises(ValidationError, match="rate limiting is required"):
        Settings(**shared)

    configured = Settings(**shared, rate_limits_enabled=True)
    assert configured.rate_limits_enabled is True


def rate_limit_test_app(limiter: object, *, declared: bool = True) -> FastAPI:
    settings = Settings(environment=Environment.TEST)
    app = FastAPI()
    app.state.rate_limiter = limiter
    app.state.metrics = MetricsRegistry(started_at=1.0)
    app.state.logger = configure_json_logger(settings, "campaignos-rate-limit-test")
    install_exception_handlers(app)

    def endpoint(request: Request) -> dict[str, str]:
        enforce_rate_limit(
            request,
            tenant_id=TENANT_ID,
            principal_id=PRINCIPAL_ID,
            policy_class=RateLimitPolicyClass.READ,
        )
        return {"status": "allowed"}

    if declared:
        endpoint = rate_limit_policy(RateLimitPolicyClass.READ)(endpoint)
    app.get("/protected")(endpoint)
    return app


def test_denial_is_sanitized_rfc9457_with_retry_after() -> None:
    limiter = FixedLimiter(
        RateLimitDecision(
            allowed=False,
            policy_class=RateLimitPolicyClass.READ,
            retry_after_seconds=17,
            policy_version=1,
        )
    )
    with TestClient(rate_limit_test_app(limiter)) as client:
        response = client.get("/protected", headers={"X-Correlation-ID": "rate-limit-test"})

    assert response.status_code == 429
    assert response.headers["retry-after"] == "17"
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "RATE_LIMIT_EXCEEDED"
    serialized = response.text
    assert str(TENANT_ID) not in serialized
    assert str(PRINCIPAL_ID) not in serialized
    assert "request_count" not in serialized
    assert limiter.calls == [(TENANT_ID, PRINCIPAL_ID, RateLimitPolicyClass.READ)]


def test_store_failure_and_missing_metadata_fail_closed() -> None:
    with TestClient(rate_limit_test_app(UnavailableRateLimiter())) as client:
        unavailable = client.get("/protected")
    assert unavailable.status_code == 503
    assert unavailable.json()["code"] == "RATE_LIMIT_UNAVAILABLE"

    allowed = FixedLimiter(
        RateLimitDecision(
            allowed=True,
            policy_class=RateLimitPolicyClass.READ,
            retry_after_seconds=0,
            policy_version=1,
        )
    )
    with TestClient(rate_limit_test_app(allowed, declared=False)) as client:
        mismatched = client.get("/protected")
    assert mismatched.status_code == 503
    assert mismatched.json()["code"] == "RATE_LIMIT_UNAVAILABLE"
    assert allowed.calls == []


def test_rate_limit_metrics_are_low_cardinality() -> None:
    registry = MetricsRegistry(started_at=1.0)
    registry.rate_limit_decision(policy_class="read", outcome="allowed")
    registry.rate_limit_decision(policy_class="read", outcome="denied")
    payload = registry.render_prometheus(service="campaignos-api", version="test")

    assert 'policy_class="read",outcome="allowed"} 1' in payload
    assert 'policy_class="read",outcome="denied"} 1' in payload
    assert str(TENANT_ID) not in payload
    assert str(PRINCIPAL_ID) not in payload
    with pytest.raises(ValueError, match="bounded labels"):
        registry.rate_limit_decision(policy_class=str(TENANT_ID), outcome="allowed")
