# CampaignOS current-state assessment

Assessment date: `2026-07-21 America/Guatemala`

Authoritative target: CampaignOS production-readiness program for `BernydotJar/OS-Electoral`.

Repository evidence point: `main@d0719c91dd6b0ac68e8499912c6c4eef983a0b1f`; draft review stack `#84` through `#92`; identity checkpoint `fecb1d347389eebd08d04be6d38a3f518787e4e4`; guided-intake checkpoint `agent/c3-onboard-001-guided-intake@05ed4b8825436d1c4cc9b3d35d2c57aeed71ec7c` with draft PR `#92`; active candidate worktree `agent/c3-candidate-001-evidence-workspace` is based on that checkpoint.

## Executive determination

Production readiness is **BLOCKED**.

Foundation PR `#72`, IAM PR `#73` and the first protected campaign API PR `#83` are merged. Draft PRs `#84` through `#90` form a correctly based review chain and are green at their recorded heads. PR `#89` initially exposed a relative frontend artifact-path defect in run `29854467576`; commit `437b469` repaired the root cause and exact-head run `29856835515` plus visual run `29856835522` succeeded.

Draft PR `#90` adds tenant-scoped invitation, application-session, membership-revocation and time-bound support lifecycles at `5eb45e9`. Those controls are local/PostgreSQL and exact-head CI-green, but no live provider operation exists. None of this evidence is a deployment or human production approval.

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
- strict mypy: PASS across 44 source files.
- Full locked suite: `467 passed`, `5 skipped`.
- Enforced coverage: `91.67%` with `fail_under=90`.
- Isolated PostgreSQL gate reaches revision `20260721_0006` and is reproduced twice on a disposable PostgreSQL 15 UTF8 cluster.
- PostgreSQL evidence covers forced RLS, `NOSUPERUSER`/`NOBYPASSRLS` runtime roles, tenant isolation, candidate create/update concurrency, exact replay and version-bound approvals.
- Frontend regression: ESLint, strict TypeScript, 0 Vitest tests, Next production build and npm audit with zero vulnerabilities PASS.
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
- Guided intake persists one tenant/campaign aggregate with exact-authorized start/resume/read/update, optimistic concurrency, authority-bound idempotency, audit and internal no-effect outbox evidence.
- Candidate Workspace persists evidence, claims, contradictions, development, reputation risks and append-only current-version section approvals under exact authorization and forced RLS.
- Candidate factual verification requires independent evidence; self-assessment, perception and contradiction references retain distinct semantics.
- The dynamic shell now renders a read-only ES/EN campaign-starting roadmap and fails closed on malformed, contradictory or cross-campaign intake evidence.
- Provider planning remains no-effect: a Cognito `AdminCreateUser` request can be described, but no SDK, email or external provider call is wired.
- `RTK.md` and `web/` remain unchanged.

## What remains absent or unproven

- No live OIDC/Cognito login, recovery, MFA, invitation email, provider token rotation or external provider revocation.
- No trusted tenant portfolio selector or customer-facing identity-administration UI.
- No RDS, dev, staging or production verification of identity lifecycle.
- Guided intake and Candidate Workspace persistence/read-only surfaces are verified locally/PostgreSQL; authenticated editing/approval journeys, dedicated reviewer separation, Team Builder, campaign roadmap, durable cross-domain approvals and broader product journeys remain absent or prototype-only.
- Production object storage, attachment safety, external transport, production observability, rate controls and operational administration remain incomplete.
- No Terraform baseline, verified AWS environment, backup/restore, load, rollback or disaster-recovery evidence.
- Main is unprotected; rulesets and required checks are absent; Actions policy is permissive and vulnerability alerts are disabled.
- Six historical failures and five CRITICAL/HIGH findings remain explicit production blockers.
- No independent security, privacy, accessibility, domain, legal or human production approval is recorded.

## Delivery table

| Area | Evidence | Determination |
|---|---|---|
| Foundation/IAM/first campaign API | PRs `#72`, `#73`, `#83` merged | `MERGED`; not deployed |
| Review stack | PRs `#84`–`#90`, correct bases and green exact-head checks | `CI_GREEN`; human review/merge pending |
| Dynamic frontend | `437b469`, CI `29856835515`, visual `29856835522` | `CI_GREEN`; synthetic and not deployed |
| Identity lifecycle | migration, API, contracts, 381-test suite, PostgreSQL twice, PR `#90` CI `29857981975` | `CI_GREEN`; human review/merge and live provider pending |
| Guided intake | revision `20260721_0005`, exact API, 425-test suite, PostgreSQL twice, 16 frontend tests, PR `#92`, CI `29865306720` and visual `29865306576` | `CI_GREEN`; human review/merge and live edit journey pending |
| Candidate workspace | revision `20260721_0006`, evidence contracts, exact API, 467-test suite, PostgreSQL twice, 22 frontend tests and WCAG browser gate | `VERIFIED_POSTGRESQL_LOCAL_ONLY`; branch/PR/CI publication pending |
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

1. Publish `C3-CANDIDATE-001`, verify exact remote SHA, open its stacked draft PR and repair exact-head CI if needed.
2. Start `C3-TEAM-001` as a separate evidence-governed team and accountability increment.
3. Advance authenticated non-technical editing/review journeys without merging or deploying.
3. Advance independent platform plan-only, operations evidence and confirmed CI/supply-chain findings without AWS apply or production claims.

Production deployment remains prohibited until every production gate passes and an authorized human records explicit scoped approval.
