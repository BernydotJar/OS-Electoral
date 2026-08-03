from __future__ import annotations

import copy
import json
import shutil
import stat
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError
from scripts.operations.verify_release_rollback import main

from campaignos.operability.rollback import (
    EXPECTED_SCENARIOS,
    ArtifactCheck,
    AuthorityCheck,
    HealthCheck,
    RehearsalContext,
    RollbackFailureReceipt,
    RollbackPolicy,
    RollbackReceipt,
    RollbackResponse,
    assert_sanitized_receipt,
    build_receipt,
    load_policy,
    validate_policy_against_repository,
    write_receipt,
)

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "program/rollback-readiness.json"
SOURCE = "a" * 40
PREVIOUS = "b" * 40


def policy() -> RollbackPolicy:
    return load_policy(POLICY_PATH)


def git_revisions() -> tuple[str, str]:
    git = shutil.which("git")
    assert git is not None
    source = subprocess.run(  # noqa: S603 - resolved git and fixed test reference.
        [git, "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    previous = subprocess.run(  # noqa: S603 - resolved git and fixed test reference.
        [git, "rev-parse", "HEAD^"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return source, previous


def context_for(scenario_id: str, **overrides: object) -> RehearsalContext:
    values: dict[str, object] = {
        "scenario_id": scenario_id,
        "source_revision": SOURCE,
        "candidate_revision": SOURCE,
        "previous_known_good_revision": PREVIOUS,
        "environment_classification": "CONSTRAINED_NON_PRODUCTION",
        "authority": AuthorityCheck(
            granted=True,
            scope="CONSTRAINED_NON_PRODUCTION_REHEARSAL",
        ),
        "artifact": ArtifactCheck(
            reference=PREVIOUS,
            immutable=True,
            provenance_present=True,
        ),
        "migration_head": "20260801_0013",
        "committed_writes_observed": False,
        "health_checks": (
            HealthCheck(name="liveness", passed=False),
            HealthCheck(name="readiness", passed=False),
            HealthCheck(name="database", passed=True),
        ),
        "configuration_snapshot_present": True,
        "protected_controls_preserved": True,
        "verified_backup_present": True,
        "isolated_restore_target": True,
        "automatic_worker_replay_requested": False,
        "production_target": False,
        "requested_operation": "AUTO_SELECT",
    }
    values.update(overrides)
    return RehearsalContext.model_validate(values)


def test_policy_matches_repository_migrations_and_required_scenarios() -> None:
    current = policy()

    validate_policy_against_repository(current, ROOT)

    assert {item.id: item.expected_response for item in current.scenarios} == EXPECTED_SCENARIOS
    assert current.current_migration_head == "20260801_0013"
    assert current.production_rollback_claim is False
    assert current.production_status == "BLOCKED"


@pytest.mark.parametrize(("scenario_id", "expected"), EXPECTED_SCENARIOS.items())
def test_every_required_scenario_selects_the_reviewed_response(
    scenario_id: str,
    expected: RollbackResponse,
) -> None:
    overrides: dict[str, object] = {}
    if scenario_id == "application_health_failure_unknown_schema":
        overrides["migration_head"] = "unknown_revision"
    if scenario_id == "missing_authority_or_evidence":
        overrides["authority"] = AuthorityCheck(
            granted=False,
            scope="CONSTRAINED_NON_PRODUCTION_REHEARSAL",
        )
        overrides["artifact"] = ArtifactCheck(
            reference="mutable-tag",
            immutable=False,
            provenance_present=False,
        )
    if scenario_id == "suspected_data_integrity_after_writes":
        overrides["committed_writes_observed"] = True

    receipt = build_receipt(policy(), context_for(scenario_id, **overrides))

    assert receipt.selected_response == expected
    assert receipt.expected_response == expected
    assert receipt.decision == "PASS"
    assert receipt.production_rollback_claim is False
    assert receipt.external_effects == "NONE"
    assert receipt.cleanup.restore_target_state == "NOT_CREATED"


def test_destructive_alembic_downgrade_is_refused() -> None:
    receipt = build_receipt(
        policy(),
        context_for(
            "application_health_failure_backward_compatible",
            requested_operation="alembic downgrade -1",
        ),
    )

    assert receipt.selected_response == RollbackResponse.REFUSE_UNSAFE_ROLLBACK
    assert receipt.decision == "FAIL"
    assert receipt.decision_reason == "DESTRUCTIVE_OPERATION_REFUSED"


def test_mutable_or_unproven_artifact_is_refused() -> None:
    receipt = build_receipt(
        policy(),
        context_for(
            "application_health_failure_backward_compatible",
            artifact=ArtifactCheck(
                reference="latest",
                immutable=False,
                provenance_present=False,
            ),
        ),
    )

    assert receipt.selected_response == RollbackResponse.REFUSE_UNSAFE_ROLLBACK
    assert receipt.decision_reason == "ARTIFACT_EVIDENCE_INVALID"


def test_configuration_reversal_cannot_weaken_protected_controls() -> None:
    receipt = build_receipt(
        policy(),
        context_for(
            "configuration_regression",
            protected_controls_preserved=False,
        ),
    )

    assert receipt.selected_response == RollbackResponse.REFUSE_UNSAFE_ROLLBACK
    assert receipt.decision_reason == "PROTECTED_CONTROL_WEAKENING_REFUSED"


def test_worker_replay_is_never_automatic() -> None:
    receipt = build_receipt(
        policy(),
        context_for(
            "worker_retry_or_dead_letter_growth",
            automatic_worker_replay_requested=True,
        ),
    )

    assert receipt.selected_response == RollbackResponse.REFUSE_UNSAFE_ROLLBACK
    assert receipt.decision_reason == "AUTOMATIC_REPLAY_REFUSED"


def test_production_target_is_refused_even_with_other_evidence() -> None:
    receipt = build_receipt(
        policy(),
        context_for("release_stopped_before_migration", production_target=True),
    )

    assert receipt.selected_response == RollbackResponse.REFUSE_UNSAFE_ROLLBACK
    assert receipt.decision_reason == "PRODUCTION_TARGET_FORBIDDEN"


def test_unknown_policy_fields_fail_closed() -> None:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    payload["unexpected"] = True

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RollbackPolicy.model_validate(payload)


def test_missing_migration_classification_fails_repository_validation(tmp_path: Path) -> None:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    payload["migrations"] = payload["migrations"][:-1]
    payload["current_migration_head"] = payload["migrations"][-1]["revision"]
    incomplete = RollbackPolicy.model_validate(payload)

    with pytest.raises(ValueError, match="migration policy does not match"):
        validate_policy_against_repository(incomplete, ROOT)


def test_duplicate_response_and_scenario_inventory_is_rejected() -> None:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    duplicated_response = copy.deepcopy(payload)
    duplicated_response["allowed_responses"].append(duplicated_response["allowed_responses"][0])
    with pytest.raises(ValidationError, match="allowed response inventory contains duplicates"):
        RollbackPolicy.model_validate(duplicated_response)

    duplicated_scenario = copy.deepcopy(payload)
    duplicated_scenario["scenarios"].append(duplicated_scenario["scenarios"][0])
    with pytest.raises(ValidationError, match="scenario inventory contains duplicates"):
        RollbackPolicy.model_validate(duplicated_scenario)


def test_non_linear_migration_chain_is_rejected(tmp_path: Path) -> None:
    migration_root = tmp_path / "backend/migrations/versions"
    shutil.copytree(ROOT / "backend/migrations/versions", migration_root)
    second = migration_root / "20260721_0002_idempotency_records.py"
    second.write_text(
        second.read_text(encoding="utf-8").replace(
            'down_revision: str | None = "20260719_0001"',
            "down_revision: str | None = None",
        ),
        encoding="utf-8",
    )
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    payload["migrations"][1]["down_revision"] = None
    non_linear = RollbackPolicy.model_validate(payload)

    with pytest.raises(ValueError, match="migration chain is not linear"):
        validate_policy_against_repository(non_linear, tmp_path)


def test_receipt_rejects_unknown_fields() -> None:
    receipt = build_receipt(policy(), context_for("release_stopped_before_migration"))
    payload = receipt.model_dump(mode="json")
    payload["unexpected"] = True

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RollbackReceipt.model_validate(payload)


@pytest.mark.parametrize(
    "sensitive_value",
    [
        "password=do-not-retain",
        "Bearer abcdefghijklmnop",
        "dependency at 192.0.2.10",
    ],
)
def test_receipt_sensitive_content_is_rejected(sensitive_value: str) -> None:
    receipt = build_receipt(policy(), context_for("release_stopped_before_migration"))
    payload = receipt.model_dump(mode="json")
    payload["limitations"] = [sensitive_value]
    unsafe = RollbackReceipt.model_validate(payload)

    with pytest.raises(ValueError, match="prohibited sensitive content"):
        assert_sanitized_receipt(unsafe)


def test_receipt_write_is_atomic_and_owner_only(tmp_path: Path) -> None:
    receipt = build_receipt(policy(), context_for("release_stopped_before_migration"))
    output = tmp_path / "receipt.json"

    write_receipt(output, receipt)

    assert RollbackReceipt.model_validate_json(output.read_text(encoding="utf-8")) == receipt
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    assert not output.with_suffix(".json.tmp").exists()


def test_cli_writes_a_sanitized_rehearsal_receipt(tmp_path: Path) -> None:
    output = tmp_path / "rollback-rehearsal.json"
    source, previous = git_revisions()

    result = main(
        [
            "--policy",
            str(POLICY_PATH),
            "--output",
            str(output),
            "--source-revision",
            source,
            "--previous-known-good-revision",
            previous,
            "--authority-granted",
            "--protected-controls-preserved",
        ]
    )

    receipt = RollbackReceipt.model_validate_json(output.read_text(encoding="utf-8"))
    assert result == 0
    assert receipt.decision == "PASS"
    assert receipt.selected_response == RollbackResponse.ROLL_BACK_APPLICATION_ARTIFACT
    assert receipt.cleanup.restore_target_state == "NOT_CREATED"


def test_cli_failure_writes_only_a_sanitized_failure_class(tmp_path: Path) -> None:
    output = tmp_path / "rollback-rehearsal.json"
    source, previous = git_revisions()

    result = main(
        [
            "--policy",
            str(POLICY_PATH),
            "--output",
            str(output),
            "--source-revision",
            source,
            "--previous-known-good-revision",
            previous,
            "--scenario-id",
            "unknown_scenario",
            "--requested-operation",
            "password=must-never-appear",
            "--authority-granted",
            "--protected-controls-preserved",
        ]
    )

    receipt = RollbackFailureReceipt.model_validate_json(output.read_text(encoding="utf-8"))
    serialized = output.read_text(encoding="utf-8")
    assert result == 1
    assert receipt.failure_class == "POLICY_OR_CONTEXT_VALIDATION_FAILED"
    assert receipt.selected_response == RollbackResponse.REFUSE_UNSAFE_ROLLBACK
    assert "must-never-appear" not in serialized
    assert stat.S_IMODE(output.stat().st_mode) == 0o600


def test_catalog_tampering_changes_no_live_policy_file() -> None:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    mutated = copy.deepcopy(payload)
    mutated["scenarios"][0]["expected_response"] = "CONTAIN_AND_ESCALATE"

    with pytest.raises(ValidationError, match="scenario inventory"):
        RollbackPolicy.model_validate(mutated)
