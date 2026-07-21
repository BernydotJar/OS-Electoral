# CampaignOS current-state assessment

Assessment date: `2026-07-21 America/Guatemala`

Authoritative target: CampaignOS production-readiness program for `BernydotJar/OS-Electoral`.

Repository evidence point: `main` at `d0719c91dd6b0ac68e8499912c6c4eef983a0b1f`; green review stack through `agent/c3-api-004-workspace-write@236a0d04c5b2c061948261a5c60852e0d4736b0f`; published readiness and campaign-create checkpoints through `agent/c3-api-006-campaign-create@a21e7353f0a91f8c50a10904d942e03db45b8318`; local dynamic-shell worktree on `agent/c3-front-001-dynamic-shell`.

## Executive determination

Production readiness is **BLOCKED**.

Foundation PR `#72`, IAM PR `#73`, and the first protected campaign API PR `#83` are merged to `main`. Draft PRs `#84`, `#85`, and `#86` form a correctly based review stack and have green checks at their recorded heads. Published stacked checkpoints add audited readiness and exact-authorized idempotent campaign creation. The current local branch adds a server-rendered bilingual Next.js shell, server-only typed API boundary, runtime contract validation, synthetic read-only demo classification, accessibility evidence, and a dedicated frontend CI job. It has no current-branch PR, CI, review, merge, or deployment evidence. None of these proofs constitutes production readiness or approval.

The only public deployed surface remains the static, read-only GitHub Pages demonstration. It is classified `DEMO_NON_PRODUCTION`, publishes only through a manual confirmation workflow, and never counts as a production environment.

## Reconciled repository and delivery state

- PR `#72` (`bac781e`) merged on `2026-07-21`; its final-head CampaignOS CI run `29706314953` and visual run `29706314936` succeeded.
- PR `#73` (`5b203ec`) merged on `2026-07-21`; CampaignOS CI run `29770562360` and visual run `29770562352` succeeded.
- PR `#83` (`ed41ae0`) merged as `main@d0719c9`; CampaignOS CI run `29802998261` succeeded.
- PR `#84` (`e938930`) is draft against `main`; CampaignOS CI run `29804446308` succeeded.
- PR `#85` (`0f38361`) is draft against `agent/c3-api-002-idempotency`; CampaignOS CI run `29807485042` and visual run `29807485041` succeeded.
- PR `#86` (`236a0d0`) is draft against `agent/c3-api-003-outbox-worker`; CampaignOS CI run `29807878943` succeeded.
- The public rulesets endpoint returned an empty list. Branch-protection and Actions-permission endpoints require authentication, so required-check enforcement is not currently verifiable and remains a production blocker.
- Twenty-three non-PR issues remain open. The C2 issues associated with already merged PRs have not been rewritten or closed by this checkpoint.

## Verification reproduced at the current dynamic-frontend worktree

- `make verify`: PASS.
- Ruff lint and format: PASS.
- Strict mypy across 33 source files: PASS.
- Full locked suite: `327 passed`, `2 skipped` on the uv-managed Python `3.14.6` environment.
- Enforced coverage gate: `90.92%` with `fail_under=90`.
- Program-truth validator: PASS with `production=BLOCKED`, five open CRITICAL/HIGH findings, and six retained failed runs.
- Required-eval catalog validator: PASS with all 33 required IDs inventoried as `5 PASS`, `10 PARTIAL`, and `18 NOT_RUN`.
- Campaign safety scan: PASS.
- Dynamic frontend: exact npm install, ESLint, strict TypeScript, 12 Vitest contract tests, Next production build, and npm audit with zero vulnerabilities all PASS.
- Production-shell browser review: Spanish/English desktop, Spanish mobile, full-document locale change, keyboard skip link, reduced motion, zero horizontal overflow, empty browser storage, no external hosts, no console/page errors, and zero axe-core WCAG 2.2 A/AA violations all PASS.
- `actionlint 1.7.12`: official ARM64 binary installed after SHA-256 verification; all workflows PASS.
- Daemonless frontend image verification: Buildah `1.28.2` with `vfs` storage and `chroot` isolation built the digest-pinned Docker-format image, preserved the health check, verified runtime user `10001:10001`, and served the synthetic Spanish shell in an in-image smoke test.
- Isolated PostgreSQL integration: `2 passed`, `5 deselected` against temporary PostgreSQL `15.18`, covering Alembic downgrade/upgrade/check, forced RLS, constrained-role behavior, tenant visibility, exact grant loading, readiness projection, successful-read audit/no-outbox behavior, equal-key campaign-create replay, distinct-key same-slug conflict serialization, and cross-tenant create invisibility.
- Gitleaks `8.30.1`: the effective current worktree and `origin/main..HEAD` stacked history scans PASS with no leaks.
- AutoSkills `0.3.6`: package integrity and manifest reviewed; pinned `--dry-run` proposed eleven skills, installed none, and did not mutate the repository. The decision remains `NO_INSTALL`.

