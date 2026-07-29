"""FastAPI adapter for the server-owned rate-limit security boundary."""

from __future__ import annotations

from typing import cast
from uuid import UUID

from fastapi import Request, status

from campaignos.api.errors import ProblemException
from campaignos.identity.models import AuthenticatedPrincipal
from campaignos.observability import MetricsRegistry
from campaignos.security.rate_limit_contracts import RateLimitPolicyClass
from campaignos.security.rate_limits import (
    PREAUTH_SCOPE_TENANT_ID,
    RateLimiter,
    RateLimitStoreUnavailable,
    declared_rate_limit_policy,
    preauth_principal_id,
    rate_limit_policy,
)

__all__ = [
    "declared_rate_limit_policy",
    "enforce_pre_auth_rate_limit",
    "enforce_rate_limit",
    "rate_limit_policy",
]


def enforce_pre_auth_rate_limit(
    request: Request,
    *,
    principal: AuthenticatedPrincipal,
    policy_class: RateLimitPolicyClass,
) -> None:
    enforce_rate_limit(
        request,
        tenant_id=PREAUTH_SCOPE_TENANT_ID,
        principal_id=preauth_principal_id(principal),
        policy_class=policy_class,
    )


def enforce_rate_limit(
    request: Request,
    *,
    tenant_id: UUID,
    principal_id: UUID,
    policy_class: RateLimitPolicyClass,
) -> None:
    """Validate endpoint metadata, consume a budget, and emit sanitized evidence."""
    endpoint = request.scope.get("endpoint")
    declared = declared_rate_limit_policy(endpoint)
    if declared is not policy_class:
        _record_rate_limit_event(request, policy_class=policy_class, outcome="configuration_error")
        raise ProblemException(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Service unavailable",
            detail="Request protection is temporarily unavailable",
            code="RATE_LIMIT_UNAVAILABLE",
        )
    limiter = cast(RateLimiter, request.app.state.rate_limiter)
    try:
        decision = limiter.consume(tenant_id, principal_id, policy_class)
    except RateLimitStoreUnavailable as exc:
        _record_rate_limit_event(request, policy_class=policy_class, outcome="unavailable")
        raise ProblemException(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Service unavailable",
            detail="Request protection is temporarily unavailable",
            code="RATE_LIMIT_UNAVAILABLE",
        ) from exc
    outcome = "allowed" if decision.allowed else "denied"
    _record_rate_limit_event(request, policy_class=policy_class, outcome=outcome)
    if not decision.allowed:
        raise ProblemException(
            status=status.HTTP_429_TOO_MANY_REQUESTS,
            title="Too many requests",
            detail="The request rate for this operation is temporarily limited",
            code="RATE_LIMIT_EXCEEDED",
            headers={"Retry-After": str(max(decision.retry_after_seconds, 1))},
        )


def _record_rate_limit_event(
    request: Request,
    *,
    policy_class: RateLimitPolicyClass,
    outcome: str,
) -> None:
    metrics = cast(MetricsRegistry, request.app.state.metrics)
    metrics.rate_limit_decision(policy_class=policy_class.value, outcome=outcome)
    request.app.state.logger.info(
        "rate_limit_decision",
        extra={
            "correlation_id": getattr(request.state, "correlation_id", "unknown"),
            "policy_class": policy_class.value,
            "rate_limit_outcome": outcome,
        },
    )
