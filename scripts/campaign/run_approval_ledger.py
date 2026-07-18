#!/usr/bin/env python3
"""Project an approval inbox or propose a ledger transition without persistence."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from core.approval_ledger import ApprovalLedgerValidationError, canonical_json, project_inbox, propose_transition

def safe_path(value:str,label:str,must_exist:bool)->Path:
    raw=Path(value)
    if raw.is_absolute() or ".." in raw.parts: raise ApprovalLedgerValidationError(f"{label} must be repository-relative without traversal")
    cursor=ROOT
    for part in raw.parts:
        cursor=cursor/part
        if cursor.exists() and cursor.is_symlink(): raise ApprovalLedgerValidationError(f"{label} cannot use symbolic links")
    path=(ROOT/raw).resolve()
    try: path.relative_to(ROOT)
    except ValueError as exc: raise ApprovalLedgerValidationError(f"{label} must remain inside repository") from exc
    if path.suffix.lower()!=".json": raise ApprovalLedgerValidationError(f"{label} must be JSON")
    if must_exist and not path.is_file(): raise ApprovalLedgerValidationError(f"{label} must be an existing regular file")
    return path

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state",required=True); parser.add_argument("--command"); parser.add_argument("--output",required=True)
    args=parser.parse_args()
    try:
        state_path=safe_path(args.state,"state",True); output_path=safe_path(args.output,"output",False)
        artifact_root=(ROOT/"artifacts/approval-ledger").resolve()
        try: output_path.relative_to(artifact_root)
        except ValueError as exc: raise ApprovalLedgerValidationError("output must stay inside artifacts/approval-ledger") from exc
        state=json.loads(state_path.read_text(encoding="utf-8"))
        if args.command:
            command_path=safe_path(args.command,"command",True)
            result=propose_transition(state,json.loads(command_path.read_text(encoding="utf-8")))
        else: result=project_inbox(state)
        output_path.parent.mkdir(parents=True,exist_ok=True)
        output_path.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(f"[OK] approval ledger artifact written: {output_path}")
        return 0
    except (ApprovalLedgerValidationError,json.JSONDecodeError,OSError) as exc:
        print(f"[ERROR] {exc}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
