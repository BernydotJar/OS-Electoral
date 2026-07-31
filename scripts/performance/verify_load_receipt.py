#!/usr/bin/env python3
"""Independently validate a C3-PERF-001 receipt."""

from __future__ import annotations

import argparse
from pathlib import Path

from campaignos.performance import load_and_verify_receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    receipt = load_and_verify_receipt(args.receipt)
    return 0 if receipt.overall_decision == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
