"""Process-isolated supervisor for hard scenario and harness deadlines."""

from __future__ import annotations

import multiprocessing
import os
import platform
import re
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from typing import Any, Literal
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from campaignos.performance.catalog import default_workload_catalog
from campaignos.performance.contracts import (
    LatencySummary,
    LoadVerificationReceipt,
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
    validate_receipt_against_catalog,
)
from campaignos.performance.executor import (
    CampaignOSLoadExecutor,
    cleanup_verification_role,
)
from campaignos.performance.runner import BoundedLoadRunner


def _validated_database_url(database_url: str) -> None:
    parsed = make_url(database_url)
    if parsed.drivername != "postgresql+psycopg" or not (
        parsed.database and parsed.database.endswith("_test")
    ):
        raise ValueError("supervised load verification requires PostgreSQL *_test")


def _postgresql_version(database_url: str) -> str:
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            raw = str(connection.scalar(text("SHOW server_version")))
    finally:
        engine.dispose()
    matched = re.match(r"^(\d+(?:\.\d+){0,2})", raw)
    if matched is None:
        raise ValueError("PostgreSQL version could not be normalized")
    return matched.group(1)


def _scenario_process_entrypoint(
    database_url: str,
    role_name: str,
    source_revision: str,
    scenario_payload: dict[str, object],
    output_path: str,
) -> None:
    """Run exactly one scenario in a killable child process."""

    scenario = WorkloadScenario.model_validate(scenario_payload)
    catalog = default_workload_catalog()
    executor = CampaignOSLoadExecutor(database_url, role_name=role_name)
    runner = BoundedLoadRunner(
        catalog=catalog,
        executor=executor,
        source_revision=source_revision,
        postgresql_version=executor.postgresql_version,
    )
    receipt = runner.run_scenario(scenario)
    if receipt.timed_out == 0:
        executor.close()
    target = Path(output_path)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(receipt.model_dump_json(indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)


def _failed_scenario_receipt(
    scenario: WorkloadScenario,
    *,
    failure_code: str,
    timed_out: bool,
) -> ScenarioReceipt:
    snapshot = PoolSnapshot()
    timeout_count = scenario.request_count if timed_out else 0
    transport_count = 0 if timed_out else scenario.request_count
    return ScenarioReceipt(
        scenario_id=scenario.scenario_id,
        policy_class=scenario.policy_class,
        configured_requests=scenario.request_count,
        configured_concurrency=scenario.concurrency,
        configured_timeout_seconds=scenario.timeout_seconds,
        completed=0,
        expected_errors=0,
        unexpected_errors=transport_count,
        timed_out=timeout_count,
        response_classes=ResponseClassCounts(
            success_2xx=0,
            redirect_3xx=0,
            client_error_4xx=0,
            server_error_5xx=0,
            transport_error=transport_count,
        ),
        rate_limit_outcomes=RateLimitOutcomeCounts(
            allowed=0,
            denied=0,
            unavailable=0,
            not_applicable=0,
        ),
        latency=LatencySummary(
            minimum_ms=0,
            median_ms=0,
            p95_ms=0,
            p99_ms=0,
            maximum_ms=0,
        ),
        pool=PoolEvidence(before=snapshot, peak=snapshot, after=snapshot),
        invariant_failures=(failure_code,),
        invariant_decision="FAIL",
        threshold_decision="FAIL",
        cleanup_decision="FAIL",
        cleanup_duration_ms=0,
        overall_decision="FAIL",
    )


class ProcessIsolatedLoadSupervisor:
    """Terminate a child process when any scenario exceeds its hard deadline."""

    def __init__(
        self,
        *,
        database_url: str,
        source_revision: str,
        catalog: WorkloadCatalog | None = None,
        limits: RunnerLimits | None = None,
    ) -> None:
        _validated_database_url(database_url)
        if not re.fullmatch(r"[0-9a-f]{40}", source_revision):
            raise ValueError("source revision must be an exact Git SHA")
        self.database_url = database_url
        self.source_revision = source_revision
        self.catalog = catalog or default_workload_catalog()
        self.limits = limits or RunnerLimits()
        self._validate_limits()

    def _validate_limits(self) -> None:
        for scenario in self.catalog.scenarios:
            if scenario.concurrency > self.limits.max_concurrency:
                raise ValueError("scenario concurrency exceeds supervisor limit")
            if scenario.request_count > self.limits.max_requests_per_scenario:
                raise ValueError("scenario requests exceed supervisor limit")
            if scenario.timeout_seconds > self.limits.max_scenario_seconds:
                raise ValueError("scenario timeout exceeds supervisor limit")
        if sum(item.timeout_seconds for item in self.catalog.scenarios) > (
            self.limits.max_harness_seconds
        ):
            raise ValueError("catalog timeout envelope exceeds supervisor limit")

    def run(self) -> LoadVerificationReceipt:
        started = monotonic()
        version = _postgresql_version(self.database_url)
        receipts: list[ScenarioReceipt] = []
        context = multiprocessing.get_context("spawn")
        with TemporaryDirectory(prefix="campaignos-perf-") as directory:
            for scenario in self.catalog.scenarios:
                remaining = self.limits.max_harness_seconds - (monotonic() - started)
                if remaining <= 0:
                    receipts.append(
                        _failed_scenario_receipt(
                            scenario,
                            failure_code="HARNESS_TIMEOUT",
                            timed_out=True,
                        )
                    )
                    continue
                receipts.append(
                    self._run_process_scenario(
                        context=context,
                        scenario=scenario,
                        directory=Path(directory),
                        timeout_seconds=min(scenario.timeout_seconds, remaining),
                    )
                )

        overall: Literal["PASS", "FAIL"] = (
            "PASS" if all(item.overall_decision == "PASS" for item in receipts) else "FAIL"
        )
        receipt = LoadVerificationReceipt(
            source_revision=self.source_revision,
            generated_at=datetime.now(UTC),
            python_version=platform.python_version(),
            postgresql_version=version,
            catalog_version=self.catalog.catalog_version,
            runtime_context=RuntimeContext(
                operating_system=platform.system() or "Unknown",
                machine=platform.machine() or "unknown",
                cpu_count=os.cpu_count() or 1,
            ),
            runner_limits=self.limits,
            scenarios=tuple(receipts),
            overall_decision=overall,
        )
        validate_receipt_against_catalog(receipt, self.catalog)
        assert_receipt_sanitized(receipt)
        return receipt

    def _run_process_scenario(
        self,
        *,
        context: Any,
        scenario: WorkloadScenario,
        directory: Path,
        timeout_seconds: float,
    ) -> ScenarioReceipt:
        role_name = f"campaignos_perf_{uuid4().hex[:12]}"
        output = directory / f"{scenario.scenario_id.value}.json"
        process = context.Process(
            target=_scenario_process_entrypoint,
            args=(
                self.database_url,
                role_name,
                self.source_revision,
                scenario.model_dump(mode="json"),
                str(output),
            ),
            name=f"campaignos-{scenario.scenario_id.value}",
        )
        scenario_started = monotonic()
        process.start()
        remaining = max(0.0, timeout_seconds - (monotonic() - scenario_started))
        process.join(timeout=remaining)
        timed_out = process.is_alive()
        if timed_out:
            process.terminate()
            process.join(timeout=1)
            if process.is_alive():
                process.kill()
                process.join(timeout=1)

        cleanup_failed = False
        try:
            cleanup_verification_role(self.database_url, role_name)
        except Exception:
            cleanup_failed = True

        if timed_out:
            return _failed_scenario_receipt(
                scenario,
                failure_code="SCENARIO_PROCESS_TIMEOUT",
                timed_out=True,
            )
        if cleanup_failed:
            return _failed_scenario_receipt(
                scenario,
                failure_code="SUPERVISOR_ROLE_CLEANUP_FAILURE",
                timed_out=False,
            )
        if process.exitcode != 0 or not output.is_file():
            return _failed_scenario_receipt(
                scenario,
                failure_code="SCENARIO_PROCESS_FAILURE",
                timed_out=False,
            )
        try:
            receipt = ScenarioReceipt.model_validate_json(output.read_text(encoding="utf-8"))
        except Exception:
            return _failed_scenario_receipt(
                scenario,
                failure_code="SCENARIO_RECEIPT_INVALID",
                timed_out=False,
            )
        if receipt.scenario_id is not scenario.scenario_id:
            return _failed_scenario_receipt(
                scenario,
                failure_code="SCENARIO_RECEIPT_ID_DRIFT",
                timed_out=False,
            )
        return receipt
