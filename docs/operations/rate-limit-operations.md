# CampaignOS rate-limit operations

Status: **pre-production implementation evidence only**. This runbook does not authorize deployment or production release.

## Configuration ownership

Security and Platform Operations own the policy version, request budgets, windows and cleanup schedule. Configuration keys use the `CAMPAIGNOS_` prefix:

- `CAMPAIGNOS_RATE_LIMITS_ENABLED`
- `CAMPAIGNOS_RATE_LIMIT_POLICY_VERSION`
- `CAMPAIGNOS_RATE_LIMIT_READ_REQUESTS`, `CAMPAIGNOS_RATE_LIMIT_READ_WINDOW_SECONDS`
- `CAMPAIGNOS_RATE_LIMIT_MUTATION_REQUESTS`, `CAMPAIGNOS_RATE_LIMIT_MUTATION_WINDOW_SECONDS`
- `CAMPAIGNOS_RATE_LIMIT_EXPENSIVE_READ_REQUESTS`, `CAMPAIGNOS_RATE_LIMIT_EXPENSIVE_READ_WINDOW_SECONDS`
- `CAMPAIGNOS_RATE_LIMIT_IDENTITY_REQUESTS`, `CAMPAIGNOS_RATE_LIMIT_IDENTITY_WINDOW_SECONDS`
- `CAMPAIGNOS_RATE_LIMIT_AGENT_REQUESTS`, `CAMPAIGNOS_RATE_LIMIT_AGENT_WINDOW_SECONDS`
- `CAMPAIGNOS_RATE_LIMIT_CLEANUP_BATCH_SIZE`

Staging and production refuse to start with rate limiting disabled. A policy change must increment `CAMPAIGNOS_RATE_LIMIT_POLICY_VERSION` so old and new windows cannot share one key.

## Rollout

1. Back up and verify the target non-production database under the existing recovery procedure.
2. Apply Alembic revision `20260729_0012` through the normal migration role.
3. Confirm `rate_limit_buckets` has forced RLS and `tenant_isolation` policy.
4. Configure reviewed budgets and `RATE_LIMITS_ENABLED=true`.
5. Start one API instance and verify health, readiness, authorized reads/mutations, `429`, `Retry-After`, metrics and sanitized logs.
6. Increase staging concurrency gradually while monitoring database latency, locks, pool saturation and denial ratio.
7. Retain exact config version, migration, load profile, CI SHA and human acceptance receipts.

Local/CI concurrency is not production capacity evidence. Promotion remains blocked until representative staging load and failure exercises pass.

## Metrics and logs

Prometheus exposes:

```text
campaignos_rate_limit_decisions_total{policy_class="...",outcome="..."}
```

Allowed outcomes are `allowed`, `denied`, `unavailable` and `configuration_error`. Alert routing is not deployed in this increment. A staging owner must define thresholds from observed baselines rather than using repository defaults as production SLOs.

Structured event `rate_limit_decision` contains correlation ID, policy class and outcome only. Never add tenant, principal, IP, email, token, request body, raw count or campaign content.

## Cleanup and retention

Expired rows are deleted outside the request path in tenant-scoped batches of 1–1,000 using `FOR UPDATE SKIP LOCKED`. The repository default batch size is 500. A future scheduler must:

- enumerate tenants through an authorized operational control plane;
- call bounded cleanup separately for each tenant;
- record aggregate rows deleted and duration without bucket identifiers;
- retry with bounded backoff;
- avoid full-table request-path deletes;
- preserve no bucket longer than the independently approved security retention period.

The scheduler itself is not implemented here. Until staging defines and tests it, retention remains a production gate.

## Failure response

### Elevated denials

1. Check policy class and aggregate outcome metrics.
2. Confirm the policy version and budget were not changed unexpectedly.
3. Distinguish legitimate burst, application retry loop and hostile traffic without inspecting political content.
4. Do not disable enforcement or mutate grants as an automatic response.
5. Escalate volumetric abuse to the separate edge/WAF owner.

### Store unavailable

1. Confirm PostgreSQL readiness, pool state and migration head.
2. Expect protected routes to return `503 RATE_LIMIT_UNAVAILABLE`.
3. Do not activate a permissive fallback.
4. Restore database service or roll back the application through an approved release procedure.

## Rollback and remediation

Application rollback may return to the previous artifact only while retaining migration `20260729_0012`; the added table is backward-compatible and unused by the prior application. Disabling rate limiting is permitted only in isolated development/test environments.

Dropping the table requires a separately approved destructive migration after traffic has stopped and evidence retention is resolved. The Alembic downgrade exists for disposable/test verification and is not blanket production authorization.

## Remaining gates

Before production:

- representative multi-instance staging load and contention thresholds;
- cleanup scheduler and retention acceptance;
- deployed dashboards, alert routing and on-call ownership;
- edge DDoS/WAF controls;
- independent security, privacy, database and operational approval;
- explicit scoped production approval.