The nested Docker daemon still cannot prepare the complete Compose stack because the outer user namespace rejects layer operations. That limitation no longer blocks frontend-image verification: the same Dockerfile builds and smoke-tests successfully through daemonless Buildah with `vfs`/`chroot`. Native PostgreSQL and recorded CI remain the validated alternatives for the full Compose contract; no local Compose PASS is claimed.

## Implemented and preserved

- Fixed-algorithm OIDC identity verification remains separate from server-owned application authorization.
- Active, non-expired memberships and exact grants are loaded from tenant-scoped PostgreSQL transactions.
- Effective permission matching includes principal, tenant, campaign, workspace, action, resource type, resource identifier, purpose, validity, and revocation state.
- Campaign list/get/update boundaries enforce exact campaign grants, sanitized errors, pagination, optimistic concurrency, idempotency, atomic audit, and outbox evidence.
- The draft stack serializes equal idempotency keys, claims outbox rows with leases and `SKIP LOCKED`, recovers expired work, applies bounded retries/dead-letter state, and revalidates tenant evidence before internal delivery.
- Workspace creation requires an exact campaign-scoped grant and commits workspace, audit, outbox, and idempotency evidence atomically.
- Campaign readiness requires an exact tenant/campaign/resource/purpose grant, reports only operational setup, appends a successful-read audit receipt, emits no outbox event and refuses to act as a human approval.
- Campaign creation requires an exact tenant-level collection grant and commits a server-owned `DRAFT` campaign, purpose-bound audit receipt, internal `campaign.created` outbox event and replay receipt atomically; concurrent PostgreSQL requests serialize by idempotency key and tenant slug.
- Campaign, workspace and readiness audit appends now share a tenant-serialized, monotonic hash-chain primitive.
- The machine-readable eval catalog preserves missing capabilities as `NOT_IMPLEMENTED`/`NOT_RUN` instead of inferring PASS.
- A real Next.js/React/TypeScript shell now exists separately from `web/`. It keeps bearer material server-only, treats tenant/campaign cookies as context rather than authority, validates upstream JSON at runtime, supports ES/EN document parity, fails closed outside an explicit synthetic demo mode, and passes automated browser/accessibility review.
- The static `web/` surface remains preserved as `DEMO_NON_PRODUCTION` and a visual reference; its JavaScript is not imported into the dynamic runtime.
- The Governance Workspace mutation-race regression and narrow Gitleaks false-positive handling remain present.
- `RTK.md` was read only and remains unchanged. `artifacts/c1-front-003/` is not present in this sandbox checkout; no cleanup or destructive Git operation was used.

## What remains unproven or absent

