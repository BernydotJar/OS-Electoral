from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "scripts" / "architecture" / "validate_program_state.py"
MANIFEST_PATH = ROOT / "architecture" / "program-state.json"
GRAPH_HARNESS_PATH = ROOT / "program" / "graph-harness-execution.json"


def load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "campaignos_test_program_state_validator",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load program state validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def manifest() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(MANIFEST_PATH.read_text(encoding="utf-8")))


def failed_stack_item(payload: dict[str, Any]) -> dict[str, Any]:
    return next(item for item in payload["stack"] if item["validation"]["conclusion"] == "FAILURE")


def test_current_manifest_passes_with_explicit_supersession() -> None:
    validator = load_validator()
    payload = manifest()

    superseded = validator.validate_superseded_runs(payload)
    integrations = validator.validate_integration_runs(payload)
    unresolved = validator.validate_stack(payload, superseded, integrations)

    assert unresolved == set()
    assert len(superseded) >= 10


def test_superseded_stack_failure_requires_matching_record() -> None:
    validator = load_validator()
    payload = copy.deepcopy(manifest())
    item = failed_stack_item(payload)
    run_id = item["validation"]["run_id"]
    payload["superseded_validation_runs"] = [
        record for record in payload["superseded_validation_runs"] if record["run_id"] != run_id
    ]

    superseded = validator.validate_superseded_runs(payload)
    integrations = validator.validate_integration_runs(payload)
    with pytest.raises(AssertionError, match="missing supersession record"):
        validator.validate_stack(payload, superseded, integrations)


def test_superseded_stack_failure_cannot_remain_blocking() -> None:
    validator = load_validator()
    payload = copy.deepcopy(manifest())
    item = failed_stack_item(payload)
    item["validation"]["blocking_for_production"] = True

    superseded = validator.validate_superseded_runs(payload)
    integrations = validator.validate_integration_runs(payload)
    with pytest.raises(AssertionError, match="superseded failure cannot block production"):
        validator.validate_stack(payload, superseded, integrations)


def test_supersession_record_requires_distinct_successor_run() -> None:
    validator = load_validator()
    payload = copy.deepcopy(manifest())
    record = payload["superseded_validation_runs"][0]
    record["superseded_by"] = record["run_id"]

    with pytest.raises(AssertionError, match="must reference a distinct successor"):
        validator.validate_superseded_runs(payload)


def test_superseded_stack_failure_requires_successful_integration_run() -> None:
    validator = load_validator()
    payload = copy.deepcopy(manifest())
    item = failed_stack_item(payload)
    run_id = item["validation"]["run_id"]
    record = next(
        record for record in payload["superseded_validation_runs"] if record["run_id"] == run_id
    )
    item["validation"]["superseded_by"] = 99999999999
    record["superseded_by"] = 99999999999

    superseded = validator.validate_superseded_runs(payload)
    integrations = validator.validate_integration_runs(payload)
    with pytest.raises(AssertionError, match="lacks integration evidence"):
        validator.validate_stack(payload, superseded, integrations)


def test_program_accepts_verified_delivery_closure() -> None:
    validator = load_validator()
    payload = manifest()

    roadmap = validator.validate_workstreams_and_roadmap(payload)

    assert roadmap["C3-RELEASE-001"]["status"] == "MERGED_TO_MAIN"
    assert roadmap["C3-OPS-002"]["status"] == "MERGED_TO_MAIN"
    assert roadmap["action:production-deployment"]["status"] == "HUMAN_BLOCKED"


def test_program_rejects_incomplete_delivery_without_active_increment() -> None:
    validator = load_validator()
    payload = copy.deepcopy(manifest())
    release = next(item for item in payload["roadmap"] if item["id"] == "C3-RELEASE-001")
    release["status"] = "IMPLEMENTED_LOCAL"
    for item in payload["roadmap"]:
        if item["status"] in {"ACTIVE", "EXECUTABLE_NEXT", "REVIEWED"}:
            item["status"] = "TESTED_LOCAL"

    with pytest.raises(AssertionError, match="fully verified delivery closure"):
        validator.validate_workstreams_and_roadmap(payload)


def test_fallback_ledger_rejects_stale_merge_blocker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator = load_validator()
    payload = manifest()
    roadmap = validator.validate_workstreams_and_roadmap(payload)
    task_ledger = json.loads(validator.TASK_LEDGER.read_text(encoding="utf-8"))
    merged_entry = next(
        entry for entry in task_ledger["entries"] if entry["status"] == "MERGED_TO_MAIN"
    )
    merged_entry.setdefault("blockers", []).append("Merge remains pending")
    original_load_json = validator.load_json

    def load_json(path: Path) -> dict[str, Any]:
        if path == validator.TASK_LEDGER:
            return task_ledger
        return original_load_json(path)

    monkeypatch.setattr(validator, "load_json", load_json)
    with pytest.raises(AssertionError, match="stale merge blocker"):
        validator.validate_fallback_records(payload, roadmap)


