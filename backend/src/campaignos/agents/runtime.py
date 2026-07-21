"""Deterministic pre/post guarded provider-neutral agent runtime."""

from __future__ import annotations

import hashlib
import json
from typing import Protocol

from pydantic import ValidationError

from campaignos.agents.contracts import (
    PROMPT_TEMPLATE_VERSIONS,
    AgentExecutionResult,
    AgentPromptEnvelope,
    AgentRecommendation,
    AgentRunRequest,
    AgentStrategyContext,
    ProviderGenerationRequest,
    ProviderGenerationResponse,
)

PROHIBITED_FRAGMENTS = (
    "ignore previous",
    "ignore all previous",
    "system prompt",
    "reveal secret",
    "exfiltrate",
    "publish this",
    "send email",
    "send sms",
    "contact voter",
    "contact citizen",
    "call voter",
    "mobilize",
    "spend funds",
    "deploy",
    "grant access",
    "alter grant",
    "microtarget",
    "psychographic",
    "individual targeting",
    "persuade voters",
)
MAX_INPUT_CHARACTERS = 20_000


class AgentProviderUnavailable(RuntimeError):
    """Structured generation provider cannot complete the bounded request."""


class StructuredGenerationProvider(Protocol):
    provider_name: str
    model_name: str

    def generate(self, request: ProviderGenerationRequest) -> ProviderGenerationResponse: ...


class UnavailableStructuredGenerationProvider:
    provider_name = "unavailable"
    model_name = "unavailable"

    def generate(self, request: ProviderGenerationRequest) -> ProviderGenerationResponse:
        del request
        raise AgentProviderUnavailable("Structured generation provider is unavailable")


def _contains_prohibited(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in PROHIBITED_FRAGMENTS)


def canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _context_size(context: AgentStrategyContext, request: AgentRunRequest) -> int:
    return (
        len(request.instruction)
        + sum(len(item.statement) + len(item.source_reference or "") for item in context.evidence)
        + sum(len(item.title) + len(item.summary) for item in context.options)
    )


def _refusal(
    code: str,
    detail: str,
    *,
    envelope: AgentPromptEnvelope | None = None,
    digest: str | None = None,
    response: ProviderGenerationResponse | None = None,
) -> AgentExecutionResult:
    values: dict[str, object] = {
        "status": "REFUSED",
        "refusal_code": code,
        "refusal_detail": detail,
        "prompt_envelope": envelope,
        "prompt_digest": digest,
    }
    if response is not None:
        values.update(
            provider=response.provider,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            output_tokens=response.output_tokens,
            latency_ms=response.latency_ms,
            cost_micros=response.cost_micros,
        )
    return AgentExecutionResult.model_validate(values)


