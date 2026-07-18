#!/usr/bin/env python3
"""Validate the read-only Governance Workspace snapshot and bootstrap."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WEB=ROOT/"web"

def require(condition:bool,message:str)->None:
    if not condition: raise AssertionError(message)

def main()->int:
    data=json.loads((WEB/"data/governance.json").read_text(encoding="utf-8"))
    script=(WEB/"governance.js").read_text(encoding="utf-8")
    bootstrap=(WEB/"accessibility.js").read_text(encoding="utf-8")
    require(data["mode"]=="READ_ONLY","governance snapshot must be READ_ONLY")
    require(data["publicUseStatus"]=="BLOCKED","public use must remain blocked")
    require(data["brand"]["status"]=="SETUP_REQUIRED","Antigua brand must remain setup-required")
    require(data["brand"]["verifiedAttributes"]==0,"no candidate attribute may be invented")
    require(data["approvalInbox"]["pendingCount"]==len(data["approvalInbox"]["requests"]),"pending count mismatch")
    require(data["approvalInbox"]["pendingCount"]>=1,"approval inbox requires a visible pending request")
    require(data["operations"]["kpis"]["total"]==len(data["operations"]["assignments"]),"assignment KPI mismatch")
    require(all(item["evidenceRefs"] for item in data["operations"]["assignments"]),"assignments require evidence refs")
    serialized=json.dumps(data,ensure_ascii=False).lower()
    for forbidden in ("persuadability_score","voter_profile","voter_id","microtargeting"):
        require(forbidden not in serialized,f"forbidden governance field: {forbidden}")
    require('tab.dataset.module = "governance"' in script,"governance navigation tab is missing")
    require('section.dataset.view = "governance"' in script,"governance module view is missing")
    require('public_use_status' not in script.lower(),"frontend must not reinterpret domain field names")
    require('data-action=' not in script and 'approve-button' not in script,"external decision controls are forbidden")
    require('./governance.js' in bootstrap,"governance bootstrap is missing")
    require("Coordinate 04 · Human governance" in bootstrap,"governance status label is missing")
    require("No publication, spending, targeting, paid media, mobilization or citizen contact" in data["safetyStatement"],"safety contract is incomplete")
    print("[OK] Governance Workspace snapshot, navigation and read-only contracts")
    return 0

if __name__=="__main__": raise SystemExit(main())
