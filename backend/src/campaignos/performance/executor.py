"""CampaignOS HTTP and PostgreSQL executor for the bounded verification catalog."""

from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime, timedelta
from threading import Lock
from time import monotonic_ns
from typing import Any, Protocol, cast
from uuid import UUID, uuid4, uuid5

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url

from campaignos.agents import UnavailableAgentRunService
from campaignos.api.app import create_app
from campaignos.campaigns import (
    CampaignCreator,
    CampaignReadinessInput,
    CampaignReadinessReader,
    InMemoryCampaignCreator,
    InMemoryCampaignReadinessReader,
)
from campaignos.config import Environment, Settings
from campaignos.data import Database
from campaignos.data.models import RateLimitBucket
from campaignos.identity import (
    AuthenticatedPrincipal,
    EffectiveMembership,
    EffectivePermissionGrant,
    TenantAccessDenied,
    TenantAuthorizationContext,
)
from campaignos.identity.lifecycle import IdentityLifecycle
from campaignos.identity.lifecycle_contracts import SessionEvidence, SessionProjection
from campaignos.identity.oidc import AuthenticationError
from campaignos.performance.contracts import (
    CleanupResult,
    OperationResult,
    PoolSnapshot,
    ScenarioId,
    WorkloadScenario,
)
from campaignos.security import (
    RateLimitDecision,
    RateLimitPolicy,
    RateLimitPolicyCatalog,
    RateLimitPolicyClass,
    SqlAlchemyRateLimiter,
    UnavailableRateLimiter,
    policy_catalog_from_settings,
)
from campaignos.security.rate_limits import PREAUTH_SCOPE_TENANT_ID


class _HttpResponse(Protocol):
    status_code: int

    def json(self) -> Any: ...


TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("11111111-1111-4111-8111-111111111112")
PRINCIPAL_ID = UUID("22222222-2222-4222-8222-222222222222")
MEMBERSHIP_ID = UUID("33333333-3333-4333-8333-333333333333")
CAMPAIGN_ID = UUID("44444444-4444-4444-8444-444444444444")
NAMESPACE = UUID("55555555-5555-4555-8555-555555555555")
ACCESS_TOKEN = "campaignos-performance-token"  # noqa: S105 - local deterministic fixture.


class _Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        if token != ACCESS_TOKEN:
            raise AuthenticationError("Invalid local verification token")
        now = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)
        return AuthenticatedPrincipal(
            subject="performance-operator",
            issuer="https://identity.example.test/",
            audience="campaignos-performance",
            authenticated_at=now,
            expires_at=now + timedelta(hours=8),
        )

    def readiness(self) -> tuple[bool, str]:
        return True, "Local verification identity is ready"


class _Directory:
    def load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        *,
        evaluated_at: datetime | None = None,
    ) -> TenantAuthorizationContext:
        del principal
        if tenant_id != TENANT_ID:
            raise TenantAccessDenied("Tenant access is not authorized")
        grants = (
            self._grant(
                "create",
                "campaign_collection",
                str(TENANT_ID),
                "Create tenant campaign",
                campaign_id=None,
            ),
            self._grant(
                "read",
                "campaign_readiness",
                str(CAMPAIGN_ID),
                "Assess assigned campaign readiness",
                campaign_id=CAMPAIGN_ID,
            ),
            self._grant(
                "create",
                "agent_run",
                str(CAMPAIGN_ID),
                "Create internal governed recommendation run",
                campaign_id=CAMPAIGN_ID,
            ),
        )
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=evaluated_at or datetime.now(UTC),
            memberships=(
                EffectiveMembership(
                    membership_id=MEMBERSHIP_ID,
                    campaign_id=None,
                    roles=("review_operator",),
                    grants=grants,
                ),
            ),
        )

    @staticmethod
    def _grant(
        action: str,
        resource_type: str,
        resource_id: str,
        purpose: str,
        *,
        campaign_id: UUID | None,
    ) -> EffectivePermissionGrant:
        grant_id = uuid5(NAMESPACE, f"{action}:{resource_type}:{resource_id}:{purpose}")
        return EffectivePermissionGrant(
            grant_id=grant_id,
            campaign_id=campaign_id,
            workspace_id=None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            purpose=purpose,
            approval_receipt_id="performance-local-approval",
        )


