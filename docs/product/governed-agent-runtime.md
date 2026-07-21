# Governed Agent Runtime — internal recommendation evidence

## Product boundary

The Governed Agent Runtime helps an authorized human review the exact current Strategy evidence. It can synthesize accepted evidence, compare declared options, or red-team the documented reasoning. It cannot act on behalf of a campaign.

The product object is an append-only **Agent Run**. A run records its Strategy snapshot, policy and prompt-template versions, evidence references, provider identity and budgets, structured recommendation or refusal, and a pending human disposition.

## Human control model

1. A human-owned exact grant authorizes creation of one internal run.
2. CampaignOS loads the Strategy snapshot server-side; the client cannot supply another tenant's context.
3. Deterministic guards decide whether provider invocation is eligible.
4. A provider, when configured in a future reviewed environment, can return structured data only.
5. Deterministic guards validate every field and reference again.
6. CampaignOS records the result as `PENDING` human review with no authority or external effect.
7. Any future acceptance, Strategy change, content creation, publication, spending, contact, or mobilization requires separate product workflows and exact authorization.

## Prompt-injection posture

Research and Strategy evidence is untrusted data. It is serialized in a separate `untrusted_evidence` field, with no tool list and immutable policy metadata. Text such as “ignore previous instructions” inside evidence is retained for provenance but does not become an application instruction. The same language in the authorized instruction is refused before provider invocation.

## Refusal is evidence

The runtime persists deterministic and provider refusals. A refusal is not retried silently with weaker policy, another provider, a larger budget, or a tool-enabled mode. This preserves attribution and prevents fallback from lowering safety.

## Non-capabilities

The runtime has no network tools, browser, search, email, SMS, social publication, ad platform, CRM, voter file, finance, cloud deployment, permission administration, or shell capability. It does not infer individual political preferences, optimize persuasion, generate contact lists, or choose people for targeting.

## Current maturity

The provider abstraction, strict contracts, durable journal, exact API, idempotency, audit, internal no-effect outbox, prompt-injection hard evals, concurrency, and forced RLS are locally/PostgreSQL verified. No live model provider or production data-processing approval exists. Production remains `BLOCKED`.
