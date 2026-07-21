# C3-AGENT-001 — Governed provider-neutral recommendation runtime

- `branch`: `agent/c3-agent-001-governed-runtime`
- `base`: `agent/c3-api-001-reconciliation@837f383e215bdd54c0b4ad2a9bd73ba5c366d76c`
- `status`: `VERIFIED_POSTGRESQL`
- `production_status`: `BLOCKED`
- `external_effects`: `NONE`

## Bounded objective

Implement a provider-neutral, evidence-bound runtime that can produce structured **internal recommendations for human review** from the exact persisted Strategy workspace version. The runtime is not an autonomous actor and has no tool, network, publication, spending, targeting, contact, grant-management, deployment or mobilization capability.

## Acceptance criteria

1. Application-owned provider interface; no provider SDK or credential is required.
2. Default provider is unavailable/no-effect and never performs a network call.
3. Exact tenant/campaign/Strategy workspace version is loaded server-side; client context is not trusted.
4. Prompt envelope is policy/template versioned, canonicalized and digestible.
5. Evidence is minimized, delimited and explicitly marked untrusted data.
6. Purpose allow-list is limited to evidence synthesis, option comparison and red-team review.
7. Tool list is always empty and any provider tool-call attempt is rejected.
8. Deterministic pre-guards reject prohibited instructions and budget excess before provider invocation.
9. Structured post-guards reject invalid schema, unknown evidence references, unsupported claims, prohibited output, stale options and provider budget excess.
10. Run, audit, internal outbox and idempotency receipt commit atomically under tenant RLS.
11. Same key/request/authority/snapshot replays exactly; changed intent conflicts without a second provider call or mutation.
12. Refusals are attributable and persist without converting model output into authority.
13. Hard evals cover prompt injection, unsupported claims, tool calls, cross-tenant scope, budget overflow and external-action refusal.
14. API requires exact campaign-scoped create/read grants and fails closed on scope drift.
15. Every result declares `human_disposition=PENDING`, `authority_effect=NONE`, `external_effects=NONE`.

## Explicit non-goals

- no OpenAI, Anthropic, Bedrock or other live provider adapter;
- no browsing, retrieval network, plugins, shell, email, publication or campaign-system integration;
- no voter profiling, individual targeting, persuasion optimization or citizen contact;
- no automatic approval, strategy mutation, grant change or downstream execution;
- no claim of production provider/privacy/data-processing approval.


## Local/PostgreSQL checkpoint — 2026-07-21

- revision `20260721_0010`, strict provider-neutral contracts and append-only Agent Run journal;
- 18 deterministic runtime adversarial tests and 60 focused Agent/worker tests with 2 controlled skips;
- full locked suite: 628 passed, 9 skipped, 90.95% coverage;
- PostgreSQL combined gate: 9 selected slices, two clean consecutive runs;
- equal-key concurrent replay invokes the provider once and persists one run/audit/outbox/idempotency receipt;
- forced RLS cross-tenant read/write denial under `NOSUPERUSER NOBYPASSRLS`;
- prompt-injection eval elevated to PARTIAL; provider privacy and production enablement remain absent;
- production remains `BLOCKED`; branch publication/CI are pending and external effects remain `NONE`.
