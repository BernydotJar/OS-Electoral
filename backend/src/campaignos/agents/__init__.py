"""Governed provider-neutral recommendation runtime."""

from campaignos.agents.contracts import (
    AgentClaim,
    AgentEvidenceItem,
    AgentExecutionResult,
    AgentOptionContext,
    AgentPromptEnvelope,
    AgentRecommendation,
    AgentRunCreateEvidence,
    AgentRunProjection,
    AgentRunReadEvidence,
    AgentRunRequest,
    AgentStrategyContext,
    ProviderGenerationRequest,
    ProviderGenerationResponse,
)
from campaignos.agents.runtime import (
    AgentProviderUnavailable,
    AgentRuntime,
    StructuredGenerationProvider,
    UnavailableStructuredGenerationProvider,
)

__all__ = [
    "AgentClaim",
    "AgentEvidenceItem",
    "AgentExecutionResult",
    "AgentOptionContext",
    "AgentPromptEnvelope",
    "AgentProviderUnavailable",
    "AgentRecommendation",
    "AgentRunCreateEvidence",
    "AgentRunProjection",
    "AgentRunReadEvidence",
    "AgentRunRequest",
    "AgentRuntime",
    "AgentStrategyContext",
    "ProviderGenerationRequest",
    "ProviderGenerationResponse",
    "StructuredGenerationProvider",
    "UnavailableStructuredGenerationProvider",
    "AgentRunIdempotencyConflict",
    "AgentRunNotFound",
    "AgentRunService",
    "AgentRunStrategyConflict",
    "AgentRunUnavailable",
    "UnavailableAgentRunService",
    "SqlAlchemyAgentRunService",
]

from campaignos.agents.service import (
    AgentRunIdempotencyConflict,
    AgentRunNotFound,
    AgentRunService,
    AgentRunStrategyConflict,
    AgentRunUnavailable,
    UnavailableAgentRunService,
)
from campaignos.agents.sql_service import SqlAlchemyAgentRunService
