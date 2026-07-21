# C3-API-001 — Cumulative API and background-job baseline reconciliation

- `branch`: `agent/c3-api-001-reconciliation`
- `base`: `agent/c3-strategy-001-evidence-decision-room@427ed62cc8272efe9515d908d590187cfee94ae8`
- `status`: `VERIFIED_POSTGRESQL`
- `production_status`: `BLOCKED`
- `external_effects`: `NONE`

## Reconciliation premise

`C3-API-001` is an umbrella milestone whose original protected campaign read/write boundary was merged in PR `#83`. The work once listed as missing was subsequently delivered and verified through the stacked increments for durable idempotency, recoverable outbox processing, workspace creation, campaign readiness and campaign creation. This increment changes no product behavior; it reconciles the umbrella against the cumulative repository and GitHub evidence.

## Baseline acceptance

1. Every public application route is versioned under `/api/v1`, with versioned OpenAPI.
2. `/health` is public liveness; `/ready` checks identity and database dependencies and returns `503` fail closed.
3. Authentication and authorization errors use sanitized Problem Details and server-owned tenant membership/grant evidence.
4. Campaign reads, lists, updates, creation and readiness enforce exact tenant/campaign/resource/purpose authorization.
5. Mutating boundaries use optimistic versions and/or durable tenant-scoped idempotency as appropriate.
6. State, audit receipt, internal outbox and replay evidence commit atomically.
7. The internal outbox worker uses explicit tenant scopes, `SKIP LOCKED`, leases, bounded retries, dead letter and graceful stop.
8. PostgreSQL migrations, forced RLS, constrained roles, replay races and tenant isolation pass.
9. No handler performs network delivery or grants publication, targeting, contact, spending or mobilization authority.
10. Worker administration, dead-letter replay UI, telemetry and external event transport remain separate observability/platform increments.

## Cumulative delivery evidence

- PR `#83`: original protected campaign read/write boundary, merged with CI `29802998261`.
- PR `#84`: durable idempotency.
- PR `#85`: recoverable outbox worker.
- PR `#86`: idempotent workspace write.
- PR `#87`: audited campaign readiness.
- PR `#88`: idempotent tenant campaign creation.
- Later exact-authorized Candidate, Team, Strategy and Operations APIs demonstrate that the baseline is extensible without bypassing its contracts.

## Local checkpoint — 2026-07-21

- Ruff/format/mypy over 27 maintained API/worker source files: PASS.
- Focused cumulative API/worker suite: 120 passed.
- Full inherited exact-head suite before reconciliation docs: 585 passed, 8 skipped, 90.70% coverage.
- PostgreSQL combined gate: 8 selected slices, two clean consecutive runs, migration head `20260721_0009`.
- Program truth/eval/safety: PASS with production still `BLOCKED`.

## Remaining limitations

- Human review and merge of the stacked review branches remain pending.
- No live identity provider, RDS, staging, production, telemetry, backup/restore or customer acceptance is claimed.
- No worker control plane, dead-letter replay UI or external transport exists.
- No external campaign effect is authorized or implemented by this baseline.
