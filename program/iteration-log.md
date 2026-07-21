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

## C3 API campaign read boundary — 2026-07-20

- `branch`: `agent/c3-api-001-campaign-read-boundary`
- `base`: `agent/c3-iam-001-membership-authorization@5b203ec7d52c87950778b67b298de5d9b0a7a6fb`
- `production_status`: `BLOCKED`
- `external_effects`: local and review-branch code only; no campaign action, publication, deployment or data mutation.

### Implementation evidence

- Added `GET /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}` as the first protected campaign-domain projection.
- Requires fresh server-owned tenant authorization and an exact `read` grant over the requested campaign identifier, campaign scope and approved purpose before persistence is queried.
- Added a tenant-scoped SQLAlchemy campaign directory that returns only `DRAFT` or `ACTIVE` campaigns and fails closed for foreign-tenant or archived identifiers.
- Added sanitized 403, 404 and 503 behavior plus mismatched projection scope rejection.
- Added `GET /api/v1/tenants/{tenant_id}/campaigns` with UUID keyset pagination, a maximum page size of 100, no total-count leakage and a query restricted to exact authorized campaign identifiers.

### Verification evidence

- Ruff lint/format and strict mypy passed across the maintained backend.
- Focused API/read-model suite: `19 passed`.
- Workstation Python 3.14 full suite before pagination: `218 passed`, `1 skipped`, `18 subtests passed`; strict resource warnings exposed and corrected deterministic SQLite cleanup.
- Workstation Docker Compose E2E passed with PostgreSQL 18, Alembic upgrade/check, constrained API role, S3Mock and Mailpit after moving the internal daemon data root off the host-backed `fakeowner` mount.
- Program truth validator and campaign safety scanner passed; production remains `BLOCKED` with five critical/high findings and six retained failed runs.
- `C3-API-001` remains `IN_PROGRESS`: writes, concurrency contracts and the background worker runtime are not implemented.

## C3 API campaign write boundary — 2026-07-20

- `branch`: `agent/c3-api-001-campaign-read-boundary`
- `base_checkpoint`: `6155f77d5d1e9de7acc448c20c6f8385764df00e`
- `production_status`: `BLOCKED`
- `external_effects`: none; outbox rows remain local `PENDING` records and no worker delivery exists.

### Implementation evidence

- Added authenticated `PATCH /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}`.
- Requires an exact current `update` grant for the campaign and purpose `Maintain assigned campaign`.
- Requires `If-Match` with the current positive aggregate version and returns 412 for stale writes.
- Updates bounded campaign fields, increments version, appends a hash-linked audit event and creates a `PENDING` outbox event in one tenant-scoped transaction.
- Returns committed campaign, audit event and outbox event identifiers without delivering any external effect.

### Verification evidence

- Focused write/read/API suite: `30 passed`.
- Ruff and strict mypy passed before the full gate.
- `C3-API-001` remains `IN_PROGRESS`: idempotency keys, worker claiming/retry/dead-letter behavior and broader domain writes remain incomplete.


## C3 API durable idempotency boundary — 2026-07-21

- `branch`: `agent/c3-api-002-idempotency`
- `base`: `main@d0719c91dd6b0ac68e8499912c6c4eef983a0b1f`
- `production_status`: `BLOCKED`
- `external_effects`: none; replay returns stored internal evidence and outbox delivery remains disabled.

### Implementation evidence

- Added mandatory `Idempotency-Key` handling after exact authorization succeeds, preserving deny-first behavior.
- Added a tenant-scoped durable idempotency record with a unique operation/key boundary, request digest and committed response evidence.
- Replays with the same key and request return the original campaign/audit/outbox identifiers without a second mutation.
- Reuse of a key with a different request fails closed with structured HTTP 409 and no additional campaign, audit or outbox write.
- PostgreSQL equal-key requests are serialized with a transaction-scoped advisory lock; RLS is forced on the new table.

### Verification evidence

- Focused API, writer and database suite: `15 passed`, `1 skipped` before the full gate.
- Full locked verification: `233 passed`, `1 skipped`; Ruff, formatting, strict mypy, program truth and safety scan all passed.
- PostgreSQL Compose E2E: PASS with migration upgrade/check, forced RLS, constrained API role, S3Mock and Mailpit.
- Strict mypy: PASS across 23 backend source files.
- `C3-API-001` remains `IN_PROGRESS`: broader domain writes and a background worker runtime remain incomplete.

## C3-RESUME-001 review-stack reconciliation - 2026-07-21

