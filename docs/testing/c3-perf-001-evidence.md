# C3-PERF-001 evidence — authenticated load and contention verification

## Scope

Bounded SHIP verification for authenticated API behavior, authorization denial, PostgreSQL fixed-window contention, domain rollback accounting, fail-closed dependency behavior, connection-pool recovery and tenant-scoped cleanup.

This increment introduces no runtime endpoint, production configuration, dependency, cloud resource or external political effect.

## Implemented contracts

- versioned eleven-scenario workload catalog;
- strict Pydantic receipt schema with unknown-field rejection;
- recursive sensitive-key and sensitive-value scan before persistence;
- deterministic nearest-rank p50/p95/p99 calculation;
- hard per-scenario concurrency, request and timeout ceilings;
- one FastAPI client per operation without concurrent shared lifespan management;
- exact 5/15 allowed/denied contention contract;
- temporary PostgreSQL role with forced-RLS-compatible privileges and bounded lock/statement timeouts;
- atomic receipt write and independent re-read verification;
- `always()` artifact upload in the existing PostgreSQL required check.

## Local evidence

```text
focused contract/runner/HTTP tests: 22 passed
complete Python suite: 778 passed, 12 controlled skips
coverage: 90.52% before final red-team hardening; final full gate recorded below
Ruff: PASS
mypy: PASS
CI policy validator: PASS
failure-receipt path: PASS (runner=1, verifier=1, sanitized receipt retained)
program/security/release/eval/safety validators: PASS
```

The local Docker daemon cannot register the pinned PostgreSQL 18.3 image layer because the sandbox rejects `lchown /var/empty`. The failure occurs before PostgreSQL or CampaignOS starts. PostgreSQL 15 was explicitly not accepted as substitute evidence. Exact-head hosted CI must execute the authoritative PostgreSQL 18.3 harness before merge.

## Correctness boundaries

- expected governed-agent and unavailable-store `503` responses are recorded as expected fail-closed behavior;
- any other 5xx, transport exception, timeout, authorization drift, exact-count drift, cleanup residue or checked-out pool increase fails the scenario;
- the harness never calls a model provider and never stores request/response bodies;
- thresholds are regression sanity ceilings, not production SLOs;
- production remains `BLOCKED`, release remains `DENY_RELEASE`, external effects remain `NONE`.

## Hosted gates pending

- PostgreSQL 18.3 exact-head scenario execution;
- exact-head quality, security, supply-chain and functional checks;
- exact-head review-thread closure;
- merge and post-merge main CI.

## Exact-head PostgreSQL 18.3 evidence

Implementation head `65b962d71e4b71a7e88bf9cec4ee1e7e5ed2dcee` passed CampaignOS CI run `30669150640` and runtime visual run `30669150651`.

Sanitized artifact `campaignos-authenticated-load-verification` (`8808117715`) was independently downloaded and re-validated:

```text
PostgreSQL: 18.3
scenarios: 11 / 11 PASS
contention: 5 allowed / 15 denied
peak checked-out connections: 18
checked-out connections after every scenario: 0
unexpected errors: 0
scenario timeouts: 0
sensitive key/value scan: PASS
production_capacity_claim: false
external_effects: NONE
```

## Review repair — process isolation and receipt consistency

Three review findings superseded the first successful exact-head run:

1. malformed and BOLA scenarios now record sanitized rate-limit scope/policy calls and require exactly one opaque preauthorization consumption per request with no tenant budget consumed before authorization;
2. the authoritative CLI now runs every scenario in a separate spawn process, terminates it at the scenario deadline, and idempotently revokes its deterministic temporary PostgreSQL role after normal or abnormal exit;
3. scenario receipts now cross-check operation totals, status classes, rate-limit outcomes, latency ordering, child decisions and pool recovery; the independent verifier also requires complete catalog coverage and exact immutable configuration before accepting PASS.

Repaired local evidence at code commit `b74272d`:

```text
focused performance tests: 33 passed / 1 PostgreSQL integration skip
complete Python suite: 790 passed / 12 controlled skips
coverage: 90.22%
Ruff: PASS
mypy: PASS
failure receipt retained and independently rejected as PASS: PASS
hard-timeout supervisor termination test: PASS
exact preauthorization ordering tests: PASS
truncated/failed-child PASS rejection tests: PASS
```

The earlier successful exact-head runs and artifact remain historical evidence for the pre-repair implementation only. PostgreSQL 18.3 must pass again on the repaired head before merge.

## Final repaired local gate

```text
make verify: PASS
Python: 790 passed / 12 controlled skips / 90.22% coverage
Frontend: 29 files / 122 tests PASS
Ruff / format / mypy: PASS
Next.js production build / npm audit: PASS
Terraform: PASS_PLAN_ONLY_NO_APPLY
Program / security / release / eval / safety: PASS with production BLOCKED
```
