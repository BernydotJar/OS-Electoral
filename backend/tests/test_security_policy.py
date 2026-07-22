from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from scripts.security.verify_security_policy import load_policy, verify

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "docs/security/data-policy.json"


def policy() -> dict[str, Any]:
    return copy.deepcopy(load_policy(POLICY_PATH))


def failed_errors(value: dict[str, Any]) -> list[str]:
    report = verify(ROOT, value)
    assert report["result"] == "FAIL"
    errors = report["errors"]
    assert isinstance(errors, list)
    return [str(item) for item in errors]


def record(value: dict[str, Any], record_id: str) -> dict[str, Any]:
    records = value["record_types"]
    assert isinstance(records, list)
    item = next(
        candidate
        for candidate in records
        if isinstance(candidate, dict) and candidate.get("id") == record_id
    )
    return item


def test_current_security_policy_passes() -> None:
    report = verify(ROOT)
    assert report["result"] == "PASS", report["errors"]
    assert report["record_types"] == 12
    assert report["append_only_tables"] == 6
    assert report["production_status"] == "BLOCKED"


def test_missing_required_record_fails_closed() -> None:
    value = policy()
    records = value["record_types"]
    assert isinstance(records, list)
    value["record_types"] = [
        item for item in records if isinstance(item, dict) and item.get("id") != "audit_evidence"
    ]
    assert any("record type definitions" in item for item in failed_errors(value))


def test_removed_political_data_prohibition_fails_closed() -> None:
    value = policy()
    fields = value["prohibited_fields"]
    assert isinstance(fields, list)
    fields.remove("PERSUADABILITY_SCORE")
    assert any("prohibition" in item for item in failed_errors(value))


def test_unknown_classification_fails_closed() -> None:
    value = policy()
    record(value, "candidate_evidence")["classification"] = "SENSITIVE_MAYBE"
    assert any("unknown classification" in item for item in failed_errors(value))


def test_record_cannot_claim_production_ready() -> None:
    value = policy()
    record(value, "campaign_workspace")["production_ready"] = True
    assert any("production_ready" in item for item in failed_errors(value))


def test_live_ai_processor_cannot_be_enabled() -> None:
    value = policy()
    processors = value["live_processors"]
    assert isinstance(processors, dict)
    processors["ai_provider"] = "ENABLED"
    assert any("live processors" in item for item in failed_errors(value))


def test_secret_storage_must_remain_prohibited() -> None:
    value = policy()
    secret = record(value, "secret_or_token")
    secret["classification"] = "RESTRICTED"
    secret["retention_posture"] = "SECURITY_EVIDENCE_REVIEW_REQUIRED"
    assert any("storage must remain prohibited" in item for item in failed_errors(value))
