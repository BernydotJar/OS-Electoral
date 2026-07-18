#!/usr/bin/env python3
"""Run one read-only Candidate Brand assessment."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.candidate_brand import CandidateBrandValidationError, build_candidate_brand_assessment, canonical_json


def safe_path(value: str, label: str, must_exist: bool) -> Path:
    raw = Path(value)
    if raw.is_absolute() or ".." in raw.parts:
        raise CandidateBrandValidationError(f"{label} must be repository-relative without traversal")
    cursor = ROOT
    for part in raw.parts:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise CandidateBrandValidationError(f"{label} cannot use symbolic links")
    path = (ROOT / raw).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise CandidateBrandValidationError(f"{label} must remain inside repository") from exc
    if path.suffix.lower() != ".json":
        raise CandidateBrandValidationError(f"{label} must be JSON")
    if must_exist and not path.is_file():
        raise CandidateBrandValidationError(f"{label} must be an existing regular file")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--brand", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        workspace_path = safe_path(args.workspace, "workspace", True)
        brand_path = safe_path(args.brand, "brand", True)
        output_path = safe_path(args.output, "output", False)
        artifact_root = (ROOT / "artifacts/candidate-brand").resolve()
        try:
            output_path.relative_to(artifact_root)
        except ValueError as exc:
            raise CandidateBrandValidationError("output must stay inside artifacts/candidate-brand") from exc
        if output_path in {workspace_path, brand_path}:
            raise CandidateBrandValidationError("output cannot overwrite input")
        workspace = json.loads(workspace_path.read_text(encoding="utf-8"))
        brand = json.loads(brand_path.read_text(encoding="utf-8"))
        result = build_candidate_brand_assessment(brand, workspace)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(canonical_json(result), encoding="utf-8")
        print(f"[OK] candidate brand assessment written: {output_path}")
        return 0
    except (CandidateBrandValidationError, json.JSONDecodeError, OSError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
