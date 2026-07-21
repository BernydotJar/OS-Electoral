# Campaign operations API

All routes are versioned under `/api/v1`, require a verified bearer identity, load server-owned tenant membership, and authorize the exact principal/tenant/campaign/action/resource/purpose tuple before adapter invocation.

## Roadmap routes

### `POST /tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap`

Creates the single campaign roadmap.

- action: `create`
- resource type: `campaign_roadmap`
- resource ID: campaign UUID
- purpose: `Create campaign operations roadmap`
- required header: one bounded `Idempotency-Key`
- success: `201`, `Location`, quoted `ETag`

### `GET /tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap`

Returns an audited deterministic projection.

- action: `read`
- purpose: `Review campaign operations roadmap`
- success: `200`, quoted `ETag`

### `PATCH /tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap`

Applies a partial versioned update.

- action: `update`
- purpose: `Maintain campaign operations roadmap`
- required headers: exactly one `Idempotency-Key` and quoted positive `If-Match`
- success: `200`, next quoted `ETag`

## Daily War Room routes

### `GET /tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap/war-room-snapshots/latest`

Returns the latest audited immutable snapshot.

- action: `read`
- resource type: `war_room_snapshot`
- purpose: `Review daily campaign war room snapshot`

### `POST /tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap/war-room-snapshots`

Creates one version-bound snapshot for a date.

- action: `create`
- purpose: `Create daily campaign war room snapshot`
- required headers: one `Idempotency-Key` and quoted roadmap `If-Match`
- snapshot is unique per tenant/campaign/date
- success: `201`, `Location`, quoted roadmap `ETag`

## Failure behavior

- `401`: identity missing or invalid;
- `403`: exact application grant absent;
- `404`: scoped roadmap or snapshot absent;
- `409`: existing roadmap, duplicate snapshot date, invalid evidence graph, or idempotency conflict;
- `412`: stale roadmap version;
- `428`: missing write precondition;
- `503`: dependency unavailable or adapter scope/authority drift.

Responses use sanitized problem details. Database constraint names, cross-tenant existence, internal exceptions, raw authorization records, and private payload values are not exposed.

## Transactional evidence

Successful create/update/snapshot writes atomically persist:

1. the roadmap or snapshot;
2. an append-only audit event;
3. an internal outbox event marked `external_effects=NONE`;
4. an idempotency receipt.

No external delivery is performed by these routes.
