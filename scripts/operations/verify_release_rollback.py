#!/usr/bin/env python3
"""Validate rollback policy and write one constrained rehearsal receipt."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import psycopg
from sqlalchemy.engine import make_url

from campaignos.operability.rollback import (
    ArtifactCheck,
    AuthorityCheck,
    HealthCheck,
    RehearsalContext,
    RollbackReceipt,
    build_failure_receipt,
    build_receipt,
    load_policy,
    validate_policy_against_repository,
    write_failure_receipt,
    write_receipt,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = ROOT / "program/rollback-readiness.json"
DEFAULT_OUTPUT = ROOT / "artifacts/c3-ops-002/rollback-rehearsal.json"


def _git_revision(reference: str) -> str:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git executable is unavailable")
    result = subprocess.run(  # noqa: S603 - resolved executable and bounded reference.
        [git, "rev-parse", reference],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _git_commit_exists(revision: str) -> bool:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git executable is unavailable")
    result = subprocess.run(  # noqa: S603 - resolved executable and full SHA only.
        [git, "cat-file", "-e", f"{revision}^{{commit}}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _database_migration_head(environment_name: str | None, fallback: str) -> str:
    if environment_name is None:
        return fallback
    database_url = os.environ.get(environment_name)
    if not database_url:
        return fallback
    url = make_url(database_url).set(drivername="postgresql")
    with psycopg.connect(url.render_as_string(hide_password=False)) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version_num FROM alembic_version")
            row = cursor.fetchone()
    if row is None or not isinstance(row[0], str):
        raise RuntimeError("database did not return an Alembic revision")
    return row[0]


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    value.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    value.add_argument("--source-revision")
    value.add_argument("--previous-known-good-revision")
    value.add_argument(
        "--scenario-id",
        default="application_health_failure_backward_compatible",
    )
    value.add_argument("--database-url-env")
    value.add_argument("--requested-operation", default="AUTO_SELECT")
    value.add_argument("--authority-granted", action="store_true")
    value.add_argument(
        "--authority-scope",
        default="CONSTRAINED_NON_PRODUCTION_REHEARSAL",
    )
    value.add_argument("--committed-writes", action="store_true")
    value.add_argument("--production-target", action="store_true")
    value.add_argument("--automatic-worker-replay", action="store_true")
    value.add_argument("--configuration-snapshot-present", action="store_true")
    value.add_argument("--protected-controls-preserved", action="store_true")
    value.add_argument("--verified-backup-present", action="store_true")
    value.add_argument("--isolated-restore-target", action="store_true")
    return value


def _failure_class(exc: Exception) -> str:
    if isinstance(exc, FileNotFoundError):
        return "POLICY_OR_EVIDENCE_FILE_MISSING"
    if isinstance(exc, json.JSONDecodeError):
        return "POLICY_JSON_INVALID"
    if isinstance(exc, subprocess.CalledProcessError):
        return "GIT_EVIDENCE_COMMAND_FAILED"
    if isinstance(exc, RuntimeError):
        return "REHEARSAL_RUNTIME_ERROR"
    if isinstance(exc, ValueError):
        return "POLICY_OR_CONTEXT_VALIDATION_FAILED"
    return "UNEXPECTED_REHEARSAL_ERROR"


def _execute(arguments: argparse.Namespace) -> RollbackReceipt:
    policy = load_policy(arguments.policy)
    validate_policy_against_repository(policy, ROOT)
    source_revision = arguments.source_revision or _git_revision("HEAD")
    previous_revision = arguments.previous_known_good_revision or _git_revision("HEAD^")
    migration_head = _database_migration_head(
        arguments.database_url_env,
        policy.current_migration_head,
    )
    source_commit_present = _git_commit_exists(source_revision)
    previous_commit_present = _git_commit_exists(previous_revision)
    context = RehearsalContext(
        scenario_id=arguments.scenario_id,
        source_revision=source_revision,
        candidate_revision=source_revision,
        previous_known_good_revision=previous_revision,
        environment_classification="CONSTRAINED_NON_PRODUCTION",
        authority=AuthorityCheck(
            granted=arguments.authority_granted,
            scope=arguments.authority_scope,
        ),
        artifact=ArtifactCheck(
            reference=previous_revision,
            immutable=source_commit_present and previous_commit_present,
            provenance_present=source_commit_present and previous_commit_present,
        ),
        migration_head=migration_head,
        committed_writes_observed=arguments.committed_writes,
        health_checks=(
            HealthCheck(name="liveness", passed=False),
            HealthCheck(name="readiness", passed=False),
            HealthCheck(name="database", passed=True),
        ),
        configuration_snapshot_present=arguments.configuration_snapshot_present,
        protected_controls_preserved=arguments.protected_controls_preserved,
        verified_backup_present=arguments.verified_backup_present,
        isolated_restore_target=arguments.isolated_restore_target,
        automatic_worker_replay_requested=arguments.automatic_worker_replay,
        production_target=arguments.production_target,
        requested_operation=arguments.requested_operation,
    )
    return build_receipt(policy, context)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        receipt = _execute(arguments)
    except Exception as exc:  # noqa: BLE001 - fail-closed boundary writes sanitized class only.
        failure = build_failure_receipt(_failure_class(exc))
        write_failure_receipt(arguments.output, failure)
        print(
            f"[FAIL] rollback rehearsal class={failure.failure_class}; "
            "response=REFUSE_UNSAFE_ROLLBACK; production_claim=false",
            file=sys.stderr,
        )
        return 1
    write_receipt(arguments.output, receipt)
    print(
        "[OK] rollback rehearsal "
        f"scenario={receipt.scenario_id}; response={receipt.selected_response.value}; "
        f"decision={receipt.decision}; production_claim=false"
    )
    return 0 if receipt.decision == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
