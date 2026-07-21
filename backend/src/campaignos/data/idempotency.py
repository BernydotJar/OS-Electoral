"""Transaction-scoped serialization for durable idempotency keys."""

from __future__ import annotations

import hashlib
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def lock_idempotency_key(
    session: Session,
    *,
    tenant_id: UUID,
    operation: str,
    idempotency_key: str,
) -> None:
    """Serialize one tenant/operation/key tuple inside a PostgreSQL transaction.

    The idempotency table unique constraint is the final integrity boundary. This
    advisory transaction lock removes the check-then-insert race so concurrent
    equal keys observe the committed record and replay deterministically.
    """
    bind = session.get_bind()
    if bind.dialect.name != "postgresql":
        return
    digest = hashlib.sha256(f"{tenant_id}:{operation}:{idempotency_key}".encode()).digest()
    lock_id = int.from_bytes(digest[:8], byteorder="big", signed=True)
    session.execute(
        text("SELECT pg_advisory_xact_lock(:lock_id)"),
        {"lock_id": lock_id},
    )
