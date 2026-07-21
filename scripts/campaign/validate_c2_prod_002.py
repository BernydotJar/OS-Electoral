#!/usr/bin/env python3
"""Validate Approval Inbox and Decision Ledger contracts."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main()->int:
    tests=subprocess.run([sys.executable,"-m","unittest","discover","-s","tests","-p","test_approval_ledger.py","-v"],cwd=ROOT,check=False)
    if tests.returncode: return tests.returncode
    commands=[
        [sys.executable,"scripts/campaign/run_approval_ledger.py","--state","fixtures/approval-ledger/antigua.json","--output","artifacts/approval-ledger/antigua-inbox.json"],
        [sys.executable,"scripts/campaign/run_approval_ledger.py","--state","fixtures/approval-ledger/antigua.json","--command","fixtures/approval-ledger/antigua-approve-command.json","--principal","fixtures/approval-ledger/antigua-trusted-principal.json","--authorization-request","fixtures/approval-ledger/antigua-transition-authorization-request.json","--authentication-binding","fixtures/approval-ledger/antigua-authenticated-binding.json","--output","artifacts/approval-ledger/antigua-transition-proposal.json"],
        [sys.executable,"scripts/campaign/run_approval_ledger.py","--state","fixtures/approval-ledger/rio-claro.json","--output","artifacts/approval-ledger/rio-claro-inbox.json"],
    ]
    for command in commands:
        run=subprocess.run(command,cwd=ROOT,check=False)
        if run.returncode: return run.returncode
    for relative in ("schemas/approval-ledger-v1.schema.json","schemas/approval-transition-v1.schema.json","fixtures/approval-ledger/antigua.json","fixtures/approval-ledger/rio-claro.json","artifacts/approval-ledger/antigua-inbox.json","artifacts/approval-ledger/antigua-transition-proposal.json","artifacts/approval-ledger/rio-claro-inbox.json"):
        json.loads((ROOT/relative).read_text(encoding="utf-8"))
    print("[OK] C2-PROD-002 approval inbox, ledger integrity, tenancy and authority contracts")
    return 0
if __name__=="__main__": raise SystemExit(main())
