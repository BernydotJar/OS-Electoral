from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from campaignos.performance import (
    AuthorizationScope,
    LoadVerificationReceipt,
    RouteClass,
    RunnerLimits,
    ScenarioId,
    WorkloadCatalog,
    WorkloadScenario,
    assert_complete_catalog,
    assert_receipt_sanitized,
    default_workload_catalog,
    load_and_verify_receipt,
    write_receipt,
)
from campaignos.performance.contracts import RuntimeContext


def failure_receipt() -> LoadVerificationReceipt:
    return LoadVerificationReceipt(
        source_revision="a" * 40,
        generated_at=datetime(2026, 7, 31, tzinfo=UTC),
        python_version="3.14.0",
        postgresql_version="18.3",
        catalog_version="1.0",
        runtime_context=RuntimeContext(
            operating_system="Linux",
            machine="x86_64",
            cpu_count=4,
        ),
        runner_limits=RunnerLimits(),
        scenarios=(),
        harness_failure_codes=("BOOTSTRAP_FAILURE",),
        overall_decision="FAIL",
    )


def test_default_catalog_is_complete_unique_and_bounded() -> None:
    catalog = default_workload_catalog()

    assert catalog.catalog_version == "1.0"
    assert {scenario.scenario_id for scenario in catalog.scenarios} == set(ScenarioId)
    assert len(catalog.scenarios) == len(ScenarioId) == 11
    assert max(scenario.concurrency for scenario in catalog.scenarios) == 20
    assert all(scenario.request_count <= 600 for scenario in catalog.scenarios)
    assert all(scenario.timeout_seconds <= 60 for scenario in catalog.scenarios)
    contention = next(
        scenario
        for scenario in catalog.scenarios
        if scenario.scenario_id is ScenarioId.RATE_LIMIT_CONTENTION
    )
    assert contention.expected_allowed == 5
    assert contention.expected_denied == 15
    assert contention.request_count == 20


def test_catalog_rejects_duplicate_missing_and_unbounded_scenarios() -> None:
    scenario = default_workload_catalog().scenarios[0]
    with pytest.raises(ValidationError, match="scenario IDs must be unique"):
        WorkloadCatalog(catalog_version="1.0", scenarios=(scenario, scenario))

    incomplete = WorkloadCatalog(catalog_version="1.0", scenarios=(scenario,))
    with pytest.raises(ValueError, match="coverage mismatch"):
        assert_complete_catalog(incomplete)

    with pytest.raises(ValidationError):
        WorkloadScenario(
            scenario_id=ScenarioId.AUTHENTICATED_READ,
            route_class=RouteClass.IDENTITY_READ,
            policy_class="read",
            request_count=601,
            concurrency=21,
            timeout_seconds=61,
            expected_status_codes=(200,),
            authorization_scope=AuthorizationScope.PREAUTH,
            latency_ceiling_ms=1_000,
        )


def test_exact_rate_limit_expectations_must_cover_every_request() -> None:
    with pytest.raises(ValidationError, match="allowed and denied totals"):
        WorkloadScenario(
            scenario_id=ScenarioId.RATE_LIMIT_CONTENTION,
            route_class=RouteClass.RATE_LIMIT_STORE,
            policy_class="mutation",
            request_count=20,
            concurrency=20,
            timeout_seconds=10,
            expected_status_codes=(200, 429),
            authorization_scope=AuthorizationScope.TENANT,
            latency_ceiling_ms=10_000,
            expected_allowed=5,
            expected_denied=14,
        )


def test_receipt_schema_is_strict_and_failure_receipts_are_sanitized(tmp_path: Path) -> None:
    receipt = failure_receipt()
    output = tmp_path / "receipt.json"

    write_receipt(output, receipt)
    loaded = load_and_verify_receipt(output)

    assert loaded == receipt
    assert loaded.production_capacity_claim is False
    assert loaded.external_effects == "NONE"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        LoadVerificationReceipt.model_validate(
            {**receipt.model_dump(mode="json"), "database_url": "forbidden"}
        )
    with pytest.raises(ValidationError, match="passing receipts require scenario evidence"):
        LoadVerificationReceipt.model_validate(
            {
                **receipt.model_dump(mode="json"),
                "harness_failure_codes": [],
                "overall_decision": "PASS",
            }
        )


