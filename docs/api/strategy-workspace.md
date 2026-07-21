# Strategy workspace API

All routes are under `/api/v1`, require a verified bearer identity, load server-owned tenant membership, and authorize the exact principal, tenant, campaign, action, resource type, resource ID, purpose, validity, and revocation state before adapter invocation.

## Routes

### `POST /tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace`

Creates the single campaign Strategy and Decision Room.

- action: `create`
- resource type: `strategy_workspace`
- resource ID: campaign UUID
- purpose: `Create campaign strategy workspace`
- required header: exactly one bounded `Idempotency-Key`
- success: `201`, `Location`, quoted `ETag`

Creation binds the exact current Campaign, Candidate Workspace, and Team Builder versions and the exact Team Builder role-ID snapshot.

### `GET /tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace`

Returns an audited deterministic projection.

- action: `read`
- purpose: `Review campaign strategy workspace`
- success: `200`, quoted `ETag`

### `PATCH /tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace`

Applies a partial evidence/options/objectives update.

- action: `update`
- purpose: `Maintain campaign strategy workspace`
- required headers: exactly one `Idempotency-Key` and quoted positive `If-Match`
- success: `200`, next quoted `ETag`

Any update advances the workspace version and invalidates decision completeness for the new version. Historical receipts remain append-only.

### `POST /tenants/{tenant_id}/campaigns/{campaign_id}/strategy-workspace/decision`

Records the authorized human selection of one internal option for the exact current strategy version.

- action: `approve`
- purpose: `Approve internal campaign strategy option`
- required headers: exactly one `Idempotency-Key` and quoted positive `If-Match`
- body: selected option ID, human reason, and human Team Builder role ID
- success: `200`, quoted workspace `ETag`

The decision is accepted only when:

- the workspace is currently `READY_FOR_HUMAN_DECISION`;
- the option exists in the exact version;
- the human role belongs to the persisted prerequisite role snapshot;
- the version precondition matches;
- no decision already exists for that version;
- the approval receipt and exact application grant are present.

This receipt is internal evidence. It does not authorize contact, publication, spending, mobilization, targeting, or another downstream effect.

## Failure behavior

- `401`: identity missing or invalid;
- `403`: exact application grant absent, including wrong action, purpose, resource, or scope;
- `404`: scoped campaign or strategy workspace absent;
- `409`: prerequisite workspace absent, existing workspace, invalid evidence graph, unsupported decision, or idempotency conflict;
- `412`: stale workspace version;
- `428`: missing write precondition;
- `503`: dependency unavailable or adapter scope/authority drift.

Problem details are sanitized. Cross-tenant existence, database constraint names, internal exceptions, raw authorization records, and private payload values are not exposed.

## Transactional evidence

Successful create/update/decision writes atomically persist:

1. the workspace or append-only decision receipt;
2. an append-only audit event;
3. an internal outbox event marked `external_effects=NONE`;
4. a durable idempotency receipt.

No external delivery or campaign execution occurs in these routes.
