# CampaignOS current-state assessment

Assessment date: `2026-07-21 America/Guatemala`

Authoritative target: CampaignOS production-readiness program for `BernydotJar/OS-Electoral`.

Repository evidence point: `main@d0719c91dd6b0ac68e8499912c6c4eef983a0b1f`; draft review stack `#84` through `#89`; frontend head `agent/c3-front-001-dynamic-shell@437b46930c68d6ed3a8233c139b0eaa03724b068`; active local identity worktree `agent/c3-iam-002-identity-lifecycle` based for review on that frontend head.

## Executive determination

Production readiness is **BLOCKED**.

Foundation PR `#72`, IAM PR `#73` and the first protected campaign API PR `#83` are merged. Draft PRs `#84` through `#89` form a correctly based review chain and are green at their recorded heads. PR `#89` initially exposed a relative frontend artifact-path defect in run `29854467576`; commit `437b469` repaired the root cause and exact-head run `29856835515` plus visual run `29856835522` succeeded.

The active `C3-IAM-002` worktree adds tenant-scoped invitation, application-session, membership-revocation and time-bound support lifecycles. Those controls are verified locally and against isolated PostgreSQL, but the branch is not yet published and no live provider operation exists. None of this evidence is a deployment or human production approval.

The only public deployed surface remains the static, read-only GitHub Pages demonstration classified `DEMO_NON_PRODUCTION`.

## Reconciled repository and GitHub state

- Merged PRs: `#72`, `#73`, `#83`.
- Draft stack: `#84` → `#85` → `#86` → `#87` → `#88` → `#89`.
- PR `#87` at `3b4bc9b` passed CampaignOS CI `29854461414` and visual review `29854461367`.
- PR `#88` at `a21e735` passed CampaignOS CI `29854464519` and visual review `29854464523`.
- PR `#89` at `437b469` passed CampaignOS CI `29856835515` and visual review `29856835522`.
- Twenty-three non-PR issues remain open.
- Authenticated repository-settings inspection confirmed: `main` has no branch protection; rulesets are empty; all Actions/workflows are allowed; repository SHA pinning is not required; vulnerability alerts are disabled.
- Those settings are a confirmed production blocker. They are not a blocker to feature-branch implementation, normal push or draft PR creation.
- No force-push, merge or deployment occurred.

## Current verification

- `make verify`: PASS.
- Ruff lint and format: PASS.
- strict mypy: PASS across 36 source files.
- Full locked suite: `381 passed`, `3 skipped`.
- Enforced coverage: `91.34%` with `fail_under=90`.
- Isolated PostgreSQL gate: `3 passed`, `5 deselected`, reproduced twice after database recreation.
- PostgreSQL evidence covers Alembic downgrade/upgrade/check, revision `20260721_0004`, forced RLS, a `NOSUPERUSER`/`NOBYPASSRLS` runtime role, tenant isolation, invitation concurrency/replay, session digest persistence and support revocation/regrant.
- Frontend regression: ESLint, strict TypeScript, 12 Vitest tests, Next production build and npm audit with zero vulnerabilities PASS.
- Frontend exact-head PR CI and automated browser/WCAG review: PASS.
- Program truth: PASS with five open CRITICAL/HIGH findings and six retained historical failed runs.
- Required eval inventory: `5 PASS`, `12 PARTIAL`, `16 NOT_RUN`; production remains blocked.
- Campaign safety scan: PASS.

## Implemented and preserved

- Fixed-algorithm OIDC verification remains separate from application authorization. The principal now preserves validated `email_verified`, `iat` and `exp` evidence.
- Active memberships and exact grants remain server-owned and tenant scoped.
- Campaign create/read/update, workspace create and readiness boundaries retain exact action/resource/scope/purpose checks, concurrency controls, audit and internal outbox evidence.
- The internal outbox worker draft retains leases, `SKIP LOCKED`, recovery, bounded retries and dead-letter behavior without external political delivery.
- The dynamic Next.js shell remains server-rendered, ES/EN, synthetic/read-only outside live configuration and fail-closed on malformed or cross-scope upstream data.
- Identity invitations normalize email, require `email_verified=true` at acceptance, expire, accept once and create only an empty membership.
- Application sessions persist only a digest of the provider session identifier and support audited expiry and local revocation.
- Membership revocation disables current grants, roles and local sessions atomically.
- Support access binds requester, target, approver, tenant/campaign/workspace, exact action/resource/purpose, reason, receipt and expiry. Separation of duty is enforced. Pre-existing membership and unrelated access are preserved.
- Invitation, session and support expiry transitions are persisted and audited; active uniqueness slots are released only after terminal state.
- Provider planning remains no-effect: a Cognito `AdminCreateUser` request can be described, but no SDK, email or external provider call is wired.
- `RTK.md` and `web/` remain unchanged.

## What remains absent or unproven

- No live OIDC/Cognito login, recovery, MFA, invitation email, provider token rotation or external provider revocation.
- No trusted tenant portfolio selector or customer-facing identity-administration UI.
- No RDS, dev, staging or production verification of identity lifecycle.
- Guided intake, Candidate Workspace, Team Builder, campaign roadmap, durable approvals and broader product journeys remain absent or prototype-only.
- Production object storage, attachment safety, external transport, production observability, rate controls and operational administration remain incomplete.
- No Terraform baseline, verified AWS environment, backup/restore, load, rollback or disaster-recovery evidence.
- Main is unprotected; rulesets and required checks are absent; Actions policy is permissive and vulnerability alerts are disabled.
- Six historical failures and five CRITICAL/HIGH findings remain explicit production blockers.
- No independent security, privacy, accessibility, domain, legal or human production approval is recorded.

## Delivery table

| Area | Evidence | Determination |
|---|---|---|
| Foundation/IAM/first campaign API | PRs `#72`, `#73`, `#83` merged | `MERGED`; not deployed |
| Review stack | PRs `#84`–`#89`, correct bases and green exact-head checks | `CI_GREEN`; human review/merge pending |
| Dynamic frontend | `437b469`, CI `29856835515`, visual `29856835522` | `CI_GREEN`; synthetic and not deployed |
| Identity lifecycle | migration, API, contracts, 381-test suite, PostgreSQL twice | `VERIFIED_POSTGRESQL`; unpublished local branch |
| Required evals | exact 33-item fail-closed catalog | `5 PASS / 12 PARTIAL / 16 NOT_RUN` |
| Repository protection | authenticated API: no protection/rulesets; all Actions allowed; no SHA policy | production blocker confirmed |
| Historical validation | six manifest-linked failures retained | production-blocking until explicit supersession |
| AWS/operations | no verified environment, backup/restore or observability | `NOT_VERIFIED` / `NOT_IMPLEMENTED` |

## Historical validation requiring explicit supersession

The following run IDs retain `FAILURE` and remain production-blocking:

```text
29659355550
29659451027
29659542083
29659623156
29659692005
29659733648
```

Frontend run `29854467576` is separately recorded as superseded by exact-scope run `29856835515`; it is not silently deleted.

## Next executable increments

1. Publish `C3-IAM-002`, create its draft PR against `agent/c3-front-001-dynamic-shell`, obtain exact-head CI and record the checkpoint.
2. Begin `C3-ONBOARD-001`: persisted resumable guided intake starting from campaign creation/readiness, with no automatic strategy or external effect.
3. Advance independent platform plan-only and operations evidence without AWS apply or production claims.
4. Continue closing required evals and confirmed CI/supply-chain findings.

Production deployment remains prohibited until every production gate passes and an authorized human records explicit scoped approval.
