#!/usr/bin/env python3
"""Validate the partial 2023 Antigua Guatemala ballot-accounting state."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURATED = ROOT / "research" / "curated" / "electoral-2023"
ACCOUNTING = CURATED / "antigua-guatemala-ballot-accounting-2023.csv"
RECONCILIATION = CURATED / "antigua-guatemala-ballot-reconciliation-2023.md"
RESULTS = CURATED / "antigua-guatemala-municipal-results-2023.csv"


def fail(message: str) -> None:
    raise SystemExit(f"[FAIL] {message}")


with ACCOUNTING.open(encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))

if len(rows) != 1:
    fail(f"expected exactly one authenticated accounting row, found {len(rows)}")

row = rows[0]
if row["field_name"] != "registered_electorate":
    fail("only registered_electorate may be populated in the current partial state")
if row["field_value"] != "39099":
    fail("registered electorate must equal official EV-0139 value 39099")
if row["verification_status"] != "OFFICIAL_SOURCE_AUTHENTICATED":
    fail("registered electorate lacks authenticated official status")
if row["election_date"]:
    fail("election_date must remain blank because it is not printed in the cited source row")

with RESULTS.open(encoding="utf-8", newline="") as handle:
    result_rows = list(csv.DictReader(handle))
visible_sum = sum(int(item["votes"]) for item in result_rows)
if len(result_rows) != 14 or visible_sum != 26091:
    fail("visible result baseline must remain 14 rows summing to 26091")

text = RECONCILIATION.read_text(encoding="utf-8")
required = [
    "Status: `PARTIAL_RECONCILIATION`",
    "registered_electorate = 39,099",
    "participation_rate ?= ballots_cast / 39,099",
    "No residual category is inferred",
]
for marker in required:
    if marker not in text:
        fail(f"missing reconciliation marker: {marker}")

for prohibited in [
    "participation_rate =",
    "abstention_rate =",
    "ballots_cast = 26,091",
    "printed_valid_vote_total = 26,091",
]:
    if prohibited in text:
        fail(f"unsupported accounting assertion found: {prohibited}")

print("[OK] registered electorate=39099 authenticated")
print("[OK] visible rows=14; derived sum=26091")
print("[OK] reconciliation=PARTIAL_RECONCILIATION")
print("[OK] participation and abstention remain uncalculated")
