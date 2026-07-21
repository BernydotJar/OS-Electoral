# Governed internal agent runs API

CampaignOS exposes a bounded provider-neutral recommendation boundary. It records either a structured internal recommendation or a deterministic refusal for human review. It is not an autonomous action API.

## Create a run

`POST /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/agent-runs`

Required controls:

- valid authenticated principal and current server-owned tenant authorization;
- exact `create/agent_run` grant over the campaign identifier;
- purpose `Create internal governed recommendation run`;
- exactly one non-empty `Idempotency-Key`;
- exact current Strategy workspace version;
- allowed purpose: evidence synthesis, option comparison, or red-team review;
- bounded output token, timeout, and cost ceilings.

A `201` means an append-only run journal was recorded. The journal can contain `COMPLETED` or `REFUSED`; neither status grants authority. Every response fixes:

```yaml
human_disposition: PENDING
authority_effect: NONE
external_effects: NONE
```

The response includes the run projection, audit event identifier, internal outbox event identifier, provider/model metadata when a provider responded, prompt digest, usage/cost metadata, evidence and option references, and a sanitized refusal when applicable. The raw instruction is not stored; only its SHA-256 digest is persisted.

## Read a run

`GET /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/agent-runs/{run_id}`

Requires an exact `read/agent_run` grant with purpose `Review internal governed recommendation run`. A successful read appends an audit receipt and emits no new outbox event.

## Deterministic safety behavior

Before provider invocation, CampaignOS rejects stale/ineligible Strategy snapshots, prohibited instructions, and oversized authorized context. Evidence is placed in a dedicated `untrusted_evidence` field and cannot add tools or rewrite policy.

After provider response, CampaignOS rejects:

- provider/model identity drift;
- provider refusal or unavailability;
- any tool call;
- token, latency, or cost budget excess;
- invalid output schema;
- unknown evidence or option references;
- supported claims based on unknown/unaccepted evidence;
- output requesting disclosure, publication, citizen contact, spending, targeting, grant changes, deployment, or mobilization.

Refusals are persisted as attributable internal evidence. No live provider adapter is configured by default; the default adapter performs no network call and records `PROVIDER_UNAVAILABLE`.

## Idempotency and atomicity

The idempotency digest binds request, principal, grant, approval receipt, purpose, and Strategy version. Equal concurrent keys replay the original evidence and invoke the provider once. Changed request or authority under the same key returns `409 IDEMPOTENCY_CONFLICT` without another provider call or mutation.

Run, audit, internal outbox, and replay evidence commit atomically under tenant RLS. The internal `agent.run.recorded` event is envelope-validated by the existing worker and has no external transport.

## Limitations

- no OpenAI, Anthropic, Bedrock, browsing, retrieval network, plugin, shell, email, social, or campaign-system adapter;
- no automatic Strategy mutation or human disposition transition;
- no voter profiling, individual targeting, persuasion optimization, citizen contact, publication, spending, deployment, or mobilization;
- no production provider, privacy, retention, data-processing, residency, load, staging, or customer acceptance claim;
- production remains `BLOCKED`.