def test_graph_harness_projection_selects_pending_training_spec() -> None:
    validator = load_validator()
    payload = manifest()

    validator.validate_graph_harness_execution(payload)

    execution = json.loads(GRAPH_HARNESS_PATH.read_text(encoding="utf-8"))
    selected = execution["scheduler"]["selected_node"]
    assert execution["scheduler"]["active_feature"] is None
    assert execution["scheduler"]["ready_nodes"] == []
    assert selected["id"] == "C3-TRAINING-001"
    assert selected["state"] == "spec_ready"
    assert selected["human_approval"] == "PENDING"
    assert "approval_receipt" not in selected
    assert selected["id"] not in {item["id"] for item in payload["roadmap"]}
    assert selected["specs"] == [
        "specs/C3-TRAINING-001/requirements.md",
        "specs/C3-TRAINING-001/design.md",
        "specs/C3-TRAINING-001/tasks.md",
    ]


def test_graph_harness_projection_rejects_stale_canonical_runtime_state() -> None:
    validator = load_validator()
    payload = copy.deepcopy(manifest())
    payload["graph_harness_runtime"]["active_feature"] = "C1-PLAN-001"
    payload["graph_harness_runtime"]["selected_feature_state"] = "review"
    payload["graph_harness_runtime"]["approval_gate"] = "APPROVED"

    with pytest.raises(
        AssertionError,
        match="canonical manifest Graph Harness runtime state drift",
    ):
        validator.validate_graph_harness_execution(payload)


def test_graph_harness_projection_rejects_spec_ready_approval_bypass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator = load_validator()
    payload = manifest()
    execution = json.loads(GRAPH_HARNESS_PATH.read_text(encoding="utf-8"))
    execution["scheduler"]["selected_node"]["human_approval"] = "APPROVED"
    original_load_json = validator.load_json

    def load_json(path: Path) -> dict[str, Any]:
        if path == validator.GRAPH_HARNESS_EXECUTION:
            return execution
        return original_load_json(path)

    monkeypatch.setattr(validator, "load_json", load_json)
    with pytest.raises(AssertionError, match="spec-ready node bypassed human approval"):
        validator.validate_graph_harness_execution(payload)


def test_graph_harness_projection_rejects_pending_approval_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator = load_validator()
    payload = manifest()
    execution = json.loads(GRAPH_HARNESS_PATH.read_text(encoding="utf-8"))
    execution["scheduler"]["selected_node"]["approval_receipt"] = {
        "source": "USER_EXPLICIT_APPROVAL"
    }
    original_load_json = validator.load_json

    def load_json(path: Path) -> dict[str, Any]:
        if path == validator.GRAPH_HARNESS_EXECUTION:
            return execution
        return original_load_json(path)

    monkeypatch.setattr(validator, "load_json", load_json)
    with pytest.raises(AssertionError, match="pending node cannot contain an approval receipt"):
        validator.validate_graph_harness_execution(payload)


def test_graph_harness_projection_rejects_merge_gate_bypass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator = load_validator()
    payload = manifest()
    execution = json.loads(GRAPH_HARNESS_PATH.read_text(encoding="utf-8"))
    execution["localized_repair"]["delivery"]["merge_gate"] = "APPROVED"
    original_load_json = validator.load_json

    def load_json(path: Path) -> dict[str, Any]:
        if path == validator.GRAPH_HARNESS_EXECUTION:
            return execution
        return original_load_json(path)

    monkeypatch.setattr(validator, "load_json", load_json)
    with pytest.raises(AssertionError, match="lacks explicit merge authorization"):
        validator.validate_graph_harness_execution(payload)


def test_graph_harness_selected_spec_files_must_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator = load_validator()
    payload = manifest()
    execution = json.loads(GRAPH_HARNESS_PATH.read_text(encoding="utf-8"))
    execution["scheduler"]["selected_node"]["specs"][0] = "specs/missing.md"
    original_load_json = validator.load_json

    def load_json(path: Path) -> dict[str, Any]:
        if path == validator.GRAPH_HARNESS_EXECUTION:
            return execution
        return original_load_json(path)

    monkeypatch.setattr(validator, "load_json", load_json)
    with pytest.raises(AssertionError, match="missing Graph Harness feature spec"):
        validator.validate_graph_harness_execution(payload)
