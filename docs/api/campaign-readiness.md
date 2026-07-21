# Campaign readiness API

Status: `IMPLEMENTED_LOCAL`

Versioned route:

```http
GET /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/readiness
Authorization: Bearer <OIDC access token>
X-Correlation-ID: <optional caller correlation id>
```

## Purpose and boundary

This endpoint reports whether a persisted campaign has the minimum **operational setup** required to begin the guided intake journey. It does not assess political viability, legality, finance approval, security approval, publication approval, production readiness, citizens, voters, persuasion, or campaign strategy.

The response always includes:

```json
{
  "readiness": {
    "readiness_scope": "OPERATIONAL_SETUP_ONLY",
    "status": "READY_FOR_GUIDED_INTAKE",
    "ready_for_guided_intake": true,
    "next_action": "BEGIN_GUIDED_INTAKE",
    "limitation_codes": [
      "NOT_A_HUMAN_APPROVAL",
      "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT"
    ]
  },
  "audit_event_id": "<uuid>"
}
```

A positive result is not a gate receipt and never grants authority.

## Exact authorization contract

The server loads the current application principal, active membership and non-expired/non-revoked grants. Before the readiness adapter is invoked, one grant must match every field below:

| Field | Required value |
|---|---|
| tenant | path `tenant_id` and authorization context tenant |
| campaign | path `campaign_id` |
| workspace | `null` |
| action | `read` |
| resource type | `campaign_readiness` |
| resource identifier | exact path `campaign_id` string |
| purpose | `Assess assigned campaign readiness` |
| validity | active, not expired, not revoked |

A generic `campaign:read` grant, role label, tenant selector, foreign campaign identifier, workspace-scoped grant or similar purpose does not authorize this endpoint.

## Deterministic policy

The projection evaluates four ordered checks from persisted tenant-scoped facts:

1. campaign name is non-blank;
2. jurisdiction is non-blank;
3. campaign stage is non-blank;
4. at least one workspace is `ACTIVE` for the exact campaign.

Possible states:

| Status | Next action |
|---|---|
| `NEEDS_CAMPAIGN_METADATA` | `COMPLETE_CAMPAIGN_METADATA` |
| `NEEDS_CAMPAIGN_WORKSPACE` | `CREATE_CAMPAIGN_WORKSPACE` |
| `READY_FOR_GUIDED_INTAKE` | `BEGIN_GUIDED_INTAKE` |

Archived campaigns are not assessed. Archived workspaces do not count.

## Persistence and audit semantics

The SQLAlchemy adapter executes under `Database.tenant_transaction(tenant_id)` and forced PostgreSQL RLS. It locks the stable tenant row before reading the campaign so audited reads are ordered with campaign/workspace mutations.

Every successful response appends one `campaign.readiness_viewed` event to the tenant audit chain in the same database transaction. The event records the application principal, exact grant, approval receipt reference, purpose, correlation ID, campaign version, readiness result and `external_effects=NONE`.

The shared audit appender:

- requires a session-bound tenant lock token;
- assigns a monotonic timezone-aware timestamp after the lock is acquired;
- links `previous_hash` to the current tenant head;
- hashes canonical event evidence;
- flushes before another append can observe the head;
- rolls back the read receipt if any later transaction step fails.

This observation-only endpoint emits **no outbox event** and cannot trigger external delivery.

## Error contract

| Condition | HTTP | Structured code |
|---|---:|---|
| token missing or invalid | `401` | authentication error |
| tenant membership or exact grant absent | `403` | `AUTHORIZATION_DENIED` |
| campaign absent, archived or hidden by RLS | `404` | `RESOURCE_NOT_FOUND` |
| database, validation, audit or adapter-scope invariant unavailable | `503` | `AUTHORIZATION_UNAVAILABLE` |

Private database or authorization details are never returned.

## Adapters

- `SqlAlchemyCampaignReadinessReader`: durable PostgreSQL implementation.
- `InMemoryCampaignReadinessReader`: deterministic unit-test adapter.
- `UnavailableCampaignReadinessReader`: fail-closed runtime fallback.

All implement `CampaignReadinessReader`.

## Verification

The executable evidence is mapped in `docs/testing/c3-api-005-evidence.md`. OpenAPI must expose the typed `CampaignReadinessEvidence` schema and bearer security requirement.
