from __future__ import annotations

from dataclasses import dataclass, field
from time import sleep

from campaignos.performance import (
    AuthorizationScope,
    BoundedLoadRunner,
    CleanupResult,
    OperationResult,
    PoolSnapshot,
    RouteClass,
    ScenarioId,
    WorkloadCatalog,
    WorkloadScenario,
    nearest_rank,
)


@dataclass
class ScriptedExecutor:
    results: list[OperationResult | Exception]
    before: PoolSnapshot = field(default_factory=PoolSnapshot)
    after: PoolSnapshot = field(default_factory=PoolSnapshot)
    cleanup_result: CleanupResult = field(
        default_factory=lambda: CleanupResult(
            decision="PASS",
            duration_ms=1,
            residue_count=0,
        )
    )
    delay_seconds: float = 0
    prepared: ScenarioId | None = None
    closed: bool = False

    def prepare(self, scenario: WorkloadScenario) -> None:
        self.prepared = scenario.scenario_id

    def execute(self, scenario: WorkloadScenario, request_index: int) -> OperationResult:
        assert self.prepared is scenario.scenario_id
        if self.delay_seconds:
            sleep(self.delay_seconds)
        result = self.results[request_index]
        if isinstance(result, Exception):
            raise result
        return result

    def pool_snapshot(self) -> PoolSnapshot:
        return self.after if self.closed else self.before

    def cleanup(self, scenario: WorkloadScenario) -> CleanupResult:
        del scenario
        self.closed = True
        return self.cleanup_result

    def close(self) -> None:
        self.closed = True


def scenario(
    *,
    scenario_id: ScenarioId = ScenarioId.AUTHENTICATED_READ,
    requests: int = 4,
    concurrency: int = 2,
    timeout: float = 1,
    expected_status_codes: tuple[int, ...] = (200,),
    expected_allowed: int | None = None,
    expected_denied: int | None = None,
) -> WorkloadScenario:
    return WorkloadScenario(
        scenario_id=scenario_id,
        route_class=(
            RouteClass.RATE_LIMIT_STORE
            if scenario_id is ScenarioId.RATE_LIMIT_CONTENTION
            else RouteClass.IDENTITY_READ
        ),
        policy_class="mutation" if scenario_id is ScenarioId.RATE_LIMIT_CONTENTION else "read",
        request_count=requests,
        concurrency=concurrency,
        timeout_seconds=timeout,
        expected_status_codes=expected_status_codes,
        authorization_scope=AuthorizationScope.TENANT,
        latency_ceiling_ms=10_000,
        expected_allowed=expected_allowed,
        expected_denied=expected_denied,
    )


def run_with(executor: ScriptedExecutor, workload: WorkloadScenario):
    return BoundedLoadRunner(
        catalog=WorkloadCatalog(catalog_version="1.0", scenarios=(workload,)),
        executor=executor,
        source_revision="b" * 40,
        postgresql_version="18.3",
    ).run()


def test_nearest_rank_is_deterministic() -> None:
    values = [10.0, 1.0, 7.0, 5.0, 3.0]
    assert nearest_rank(values, 50) == 5.0
    assert nearest_rank(values, 95) == 10.0
    assert nearest_rank(values, 99) == 10.0


def test_runner_passes_complete_bounded_success() -> None:
    workload = scenario()
    executor = ScriptedExecutor(
        results=[OperationResult(status_code=200, rate_limit_outcome="allowed") for _ in range(4)]
    )

    receipt = run_with(executor, workload)
    result = receipt.scenarios[0]

    assert receipt.overall_decision == "PASS"
    assert result.completed == 4
    assert result.response_classes.success_2xx == 4
    assert result.response_classes.transport_error == 0
    assert result.invariant_failures == ()
    assert executor.closed is True


