#!/usr/bin/env python3
"""Fail-closed validation for C1-FRONT-002 Campaign Team Command Center."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
TEAM = WEB / "data" / "team.json"

REQUIRED_FILES = [
    WEB / "index.html",
    WEB / "styles.css",
    WEB / "app.js",
    WEB / "README.md",
    WEB / "data" / "status.json",
    TEAM,
]

EXPECTED_DEPARTMENTS = {
    "research-evidence": "ACTIVE",
    "strategy-war-room": "RESEARCH_ONLY",
    "brand-reputation": "SETUP_REQUIRED",
    "policy-government": "RESEARCH_ONLY",
    "communications-media": "LOCKED",
    "legal-compliance": "ACTIVE",
    "finance-administration": "SETUP_REQUIRED",
    "operations-team": "SETUP_REQUIRED",
    "security-protection": "SETUP_REQUIRED",
    "performance-learning": "ACTIVE",
}

ALLOWED_STATUSES = {"ACTIVE", "RESEARCH_ONLY", "SETUP_REQUIRED", "LOCKED", "BLOCKED"}
REQUIRED_FIELDS = {
    "id", "name", "shortName", "mission", "status", "skills", "evidenceInputs",
    "blockers", "approvalOwner", "autonomy", "lastReviewed",
}
REQUIRED_GATES = {
    "Priority segment selection",
    "Territorial ranking",
    "Public narrative",
    "Paid-media activation",
    "Targeting and persuasion scoring",
    "Field mobilization",
    "Automatic publishing",
    "Public promises or attacks",
    "Individual voter inference",
}
FORBIDDEN_TOKENS = {
    "/Users/",
    ".gemini/config/skills",
    "voter_name",
    "voter_id",
    "support_probability",
    "persuasion_score",
    "segment_score",
    "sensitive_trait",
}
REQUIRED_UI_HOOKS = {
    'id="teamModule"',
    'id="evidenceModule"',
    'id="teamGrid"',
    'id="agentDrawer"',
    'role="dialog"',
    'aria-modal="true"',
    'id="drawerClose"',
    'data-module="team"',
    'data-module="evidence"',
}
REQUIRED_JS_BEHAVIORS = {
    "openDepartment",
    "closeDrawer",
    "trapDrawerFocus",
    "prefers-reduced-motion",
    "document.startViewTransition",
    "escapeHtml",
}


def fail(message: str) -> None:
    raise SystemExit(f"[FAILED] {message}")


def main() -> None:
    for path in REQUIRED_FILES:
        if not path.is_file():
            fail(f"required file missing: {path.relative_to(ROOT)}")

    data = json.loads(TEAM.read_text(encoding="utf-8"))
    if data.get("mode") != "READ_ONLY":
        fail("team snapshot must remain READ_ONLY")
    if data.get("candidate", {}).get("authority") != "FINAL_HUMAN_DECISION_OWNER":
        fail("candidate must remain final human decision owner")
    if data.get("chiefOfStaff", {}).get("authority") != "COORDINATION_ONLY":
        fail("AI Chief of Staff authority must remain COORDINATION_ONLY")

    departments = data.get("departments")
    if not isinstance(departments, list) or len(departments) != 10:
        fail("exactly ten departments are required")

    seen: dict[str, str] = {}
    for department in departments:
        missing = REQUIRED_FIELDS - set(department)
        if missing:
            fail(f"department missing fields: {sorted(missing)}")
        department_id = department["id"]
        if department_id in seen:
            fail(f"duplicate department id: {department_id}")
        status = department["status"]
        if status not in ALLOWED_STATUSES:
            fail(f"unsupported status for {department_id}: {status}")
        if not department["skills"] or not department["evidenceInputs"] or not department["blockers"]:
            fail(f"department {department_id} must expose skills, evidence inputs and blockers")
        seen[department_id] = status

    if seen != EXPECTED_DEPARTMENTS:
        fail(f"department/state mapping drifted: {seen}")

    if set(data.get("closedGates", [])) != REQUIRED_GATES:
        fail("closed political gate set mismatch")

    combined = "\n".join(path.read_text(encoding="utf-8", errors="strict") for path in REQUIRED_FILES)
    for token in FORBIDDEN_TOKENS:
        if token in combined:
            fail(f"forbidden token found: {token}")

    html = (WEB / "index.html").read_text(encoding="utf-8")
    missing_hooks = REQUIRED_UI_HOOKS - {hook for hook in REQUIRED_UI_HOOKS if hook in html}
    if missing_hooks:
        fail(f"required UI hooks missing: {sorted(missing_hooks)}")

    js = (WEB / "app.js").read_text(encoding="utf-8")
    missing_behaviors = REQUIRED_JS_BEHAVIORS - {item for item in REQUIRED_JS_BEHAVIORS if item in js}
    if missing_behaviors:
        fail(f"required JS behaviors missing: {sorted(missing_behaviors)}")

    css = (WEB / "styles.css").read_text(encoding="utf-8")
    for required in ("@media (prefers-reduced-motion: reduce)", ".team-grid", ".drawer", ":focus-visible"):
        if required not in css:
            fail(f"required CSS behavior missing: {required}")

    print("[OK] ten governed departments and states validated")
    print("[OK] candidate is final human authority; AI is coordination only")
    print("[OK] political gates remain closed")
    print("[OK] team/evidence modules and accessible drawer hooks present")
    print("[OK] reduced motion and progressive view transition hooks present")
    print("[OK] no personal paths, voter scoring fields or global-skill runtime dependency")


if __name__ == "__main__":
    main()
