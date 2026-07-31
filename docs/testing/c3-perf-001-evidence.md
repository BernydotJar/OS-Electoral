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
