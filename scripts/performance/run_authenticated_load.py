#!/usr/bin/env python3
"""Run the bounded C3-PERF-001 harness against an isolated PostgreSQL database."""

from __future__ import annotations

import argparse
import os
import platform
from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from campaignos.performance import (
    LoadVerificationReceipt,
    ProcessIsolatedLoadSupervisor,
    RunnerLimits,
    write_receipt,
)
from campaignos.performance.contracts import RuntimeContext


def _revision(value: str | None) -> str:
    if value and len(value) == 40 and all(character in "0123456789abcdef" for character in value):
        return value
    raise ValueError("an exact 40-character source revision is required")


def _database_url(value: str | None) -> str:
    if not value:
        raise ValueError("isolated performance database URL is required")
    parsed = make_url(value)
    if parsed.drivername != "postgresql+psycopg" or not (
        parsed.database and parsed.database.endswith("_test")
    ):
        raise ValueError("performance database must use PostgreSQL psycopg and end in _test")
    return value


def _migrate(database_url: str) -> None:
    previous = os.environ.get("CAMPAIGNOS_DATABASE_URL")
    os.environ["CAMPAIGNOS_DATABASE_URL"] = database_url
    try:
        config = Config("alembic.ini")
        command.upgrade(config, "head")
        command.check(config)
    finally:
        if previous is None:
            os.environ.pop("CAMPAIGNOS_DATABASE_URL", None)
        else:
            os.environ["CAMPAIGNOS_DATABASE_URL"] = previous


def _failure_receipt(revision: str, code: str) -> LoadVerificationReceipt:
    return LoadVerificationReceipt(
        source_revision=revision,
        generated_at=datetime.now(UTC),
        python_version=platform.python_version(),
        postgresql_version="0",
        catalog_version="1.0",
        runtime_context=RuntimeContext(
            operating_system=platform.system() or "Unknown",
            machine=platform.machine() or "unknown",
            cpu_count=os.cpu_count() or 1,
        ),
        runner_limits=RunnerLimits(),
        scenarios=(),
        harness_failure_codes=(code,),
        overall_decision="FAIL",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database-url",
        default=os.environ.get("CAMPAIGNOS_TEST_DATABASE_URL"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/c3-perf-001/load-verification.json"),
    )
    parser.add_argument("--revision", default=os.environ.get("SOURCE_REVISION"))
    args = parser.parse_args()

    try:
        revision = _revision(args.revision)
    except Exception:
        revision = "0" * 40
        write_receipt(args.output, _failure_receipt(revision, "SOURCE_REVISION_FAILURE"))
        return 1

    try:
        database_url = _database_url(args.database_url)
        _migrate(database_url)
        supervisor = ProcessIsolatedLoadSupervisor(
            database_url=database_url,
            source_revision=revision,
        )
        receipt = supervisor.run()
    except Exception:
        receipt = _failure_receipt(revision, "HARNESS_EXECUTION_FAILURE")

    write_receipt(args.output, receipt)
    return 0 if receipt.overall_decision == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
