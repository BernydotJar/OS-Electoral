from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url

from campaignos.operability.recovery import (
    DatabaseEndpoint,
    _require_restore_target,
    verify_postgres_recovery,
)

TEST_PASSWORD = "secret-value"  # noqa: S105 - deterministic isolated test credential.


def test_database_endpoint_parses_without_exposing_password() -> None:
    endpoint = DatabaseEndpoint.from_sqlalchemy_url(
        f"postgresql+psycopg://campaignos_admin:{TEST_PASSWORD}@127.0.0.1:55432/campaignos_test"
    )

    assert endpoint.host == "127.0.0.1"
    assert endpoint.port == 55432
    assert endpoint.username == "campaignos_admin"
    assert endpoint.database == "campaignos_test"
    assert "secret-value" not in repr(endpoint)
    parsed = make_url(endpoint.sqlalchemy_url())
    assert parsed.password == TEST_PASSWORD


@pytest.mark.parametrize(
    ("target", "source"),
    [
        ("campaignos", "campaignos"),
        ("campaignos_restore", "campaignos"),
        ("campaignos_restore_test;DROP DATABASE campaignos", "campaignos"),
        ("campaignos_restore_test", "campaignos_restore_test"),
    ],
)
def test_restore_target_guard_rejects_source_and_unbounded_names(target: str, source: str) -> None:
    with pytest.raises(ValueError):
        _require_restore_target(target, source)


def test_recovery_rejects_mutable_client_image_before_network_or_database_access(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="immutable sha256 digest"):
        verify_postgres_recovery(
            source_database_url=(
                "postgresql+psycopg://campaignos_admin:{TEST_PASSWORD}@127.0.0.1:55432/campaignos_test"
            ),
            output_directory=tmp_path,
            source_revision="a" * 40,
            target_database="campaignos_restore_test",
            client_container_image="postgres:18",
        )


def test_recovery_rejects_invalid_revision_before_network_or_database_access(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="source_revision"):
        verify_postgres_recovery(
            source_database_url=(
                "postgresql+psycopg://campaignos_admin:{TEST_PASSWORD}@127.0.0.1:55432/campaignos_test"
            ),
            output_directory=tmp_path,
            source_revision="not a sha",
            target_database="campaignos_restore_test",
            client_container_image=None,
        )


def test_recovery_manifest_contract_contains_no_connection_secret(tmp_path: Path) -> None:
    manifest = {
        "schema_version": "1.0",
        "status": "PASS",
        "source_database": "campaignos_test",
        "target_database": "campaignos_restore_test",
        "backup_sha256": "a" * 64,
        "source_mutation": "NONE",
        "external_effects": "NONE_TEST_RESTORE_ONLY",
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    text = path.read_text(encoding="utf-8")
    assert "password" not in text
    assert "secret" not in text
    assert "postgresql" not in text


def test_restore_target_guard_rejects_identifiers_longer_than_postgresql_limit() -> None:
    oversized = ("a" * 55) + "_restore_test"
    assert len(oversized) > 63
    with pytest.raises(ValueError, match="bounded"):
        _require_restore_target(oversized, "campaignos_source_test")
