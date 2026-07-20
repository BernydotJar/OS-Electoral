# Program iteration log

## C3 IAM membership-authorization increment — 2026-07-19

- `branch`: `agent/c3-iam-001-membership-authorization`
- `base`: `agent/c3-found-001-production-foundation@bac781eea1d0de1b9a845f0f4243924ee4808c54`
- `version`: `0.2.0`
- `production_status`: `BLOCKED`
- `external_effects`: local implementation checkpoint only; review-branch publication is pending. No merge, production/AWS deployment, campaign action, data deletion or Pages publish occurred.

### Implementation evidence

- Added a server-owned membership directory that maps a cryptographically verified issuer/subject to an enabled internal principal inside an explicitly tenant-scoped transaction.
- Loads only active tenant/campaign membership, unexpired roles and active grants whose campaign/workspace remains usable; inactive, missing, expired, revoked and inconsistent scope fails closed.
- Exact permission checks require action, resource type, resource identifier, campaign/workspace scope and purpose. Role labels never imply authority.
- Added `/api/v1/tenants/{tenant_id}/me` while retaining `/api/v1/me` as identity-only. Authorization denial and dependency/data failures return sanitized RFC 9457-style `403`/`503` problems.
- Added API, SQLite authorization and PostgreSQL/RLS integration coverage, including no-membership denial, cross-campaign corruption, wrong directory scope, inactive scope and unavailable persistence.

### Local verification evidence

- `make verify`: `214 passed`, `1 skipped`; Ruff lint/format, strict mypy, program truth and campaign-safety scan passed. The skip remains the explicitly isolated PostgreSQL marker.
- coverage: `93.91%`, above the configured `90%` threshold.
- focused authorization/API/database suite after exact-purpose hardening: `32 passed`, `1 skipped`.
- isolated PostgreSQL 18.3 migration/RLS/authorization run: `1 passed`, `5 deselected`; the disposable container was removed after the test.
- disposable Compose E2E rebuilt the API and passed migration check, constrained application-role proof, PostgreSQL/S3Mock/Mailpit reachability and fail-closed OIDC readiness; cleanup succeeded.
- Gitleaks `8.30.0` worktree scan: no leaks found.
- Production gates remain unchanged: membership administration, live identity/session lifecycle, domain and worker enforcement, staging evidence and all previously recorded blockers remain open.

## C3 production-foundation increment — 2026-07-19

- `branch`: `agent/c3-found-001-production-foundation`
- `base`: `main@8f32bc158003a55a76cb471af45da2193ca71003`
- `production_status`: `BLOCKED`
- `external_effects`: pushed the review branch and opened draft PR `#72`; no merge, production/AWS deployment, campaign action, data deletion or Pages publish occurred. Other network effects were official metadata/package/image retrieval and read-only GitHub inspection. Isolated Docker test containers/volumes were removed automatically.

### Program and architecture

- `C3-FOUND-001A`: `COMPLETE_LOCAL` — fail-closed program manifest, graph, ledger, evidence registers, guarded demo delivery and truthful production gates.
- `C3-ARCH-001`: `COMPLETE_LOCAL` — product/non-goal boundaries, modular-monolith context/data/deployment documents and ADRs 001–005.
- `C3-DEVEX-001`: `COMPLETE_LOCAL` — exact dependency lock, Make entry points, non-root pinned API image and hermetic PostgreSQL/S3Mock/Mailpit stack.
- `C3-CI-001`: `IN_PROGRESS` — draft PR `#72` has green quality, CodeQL, dependency/secret, PostgreSQL/RLS, disposable-stack E2E and visual evidence at its recorded head; human review, merge and protected-main enforcement are pending.
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
- Added `.gitleaks.toml` while inheriting all default rules; its only exceptions require the `generic-api-key` rule, one exact known synthetic token and its exact original path simultaneously.
- Hardened approval authentication/digest binding, operation-specific persistence permissions, repository atomicity/copy isolation, evidence-review receipts, claim canonicalization and contradiction eligibility.
- Fixed the Governance Workspace status race exposed by PR browser CI and added a static regression assertion for the Coordinate 04 mapping.
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
- draft PR `#72`, head `e8adf4ce008bbf4b82fe9d7e6515ee4b37595922`: CampaignOS CI run `29706162737` and runtime visual run `29706162740` completed `SUCCESS`; all seven named PR checks were green.

### Findings and decisions

- Fixed the critic-identified trust-boundary defects in approval, repository, persistence, evidence and OIDC code and added regression coverage.
- Fixed a container packaging failure discovered by E2E: copied virtualenv console scripts had `/build/.venv` shebangs. The builder now creates the environment at its final `/app/.venv` path.
- Removed database-owner privileges from the running API after the E2E critic pass exposed that Compose had reused the migration identity. PostgreSQL bootstrap now creates a constrained application role, migrations run separately as the bootstrap administrator, and E2E asserts the effective role attributes.
- The first PR secret scan correctly rejected two `generic-api-key` false positives from earlier branch history. Final fixture/prose text was made unambiguous, and narrow rule+token+path `AND` exceptions preserve full-range scanning; both local history/worktree scans and GitHub Gitleaks now pass.
- The first PR visual run exposed a MutationObserver race that reset Governance Workspace status to Coordinate 01. The canonical premium status map now includes governance, the desktop/mobile/reduced-motion review passes, and the rerun is green.
- Kept `FND-PLATFORM-001` critical because local runtime evidence does not replace Terraform/AWS/staging/production, backup/restore or approval evidence.
- Kept historical GitHub failures unchanged; later local or integrated successes do not rewrite their recorded conclusions.
- Marked audit-wording and missing-program-record findings resolved; retained CI, delivery and supply-chain findings because green draft-PR execution is not human review, protected-main enforcement, SBOM/provenance/signing or production evidence.

### Next critical work

1. Obtain review of draft PR `#72`, reconcile historical failures and establish protected-main requirements using the green check names.
2. Integrate live identity plus server-owned membership/grant loading.
3. Connect durable domain repositories/API/outbox-worker behavior.
4. Build reviewed AWS development infrastructure before any staging or production action.
