#!/usr/bin/env python3
"""Fail-closed validation for C1-ELEC-2023-005."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURATED = ROOT / "research" / "curated" / "electoral-2023"
RESEARCH = ROOT / "research" / "electoral-2023"

SOURCE_AUDIT = RESEARCH / "final-ballot-source-audit.csv"
FIELDS = CURATED / "final-ballot-accounting-fields-2023.csv"
MISSING_ACTA = CURATED / "missing-trep-acta-investigation-2023.csv"
RECONCILIATION = CURATED / "final-ballot-accounting-reconciliation-2023.md"
REPORT = CURATED / "C1-ELEC-2023-005-implementation-report.md"


def fail(message: str) -> None:
    print(f"[FAIL] {message}", file=sys.stderr)
    sys.exit(1)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


source_rows = read_csv(SOURCE_AUDIT)
field_rows = read_csv(FIELDS)
missing_rows = read_csv(MISSING_ACTA)

required_source_cols = {
    "source_id",
    "evidence_id",
    "authority",
    "source_name",
    "source_type",
    "stable_url_or_path",
    "retrieval_time",
    "content_encoding",
    "raw_sha256",
    "decoded_sha256",
    "scope",
    "fields_observed",
    "source_status",
    "limitations",
}
required_field_cols = {
    "evidence_id",
    "field_name",
    "field_value",
    "unit",
    "source_id",
    "source_record",
    "source_location",
    "source_status",
    "verification_status",
    "limitations",
}
required_missing_cols = {
    "record_key",
    "jrv_id",
    "acta_id",
    "center_code",
    "trep_status",
    "official_source_id",
    "source_location",
    "investigation_status",
    "observed_values",
    "limitations",
}

for label, rows, required in [
    ("source audit", source_rows, required_source_cols),
    ("final fields", field_rows, required_field_cols),
    ("missing acta", missing_rows, required_missing_cols),
]:
    if not rows:
        fail(f"{label} has no rows")
    missing = required - set(rows[0])
    if missing:
        fail(f"{label} missing columns: {sorted(missing)}")

expected_sources = {
    "ELEC23-SRC-010": ("4f856d24f0ffebca83696d89a64abba634fae8bd0582ca710f233e65aa07bffa", "PRELIMINARY_SOURCE_AUTHENTICATED"),
    "ELEC23-SRC-011": ("c79261df959300834b64a947330999aeab34590a216338ac253a468a425cdd4d", "PRELIMINARY_CONFLICT_NOT_PROMOTED"),
    "ELEC23-SRC-012": ("9ab26dc34ca151600c97c89359ee36db9f970f2a559c0abcac9994759808d4c4", "PRELIMINARY_ACTA_STATUS_AUTHENTICATED"),
}
sources = {row["source_id"]: row for row in source_rows}
for source_id, (raw_hash, status) in expected_sources.items():
    row = sources.get(source_id)
    if not row:
        fail(f"missing source row: {source_id}")
    if row["raw_sha256"] != raw_hash:
        fail(f"{source_id} raw hash mismatch")
    if row["source_status"] != status:
        fail(f"{source_id} source_status mismatch: {row['source_status']}")

missing = missing_rows[0]
if len(missing_rows) != 1:
    fail(f"expected one missing-acta investigation row, found {len(missing_rows)}")
if missing["jrv_id"] != "5401":
    fail(f"missing acta jrv_id expected 5401, found {missing['jrv_id']}")
if missing["investigation_status"] != "IDENTIFIED_OFFICIAL":
    fail("missing acta must be IDENTIFIED_OFFICIAL")
if "status=1" not in missing["trep_status"] or "Acta ilegible" not in missing["trep_status"]:
    fail("missing acta TREP status not documented")
if "imgSha=93301a333039a54d82a4bf73117e3838765c6299985534b7e55ce87aa94e7072" not in missing["observed_values"]:
    fail("missing acta image hash not documented")

fields = {(row["field_name"], row["field_value"]) for row in field_rows}
if ("registered_electorate", "39099") not in fields:
    fail("registered_electorate=39099 not present")
if ("visible_organization_vote_sum", "26091") not in fields:
    fail("visible_organization_vote_sum=26091 not present")

prohibited_final_fields = {
    "ballots_cast",
    "printed_valid_vote_total",
    "valid_votes",
    "null_votes",
    "blank_votes",
    "participation_rate",
    "abstention_rate",
}
for row in field_rows:
    if row["field_name"] in prohibited_final_fields:
        fail(f"unsupported final field promoted: {row['field_name']}")
    if row["field_value"] in {"26828", "25827", "912", "89"}:
        fail(f"preliminary value promoted in final fields: {row}")

text = "\n".join(
    path.read_text(encoding="utf-8")
    for path in [RECONCILIATION, REPORT]
)

for required in [
    "25,827 + 912 + 89 = 26,828",
    "26,091 - 25,827 = 264",
    "PARTIAL_RECONCILIATION_WITH_IDENTIFIED_MISSING_ACTA",
    "Political gates remain closed",
]:
    if required not in text:
        fail(f"required statement missing: {required}")

for prohibited in [
    "participation_rate =",
    "abstention_rate =",
    "ballots_cast = 26,828",
    "valid_votes = 25,827",
    "null_votes = 912",
    "blank_votes = 89",
    "territorial ranking approved",
    "paid-media audience approved",
    "mobilization authorized",
]:
    if prohibited in text:
        fail(f"prohibited assertion found: {prohibited}")

for path in [SOURCE_AUDIT, FIELDS, MISSING_ACTA, RECONCILIATION, REPORT]:
    content = path.read_text(encoding="utf-8")
    if re.search(r"/Users/|/Volumes|/tmp/", content):
        fail(f"non-portable path found in {path.relative_to(ROOT)}")
    if re.search(r"\bDPI\b|\b\d{13}\b", content):
        fail(f"possible personal identifier found in {path.relative_to(ROOT)}")

if 26091 - 25827 != 264:
    fail("conflict equation failed")
if 25827 + 912 + 89 != 26828:
    fail("preliminary TREP equation failed")

print("[OK] TREP snapshot sources authenticated")
print("[OK] missing acta identified from official preliminary status data")
print("[OK] final/preliminary separation preserved")
print("[OK] unsupported participation and abstention rejected")
print("[OK] political gates remain closed")
