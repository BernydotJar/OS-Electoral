#!/usr/bin/env python3
"""Reproducible C2-PLAT-001 contract and adversarial evaluation gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_campaign_workspace.py", "-v"]
    run = subprocess.run(command, cwd=ROOT, check=False)
    if run.returncode:
        return run.returncode
    for relative in ("schemas/campaign-workspace-v1.schema.json", "schemas/cycle-request-v1.schema.json"):
        json.loads((ROOT / relative).read_text(encoding="utf-8"))
    for relative in ("campaigns/antigua-guatemala/workspace.json", "fixtures/workspaces/rio-claro-demo.json"):
        data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        if data["metadata"]["fixture_type"] not in {"OPERATOR_WORKSPACE", "SYNTHETIC"}:
            raise AssertionError(f"unexpected fixture type: {relative}")
    scan = subprocess.run([sys.executable, "scripts/campaign/scan_c2_safety.py"], cwd=ROOT, check=False)
    if scan.returncode:
        return scan.returncode
    print("[OK] C2 schemas, invariants, gates, loops, tenancy and adversarial contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
