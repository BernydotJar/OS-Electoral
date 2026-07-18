#!/usr/bin/env python3
"""Scan C2 data artifacts for secrets, personal paths, PII and unsafe capabilities."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGETS = (
    ROOT / "campaigns" / "antigua-guatemala" / "workspace.json",
    ROOT / "fixtures" / "workspaces" / "rio-claro-demo.json",
    ROOT / "fixtures" / "cycle-requests" / "antigua-evidence-priority.json",
    ROOT / "fixtures" / "cycle-requests" / "rio-claro-research-gap.json",
    ROOT / "artifacts" / "cycle-runs" / "antigua-evidence-priority-result.json",
    ROOT / "artifacts" / "cycle-runs" / "rio-claro-research-gap-result.json",
)
FORBIDDEN = {
    "personal path": re.compile(r"/Users/|/home/[^/]+|[A-Za-z]:\\\\Users\\\\"),
    "secret": re.compile(r"(?i)(api[_-]?key|client[_-]?secret|private[_-]?key|password)\s*[:=]\s*['\"]?[A-Za-z0-9+/=_-]{8,}"),
    "voter-level capability": re.compile(r"(?i)(voter[_-]?record|persuasion[_-]?score|citizen[_-]?profile|microtarget)"),
    "outbound capability": re.compile(r"(?i)(send[_-]?message|publish[_-]?content|activate[_-]?ads|spend[_-]?budget|mobilize[_-]?voter)"),
}


def main() -> int:
    for path in TARGETS:
        if not path.is_file():
            raise AssertionError(f"missing safety scan target: {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        for label, pattern in FORBIDDEN.items():
            if pattern.search(text):
                raise AssertionError(f"{label} marker found in {path.relative_to(ROOT)}")
    print("[OK] C2 seeds, requests and results contain no secrets, personal paths, PII capability or outbound execution markers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
