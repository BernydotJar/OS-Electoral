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