- No live OIDC provider, login, invitation, recovery, MFA, durable session lifecycle, or revocation path is integrated.
- No membership-administration, support-elevation, or time-bound support-access workflow exists.
- Campaign creation and readiness are local/PostgreSQL proof only; candidate, approval, assignment, artifact, guided-intake, team, roadmap and broader evidence workflows remain unimplemented or prototype-only.
- The outbox worker has no reviewed external transport, administration surface, production observability, staging concurrency proof, or external political effects.
- S3Mock and Mailpit remain local test dependencies; production object storage, email, attachment validation, quarantine, malware handling, KMS, and retention are absent.
- The dynamic shell is local and synthetic-only; live login/session integration, trusted tenant selection, campaign mutation UI, guided onboarding, full-product i18n, Training Academy, and complete API-backed non-technical journeys remain absent.
- No Terraform, AWS dev/staging/production environment, backup, restore, load, rollback, disaster-recovery, or production observability evidence exists.
- Branch-protection enforcement is unverified; no SBOM, provenance, image signing, or protected promotion flow exists.
- Six historical CI failures and five CRITICAL/HIGH findings remain explicit blockers; none has been removed or inferred away.
- No independent production security, privacy, legal, political-science, research-methodology, communication-ethics, or human production approval is recorded.

## Delivery table

| Area | Evidence | Determination |
|---|---|---|
| Foundation, IAM, first campaign API | PRs `#72`, `#73`, `#83` merged with green recorded checks | `MERGED`; not deployed |
| Active review stack | PRs `#84` → `#85` → `#86`, draft and green at recorded heads | `CI_GREEN`; not merged |
| Local quality | 327 passed, 2 skipped, 90.92% enforced coverage, lint, format, mypy, program/eval/safety validators | `TESTED_LOCAL` |
| Readiness slice | Exact authorization, deterministic projection, audit and no-outbox tests | `VERIFIED_POSTGRESQL`; CI/review/merge pending |
| Campaign-create slice | Exact collection authorization, atomic evidence, replay and concurrent slug-conflict tests | `VERIFIED_POSTGRESQL`; publication/CI/review pending |
| Dynamic frontend shell | Exact lock, typed server-only API client, runtime parsers, ES/EN, production build, browser/WCAG review and daemonless non-root image smoke | `TESTED_LOCAL`; current-branch CI/review/deploy pending |
| PostgreSQL | Native temporary PostgreSQL integration PASS; prior-stack CI PostgreSQL jobs green | `VERIFIED_POSTGRESQL_LOCAL`; current branch CI pending |
| Local Compose | Nested-daemon ownership limitation | `LOCAL_BLOCKER`; CI substitute retained |
| Historical validation | Six manifest-linked runs retain `FAILURE` | Production-blocking until explicit supersession |
| Rulesets/protection | Public rulesets empty; protection endpoint requires auth | Required-check enforcement unverified |
| Pages | Live HTTPS static site; workflow manual-only | `DEMO_NON_PRODUCTION` |
| AWS | No current credentials or IaC environment evidence | `NOT_VERIFIED` |

## Historical CI evidence requiring explicit supersession

These run IDs retain conclusion `FAILURE` until a reviewed record supplies `superseded_by`, scope-equivalent verification evidence, reviewer, date, and reason:

```text
29659355550
29659451027
29659542083
29659623156
29659692005
29659733648
```

Later green runs do not rewrite those records automatically.

## Program-tool evidence

- AutoSkills `0.3.6` package integrity is recorded, but suggested third-party skill payloads remain uninstalled because individual license, path, provenance, and prompt-injection review is incomplete.
- Context7 is not available as a live MCP capability in this workspace. Previously retained references remain advisory; current implementation uses pinned dependencies, official source cross-checks, and executable tests.
- Farmtable is unavailable; the fail-closed task graph, ledger, manifest, and iteration records preserve equivalent dependency semantics.
- Producer, critic, fixer, independent verifier, and release-review responsibilities are separated sequentially in this session record; no producer self-approval is claimed.

## Next executable increments

1. `C3-ONBOARD-001`: add a persisted, resumable guided-intake aggregate and API-backed shell journey that begins from campaign creation/readiness without producing strategy or external effects.
2. Continue `C3-IAM-002` contract-first invitation, membership, session, and support-elevation lifecycle work without claiming live Cognito integration.
3. Advance Terraform validation, operations evidence and additional required evals in independent workstreams without inferring deployment readiness.
4. Expand the dynamic shell only through bounded, authorized product journeys; preserve `web/` until explicit parity review.

Production deployment remains prohibited until every production gate passes and an authorized human records an explicit scoped approval receipt.
