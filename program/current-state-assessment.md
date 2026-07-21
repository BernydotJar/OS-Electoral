# CampaignOS current-state assessment

Assessment date: `2026-07-21 America/Guatemala`

Authoritative target: CampaignOS production-readiness program for `BernydotJar/OS-Electoral`.

Repository evidence point: `main` at `d0719c91dd6b0ac68e8499912c6c4eef983a0b1f`; green review stack through `agent/c3-api-004-workspace-write@236a0d04c5b2c061948261a5c60852e0d4736b0f`; published readiness checkpoint `agent/c3-api-005-campaign-readiness@3b4bc9b14834fa8c7d4a17b84e76fba6af0bdaf1`; published campaign-create implementation `agent/c3-api-006-campaign-create@c91d60217e2ee0c0ec0f38c139852e7d73c78a58`.

## Executive determination

Production readiness is **BLOCKED**.

Foundation PR `#72`, IAM PR `#73`, and the first protected campaign API PR `#83` are merged to `main`. Draft PRs `#84`, `#85`, and `#86` form a correctly based review stack and have green checks at their recorded heads. The published readiness branch adds an audited operational-readiness projection and the required-eval catalog. The current published branch adds exact-authorized, idempotent tenant campaign creation with atomic audit/internal-outbox evidence and real PostgreSQL concurrency proof. Public GitHub inspection found zero open PRs and zero workflow runs for its exact head, so no CI, review, PR or merge evidence is claimed. None of these proofs constitutes deployment or production approval.

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

## Verification reproduced at the current campaign-create worktree

- `make verify`: PASS.
- Ruff lint and format: PASS.
- Strict mypy across 33 source files: PASS.
- Full locked suite: `327 passed`, `2 skipped` on the uv-managed Python `3.14.6` environment.
- Enforced coverage gate: `90.92%` with `fail_under=90`.
- Program-truth validator: PASS with `production=BLOCKED`, five open CRITICAL/HIGH findings, and six retained failed runs.
- Required-eval catalog validator: PASS with all 33 required IDs inventoried as `5 PASS`, `8 PARTIAL`, and `20 NOT_RUN`.
- Campaign safety scan: PASS.
- Isolated PostgreSQL integration: `2 passed`, `5 deselected` against temporary PostgreSQL `15.18`, covering Alembic downgrade/upgrade/check, forced RLS, constrained-role behavior, tenant visibility, exact grant loading, readiness projection, successful-read audit/no-outbox behavior, equal-key campaign-create replay, distinct-key same-slug conflict serialization, and cross-tenant create invisibility.
- Gitleaks `8.30.1`: the effective current worktree and `origin/main..HEAD` stacked history scans PASS with no leaks.
- AutoSkills `0.3.6`: package integrity and manifest reviewed; pinned `--dry-run` proposed eleven skills, installed none, and did not mutate the repository. The decision remains `NO_INSTALL`.

The nested Docker daemon in the sandbox could not register any pulled image layer because its outer user namespace denied `lchown /var/empty`. This is a local platform limitation, not a product assertion. No local Compose PASS is claimed for this session. The equivalent constrained-stack E2E remains green in GitHub Actions at the recorded PR heads.

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
- The Governance Workspace mutation-race regression and narrow Gitleaks false-positive handling remain present.
- `RTK.md` was read only and remains unchanged. `artifacts/c1-front-003/` is not present in this sandbox checkout; no cleanup or destructive Git operation was used.

## What remains unproven or absent

- No live OIDC provider, login, invitation, recovery, MFA, durable session lifecycle, or revocation path is integrated.
- No membership-administration, support-elevation, or time-bound support-access workflow exists.
- Campaign creation and readiness are local/PostgreSQL proof only; candidate, approval, assignment, artifact, guided-intake, team, roadmap and broader evidence workflows remain unimplemented or prototype-only.
- The outbox worker has no reviewed external transport, administration surface, production observability, staging concurrency proof, or external political effects.
- S3Mock and Mailpit remain local test dependencies; production object storage, email, attachment validation, quarantine, malware handling, KMS, and retention are absent.
- The dynamic Next.js application shell, guided onboarding, full i18n, Training Academy, and API-backed non-technical journeys are absent.
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

1. `C3-FRONT-001`: review the static Premium Slate reference and begin the real Next.js/TypeScript authenticated shell with typed API contracts, tenant/campaign context, accessible states and Spanish/English foundations.
2. Continue `C3-IAM-002` contract-first invitation, membership, session, and support-elevation lifecycle work without claiming live Cognito integration.
3. Begin `C3-ONBOARD-001` only after the dynamic shell can consume campaign create/readiness safely.
4. Advance Terraform validation, operations evidence and additional required evals in independent workstreams without inferring deployment readiness.

Production deployment remains prohibited until every production gate passes and an authorized human records an explicit scoped approval receipt.
