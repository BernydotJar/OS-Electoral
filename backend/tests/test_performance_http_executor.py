from __future__ import annotations

from campaignos.performance import PoolSnapshot, ScenarioId, default_workload_catalog
from campaignos.performance import executor as executor_module
from campaignos.performance.executor import CampaignOSLoadExecutor


class FakePostgresRuntime:
    server_version = "18.3"

    def __init__(self, database_url: str, *, role_name: str | None = None) -> None:
        assert database_url.endswith("_test")
        del role_name
        self.closed = False

    def pool_snapshot(self) -> PoolSnapshot:
        return PoolSnapshot()

    def clear_buckets(self) -> int:
        return 0

    def insert_stale_buckets(self, count: int) -> None:
        del count

    def close(self) -> None:
        self.closed = True


def test_http_scenarios_use_real_fastapi_boundaries(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(executor_module, "_PostgresRuntime", FakePostgresRuntime)
    executor = CampaignOSLoadExecutor("postgresql+psycopg://local/performance_test")
    scenarios = {
        scenario.scenario_id: scenario for scenario in default_workload_catalog().scenarios
    }
    expected = {
        ScenarioId.AUTHENTICATED_READ: 200,
        ScenarioId.AUTHENTICATED_MUTATION: 201,
        ScenarioId.EXPENSIVE_READ: 200,
        ScenarioId.IDENTITY_LIFECYCLE: 200,
        ScenarioId.GOVERNED_AGENT: 503,
        ScenarioId.MALFORMED_AUTHENTICATED: 422,
        ScenarioId.BOLA_DENIED: 403,
        ScenarioId.STORE_UNAVAILABLE: 503,
    }

    try:
        for scenario_id, expected_status in expected.items():
            scenario = scenarios[scenario_id]
            executor.prepare(scenario)
            result = executor.execute(scenario, 0)
            assert result.status_code == expected_status
            assert result.invariant_failures == ()
            assert executor.cleanup(scenario).decision == "PASS"
    finally:
        executor.close()


class FakeSession:
    def scalar(self, statement):  # type: ignore[no-untyped-def]
        del statement
        return 1


class FakeTransaction:
    def __enter__(self) -> FakeSession:
        return FakeSession()

    def __exit__(self, exc_type, exc, traceback) -> bool:  # type: ignore[no-untyped-def]
        del exc_type, exc, traceback
        return False


class FakeDatabase:
    def tenant_transaction(self, tenant_id):  # type: ignore[no-untyped-def]
        del tenant_id
        return FakeTransaction()


class FakeLimiter:
    def __init__(self) -> None:
        self.calls = 0

    def consume(self, tenant_id, principal_id, policy_class):  # type: ignore[no-untyped-def]
        from campaignos.security import RateLimitDecision

        del tenant_id, principal_id
        self.calls += 1
        allowed = policy_class.value == "read" or self.calls <= 5
        return RateLimitDecision(
            allowed=allowed,
            policy_class=policy_class,
            retry_after_seconds=0 if allowed else 1,
            policy_version=9001,
        )

    def cleanup_expired(self, tenant_id, *, before, batch_size):  # type: ignore[no-untyped-def]
        del tenant_id, before
        return batch_size


class OperationalFakePostgresRuntime(FakePostgresRuntime):
    def __init__(self, database_url: str, *, role_name: str | None = None) -> None:
        super().__init__(database_url, role_name=role_name)
        self.limiter = FakeLimiter()
        self.database = FakeDatabase()
        self.inserted_stale = 0
        self.clear_calls = 0

    def clear_buckets(self) -> int:
        self.clear_calls += 1
        return 0

    def insert_stale_buckets(self, count: int) -> None:
        self.inserted_stale += count


def test_postgres_scenario_orchestration_is_bounded(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        executor_module,
        "_PostgresRuntime",
        OperationalFakePostgresRuntime,
    )
    executor = CampaignOSLoadExecutor("postgresql+psycopg://local/performance_test")
    scenarios = {
        scenario.scenario_id: scenario for scenario in default_workload_catalog().scenarios
    }

    try:
        contention = scenarios[ScenarioId.RATE_LIMIT_CONTENTION]
        executor.prepare(contention)
        results = [executor.execute(contention, index) for index in range(contention.request_count)]
        assert sum(result.status_code == 200 for result in results) == 5
        assert sum(result.status_code == 429 for result in results) == 15
        assert executor.cleanup(contention).residue_count == 0

        rollback = scenarios[ScenarioId.DOMAIN_ROLLBACK_ACCOUNTING]
        executor.prepare(rollback)
        result = executor.execute(rollback, 0)
        assert result.status_code == 200
        assert result.invariant_failures == ()
        assert executor.cleanup(rollback).decision == "PASS"

        cleanup = scenarios[ScenarioId.CLEANUP]
        executor.prepare(cleanup)
        assert executor._postgres.inserted_stale == cleanup.request_count  # type: ignore[attr-defined]
        assert [executor.execute(cleanup, index).invariant_failures for index in range(2)] == [
            (),
            (),
        ]
        assert executor.cleanup(cleanup).decision == "PASS"
    finally:
        executor.close()


def test_malformed_and_bola_scenarios_record_only_preauthorization_calls(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        executor_module,
        "_PostgresRuntime",
        OperationalFakePostgresRuntime,
    )
    executor = CampaignOSLoadExecutor("postgresql+psycopg://local/performance_test")
    scenarios = {
        scenario.scenario_id: scenario for scenario in default_workload_catalog().scenarios
    }
    try:
        for scenario_id in (
            ScenarioId.MALFORMED_AUTHENTICATED,
            ScenarioId.BOLA_DENIED,
        ):
            scenario = scenarios[scenario_id]
            executor.prepare(scenario)
            results = [executor.execute(scenario, index) for index in range(scenario.request_count)]
            assert all(result.invariant_failures == () for result in results)
            assert executor.invariant_failures(scenario) == ()

        bola = scenarios[ScenarioId.BOLA_DENIED]
        executor.prepare(bola)
        executor.execute(bola, 0)
        executor._recording_limiter.consume(  # type: ignore[attr-defined]
            executor_module.TENANT_ID,
            executor_module.PRINCIPAL_ID,
            executor_module.RateLimitPolicyClass.READ,
        )
        failures = executor.invariant_failures(bola)
        assert "TENANT_BUDGET_CONSUMED_BEFORE_AUTHORIZATION" in failures
        assert "UNEXPECTED_RATE_LIMIT_SCOPE_CALL" in failures
    finally:
        executor.close()
