# C3 API recoverable outbox worker — 2026-07-21

- `branch`: `agent/c3-api-003-outbox-worker`
- `base`: `agent/c3-api-002-idempotency@50a4a76`
- `production_status`: `BLOCKED`
- `external_effects`: none; the only handler validates internal campaign and audit evidence and performs no network delivery.

## Implementation

- Tenant-explicit runtime; no global cross-tenant scan under RLS.
- `FOR UPDATE SKIP LOCKED` claims with worker ownership and expiring leases.
- Recovery of expired `PROCESSING` rows.
- Bounded exponential retries and terminal `DEAD_LETTER` state.
- Delivery requires the same lease owner and revalidates tenant-scoped campaign and audit evidence.
- Stored errors contain only exception class names, not arbitrary messages.
- CLI supports repeated `--tenant-id`, bounded batch/poll values, `--once`, and graceful SIGTERM/SIGINT.
- `make worker-once TENANT_ID=<uuid>` is available for a bounded local pass.

## Verification

- Full locked verification: `247 passed`, `1 skipped`.
- Ruff, formatting, strict mypy, program truth, and campaign safety scan: PASS.
- First PostgreSQL E2E detected missing model metadata for `ix_outbox_events_recoverable`.
- After repair, repeated E2E passed migration `0003`, `alembic check`, constrained API role, PostgreSQL, S3Mock, and Mailpit gates.
- Production remains blocked; no external transport, worker administration, staging proof, or production approval exists.

## Remaining C3-API-001 blockers

- Broader domain writes.
- Worker administration and observability.
- Reviewed external event transport.
- Staging concurrency and recovery evidence.