def test_runner_enforces_exact_rate_limit_totals() -> None:
    workload = scenario(
        scenario_id=ScenarioId.RATE_LIMIT_CONTENTION,
        requests=4,
        concurrency=4,
        expected_status_codes=(200, 429),
        expected_allowed=2,
        expected_denied=2,
    )
    passing = ScriptedExecutor(
        results=[
            OperationResult(status_code=200, rate_limit_outcome="allowed"),
            OperationResult(status_code=429, rate_limit_outcome="denied", expected_error=True),
            OperationResult(status_code=200, rate_limit_outcome="allowed"),
            OperationResult(status_code=429, rate_limit_outcome="denied", expected_error=True),
        ]
    )
    assert run_with(passing, workload).overall_decision == "PASS"

    drifted = ScriptedExecutor(
        results=[OperationResult(status_code=200, rate_limit_outcome="allowed") for _ in range(4)]
    )
    result = run_with(drifted, workload).scenarios[0]
    assert result.overall_decision == "FAIL"
    assert "RATE_LIMIT_ALLOWED_COUNT_DRIFT" in result.invariant_failures
    assert "RATE_LIMIT_DENIED_COUNT_DRIFT" in result.invariant_failures


def test_runner_fails_on_transport_5xx_cleanup_and_pool_leak() -> None:
    workload = scenario()
    executor = ScriptedExecutor(
        results=[
            OperationResult(status_code=500, rate_limit_outcome="allowed"),
            RuntimeError("worker failure"),
            OperationResult(status_code=200, rate_limit_outcome="allowed"),
            OperationResult(status_code=200, rate_limit_outcome="allowed"),
        ],
        before=PoolSnapshot(size=2, checked_in=2, checked_out=0, overflow=0),
        after=PoolSnapshot(size=2, checked_in=1, checked_out=1, overflow=0),
        cleanup_result=CleanupResult(decision="FAIL", duration_ms=1, residue_count=1),
    )

    result = run_with(executor, workload).scenarios[0]

    assert result.overall_decision == "FAIL"
    assert result.response_classes.transport_error == 1
    assert "UNEXPECTED_SERVER_ERROR" in result.invariant_failures
    assert "CLEANUP_INCOMPLETE" in result.invariant_failures
    assert "POOL_CONNECTION_LEAK" in result.invariant_failures


def test_runner_records_scenario_timeout() -> None:
    workload = scenario(requests=1, concurrency=1, timeout=0.05)
    executor = ScriptedExecutor(
        results=[OperationResult(status_code=200, rate_limit_outcome="allowed")],
        delay_seconds=0.08,
    )

    result = run_with(executor, workload).scenarios[0]

    assert result.overall_decision == "FAIL"
    assert result.timed_out == 1
    assert "SCENARIO_TIMEOUT" in result.invariant_failures


def test_nearest_rank_rejects_invalid_percentiles_and_handles_empty_samples() -> None:
    import pytest

    assert nearest_rank([], 50) == 0
    with pytest.raises(ValueError, match="percentile"):
        nearest_rank([1.0], 0)
    with pytest.raises(ValueError, match="percentile"):
        nearest_rank([1.0], 101)


def test_runner_rejects_catalog_that_exceeds_local_limits() -> None:
    import pytest

    from campaignos.performance import RunnerLimits

    workload = scenario(requests=4, concurrency=2)
    executor = ScriptedExecutor(
        results=[OperationResult(status_code=200, rate_limit_outcome="allowed") for _ in range(4)]
    )
    with pytest.raises(ValueError, match="concurrency exceeds"):
        BoundedLoadRunner(
            catalog=WorkloadCatalog(catalog_version="1.0", scenarios=(workload,)),
            executor=executor,
            source_revision="d" * 40,
            postgresql_version="18.3",
            limits=RunnerLimits(max_concurrency=1),
        )


def test_runner_records_cleanup_exception_as_failure() -> None:
    class CleanupFailureExecutor(ScriptedExecutor):
        def cleanup(self, scenario: WorkloadScenario) -> CleanupResult:
            del scenario
            raise RuntimeError("cleanup failed")

    workload = scenario(requests=1, concurrency=1)
    executor = CleanupFailureExecutor(
        results=[OperationResult(status_code=200, rate_limit_outcome="allowed")]
    )
    result = run_with(executor, workload).scenarios[0]
    assert result.cleanup_decision == "FAIL"
    assert "CLEANUP_INCOMPLETE" in result.invariant_failures
