"""Atomic sanitized receipt persistence and independent verification."""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from campaignos.performance.catalog import default_workload_catalog
from campaignos.performance.contracts import (
    LoadVerificationReceipt,
    assert_receipt_sanitized,
    validate_receipt_against_catalog,
)


def write_receipt(path: Path, receipt: LoadVerificationReceipt) -> None:
    validate_receipt_against_catalog(receipt, default_workload_catalog())
    assert_receipt_sanitized(receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(receipt.model_dump_json(indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_and_verify_receipt(path: Path) -> LoadVerificationReceipt:
    try:
        receipt = LoadVerificationReceipt.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as exc:
        raise ValueError("load-verification receipt is invalid") from exc
    validate_receipt_against_catalog(receipt, default_workload_catalog())
    assert_receipt_sanitized(receipt)
    return receipt
