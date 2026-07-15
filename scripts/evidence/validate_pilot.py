#!/usr/bin/env python3
"""Validate Cycle 1 evidence extraction pilot outputs."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Any

import yaml


EXPECTED_IDS = {"EV-0111", "EV-0112", "EV-0105", "EV-0114"}
HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
PII_RE = re.compile(
    r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?<!\d)\+?502[\s.-]?\d{4}[\s.-]?\d{4}(?!\d)|(?i:\b(?:tel(?:efo(?:no)?)?|telefono|cel(?:ular)?|whatsapp)\s*[:#-]?\s*\d{4}[\s.-]?\d{4}\b)|(?i:\b(?:dpi|cui)\s*[:#-]?\s*(?:\d[\s-]?){13}\b)"
)
PII_NEGATIVE_SELF_TESTS = [
    "CUILAPA",
    "CUILCO",
    "Dirección Municipal de Planificación",
    "Direccion Municipal de Planificacion",
    "10001437",
    "34.293.293",
    "Población 155,383",
]
PII_POSITIVE_SELF_TESTS = [
    "correo persona@example.com",
    "+502 5555 1234",
    "telefono: 5555-1234",
    "DPI 1234567890101",
    "CUI 1234567890101",
]
PDF_CSV_COLUMNS = {
    "evidence_id",
    "source_file",
    "page",
    "table_index",
    "row_index",
    "column_index",
    "column_name",
    "cell_value",
}
XLSX_CSV_COLUMNS = {
    "evidence_id",
    "workbook",
    "sheet",
    "row",
    "column",
    "column_letter",
    "header",
    "value",
    "formula",
    "is_blank",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate extracted pilot outputs.")
    parser.add_argument("--input", required=True, help="Extraction output directory.")
    parser.add_argument("--pii-self-test", action="store_true", help="Run PII scanner self-tests before validating files.")
    return parser.parse_args()


def run_pii_self_test() -> list[str]:
    errors: list[str] = []
    for text in PII_NEGATIVE_SELF_TESTS:
        if PII_RE.search(text):
            errors.append(f"PII false positive for: {text}")
    for text in PII_POSITIVE_SELF_TESTS:
        if not PII_RE.search(text):
            errors.append(f"PII false negative for: {text}")
    return errors


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a YAML mapping")
    return data


def scan_for_pii(path: Path) -> list[str]:
    if path.suffix.lower() not in {".md", ".csv", ".yaml", ".yml"}:
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    matches = sorted(set(match.group(0) for match in PII_RE.finditer(text)))
    return matches[:10]


def validate_csv(path: Path, expected: set[str], evidence_id: str) -> list[str]:
    errors: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = expected - columns
        if missing:
            errors.append(f"{path} missing columns: {sorted(missing)}")
        row_count = 0
        for row in reader:
            row_count += 1
            if row.get("evidence_id") != evidence_id:
                errors.append(f"{path} row {row_count} has wrong evidence_id: {row.get('evidence_id')}")
                break
        if row_count == 0 and path.name.endswith(".tables.csv"):
            # PDF table extraction can legitimately produce a header-only file.
            return errors
        if row_count == 0:
            errors.append(f"{path} has no data rows")
    return errors


def validate_pdf_markdown(path: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    page_count = manifest.get("page_count")
    pages = [int(match.group(1)) for match in re.finditer(r"^## Pagina (\d+)$", text, re.MULTILINE)]
    if not isinstance(page_count, int) or page_count <= 0:
        errors.append(f"{path} manifest has invalid page_count")
    elif pages != list(range(1, page_count + 1)):
        errors.append(f"{path} page headings do not preserve full numbering")
    return errors


def validate_manifest(path: Path, input_dir: Path) -> tuple[str | None, list[str]]:
    errors: list[str] = []
    manifest = read_yaml(path)
    evidence_id = manifest.get("evidence_id")
    if evidence_id not in EXPECTED_IDS:
        errors.append(f"{path} has unexpected evidence_id: {evidence_id}")
        return None, errors

    required_keys = [
        "source_path",
        "source_type",
        "collection",
        "source_class",
        "review_status_before",
        "extracted_at",
        "extractor",
        "content_hash",
        "extraction_status",
        "limitations",
        "outputs",
    ]
    for key in required_keys:
        if key not in manifest:
            errors.append(f"{path} missing key: {key}")

    content_hash = str(manifest.get("content_hash", ""))
    if not HASH_RE.match(content_hash):
        errors.append(f"{path} has invalid content_hash")

    source_path = Path(str(manifest.get("source_path", "")))
    if not source_path.exists():
        errors.append(f"{path} source_path does not exist: {source_path}")

    limitations = manifest.get("limitations")
    if not isinstance(limitations, list) or not limitations:
        errors.append(f"{path} must declare limitations")

    outputs = manifest.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        errors.append(f"{path} must list outputs")
        outputs = []

    for output_name in outputs:
        output_path = Path(str(output_name))
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        if not output_path.exists():
            errors.append(f"{path} output missing: {output_path}")
            continue
        if output_path.stat().st_size == 0:
            errors.append(f"{path} output empty: {output_path}")
        pii = scan_for_pii(output_path)
        if pii:
            errors.append(f"{output_path} contains possible unredacted PII: {pii}")

    source_type = manifest.get("source_type")
    if source_type == "pdf":
        markdowns = [Path(str(item)) for item in outputs if str(item).endswith(".md")]
        csvs = [Path(str(item)) for item in outputs if str(item).endswith(".tables.csv")]
        if len(markdowns) != 1:
            errors.append(f"{path} pdf must have exactly one markdown output")
        else:
            errors.extend(validate_pdf_markdown(markdowns[0], manifest))
        if len(csvs) != 1:
            errors.append(f"{path} pdf must have exactly one tables CSV")
        else:
            errors.extend(validate_csv(csvs[0], PDF_CSV_COLUMNS, str(evidence_id)))
    elif source_type == "xlsx":
        sheet_names = manifest.get("sheet_names")
        if not isinstance(sheet_names, list) or not sheet_names:
            errors.append(f"{path} xlsx must list sheet_names")
        csvs = [Path(str(item)) for item in outputs if ".sheet-" in str(item) and str(item).endswith(".csv")]
        if not sheet_names or len(csvs) != len(sheet_names):
            errors.append(f"{path} xlsx CSV count must match sheet_names")
        for csv_path in csvs:
            errors.extend(validate_csv(csv_path, XLSX_CSV_COLUMNS, str(evidence_id)))
    else:
        errors.append(f"{path} unsupported source_type in manifest: {source_type}")

    return str(evidence_id), errors


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input)
    manifests_dir = input_dir / "manifests"
    errors: list[str] = []

    manifest_paths = sorted(manifests_dir.glob("EV-*.yaml"))
    found_ids: set[str] = set()
    if len(manifest_paths) != 4:
        errors.append(f"expected 4 manifests, found {len(manifest_paths)}")

    for manifest_path in manifest_paths:
        evidence_id, manifest_errors = validate_manifest(manifest_path, input_dir)
        if evidence_id:
            found_ids.add(evidence_id)
        errors.extend(manifest_errors)

    missing_ids = EXPECTED_IDS - found_ids
    if missing_ids:
        errors.append(f"missing manifests for: {sorted(missing_ids)}")

    if errors:
        print("[FAILED] pilot validation failed")
        for error in errors:
            print(f"- {error}")
        return 1

    print("[OK] pilot validation passed")
    print(f"- manifests: {len(manifest_paths)}")
    print(f"- evidence_ids: {', '.join(sorted(found_ids))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
