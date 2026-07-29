from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from time import perf_counter, sleep
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine, make_url

from campaignos.data import Database
from campaignos.data.models import RateLimitBucket
from campaignos.security import (
    RateLimitPolicy,
    RateLimitPolicyCatalog,
    RateLimitPolicyClass,
    SqlAlchemyRateLimiter,
)


def postgres_test_url() -> str:
    value = os.environ.get("CAMPAIGNOS_TEST_DATABASE_URL", "")
    if not value:
        pytest.skip("CAMPAIGNOS_TEST_DATABASE_URL is not configured")
    parsed = make_url(value)
    if parsed.drivername != "postgresql+psycopg" or not (
        parsed.database and parsed.database.endswith("_test")
    ):
        pytest.fail("PostgreSQL integration tests require an isolated *_test database")
    return value


def drop_role(engine: Engine, role_name: str) -> None:
    with engine.begin() as connection:
        exists = bool(
            connection.scalar(
                text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :name)"),
                {"name": role_name},
            )
        )
        if exists:
            connection.execute(text(f'DROP OWNED BY "{role_name}"'))
            connection.execute(text(f'DROP ROLE "{role_name}"'))


def catalog(
    *, limit: int = 5, version: int = 1, window_seconds: int = 3600
) -> RateLimitPolicyCatalog:
    return RateLimitPolicyCatalog(
        policies=tuple(
            RateLimitPolicy(
                policy_class=policy_class,
                version=version,
                request_limit=limit,
                window_seconds=window_seconds,
            )
            for policy_class in RateLimitPolicyClass
        )
    )


