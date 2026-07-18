#!/usr/bin/env python3
"""Run one governed campaign cycle without mutating inputs or external systems."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.campaign_workspace import (  # noqa: E402
    WorkspaceValidationError, canonical_json, run_governed_cycle
)


def safe_repo_path(value: str, label: str, must_exist: bool) -> Path:
    raw = Path(value)
    if raw.is_absolute() or ".." in raw.parts:
        raise WorkspaceValidationError(f"{label} must be a repository-relative path without traversal")
    path = ROOT / raw
    cursor = ROOT
    for part in raw.parts:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise WorkspaceValidationError(f"{label} cannot use symbolic links")
    if path.suffix.lower() != ".json":
        raise WorkspaceValidationError(f"{label} must be a JSON file")
    if must_exist and (path.is_symlink() or not path.is_file()):
        raise WorkspaceValidationError(f"{label} must be an existing regular, non-symlink file")
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise WorkspaceValidationError(f"{label} must stay inside the repository") from exc
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        workspace_path = safe_repo_path(args.workspace, "workspace", must_exist=True)
        request_path = safe_repo_path(args.request, "request", must_exist=True)
        output_path = safe_repo_path(args.output, "output", must_exist=False)
        if output_path in {workspace_path, request_path}:
            raise WorkspaceValidationError("output cannot overwrite an input")
        workspace = json.loads(workspace_path.read_text(encoding="utf-8"))
        request = json.loads(request_path.read_text(encoding="utf-8"))
        result = run_governed_cycle(workspace, request)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(canonical_json(result), encoding="utf-8")
        print(f"[OK] governed cycle written: {output_path}")
        return 0
    except (WorkspaceValidationError, json.JSONDecodeError, OSError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
