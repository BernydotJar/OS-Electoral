#!/usr/bin/env python3
"""Fail-closed validation for the CampaignOS required-eval catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "program" / "eval-catalog.json"

REQUIRED_EVALS = {
    "EVAL-TENANT-001",
    "EVAL-AUTHZ-001",
    "EVAL-BOLA-001",
    "EVAL-SESSION-001",
    "EVAL-INVITATION-001",
    "EVAL-AUDIT-001",
    "EVAL-OUTBOX-001",
    "EVAL-REPLAY-001",
    "EVAL-PROMPT-INJECTION-001",
    "EVAL-ONBOARDING-001",
    "EVAL-CANDIDATE-001",
    "EVAL-TEAM-001",
    "EVAL-ROADMAP-001",
    "EVAL-WARROOM-001",
    "EVAL-TRAINING-001",
    "EVAL-I18N-001",
    "EVAL-NONTECH-001",
    "EVAL-OBJECTIVE-001",
    "EVAL-METHOD-001",
    "EVAL-BIOPOLITICS-001",
    "EVAL-NEUROMARKETING-001",
    "EVAL-CONTACT-001",
    "EVAL-TROLL-CENTER-001",
    "EVAL-PARTICIPATION-001",
    "EVAL-CAMPAIGN-GOVERNMENT-FIREWALL-001",
    "EVAL-TEAM-WELLBEING-001",
    "EVAL-BRAND-COHERENCE-001",
    "EVAL-OPPOSITION-RESEARCH-001",
    "EVAL-RECOVERY-001",
    "EVAL-ACCESSIBILITY-001",
    "EVAL-LOAD-001",
    "EVAL-ROLLBACK-001",
    "EVAL-OBSERVABILITY-001",
}
ALLOWED_STATUSES = {
    "NOT_IMPLEMENTED",
    "PARTIAL_TESTED_LOCAL",
    "TESTED_LOCAL",
    "VERIFIED_POSTGRESQL",
    "CI_GREEN",
    "REVIEWED",
}
ALLOWED_RESULTS = {"NOT_RUN", "PARTIAL", "PASS", "FAIL"}
EXPECTED_HARD_GATES = {
    "critical_failures_allowed": 0,
    "high_failures_allowed": 0,
    "required_tests_pass_rate": 100,
    "required_acceptance_criteria": 100,
    "cross_tenant_leaks_allowed": 0,
    "authorization_bypasses_allowed": 0,
    "approval_bypasses_allowed": 0,
    "external_effects_allowed": 0,
    "unsupported_evidence_claims_allowed": 0,
}


def fail(message: str) -> None:
    raise SystemExit(f"[FAIL] {message}")


def require_string(record: dict[str, Any], key: str, eval_id: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"{eval_id}: {key} must be a non-empty string")
    return value


def main() -> None:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0":
        fail("unsupported eval catalog schema_version")
    if payload.get("production_gate") != "BLOCKED":
        fail("production_gate must remain BLOCKED until every required eval passes review")
    if payload.get("hard_gates") != EXPECTED_HARD_GATES:
        fail("hard_gates do not match the fail-closed CampaignOS policy")

    records = payload.get("evals")
    if not isinstance(records, list):
        fail("evals must be a list")
    identifiers: list[str] = []
    result_counts = {result: 0 for result in ALLOWED_RESULTS}
    for raw_record in records:
        if not isinstance(raw_record, dict):
            fail("every eval record must be an object")
        eval_id = require_string(raw_record, "id", "unknown")
        identifiers.append(eval_id)
        status = require_string(raw_record, "status", eval_id)
        result = require_string(raw_record, "gate_result", eval_id)
        require_string(raw_record, "category", eval_id)
        require_string(raw_record, "limitations", eval_id)
        if status not in ALLOWED_STATUSES:
            fail(f"{eval_id}: unsupported status {status}")
        if result not in ALLOWED_RESULTS:
            fail(f"{eval_id}: unsupported gate_result {result}")
        result_counts[result] += 1

        evidence = raw_record.get("evidence")
        commands = raw_record.get("commands")
        if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
            fail(f"{eval_id}: evidence must be a string list")
        if not isinstance(commands, list) or not all(isinstance(item, str) for item in commands):
            fail(f"{eval_id}: commands must be a string list")
        if status == "NOT_IMPLEMENTED":
            has_verification_date = raw_record.get("last_verified_at") is not None
            if result != "NOT_RUN" or evidence or commands or has_verification_date:
                fail(f"{eval_id}: NOT_IMPLEMENTED must remain evidence-free and NOT_RUN")
        else:
            if not evidence or not commands or not raw_record.get("last_verified_at"):
                fail(f"{eval_id}: implemented statuses require evidence, commands and date")
            for relative in evidence:
                if not (ROOT / relative).exists():
                    fail(f"{eval_id}: missing evidence path {relative}")
            if status == "PARTIAL_TESTED_LOCAL" and result != "PARTIAL":
                fail(f"{eval_id}: partial status must have PARTIAL result")
            completed_statuses = {
                "TESTED_LOCAL",
                "VERIFIED_POSTGRESQL",
                "CI_GREEN",
                "REVIEWED",
            }
            if status in completed_statuses and result != "PASS":
                fail(f"{eval_id}: completed verification status must have PASS result")

    if len(identifiers) != len(set(identifiers)):
        fail("duplicate eval IDs are forbidden")
    observed = set(identifiers)
    if observed != REQUIRED_EVALS:
        missing = sorted(REQUIRED_EVALS - observed)
        extra = sorted(observed - REQUIRED_EVALS)
        fail(f"required eval inventory mismatch; missing={missing}; extra={extra}")
    if result_counts["FAIL"]:
        fail("the catalog contains a failing required eval")
    if result_counts["PASS"] == len(REQUIRED_EVALS):
        fail(
            "all evals pass but production_gate is still BLOCKED; "
            "require explicit reviewed transition"
        )

    print(
        "[OK] CampaignOS eval catalog validated; "
        f"required={len(REQUIRED_EVALS)}; pass={result_counts['PASS']}; "
        f"partial={result_counts['PARTIAL']}; not_run={result_counts['NOT_RUN']}; "
        "production=BLOCKED"
    )


if __name__ == "__main__":
    main()
