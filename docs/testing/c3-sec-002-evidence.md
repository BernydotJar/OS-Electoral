# C3-SEC-002 evidence — tenant/principal rate limiting

Date: `2026-07-29`  
Mode: `SHIP`  
State: `REVIEWED_LOCAL`  
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
- mismatched transaction scope fails before SQL;
- shared-transaction rollback removes the counter mutation;
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

The hosted CI PostgreSQL baseline uses PostgreSQL 18 and remains required at the exact published head.

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
