from __future__ import annotations

from typing import Self

import pytest

from campaignos.performance import executor as executor_module


class FakeAdminConnection:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def scalar(self, statement):  # type: ignore[no-untyped-def]
        self.statements.append(str(statement))
        return "18.3 (verification build)"

    def execute(self, statement):  # type: ignore[no-untyped-def]
        self.statements.append(str(statement))
        return None


class FakeAdminEngine:
    def __init__(self) -> None:
        self.connection = FakeAdminConnection()
        self.disposed = False

    def begin(self) -> Self:
        return self

    def __enter__(self) -> FakeAdminConnection:
        return self.connection

    def __exit__(self, exc_type, exc, traceback) -> bool:  # type: ignore[no-untyped-def]
        del exc_type, exc, traceback
        return False

    def dispose(self) -> None:
        self.disposed = True


class FakeTenantSession:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute(self, statement, parameters=None):  # type: ignore[no-untyped-def]
        self.statements.append(str(statement))
        del parameters
        return None

    def scalar(self, statement):  # type: ignore[no-untyped-def]
        self.statements.append(str(statement))
        return 0


class FakeTenantTransaction:
    def __init__(self, session: FakeTenantSession) -> None:
        self.session = session

    def __enter__(self) -> FakeTenantSession:
        return self.session

    def __exit__(self, exc_type, exc, traceback) -> bool:  # type: ignore[no-untyped-def]
        del exc_type, exc, traceback
        return False


class FakeDatabaseInstance:
    def __init__(self) -> None:
        self.session = FakeTenantSession()
        self.disposed = False

    def pool_snapshot(self) -> dict[str, int]:
        return {"size": 20, "checked_in": 20, "checked_out": 0, "overflow": 0}

    def tenant_transaction(self, tenant_id):  # type: ignore[no-untyped-def]
        del tenant_id
        return FakeTenantTransaction(self.session)

    def dispose(self) -> None:
        self.disposed = True


class FakeDatabaseFactory:
    instance = FakeDatabaseInstance()

    @classmethod
    def from_url(cls, url: str, **kwargs):  # type: ignore[no-untyped-def]
        assert "campaignos_perf_" in url
        assert kwargs == {"pool_size": 20, "max_overflow": 0, "pool_timeout_seconds": 5}
        return cls.instance


class FailingDatabaseFactory:
    @classmethod
    def from_url(cls, url: str, **kwargs):  # type: ignore[no-untyped-def]
        del cls, url, kwargs
        raise RuntimeError("pool construction failed")


def test_postgres_runtime_creates_and_revokes_least_privilege_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin = FakeAdminEngine()
    fake_database = FakeDatabaseInstance()
    FakeDatabaseFactory.instance = fake_database
    monkeypatch.setattr(executor_module, "create_engine", lambda *args, **kwargs: admin)
    monkeypatch.setattr(executor_module, "Database", FakeDatabaseFactory)

    runtime = executor_module._PostgresRuntime(
        "postgresql+psycopg://admin:local@127.0.0.1/campaignos_perf_test"
    )

    assert runtime.server_version == "18.3"
    assert runtime.pool_snapshot().checked_out == 0
    assert runtime.clear_buckets() == 0
    assert runtime.count_buckets() == 0
    runtime.insert_stale_buckets(2)
    assert (
        sum("INSERT INTO rate_limit_buckets" in item for item in fake_database.session.statements)
        == 2
    )

    runtime.close()

    statements = "\n".join(admin.connection.statements)
    assert "NOSUPERUSER NOBYPASSRLS" in statements
    assert "statement_timeout" in statements
    assert "lock_timeout" in statements
    assert "DROP OWNED BY" in statements
    assert "DROP ROLE" in statements
    assert fake_database.disposed is True
    assert admin.disposed is True


def test_postgres_runtime_revokes_role_after_partial_initialization_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin = FakeAdminEngine()
    monkeypatch.setattr(executor_module, "create_engine", lambda *args, **kwargs: admin)
    monkeypatch.setattr(executor_module, "Database", FailingDatabaseFactory)

    with pytest.raises(RuntimeError, match="pool construction failed"):
        executor_module._PostgresRuntime(
            "postgresql+psycopg://admin:local@127.0.0.1/campaignos_perf_test"
        )

    statements = "\n".join(admin.connection.statements)
    assert "CREATE ROLE" in statements
    assert "DROP OWNED BY" in statements
    assert "DROP ROLE" in statements
    assert admin.disposed is True


def test_postgres_runtime_rejects_non_test_database() -> None:
    with pytest.raises(ValueError, match="isolated PostgreSQL"):
        executor_module._PostgresRuntime("postgresql+psycopg://admin:local@127.0.0.1/campaignos")
