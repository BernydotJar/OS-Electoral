# Campaign creation API

Status: `VERIFIED_POSTGRESQL_LOCAL_ONLY`

Versioned route:

```http
POST /api/v1/tenants/{tenant_id}/campaigns
Authorization: Bearer <OIDC access token>
Idempotency-Key: <caller-stable key>
X-Correlation-ID: <optional caller correlation id>
Content-Type: application/json
```

## Product and authority boundary

This endpoint creates one internal tenant-scoped campaign record with:

```text
status = DRAFT
version = 1
```

It does not create a workspace, strategy, budget approval, publication approval, outreach plan, mobilization authority, legal conclusion, production approval, citizen contact, or any other external political effect. The server owns the campaign identifier, status, version, timestamps, audit identifier, outbox identifier, and idempotency receipt.

## Request contract

```json
{
  "slug": "municipal-2028",
  "name": "Municipal Campaign 2028",
  "jurisdiction": "Antigua Guatemala",
  "stage": "PRECAMPAIGN"
}
```

Only these four fields are accepted. Caller-supplied identifiers, status, version, timestamps, permissions, approvals, evidence identifiers, workspaces, strategy, or downstream actions are rejected.

Normalization occurs before validation:

- `slug` is trimmed, lowercased, limited to 100 characters, and must match `^[a-z0-9]+(?:-[a-z0-9]+)*$`;
- `name` and `jurisdiction` collapse internal whitespace and are limited to 255 characters;
- `stage` collapses internal whitespace and is limited to 80 characters;
- whitespace-only values are invalid.

## Exact authorization contract

The server loads the current application principal, active memberships, and current non-expired/non-revoked grants. Before invoking persistence, one grant must match every field below:

| Field | Required value |
|---|---|
| tenant | exact path `tenant_id` and authorization context tenant |
| campaign | `null` |
| workspace | `null` |
| action | `create` |
| resource type | `campaign_collection` |
| resource identifier | exact path `tenant_id` string |
| purpose | `Create tenant campaign` |
| validity | active, not expired, not revoked |

A role label, generic campaign grant, campaign-scoped grant, workspace-scoped grant, different resource identifier, similar purpose, or tenant selector does not authorize creation.

## Idempotency contract

`Idempotency-Key` is required, trimmed, non-empty, and limited to 255 characters.

The durable request digest binds:

- exact tenant;
- normalized request body;
- application principal;
- exact authorization grant;
- approval-receipt reference;
- exact authorization purpose.

The correlation ID is audit metadata and is deliberately excluded from the digest. A retry with the same key and same bound request/authority returns the exact originally committed response and evidence identifiers; it does not write a second campaign, audit event, outbox event, or idempotency record.

Reusing the key with a different request, grant, approval receipt, or authorization purpose returns:

```json
{
  "status": 409,
  "code": "IDEMPOTENCY_CONFLICT",
  "detail": "Idempotency key conflicts with a previous request"
}
```

PostgreSQL serializes an equal tenant/operation/key tuple with a transaction advisory lock. The table unique constraint remains the final integrity boundary.

## Slug conflict contract

The tenant campaign slug is unique. A different idempotency key cannot create a second campaign with the same normalized slug in the same tenant.

```json
{
  "status": 409,
  "code": "RESOURCE_CONFLICT",
  "detail": "Campaign slug is already reserved"
}
```

The same slug may exist in another tenant. Forced PostgreSQL RLS and tenant-scoped queries prevent cross-tenant visibility.

## Atomic persistence contract

The SQLAlchemy adapter executes inside one `Database.tenant_transaction(tenant_id)` and commits all of the following atomically:

1. campaign `DRAFT` row;
2. `campaign.created` append-only audit event;
3. internal `campaign.created` outbox event;
4. durable idempotency receipt.

The tenant audit stream is locked before the append. The campaign parent is flushed inside the same transaction before its FK-bound audit append. The audit payload binds the application principal, exact authorization grant, approval receipt reference, authorization purpose, correlation ID, normalized campaign metadata, `status=DRAFT`, `version=1`, and `external_effects=NONE`.

The outbox payload is internal evidence only and also records `external_effects=NONE`. No external transport or political action is enabled by this route. If audit, outbox, idempotency, validation, or transaction work fails, the campaign row rolls back with the evidence.

## Success response

```http
HTTP/1.1 201 Created
Location: /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}
ETag: "1"
```

```json
{
  "campaign": {
    "id": "<server UUID>",
    "tenant_id": "<tenant UUID>",
    "slug": "municipal-2028",
    "name": "Municipal Campaign 2028",
    "jurisdiction": "Antigua Guatemala",
    "stage": "PRECAMPAIGN",
    "status": "DRAFT",
    "version": 1
  },
  "audit_event_id": "<UUID>",
  "outbox_event_id": "<UUID>"
}
```

The route verifies that adapter output still matches the authorized tenant, normalized request, `DRAFT` status, and version `1`. Any adapter contract drift fails closed with a sanitized `503`.

## Error contract

| Condition | HTTP | Structured code |
|---|---:|---|
| token missing or invalid | `401` | authentication error |
| tenant membership or exact collection grant absent | `403` | `AUTHORIZATION_DENIED` |
| idempotency key missing or blank | `428` | request precondition error |
| idempotency key longer than 255 characters or duplicated header | `400` | `INVALID_REQUEST` |
| request schema or server-owned field invalid | `422` | validation error |
| same key, different request or authority | `409` | `IDEMPOTENCY_CONFLICT` |
| normalized tenant slug already exists | `409` | `RESOURCE_CONFLICT` |
| database, audit, validation, or adapter contract unavailable | `503` | `AUTHORIZATION_UNAVAILABLE` |

Private database, uniqueness, grant, or digest details are never returned.

## Adapters

- `SqlAlchemyCampaignCreator`: durable PostgreSQL implementation.
- `InMemoryCampaignCreator`: deterministic unit-test adapter.
- `UnavailableCampaignCreator`: fail-closed runtime fallback.

All implement `CampaignCreator`.

## Verification and limitations

Executable evidence is mapped in `docs/testing/c3-api-006-evidence.md`.

The current proof is local and isolated PostgreSQL only. It does not imply CI, review, merge, RDS, dev, staging, production, live identity, complete onboarding, backup/restore, or human production approval.
