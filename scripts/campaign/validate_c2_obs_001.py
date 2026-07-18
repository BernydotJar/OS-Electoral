#!/usr/bin/env python3
"""Validation harness for C2-OBS-001 audit observability and integrity read model."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_unit_tests() -> None:
    print("Executing audit observability unit tests...")
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_audit_observability.py", "-v"]
    res = subprocess.run(command, cwd=ROOT, check=False)
    if res.returncode != 0:
        raise AssertionError("Audit observability unit tests failed")


def run_cli_tests() -> None:
    print("Executing CLI generate_audit_report tests...")
    for label, store_name, output_name in [
        ("Antigua", "fixtures/persistence/antigua-store.json", "audit-report-antigua-2026.md"),
        ("Rio Claro", "fixtures/persistence/rio-claro-store.json", "audit-report-rio-claro-2026-demo.md")
    ]:
        store_path = ROOT / store_name
        output_dir = ROOT / "artifacts/persistence-audit"
        command = [
            sys.executable,
            "scripts/campaign/generate_audit_report.py",
            "--store", str(store_path),
            "--output-dir", str(output_dir)
        ]
        res = subprocess.run(command, cwd=ROOT, check=False)
        if res.returncode != 0:
            raise AssertionError(f"CLI generation failed for {label}")

        expected_file = output_dir / output_name
        if not expected_file.is_file():
            raise AssertionError(f"Expected audit report file missing: {expected_file.relative_to(ROOT)}")


def verify_safety() -> None:
    print("Running safety scans on observability files...")
    targets = [
        ROOT / "core/audit_observability.py",
        ROOT / "scripts/campaign/generate_audit_report.py",
        ROOT / "tests/test_audit_observability.py"
    ]
    forbidden = {
        "personal path": re.compile(r"/Users/|/home/[^/]+|[A-Za-z]:\\\\Users\\\\"),
        "secret": re.compile(r"(?i)(api[_-]?key|client[_-]?secret|private[_-]?key|password)\s*[:=]\s*['\"]?[A-Za-z0-9+/=_-]{8,}"),
        "voter-level capability": re.compile(r"(?i)(voter[_-]?record|persuasion[_-]?score|citizen[_-]?profile|microtarget)"),
        "outbound capability": re.compile(r"(?i)(send[_-]?message|publish[_-]?content|activate[_-]?ads|spend[_-]?budget|mobilize[_-]?voter)"),
    }
    for path in targets:
        if not path.is_file():
            raise AssertionError(f"Target file for safety scan missing: {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        for label, pattern in forbidden.items():
            if pattern.search(text):
                raise AssertionError(f"{label} found in {path.relative_to(ROOT)}")


def main() -> int:
    try:
        run_unit_tests()
        run_cli_tests()
        verify_safety()
        print("[OK] C2-OBS-001 audit observability read model validation passed successfully.")
        return 0
    except Exception as exc:
        print(f"[ERROR] Validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