- Confirmed `main@d0719c91dd6b0ac68e8499912c6c4eef983a0b1f` and merged PRs `#72`, `#73` and `#83`.
- Confirmed draft stack `#84` -> `#85` -> `#86` has correct bases and green recorded checks through CampaignOS CI run `29807878943`.
- Reproduced `make verify`: Ruff, format, strict mypy, `256 passed`, `1 skipped`, program truth and campaign safety PASS.
- Reproduced isolated PostgreSQL migration/RLS/authorization proof: `1 passed`, `5 deselected`.
- Reproduced Gitleaks `8.30.1` tracked-snapshot and active-stack scans: PASS.
- Independently reconciled the manifest against GitHub API branch, PR, workflow-run and job data: PASS.
- Reviewed pinned AutoSkills `0.3.6` package integrity and dry-run; eleven suggestions, zero installs, zero repository mutation, decision `NO_INSTALL`.
- Recorded a local-only Docker daemon blocker: image layers cannot be registered because the outer namespace denies `lchown /var/empty`; no local Compose PASS is claimed. Equivalent constrained-stack CI is green at the recorded review heads.
- Preserved five open CRITICAL/HIGH findings and six unsuperseded historical failed runs. Production remains `BLOCKED`.
- Selected `C3-API-005` campaign readiness as the next executable bounded slice.

## C3-API-005 audited campaign readiness - 2026-07-21

- Added exact-purpose `GET /api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/readiness` with authorization before persistence, typed OpenAPI, sanitized failures and adapter-scope verification.
- Added deterministic operational setup checks for campaign metadata and one active workspace; fixed limitation codes prohibit treating readiness as political, legal, financial, security, publication or production approval.
- Added mandatory successful-read audit evidence and verified zero readiness outbox events.
- Centralized campaign/workspace/readiness audit appends behind a tenant-row lock, session-bound token, monotonic timestamp and canonical hash chain after the critic identified a concurrent ordering risk.
- Restored the executable coverage gate: the previously inactive real value was `89.29%`; added fail-closed branch tests and reached `90.64%` under `fail_under=90`.
- Added the exact 33-item required-eval catalog and validator: `5 PASS`, `8 PARTIAL`, `20 NOT_RUN`; production remains `BLOCKED`.
- Full locked suite: `286 passed`, `1 skipped`; strict mypy across 31 source files, Ruff, program truth, eval catalog and campaign safety PASS.
- Isolated PostgreSQL migration/RLS/readiness/audit proof: `1 passed`, `5 deselected`.
- Implementation commit `22bc9a3f324a9a3cb1312fad7322596c7b719249` is published on `agent/c3-api-005-campaign-readiness`. Public API verification found zero open PRs and zero workflow runs for that head; no review, merge, deployment or external campaign effect is claimed.


## C3-API-006 idempotent tenant campaign creation - 2026-07-21

- Added exact-authorized `POST /api/v1/tenants/{tenant_id}/campaigns` with a required single `Idempotency-Key`, bounded normalized metadata, typed OpenAPI, `Location` and quoted `ETag`.
- Added server-owned `DRAFT`/version `1`, in-memory/unavailable/SQLAlchemy adapters and atomic campaign, audit, internal outbox and idempotency evidence.
- Bound tenant, normalized request, principal, grant, approval receipt and authorization purpose into replay identity; correlation remains immutable audit metadata.
- Centralized PostgreSQL equal-key serialization for campaign create/update and workspace create.
- The critic pass repaired duplicate validation handlers, missing/deprecated status constants, a misplaced test parametrizer, duplicate-header error taxonomy and missing purpose binding.
- Real PostgreSQL exposed and verified the required parent flush before the FK-bound audit append without weakening transaction atomicity.
- Full locked suite: `327 passed`, `2 skipped`; coverage `90.92%`; Ruff, format, strict mypy across 33 source files, program truth, eval catalog and campaign safety PASS.
- Isolated constrained-role PostgreSQL: `2 passed`, `5 deselected`, covering forced RLS, equal-key replay, same-slug race conflict and cross-tenant invisibility.
- Implementation commit `c91d60217e2ee0c0ec0f38c139852e7d73c78a58` is published on `agent/c3-api-006-campaign-create`; exact local/remote/GitHub branch SHAs match. Effective-worktree and `origin/main..HEAD` Gitleaks `8.30.1` scans PASS. Public GitHub inspection found zero open PRs and zero workflow runs for this head.
- Production remains `BLOCKED`; no external delivery, campaign publication, outreach, spending, mobilization or political approval occurred.

## C3-FRONT-001 dynamic application shell - 2026-07-21

