#!/usr/bin/env python3
"""Create auditable PostgreSQL backup/restore evidence without touching source data."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

from campaignos.operability import verify_postgres_recovery

DEFAULT_CLIENT_IMAGE = (
    "postgres:18.3-alpine3.23@sha256:"
    "54451ecb8ab38c24c3ec123f2fd501303a3a1856a5c66e98cecf2460d5e1e9d7"
)


def _git_revision() -> str:
    executable = shutil.which("git")
    if executable is None:
        raise RuntimeError("Git is required to determine the source revision")
    result = subprocess.run(  # noqa: S603 - resolved trusted local executable.
        [executable, "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a native PostgreSQL backup through an isolated restore"
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("CAMPAIGNOS_RECOVERY_DATABASE_URL"),
        help="Source postgresql+psycopg URL; may use CAMPAIGNOS_RECOVERY_DATABASE_URL",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/c3-obs-001"))
    parser.add_argument("--source-revision", default=None)
    parser.add_argument("--target-database", default="campaignos_recovery_restore_test")
    parser.add_argument("--client-image", default=DEFAULT_CLIENT_IMAGE)
    parser.add_argument("--local-client", action="store_true")
    parser.add_argument("--keep-restored-database", action="store_true")
    args = parser.parse_args()

    if not args.database_url:
        parser.error("--database-url or CAMPAIGNOS_RECOVERY_DATABASE_URL is required")
    source_revision = args.source_revision or _git_revision()
    result = verify_postgres_recovery(
        source_database_url=args.database_url,
        output_directory=args.output_dir,
        source_revision=source_revision,
        target_database=args.target_database,
        client_container_image=None if args.local_client else args.client_image,
        keep_restored_database=args.keep_restored_database,
    )
    print(
        "[OK] PostgreSQL recovery verified; "
        f"backup={result.backup_path}; manifest={result.manifest_path}; "
        f"tables={len(result.table_counts)}; revision={result.alembic_version}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