@pytest.mark.postgres
def test_rate_limit_postgres_atomicity_rls_rollback_and_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin_url = postgres_test_url()
    monkeypatch.setenv("CAMPAIGNOS_DATABASE_URL", admin_url)
    alembic = Config("alembic.ini")
    command.upgrade(alembic, "head")
    command.check(alembic)

    admin_engine = create_engine(admin_url)
    database_name = make_url(admin_url).database
    assert database_name is not None
    assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*_test", database_name)
    role_name = f"campaignos_rate_limit_{uuid4().hex[:12]}"
    role_password = f"test-{uuid4().hex}"
    drop_role(admin_engine, role_name)

    with admin_engine.begin() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "20260729_0012"
        )
        connection.execute(text("TRUNCATE TABLE rate_limit_buckets"))
        policy = connection.execute(
            text(
                "SELECT permissive, roles, cmd, qual, with_check "
                "FROM pg_policies WHERE schemaname = 'public' "
                "AND tablename = 'rate_limit_buckets' "
                "AND policyname = 'tenant_isolation'"
            )
        ).one()
        assert policy.permissive == "PERMISSIVE"
        assert policy.cmd == "ALL"
        assert "campaignos.tenant_id" in policy.qual
        assert "campaignos.tenant_id" in policy.with_check
        forced = connection.scalar(
            text(
                "SELECT relforcerowsecurity FROM pg_class "
                "WHERE oid = 'public.rate_limit_buckets'::regclass"
            )
        )
        assert forced is True
        connection.execute(
            text(
                f"CREATE ROLE \"{role_name}\" LOGIN PASSWORD '{role_password}' "
                "NOSUPERUSER NOBYPASSRLS"
            )
        )
        connection.execute(text(f'GRANT CONNECT ON DATABASE "{database_name}" TO "{role_name}"'))
        connection.execute(text(f'GRANT USAGE ON SCHEMA public TO "{role_name}"'))
        connection.execute(
            text(f'GRANT SELECT, INSERT, UPDATE, DELETE ON rate_limit_buckets TO "{role_name}"')
        )

    application_url = make_url(admin_url).set(username=role_name, password=role_password)
    database = Database.from_url(
        application_url.render_as_string(hide_password=False),
        pool_size=12,
        max_overflow=12,
        pool_timeout_seconds=10,
    )
    limiter = SqlAlchemyRateLimiter(database, catalog())
    tenant_a = uuid4()
    tenant_b = uuid4()
    principal_a = uuid4()
    principal_b = uuid4()

    try:
        burst_started = perf_counter()
        with ThreadPoolExecutor(max_workers=20) as executor:
            decisions = list(
                executor.map(
                    lambda _: limiter.consume(
                        tenant_a,
                        principal_a,
                        RateLimitPolicyClass.MUTATION,
                    ),
                    range(20),
                )
            )
        burst_duration = perf_counter() - burst_started
        assert burst_duration < 10
        assert sum(decision.allowed for decision in decisions) == 5
        assert sum(not decision.allowed for decision in decisions) == 15
        assert all(decision.retry_after_seconds == 0 for decision in decisions if decision.allowed)
        assert all(
            1 <= decision.retry_after_seconds <= 3600
            for decision in decisions
            if not decision.allowed
        )

        with database.tenant_transaction(tenant_a) as session:
            mutation_bucket = session.scalar(
                select(RateLimitBucket).where(
                    RateLimitBucket.principal_id == principal_a,
                    RateLimitBucket.policy_class == RateLimitPolicyClass.MUTATION.value,
                    RateLimitBucket.policy_version == 1,
                )
            )
            assert mutation_bucket is not None
            assert mutation_bucket.request_count == 6
            assert session.scalar(select(func.count()).select_from(RateLimitBucket)) == 1

        assert limiter.consume(tenant_a, principal_b, RateLimitPolicyClass.MUTATION).allowed
        assert limiter.consume(tenant_a, principal_a, RateLimitPolicyClass.READ).allowed
        assert limiter.consume(tenant_b, principal_a, RateLimitPolicyClass.MUTATION).allowed

        with database.tenant_transaction(tenant_a) as session:
            visible = set(
                session.execute(
                    select(
                        RateLimitBucket.tenant_id,
                        RateLimitBucket.principal_id,
                        RateLimitBucket.policy_class,
                    )
                ).all()
            )
            assert visible == {
                (tenant_a, principal_a, RateLimitPolicyClass.MUTATION.value),
                (tenant_a, principal_b, RateLimitPolicyClass.MUTATION.value),
                (tenant_a, principal_a, RateLimitPolicyClass.READ.value),
            }
        with database.tenant_transaction(tenant_b) as session:
            visible = session.execute(
                select(
                    RateLimitBucket.tenant_id,
                    RateLimitBucket.principal_id,
                    RateLimitBucket.policy_class,
                )
            ).all()
            assert visible == [(tenant_b, principal_a, RateLimitPolicyClass.MUTATION.value)]

        rollover_principal = uuid4()
        one_second = SqlAlchemyRateLimiter(database, catalog(limit=1, version=77, window_seconds=1))
        assert one_second.consume(tenant_a, rollover_principal, RateLimitPolicyClass.READ).allowed
        assert not one_second.consume(
            tenant_a, rollover_principal, RateLimitPolicyClass.READ
        ).allowed
        sleep(1.1)
        assert one_second.consume(tenant_a, rollover_principal, RateLimitPolicyClass.READ).allowed
        with database.tenant_transaction(tenant_a) as session:
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(RateLimitBucket)
                    .where(
                        RateLimitBucket.principal_id == rollover_principal,
                        RateLimitBucket.policy_version == 77,
                    )
                )
                == 2
            )

        version_two = SqlAlchemyRateLimiter(database, catalog(version=2))
        assert version_two.consume(tenant_a, principal_a, RateLimitPolicyClass.MUTATION).allowed
        with database.tenant_transaction(tenant_a) as session:
            versions = set(
                session.scalars(
                    select(RateLimitBucket.policy_version).where(
                        RateLimitBucket.principal_id == principal_a,
                        RateLimitBucket.policy_class == RateLimitPolicyClass.MUTATION.value,
                    )
                )
            )
            assert versions == {1, 2}

        rollback_principal = uuid4()
        decision = limiter.consume(tenant_a, rollback_principal, RateLimitPolicyClass.READ)
        assert decision.allowed
        with pytest.raises(RuntimeError, match="force domain rollback"):
            with database.tenant_transaction(tenant_a):
                raise RuntimeError("force domain rollback")
        with database.tenant_transaction(tenant_a) as session:
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(RateLimitBucket)
                    .where(RateLimitBucket.principal_id == rollback_principal)
                )
                == 1
            )

        stale_a = uuid4()
        stale_b = uuid4()
        stale_window = datetime.now(UTC) - timedelta(days=2)
        with admin_engine.begin() as connection:
            for tenant_id, principal_id in ((tenant_a, stale_a), (tenant_b, stale_b)):
                connection.execute(
                    text(
                        "INSERT INTO rate_limit_buckets ("
                        "tenant_id, principal_id, policy_class, policy_version, "
                        "window_start, window_seconds, request_count, updated_at"
                        ") VALUES ("
                        ":tenant_id, :principal_id, 'read', 99, :window_start, 60, 1, :updated_at"
                        ")"
                    ),
                    {
                        "tenant_id": tenant_id,
                        "principal_id": principal_id,
                        "window_start": stale_window,
                        "updated_at": stale_window,
                    },
                )
        assert (
            limiter.cleanup_expired(
                tenant_a,
                before=datetime.now(UTC) - timedelta(hours=1),
                batch_size=1,
            )
            == 1
        )
        with admin_engine.begin() as connection:
            remaining = set(
                connection.execute(
                    text(
                        "SELECT tenant_id, principal_id FROM rate_limit_buckets "
                        "WHERE policy_version = 99"
                    )
                ).all()
            )
            assert remaining == {(tenant_b, stale_b)}

        with pytest.raises(ValueError, match="include a timezone"):
            limiter.cleanup_expired(
                tenant_a,
                before=datetime.now(),
                batch_size=1,
            )
        with pytest.raises(ValueError, match="between 1 and 1000"):
            limiter.cleanup_expired(
                tenant_a,
                before=datetime.now(UTC),
                batch_size=0,
            )
    finally:
        database.dispose()
        drop_role(admin_engine, role_name)
        admin_engine.dispose()
