from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from campaignos.operability import recovery

PASSWORD = "campaignos-recovery-test-password"  # noqa: S105 - isolated test fixture.
SOURCE_URL = (
    f"postgresql+psycopg://campaignos_admin:{PASSWORD}@127.0.0.1:55432/campaignos_source_test"
)
TARGET = "campaignos_runtime_restore_test"
IMAGE = "postgres:18@sha256:" + ("a" * 64)


def _install_success_fakes(
    monkeypatch: pytest.MonkeyPatch,
    *,
    source_snapshot: tuple[str, dict[str, int]] = ("20260721_0011", {"tenants": 1}),
    target_snapshot: tuple[str, dict[str, int]] = ("20260721_0011", {"tenants": 1}),
) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(recovery, "_server_major", lambda endpoint, database: 18)
    monkeypatch.setattr(recovery, "_client_major", lambda image: 18)
    monkeypatch.setattr(
        recovery,
        "_drop_restore_database",
        lambda endpoint, database: calls.append(("drop", database)),
    )
    monkeypatch.setattr(
        recovery,
        "_create_restore_database",
        lambda endpoint, database: calls.append(("create", database)),
    )

    def dump(endpoint: object, path: Path, image: str | None) -> None:
        del endpoint, image
        calls.append(("dump", path.name))
        path.write_bytes(b"native-postgresql-backup")

    monkeypatch.setattr(recovery, "_dump_database", dump)
    monkeypatch.setattr(
        recovery,
        "_validate_archive",
        lambda endpoint, path, image: calls.append(("validate", path.name)),
    )
    monkeypatch.setattr(
        recovery,
        "_restore_database",
        lambda endpoint, database, path, image: calls.append(("restore", database)),
    )

    def snapshot(endpoint: recovery.DatabaseEndpoint, database: str) -> tuple[str, dict[str, int]]:
        del endpoint
        return source_snapshot if database == "campaignos_source_test" else target_snapshot

    monkeypatch.setattr(recovery, "_snapshot", snapshot)
    return calls


