"""Versioned bounded workload catalog for C3-PERF-001."""

from __future__ import annotations

from campaignos.performance.contracts import (
    AuthorizationScope,
    RouteClass,
    ScenarioId,
    WorkloadCatalog,
    WorkloadScenario,
)

CATALOG_VERSION = "1.0"


def default_workload_catalog() -> WorkloadCatalog:
    scenarios = (
        WorkloadScenario(
            scenario_id=ScenarioId.AUTHENTICATED_READ,
            route_class=RouteClass.IDENTITY_READ,
            policy_class="read",
            request_count=24,
            concurrency=4,
            timeout_seconds=20,
            expected_status_codes=(200,),
            authorization_scope=AuthorizationScope.PREAUTH,
            latency_ceiling_ms=5_000,
        ),
        WorkloadScenario(
            scenario_id=ScenarioId.AUTHENTICATED_MUTATION,
            route_class=RouteClass.DRAFT_MUTATION,
            policy_class="mutation",
            request_count=12,
            concurrency=3,
            timeout_seconds=20,
            expected_status_codes=(201,),
            authorization_scope=AuthorizationScope.TENANT,
            latency_ceiling_ms=5_000,
        ),
        WorkloadScenario(
            scenario_id=ScenarioId.EXPENSIVE_READ,
            route_class=RouteClass.WORKSPACE_PROJECTION,
            policy_class="expensive_read",
            request_count=12,
            concurrency=3,
            timeout_seconds=20,
            expected_status_codes=(200,),
            authorization_scope=AuthorizationScope.TENANT,
            latency_ceiling_ms=5_000,
        ),
        WorkloadScenario(
            scenario_id=ScenarioId.IDENTITY_LIFECYCLE,
            route_class=RouteClass.IDENTITY_CONTROL,
            policy_class="identity_lifecycle",
            request_count=8,
            concurrency=2,
            timeout_seconds=20,
            expected_status_codes=(200,),
            authorization_scope=AuthorizationScope.TENANT,
            latency_ceiling_ms=5_000,
        ),
        WorkloadScenario(
            scenario_id=ScenarioId.GOVERNED_AGENT,
            route_class=RouteClass.GOVERNED_RECOMMENDATION,
            policy_class="governed_agent_execution",
            request_count=6,
            concurrency=2,
            timeout_seconds=20,
            expected_status_codes=(503,),
            authorization_scope=AuthorizationScope.TENANT,
            latency_ceiling_ms=5_000,
        ),
        WorkloadScenario(
            scenario_id=ScenarioId.MALFORMED_AUTHENTICATED,
            route_class=RouteClass.REQUEST_VALIDATION,
            policy_class="mutation",
            request_count=8,
            concurrency=2,
            timeout_seconds=20,
            expected_status_codes=(422,),
            authorization_scope=AuthorizationScope.PREAUTH,
            latency_ceiling_ms=5_000,
        ),
        WorkloadScenario(
            scenario_id=ScenarioId.BOLA_DENIED,
            route_class=RouteClass.AUTHORIZATION_DENIAL,
            policy_class="read",
            request_count=8,
            concurrency=2,
            timeout_seconds=20,
            expected_status_codes=(403,),
            authorization_scope=AuthorizationScope.CROSS_TENANT_DENIED,
            latency_ceiling_ms=5_000,
        ),
        WorkloadScenario(
            scenario_id=ScenarioId.RATE_LIMIT_CONTENTION,
            route_class=RouteClass.RATE_LIMIT_STORE,
            policy_class="mutation",
            request_count=20,
            concurrency=20,
            timeout_seconds=20,
            expected_status_codes=(200, 429),
            authorization_scope=AuthorizationScope.TENANT,
            latency_ceiling_ms=10_000,
            expected_allowed=5,
            expected_denied=15,
        ),
        WorkloadScenario(
            scenario_id=ScenarioId.DOMAIN_ROLLBACK_ACCOUNTING,
            route_class=RouteClass.DOMAIN_TRANSACTION,
            policy_class="read",
            request_count=3,
            concurrency=1,
            timeout_seconds=20,
            expected_status_codes=(200,),
            authorization_scope=AuthorizationScope.TENANT,
            latency_ceiling_ms=5_000,
        ),
        WorkloadScenario(
            scenario_id=ScenarioId.STORE_UNAVAILABLE,
            route_class=RouteClass.DEPENDENCY_FAILURE,
            policy_class="read",
            request_count=4,
            concurrency=2,
            timeout_seconds=20,
            expected_status_codes=(503,),
            authorization_scope=AuthorizationScope.PREAUTH,
            latency_ceiling_ms=5_000,
        ),
        WorkloadScenario(
            scenario_id=ScenarioId.CLEANUP,
            route_class=RouteClass.MAINTENANCE,
            policy_class="read",
            request_count=2,
            concurrency=1,
            timeout_seconds=20,
            expected_status_codes=(200,),
            authorization_scope=AuthorizationScope.OPERATIONAL,
            latency_ceiling_ms=5_000,
        ),
    )
    catalog = WorkloadCatalog(catalog_version=CATALOG_VERSION, scenarios=scenarios)
    assert_complete_catalog(catalog)
    return catalog


def assert_complete_catalog(catalog: WorkloadCatalog) -> None:
    observed = {scenario.scenario_id for scenario in catalog.scenarios}
    expected = set(ScenarioId)
    if observed != expected:
        missing = sorted(item.value for item in expected - observed)
        extra = sorted(item.value for item in observed - expected)
        raise ValueError(f"workload catalog coverage mismatch; missing={missing}; extra={extra}")
