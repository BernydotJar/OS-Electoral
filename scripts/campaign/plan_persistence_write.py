#!/usr/bin/env python3
"""Run a read-only persistence planning operation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.persistence_audit import PersistenceContractError, plan_append, pretty


def safe_path(value: str, label: str, must_exist: bool) -> Path:
    raw = Path(value)
    if raw.is_absolute() or ".." in raw.parts:
        raise PersistenceContractError(f"{label} must be repository-relative without traversal")
    cursor = ROOT
    for part in raw.parts:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise PersistenceContractError(f"{label} cannot use symbolic links")
    path = (ROOT / raw).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise PersistenceContractError(f"{label} must remain inside repository") from exc
    if path.suffix.lower() != ".json":
        raise PersistenceContractError(f"{label} must be JSON")
    if must_exist and not path.is_file():
        raise PersistenceContractError(f"{label} must be an existing regular file")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        store_path = safe_path(args.store, "store", True)
        auth_path = safe_path(args.authorization, "authorization", True)
        intent_path = safe_path(args.intent, "intent", True)
        output_path = safe_path(args.output, "output", False)

        artifact_root = (ROOT / "artifacts/persistence-audit").resolve()
        try:
            output_path.relative_to(artifact_root)
        except ValueError as exc:
            raise PersistenceContractError("output must stay inside artifacts/persistence-audit") from exc

        if output_path in {store_path, auth_path, intent_path}:
            raise PersistenceContractError("output cannot overwrite input")

        store = json.loads(store_path.read_text(encoding="utf-8"))
        authorization = json.loads(auth_path.read_text(encoding="utf-8"))
        intent = json.loads(intent_path.read_text(encoding="utf-8"))

        result = plan_append(store, intent, authorization)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(pretty(result), encoding="utf-8")
        print(f"[OK] persistence write plan written: {output_path}")
        return 0
    except (PersistenceContractError, json.JSONDecodeError, OSError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
