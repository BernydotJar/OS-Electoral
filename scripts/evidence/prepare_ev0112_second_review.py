#!/usr/bin/env python3
"""Prepare EV-0112 rendered pages and OCR assists for independent review.

This script never updates curated evidence. It only prepares review materials under
`.workspace/ev0112-second-review/` and fails closed when the source is missing.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import fitz

EXPECTED_RELATIVE_PATH = Path(
    "07_Fichas_Comunitarias/"
    "ACUERDO 1-2023 Declarar la validez de la elección de la Corporación "
    "Municipal de ANTIGUA GUATEMALA, del Departamento de Sacatepéquez..pdf"
)
ALTERNATIVE_NAME = "EV-0112.pdf"
EXPECTED_PAGES = 3


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_source(root: Path) -> Path | None:
    for candidate in (root / EXPECTED_RELATIVE_PATH, root / ALTERNATIVE_NAME):
        if candidate.is_file():
            return candidate
    return None


def run_ocr(image: Path, output_base: Path, psm: int) -> dict[str, object]:
    command = ["tesseract", str(image), str(output_base), "-l", "spa+eng", "--psm", str(psm)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "output": str(output_base.with_suffix(".txt")),
    }


def load_dotenv_value(name: str, path: Path = Path(".env")) -> str | None:
    if not path.is_file():
        return None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"').strip("'")
    return None


def main() -> int:
    politics_root_text = os.environ.get("POLITICS_ROOT") or load_dotenv_value("POLITICS_ROOT")
    if not politics_root_text:
        print("[BLOCKED] POLITICS_ROOT is not set and .env has no value", file=sys.stderr)
        return 2

    politics_root = Path(politics_root_text).expanduser().resolve()
    source = find_source(politics_root)
    if source is None:
        print("[BLOCKED] EV-0112 source PDF not found", file=sys.stderr)
        print(f"- expected: {politics_root / EXPECTED_RELATIVE_PATH}", file=sys.stderr)
        print(f"- alternative: {politics_root / ALTERNATIVE_NAME}", file=sys.stderr)
        return 3

    if shutil.which("tesseract") is None:
        print("[FAILED] tesseract is unavailable", file=sys.stderr)
        return 4

    out_dir = Path(".workspace/ev0112-second-review")
    pages_dir = out_dir / "pages"
    ocr_dir = out_dir / "ocr"
    pages_dir.mkdir(parents=True, exist_ok=True)
    ocr_dir.mkdir(parents=True, exist_ok=True)

    document = fitz.open(source)
    if document.page_count != EXPECTED_PAGES:
        print(f"[BLOCKED] expected {EXPECTED_PAGES} pages, found {document.page_count}", file=sys.stderr)
        return 5

    manifest: dict[str, object] = {
        "evidence_id": "EV-0112",
        "source_path": "${POLITICS_ROOT}/" + str(source.relative_to(politics_root)),
        "source_sha256": sha256(source),
        "page_count": document.page_count,
        "render_dpi": 300,
        "ocr_languages": "spa+eng",
        "ocr_role": "assistive_only_requires_visual_review",
        "pages": [],
    }

    matrix = fitz.Matrix(300 / 72, 300 / 72)
    for page_number, page in enumerate(document, start=1):
        image_path = pages_dir / f"page-{page_number:02d}.png"
        page.get_pixmap(matrix=matrix, alpha=False).save(image_path)
        embedded_text = page.get_text("text")
        page_record: dict[str, object] = {
            "page": page_number,
            "image": str(image_path),
            "image_sha256": sha256(image_path),
            "embedded_text_length": len(embedded_text.strip()),
            "ocr": [],
        }
        for psm in (6, 11):
            output_base = ocr_dir / f"page-{page_number:02d}-psm{psm}"
            page_record["ocr"].append(run_ocr(image_path, output_base, psm))
        manifest["pages"].append(page_record)

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] prepared EV-0112 independent review materials: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
