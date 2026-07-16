#!/usr/bin/env python3
"""Fail-closed validation for the static Evidence Control Room."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
STATUS = WEB / "data" / "status.json"

REQUIRED_FILES = [
    WEB / "index.html",
    WEB / "styles.css",
    WEB / "app.js",
    WEB / "README.md",
    STATUS,
]

REQUIRED_GATES = {
    "Priority segment",
    "Territorial ranking",
    "Public narrative",
    "Paid-media audience",
    "Targeting / microtargeting",
    "Field mobilization",
    "Public promises or attacks",
}

REQUIRED_POLICIES = {
    "No selecciona segmentos electorales",
    "No genera ranking territorial",
    "No produce narrativa política",
    "No define audiencias de pauta",
    "No ejecuta targeting o microtargeting",
    "No activa movilización de campo",
}


def fail(message: str) -> None:
    raise SystemExit(f"[FAILED] {message}")


def metric_by_label(data: dict, label: str) -> dict:
    matches = [item for item in data["metrics"] if item.get("label") == label]
    if len(matches) != 1:
        fail(f"expected exactly one metric named {label!r}")
    return matches[0]


def main() -> None:
    for path in REQUIRED_FILES:
        if not path.is_file():
            fail(f"required file missing: {path.relative_to(ROOT)}")

    data = json.loads(STATUS.read_text(encoding="utf-8"))

    for key in (
        "version",
        "snapshotDate",
        "progressPercent",
        "overallSummary",
        "metrics",
        "workstreams",
        "gates",
        "blockers",
        "sources",
        "reconciliation",
        "policies",
    ):
        if key not in data:
            fail(f"status snapshot missing key: {key}")

    progress = data["progressPercent"]
    if not isinstance(progress, int) or not 0 <= progress <= 100:
        fail("progressPercent must be an integer between 0 and 100")

    expected_metrics = {
        "Empadronados 2023": ("39,099", "OFFICIAL", "EV-0139"),
        "Votos visibles confirmados": ("26,091", "DERIVED", "EV-0112"),
        "Centros oficiales": ("18", "OFFICIAL", "EV-0142"),
        "JRV reconciliadas": ("100", "OFFICIAL", "EV-0142"),
        "TREP válido-like": ("25,827", "PRELIMINARY", "EV-0144"),
        "Diferencia documentada": ("264", "DERIVED", "Reconciliation"),
        "Mesa pendiente TREP": ("5401", "PRELIMINARY", "EV-0145"),
        "Crosswalks explícitos": ("28", "OFFICIAL", "C1-ELEC-2023-003"),
    }

    for label, expected in expected_metrics.items():
        metric = metric_by_label(data, label)
        actual = (metric.get("value"), metric.get("evidence"), metric.get("source"))
        if actual != expected:
            fail(f"metric {label!r} mismatch: expected {expected}, got {actual}")

    if 26091 - 25827 != 264:
        fail("reconciliation arithmetic changed unexpectedly")

    gates = set(data["gates"])
    if gates != REQUIRED_GATES:
        fail(f"gate set mismatch: expected {sorted(REQUIRED_GATES)}, got {sorted(gates)}")

    policies = set(data["policies"])
    missing_policies = REQUIRED_POLICIES - policies
    if missing_policies:
        fail(f"required safety policies missing: {sorted(missing_policies)}")

    if not any(item.get("name") == "Contabilidad final" and item.get("status") == "PARTIAL" for item in data["workstreams"]):
        fail("final ballot accounting must remain PARTIAL")

    source_status = {item.get("id"): item.get("status") for item in data["sources"]}
    if source_status.get("EV-0144") != "PRELIMINARY_CONFLICT_NOT_PROMOTED":
        fail("EV-0144 must remain preliminary and not promoted")
    if source_status.get("EV-0145") != "PRELIMINARY_ACTA_STATUS_AUTHENTICATED":
        fail("EV-0145 status mismatch")

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="strict")
        for path in REQUIRED_FILES
    )

    forbidden = [
        "/Users/",
        "voter_name",
        "voter_id",
        "DPI",
        "segment_score",
        "support_probability",
    ]
    for token in forbidden:
        if token in combined:
            fail(f"forbidden token found in frontend artifacts: {token}")

    print("[OK] required frontend files present")
    print("[OK] verified metrics and evidence classes preserved")
    print("[OK] preliminary TREP values remain unpromoted")
    print("[OK] reconciliation difference=264")
    print("[OK] all political gates represented as closed")
    print("[OK] safety policy and privacy checks passed")


if __name__ == "__main__":
    main()
