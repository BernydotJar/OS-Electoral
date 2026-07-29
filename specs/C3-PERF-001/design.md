# C3-PERF-001 Design

## Approach

Implement a repository-owned performance-verification boundary rather than a production benchmark service. A typed workload catalog defines a small set of authenticated scenarios. A bounded runner executes each scenario against a disposable CampaignOS API/PostgreSQL runtime, aggregates low-cardinality observations, evaluates deterministic regression thresholds and writes one versioned JSON receipt.

The runner is evidence tooling only. It must not provision infrastructure, modify production configuration, contact external political systems, publish content, spend funds or claim managed-environment capacity.

## Execution Order

1. verify the source revision and approved workload catalog;
2. create deterministic tenant, principal, membership, grant and domain fixtures;
3. start or connect only to an explicitly disposable local/CI runtime;
4. run one bounded scenario at a time with a hard timeout;
5. collect response, latency, rate-limit, database and pool evidence;
6. evaluate exact invariants before aggregate timing thresholds;
7. clean up fixtures and expired rate-limit buckets in bounded batches;
8. write a sanitized receipt even when a gate fails;
9. return a non-zero status on any invariant, threshold or cleanup failure.

## Workload Catalog

The initial catalog must include at least:

- `authenticated_read`: authorized tenant read with deterministic success totals;
- `authenticated_mutation`: authorized idempotent draft mutation using unique deterministic intent keys;
- `expensive_read`: bounded readiness/workspace projection without an external provider;
- `identity_lifecycle`: internal no-delivery lifecycle planning path;
- `governed_agent`: provider-stubbed or unavailable-provider path with no outbound generation;
- `malformed_authenticated`: invalid body/header traffic counted by the opaque preauthorization budget;
- `bola_denied`: authenticated cross-tenant/resource denial with no tenant-budget mutation;
- `rate_limit_contention`: concurrent fixed-window requests with exact allow/deny totals;
- `domain_rollback_accounting`: consumed attempt remains counted after later domain failure;
- `store_unavailable`: fail-closed sanitized response and bounded recovery;
- `cleanup`: expired bucket removal is tenant-scoped, bounded and leaves current windows intact.

## Threshold Model

Correctness invariants take precedence over timing. Any unexpected authorization success, cross-tenant disclosure, counter drift, unexpected `5xx`, sensitive receipt field, leaked connection or incomplete cleanup fails the run.

Timing thresholds are constrained-CI regression ceilings, not production SLOs. They must be:

- explicit in a versioned configuration contract;
- bounded by the envelope in `requirements.md`;
- evaluated from monotonic time;
- stable enough for repeated hosted CI;
- changed only with recorded evidence and reviewer approval;
- reported alongside the exact hardware/runtime context available to the process.

Throughput is recorded but is not, by itself, a release pass. Percentiles must be computed deterministically from the complete bounded sample using documented nearest-rank semantics.

## Evidence Contract

Proposed receipt: `artifacts/c3-perf-001/load-verification.json`.

Required top-level fields:

- `schema_version`
- `source_revision`
- `generated_at`
- `environment_classification` = `CONSTRAINED_NON_PRODUCTION`
- `python_version`
- `postgresql_version`
- `catalog_version`
- `runner_limits`
- `scenarios`
- `overall_decision`
- `production_capacity_claim` = `false`
- `external_effects` = `NONE`

Each scenario records only:

- stable scenario ID and policy class;
- configured request count, concurrency and timeout;
- completed/allowed/denied/expected-error/unexpected-error totals;
- minimum, median, p95, p99 and maximum latency in milliseconds;
- bounded rate-limit outcome counts;
- connection-pool gauges before, peak and after;
- invariant and threshold decisions;
- cleanup decision and duration.

The receipt must reject unknown fields and must not contain raw URLs, credentials, tokens, cookies, request/response bodies, UUIDs, emails, IP addresses, campaign text or political content.

## Files You May Read