class AgentRuntime:
    """Execute one bounded recommendation request with no tools or authority."""

    def __init__(self, provider: StructuredGenerationProvider) -> None:
        self.provider = provider

    def execute(
        self,
        context: AgentStrategyContext,
        request: AgentRunRequest,
    ) -> AgentExecutionResult:
        if request.strategy_workspace_version != context.workspace_version:
            return _refusal(
                "STRATEGY_NOT_ELIGIBLE",
                "Requested strategy workspace version is not current",
            )
        if context.status not in {"READY_FOR_HUMAN_DECISION", "DECIDED_INTERNAL"}:
            return _refusal(
                "STRATEGY_NOT_ELIGIBLE",
                "Strategy workspace is not eligible for governed recommendation",
            )
        if _contains_prohibited(request.instruction):
            return _refusal(
                "PROHIBITED_INSTRUCTION",
                "Instruction requests a prohibited capability or disclosure",
            )
        if _context_size(context, request) > MAX_INPUT_CHARACTERS:
            return _refusal(
                "INPUT_BUDGET_EXCEEDED",
                "Authorized strategy context exceeds the bounded input budget",
            )

        template_id, _template_version = PROMPT_TEMPLATE_VERSIONS[request.purpose]
        envelope = AgentPromptEnvelope(
            prompt_template_id=template_id,
            prompt_template_version="1.0",
            purpose=request.purpose,
            instruction=request.instruction,
            strategy_workspace_id=context.workspace_id,
            strategy_workspace_version=context.workspace_version,
            untrusted_evidence=context.evidence,
            options=context.options,
            limitation_codes=context.limitation_codes,
        )
        digest = canonical_digest(envelope.model_dump(mode="json"))
        provider_request = ProviderGenerationRequest(
            envelope=envelope,
            output_token_limit=request.output_token_limit,
            timeout_ms=request.timeout_ms,
            cost_ceiling_micros=request.cost_ceiling_micros,
        )
        try:
            response = self.provider.generate(provider_request)
        except Exception:
            return _refusal(
                "PROVIDER_UNAVAILABLE",
                "Structured generation provider is unavailable",
                envelope=envelope,
                digest=digest,
            )

        if (
            response.provider != self.provider.provider_name
            or response.model != self.provider.model_name
        ):
            return _refusal(
                "PROVIDER_IDENTITY_MISMATCH",
                "Provider response identity does not match configured adapter",
                envelope=envelope,
                digest=digest,
                response=response,
            )
        if response.refusal_code is not None:
            return _refusal(
                "PROVIDER_REFUSAL",
                "Provider refused the bounded structured generation request",
                envelope=envelope,
                digest=digest,
                response=response,
            )
        if response.tool_calls:
            return _refusal(
                "TOOL_CALL_REJECTED",
                "Provider attempted a tool call while tools are disabled",
                envelope=envelope,
                digest=digest,
                response=response,
            )
        if (
            response.output_tokens > request.output_token_limit
            or response.latency_ms > request.timeout_ms
            or response.cost_micros > request.cost_ceiling_micros
        ):
            return _refusal(
                "PROVIDER_BUDGET_EXCEEDED",
                "Provider response exceeded an explicit runtime budget",
                envelope=envelope,
                digest=digest,
                response=response,
            )
        if response.content is None:
            return _refusal(
                "OUTPUT_SCHEMA_INVALID",
                "Provider returned no structured output",
                envelope=envelope,
                digest=digest,
                response=response,
            )
        try:
            recommendation = AgentRecommendation.model_validate(response.content)
        except ValidationError:
            return _refusal(
                "OUTPUT_SCHEMA_INVALID",
                "Provider output failed the strict recommendation schema",
                envelope=envelope,
                digest=digest,
                response=response,
            )

        evidence = {item.id: item for item in context.evidence}
        known_options = {item.id for item in context.options}
        if not set(recommendation.option_refs) <= known_options:
            return _refusal(
                "UNKNOWN_OPTION",
                "Provider output references an unknown strategy option",
                envelope=envelope,
                digest=digest,
                response=response,
            )
        for claim in recommendation.claims:
            if not set(claim.evidence_refs) <= set(evidence):
                return _refusal(
                    "UNSUPPORTED_CLAIM",
                    "Provider output references unknown evidence",
                    envelope=envelope,
                    digest=digest,
                    response=response,
                )
            if claim.classification == "SUPPORTED" and any(
                evidence[ref].classification == "UNKNOWN" or evidence[ref].status != "ACCEPTED"
                for ref in claim.evidence_refs
            ):
                return _refusal(
                    "UNSUPPORTED_CLAIM",
                    "Supported claim relies on evidence that is not accepted and sourced",
                    envelope=envelope,
                    digest=digest,
                    response=response,
                )
        output_text = " ".join(
            [
                recommendation.summary,
                *(claim.statement for claim in recommendation.claims),
                *recommendation.risks,
                *recommendation.uncertainties,
            ]
        )
        if _contains_prohibited(output_text):
            return _refusal(
                "PROHIBITED_OUTPUT",
                "Provider output contains a prohibited capability or action",
                envelope=envelope,
                digest=digest,
                response=response,
            )
        return AgentExecutionResult(
            status="COMPLETED",
            prompt_envelope=envelope,
            prompt_digest=digest,
            provider=response.provider,
            model=response.model,
            recommendation=recommendation,
            prompt_tokens=response.prompt_tokens,
            output_tokens=response.output_tokens,
            latency_ms=response.latency_ms,
            cost_micros=response.cost_micros,
        )