- Created a separate Next.js `16.2.10` / React `19.2.7` / TypeScript application under `frontend/`; preserved `web/` unchanged as the static `DEMO_NON_PRODUCTION` reference.
- Added fail-closed live/demo configuration, server-only bearer handling, typed no-store API calls, exact runtime JSON parsers, tenant/campaign scope reconciliation and grant-derived navigation that never treats roles as permission.
- Added structurally tested Spanish/English dictionaries, locale routing, correct document language, loading/error/unauthenticated/context/empty/unavailable states and responsive Premium Slate foundations.
- Added a digest-pinned non-root standalone Dockerfile, exact npm lock, zero-vulnerability audit, npm/Docker Dependabot coverage, JavaScript/TypeScript CodeQL and a dedicated frontend CI/browser-review job.
- Critic pass repaired a PostCSS advisory, stale root-layout language during App Router navigation, missing standalone static assets in local E2E, stale-server port collisions and the absence of runtime response validation.
- Static gates: ESLint, strict TypeScript, 12 Vitest tests, production build and npm audit PASS.
- Browser gate: ES/EN desktop, ES mobile, keyboard skip link, reduced motion, no overflow, empty storage, no external hosts, no console/page errors and zero axe-core WCAG 2.2 A/AA violations PASS.
- Official Playwright Chromium and checksum-verified actionlint `1.7.12` were installed inside the workstation; all workflows pass actionlint.
- AutoSkills `0.3.6` dry-run proposed eleven skills, installed none and left Git status unchanged; decision remains `NO_INSTALL`.
- The nested Docker daemon remained namespace-blocked, so the frontend image was rebuilt with Buildah `1.28.2`, `vfs` storage and `chroot` isolation. Docker-format metadata preserved UID/GID `10001:10001`, command and health check; an in-image synthetic-shell smoke test passed. The daemon limitation now applies only to the complete Compose stack.
- A generated `.next` manifest triggered six local generic-key findings when scanning the raw directory. The release gate now snapshots tracked plus non-ignored files from Git before scanning; this excludes generated ignored output without a scanner allowlist. Effective-worktree and `origin/main..HEAD` Gitleaks scans pass.
- Independent BOLA review added a full-page tenant invariant: one valid selected campaign can no longer mask a foreign-tenant item returned in the same upstream list. The exact runtime parser and adversarial Vitest now fail closed.
- Final staged-set review found that empty `frontend/public/` would disappear in a clean checkout even though Docker/E2E copy it. Added a tracked placeholder and reran frontend build, browser, image and secret gates successfully.
- Production remains `BLOCKED`; no live identity, domain mutation UI, deployment or external effect occurred.

## C3-FRONT-001 publication checkpoint - 2026-07-21

- Published `agent/c3-front-001-dynamic-shell` at `b21f3d55ca0e89d3e6575076b5affa90732e3438` and verified exact local/origin/public GitHub SHA equality.
- Public inspection found zero open PRs and zero workflow runs for the head; `gh auth status` confirms no authenticated mutation session, so draft PR creation is classified as an external dependency.
- The first MCP push omitted the supported `branch` argument and followed stale workspace metadata into IAM. GitHub was reached; `e7304e61242280482f402bdfe047665d2c62fe4d` restores the exact `5b203ec7d52c87950778b67b298de5d9b0a7a6fb` tree by fast-forward, without force-push or history rewrite.
- C3-FRONT-001 is a `CHECKPOINT_COMPLETED` at `TESTED_LOCAL_PUBLISHED_UNREVIEWED`; production remains `BLOCKED` and execution continues.

## Review-stack restoration and frontend CI repair - 2026-07-21

- Created draft PR `#87` (`C3-API-005`), `#88` (`C3-API-006`) and `#89` (`C3-FRONT-001`) with exact stacked bases.
- PRs `#87` and `#88` passed all recorded checks.
- PR `#89` first failed CampaignOS CI run `29854467576` because the browser artifact path was relative to a later working directory.
- Commit `437b46930c68d6ed3a8233c139b0eaa03724b068` resolves relative paths against repository root. Exact-head CampaignOS CI `29856835515` and visual review `29856835522` pass.
- The isolated-workspace push wrapper emitted a nested-Docker error after GitHub accepted the push. Remote SHA verification, not the wrapper message, established the result. No force-push occurred.

## C3-IAM-002 identity lifecycle local/PostgreSQL verification - 2026-07-21

- Added revision `20260721_0004`, forced-RLS identity lifecycle tables and optimistic membership versions.
- Added exact-authorized invitation, session, membership-revocation and time-bound support APIs with provider-neutral no-effect contracts.
- Critic/fixer passes added verified-email acceptance, canonical scope-key constraints, explicit expiry evidence, unrelated-access preservation and adversarial rollback/error tests.
- Full gate: `381 passed`, `3 skipped`, coverage `91.34%`, Ruff, format, strict mypy, frontend regression and program/safety validators PASS.
- Disposable PostgreSQL gate passed twice: `3 passed`, `5 deselected` per run.
- `EVAL-SESSION-001` and `EVAL-INVITATION-001` advance only to `PARTIAL_TESTED_LOCAL`; no live provider claim is made.
- Production remains `BLOCKED`. The next delivery step is commit, rebase onto frontend `437b469`, push, draft PR and exact-head CI.

## C3-IAM-002 publication checkpoint - 2026-07-21

- Published implementation `5eb45e92f6f292ea673c572811031805cc89cabe`; exact remote SHA verified.
- Opened draft PR `#90` against the CI-green frontend head.
- CampaignOS CI `29857981975` and runtime visual review `29857981487` succeeded at the exact implementation head.
- Recorded `C3-IAM-002` as `CI_GREEN`; production remains `BLOCKED` and no external effect occurred.
