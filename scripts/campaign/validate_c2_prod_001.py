#!/usr/bin/env python3
"""Validate Candidate Brand contracts, fixtures and artifacts."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_candidate_brand.py", "-v"], cwd=ROOT, check=False)
    if tests.returncode:
        return tests.returncode
    commands = [
        [sys.executable, "scripts/campaign/run_candidate_brand_assessment.py", "--workspace", "campaigns/antigua-guatemala/workspace.json", "--brand", "fixtures/candidate-brand/antigua-candidate-brand.json", "--output", "artifacts/candidate-brand/antigua-brand-assessment.json"],
        [sys.executable, "scripts/campaign/run_candidate_brand_assessment.py", "--workspace", "fixtures/workspaces/rio-claro-demo.json", "--brand", "fixtures/candidate-brand/rio-claro-candidate-brand.json", "--output", "artifacts/candidate-brand/rio-claro-brand-assessment.json"],
    ]
    for command in commands:
        run = subprocess.run(command, cwd=ROOT, check=False)
        if run.returncode:
            return run.returncode
    for relative in (
        "schemas/candidate-brand-workspace-v1.schema.json",
        "fixtures/candidate-brand/antigua-candidate-brand.json",
        "fixtures/candidate-brand/rio-claro-candidate-brand.json",
        "artifacts/candidate-brand/antigua-brand-assessment.json",
        "artifacts/candidate-brand/rio-claro-brand-assessment.json",
    ):
        json.loads((ROOT / relative).read_text(encoding="utf-8"))
    print("[OK] C2-PROD-001 candidate brand, tenancy and authority contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
