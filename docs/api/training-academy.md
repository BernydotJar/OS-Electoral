# Training Academy API

All routes require authenticated tenant context, exact campaign-scoped permission grants, and the reviewed purpose string. Role labels and course completion are never authorization inputs.

Base path:

```text
/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/training
```

## Authorization matrix

| Operation | Action | Purpose |
|---|---|---|
| Read approved catalog | `training.catalog.read` | `Review approved training catalog` |
| Read own assignments | `training.self.read` | `Review own campaign training` |
| Create an assignment | `training.assignment.manage` | `Assign campaign learning path` |
| Read one assignment administratively | `training.assignment.read` | `Review campaign training assignment` |
| Start/attempt an assigned module | `training.self.complete` | `Complete assigned campaign training` |
| Read own completion receipts | `training.receipt.read` | `Review own campaign training` |

Every grant must target `resource_type=training_academy`, the exact campaign resource ID, the same campaign, and no workspace.

## Routes

### `GET /catalog?locale=es|en`

Returns the approved localized module and learning-path projection. Correct answer IDs are removed from the response.

### `GET /me`

Returns assignments for the authenticated principal only. The service and route both verify tenant, campaign, principal, and `authority_effect=NONE`.

### `POST /assignments`

Creates one approved learning-path assignment for an active principal in the same tenant/campaign. Requires exactly one `Idempotency-Key` header and the current catalog SHA-256 digest.

The service enforces:

- maximum 25 active assignments per principal;
- maximum 200 active assignments per campaign;
- unique principal/path/version assignment;
- optional role slug must be eligible for the selected path;
- no retired or unknown module version.

### `GET /assignments/{assignment_id}`

Returns one exact-scoped assignment for an authorized manager/reviewer.

### `POST /assignments/{assignment_id}/modules/{module_id}/start`

Starts one assigned module. Only the assigned principal can execute it. The request requires the observed assignment version, progress version, catalog digest, and one idempotency key.

### `POST /assignments/{assignment_id}/modules/{module_id}/attempts`

Submits one bounded assessment. Only the assigned principal can execute it. The request must cover every question exactly once and reference only current option IDs.

A passing attempt writes an append-only completion receipt in the same transaction as progress, assignment, audit, and idempotency evidence. A failed attempt increments the bounded attempt count without a receipt.

### `GET /me/assignments/{assignment_id}/receipts`

Returns completion receipts only when the assignment belongs to the authenticated principal.

## Persistence and isolation

Migration `20260801_0013` adds:

- `training_assignments`;
- `training_module_progress`;
- `training_completion_receipts`.

All three tables carry tenant/campaign scope and forced PostgreSQL row-level security. Scoped composite foreign keys prevent cross-tenant assignment/progress/receipt references. The completion receipt table rejects `UPDATE` and `DELETE` through the repository append-only trigger.

## Idempotency and version conflicts

Assignment, start, and attempt mutations use tenant-scoped advisory locking plus persisted idempotency records. Reusing a key with different intent returns a conflict. Exact JSON evidence is replayed for an identical request.

The current catalog digest and observed assignment/progress versions are required. Stale values fail with `412` and do not partially mutate state.

## Failure behavior

- missing/mismatched grant: `403`;
- missing or duplicate idempotency header: `428`;
- stale catalog or state version: `412`;
- state, attempt-limit, or idempotency conflict: `409`;
- hidden or cross-scope resource: `404` or fail-closed service response;
- audit/database/catalog integrity failure: `503` with the transaction rolled back.