class _LockedCampaignCreator:
    def __init__(self) -> None:
        self._delegate = InMemoryCampaignCreator()
        self._lock = Lock()

    def create(self, tenant_id: UUID, **kwargs: object):  # type: ignore[no-untyped-def]
        with self._lock:
            return self._delegate.create(tenant_id, **kwargs)  # type: ignore[arg-type]


class _LockedReadinessReader:
    def __init__(self) -> None:
        source = CampaignReadinessInput(
            tenant_id=TENANT_ID,
            campaign_id=CAMPAIGN_ID,
            campaign_version=1,
            campaign_status="DRAFT",
            name="Verification campaign",
            jurisdiction="Verification jurisdiction",
            stage="PREPARATION",
            active_workspace_count=1,
        )
        self._delegate = InMemoryCampaignReadinessReader(
            snapshots={(TENANT_ID, CAMPAIGN_ID): source}
        )
        self._lock = Lock()

    def get(self, tenant_id: UUID, campaign_id: UUID, **kwargs: object):  # type: ignore[no-untyped-def]
        with self._lock:
            return self._delegate.get(tenant_id, campaign_id, **kwargs)  # type: ignore[arg-type]


class _SessionLifecycle:
    def register_session(
        self,
        tenant_id: UUID,
        *,
        principal: AuthenticatedPrincipal,
        application_principal_id: UUID,
        correlation_id: str,
    ) -> SessionEvidence:
        del correlation_id
        now = datetime.now(UTC)
        return SessionEvidence(
            session=SessionProjection(
                id=uuid4(),
                tenant_id=tenant_id,
                principal_id=application_principal_id,
                status="ACTIVE",
                authenticated_at=principal.authenticated_at,
                last_seen_at=now,
                expires_at=now + timedelta(hours=1),
                revoked_at=None,
                revocation_reason=None,
                version=1,
            ),
            audit_event_id=uuid4(),
            created=True,
        )


class _RecordingRateLimiter:
    """Record sanitized scope/policy calls while returning deterministic allows."""

    def __init__(self, catalog: RateLimitPolicyCatalog) -> None:
        self._catalog = catalog
        self._lock = Lock()
        self._calls: list[tuple[str, RateLimitPolicyClass]] = []

    def consume(
        self,
        tenant_id: UUID,
        principal_id: UUID,
        policy_class: RateLimitPolicyClass,
    ) -> RateLimitDecision:
        del principal_id
        scope = "preauth" if tenant_id == PREAUTH_SCOPE_TENANT_ID else "tenant"
        with self._lock:
            self._calls.append((scope, policy_class))
        policy = self._catalog.policy_for(policy_class)
        return RateLimitDecision(
            allowed=True,
            policy_class=policy.policy_class,
            retry_after_seconds=0,
            policy_version=policy.version,
        )

    def reset(self) -> None:
        with self._lock:
            self._calls.clear()

    def snapshot(self) -> tuple[tuple[str, RateLimitPolicyClass], ...]:
        with self._lock:
            return tuple(self._calls)


