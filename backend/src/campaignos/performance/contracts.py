"""Strict contracts for bounded non-production performance verification."""

from __future__ import annotations

import json
import re
from datetime import datetime
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_CONCURRENCY = 20
MAX_REQUESTS = 600
MAX_SCENARIO_SECONDS = 60.0
MAX_HARNESS_SECONDS = 600.0


class ScenarioId(StrEnum):
    AUTHENTICATED_READ = "authenticated_read"
    AUTHENTICATED_MUTATION = "authenticated_mutation"
    EXPENSIVE_READ = "expensive_read"
    IDENTITY_LIFECYCLE = "identity_lifecycle"
    GOVERNED_AGENT = "governed_agent"
    MALFORMED_AUTHENTICATED = "malformed_authenticated"
    BOLA_DENIED = "bola_denied"
    RATE_LIMIT_CONTENTION = "rate_limit_contention"
    DOMAIN_ROLLBACK_ACCOUNTING = "domain_rollback_accounting"
    STORE_UNAVAILABLE = "store_unavailable"
    CLEANUP = "cleanup"


class RouteClass(StrEnum):
    IDENTITY_READ = "identity_read"
    DRAFT_MUTATION = "draft_mutation"
    WORKSPACE_PROJECTION = "workspace_projection"
    IDENTITY_CONTROL = "identity_control"
    GOVERNED_RECOMMENDATION = "governed_recommendation"
    REQUEST_VALIDATION = "request_validation"
    AUTHORIZATION_DENIAL = "authorization_denial"
    RATE_LIMIT_STORE = "rate_limit_store"
    DOMAIN_TRANSACTION = "domain_transaction"
    DEPENDENCY_FAILURE = "dependency_failure"
    MAINTENANCE = "maintenance"


class AuthorizationScope(StrEnum):
    PREAUTH = "opaque_preauthorization"
    TENANT = "exact_tenant_grant"
    CROSS_TENANT_DENIED = "cross_tenant_denied"
    OPERATIONAL = "internal_operational"


