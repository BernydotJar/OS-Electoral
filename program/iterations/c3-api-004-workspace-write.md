# C3 API workspace write boundary — 2026-07-21

- `branch`: `agent/c3-api-004-workspace-write`
- `base`: `agent/c3-api-003-outbox-worker@0f38361`
- `production_status`: `BLOCKED`
- `external_effects`: none; workspace creation persists internal state and evidence only.

## Implementation

- Added `POST /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/workspaces`.
- Requires an exact campaign-scoped `create/workspace` grant with purpose `Configure assigned campaign workspace`.
- Performs authorization before validating the mandatory `Idempotency-Key` header.
- Creates only lowercase kebab-case workspace slugs and bounded names.
- Serializes equal PostgreSQL idempotency keys with a transaction-scoped advisory lock.
- Commits workspace, `workspace.created` audit, outbox and idempotency evidence atomically.
- Replays an identical request without mutation and rejects a changed request under the same key.
- Extends the internal worker validator for `workspace.created` without network delivery.
- Delivery requires matching topic, audit type, resource, workspace, tenant and campaign scope.

## Verification

- Maintained backend Ruff lint and format gates: PASS.
- Strict mypy across 29 source files: PASS.
- Full locked suite: `256 passed`, `1 skipped`.
- Program truth: PASS with production still `BLOCKED`.
- Campaign safety scan: PASS.

## Remaining C3-API-001 blockers

- Candidate, approval, assignment and artifact domain writes.
- Worker administration and observability.
- Reviewed external event transport.
- Staging concurrency/recovery evidence and production approval.
