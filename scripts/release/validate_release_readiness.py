#!/usr/bin/env python3
"""Validate the fail-closed CampaignOS release-readiness record."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / "program" / "release-readiness.json"
ALLOWED_GATE_STATUSES = {"BLOCKED", "NOT_IMPLEMENTED", "NOT_VERIFIED", "PARTIAL", "PASS"}
REQUIRED_GATES = {
    "open-critical-high-findings",
    "staging-environment",
    "managed-backup-pitr",
    "telemetry-alert-routing",
    "rpo-rto-exercise",
    "load-and-rollback",
    "independent-security-privacy-legal-review",
    "human-production-approval",
}
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
EXPECTED_SUPERSEDING_RUN = 29660653755
EXPECTED_SUPERSEDING_HEAD = "30e2473f6eac2a554bc7e51b18f7b25746e42475"
EXPECTED_SUPERSEDED_RUNS = {
    29659355550,
    29659451027,
    29659542083,
    29659623156,
    29659692005,
    29659733648,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_record(path: Path = RECORD) -> dict[str, Any]:
    require(path.is_file(), f"missing release record: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "release record must be an object")
    return value


def validate_record(record: dict[str, Any]) -> None:
    require(record["schema_version"] == "1.0", "unsupported release schema")
    require(record["increment"] == "C3-RELEASE-001", "release increment drift")
    date.fromisoformat(record["assessed_at"])
    require(record["production_status"] == "BLOCKED", "production status must remain BLOCKED")
    require(
        record["release_decision"] == "DENY_RELEASE",
        "release decision must remain DENY_RELEASE",
    )
    require(record["external_effects"] == "NONE", "release audit cannot create external effects")

    historical = record["historical_validation"]
    require(historical["unresolved_failed_runs"] == [], "historical failures remain unresolved")
    require(
        historical["superseding_visual_run"] == EXPECTED_SUPERSEDING_RUN,
        "superseding visual run drift",
    )
    require(
        historical["superseding_head"] == EXPECTED_SUPERSEDING_HEAD,
        "superseding head drift",
    )
    superseded = historical["superseded_run_ids"]
    require(
        set(superseded) == EXPECTED_SUPERSEDED_RUNS,
        "historical supersession inventory mismatch",
    )
    require(len(superseded) == len(set(superseded)), "duplicate historical supersession run")

    gates = record["gates"]
    ids = [gate["id"] for gate in gates]
    require(
        set(ids) == REQUIRED_GATES and len(ids) == len(set(ids)),
        "release gate inventory mismatch",
    )
    for gate in gates:
        require(
            gate["status"] in ALLOWED_GATE_STATUSES,
            f"invalid release gate status: {gate['id']}",
        )
        require(bool(gate["reason"].strip()), f"release gate lacks reason: {gate['id']}")
        for evidence in gate["evidence"]:
            require(
                (ROOT / evidence).is_file(),
                f"missing release gate evidence: {gate['id']}: {evidence}",
            )
    require(
        any(gate["status"] != "PASS" for gate in gates),
        "release cannot be denied with every gate PASS",
    )

    approval = record["required_human_approval"]
    require(
        approval == {"recorded": False, "receipt": None},
        "human production approval must remain absent",
    )
    require(record["next_safe_actions"], "release record requires next safe actions")


def main() -> int:
    record = load_record()
    validate_record(record)
    print(
        "[OK] CampaignOS release readiness validated; "
        f"decision={record['release_decision']}; production={record['production_status']}; "
        f"gates={len(record['gates'])}; unresolved_historical=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
