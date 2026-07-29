# C3-SEC-002 Design

## Approach

Implement a server-owned rate-limit policy catalog and a PostgreSQL-backed fixed-window counter service. The service uses database time and one atomic `INSERT ... ON CONFLICT ... DO UPDATE ... WHERE` statement per checked policy to remain consistent across API processes.

The application derives a canonical key from authenticated principal ID, tenant ID, policy class, policy version, and window start. Raw tokens, email addresses, IP addresses, request bodies, campaign text, and voter-level data are excluded from the key and from logs.

Authorization ordering is route-sensitive:

1. authenticate principal;
2. resolve server-owned tenant/resource scope;
3. authorize exact purpose where the route already requires it;
4. consume the scoped policy budget;
5. execute the domain operation.

Every protected authenticated route runs an opaque principal-level pre-authorization budget after token verification and before FastAPI request-model binding. That budget uses the internal preauthorization namespace and cannot reveal tenant or resource existence. Tenant-scoped consumption remains after exact grant authorization inside the endpoint.

## Files You May Read

- `AGENTS.md`
- `RTK.md`
- `specs/C3-SEC-002/**`
- `backend/src/campaignos/api/**`
- `backend/src/campaignos/identity/**`
- `backend/src/campaignos/data/**`
- `backend/src/campaignos/agents/**`
- `backend/migrations/versions/**`
- `backend/tests/**`
- `frontend/src/lib/api-client.ts`
- `frontend/src/lib/i18n.ts`
- `docs/security/**`
- `docs/api/**`
- `docs/operations/**`
- `program/**`

## Files You May Touch

- `backend/migrations/versions/<next>_rate_limit_buckets.py`
- `backend/src/campaignos/security/rate_limits.py`
- `backend/src/campaignos/security/rate_limit_contracts.py`
- `backend/src/campaignos/api/dependencies.py`
- `backend/src/campaignos/api/errors.py`
- `backend/src/campaignos/config.py`
- narrowly selected protected route modules required to bind policy classes
- `backend/tests/test_rate_limit_contracts.py`
- `backend/tests/test_rate_limits.py`
- `backend/tests/test_rate_limit_api.py`
- `backend/tests/test_rate_limit_postgres.py`
- existing API/PostgreSQL regression tests when assertions must be extended
- `frontend/src/lib/i18n.ts` and its tests only if throttling is surfaced to users
- `docs/security/rate-limiting.md`
- `docs/api/errors.md`
- `docs/operations/rate-limit-operations.md`
- `docs/testing/c3-sec-002-evidence.md`
- `program/iterations/c3-sec-002.md`
- `program/validations/c3-sec-002.json`
- canonical program graph, ledger, risk, decision, and evidence records for this increment

## Files You Must Not Touch

- framework repository concepts or source files
- campaign strategy, persuasion, targeting, citizen-contact, publishing, spending, or mobilization modules
- Terraform apply/state files or live cloud resources
- unrelated migrations
- lockfiles or dependency manifests unless a separate human approval explicitly expands the spec
- secrets, environment credentials, or local review deployment data
- existing historical evidence except append-only reconciliation notes

## Data Contracts

Proposed table: `rate_limit_buckets`.

Required fields:

- `tenant_id UUID NOT NULL`
- `principal_id UUID NOT NULL`
- `policy_class TEXT NOT NULL`
- `policy_version INTEGER NOT NULL`
- `window_start TIMESTAMPTZ NOT NULL`
- `window_seconds INTEGER NOT NULL`
- `request_count INTEGER NOT NULL`
- `updated_at TIMESTAMPTZ NOT NULL`

Canonical key:

`(tenant_id, principal_id, policy_class, policy_version, window_start)`

Rules:

- database time determines `window_start`;
- increments are atomic;
- a rejected increment does not modify domain state;
- each consumed budget is committed through an independent rate-limit transaction before domain execution;
- later domain validation, conflict, exception, or rollback does not refund the consumed attempt;
- RLS binds every row to the transaction-local tenant context;
- callers cannot read arbitrary bucket rows through public API routes;
- cleanup is bounded and operational, not request-path full-table deletion;
- policy definitions are versioned configuration, not caller input.

Response contract:

- HTTP `429`
- machine code `RATE_LIMIT_EXCEEDED`
- sanitized detail
- `Retry-After` seconds
- correlation/request ID
- no limit key, principal ID, tenant ID, raw counters, or sensitive payload

## Dependencies

No new runtime package is planned. Use existing SQLAlchemy, psycopg, FastAPI, configuration, error, metrics, and test tooling.

The proposed migration and schema are not authorized until the human approval gate accepts this spec.

## Context7 Checkpoints

Before implementation, confirm current primary documentation for:

- FastAPI dependency and exception-response behavior used by the pinned version;
- PostgreSQL 18 `INSERT ... ON CONFLICT`, transaction isolation, database time, and RLS semantics;
- RFC 9457 problem details and HTTP `Retry-After` semantics;
- the pinned SQLAlchemy/psycopg transaction APIs used in this repository.

No current-documentation checkpoint is needed for program-ledger bookkeeping.

## Risks

- Database contention: mitigate with bounded policy classes, indexed exact keys, fixed windows, and measured concurrency tests.
- Counter persistence boundary: commit consumption before domain execution and prove that later domain rollback does not make abusive failing requests free.
- Authorization oracle: pre-authorization limits use only an opaque principal identity and never reveal resource existence or tenant membership; tenant counters remain exact-grant gated.
- Shared-principal abuse: keys include tenant and policy class; support/service identities require explicit reviewed policies.
- Clock drift: use database time only.
- Unbounded retention: define bounded cleanup and operational ownership.
- False production claim: local and CI evidence cannot replace staging load/WAF evidence.

## Verification Plan

- `uv run --locked ruff check backend`
- `uv run --locked ruff format --check backend`
- `uv run --locked mypy`
- focused rate-limit contract/model/API tests
- isolated PostgreSQL migration, RLS, concurrency, rollback, cross-tenant, and cleanup tests
- complete locked Python suite with coverage floor
- frontend lint/type/test/build/audit only if user-facing throttling copy changes
- `make program-verify`
- effective worktree and committed-range secret scans
- hosted exact-head CI, including PostgreSQL, recovery, CodeQL, dependency, supply-chain, and constrained-stack jobs
- independent implementer/reviewer separation and SHIP production review artifact
