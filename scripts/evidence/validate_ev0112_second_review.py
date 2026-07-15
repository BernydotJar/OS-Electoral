#!/usr/bin/env python3
"""Validate EV-0112 second-review artifacts without promoting evidence."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ALLOWED_CHANGE_TYPES = {"CONFIRMED", "CORRECTED", "UNRESOLVED", "NOT_PRESENT"}
REQUIRED_COLUMNS = {
    "field_group",
    "page",
    "record_key",
    "previous_value",
    "reviewed_value",
    "change_type",
    "review_status",
    "review_note",
}
EXPECTED_VOTE_KEYS = {
    "COD-108", "COD-23", "COD-35", "COD-38", "COD-33", "COD-36", "COD-12",
    "COD-27", "COD-32", "COD-15", "COD-19", "COD-18", "COD-17", "COD-31",
}


def main() -> int:
    path = Path("research/curated/electoral-2023/EV-0112-corrections.csv")
    if not path.is_file():
        print(f"[FAILED] missing {path}", file=sys.stderr)
        return 1

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - fields
        if missing:
            print(f"[FAILED] missing columns: {sorted(missing)}", file=sys.stderr)
            return 1
        rows = list(reader)

    invalid = sorted({row["change_type"] for row in rows} - ALLOWED_CHANGE_TYPES)
    if invalid:
        print(f"[FAILED] invalid change types: {invalid}", file=sys.stderr)
        return 1

    vote_rows = [row for row in rows if row["field_group"] == "vote_row"]
    vote_keys = {row["record_key"] for row in vote_rows}
    if vote_keys != EXPECTED_VOTE_KEYS:
        print(
            f"[FAILED] vote-row coverage mismatch; missing={sorted(EXPECTED_VOTE_KEYS-vote_keys)} "
            f"unexpected={sorted(vote_keys-EXPECTED_VOTE_KEYS)}",
            file=sys.stderr,
        )
        return 1

    if len(vote_rows) != 14:
        print(f"[FAILED] expected 14 vote rows, found {len(vote_rows)}", file=sys.stderr)
        return 1

    source_available = (
        Path(".workspace/ev0112-second-review/manifest.json").is_file()
        or Path("research/curated/electoral-2023/EV-0112-second-review-manifest.json").is_file()
    )
    if not source_available:
        falsely_resolved = [
            row["record_key"] for row in rows
            if row["change_type"] in {"CONFIRMED", "CORRECTED"}
        ]
        if falsely_resolved:
            print(
                "[FAILED] source is unavailable but fields were confirmed/corrected: "
                + ", ".join(falsely_resolved),
                file=sys.stderr,
            )
            return 1

    print(f"[OK] EV-0112 corrections ledger rows={len(rows)} vote_rows=14")
    print(f"[OK] source_material_available={source_available}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
