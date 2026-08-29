#!/usr/bin/env python3
"""Validate CampaignOS controlled internal-use readiness without granting production authority."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / "program" / "controlled-use-readiness.json"
MANIFEST = ROOT / "architecture" / "program-state.json"
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
REQUIRED_GATES = {
    "current-main-reconciled",
    "backend-quality",
    "frontend-quality",
    "independent-browser-review",
    "postgresql-api-browser-journey",
    "exact-authorization",
    "operator-documentation-current",
    "development-identity-contained",
    "firmes-boundary",
    "production-separation",
    "external-effects-none",
}
REQUIRED_PROHIBITIONS = {
    "PUBLIC_EXPOSURE_WITH_DEVELOPMENT_IDENTITY",
    "PRODUCTION_DEPLOYMENT",
    "FIRMES_SYNC_WITHOUT_APPROVAL",
    "CITIZEN_CONTACT",
    "INDIVIDUAL_TARGETING_OR_PROFILING",
    "PERSUASION_AUTOMATION",
    "PUBLICATION",
    "SPENDING",
    "MOBILIZATION",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing controlled-use artifact: {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected object: {path.relative_to(ROOT)}")
    return value


def validate_record(record: dict[str, Any], manifest: dict[str, Any] | None = None) -> None:
    manifest = manifest or load_json(MANIFEST)
    require(record["schema_version"] == "1.0", "unsupported controlled-use schema")
    require(record["increment"] == "C3-RELEASE-002", "controlled-use increment drift")
    date.fromisoformat(record["assessed_at"])
    require(bool(SHA_PATTERN.fullmatch(record["base_main_sha"])), "invalid controlled-use base SHA")
    require(
        record["base_main_sha"] == manifest["github_state"]["cumulative_merge"]["main_sha"],
        "controlled-use assessment is not bound to the canonical main baseline",
    )
    require(
        record["decision"] == "READY_FOR_CONTROLLED_INTERNAL_USE",
        "controlled-use decision must remain READY_FOR_CONTROLLED_INTERNAL_USE",
    )
    require(
        record["production_status"] == "BLOCKED", "controlled use cannot claim production READY"
    )
    require(
        record["production_release_decision"] == "DENY_RELEASE",
        "controlled use cannot authorize production release",
    )
    require(record["external_effects"] == "NONE", "controlled use cannot create external effects")

    gates = record["gates"]
    ids = [gate["id"] for gate in gates]
    require(
        set(ids) == REQUIRED_GATES and len(ids) == len(set(ids)),
        "controlled-use gate inventory mismatch",
    )
    for gate in gates:
        require(gate["status"] == "PASS", f"controlled-use gate is not PASS: {gate['id']}")
        require(bool(gate["reason"].strip()), f"controlled-use gate lacks reason: {gate['id']}")
        for evidence in gate["evidence"]:
            require(
                (ROOT / evidence).is_file(),
                f"missing controlled-use evidence: {gate['id']}: {evidence}",
            )

    identity = record["identity_boundary"]
    require(
        identity["mode"] == "DEVELOPMENT_ONLY_LOCAL_OR_ISOLATED",
        "development identity boundary drift",
    )
    require(identity["public_exposure_allowed"] is False, "development identity cannot be public")
    require(
        identity["production_allowed"] is False, "development identity cannot be production auth"
    )
    require(
        identity["live_oidc_ready"] is False,
        "controlled-use record cannot invent live OIDC readiness",
    )

    prohibitions = record["prohibited_uses"]
    require(
        REQUIRED_PROHIBITIONS <= set(prohibitions),
        "controlled-use prohibited-use boundary is incomplete",
    )
    require(record["allowed_uses"], "controlled-use record requires explicit allowed uses")
    require(record["production_blockers"], "controlled-use record requires production blockers")

    human_gates = record["human_gates"]
    require(
        human_gates["production_approval"] == {"recorded": False, "receipt": None},
        "controlled use cannot invent production approval",
    )
    require(
        human_gates["firmes_integration_approval"] == {"recorded": False, "receipt": None},
        "controlled use cannot invent FIRMES approval",
    )


def main() -> int:
    record = load_json(RECORD)
    validate_record(record)
    print(
        "[OK] CampaignOS controlled-use readiness validated; "
        f"decision={record['decision']}; production={record['production_status']}; "
        f"gates={len(record['gates'])}; external_effects={record['external_effects']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
