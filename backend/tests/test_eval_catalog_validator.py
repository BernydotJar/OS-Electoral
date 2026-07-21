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
VALIDATOR_PATH = ROOT / "scripts" / "architecture" / "validate_eval_catalog.py"
CATALOG_PATH = ROOT / "program" / "eval-catalog.json"


def load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "campaignos_test_eval_catalog_validator",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the eval catalog validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def catalog() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(CATALOG_PATH.read_text(encoding="utf-8")),
    )


def run_with_catalog(
    validator: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, Any],
) -> None:
    candidate = tmp_path / "eval-catalog.json"
    candidate.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(validator, "CATALOG_PATH", candidate)
    validator.main()


def test_current_required_eval_catalog_passes(capsys: pytest.CaptureFixture[str]) -> None:
    validator = load_validator()

    validator.main()

    output = capsys.readouterr().out
    assert "required=33" in output
    assert "pass=5" in output
    assert "partial=8" in output
    assert "not_run=20" in output
    assert "production=BLOCKED" in output


def test_missing_required_eval_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator = load_validator()
    payload = catalog()
    payload["evals"] = payload["evals"][:-1]

    with pytest.raises(SystemExit, match="required eval inventory mismatch"):
        run_with_catalog(validator, tmp_path, monkeypatch, payload)


def test_not_implemented_eval_cannot_claim_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator = load_validator()
    payload = copy.deepcopy(catalog())
    invitation = next(item for item in payload["evals"] if item["id"] == "EVAL-INVITATION-001")
    invitation["evidence"] = ["backend/tests/test_authorization.py"]

    with pytest.raises(SystemExit, match="must remain evidence-free and NOT_RUN"):
        run_with_catalog(validator, tmp_path, monkeypatch, payload)


def test_production_gate_cannot_be_elevated_by_catalog_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator = load_validator()
    payload = catalog()
    payload["production_gate"] = "READY"

    with pytest.raises(SystemExit, match="production_gate must remain BLOCKED"):
        run_with_catalog(validator, tmp_path, monkeypatch, payload)
