"""Strict contracts for evidence-bound internal recommendation runs."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AgentPurpose = Literal["EVIDENCE_SYNTHESIS", "OPTION_COMPARISON", "RED_TEAM_REVIEW"]
AgentEvidenceClassification = Literal["VERIFIED", "INFERRED", "UNKNOWN"]
AgentEvidenceStatus = Literal["ACCEPTED", "NEEDS_REVIEW"]
AgentClaimClassification = Literal["SUPPORTED", "ASSUMPTION", "UNKNOWN"]
AgentRunStatus = Literal["COMPLETED", "REFUSED"]
AgentRefusalCode = Literal[
    "PROHIBITED_INSTRUCTION",
    "INPUT_BUDGET_EXCEEDED",
    "STRATEGY_NOT_ELIGIBLE",
    "PROVIDER_UNAVAILABLE",
    "PROVIDER_IDENTITY_MISMATCH",
    "PROVIDER_REFUSAL",
    "TOOL_CALL_REJECTED",
    "OUTPUT_SCHEMA_INVALID",
    "UNSUPPORTED_CLAIM",
    "UNKNOWN_OPTION",
    "PROHIBITED_OUTPUT",
    "PROVIDER_BUDGET_EXCEEDED",
]

POLICY_ID = "campaignos.agent.internal-recommendation"
POLICY_VERSION = "1.0"
OUTPUT_SCHEMA_VERSION = "1.0"
PROMPT_TEMPLATE_VERSIONS: dict[AgentPurpose, tuple[str, str]] = {
    "EVIDENCE_SYNTHESIS": ("agent.evidence-synthesis", "1.0"),
    "OPTION_COMPARISON": ("agent.option-comparison", "1.0"),
    "RED_TEAM_REVIEW": ("agent.red-team-review", "1.0"),
}


class AgentContractError(ValueError):
    """A runtime contract violates deterministic governance rules."""


def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise AgentContractError(detail)


def _normalized_text(value: str) -> str:
    return " ".join(value.split())


def _normalize_text_tuple(value: object) -> object:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Iterable):
        raise ValueError("expected an array of strings")
    normalized = tuple(_normalized_text(str(item)) for item in value)
    if any(not item for item in normalized):
        raise ValueError("array values must be non-empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError("array values must be unique")
    return normalized


class AgentModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class AgentRunRequest(AgentModel):
    strategy_workspace_version: int = Field(ge=1)
    purpose: AgentPurpose
    instruction: str = Field(min_length=1, max_length=2000)
    output_token_limit: int = Field(default=1024, ge=1, le=2048)
    timeout_ms: int = Field(default=10_000, ge=100, le=30_000)
    cost_ceiling_micros: int = Field(default=0, ge=0, le=1_000_000)

    @field_validator("instruction", mode="before")
    @classmethod
    def normalize_instruction(cls, value: object) -> object:
        return _normalized_text(value) if isinstance(value, str) else value


class AgentEvidenceItem(AgentModel):
    id: UUID
    classification: AgentEvidenceClassification
    status: AgentEvidenceStatus
    statement: str = Field(min_length=1, max_length=2000)
    source_reference: str | None = Field(default=None, max_length=500)

    @field_validator("statement", "source_reference", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        return _normalized_text(value) if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_provenance(self) -> Self:
        if self.classification in {"VERIFIED", "INFERRED"}:
            _require(self.source_reference is not None, "sourced evidence requires provenance")
        if self.classification == "UNKNOWN":
            _require(self.status == "NEEDS_REVIEW", "unknown evidence must need review")
        return self


class AgentOptionContext(AgentModel):
    id: UUID
    title: str = Field(min_length=1, max_length=180)
    summary: str = Field(min_length=1, max_length=2000)
    evidence_refs: tuple[UUID, ...] = Field(min_length=1, max_length=80)

    @field_validator("title", "summary", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        return _normalized_text(value) if isinstance(value, str) else value


class AgentStrategyContext(AgentModel):
    workspace_id: UUID
    tenant_id: UUID
    campaign_id: UUID
    workspace_version: int = Field(ge=1)
    status: Literal["READY_FOR_HUMAN_DECISION", "DECIDED_INTERNAL"]
    evidence: tuple[AgentEvidenceItem, ...] = Field(min_length=1, max_length=100)
    options: tuple[AgentOptionContext, ...] = Field(min_length=2, max_length=20)
    limitation_codes: tuple[str, ...] = Field(min_length=1, max_length=20)

    _normalize_limitations = field_validator("limitation_codes", mode="before")(
        _normalize_text_tuple
    )

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        evidence_ids = {item.id for item in self.evidence}
        _require(len(evidence_ids) == len(self.evidence), "evidence IDs must be unique")
        option_ids = {item.id for item in self.options}
        _require(len(option_ids) == len(self.options), "option IDs must be unique")
        for option in self.options:
            _require(
                set(option.evidence_refs) <= evidence_ids,
                "strategy option contains unknown evidence references",
            )
        return self


class AgentPromptEnvelope(AgentModel):
    policy_id: Literal["campaignos.agent.internal-recommendation"] = (
        "campaignos.agent.internal-recommendation"
    )
    policy_version: Literal["1.0"] = "1.0"
    prompt_template_id: str
    prompt_template_version: Literal["1.0"] = "1.0"
    output_schema_version: Literal["1.0"] = "1.0"
    purpose: AgentPurpose
    instruction: str
    strategy_workspace_id: UUID
    strategy_workspace_version: int
    untrusted_evidence: tuple[AgentEvidenceItem, ...]
    options: tuple[AgentOptionContext, ...]
    limitation_codes: tuple[str, ...]
    tool_names: tuple[str, ...] = ()
    human_review_required: Literal[True] = True
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"

    @model_validator(mode="after")
    def forbid_tools(self) -> Self:
        _require(not self.tool_names, "agent prompt tools must remain disabled")
        return self


class ProviderGenerationRequest(AgentModel):
    envelope: AgentPromptEnvelope
    output_token_limit: int = Field(ge=1, le=2048)
    timeout_ms: int = Field(ge=100, le=30_000)
    cost_ceiling_micros: int = Field(ge=0, le=1_000_000)


class ProviderGenerationResponse(AgentModel):
    provider: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=160)
    content: dict[str, Any] | None = None
    tool_calls: tuple[str, ...] = Field(default=(), max_length=20)
    prompt_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0)
    cost_micros: int = Field(default=0, ge=0)
    refusal_code: str | None = Field(default=None, max_length=100)

    @field_validator("provider", "model", "refusal_code", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        return _normalized_text(value) if isinstance(value, str) else value


class AgentClaim(AgentModel):
    statement: str = Field(min_length=1, max_length=2000)
    classification: AgentClaimClassification
    evidence_refs: tuple[UUID, ...] = Field(default=(), max_length=80)

    @field_validator("statement", mode="before")
    @classmethod
    def normalize_statement(cls, value: object) -> object:
        return _normalized_text(value) if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_support(self) -> Self:
        if self.classification == "SUPPORTED":
            _require(bool(self.evidence_refs), "supported claims require evidence")
        return self


class AgentRecommendation(AgentModel):
    summary: str = Field(min_length=1, max_length=4000)
    claims: tuple[AgentClaim, ...] = Field(min_length=1, max_length=40)
    option_refs: tuple[UUID, ...] = Field(default=(), max_length=20)
    risks: tuple[str, ...] = Field(default=(), max_length=30)
    uncertainties: tuple[str, ...] = Field(default=(), max_length=30)
    human_review_required: Literal[True] = True
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"

    @field_validator("summary", mode="before")
    @classmethod
    def normalize_summary(cls, value: object) -> object:
        return _normalized_text(value) if isinstance(value, str) else value

    @field_validator("risks", "uncertainties", mode="before")
    @classmethod
    def normalize_lists(cls, value: object) -> object:
        return _normalize_text_tuple(value)


class AgentExecutionResult(AgentModel):
    status: AgentRunStatus
    refusal_code: AgentRefusalCode | None = None
    refusal_detail: str | None = Field(default=None, max_length=255)
    prompt_envelope: AgentPromptEnvelope | None = None
    prompt_digest: str | None = Field(default=None, min_length=64, max_length=64)
    provider: str | None = None
    model: str | None = None
    recommendation: AgentRecommendation | None = None
    prompt_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0)
    cost_micros: int = Field(default=0, ge=0)
    human_disposition: Literal["PENDING"] = "PENDING"
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.status == "COMPLETED":
            _require(self.refusal_code is None, "completed run cannot include refusal")
            _require(self.recommendation is not None, "completed run requires recommendation")
            _require(self.prompt_envelope is not None, "completed run requires prompt evidence")
            _require(self.prompt_digest is not None, "completed run requires prompt digest")
            _require(
                self.provider is not None and self.model is not None, "provider identity required"
            )
        else:
            _require(self.refusal_code is not None, "refused run requires refusal code")
            _require(self.recommendation is None, "refused run cannot include recommendation")
        return self


class AgentRunProjection(AgentModel):
    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    strategy_workspace_id: UUID
    strategy_workspace_version: int = Field(ge=1)
    purpose: AgentPurpose
    instruction_digest: str = Field(min_length=64, max_length=64)
    policy_id: str
    policy_version: str
    prompt_template_id: str
    prompt_template_version: str
    output_schema_version: str
    prompt_digest: str | None = Field(default=None, min_length=64, max_length=64)
    provider: str | None = None
    model: str | None = None
    status: AgentRunStatus
    refusal_code: AgentRefusalCode | None = None
    refusal_detail: str | None = None
    recommendation: AgentRecommendation | None = None
    evidence_refs: tuple[UUID, ...] = ()
    option_refs: tuple[UUID, ...] = ()
    prompt_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    cost_micros: int = Field(ge=0)
    human_disposition: Literal["PENDING"] = "PENDING"
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"
    created_at: datetime


class AgentRunCreateEvidence(AgentModel):
    run: AgentRunProjection
    audit_event_id: UUID
    outbox_event_id: UUID


class AgentRunReadEvidence(AgentModel):
    run: AgentRunProjection
    audit_event_id: UUID
