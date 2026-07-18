#!/usr/bin/env python3
"""Validate Daily Operating Workflow contracts."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main()->int:
    tests=subprocess.run([sys.executable,"-m","unittest","discover","-s","tests","-p","test_daily_workflow.py","-v"],cwd=ROOT,check=False)
    if tests.returncode:return tests.returncode
    commands=[
        [sys.executable,"scripts/campaign/run_daily_workflow.py","--state","fixtures/daily-workflow/antigua.json","--output","artifacts/daily-workflow/antigua-daily-brief.json"],
        [sys.executable,"scripts/campaign/run_daily_workflow.py","--state","fixtures/daily-workflow/rio-claro.json","--output","artifacts/daily-workflow/rio-claro-daily-brief.json"],
    ]
    for command in commands:
        run=subprocess.run(command,cwd=ROOT,check=False)
        if run.returncode:return run.returncode
    for relative in ("schemas/daily-operating-workflow-v1.schema.json","fixtures/daily-workflow/antigua.json","fixtures/daily-workflow/rio-claro.json","artifacts/daily-workflow/antigua-daily-brief.json","artifacts/daily-workflow/rio-claro-daily-brief.json"):
        json.loads((ROOT/relative).read_text(encoding="utf-8"))
    print("[OK] C2-PROD-003 daily workflow, tenancy, evidence and no-effect contracts")
    return 0
if __name__=="__main__": raise SystemExit(main())