@pytest.mark.parametrize(
    "payload",
    [
        {"database_url": "hidden"},
        {"safe": "Bearer secret-value"},
        {"safe": "postgresql+psycopg://user:password@host/database"},
        {"safe": "https://example.test/internal"},
        {"safe": "11111111-1111-4111-8111-111111111111"},
        {"safe": "operator@example.test"},
        {"safe": "192.0.2.4"},
    ],
)
def test_receipt_sanitizer_rejects_sensitive_keys_and_values(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="sensitive receipt"):
        assert_receipt_sanitized(payload)


def test_receipt_loader_rejects_corrupt_json(tmp_path: Path) -> None:
    output = tmp_path / "corrupt.json"
    output.write_text("not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="receipt is invalid"):
        load_and_verify_receipt(output)


def test_default_verifier_rejects_truncated_pass_receipt(tmp_path: Path) -> None:
    from campaignos.performance import (
        BoundedLoadRunner,
        CleanupResult,
        OperationResult,
        PoolSnapshot,
        WorkloadCatalog,
        default_workload_catalog,
    )

    class OneScenarioExecutor:
        def prepare(self, scenario):  # type: ignore[no-untyped-def]
            del scenario

        def execute(self, scenario, request_index):  # type: ignore[no-untyped-def]
            del scenario, request_index
            return OperationResult(status_code=200, rate_limit_outcome="allowed")

        def invariant_failures(self, scenario):  # type: ignore[no-untyped-def]
            del scenario
            return ()

        def pool_snapshot(self):  # type: ignore[no-untyped-def]
            return PoolSnapshot()

        def cleanup(self, scenario):  # type: ignore[no-untyped-def]
            del scenario
            return CleanupResult(decision="PASS", duration_ms=0, residue_count=0)

        def close(self):  # type: ignore[no-untyped-def]
            return None

    configured = default_workload_catalog().scenarios[0]
    catalog = WorkloadCatalog(catalog_version="1.0", scenarios=(configured,))
    receipt = BoundedLoadRunner(
        catalog=catalog,
        executor=OneScenarioExecutor(),
        source_revision="e" * 40,
        postgresql_version="18.3",
    ).run()
    assert receipt.overall_decision == "PASS"
    output = tmp_path / "truncated-pass.json"
    output.write_text(receipt.model_dump_json(), encoding="utf-8")

    with pytest.raises(ValueError, match="overall decision does not match catalog evidence"):
        load_and_verify_receipt(output)


def test_top_level_pass_rejects_failed_child_scenario() -> None:
    from campaignos.performance.contracts import (
        LatencySummary,
        PoolEvidence,
        PoolSnapshot,
        RateLimitOutcomeCounts,
        ResponseClassCounts,
        ScenarioReceipt,
    )

    failed = ScenarioReceipt(
        scenario_id=ScenarioId.AUTHENTICATED_READ,
        policy_class="read",
        configured_requests=1,
        configured_concurrency=1,
        configured_timeout_seconds=1,
        completed=0,
        expected_errors=0,
        unexpected_errors=1,
        timed_out=0,
        response_classes=ResponseClassCounts(
            success_2xx=0,
            redirect_3xx=0,
            client_error_4xx=0,
            server_error_5xx=0,
            transport_error=1,
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
        pool=PoolEvidence(before=PoolSnapshot(), peak=PoolSnapshot(), after=PoolSnapshot()),
        invariant_failures=("SCENARIO_PROCESS_FAILURE",),
        invariant_decision="FAIL",
        threshold_decision="FAIL",
        cleanup_decision="FAIL",
        cleanup_duration_ms=0,
        overall_decision="FAIL",
    )
    payload = failure_receipt().model_dump(mode="json")
    payload.update(
        {
            "scenarios": [failed.model_dump(mode="json")],
            "harness_failure_codes": [],
            "overall_decision": "PASS",
        }
    )
    with pytest.raises(ValidationError, match="failed scenario"):
        LoadVerificationReceipt.model_validate(payload)