class _PostgresRuntime:
    def __init__(self, admin_url: str, *, role_name: str | None = None) -> None:
        parsed = make_url(admin_url)
        if parsed.drivername != "postgresql+psycopg" or not (
            parsed.database and parsed.database.endswith("_test")
        ):
            raise ValueError(
                "performance verification requires an isolated PostgreSQL *_test database"
            )
        self.admin_engine = create_engine(admin_url, pool_pre_ping=True)
        self.role_name = role_name or f"campaignos_perf_{uuid4().hex[:12]}"
        self.role_password = uuid4().hex
        if not re.fullmatch(r"campaignos_perf_[0-9a-f]{12}", self.role_name):
            raise ValueError("generated database role is invalid")
        role_created = False
        database: Database | None = None
        try:
            with self.admin_engine.begin() as connection:
                server_version = str(connection.scalar(text("SHOW server_version")))
                matched = re.match(r"^(\d+(?:\.\d+){0,2})", server_version)
                if matched is None:
                    raise ValueError("PostgreSQL version could not be normalized")
                self.server_version = matched.group(1)
                connection.execute(
                    text(
                        f"CREATE ROLE \"{self.role_name}\" LOGIN PASSWORD '{self.role_password}' "
                        "NOSUPERUSER NOBYPASSRLS"
                    )
                )
                role_created = True
                database_name = parsed.database
                connection.execute(
                    text(f'GRANT CONNECT ON DATABASE "{database_name}" TO "{self.role_name}"')
                )
                connection.execute(text(f'GRANT USAGE ON SCHEMA public TO "{self.role_name}"'))
                connection.execute(
                    text(
                        f"GRANT SELECT, INSERT, UPDATE, DELETE ON rate_limit_buckets "
                        f'TO "{self.role_name}"'
                    )
                )
                connection.execute(
                    text(f"ALTER ROLE \"{self.role_name}\" SET statement_timeout = '5s'")
                )
                connection.execute(text(f"ALTER ROLE \"{self.role_name}\" SET lock_timeout = '2s'"))
            app_url = parsed.set(username=self.role_name, password=self.role_password)
            database = Database.from_url(
                app_url.render_as_string(hide_password=False),
                pool_size=20,
                max_overflow=0,
                pool_timeout_seconds=5,
            )
            catalog = RateLimitPolicyCatalog(
                policies=tuple(
                    RateLimitPolicy(
                        policy_class=policy_class,
                        version=9001,
                        request_limit=5,
                        window_seconds=3600,
                    )
                    for policy_class in RateLimitPolicyClass
                )
            )
            self.database = database
            self.limiter = SqlAlchemyRateLimiter(self.database, catalog)
        except Exception:
            if database is not None:
                database.dispose()
            if role_created:
                self._drop_role()
            self.admin_engine.dispose()
            raise

    def _drop_role(self) -> None:
        with self.admin_engine.begin() as connection:
            connection.execute(text(f'DROP OWNED BY "{self.role_name}"'))
            connection.execute(text(f'DROP ROLE "{self.role_name}"'))

    def pool_snapshot(self) -> PoolSnapshot:
        values = self.database.pool_snapshot()
        return PoolSnapshot(
            size=values.get("size", 0),
            checked_in=values.get("checked_in", 0),
            checked_out=values.get("checked_out", 0),
            overflow=values.get("overflow", 0),
        )

    def clear_buckets(self) -> int:
        with self.database.tenant_transaction(TENANT_ID) as session:
            session.execute(text("DELETE FROM rate_limit_buckets"))
            remaining = session.scalar(select(func.count()).select_from(RateLimitBucket))
            return int(remaining or 0)

    def count_buckets(self) -> int:
        with self.database.tenant_transaction(TENANT_ID) as session:
            return int(session.scalar(select(func.count()).select_from(RateLimitBucket)) or 0)

    def insert_stale_buckets(self, count: int) -> None:
        stale = datetime.now(UTC) - timedelta(days=2)
        with self.database.tenant_transaction(TENANT_ID) as session:
            for index in range(count):
                session.execute(
                    text(
                        "INSERT INTO rate_limit_buckets ("
                        "tenant_id, principal_id, policy_class, policy_version, "
                        "window_start, window_seconds, request_count, updated_at"
                        ") VALUES ("
                        ":tenant_id, :principal_id, 'read', 9901, :window_start, 60, 1, "
                        ":updated_at)"
                    ),
                    {
                        "tenant_id": str(TENANT_ID),
                        "principal_id": str(uuid5(NAMESPACE, f"stale:{index}")),
                        "window_start": stale,
                        "updated_at": stale,
                    },
                )

    def close(self) -> None:
        try:
            self.clear_buckets()
        finally:
            self.database.dispose()
            try:
                self._drop_role()
            finally:
                self.admin_engine.dispose()


def cleanup_verification_role(admin_url: str, role_name: str) -> None:
    """Idempotently revoke a supervised verification role after abnormal exit."""

    parsed = make_url(admin_url)
    if parsed.drivername != "postgresql+psycopg" or not (
        parsed.database and parsed.database.endswith("_test")
    ):
        raise ValueError("role cleanup requires an isolated PostgreSQL *_test database")
    if not re.fullmatch(r"campaignos_perf_[0-9a-f]{12}", role_name):
        raise ValueError("verification role name is invalid")
    engine = create_engine(admin_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            exists = bool(
                connection.scalar(
                    text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :role_name)"),
                    {"role_name": role_name},
                )
            )
            if not exists:
                return
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE usename = :role_name AND pid <> pg_backend_pid()"
                ),
                {"role_name": role_name},
            )
            connection.execute(text(f'DROP OWNED BY "{role_name}"'))
            connection.execute(text(f'DROP ROLE "{role_name}"'))
    finally:
        engine.dispose()


