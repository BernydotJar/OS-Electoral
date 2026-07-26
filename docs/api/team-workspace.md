# Team workspace API

`C3-TEAM-001` exposes one internal organizational workspace per tenant and campaign. It persists role cards, RACI work items, availability, vacancies, onboarding, training and access recommendations without creating application authority or external effects.

## Routes

```text
POST  /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace
GET   /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace
PATCH /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace
POST  /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace/template-preview
POST  /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace/template-apply
```

| Operation | Action | Resource type | Resource ID | Purpose |
|---|---|---|---|---|
| create | `create` | `team_workspace` | campaign UUID | `Create campaign team workspace` |
| read | `read` | `team_workspace` | campaign UUID | `Review campaign team workspace` |
| update | `update` | `team_workspace` | campaign UUID | `Maintain campaign team workspace` |
| template preview | `update` | `team_workspace` | campaign UUID | `Maintain campaign team workspace` |
| template apply | `update` | `team_workspace` | campaign UUID | `Maintain campaign team workspace` |

Every grant must also contain the same campaign UUID, null workspace scope, current validity and no revocation. Roles are informational labels and never satisfy authorization.

## Create

Creation requires one non-empty `Idempotency-Key`. The campaign must exist and a candidate workspace must already be present. The response is `201 Created` with `Location` and a quoted positive `ETag`.

Concurrent requests using the same key replay exactly. Distinct keys racing to create the one campaign workspace produce one success and one stable conflict.

## Read

Read returns the deterministic projection and appends a sensitive-read audit receipt. No outbox event or external call occurs.

## Update

Update requires one `Idempotency-Key` and one positive `If-Match` version. It may replace:

- organization template;
- role cards;
- RACI work items;
- training requirements;
- access recommendations.

A successful mutation increments the version and commits the aggregate, audit event, internal outbox event and idempotency receipt atomically.

## Organizational validation

- active work has one accountable and at least one responsible filled role;
- role, training and RACI references remain inside the same workspace;
- filled/vacant lifecycle fields are mutually exclusive;
- access recommendations are campaign-bound and scope-canonical;
- a non-null recommended workspace must be active and belong to the same tenant/campaign;
- `authority_effect` and `external_effects` are always `NONE`;
- unknown fields, duplicate IDs and duplicate RACI assignments are rejected.

## Persistence

Revision `20260721_0007` adds `team_workspaces` with a composite tenant/campaign foreign key, one-workspace-per-campaign uniqueness, tenant-leading index and forced PostgreSQL RLS.

The service stores organizational role cards only inside the team document. It never inserts rows into authorization tables such as `roles` or `permission_grants`.

## Error behavior

Authorization mismatches fail before adapter invocation. Conflicts, missing prerequisites, stale versions, missing resources and dependency failures use stable sanitized problem codes. Adapter scope drift and corrupt persisted recommendation scope fail closed.
## Versioned role-blueprint creation

Creation accepts the locale used to materialize the initial job descriptions:

```json
{
  "organization_template": "LEAN_CAMPAIGN",
  "blueprint_locale": "es"
}
```

`blueprint_locale` is restricted to `es` or `en` and defaults to `es` for backward-compatible API clients. It is included in the idempotency digest, so one idempotency key cannot replay with a different language or template.

For `LEAN_CAMPAIGN` and `FULL_CAMPAIGN`, the service builds the role cards before the transaction and commits the workspace, generated roles, audit event, internal outbox event and idempotency receipt atomically. `CUSTOM` stores no generated role cards.

Audit and internal outbox evidence record the immutable blueprint version and seeded-role count. Generated role cards are organizational data only: they create no principal assignment, application membership, permission grant, access recommendation, capacity, onboarding completion or external effect.

## Preview and append-only template application

`C3-TEAM-003` adds two exact-authorized operations for evolving an existing team map without replacing current organization data:

```text
POST /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace/template-preview
POST /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace/template-apply
```

Both operations require the exact `update` grant for `team_workspace`, the campaign UUID as resource ID, null workspace scope and purpose `Maintain campaign team workspace`.

### Preview

Preview requires a quoted positive `If-Match` version and accepts only `LEAN_CAMPAIGN` or `FULL_CAMPAIGN` plus `es` or `en`. It:

- reads the current version under tenant scope;
- recognizes equivalent built-in functions across Spanish and English;
- falls back to normalized exact title-and-area matching for historical role cards;
- proposes deterministic UUIDv5 role IDs for missing functions;
- returns additions, preserved matches, the blueprint version and a SHA-256 preview digest;
- appends an audit receipt bound to the principal, grant, approval receipt, purpose and correlation ID;
- creates no outbox event, role assignment, capacity, membership, permission or external effect.

### Apply

Apply requires the same `If-Match`, a non-empty `Idempotency-Key` and the exact preview digest. Inside one transaction it locks the workspace, recalculates the preview and fails closed when the version or digest changed. A successful application:

- appends only missing vacant role cards;
- preserves every existing role card and its identity, lifecycle and responsibilities;
- increments the workspace version;
- records counts for added and preserved functions;
- commits audit, internal outbox and idempotency evidence atomically;
- keeps `authority_effect=NONE` and `external_effects=NONE`.

A preview with no additions cannot be applied. Digest drift returns `TEAM_TEMPLATE_PREVIEW_CONFLICT`; an already-complete template returns `TEAM_TEMPLATE_NO_CHANGES`.
