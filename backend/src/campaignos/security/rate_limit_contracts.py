"""Typed server-owned rate-limit policy contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RateLimitPolicyClass(StrEnum):
    """Bounded operation classes reviewed by the C3-SEC-002 SHIP specification."""

    READ = "read"
    MUTATION = "mutation"
    EXPENSIVE_READ = "expensive_read"
    IDENTITY_LIFECYCLE = "identity_lifecycle"
    GOVERNED_AGENT = "governed_agent_execution"


class RateLimitPolicy(BaseModel):
    """One immutable fixed-window policy owned by the server."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_class: RateLimitPolicyClass
    version: int = Field(ge=1, le=1_000_000)
    request_limit: int = Field(ge=1, le=1_000_000)
    window_seconds: int = Field(ge=1, le=86_400)


class RateLimitPolicyCatalog(BaseModel):
    """Exactly one policy for every reviewed operation class."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policies: tuple[RateLimitPolicy, ...]

    @model_validator(mode="after")
    def validate_complete_catalog(self) -> RateLimitPolicyCatalog:
        classes = [policy.policy_class for policy in self.policies]
        expected = set(RateLimitPolicyClass)
        if len(classes) != len(set(classes)):
            raise ValueError("Rate-limit policy classes must be unique")
        if set(classes) != expected:
            raise ValueError("Rate-limit policy catalog must cover every reviewed operation class")
        return self

    def policy_for(self, policy_class: RateLimitPolicyClass) -> RateLimitPolicy:
        for policy in self.policies:
            if policy.policy_class is policy_class:
                return policy
        raise KeyError(policy_class)  # pragma: no cover - completeness is model-validated.


class RateLimitDecision(BaseModel):
    """Internal decision that intentionally excludes stored keys and raw counters."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    allowed: bool
    policy_class: RateLimitPolicyClass
    retry_after_seconds: int = Field(ge=0, le=86_400)
    policy_version: int = Field(ge=1, le=1_000_000)
