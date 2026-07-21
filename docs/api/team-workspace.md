# Team workspace API

`C3-TEAM-001` exposes one internal organizational workspace per tenant and campaign. It persists role cards, RACI work items, availability, vacancies, onboarding, training and access recommendations without creating application authority or external effects.

## Routes

```text
POST  /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace
GET   /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace
PATCH /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/team-workspace
```

| Operation | Action | Resource type | Resource ID | Purpose |
|---|---|---|---|---|
| create | `create` | `team_workspace` | campaign UUID | `Create campaign team workspace` |
| read | `read` | `team_workspace` | campaign UUID | `Review campaign team workspace` |
| update | `update` | `team_workspace` | campaign UUID | `Maintain campaign team workspace` |

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