"""Durable governed agent run service contracts."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from campaignos.agents.contracts import (
    AgentRunCreateEvidence,
    AgentRunReadEvidence,
    AgentRunRequest,
)


class AgentRunIdempotencyConflict(RuntimeError):
    """An idempotency key was reused with changed request or authority."""


class AgentRunNotFound(RuntimeError):
    """The exact tenant/campaign agent run is absent."""


class AgentRunStrategyConflict(RuntimeError):
    """The requested Strategy snapshot is stale or ineligible."""


class AgentRunUnavailable(RuntimeError):
    """The durable agent run boundary cannot currently complete."""


class AgentRunService(Protocol):
    def create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: AgentRunRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> AgentRunCreateEvidence: ...

    def get(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        run_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> AgentRunReadEvidence: ...


class UnavailableAgentRunService:
    def create(self, *args: object, **kwargs: object) -> AgentRunCreateEvidence:
        raise AgentRunUnavailable("Agent run service is unavailable")

    def get(self, *args: object, **kwargs: object) -> AgentRunReadEvidence:
        raise AgentRunUnavailable("Agent run service is unavailable")
