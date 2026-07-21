from __future__ import annotations

from uuid import UUID

import pytest

from campaignos.worker_main import build_parser, run

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")


def test_parser_requires_explicit_tenant_scope() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--once"])


def test_parser_supports_multiple_tenants() -> None:
    args = build_parser().parse_args(
        ["--once", "--tenant-id", str(TENANT_ID), "--tenant-id", str(UUID(int=2))]
    )
    assert args.tenant_ids == [TENANT_ID, UUID(int=2)]


def test_runtime_fails_closed_without_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CAMPAIGNOS_DATABASE_URL", raising=False)
    from campaignos.config import get_settings

    get_settings.cache_clear()
    try:
        with pytest.raises(SystemExit, match="DATABASE_URL"):
            run(["--once", "--tenant-id", str(TENANT_ID)])
    finally:
        get_settings.cache_clear()


def test_runtime_rejects_invalid_operational_limits() -> None:
    with pytest.raises(SystemExit, match="batch-size"):
        run(["--once", "--tenant-id", str(TENANT_ID), "--batch-size", "0"])
    with pytest.raises(SystemExit, match="poll-seconds"):
        run(["--once", "--tenant-id", str(TENANT_ID), "--poll-seconds", "0"])
