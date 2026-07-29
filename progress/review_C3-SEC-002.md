# C3-SEC-002 SHIP review

Feature: `C3-SEC-002 — Tenant and principal rate limiting and abuse protection`
Mode: `SHIP`
Date: `2026-07-29`
Implementation branch: `agent/c3-sec-002-rate-limiting-abuse-protection`
Base: `agent/c3-harness-001-graph-reconciliation@5e0818b6dc85376fdaa08cf2ab0af9c2d21460ea`

## Reviewer separation

The implementation role completed code and tests. The following review roles inspected the resulting worktree and evidence without editing production code:

- Functional Reviewer
- Security Reviewer
- Database Reviewer
- Production Reviewer

Localized repairs requested during review were returned to the implementation role and reverified. They were limited to the FastAPI adapter split, authenticated metrics coverage, transaction-scope validation, timezone validation, hermetic PostgreSQL fixtures, pseudonymous-data classification and test-command secret suppression.

## Functional Reviewer

Decision: **PASS FOR REVIEW**.

Evidence:

- all 41 protected source routes have exactly one reviewed policy class and an explicit matching enforcement call;
- health and readiness remain exempt; authenticated metrics is limited after token verification;
- existing authorization, idempotency, version and domain service ordering remain intact;
- `429 RATE_LIMIT_EXCEEDED` and `503 RATE_LIMIT_UNAVAILABLE` use sanitized problem details;
- no frontend behavior or user-visible campaign workflow changed.

No blocking functional finding remains in the bounded increment.

## Security Reviewer

Decision: **PASS FOR INCREMENT; PRODUCTION BLOCKED**.

Verified:

- server-owned policy catalog with no client exemptions;
- exact authorization before tenant-scoped budget consumption;
- fixed opaque preauthorization namespace for `/me`, invitation acceptance and metrics;
- no raw issuer, subject, email, IP, bearer token, body, campaign content or voter information in keys, logs or metrics;
- fail-closed store and metadata behavior;
- stable low-cardinality labels only;
- no automatic membership, grant, account or political action effect;
- no new dependency or external processor.

Residual gates:

- invalid bearer attempts and volumetric attacks still require edge/WAF controls;
- no representative staging load or deployed alert routing exists;
- independent security/privacy/legal acceptance remains absent.

## Database Reviewer

Decision: **PASS FOR ADDITIVE MIGRATION**.

Verified:

- approved revision `20260729_0012` with no backfill and no mutation of existing domain tables;
- exact composite primary key and tenant/window cleanup index;
- policy-class, version, window and count constraints;
- forced RLS under a non-superuser `NOBYPASSRLS` role;
- atomic `INSERT ... ON CONFLICT DO UPDATE` using database transaction time;
- counter cap at `limit + 1`;
- tenant, principal, class, policy-version and window separation;
- concurrent burst threshold, rollover, transaction rollback and bounded `SKIP LOCKED` cleanup;
- application rollback can retain the additive table; destructive downgrade remains test/disposable only.

Residual gates:

- cleanup scheduler and approved retention period are not implemented;
- production contention and capacity require managed staging evidence.

## Production Reviewer

Final decision: **KEEP FEATURE IN REVIEW; DENY PRODUCTION RELEASE**.

| Gate | Decision | Evidence / residual risk |
|---|---|---|
| Security | Increment pass | Application-layer authenticated controls pass; edge abuse and independent review remain. |
| Data correctness | Pass | Atomic PostgreSQL, DB time, RLS, policy version, rollback and rollover pass. |
| Performance | Partial | Exact-key statements and a 20-request local burst complete within the 10-second test budget; no representative staging capacity proof. |
| Failure modes | Pass for increment | Store unavailable, metadata mismatch, invalid config, concurrency, rollover and rollback fail closed. |
| Observability readiness | Partial | Bounded metric/log hooks exist; no deployed collector, dashboard, alert receiver or SLO. |
| Testing | Pass for local review | Full local verification and 11 PostgreSQL slices pass; exact-head hosted CI remains required. |
| UX/accessibility | Not changed | Backend returns locale-neutral machine codes; a future UI feature must add localized retry guidance. |
| Operations | Partial | Runbook, rollout/remediation and bounded cleanup contract exist; scheduler and staging exercise remain absent. |

## Local verification evidence

- `make verify`: PASS
- Python: `749 passed`, `11 skipped`, `90.31%` coverage
- frontend: `119 passed`, lint/type/build/audit PASS, zero vulnerabilities
- isolated PostgreSQL: `11 passed`, including `test_rate_limit_postgres.py`
- Ruff, format and strict mypy over `73` source files: PASS
- Terraform: plan-only validation PASS
- security/privacy policy: `13` record types, `7` prohibitions, `6` append-only tables, production `BLOCKED`
- program and release validators: PASS with `DENY_RELEASE`

## Recommendation

Advance `C3-SEC-002` to Graph Harness `review`, publish a stacked draft PR, collect exact-head hosted CI and preserve production `BLOCKED`. Human closure/merge remains a separate gate.