- `AGENTS.md`
- `RTK.md`
- `specs/C3-PERF-001/**`
- `backend/src/campaignos/api/**`
- `backend/src/campaignos/security/**`
- `backend/src/campaignos/data/**`
- `backend/src/campaignos/identity/**`
- `backend/src/campaignos/observability.py`
- `backend/tests/**`
- `scripts/dev/**`
- `scripts/infra/**`
- `.github/workflows/**`
- `docs/testing/**`
- `docs/operations/**`
- `program/**`

## Files You May Touch

- `backend/src/campaignos/performance/**` for typed catalog, receipt and runner contracts;
- `backend/tests/test_performance_contracts.py`;
- `backend/tests/test_performance_runner.py`;
- `backend/tests/test_performance_postgres.py`;
- narrowly selected existing fixtures/helpers required for deterministic setup;
- `scripts/performance/run_authenticated_load.py`;
- `scripts/performance/verify_load_receipt.py`;
- `Makefile` and `.github/workflows/ci.yml` only for the bounded verification command and retained artifact;
- `docs/testing/c3-perf-001-evidence.md`;
- `docs/operations/load-verification.md`;
- `progress/review_C3-PERF-001.md`;
- `program/iterations/c3-perf-001.md`;
- `program/validations/c3-perf-001.json`;
- canonical graph, ledger, risk, decision, eval and evidence records for this increment.

## Files You Must Not Touch

- Graph Harness framework concepts or source files;
- campaign strategy, persuasion, targeting, citizen-contact, publication, spending or mobilization modules;
- Terraform state/apply paths or live cloud resources;
- production limits, pool sizing or environment secrets;
- dependency manifests or lockfiles unless a separate human approval expands the spec;
- historical evidence except append-only reconciliation notes;
- any external campaign, social, identity-provider or AI-provider account.

## Dependencies

No new runtime or paid dependency is planned. Reuse the pinned Python standard library, existing HTTP/FastAPI test tooling, SQLAlchemy/psycopg, PostgreSQL 18 service, metrics registry and current CI artifact facilities.

Implementation is not authorized until the human approval gate accepts this specification.

## Primary-Documentation Checkpoints

Before implementation, confirm current primary documentation for the pinned versions of:

- Python `concurrent.futures`, monotonic timing and percentile implementation assumptions;
- FastAPI dependency ordering and request validation;
- SQLAlchemy connection-pool inspection and transaction behavior;
- PostgreSQL 18 lock, transaction, `pg_stat_activity` and timeout semantics used by the harness;
- GitHub Actions artifact retention and job-service behavior.

## Risks and Localized Repairs

- Flaky timing: keep timing thresholds broad, bounded and subordinate to exact correctness invariants.
- Self-induced denial: use disposable fixtures and hard request/concurrency ceilings.
- False production claim: label all evidence non-production and preserve the managed-staging gate.
- Sensitive evidence: validate a strict receipt schema and scan output before retention.
- Fixture leakage: use unique run scope plus mandatory cleanup and verify pool/session recovery.
- Authorization oracle: use opaque preauthorization evidence and never label tenant/resource identity.
- Database contention: observe and bound exact statements; do not globally tune production settings.
- Harness defect: repair only the affected scenario, runner, threshold or product subgraph and rerun equal-or-broader evidence.

## Verification Plan

- Graph Harness state validation and one-feature invariant;
- Ruff, formatting and strict mypy;
- typed catalog and receipt-schema unit tests;
- bounded runner success/failure/timeout tests;
- API tests for malformed authentication, exact authorization and sanitized results;
- isolated PostgreSQL 18 contention, rollback-accounting, RLS, pool-recovery and cleanup tests;
- complete locked Python suite with coverage floor;
- unchanged frontend verification unless user-facing behavior changes;
- program, release, security and supply-chain validators;
- effective-worktree and submitted-diff secret scans;
- exact-head hosted CI with retained sanitized receipt;
- independent critic/red-team and verifier evidence;
- release gate preserving `BLOCKED` production state.
