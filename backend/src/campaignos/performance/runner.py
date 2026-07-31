"""Bounded concurrent runner that prioritizes correctness over timing."""

from __future__ import annotations

import os
import platform
from collections import Counter
from concurrent.futures import Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from datetime import UTC, datetime
from time import monotonic_ns
from typing import Literal, Protocol

from campaignos.performance.contracts import (
    CleanupResult,
    LatencySummary,
    LoadVerificationReceipt,
    OperationResult,
    PoolEvidence,
    PoolSnapshot,
    RateLimitOutcomeCounts,
    ResponseClassCounts,
    RunnerLimits,
    RuntimeContext,
    ScenarioReceipt,
    WorkloadCatalog,
    WorkloadScenario,
    assert_receipt_sanitized,
)


class ScenarioExecutor(Protocol):
    def prepare(self, scenario: WorkloadScenario) -> None: ...

    def execute(self, scenario: WorkloadScenario, request_index: int) -> OperationResult: ...

    def pool_snapshot(self) -> PoolSnapshot: ...

    def cleanup(self, scenario: WorkloadScenario) -> CleanupResult: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class _MeasuredResult:
    result: OperationResult | None
    latency_ms: float
    pool: PoolSnapshot
    failed: bool


def nearest_rank(values: list[float], percentile: int) -> float:
    """Return the documented nearest-rank percentile from the complete sample."""

    if not values:
        return 0.0
    if percentile <= 0 or percentile > 100:
        raise ValueError("percentile must be greater than zero and at most 100")
    ordered = sorted(values)
    rank = max(1, (len(ordered) * percentile + 99) // 100)
    return ordered[min(rank - 1, len(ordered) - 1)]


def summarize_latency(values: list[float]) -> LatencySummary:
    if not values:
        return LatencySummary(
            minimum_ms=0,
            median_ms=0,
            p95_ms=0,
            p99_ms=0,
            maximum_ms=0,
        )
    ordered = sorted(values)
    return LatencySummary(
        minimum_ms=ordered[0],
        median_ms=nearest_rank(ordered, 50),
        p95_ms=nearest_rank(ordered, 95),
        p99_ms=nearest_rank(ordered, 99),
        maximum_ms=ordered[-1],
    )


class BoundedLoadRunner:
    def __init__(
        self,
        *,
        catalog: WorkloadCatalog,
        executor: ScenarioExecutor,
        source_revision: str,
        postgresql_version: str,
        limits: RunnerLimits | None = None,
    ) -> None:
        self.catalog = catalog
        self.executor = executor
        self.source_revision = source_revision
        self.postgresql_version = postgresql_version
        self.limits = limits or RunnerLimits()
        self._validate_catalog_limits()

    def _validate_catalog_limits(self) -> None:
        for scenario in self.catalog.scenarios:
            if scenario.concurrency > self.limits.max_concurrency:
                raise ValueError("scenario concurrency exceeds runner limit")
            if scenario.request_count > self.limits.max_requests_per_scenario:
                raise ValueError("scenario request count exceeds runner limit")
            if scenario.timeout_seconds > self.limits.max_scenario_seconds:
                raise ValueError("scenario timeout exceeds runner limit")
        total_timeout = sum(scenario.timeout_seconds for scenario in self.catalog.scenarios)
        if total_timeout > self.limits.max_harness_seconds:
            raise ValueError("catalog timeout envelope exceeds harness limit")

    def run(self) -> LoadVerificationReceipt:
        harness_started = monotonic_ns()
        scenario_receipts: list[ScenarioReceipt] = []
        try:
            for scenario in self.catalog.scenarios:
                elapsed_seconds = (monotonic_ns() - harness_started) / 1_000_000_000
                if elapsed_seconds >= self.limits.max_harness_seconds:
                    scenario_receipts.append(self._harness_timeout_receipt(scenario))
                    continue
                scenario_receipts.append(self._run_scenario(scenario))
        finally:
            self.executor.close()

        overall: Literal["PASS", "FAIL"] = (
            "PASS"
            if scenario_receipts
            and all(receipt.overall_decision == "PASS" for receipt in scenario_receipts)
            else "FAIL"
        )
        receipt = LoadVerificationReceipt(
            source_revision=self.source_revision,
            generated_at=datetime.now(UTC),
            python_version=platform.python_version(),
            postgresql_version=self.postgresql_version,
            catalog_version=self.catalog.catalog_version,
            runtime_context=RuntimeContext(
                operating_system=platform.system() or "Unknown",
                machine=platform.machine() or "unknown",
                cpu_count=os.cpu_count() or 1,
            ),
            runner_limits=self.limits,
            scenarios=tuple(scenario_receipts),
            overall_decision=overall,
        )
        assert_receipt_sanitized(receipt)
        return receipt

    def _run_scenario(self, scenario: WorkloadScenario) -> ScenarioReceipt:
        self.executor.prepare(scenario)
        before = self.executor.pool_snapshot()
        executor = ThreadPoolExecutor(
            max_workers=scenario.concurrency,
            thread_name_prefix=f"perf-{scenario.scenario_id.value}",
        )
        futures: list[Future[_MeasuredResult]] = [
            executor.submit(self._execute_measured, scenario, index)
            for index in range(scenario.request_count)
        ]
        done, pending = wait(futures, timeout=scenario.timeout_seconds)
        timed_out = len(pending)
        for future in pending:
            future.cancel()
        executor.shutdown(wait=True, cancel_futures=True)

        measured: list[_MeasuredResult] = []
        for future in done:
            try:
                measured.append(future.result())
            except Exception:
                measured.append(
                    _MeasuredResult(
                        result=None,
                        latency_ms=0,
                        pool=self.executor.pool_snapshot(),
                        failed=True,
                    )
                )

        cleanup_started = monotonic_ns()
        try:
            cleanup = self.executor.cleanup(scenario)
        except Exception:
            cleanup = CleanupResult(
                decision="FAIL",
                duration_ms=(monotonic_ns() - cleanup_started) / 1_000_000,
                residue_count=1,
            )
        after = self.executor.pool_snapshot()
        peak = _peak_pool([before, after, *(item.pool for item in measured)])

        results = [item.result for item in measured if item.result is not None]
        latencies = [item.latency_ms for item in measured if item.result is not None]
        response_classes = Counter(_response_class(result.status_code) for result in results)
        outcomes = Counter(result.rate_limit_outcome for result in results)
        invariant_failures = {
            failure for result in results for failure in result.invariant_failures
        }
        transport_errors = sum(item.failed for item in measured)
        unexpected_errors = transport_errors
        unexpected_errors += sum(
            result.status_code not in scenario.expected_status_codes
            or bool(result.invariant_failures)
            for result in results
        )
        expected_errors = sum(result.expected_error for result in results)

        if timed_out:
            invariant_failures.add("SCENARIO_TIMEOUT")
        if cleanup.decision != "PASS" or cleanup.residue_count:
            invariant_failures.add("CLEANUP_INCOMPLETE")
        if after.checked_out > before.checked_out:
            invariant_failures.add("POOL_CONNECTION_LEAK")
        if response_classes["5xx"] and not all(
            result.expected_error or result.status_code < 500 for result in results
        ):
            invariant_failures.add("UNEXPECTED_SERVER_ERROR")
        if scenario.expected_allowed is not None:
            if outcomes["allowed"] != scenario.expected_allowed:
                invariant_failures.add("RATE_LIMIT_ALLOWED_COUNT_DRIFT")
            if outcomes["denied"] != scenario.expected_denied:
                invariant_failures.add("RATE_LIMIT_DENIED_COUNT_DRIFT")

        latency = summarize_latency(latencies)
        invariant_decision: Literal["PASS", "FAIL"] = (
            "PASS" if not invariant_failures and unexpected_errors == 0 else "FAIL"
        )
        threshold_decision: Literal["PASS", "FAIL"] = (
            "PASS" if timed_out == 0 and latency.p99_ms <= scenario.latency_ceiling_ms else "FAIL"
        )
        cleanup_decision: Literal["PASS", "FAIL"] = (
            "PASS"
            if cleanup.decision == "PASS"
            and cleanup.residue_count == 0
            and after.checked_out <= before.checked_out
            else "FAIL"
        )
        overall: Literal["PASS", "FAIL"] = (
            "PASS"
            if invariant_decision == threshold_decision == cleanup_decision == "PASS"
            else "FAIL"
        )
        return ScenarioReceipt(
            scenario_id=scenario.scenario_id,
            policy_class=scenario.policy_class,
            configured_requests=scenario.request_count,
            configured_concurrency=scenario.concurrency,
            configured_timeout_seconds=scenario.timeout_seconds,
            completed=len(results),
            expected_errors=expected_errors,
            unexpected_errors=unexpected_errors,
            timed_out=timed_out,
            response_classes=ResponseClassCounts(
                success_2xx=response_classes["2xx"],
                redirect_3xx=response_classes["3xx"],
                client_error_4xx=response_classes["4xx"],
                server_error_5xx=response_classes["5xx"],
                transport_error=transport_errors,
            ),
            rate_limit_outcomes=RateLimitOutcomeCounts(
                allowed=outcomes["allowed"],
                denied=outcomes["denied"],
                unavailable=outcomes["unavailable"],
                not_applicable=outcomes["not_applicable"],
            ),
            latency=latency,
            pool=PoolEvidence(before=before, peak=peak, after=after),
            invariant_failures=tuple(sorted(invariant_failures)),
            invariant_decision=invariant_decision,
            threshold_decision=threshold_decision,
            cleanup_decision=cleanup_decision,
            cleanup_duration_ms=cleanup.duration_ms,
            overall_decision=overall,
        )

    def _execute_measured(self, scenario: WorkloadScenario, request_index: int) -> _MeasuredResult:
        started = monotonic_ns()
        try:
            result = self.executor.execute(scenario, request_index)
            failed = False
        except Exception:
            result = None
            failed = True
        latency_ms = (monotonic_ns() - started) / 1_000_000
        return _MeasuredResult(
            result=result,
            latency_ms=latency_ms,
            pool=self.executor.pool_snapshot(),
            failed=failed,
        )

    def _harness_timeout_receipt(self, scenario: WorkloadScenario) -> ScenarioReceipt:
        snapshot = self.executor.pool_snapshot()
        return ScenarioReceipt(
            scenario_id=scenario.scenario_id,
            policy_class=scenario.policy_class,
            configured_requests=scenario.request_count,
            configured_concurrency=scenario.concurrency,
            configured_timeout_seconds=scenario.timeout_seconds,
            completed=0,
            expected_errors=0,
            unexpected_errors=0,
            timed_out=scenario.request_count,
            response_classes=ResponseClassCounts(
                success_2xx=0,
                redirect_3xx=0,
                client_error_4xx=0,
                server_error_5xx=0,
                transport_error=scenario.request_count,
            ),
            rate_limit_outcomes=RateLimitOutcomeCounts(
                allowed=0,
                denied=0,
                unavailable=0,
                not_applicable=0,
            ),
            latency=summarize_latency([]),
            pool=PoolEvidence(before=snapshot, peak=snapshot, after=snapshot),
            invariant_failures=("HARNESS_TIMEOUT",),
            invariant_decision="FAIL",
            threshold_decision="FAIL",
            cleanup_decision="FAIL",
            cleanup_duration_ms=0,
            overall_decision="FAIL",
        )


def _response_class(status_code: int) -> str:
    return f"{status_code // 100}xx"


def _peak_pool(snapshots: list[PoolSnapshot]) -> PoolSnapshot:
    return PoolSnapshot(
        size=max(item.size for item in snapshots),
        checked_in=max(item.checked_in for item in snapshots),
        checked_out=max(item.checked_out for item in snapshots),
        overflow=max(item.overflow for item in snapshots),
    )
