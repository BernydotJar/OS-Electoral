#!/usr/bin/env python3
"""Evaluate one authorization request without authentication or side effects."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from core.authorization_policy import AuthorizationPolicyError, authorize, pretty

def safe_path(value:str,label:str,must_exist:bool)->Path:
    raw=Path(value)
    if raw.is_absolute() or ".." in raw.parts: raise AuthorizationPolicyError(f"{label} must be repository-relative without traversal")
    cursor=ROOT
    for part in raw.parts:
        cursor=cursor/part
        if cursor.exists() and cursor.is_symlink(): raise AuthorizationPolicyError(f"{label} cannot use symbolic links")
    path=(ROOT/raw).resolve()
    try: path.relative_to(ROOT)
    except ValueError as exc: raise AuthorizationPolicyError(f"{label} must remain inside repository") from exc
    if path.suffix.lower()!=".json": raise AuthorizationPolicyError(f"{label} must be JSON")
    if must_exist and not path.is_file(): raise AuthorizationPolicyError(f"{label} must be an existing regular file")
    return path

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--principal",required=True); parser.add_argument("--request",required=True); parser.add_argument("--output",required=True); args=parser.parse_args()
    try:
        principal_path=safe_path(args.principal,"principal",True); request_path=safe_path(args.request,"request",True); output_path=safe_path(args.output,"output",False)
        artifact_root=(ROOT/"artifacts/authorization").resolve()
        try: output_path.relative_to(artifact_root)
        except ValueError as exc: raise AuthorizationPolicyError("output must stay inside artifacts/authorization") from exc
        result=authorize(json.loads(principal_path.read_text(encoding="utf-8")),json.loads(request_path.read_text(encoding="utf-8")))
        output_path.parent.mkdir(parents=True,exist_ok=True); output_path.write_text(pretty(result),encoding="utf-8")
        print(f"[OK] authorization decision written: {output_path}"); return 0
    except (AuthorizationPolicyError,json.JSONDecodeError,OSError) as exc:
        print(f"[ERROR] {exc}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
