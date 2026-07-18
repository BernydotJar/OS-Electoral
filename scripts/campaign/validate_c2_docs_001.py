#!/usr/bin/env python3
"""Validation harness for C2-DOCS-001 operator runbook and release gate guide."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_safety() -> None:
    print("Running safety scans on runbook file...")
    targets = [
        ROOT / "docs/operator-runbook-release-gates.md"
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
        verify_safety()
        print("[OK] C2-DOCS-001 operator runbook and release gate guide validation passed successfully.")
        return 0
    except Exception as exc:
        print(f"[ERROR] Validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
