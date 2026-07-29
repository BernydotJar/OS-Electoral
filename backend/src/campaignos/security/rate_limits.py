"""PostgreSQL-backed tenant/principal rate limiting with bounded observability."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Final, Protocol, TypeVar, cast
from uuid import UUID, uuid5

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from campaignos.config import Settings
from campaignos.data import Database
from campaignos.identity.models import AuthenticatedPrincipal
from campaignos.security.rate_limit_contracts import (
    RateLimitDecision,
    RateLimitPolicy,
    RateLimitPolicyCatalog,
    RateLimitPolicyClass,
)

RATE_LIMIT_POLICY_ATTRIBUTE: Final = "__campaignos_rate_limit_policy__"
PREAUTH_SCOPE_TENANT_ID: Final = UUID("00000000-0000-5000-8000-000000000001")
PREAUTH_PRINCIPAL_NAMESPACE: Final = UUID("3c129df3-887a-5e8c-a5a7-0c4db4f502a4")
OPERATIONAL_METRICS_PRINCIPAL_ID: Final = UUID("00000000-0000-5000-8000-000000000002")
Endpoint = TypeVar("Endpoint", bound=Callable[..., object])


class RateLimitStoreUnavailable(RuntimeError):
    """Raised when a required rate-limit decision cannot be persisted."""


class RateLimiter(Protocol):
    """Consume one server-owned operation budget."""

    def consume(
        self,
        tenant_id: UUID,
        principal_id: UUID,
        policy_class: RateLimitPolicyClass,
    ) -> RateLimitDecision:
        """Return an allow/deny decision or fail closed."""


class DisabledRateLimiter:
    """Explicit development/test-only no-op selected by validated settings."""

    def __init__(self, catalog: RateLimitPolicyCatalog) -> None:
        self._catalog = catalog

    def consume(
        self,
        tenant_id: UUID,
        principal_id: UUID,
        policy_class: RateLimitPolicyClass,
    ) -> RateLimitDecision:
        del tenant_id, principal_id
        policy = self._catalog.policy_for(policy_class)
        return RateLimitDecision(
            allowed=True,
            policy_class=policy.policy_class,
            retry_after_seconds=0,
            policy_version=policy.version,
        )


class UnavailableRateLimiter:
    """Fail-closed boundary used when enforcement is enabled without a usable store."""

    def consume(
        self,
        tenant_id: UUID,
        principal_id: UUID,
        policy_class: RateLimitPolicyClass,
    ) -> RateLimitDecision:
        del tenant_id, principal_id, policy_class
        raise RateLimitStoreUnavailable("Rate-limit store is unavailable")


class SqlAlchemyRateLimiter:
    """Atomic fixed-window counter implemented with PostgreSQL UPSERT."""

    _CONSUME = text(
        """
        WITH clock AS (
            SELECT
                transaction_timestamp() AS observed_at,
                to_timestamp(
                    floor(
                        extract(epoch FROM transaction_timestamp())
                        / CAST(:window_seconds AS integer)
                    ) * CAST(:window_seconds AS integer)
                ) AS window_start
        ),
        consumed AS (
            INSERT INTO rate_limit_buckets (
                tenant_id,
                principal_id,
                policy_class,
                policy_version,
                window_start,
                window_seconds,
                request_count,
                updated_at
            )
            SELECT
                CAST(:tenant_id AS uuid),
                CAST(:principal_id AS uuid),
                :policy_class,
                :policy_version,
                clock.window_start,
                :window_seconds,
                1,
                clock.observed_at
            FROM clock
            ON CONFLICT (
                tenant_id,
                principal_id,
                policy_class,
                policy_version,
                window_start
            ) DO UPDATE
            SET
                request_count = LEAST(
                    rate_limit_buckets.request_count + 1,
                    CAST(:counter_cap AS integer)
                ),
                window_seconds = EXCLUDED.window_seconds,
                updated_at = EXCLUDED.updated_at
            RETURNING request_count, window_start, window_seconds
        )
        SELECT
            consumed.request_count,
            GREATEST(
                1,
                CEIL(
                    EXTRACT(
                        EPOCH FROM (
                            consumed.window_start
                            + make_interval(secs => consumed.window_seconds)
                            - transaction_timestamp()
                        )
                    )
                )
            )::integer AS retry_after_seconds
        FROM consumed
        """
    )
    _CLEANUP = text(
        """
        WITH expired AS (
            SELECT bucket.ctid
            FROM rate_limit_buckets AS bucket
            WHERE bucket.tenant_id = CAST(:tenant_id AS uuid)
              AND bucket.window_start + make_interval(secs => bucket.window_seconds) < :before
            ORDER BY bucket.window_start ASC
            LIMIT :batch_size
            FOR UPDATE SKIP LOCKED
        )
        DELETE FROM rate_limit_buckets AS bucket
        USING expired
        WHERE bucket.ctid = expired.ctid
        RETURNING 1
        """
    )

    def __init__(self, database: Database, catalog: RateLimitPolicyCatalog) -> None:
        self._database = database
        self._catalog = catalog

    def consume(
        self,
        tenant_id: UUID,
        principal_id: UUID,
        policy_class: RateLimitPolicyClass,
    ) -> RateLimitDecision:
        """Commit one budget before domain execution so later rollback cannot refund it."""
        policy = self._catalog.policy_for(policy_class)
        try:
            with self._database.tenant_transaction(tenant_id) as session:
                row = (
                    session.execute(
                        self._CONSUME,
                        {
                            "tenant_id": str(tenant_id),
                            "principal_id": str(principal_id),
                            "policy_class": policy.policy_class.value,
                            "policy_version": policy.version,
                            "window_seconds": policy.window_seconds,
                            "counter_cap": policy.request_limit + 1,
                        },
                    )
                    .mappings()
                    .one()
                )
        except SQLAlchemyError as exc:
            raise RateLimitStoreUnavailable("Rate-limit store is unavailable") from exc
        request_count = cast(int, row["request_count"])
        retry_after = cast(int, row["retry_after_seconds"])
        allowed = request_count <= policy.request_limit
        return RateLimitDecision(
            allowed=allowed,
            policy_class=policy.policy_class,
            retry_after_seconds=0 if allowed else retry_after,
            policy_version=policy.version,
        )

    def cleanup_expired(
        self,
        tenant_id: UUID,
        *,
        before: datetime,
        batch_size: int,
    ) -> int:
        """Delete one bounded tenant-scoped batch outside the request path."""
        if before.utcoffset() is None:
            raise ValueError("Rate-limit cleanup cutoff must include a timezone")
        if batch_size < 1 or batch_size > 1_000:
            raise ValueError("Rate-limit cleanup batch size must be between 1 and 1000")
        try:
            with self._database.tenant_transaction(tenant_id) as session:
                rows = session.execute(
                    self._CLEANUP,
                    {
                        "tenant_id": str(tenant_id),
                        "before": before,
                        "batch_size": batch_size,
                    },
                ).all()
                return len(rows)
        except SQLAlchemyError as exc:
            raise RateLimitStoreUnavailable("Rate-limit cleanup store is unavailable") from exc


def policy_catalog_from_settings(settings: Settings) -> RateLimitPolicyCatalog:
    """Build the complete immutable policy catalog from validated settings."""
    version = settings.rate_limit_policy_version
    return RateLimitPolicyCatalog(
        policies=(
            RateLimitPolicy(
                policy_class=RateLimitPolicyClass.READ,
                version=version,
                request_limit=settings.rate_limit_read_requests,
                window_seconds=settings.rate_limit_read_window_seconds,
            ),
            RateLimitPolicy(
                policy_class=RateLimitPolicyClass.MUTATION,
                version=version,
                request_limit=settings.rate_limit_mutation_requests,
                window_seconds=settings.rate_limit_mutation_window_seconds,
            ),
            RateLimitPolicy(
                policy_class=RateLimitPolicyClass.EXPENSIVE_READ,
                version=version,
                request_limit=settings.rate_limit_expensive_read_requests,
                window_seconds=settings.rate_limit_expensive_read_window_seconds,
            ),
            RateLimitPolicy(
                policy_class=RateLimitPolicyClass.IDENTITY_LIFECYCLE,
                version=version,
                request_limit=settings.rate_limit_identity_requests,
                window_seconds=settings.rate_limit_identity_window_seconds,
            ),
            RateLimitPolicy(
                policy_class=RateLimitPolicyClass.GOVERNED_AGENT,
                version=version,
                request_limit=settings.rate_limit_agent_requests,
                window_seconds=settings.rate_limit_agent_window_seconds,
            ),
        )
    )


def rate_limit_policy(policy_class: RateLimitPolicyClass) -> Callable[[Endpoint], Endpoint]:
    """Attach reviewed policy metadata without wrapping the FastAPI endpoint."""

    def decorate(endpoint: Endpoint) -> Endpoint:
        setattr(endpoint, RATE_LIMIT_POLICY_ATTRIBUTE, policy_class)
        return endpoint

    return decorate


def declared_rate_limit_policy(endpoint: object) -> RateLimitPolicyClass | None:
    value = getattr(endpoint, RATE_LIMIT_POLICY_ATTRIBUTE, None)
    return value if isinstance(value, RateLimitPolicyClass) else None


def preauth_principal_id(principal: AuthenticatedPrincipal) -> UUID:
    """Derive a stable opaque UUID without persisting issuer, subject, email or token."""
    return uuid5(PREAUTH_PRINCIPAL_NAMESPACE, f"{principal.issuer}\x1f{principal.subject}")
