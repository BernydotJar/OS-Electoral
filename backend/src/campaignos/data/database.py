"""SQLAlchemy engine and transaction-local tenant scope management."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session, SessionTransaction, sessionmaker


class MissingTenantScope(RuntimeError):
    """Raised before an application transaction starts without tenant scope."""


class DatabaseRuntime(Protocol):
    def readiness(self) -> tuple[bool, str]:
        """Report database dependency readiness without exposing connection details."""

    def dispose(self) -> None:
        """Release local connection-pool resources."""


class UnavailableDatabase:
    def readiness(self) -> tuple[bool, str]:
        return False, "PostgreSQL is not configured"

    def dispose(self) -> None:
        return None


class TenantSession(Session):
    """Session type that requires an immutable tenant identifier."""


@event.listens_for(TenantSession, "after_begin")
def _set_postgresql_tenant_scope(
    session: TenantSession, transaction: SessionTransaction, connection: Connection
) -> None:
    del transaction
    tenant_id = session.info.get("tenant_id")
    if not isinstance(tenant_id, UUID):
        raise MissingTenantScope("tenant-scoped transaction requires a UUID tenant_id")
    if connection.dialect.name == "postgresql":
        connection.execute(
            text("SELECT set_config('campaignos.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )


@dataclass(slots=True)
class Database:
    """Own an engine and create explicitly tenant-scoped unit-of-work sessions."""

    engine: Engine
    _sessions: sessionmaker[TenantSession]

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        pool_size: int = 5,
        max_overflow: int = 5,
        pool_timeout_seconds: int = 5,
    ) -> Database:
        engine_options: dict[str, object] = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }
        if not url.startswith("sqlite"):
            engine_options.update(
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout_seconds,
            )
        engine = create_engine(url, **engine_options)
        sessions = sessionmaker(
            bind=engine,
            class_=TenantSession,
            autoflush=False,
            expire_on_commit=False,
        )
        return cls(engine=engine, _sessions=sessions)

    @contextmanager
    def tenant_transaction(self, tenant_id: UUID) -> Iterator[TenantSession]:
        if not isinstance(tenant_id, UUID):
            raise MissingTenantScope("tenant_transaction requires a UUID tenant_id")
        with self._sessions(info={"tenant_id": tenant_id}) as session:
            with session.begin():
                yield session

    def readiness(self) -> tuple[bool, str]:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception:  # Dependency health must be safe and fail closed.
            return False, "Database connection is unavailable"
        return True, "Database connection is available"

    def dispose(self) -> None:
        self.engine.dispose()