class CampaignOSLoadExecutor:
    """Execute the reviewed catalog without outbound providers or production effects."""

    def __init__(self, database_url: str, *, role_name: str | None = None) -> None:
        self._postgres = _PostgresRuntime(database_url, role_name=role_name)
        settings = Settings(environment=Environment.TEST, expose_api_docs=False)
        self._recording_limiter = _RecordingRateLimiter(policy_catalog_from_settings(settings))
        verifier = _Verifier()
        directory = _Directory()
        self._allowed_app = create_app(
            settings,
            token_verifier=verifier,
            membership_directory=directory,
            identity_lifecycle=cast(IdentityLifecycle, _SessionLifecycle()),
            campaign_creator=cast(CampaignCreator, _LockedCampaignCreator()),
            campaign_readiness_reader=cast(CampaignReadinessReader, _LockedReadinessReader()),
            agent_run_service=UnavailableAgentRunService(),
            rate_limiter=self._recording_limiter,
        )
        self._unavailable_app = create_app(
            settings,
            token_verifier=verifier,
            membership_directory=directory,
            rate_limiter=UnavailableRateLimiter(),
        )
        self._prepared: ScenarioId | None = None

    @property
    def postgresql_version(self) -> str:
        return self._postgres.server_version

    def prepare(self, scenario: WorkloadScenario) -> None:
        self._prepared = scenario.scenario_id
        self._recording_limiter.reset()
        if scenario.scenario_id in {
            ScenarioId.RATE_LIMIT_CONTENTION,
            ScenarioId.DOMAIN_ROLLBACK_ACCOUNTING,
            ScenarioId.CLEANUP,
        }:
            residue = self._postgres.clear_buckets()
            if residue:
                raise RuntimeError("rate-limit bucket cleanup failed")
        if scenario.scenario_id is ScenarioId.CLEANUP:
            self._postgres.insert_stale_buckets(scenario.request_count)

    def execute(self, scenario: WorkloadScenario, request_index: int) -> OperationResult:
        if self._prepared is not scenario.scenario_id:
            raise RuntimeError("scenario was not prepared")
        handlers = {
            ScenarioId.AUTHENTICATED_READ: self._authenticated_read,
            ScenarioId.AUTHENTICATED_MUTATION: self._authenticated_mutation,
            ScenarioId.EXPENSIVE_READ: self._expensive_read,
            ScenarioId.IDENTITY_LIFECYCLE: self._identity_lifecycle,
            ScenarioId.GOVERNED_AGENT: self._governed_agent,
            ScenarioId.MALFORMED_AUTHENTICATED: self._malformed_authenticated,
            ScenarioId.BOLA_DENIED: self._bola_denied,
            ScenarioId.RATE_LIMIT_CONTENTION: self._rate_limit_contention,
            ScenarioId.DOMAIN_ROLLBACK_ACCOUNTING: self._rollback_accounting,
            ScenarioId.STORE_UNAVAILABLE: self._store_unavailable,
            ScenarioId.CLEANUP: self._cleanup_batch,
        }
        return handlers[scenario.scenario_id](request_index)

    def invariant_failures(self, scenario: WorkloadScenario) -> tuple[str, ...]:
        calls = self._recording_limiter.snapshot()
        expected_policy: RateLimitPolicyClass | None = None
        if scenario.scenario_id is ScenarioId.MALFORMED_AUTHENTICATED:
            expected_policy = RateLimitPolicyClass.MUTATION
        elif scenario.scenario_id is ScenarioId.BOLA_DENIED:
            expected_policy = RateLimitPolicyClass.READ
        if expected_policy is None:
            return ()

        counts = Counter(calls)
        failures: set[str] = set()
        expected_call = ("preauth", expected_policy)
        if counts[expected_call] != scenario.request_count:
            failures.add("PREAUTH_RATE_LIMIT_CALL_COUNT_DRIFT")
        if sum(counts.values()) != scenario.request_count:
            failures.add("UNEXPECTED_RATE_LIMIT_SCOPE_CALL")
        if any(scope != "preauth" for scope, _ in calls):
            failures.add("TENANT_BUDGET_CONSUMED_BEFORE_AUTHORIZATION")
        if any(policy is not expected_policy for _, policy in calls):
            failures.add("RATE_LIMIT_POLICY_ORDER_DRIFT")
        return tuple(sorted(failures))

    def pool_snapshot(self) -> PoolSnapshot:
        return self._postgres.pool_snapshot()

    def cleanup(self, scenario: WorkloadScenario) -> CleanupResult:
        started = monotonic_ns()
        residue = 0
        if scenario.scenario_id in {
            ScenarioId.RATE_LIMIT_CONTENTION,
            ScenarioId.DOMAIN_ROLLBACK_ACCOUNTING,
            ScenarioId.CLEANUP,
        }:
            residue = self._postgres.clear_buckets()
        return CleanupResult(
            decision="PASS" if residue == 0 else "FAIL",
            duration_ms=(monotonic_ns() - started) / 1_000_000,
            residue_count=residue,
        )

    def close(self) -> None:
        self._postgres.close()

    @staticmethod
    def _headers() -> dict[str, str]:
        return {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    @staticmethod
    def _request(
        app: FastAPI,
        method: str,
        path: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object] | None = None,
    ) -> _HttpResponse:
        client = TestClient(app)
        try:
            return cast(_HttpResponse, client.request(method, path, headers=headers, json=payload))
        finally:
            client.close()

    def _authenticated_read(self, request_index: int) -> OperationResult:
        del request_index
        response = self._request(self._allowed_app, "GET", "/api/v1/me", headers=self._headers())
        failures: tuple[str, ...] = ()
        if (
            response.status_code == 200
            and response.json().get("authorization_status") != "NOT_LOADED"
        ):
            failures = ("IDENTITY_PROJECTION_DRIFT",)
        return OperationResult(
            status_code=response.status_code,
            rate_limit_outcome="allowed",
            invariant_failures=failures,
        )

    def _authenticated_mutation(self, request_index: int) -> OperationResult:
        headers = {
            **self._headers(),
            "Idempotency-Key": f"performance-create-{request_index}",
        }
        response = self._request(
            self._allowed_app,
            "POST",
            f"/api/v1/tenants/{TENANT_ID}/campaigns",
            headers=headers,
            payload={
                "slug": f"verification-draft-{request_index}",
                "name": f"Verification draft {request_index}",
                "jurisdiction": "Verification jurisdiction",
                "stage": "PREPARATION",
            },
        )
        failures: tuple[str, ...] = ()
        if (
            response.status_code == 201
            and response.json().get("campaign", {}).get("status") != "DRAFT"
        ):
            failures = ("DRAFT_MUTATION_SCOPE_DRIFT",)
        return OperationResult(
            status_code=response.status_code,
            rate_limit_outcome="allowed",
            invariant_failures=failures,
        )

    def _expensive_read(self, request_index: int) -> OperationResult:
        del request_index
        response = self._request(
            self._allowed_app,
            "GET",
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/readiness",
            headers=self._headers(),
        )
        failures: tuple[str, ...] = ()
        if (
            response.status_code == 200
            and response.json().get("readiness", {}).get("readiness_scope")
            != "OPERATIONAL_SETUP_ONLY"
        ):
            failures = ("READINESS_SCOPE_DRIFT",)
        return OperationResult(
            status_code=response.status_code,
            rate_limit_outcome="allowed",
            invariant_failures=failures,
        )

    def _identity_lifecycle(self, request_index: int) -> OperationResult:
        del request_index
        response = self._request(
            self._allowed_app,
            "POST",
            f"/api/v1/tenants/{TENANT_ID}/identity/sessions/current",
            headers=self._headers(),
        )
        failures: tuple[str, ...] = ()
        if (
            response.status_code == 200
            and response.json().get("provider_revocation_state") != "NOT_EXECUTED"
        ):
            failures = ("IDENTITY_EXTERNAL_EFFECT_DRIFT",)
        return OperationResult(
            status_code=response.status_code,
            rate_limit_outcome="allowed",
            invariant_failures=failures,
        )

    def _governed_agent(self, request_index: int) -> OperationResult:
        response = self._request(
            self._allowed_app,
            "POST",
            f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/agent-runs",
            headers={
                **self._headers(),
                "Idempotency-Key": f"performance-agent-{request_index}",
            },
            payload={
                "strategy_workspace_version": 1,
                "purpose": "RED_TEAM_REVIEW",
                "instruction": "Review the internal evidence boundary.",
                "output_token_limit": 128,
                "timeout_ms": 1000,
                "cost_ceiling_micros": 0,
            },
        )
        return OperationResult(
            status_code=response.status_code,
            rate_limit_outcome="allowed",
            expected_error=True,
            invariant_failures=(
                () if response.status_code == 503 else ("GOVERNED_AGENT_FAIL_CLOSED_DRIFT",)
            ),
        )

    def _malformed_authenticated(self, request_index: int) -> OperationResult:
        response = self._request(
            self._allowed_app,
            "POST",
            f"/api/v1/tenants/{TENANT_ID}/campaigns",
            headers={
                **self._headers(),
                "Idempotency-Key": f"performance-malformed-{request_index}",
            },
            payload={"slug": request_index},
        )
        return OperationResult(
            status_code=response.status_code,
            rate_limit_outcome="allowed",
            expected_error=True,
            invariant_failures=(
                () if response.status_code == 422 else ("MALFORMED_REQUEST_ORDER_DRIFT",)
            ),
        )

    def _bola_denied(self, request_index: int) -> OperationResult:
        del request_index
        response = self._request(
            self._allowed_app,
            "GET",
            f"/api/v1/tenants/{OTHER_TENANT_ID}/campaigns/{CAMPAIGN_ID}",
            headers=self._headers(),
        )
        return OperationResult(
            status_code=response.status_code,
            rate_limit_outcome="allowed",
            expected_error=True,
            invariant_failures=(
                () if response.status_code == 403 else ("CROSS_TENANT_DENIAL_DRIFT",)
            ),
        )

    def _rate_limit_contention(self, request_index: int) -> OperationResult:
        del request_index
        decision = self._postgres.limiter.consume(
            TENANT_ID,
            PRINCIPAL_ID,
            RateLimitPolicyClass.MUTATION,
        )
        return OperationResult(
            status_code=200 if decision.allowed else 429,
            rate_limit_outcome="allowed" if decision.allowed else "denied",
            expected_error=not decision.allowed,
        )

    def _rollback_accounting(self, request_index: int) -> OperationResult:
        principal_id = uuid5(NAMESPACE, f"rollback:{request_index}")
        decision = self._postgres.limiter.consume(
            TENANT_ID,
            principal_id,
            RateLimitPolicyClass.READ,
        )
        try:
            with self._postgres.database.tenant_transaction(TENANT_ID):
                raise RuntimeError("forced verification rollback")
        except RuntimeError as exc:
            if str(exc) != "forced verification rollback":
                raise
        with self._postgres.database.tenant_transaction(TENANT_ID) as session:
            count = session.scalar(
                select(func.count())
                .select_from(RateLimitBucket)
                .where(
                    RateLimitBucket.principal_id == principal_id,
                    RateLimitBucket.policy_class == RateLimitPolicyClass.READ.value,
                    RateLimitBucket.policy_version == 9001,
                )
            )
        failures: tuple[str, ...] = ()
        if not decision.allowed or count != 1:
            failures = ("DOMAIN_ROLLBACK_REFUNDED_BUDGET",)
        return OperationResult(
            status_code=200,
            rate_limit_outcome="allowed" if decision.allowed else "denied",
            invariant_failures=failures,
        )

    def _store_unavailable(self, request_index: int) -> OperationResult:
        del request_index
        response = self._request(
            self._unavailable_app, "GET", "/api/v1/me", headers=self._headers()
        )
        failures: tuple[str, ...] = ()
        if response.status_code != 503 or response.json().get("code") != "RATE_LIMIT_UNAVAILABLE":
            failures = ("STORE_FAILURE_DID_NOT_FAIL_CLOSED",)
        return OperationResult(
            status_code=response.status_code,
            rate_limit_outcome="unavailable",
            expected_error=True,
            invariant_failures=failures,
        )

    def _cleanup_batch(self, request_index: int) -> OperationResult:
        del request_index
        deleted = self._postgres.limiter.cleanup_expired(
            TENANT_ID,
            before=datetime.now(UTC) - timedelta(hours=1),
            batch_size=1,
        )
        return OperationResult(
            status_code=200,
            rate_limit_outcome="not_applicable",
            invariant_failures=(() if deleted == 1 else ("CLEANUP_BATCH_COUNT_DRIFT",)),
        )
