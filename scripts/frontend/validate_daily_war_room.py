#!/usr/bin/env python3
"""Fail-closed validation for C1-FRONT-003 Daily War Room."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
SNAPSHOT = WEB / "data" / "war-room.json"

REQUIRED_FILES = [
    WEB / "index.html",
    WEB / "war-room.css",
    WEB / "war-room.js",
    SNAPSHOT,
]

ALLOWED_EVIDENCE_CLASSES = {
    "OFFICIAL",
    "CAMPAIGN_RESEARCH",
    "PERCEPTION",
    "HYPOTHESIS",
    "UNKNOWN",
}

ALLOWED_SIGNAL_STATES = {
    "NEW",
    "ASSESSING",
    "BLOCKED",
    "READY_FOR_HUMAN_REVIEW",
    "CLOSED",
}

REQUIRED_SIGNAL_FIELDS = {
    "id",
    "title",
    "summary",
    "evidenceClass",
    "source",
    "confidence",
    "status",
    "assessment",
    "decisionRequired",
    "owner",
    "dueDate",
    "gate",
    "blockers",
    "options",
    "approvalStatus",
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
    "voter_name",
    "voter_id",
    "support_probability",
    "persuasion_score",
    "segment_score",
    "sensitive_trait",
    "AUTO_PUBLISH",
    "AUTO_CONTACT",
    "AUTO_SPEND",
}

REQUIRED_HTML_HOOKS = {
    'data-module="war-room"',
    'data-view="war-room"',
    'id="warRoomModule"',
    'id="warSignalList"',
    'id="warDetailDialog"',
    'id="warDetailClose"',
    'aria-labelledby="warDetailTitle"',
}

REQUIRED_JS_BEHAVIORS = {
    "renderSignals",
    "openSignal",
    "closeSignal",
    "trapFocus",
    "war-room.json",
    "escapeHtml",
}


def fail(message: str) -> None:
    raise SystemExit(f"[FAILED] {message}")


def main() -> None:
    for path in REQUIRED_FILES:
        if not path.is_file():
            fail(f"required file missing: {path.relative_to(ROOT)}")

    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    required_root = {
        "version",
        "snapshotDate",
        "mode",
        "title",
        "summary",
        "pipeline",
        "signals",
        "decisions",
        "assignments",
        "risks",
        "learning",
        "closedGates",
        "safetyStatement",
    }
    missing_root = required_root - set(data)
    if missing_root:
        fail(f"snapshot missing keys: {sorted(missing_root)}")

    if data.get("mode") != "READ_ONLY":
        fail("Daily War Room must remain READ_ONLY")

    expected_pipeline = [
        "Signals",
        "Evidence",
        "Assessment",
        "Options",
        "Human Approval",
        "Assignment",
        "Follow-up",
        "Learning",
    ]
    if data.get("pipeline") != expected_pipeline:
        fail("decision pipeline changed unexpectedly")

    signals = data.get("signals")
    if not isinstance(signals, list) or not signals:
        fail("at least one signal is required")

    seen_ids: set[str] = set()
    for signal in signals:
        missing = REQUIRED_SIGNAL_FIELDS - set(signal)
        if missing:
            fail(f"signal missing fields: {sorted(missing)}")
        signal_id = signal["id"]
        if signal_id in seen_ids:
            fail(f"duplicate signal id: {signal_id}")
        seen_ids.add(signal_id)
        if signal["evidenceClass"] not in ALLOWED_EVIDENCE_CLASSES:
            fail(f"unsupported evidence class for {signal_id}")
        if signal["status"] not in ALLOWED_SIGNAL_STATES:
            fail(f"unsupported signal status for {signal_id}")
        if not signal["source"] or not signal["blockers"] or not signal["options"]:
            fail(f"signal {signal_id} must expose provenance, blockers and options")
        if signal["approvalStatus"] not in {"PENDING_HUMAN_APPROVAL", "BLOCKED"}:
            fail(f"signal {signal_id} bypasses human approval")

    for decision in data.get("decisions", []):
        if decision.get("status") not in {"PENDING_HUMAN_APPROVAL", "BLOCKED"}:
            fail(f"decision {decision.get('id')} is not human-gated")

    for assignment in data.get("assignments", []):
        boundary = assignment.get("executionBoundary", "")
        if boundary not in {"INTERNAL_RESEARCH_ONLY", "DRAFT_ONLY", "INTERNAL_ONLY"}:
            fail(f"assignment {assignment.get('id')} has unsafe execution boundary")

    if set(data.get("closedGates", [])) != REQUIRED_GATES:
        fail("closed gate set mismatch")

    combined = "\n".join(path.read_text(encoding="utf-8", errors="strict") for path in REQUIRED_FILES)
    for token in FORBIDDEN_TOKENS:
        if token in combined:
            fail(f"forbidden token found: {token}")

    html = (WEB / "index.html").read_text(encoding="utf-8")
    missing_hooks = {hook for hook in REQUIRED_HTML_HOOKS if hook not in html}
    if missing_hooks:
        fail(f"required HTML hooks missing: {sorted(missing_hooks)}")

    js = (WEB / "war-room.js").read_text(encoding="utf-8")
    missing_behaviors = {item for item in REQUIRED_JS_BEHAVIORS if item not in js}
    if missing_behaviors:
        fail(f"required JS behaviors missing: {sorted(missing_behaviors)}")

    css = (WEB / "war-room.css").read_text(encoding="utf-8")
    for required in (".war-pipeline", ".war-signal-list", "@media (prefers-reduced-motion: reduce)"):
        if required not in css:
            fail(f"required CSS behavior missing: {required}")

    print("[OK] Daily War Room snapshot schema validated")
    print("[OK] signal provenance and evidence classes validated")
    print("[OK] sensitive decisions remain human-gated")
    print("[OK] assignments remain internal and non-executing")
    print("[OK] political gates remain closed")
    print("[OK] no voter scoring, personal paths or outbound execution fields")


if __name__ == "__main__":
    main()