def test_verify_recovery_writes_evidence_and_cleans_target(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = _install_success_fakes(monkeypatch)

    result = recovery.verify_postgres_recovery(
        source_database_url=SOURCE_URL,
        output_directory=tmp_path,
        source_revision="b" * 40,
        target_database=TARGET,
        client_container_image=IMAGE,
    )

    assert result.backup_path.read_bytes() == b"native-postgresql-backup"
    assert result.backup_size_bytes == len(b"native-postgresql-backup")
    assert result.alembic_version == "20260721_0011"
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "PASS"
    assert manifest["postgres_server_major"] == 18
    assert manifest["backup_sha256"] == result.backup_sha256
    assert result.metrics_path.read_text(encoding="utf-8").count("campaignos_backup") >= 3
    assert calls[0] == ("drop", TARGET)
    assert calls[1] == ("create", TARGET)
    assert calls[-1] == ("drop", TARGET)
    assert not list(tmp_path.glob("*.tmp"))


def test_verify_recovery_can_retain_explicit_test_target(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = _install_success_fakes(monkeypatch)

    recovery.verify_postgres_recovery(
        source_database_url=SOURCE_URL,
        output_directory=tmp_path,
        source_revision="c" * 40,
        target_database=TARGET,
        client_container_image=IMAGE,
        keep_restored_database=True,
    )

    assert calls.count(("drop", TARGET)) == 1


def test_verify_recovery_rejects_version_and_row_count_mismatches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _install_success_fakes(
        monkeypatch,
        target_snapshot=("wrong_revision", {"tenants": 1}),
    )
    with pytest.raises(RuntimeError, match="Alembic version"):
        recovery.verify_postgres_recovery(
            source_database_url=SOURCE_URL,
            output_directory=tmp_path / "version",
            source_revision="d" * 40,
            target_database=TARGET,
            client_container_image=IMAGE,
        )

    _install_success_fakes(
        monkeypatch,
        target_snapshot=("20260721_0011", {"tenants": 2}),
    )
    with pytest.raises(RuntimeError, match="row counts"):
        recovery.verify_postgres_recovery(
            source_database_url=SOURCE_URL,
            output_directory=tmp_path / "rows",
            source_revision="e" * 40,
            target_database=TARGET,
            client_container_image=IMAGE,
        )


def test_verify_recovery_rejects_non_test_source_and_client_major_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="isolated .*_test source"):
        recovery.verify_postgres_recovery(
            source_database_url=SOURCE_URL.replace("campaignos_source_test", "campaignos"),
            output_directory=tmp_path,
            source_revision="f" * 40,
            target_database=TARGET,
            client_container_image=IMAGE,
        )

    monkeypatch.setattr(recovery, "_server_major", lambda endpoint, database: 18)
    monkeypatch.setattr(recovery, "_client_major", lambda image: 17)
    with pytest.raises(RuntimeError, match="major versions must match"):
        recovery.verify_postgres_recovery(
            source_database_url=SOURCE_URL,
            output_directory=tmp_path,
            source_revision="f" * 40,
            target_database=TARGET,
            client_container_image=IMAGE,
        )


def test_client_command_and_version_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    assert recovery._client_command("pg_dump", None) == ["pg_dump"]
    container = recovery._client_command("pg_dump", IMAGE)
    assert container[:4] == ["docker", "run", "--rm", "--interactive"]
    assert container[-2:] == [IMAGE, "pg_dump"]

    monkeypatch.setattr(
        recovery,
        "_run_client",
        lambda command, password: subprocess.CompletedProcess(
            command, 0, b"pg_dump (PostgreSQL) 18.3\n"
        ),
    )
    assert recovery._client_major(IMAGE) == 18

    monkeypatch.setattr(
        recovery,
        "_run_client",
        lambda command, password: subprocess.CompletedProcess(command, 0, b"unknown\n"),
    )
    with pytest.raises(RuntimeError, match="determine PostgreSQL client"):
        recovery._client_major(None)


def test_run_client_sanitizes_execution_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError())
    )
    with pytest.raises(RuntimeError, match="executable is unavailable"):
        recovery._run_client(["pg_dump"], password=PASSWORD)

    failure = subprocess.CalledProcessError(1, ["pg_dump"], stderr=b"safe failure")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(failure))
    with pytest.raises(RuntimeError, match="safe failure"):
        recovery._run_client(["pg_dump"], password=PASSWORD)


def test_archive_helpers_build_expected_commands(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    endpoint = recovery.DatabaseEndpoint.from_sqlalchemy_url(SOURCE_URL)
    calls: list[tuple[list[str], object, object]] = []

    def run_client(
        command: list[str],
        *,
        password: str,
        stdin: object = None,
        stdout: object = subprocess.PIPE,
    ) -> subprocess.CompletedProcess[bytes]:
        assert password == PASSWORD
        calls.append((command, stdin, stdout))
        if "--list" in command:
            return subprocess.CompletedProcess(
                command, 0, b"TABLE public tenants\nTABLE DATA alembic_version"
            )
        if stdout is not subprocess.PIPE and hasattr(stdout, "write"):
            stdout.write(b"archive")
        return subprocess.CompletedProcess(command, 0, b"")

    monkeypatch.setattr(recovery, "_run_client", run_client)
    backup = tmp_path / "backup.dump"
    recovery._dump_database(endpoint, backup, IMAGE)
    recovery._validate_archive(endpoint, backup, IMAGE)
    recovery._restore_database(endpoint, TARGET, backup, IMAGE)

    assert backup.read_bytes() == b"archive"
    assert any("--format=custom" in command for command, _, _ in calls)
    assert any("--list" in command for command, _, _ in calls)
    assert any("--exit-on-error" in command for command, _, _ in calls)

    monkeypatch.setattr(
        recovery,
        "_run_client",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, b"empty"),
    )
    with pytest.raises(RuntimeError, match="missing required schema objects"):
        recovery._validate_archive(endpoint, backup, None)
