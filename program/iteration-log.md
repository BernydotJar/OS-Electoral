# Program iteration log

## C3 production-foundation increment — 2026-07-19

- `branch`: `agent/c3-found-001-production-foundation`
- `base`: `main@8f32bc158003a55a76cb471af45da2193ca71003`
- `production_status`: `BLOCKED`
- `external_effects`: no production/AWS deployment, no campaign action, no data deletion, and no Pages publish. Network effects were limited to official metadata/package/image retrieval and read-only GitHub inspection. Isolated Docker test containers/volumes were removed automatically.

### Program and architecture

- `C3-FOUND-001A`: `COMPLETE_LOCAL` — fail-closed program manifest, graph, ledger, evidence registers, guarded demo delivery and truthful production gates.
- `C3-ARCH-001`: `COMPLETE_LOCAL` — product/non-goal boundaries, modular-monolith context/data/deployment documents and ADRs 001–005.
- `C3-DEVEX-001`: `COMPLETE_LOCAL` — exact dependency lock, Make entry points, non-root pinned API image and hermetic PostgreSQL/S3Mock/Mailpit stack.
- `C3-CI-001`: `IN_PROGRESS` — pinned workflow, actionlint, CodeQL, dependency/secret scans, PostgreSQL/RLS job, disposable-stack E2E and Dependabot definitions exist; GitHub execution and branch protection are pending.
- `C3-IAM-001`: `IN_PROGRESS` — fail-closed OIDC ID-token verification and identity endpoint exist; live IdP/session/membership-backed grants are pending.
- `C3-DATA-001`: `COMPLETE_LOCAL` — initial PostgreSQL/Alembic schema, transaction scope and forced RLS passed local integration proof.
- `C3-API-001`: `IN_PROGRESS` — versioned health/readiness/identity baseline exists; domain endpoints and worker runtime are pending.

### Implementation evidence

- Added `backend/src/campaignos/` application, identity, API and data packages; Alembic environment/revision; backend unit/integration tests.
- Added exact runtime/development pins in `pyproject.toml` and the hash-bearing `uv.lock` (`81` resolved packages).
- Added `.python-version`, `.env.example`, `.dockerignore`, `backend/Dockerfile`, `compose.yaml`, `Makefile` and `scripts/dev/e2e.sh`.
- Replaced the vulnerable older local MinIO image choice with current Adobe S3Mock `5.1.0`, initialized a deterministic local bucket, bound ports to loopback and documented that it is never a production storage service.
- Pinned Python, uv, PostgreSQL, S3Mock and Mailpit images by digest; pinned every third-party workflow Action by full commit SHA.
- Added `.github/workflows/campaignos-ci.yml` and `.github/dependabot.yml`; hardened the existing visual and Pages workflows.
- Hardened approval authentication/digest binding, operation-specific persistence permissions, repository atomicity/copy isolation, evidence-review receipts, claim canonicalization and contradiction eligibility.
- Preserved user-owned `RTK.md` and `artifacts/c1-front-003/` without modification or staging.

### Verification evidence

- `pytest -W error`: `193 passed`, `1 skipped` in the full unit/contract suite. The skip is the isolated PostgreSQL marker.
- isolated PostgreSQL/RLS run: `1 passed`, `5 deselected`; Alembic downgrade/upgrade/check and cross-tenant denial succeeded under a non-superuser, non-`BYPASSRLS` role.
- Docker Compose E2E: API image build, health, migration upgrade/check, constrained `campaignos_app` role proof (`NOSUPERUSER`, `NOBYPASSRLS`), PostgreSQL query, initialized S3Mock bucket, fail-closed OIDC readiness and Mailpit delivery all succeeded; cleanup succeeded.
- focused adversarial security regression set: `97 passed`, `18 subtests passed`.
- Ruff lint: pass. Ruff format check: `23 files already formatted`. Strict mypy: success in `17 source files`.
- actionlint `1.7.12`: pass for all workflows. JSON/YAML parsing, shell syntax and Compose interpolation: pass.
- hash-locked production dependency audit: `No known vulnerabilities found` at check time.
- program validator: `[OK]`, production remains `BLOCKED`, `5` open critical/high findings and `6` blocking historical failed runs.

### Findings and decisions

- Fixed the critic-identified trust-boundary defects in approval, repository, persistence, evidence and OIDC code and added regression coverage.
- Fixed a container packaging failure discovered by E2E: copied virtualenv console scripts had `/build/.venv` shebangs. The builder now creates the environment at its final `/app/.venv` path.
- Removed database-owner privileges from the running API after the E2E critic pass exposed that Compose had reused the migration identity. PostgreSQL bootstrap now creates a constrained application role, migrations run separately as the bootstrap administrator, and E2E asserts the effective role attributes.
- Kept `FND-PLATFORM-001` critical because local runtime evidence does not replace Terraform/AWS/staging/production, backup/restore or approval evidence.
- Kept historical GitHub failures unchanged; later local or integrated successes do not rewrite their recorded conclusions.
- Marked audit-wording and missing-program-record findings resolved; retained CI, delivery and supply-chain findings until GitHub/external enforcement is observed.

### Next critical work

1. Create a reviewable PR, obtain green GitHub evidence for every CI job and establish protected-main requirements.
2. Integrate live identity plus server-owned membership/grant loading.
3. Connect durable domain repositories/API/outbox-worker behavior.
4. Build reviewed AWS development infrastructure before any staging or production action.
