# Guided intake API

`C3-ONBOARD-001` exposes one resumable guided intake per tenant and campaign. The API records bounded campaign context and produces deterministic research-first next actions. It does not generate strategy, approve a candidate or budget, contact citizens, publish, spend, mobilize, or create authority.

## Routes

```text
POST  /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/guided-intake
GET   /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/guided-intake
PATCH /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/guided-intake
```

All routes require a verified bearer principal and an exact active grant. Tenant and campaign identifiers in the path select the requested resource; authority is derived only from the server-owned tenant authorization context.

| Operation | Action | Resource type | Resource ID | Purpose |
|---|---|---|---|---|
| start or resume | `create` | `guided_intake` | campaign UUID | `Begin guided campaign intake` |
| read | `read` | `guided_intake` | campaign UUID | `Review guided campaign intake` |
| update | `update` | `guided_intake` | campaign UUID | `Maintain guided campaign intake` |

Every grant must also contain the same campaign UUID, a null workspace scope, a current validity window and no revocation.

## Start or resume

`POST` requires exactly one non-empty `Idempotency-Key` of at most 255 characters. A first request creates a blank `IN_PROGRESS` intake only after campaign name, jurisdiction, stage and one active workspace are present. A later request with a new key resumes the same aggregate. Replaying the same key and exact authority returns the original committed evidence.

Responses use `201 Created` for the first creation and `200 OK` for resume or replay. `Location` identifies the canonical intake resource and `ETag` contains the quoted positive version.

## Read

`GET` returns the current projection and appends a sensitive-read audit receipt. It does not emit an outbox event. A missing intake returns a sanitized `404` only after exact authorization succeeds.

## Update

`PATCH` requires:

- exactly one `Idempotency-Key`;
- a quoted or unquoted positive `If-Match` version;
- at least one bounded field;
- no unknown fields;
- normalized non-blank text;
- arrays with at most 30 unique items of at most 255 characters each.

`null` clears an assessed optional field. An empty array means the section was assessed and no items were found. `budget_status` cannot be null. A stale version returns `412`; changed intent or authority under the same idempotency key returns `409`.

## Deterministic projection

The response contains eight canonical checks in this order:

1. campaign operational setup;
2. target office;
3. candidate project;
4. current team assessed;
5. current assets assessed;
6. budget evidence assessed;
7. known unknowns recorded;
8. evidence requirements defined.

Statuses are `BLOCKED_BY_CAMPAIGN_SETUP`, `IN_PROGRESS`, or `READY_FOR_RESEARCH`. `READY_FOR_RESEARCH` requires all checks and exposes exactly seven bounded evidence-collection actions. It is not a human approval or a strategy decision.

Mandatory limitations are always returned:

```text
NOT_A_STRATEGY
NOT_A_HUMAN_APPROVAL
NO_CITIZEN_CONTACT_OR_PROFILING
NO_EXTERNAL_EFFECTS
```

## Persistence and evidence

Revision `20260721_0005` adds the tenant/campaign-owned aggregate with a composite foreign key, unique tenant/campaign boundary, forced PostgreSQL RLS and bounded status constraints. Start, resume, read and update append audit evidence. Creation and update also append internal outbox rows whose payload explicitly records `external_effects=NONE`. Audit, outbox, aggregate mutation and idempotency evidence commit atomically.

## Error behavior

Authorization mismatch is rejected before invoking the adapter. Constraint, concurrency and adapter failures are mapped to stable sanitized responses. Internal database details, cross-tenant existence and raw exception messages are not returned.