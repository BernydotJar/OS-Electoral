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
VALIDATOR_PATH = ROOT / "scripts" / "release" / "validate_controlled_use_readiness.py"
RECORD_PATH = ROOT / "program" / "controlled-use-readiness.json"
MANIFEST_PATH = ROOT / "architecture" / "program-state.json"


def load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("campaignos_test_controlled_use", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load controlled-use validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def record() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(RECORD_PATH.read_text(encoding="utf-8")))


def manifest() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(MANIFEST_PATH.read_text(encoding="utf-8")))


def test_current_controlled_use_record_passes() -> None:
    validator = load_validator()
    validator.validate_record(record(), manifest())


def test_controlled_use_cannot_claim_production_ready() -> None:
    validator = load_validator()
    payload = copy.deepcopy(record())
    payload["production_status"] = "READY"
    with pytest.raises(AssertionError, match="cannot claim production READY"):
        validator.validate_record(payload, manifest())


def test_controlled_use_requires_complete_gate_inventory() -> None:
    validator = load_validator()
    payload = copy.deepcopy(record())
    payload["gates"] = payload["gates"][:-1]
    with pytest.raises(AssertionError, match="gate inventory mismatch"):
        validator.validate_record(payload, manifest())


def test_controlled_use_rejects_public_development_identity() -> None:
    validator = load_validator()
    payload = copy.deepcopy(record())
    payload["identity_boundary"]["public_exposure_allowed"] = True
    with pytest.raises(AssertionError, match="cannot be public"):
        validator.validate_record(payload, manifest())


def test_controlled_use_cannot_invent_firmes_approval() -> None:
    validator = load_validator()
    payload = copy.deepcopy(record())
    payload["human_gates"]["firmes_integration_approval"] = {
        "recorded": True,
        "receipt": "invented",
    }
    with pytest.raises(AssertionError, match="cannot invent FIRMES approval"):
        validator.validate_record(payload, manifest())


def test_controlled_use_must_bind_to_canonical_main() -> None:
    validator = load_validator()
    payload = copy.deepcopy(record())
    payload["base_main_sha"] = "0" * 40
    with pytest.raises(AssertionError, match="not bound to the canonical main baseline"):
        validator.validate_record(payload, manifest())
