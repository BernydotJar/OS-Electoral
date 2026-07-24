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
VALIDATOR_PATH = ROOT / "scripts" / "release" / "validate_release_readiness.py"
RECORD_PATH = ROOT / "program" / "release-readiness.json"


def load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "campaignos_test_release_readiness",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load release readiness validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def record() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(RECORD_PATH.read_text(encoding="utf-8")))


def test_current_release_record_denies_release() -> None:
    validator = load_validator()
    validator.validate_record(record())


def test_release_record_cannot_claim_ready() -> None:
    validator = load_validator()
    payload = copy.deepcopy(record())
    payload["production_status"] = "READY"
    with pytest.raises(AssertionError, match="must remain BLOCKED"):
        validator.validate_record(payload)


def test_release_record_requires_complete_gate_inventory() -> None:
    validator = load_validator()
    payload = copy.deepcopy(record())
    payload["gates"] = payload["gates"][:-1]
    with pytest.raises(AssertionError, match="release gate inventory mismatch"):
        validator.validate_record(payload)


def test_release_record_cannot_invent_human_approval() -> None:
    validator = load_validator()
    payload = copy.deepcopy(record())
    payload["required_human_approval"] = {"recorded": True, "receipt": "invented"}
    with pytest.raises(AssertionError, match="must remain absent"):
        validator.validate_record(payload)


def test_release_record_rejects_unverified_superseding_run() -> None:
    validator = load_validator()
    payload = copy.deepcopy(record())
    payload["historical_validation"]["superseding_visual_run"] = 30128291969
    with pytest.raises(AssertionError, match="superseding visual run drift"):
        validator.validate_record(payload)
