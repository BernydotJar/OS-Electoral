# C3-SEC-002 evidence — tenant/principal rate limiting

Date: `2026-07-29`
Mode: `SHIP`
State: `CI_GREEN`
Production: `BLOCKED`
External effects: `NONE`

## Delivered control

CampaignOS now has a complete server-owned rate-limit catalog across all 41 protected API routes. The additive PostgreSQL table uses database time, an exact composite key, atomic UPSERT, capped counters and forced tenant RLS. Health and readiness remain exempt; metrics preserves bearer authentication and consumes an operational budget after authentication.

The implementation stores only tenant UUID, opaque principal UUID, policy class/version, window and count metadata. It does not store token, email, IP, request content, campaign text, voter data or political preference.

## Acceptance evidence

- route inventory proves exact method/path-to-policy coverage and an explicit enforcement call;
- BOLA denial occurs before tenant budget mutation;
- allowed scope denial occurs before domain service execution;
- preauthorization uses fixed internal scope and opaque UUIDv5 principal;
- `429` includes `Retry-After` and correlation ID without key or count disclosure;
- missing policy metadata and store failure return sanitized fail-closed `503`;
- staging/production settings reject disabled enforcement;
- low-cardinality metrics reject arbitrary labels;
- migration reaches `20260729_0012`, has forced RLS and passes Alembic check;
- 20 concurrent requests against a limit of 5 produce exactly 5 allows and 15 denials, with one stored count capped at 6;
- tenant, principal, class, version and one-second window rollover are isolated;
- the public limiter owns the tenant-scoped transaction and exposes no caller-owned transaction path;
- independent rate-limit commit survives later domain rollback so failing abuse attempts are counted;
- cleanup is timezone-aware, tenant-scoped and bounded to 1–1,000 rows.

## Local verification

```text
make verify
Python: 749 passed, 11 skipped
Coverage: 90.31%
Frontend: 119 passed
npm audit: 0 vulnerabilities
Ruff / format / mypy: PASS
Terraform plan-only: PASS
Security / program / release validators: PASS
```

```text
make test-postgres
11 passed, 5 deselected
PostgreSQL 15.18 isolated cluster
UTF8
Data checksums: enabled
```

Hosted exact-head CI used PostgreSQL 18 and passed the migration, forced-RLS, concurrency, rollover, rollback and cleanup contracts.

## Localized repair history

1. Initial PostgreSQL test import exposed a cycle because the security core imported the API error adapter. The implementation split `campaignos.security.rate_limits` from `campaignos.api.rate_limits`; the security core is now framework-independent.
2. The temporary PostgreSQL harness initially generated an invalid empty-port URL. The local harness was corrected; no product file depended on it.
3. A repeated PostgreSQL test found stale rows from an earlier invocation. The isolated test now truncates only its own `rate_limit_buckets` table before execution.
4. Review expanded coverage from 40 domain routes to 41 protected routes by including authenticated metrics after token verification.
5. `make test-postgres` now suppresses command echo so database credentials are not written to logs.

No failed product validation remains unresolved locally. Historical execution details are preserved without converting environment/harness failures into product defects.

## Remaining production gates

- multi-instance managed staging load and contention proof;
- cleanup scheduler and approved retention period;
- edge DDoS/WAF and invalid-token abuse controls;
- deployed telemetry, alert routing and on-call ownership;
- independent security, privacy, database, operational and legal review;
- explicit production approval.


## Hosted exact-head evidence

```text
validated implementation head: c5261d547b1f4149ed1cb55c122159a9fe661d81
draft PR: #128 (base PR #127)
CampaignOS CI: 30431102657 SUCCESS
Runtime Visual Review: 30431101415 SUCCESS
PostgreSQL migrations/RLS: job 90508299364 SUCCESS
Constrained stack E2E: job 90508299414 SUCCESS
Recovery: job 90508299295 / artifact 8715541657
Frontend/browser: job 90508299282 / artifact 8715594812
CodeQL: job 90508299406 SUCCESS
Dependency audit: job 90508299314 SUCCESS
Secret scan: job 90508299288 / artifact 8715535489
Supply chain: job 90508299272 / artifact 8715533651
Terraform plan-only: job 90508299338 SUCCESS
Runtime visual artifact: 8715553353
```

Artifact digests are recorded in `program/validations/c3-sec-002.json`. Exact-head CI closes the repository verification gate only. Managed staging load, cleanup scheduling, edge controls, deployed observability, independent approvals, human merge and production release remain open.
