# Candidate workspace API

`C3-CANDIDATE-001` exposes one internal candidate evidence workspace per tenant and campaign. The API stores structured evidence, calculates deterministic internal readiness and appends exact version-bound section approvals. Public use remains blocked and no external effect is executed.

## Routes

```text
POST  /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace
GET   /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace
PATCH /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace
POST  /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace/section-approvals
```

All routes require a verified bearer principal and an exact active grant. Tenant and campaign path values identify the requested resource but never create authority.

| Operation | Action | Resource type | Resource ID | Purpose |
|---|---|---|---|---|
| create | `create` | `candidate_workspace` | campaign UUID | `Create candidate evidence workspace` |
| read | `read` | `candidate_workspace` | campaign UUID | `Review candidate evidence workspace` |
| update | `update` | `candidate_workspace` | campaign UUID | `Maintain candidate evidence workspace` |
| approve section | `approve` | `candidate_workspace` | campaign UUID | `Approve candidate evidence section` |

Every grant must also contain the same campaign UUID, a null workspace scope, a current validity window and no revocation.

## Create

Creation requires exactly one non-empty `Idempotency-Key` of at most 255 characters. The campaign must exist in `DRAFT` or `ACTIVE` state, have at least one active workspace and have a guided intake that dynamically reassesses to `READY_FOR_RESEARCH`.

The response is `201 Created`, with a canonical `Location` and quoted positive `ETag`. The new workspace begins at version 1 with no evidence, `SETUP_REQUIRED`, `public_use_status=BLOCKED` and `external_effects=NONE`.

Concurrent same-key requests replay exactly. Distinct keys racing to create the one campaign workspace produce one creation and one stable conflict.

## Read

`GET` returns the current deterministic projection and appends a sensitive-read audit receipt. It emits no outbox event. Missing and cross-scope resources are not exposed before exact authorization succeeds.

## Update

`PATCH` requires exactly one `Idempotency-Key` and one positive `If-Match` version. It accepts a bounded partial replacement of:

- display name;
- evidence inventory;
- identity;
- biography;
- purpose;
- values;
- attributes;
- contradictions;
- development goals;
- reputation risks.

Unknown fields, duplicate IDs, unknown references, invalid classifications and profiling-score fields are rejected. A successful update increments the workspace version, making prior approvals historical rather than current. A stale version returns `412`.

## Approve section

The approval route requires exactly one `Idempotency-Key`, one `If-Match`, an exact section and a bounded reason. The section must be complete and must not already have a current receipt for the same workspace version.

Approval appends a receipt without changing the evidence version. It can advance the internal projection to `INTERNALLY_APPROVED`, but the response continues to state:

```text
public_use_status=BLOCKED
external_effects=NONE
```

## Evidence semantics

A `VERIFIED` claim requires accepted independent evidence from the same workspace. Candidate self-assessment alone cannot verify an attribute. Perception references must resolve only to `PERCEPTION` evidence. Attribute contradiction references must resolve to candidate contradiction records. Open `CRITICAL` or `HIGH` reputation risks prevent the reputation section from becoming approvable.

## Persistence

Revision `20260721_0006` adds:

- `candidate_workspaces`;
- `candidate_section_approvals`;
- composite tenant/campaign foreign keys;
- one workspace per tenant/campaign;
- one approval per tenant/workspace/section/version;
- forced PostgreSQL RLS on both tables;
- tenant-leading indexes.

Create, read, update and approve append audit evidence. Every successful write also appends an internal outbox row declaring `external_effects=NONE`. Aggregate mutation, approval receipt, audit, outbox and idempotency evidence commit atomically.

## Error behavior

Authorization mismatches are rejected before the adapter is invoked. Conflicts, stale versions, missing resources and dependency failures use stable sanitized problem codes. Database constraint names, exception messages, cross-tenant existence and internal payloads are not returned.