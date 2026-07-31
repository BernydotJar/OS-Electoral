from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from campaignos.performance import (
    BoundedLoadRunner,
    CampaignOSLoadExecutor,
    ScenarioId,
    assert_receipt_sanitized,
    default_workload_catalog,
    load_and_verify_receipt,
    write_receipt,
)


def postgres_test_url() -> str:
    value = os.environ.get("CAMPAIGNOS_TEST_DATABASE_URL", "")
    if not value:
        pytest.skip("CAMPAIGNOS_TEST_DATABASE_URL is not configured")
    parsed = make_url(value)
    if parsed.drivername != "postgresql+psycopg" or not (
        parsed.database and parsed.database.endswith("_test")
    ):
        pytest.fail("performance integration tests require an isolated PostgreSQL *_test database")
    return value


@pytest.mark.postgres
def test_bounded_authenticated_load_harness_against_postgres(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_url = postgres_test_url()
    monkeypatch.setenv("CAMPAIGNOS_DATABASE_URL", database_url)
    alembic = Config("alembic.ini")
    command.upgrade(alembic, "head")
    command.check(alembic)

    executor = CampaignOSLoadExecutor(database_url)
    runner = BoundedLoadRunner(
        catalog=default_workload_catalog(),
        executor=executor,
        source_revision="c" * 40,
        postgresql_version=executor.postgresql_version,
    )
    receipt = runner.run()

    assert receipt.overall_decision == "PASS"
    assert receipt.production_capacity_claim is False
    assert receipt.external_effects == "NONE"
    assert {scenario.scenario_id for scenario in receipt.scenarios} == set(ScenarioId)
    assert all(scenario.overall_decision == "PASS" for scenario in receipt.scenarios)
    assert all(scenario.timed_out == 0 for scenario in receipt.scenarios)
    assert all(scenario.unexpected_errors == 0 for scenario in receipt.scenarios)
    assert all(scenario.pool.after.checked_out == 0 for scenario in receipt.scenarios)

    contention = next(
        scenario
        for scenario in receipt.scenarios
        if scenario.scenario_id is ScenarioId.RATE_LIMIT_CONTENTION
    )
    assert contention.rate_limit_outcomes.allowed == 5
    assert contention.rate_limit_outcomes.denied == 15
    assert contention.response_classes.success_2xx == 5
    assert contention.response_classes.client_error_4xx == 15

    expected_fail_closed = {
        ScenarioId.GOVERNED_AGENT,
        ScenarioId.STORE_UNAVAILABLE,
    }
    for scenario in receipt.scenarios:
        if scenario.scenario_id in expected_fail_closed:
            assert scenario.response_classes.server_error_5xx == scenario.configured_requests
            assert scenario.expected_errors == scenario.configured_requests
        else:
            assert scenario.response_classes.server_error_5xx == 0

    assert_receipt_sanitized(receipt)
    output = tmp_path / "load-verification.json"
    write_receipt(output, receipt)
    assert load_and_verify_receipt(output) == receipt
