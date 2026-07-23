"""Native PostgreSQL backup and isolated restore verification.

The source database is read-only. Database creation and deletion are restricted
to a separately named ``*_restore_test`` target. Credentials are passed only
through connection libraries or ``PGPASSWORD`` and never written to reports.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO, Final

import psycopg
from psycopg import sql
from sqlalchemy.engine import URL, make_url

SAFE_DATABASE_NAME: Final = re.compile(r"^(?=.{1,63}$)[A-Za-z_][A-Za-z0-9_]*_restore_test$")
SAFE_REVISION: Final = re.compile(r"^[0-9a-f]{7,40}$")
CLIENT_VERSION: Final = re.compile(r"\(PostgreSQL\)\s+(\d+)(?:\.\d+)?")
PINNED_IMAGE: Final = re.compile(r"^[A-Za-z0-9./:_-]+@sha256:[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class DatabaseEndpoint:
    host: str
    port: int
    username: str
    password: str = field(repr=False)
    database: str

    @classmethod
    def from_sqlalchemy_url(cls, value: str) -> DatabaseEndpoint:
        parsed = make_url(value)
        if parsed.drivername != "postgresql+psycopg":
            raise ValueError("database URL must use postgresql+psycopg")
        if not parsed.host or not parsed.username or not parsed.database:
            raise ValueError("database URL must include host, username and database")
        password = parsed.password
        if not isinstance(password, str) or not password:
            raise ValueError("database URL must include a password")
        return cls(
            host=parsed.host,
            port=parsed.port or 5432,
            username=parsed.username,
            password=password,
            database=parsed.database,
        )

    def sqlalchemy_url(self, database: str | None = None) -> str:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=database or self.database,
        ).render_as_string(hide_password=False)

    def psycopg_conninfo(self, database: str | None = None) -> str:
        return (
            make_url(self.sqlalchemy_url(database))
            .set(drivername="postgresql")
            .render_as_string(hide_password=False)
        )

    def client_args(self, database: str | None = None) -> list[str]:
        return [
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--username",
            self.username,
            "--dbname",
            database or self.database,
        ]


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    backup_path: Path
    manifest_path: Path
    metrics_path: Path
    backup_sha256: str
    backup_size_bytes: int
    alembic_version: str
    table_counts: dict[str, int]
    target_database: str


def verify_postgres_recovery(
    *,
    source_database_url: str,
    output_directory: Path,
    source_revision: str,
    target_database: str,
    client_container_image: str | None = None,
    keep_restored_database: bool = False,
) -> RecoveryResult:
    """Back up a source database and verify an isolated exact restore."""

    source = DatabaseEndpoint.from_sqlalchemy_url(source_database_url)
    if not source.database.endswith("_test"):
        raise ValueError("recovery verification requires an isolated *_test source database")
    _require_restore_target(target_database, source.database)
    if not SAFE_REVISION.fullmatch(source_revision):
        raise ValueError("source_revision must be a lowercase 7 to 40 character Git SHA")
    if client_container_image is not None and not PINNED_IMAGE.fullmatch(client_container_image):
        raise ValueError("client_container_image must use an immutable sha256 digest")

    server_major = _server_major(source, source.database)
    client_major = _client_major(client_container_image)
    if client_major != server_major:
        raise RuntimeError("PostgreSQL client and server major versions must match")

    output_directory.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(tz=UTC)
    stem = f"campaignos-{created_at.strftime('%Y%m%dT%H%M%SZ')}-{source_revision[:12]}"
    backup_path = output_directory / f"{stem}.dump"
    temporary_backup = backup_path.with_suffix(".dump.tmp")
    manifest_path = output_directory / f"{stem}.manifest.json"
    metrics_path = output_directory / "campaignos-recovery.prom"

    _drop_restore_database(source, target_database)
    _create_restore_database(source, target_database)
    try:
        _dump_database(source, temporary_backup, client_container_image)
        temporary_backup.chmod(0o600)
        temporary_backup.replace(backup_path)
        _validate_archive(source, backup_path, client_container_image)
        _restore_database(source, target_database, backup_path, client_container_image)

        source_version, source_counts = _snapshot(source, source.database)
        target_version, target_counts = _snapshot(source, target_database)
        if target_version != source_version:
            raise RuntimeError("restored Alembic version does not match the source")
        if target_counts != source_counts:
            raise RuntimeError("restored table row counts do not match the source")

        backup_sha256 = _sha256(backup_path)
        backup_size = backup_path.stat().st_size
        completed_at = datetime.now(tz=UTC)
        manifest: dict[str, object] = {
            "schema_version": "1.0",
            "status": "PASS",
            "generated_at": completed_at.isoformat().replace("+00:00", "Z"),
            "source_revision": source_revision,
            "source_database": source.database,
            "target_database": target_database,
            "postgres_server_major": server_major,
            "postgres_client_major": client_major,
            "backup_format": "postgresql-custom",
            "backup_sha256": backup_sha256,
            "backup_size_bytes": backup_size,
            "alembic_version": source_version,
            "table_counts": source_counts,
            "source_mutation": "NONE",
            "external_effects": "NONE_TEST_RESTORE_ONLY",
        }
        _write_json(manifest_path, manifest)
        _write_metrics(metrics_path, completed_at, backup_size, len(source_counts))
        return RecoveryResult(
            backup_path=backup_path,
            manifest_path=manifest_path,
            metrics_path=metrics_path,
            backup_sha256=backup_sha256,
            backup_size_bytes=backup_size,
            alembic_version=source_version,
            table_counts=source_counts,
            target_database=target_database,
        )
    finally:
        if temporary_backup.exists():
            temporary_backup.unlink()
        if not keep_restored_database:
            _drop_restore_database(source, target_database)


def _require_restore_target(target_database: str, source_database: str) -> None:
    if not SAFE_DATABASE_NAME.fullmatch(target_database):
        raise ValueError("target_database must be a bounded *_restore_test identifier")
    if target_database == source_database:
        raise ValueError("target_database must differ from the source database")


def _client_command(binary: str, image: str | None) -> list[str]:
    if image is None:
        return [binary]
    return [
        "docker",
        "run",
        "--rm",
        "--interactive",
        "--network",
        "host",
        "--env",
        "PGPASSWORD",
        image,
        binary,
    ]


def _run_client(
    command: list[str],
    *,
    password: str,
    stdin: BinaryIO | None = None,
    stdout: BinaryIO | int | None = subprocess.PIPE,
) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PGPASSWORD"] = password
    try:
        return subprocess.run(  # noqa: S603 - validated constants and endpoint fields only.
            command,
            check=True,
            env=environment,
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"required recovery executable is unavailable: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()[:500]
        raise RuntimeError(f"PostgreSQL recovery command failed: {detail}") from exc


def _client_major(image: str | None) -> int:
    result = _run_client(_client_command("pg_dump", image) + ["--version"], password="")
    matched = CLIENT_VERSION.search(result.stdout.decode("utf-8", errors="replace"))
    if matched is None:
        raise RuntimeError("unable to determine PostgreSQL client major version")
    return int(matched.group(1))


def _server_major(endpoint: DatabaseEndpoint, database: str) -> int:
    with psycopg.connect(endpoint.psycopg_conninfo(database)) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SHOW server_version_num")
            row = cursor.fetchone()
    if row is None:
        raise RuntimeError("PostgreSQL did not return server_version_num")
    return int(str(row[0])) // 10000


def _dump_database(endpoint: DatabaseEndpoint, path: Path, image: str | None) -> None:
    command = _client_command("pg_dump", image) + [
        *endpoint.client_args(),
        "--format=custom",
        "--compress=9",
        "--no-owner",
        "--no-acl",
    ]
    with path.open("wb") as output:
        _run_client(command, password=endpoint.password, stdout=output)


def _validate_archive(
    endpoint: DatabaseEndpoint,
    path: Path,
    image: str | None,
) -> None:
    command = _client_command("pg_restore", image) + ["--list"]
    with path.open("rb") as archive:
        result = _run_client(command, password=endpoint.password, stdin=archive)
    listing = result.stdout.decode("utf-8", errors="replace")
    if "TABLE" not in listing or "alembic_version" not in listing:
        raise RuntimeError("backup archive is missing required schema objects")


def _restore_database(
    endpoint: DatabaseEndpoint,
    target_database: str,
    path: Path,
    image: str | None,
) -> None:
    _require_restore_target(target_database, endpoint.database)
    command = _client_command("pg_restore", image) + [
        *endpoint.client_args(target_database),
        "--exit-on-error",
        "--no-owner",
        "--no-acl",
    ]
    with path.open("rb") as archive:
        _run_client(command, password=endpoint.password, stdin=archive)


def _snapshot(endpoint: DatabaseEndpoint, database: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    with psycopg.connect(endpoint.psycopg_conninfo(database)) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version_num FROM alembic_version")
            revision_row = cursor.fetchone()
            if revision_row is None or not isinstance(revision_row[0], str):
                raise RuntimeError("database is missing an Alembic version")
            cursor.execute(
                "SELECT tablename FROM pg_catalog.pg_tables "
                "WHERE schemaname = 'public' ORDER BY tablename"
            )
            for row in cursor.fetchall():
                table_name = str(row[0])
                cursor.execute(
                    sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table_name))
                )
                count_row = cursor.fetchone()
                if count_row is None:
                    raise RuntimeError(f"database did not return a count for {table_name}")
                counts[table_name] = int(count_row[0])
    return revision_row[0], counts


def _drop_restore_database(endpoint: DatabaseEndpoint, target_database: str) -> None:
    _require_restore_target(target_database, endpoint.database)
    with psycopg.connect(endpoint.psycopg_conninfo("postgres"), autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (target_database,),
            )
            cursor.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(target_database))
            )


def _create_restore_database(endpoint: DatabaseEndpoint, target_database: str) -> None:
    _require_restore_target(target_database, endpoint.database)
    with psycopg.connect(endpoint.psycopg_conninfo("postgres"), autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8'").format(
                    sql.Identifier(target_database)
                )
            )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)


def _write_metrics(path: Path, completed_at: datetime, backup_size: int, tables: int) -> None:
    timestamp = completed_at.timestamp()
    lines = [
        "# HELP campaignos_backup_last_success_timestamp_seconds Last verified native backup.",
        "# TYPE campaignos_backup_last_success_timestamp_seconds gauge",
        f"campaignos_backup_last_success_timestamp_seconds {timestamp:.3f}",
        (
            "# HELP campaignos_restore_verification_last_success_timestamp_seconds "
            "Last successful isolated restore proof."
        ),
        "# TYPE campaignos_restore_verification_last_success_timestamp_seconds gauge",
        f"campaignos_restore_verification_last_success_timestamp_seconds {timestamp:.3f}",
        "# HELP campaignos_backup_size_bytes Size of the latest verified native backup.",
        "# TYPE campaignos_backup_size_bytes gauge",
        f"campaignos_backup_size_bytes {backup_size}",
        "# HELP campaignos_backup_verified_tables Public tables compared after restore.",
        "# TYPE campaignos_backup_verified_tables gauge",
        f"campaignos_backup_verified_tables {tables}",
        "",
    ]
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(path)
