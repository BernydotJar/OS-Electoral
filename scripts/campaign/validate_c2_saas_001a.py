#!/usr/bin/env python3
"""Validate tenant context and authorization policy boundary."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main()->int:
    tests=subprocess.run([sys.executable,"-m","unittest","discover","-s","tests","-p","test_authorization_policy.py","-v"],cwd=ROOT,check=False)
    if tests.returncode:return tests.returncode
    command=[sys.executable,"scripts/campaign/run_authorization_policy.py","--principal","fixtures/authorization/antigua-human.json","--request","fixtures/authorization/antigua-read-request.json","--output","artifacts/authorization/antigua-read-decision.json"]
    run=subprocess.run(command,cwd=ROOT,check=False)
    if run.returncode:return run.returncode
    for relative in ("schemas/principal-context-v1.schema.json","schemas/authorization-request-v1.schema.json","fixtures/authorization/antigua-human.json","fixtures/authorization/rio-agent.json","artifacts/authorization/antigua-read-decision.json"):
        json.loads((ROOT/relative).read_text(encoding="utf-8"))
    print("[OK] C2-SAAS-001A tenant context, permission scope and deny-by-default contracts")
    return 0
if __name__=="__main__": raise SystemExit(main())
