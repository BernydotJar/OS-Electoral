"""FastAPI adapter for the server-owned rate-limit security boundary."""

from __future__ import annotations

import secrets
from typing import cast
from uuid import UUID

from fastapi import HTTPException, Request, status

from campaignos.api.dependencies import authenticated_principal_from_request
from campaignos.api.errors import ProblemException
from campaignos.identity.models import AuthenticatedPrincipal
from campaignos.observability import MetricsRegistry
from campaignos.security.rate_limit_contracts import RateLimitPolicyClass
from campaignos.security.rate_limits import (
    OPERATIONAL_METRICS_PRINCIPAL_ID,
    PREAUTH_SCOPE_TENANT_ID,
    RateLimiter,
    RateLimitStoreUnavailable,
    RateLimitSubjectScope,
    declared_rate_limit_policy,
    declared_rate_limit_scope,
    preauth_principal_id,
    rate_limit_policy,
)

__all__ = [
    "declared_rate_limit_policy",
    "enforce_declared_rate_limit_boundary",
    "enforce_pre_auth_rate_limit",
    "enforce_rate_limit",
    "rate_limit_policy",
]


def enforce_declared_rate_limit_boundary(request: Request) -> None:
    """Consume an opaque pre-auth budget before model binding.

    Tenant budgets remain exact-grant gated inside the endpoint.
    """
    endpoint = request.scope.get("endpoint")
    policy_class = declared_rate_limit_policy(endpoint)
    if policy_class is None:
        return
    subject_scope = declared_rate_limit_scope(endpoint)
    if subject_scope is None:
        _record_rate_limit_event(request, policy_class=policy_class, outcome="configuration_error")
        raise ProblemException(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Service unavailable",
            detail="Request protection is temporarily unavailable",
            code="RATE_LIMIT_UNAVAILABLE",
        )

    if subject_scope is RateLimitSubjectScope.OPERATIONAL:
        _authenticate_metrics_request(request)
        enforce_rate_limit(
            request,
            tenant_id=PREAUTH_SCOPE_TENANT_ID,
            principal_id=OPERATIONAL_METRICS_PRINCIPAL_ID,
            policy_class=policy_class,
        )
        return

    principal = authenticated_principal_from_request(request)
    if subject_scope is RateLimitSubjectScope.PREAUTH:
        enforce_pre_auth_rate_limit(
            request,
            principal=principal,
            policy_class=policy_class,
        )
        return

    # Tenant routes receive a separate opaque pre-authorization budget here.
    # The endpoint retains exact grant authorization before consuming its tenant budget.
    enforce_pre_auth_rate_limit(
        request,
        principal=principal,
        policy_class=policy_class,
    )


def _authenticate_metrics_request(request: Request) -> None:
    settings = request.app.state.settings
    if not settings.metrics_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    configured_token = settings.metrics_bearer_token
    if configured_token is None:
        return
    authorization = request.headers.get("authorization", "")
    scheme, _, supplied_token = authorization.partition(" ")
    expected_token = configured_token.get_secret_value()
    if scheme.lower() != "bearer" or not secrets.compare_digest(supplied_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Metrics authentication is required",
            headers={"WWW-Authenticate": "Bearer"},
        )


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
    key = (tenant_id, principal_id, policy_class)
    consumed = getattr(request.state, "rate_limit_consumed", None)
    if consumed is None:
        consumed = set()
        request.state.rate_limit_consumed = consumed
    if not isinstance(consumed, set):
        _record_rate_limit_event(request, policy_class=policy_class, outcome="configuration_error")
        raise ProblemException(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Service unavailable",
            detail="Request protection is temporarily unavailable",
            code="RATE_LIMIT_UNAVAILABLE",
        )
    if key in consumed:
        return
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
    consumed.add(key)
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
