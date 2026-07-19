# ADR 005: Provider-neutral, evidence-bound AI orchestration

Status: **PROPOSED; NOT IMPLEMENTED AT PRODUCTION SCOPE**
Date: `2026-07-19`

## Context

CampaignOS may use multiple model providers, but model output is probabilistic, may be injected by untrusted evidence, and must not become a hidden authorization or political-action channel. Provider lock-in would also make privacy, residency, cost, and reliability choices difficult.

## Decision

Define an application-owned provider interface for structured generation. Every invocation records provider, model, policy/versioned prompt, token usage, latency, cost, evidence references, output-schema result, refusal/fallback, and human disposition. Context is minimized to the authorized tenant/campaign purpose, and untrusted evidence is delimited and treated as data.

Deterministic pre- and post-guards reject prohibited capabilities and sensitive actions. A valid schema means only that output is parseable; evidence, policy, authorization, and human-review gates remain separate. Providers cannot publish, spend, mobilize, contact people, alter grants, or deploy environments.

## Consequences

- Provider adapters need contract tests, timeout/retry budgets, data-processing review, and leakage controls.
- Cached or logged prompts/responses inherit the source data classification and retention policy.
- Hard evals cover prompt injection, fabrication, unsupported claims, cross-tenant context, privacy, prohibited political behavior, and external-action refusal.
- Provider fallback must preserve scope, policy, and audit semantics; it may not silently lower safety controls.
- Production enablement requires model/provider review and explicit configuration, not merely an API key.