class RunnerLimits(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_concurrency: int = Field(default=MAX_CONCURRENCY, ge=1, le=MAX_CONCURRENCY)
    max_requests_per_scenario: int = Field(default=MAX_REQUESTS, ge=1, le=MAX_REQUESTS)
    max_scenario_seconds: float = Field(
        default=MAX_SCENARIO_SECONDS, ge=0.05, le=MAX_SCENARIO_SECONDS
    )
    max_harness_seconds: float = Field(default=MAX_HARNESS_SECONDS, ge=0.1, le=MAX_HARNESS_SECONDS)


class WorkloadScenario(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: ScenarioId
    route_class: RouteClass
    policy_class: Literal[
        "read",
        "mutation",
        "expensive_read",
        "identity_lifecycle",
        "governed_agent_execution",
    ]
    request_count: int = Field(ge=1, le=MAX_REQUESTS)
    concurrency: int = Field(ge=1, le=MAX_CONCURRENCY)
    timeout_seconds: float = Field(ge=0.05, le=MAX_SCENARIO_SECONDS)
    expected_status_codes: tuple[int, ...] = Field(min_length=1, max_length=8)
    authorization_scope: AuthorizationScope
    cleanup_required: bool = True
    latency_ceiling_ms: float = Field(gt=0, le=60_000)
    expected_allowed: int | None = Field(default=None, ge=0, le=MAX_REQUESTS)
    expected_denied: int | None = Field(default=None, ge=0, le=MAX_REQUESTS)

    @field_validator("expected_status_codes")
    @classmethod
    def validate_status_codes(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if len(value) != len(set(value)) or any(code < 200 or code > 599 for code in value):
            raise ValueError("expected status codes must be unique HTTP response codes")
        return tuple(sorted(value))

    @model_validator(mode="after")
    def validate_envelope(self) -> Self:
        if self.concurrency > self.request_count:
            raise ValueError("scenario concurrency cannot exceed request count")
        exact_counts = (self.expected_allowed, self.expected_denied)
        if any(value is not None for value in exact_counts):
            if any(value is None for value in exact_counts):
                raise ValueError("exact rate-limit expectations require allowed and denied totals")
            assert self.expected_allowed is not None
            assert self.expected_denied is not None
            if self.expected_allowed + self.expected_denied != self.request_count:
                raise ValueError("exact allowed and denied totals must equal request count")
        return self


class WorkloadCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    catalog_version: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    scenarios: tuple[WorkloadScenario, ...] = Field(min_length=1, max_length=len(ScenarioId))

    @model_validator(mode="after")
    def validate_unique_scenarios(self) -> Self:
        ids = [scenario.scenario_id for scenario in self.scenarios]
        if len(ids) != len(set(ids)):
            raise ValueError("scenario IDs must be unique")
        return self


class OperationResult(BaseModel):
    """One sanitized operation result; no raw request or response data is accepted."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status_code: int = Field(ge=200, le=599)
    rate_limit_outcome: Literal["allowed", "denied", "unavailable", "not_applicable"]
    expected_error: bool = False
    invariant_failures: tuple[str, ...] = Field(default=(), max_length=16)

    @field_validator("invariant_failures")
    @classmethod
    def validate_failure_codes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for code in value:
            if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", code):
                raise ValueError("invariant failures must be bounded stable codes")
        return tuple(sorted(set(value)))


class PoolSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    size: int = Field(default=0, ge=0, le=10_000)
    checked_in: int = Field(default=0, ge=0, le=10_000)
    checked_out: int = Field(default=0, ge=0, le=10_000)
    overflow: int = Field(default=0, ge=0, le=10_000)


class CleanupResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: Literal["PASS", "FAIL"]
    duration_ms: float = Field(ge=0, le=60_000)
    residue_count: int = Field(ge=0, le=1_000_000)


class LatencySummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    minimum_ms: float = Field(ge=0)
    median_ms: float = Field(ge=0)
    p95_ms: float = Field(ge=0)
    p99_ms: float = Field(ge=0)
    maximum_ms: float = Field(ge=0)


class ResponseClassCounts(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    success_2xx: int = Field(ge=0)
    redirect_3xx: int = Field(ge=0)
    client_error_4xx: int = Field(ge=0)
    server_error_5xx: int = Field(ge=0)
    transport_error: int = Field(ge=0)


class RateLimitOutcomeCounts(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    allowed: int = Field(ge=0)
    denied: int = Field(ge=0)
    unavailable: int = Field(ge=0)
    not_applicable: int = Field(ge=0)


class PoolEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    before: PoolSnapshot
    peak: PoolSnapshot
    after: PoolSnapshot


class ScenarioReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: ScenarioId
    policy_class: str = Field(pattern=r"^[a-z_]{3,40}$")
    configured_requests: int = Field(ge=1, le=MAX_REQUESTS)
    configured_concurrency: int = Field(ge=1, le=MAX_CONCURRENCY)
    configured_timeout_seconds: float = Field(ge=0.05, le=MAX_SCENARIO_SECONDS)
    completed: int = Field(ge=0, le=MAX_REQUESTS)
    expected_errors: int = Field(ge=0, le=MAX_REQUESTS)
    unexpected_errors: int = Field(ge=0, le=MAX_REQUESTS)
    timed_out: int = Field(ge=0, le=MAX_REQUESTS)
    response_classes: ResponseClassCounts
    rate_limit_outcomes: RateLimitOutcomeCounts
    latency: LatencySummary
    pool: PoolEvidence
    invariant_failures: tuple[str, ...]
    invariant_decision: Literal["PASS", "FAIL"]
    threshold_decision: Literal["PASS", "FAIL"]
    cleanup_decision: Literal["PASS", "FAIL"]
    cleanup_duration_ms: float = Field(ge=0, le=60_000)
    overall_decision: Literal["PASS", "FAIL"]


class RuntimeContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operating_system: str = Field(pattern=r"^[A-Za-z0-9_.-]{2,40}$")
    machine: str = Field(pattern=r"^[A-Za-z0-9_.-]{2,40}$")
    cpu_count: int = Field(ge=1, le=4096)


class LoadVerificationReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    source_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    generated_at: datetime
    environment_classification: Literal["CONSTRAINED_NON_PRODUCTION"] = "CONSTRAINED_NON_PRODUCTION"
    python_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    postgresql_version: str = Field(pattern=r"^[0-9]+(?:\.[0-9]+){0,2}$")
    catalog_version: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    runtime_context: RuntimeContext
    runner_limits: RunnerLimits
    scenarios: tuple[ScenarioReceipt, ...]
    harness_failure_codes: tuple[str, ...] = Field(default=(), max_length=16)
    overall_decision: Literal["PASS", "FAIL"]
    production_capacity_claim: Literal[False] = False
    external_effects: Literal["NONE"] = "NONE"

    @model_validator(mode="after")
    def validate_timestamp_and_scenarios(self) -> Self:
        if self.generated_at.utcoffset() is None:
            raise ValueError("receipt timestamp must include a timezone")
        ids = [scenario.scenario_id for scenario in self.scenarios]
        if len(ids) != len(set(ids)):
            raise ValueError("receipt scenario IDs must be unique")
        for code in self.harness_failure_codes:
            if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", code):
                raise ValueError("harness failure codes must be bounded stable codes")
        if self.overall_decision == "PASS" and self.harness_failure_codes:
            raise ValueError("passing receipts cannot contain harness failures")
        if self.overall_decision == "PASS" and not self.scenarios:
            raise ValueError("passing receipts require scenario evidence")
        return self


SENSITIVE_KEY_PATTERN = re.compile(
    r"(?:^|_)(?:token|cookie|database_url|request_body|response_body|raw_url|tenant_id|"
    r"principal_id|email|ip_address|campaign_text|political_content)(?:$|_)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"postgres(?:ql)?(?:\+psycopg)?://", re.IGNORECASE),
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-"
        r"[0-9a-f]{12}\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(
        r"(?<![0-9])(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})"
        r"(?:\.(?:25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})){3}(?![0-9])"
    ),
)


def assert_receipt_sanitized(receipt: LoadVerificationReceipt | dict[str, object]) -> None:
    """Reject sensitive key names and values before evidence leaves the process."""

    payload = receipt.model_dump(mode="json") if isinstance(receipt, BaseModel) else receipt

    def walk(value: object, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if SENSITIVE_KEY_PATTERN.search(str(key)):
                    raise ValueError(f"sensitive receipt field is forbidden at {path}.{key}")
                walk(child, f"{path}.{key}")
            return
        if isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
            return
        if isinstance(value, str):
            for pattern in SENSITIVE_VALUE_PATTERNS:
                if pattern.search(value):
                    raise ValueError(f"sensitive receipt value is forbidden at {path}")

    walk(payload, "receipt")
    json.dumps(payload, ensure_ascii=True, sort_keys=True)
