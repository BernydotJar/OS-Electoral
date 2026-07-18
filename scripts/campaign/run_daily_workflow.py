#!/usr/bin/env python3
"""Build one read-only Daily Operating Workflow brief."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from core.daily_workflow import DailyWorkflowValidationError, build_daily_operating_brief, pretty

def safe_path(value:str,label:str,must_exist:bool)->Path:
    raw=Path(value)
    if raw.is_absolute() or ".." in raw.parts: raise DailyWorkflowValidationError(f"{label} must be repository-relative without traversal")
    cursor=ROOT
    for part in raw.parts:
        cursor=cursor/part
        if cursor.exists() and cursor.is_symlink(): raise DailyWorkflowValidationError(f"{label} cannot use symbolic links")
    path=(ROOT/raw).resolve()
    try: path.relative_to(ROOT)
    except ValueError as exc: raise DailyWorkflowValidationError(f"{label} must remain inside repository") from exc
    if path.suffix.lower()!=".json": raise DailyWorkflowValidationError(f"{label} must be JSON")
    if must_exist and not path.is_file(): raise DailyWorkflowValidationError(f"{label} must be an existing regular file")
    return path

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--state",required=True); parser.add_argument("--output",required=True); args=parser.parse_args()
    try:
        state_path=safe_path(args.state,"state",True); output_path=safe_path(args.output,"output",False)
        artifact_root=(ROOT/"artifacts/daily-workflow").resolve()
        try: output_path.relative_to(artifact_root)
        except ValueError as exc: raise DailyWorkflowValidationError("output must stay inside artifacts/daily-workflow") from exc
        state=json.loads(state_path.read_text(encoding="utf-8")); result=build_daily_operating_brief(state)
        output_path.parent.mkdir(parents=True,exist_ok=True); output_path.write_text(pretty(result),encoding="utf-8")
        print(f"[OK] daily workflow brief written: {output_path}"); return 0
    except (DailyWorkflowValidationError,json.JSONDecodeError,OSError) as exc:
        print(f"[ERROR] {exc}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
