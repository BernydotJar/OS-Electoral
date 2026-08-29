# C3-RELEASE-002 evidence — final controlled-use readiness

Date: 2026-08-29
Branch: `agent/final-controlled-use-readiness`
Baseline: protected `main@1b32e46304b47c04cf44510c4b5f1b29bb9391b9` (PR `#183` reconciliation)
Mode: Graph Engineering / SHIP review

## Determination

**`READY_FOR_CONTROLLED_INTERNAL_USE`** for an isolated internal development/review environment.

**Production remains `BLOCKED`; production release remains `DENY_RELEASE`; external effects remain `NONE`.**

This determination means the complete current CampaignOS product can be exercised internally as a coherent persisted workflow. It does not approve a public shared deployment using the development identity, production infrastructure, Firmes integration, citizen contact, targeting, persuasion, publication, spending or mobilization.

## Producer verification

### Program baseline

`make program-verify` on the recovered clean main baseline passed:

- security/privacy policy: PASS;
- canonical program truth: PASS with one open CRITICAL platform finding;
- production release readiness: PASS as `DENY_RELEASE`;
- eval catalog validation: PASS (`33` required; production remains blocked);
- campaign safety scan: PASS.

### Frontend

`make frontend-verify` passed:

- `npm ci`: 388 packages;
- ESLint: PASS;
- strict TypeScript: PASS;
- Vitest: **55 test files / 250 tests PASS**;
- optimized Next.js production build: PASS;
- production dependency audit: **0 vulnerabilities**.

### Backend

`make lint format-check typecheck test` passed:

- Ruff lint: PASS;
- Ruff format check: **180 files** already formatted;
- mypy: **86 source files**, no issues;
- pytest after the release-governance repairs: **872 passed / 13 skipped**;
- coverage: **90.03%**, satisfying the enforced 90% floor.

### Independent browser review

`make frontend-e2e` on the optimized production build passed:

- Spanish desktop: PASS;
- English desktop: PASS;
- Spanish mobile: PASS;
- keyboard skip link: PASS;
- chapter route isolation and locale preservation: PASS;
- command overview/progressive path: PASS;
- reduced-motion static equivalent: PASS;
- horizontal overflow: NONE;
- WCAG 2.2 A/AA automated violations: **ZERO**;
- browser storage: EMPTY;
- unexpected outbound hosts: NONE;
- console errors: NONE;
- page errors: NONE.

### PostgreSQL / API / live frontend journey

The exact host harness used by CampaignOS CI, `scripts/frontend/e2e_functional_onboarding_host.sh`, was run against an isolated local PostgreSQL database.

- migrations reached `20260801_0013`;
- functional seed: **27 exact grants** (26 regular grants plus one tenant campaign-create grant used only by the isolated full-journey harness);
- same-origin frontend/API readiness: PASS;
- governed campaign draft creation with access unchanged: PASS;
- chapter navigation/history: PASS;
- role blueprints, consultant dossiers, Team operations board and template application: PASS;
- Candidate dossier: **9/9 complete and current-version approved**;
- Team readiness: **8/8 `READY_FOR_HUMAN_REVIEW`**;
- human role coverage: PASS without new membership/grant authority;
- Strategy: **`DECIDED_INTERNAL`** through a version-bound explicit human decision;
- Operations: roadmap readiness, explicit decision, learning and War Room snapshot: PASS;
- persistence after reload: PASS;
- exact authorization controls: PASS;
- ES/EN/mobile/WCAG: PASS;
- browser storage/unexpected hosts/errors: NONE;
- external effects: **NONE**.

## Critic / Red Team findings

1. **C3-RELEASE-002-F1 — HIGH — RESOLVED.** Operator documentation was materially stale: it still described five grants, deferred campaign creation, missing rate limiting/observability, and an unimplemented Training Academy. The current product uses 26 regular grants, the isolated full journey adds one exact campaign-create grant, and the complete Candidate/Team/Training/Strategy/Operations lifecycle is integrated. README, functional-onboarding, release-readiness and production-gap guidance were reconciled.
2. **C3-RELEASE-002-F2 — HIGH — RESOLVED.** Canonical program state still recorded cumulative `main@f118cef… / PR #182` while protected GitHub main was `1b32e463… / PR #183`. Existing validators checked task/merge status but not exact live-main SHA. Canonical Git/GitHub state is reconciled and a regression now rejects exact-main drift when the validator runs on branch `main`.
3. **C3-RELEASE-002-F3 — HIGH — RESOLVED.** The repository had only a production `DENY_RELEASE` record, so a fully passing product journey had no machine-readable status distinct from production readiness. `program/controlled-use-readiness.json` plus its fail-closed validator now represent isolated internal usability while forcing production `BLOCKED`, `DENY_RELEASE`, development-auth containment, pending Firmes approval and external effects `NONE`.

## Graph Engineering observations

The consuming repository remains pinned to Graph Harness revision `0eb0d5fe09e3b1ecaf561b4a1cc9b32510480a26`. Current Graph Harness main `477bdcc3d390c30eb49d823e5c7fd105fee2cc4d` is a descendant and adds the typed executable project/event runtime. Migrating the pin and generating a hash-chained Graph Harness event ledger is useful delivery-governance work, but it is not required to operate the current product internally and is intentionally not mixed into this release review.

Open Dependabot PRs are maintenance work, not evidence of a main regression. In particular, separate CodeQL `init` and `analyze` bumps `#191/#190` pass the other nine CampaignOS jobs but fail the CodeQL analysis job when upgraded independently. Protected main remains on its previously green pinned workflow.

## Remaining production blockers

- `FND-PLATFORM-001` remains open: no independently verified managed runtime exists;
- no production-verified live OIDC login/recovery/MFA/provider operations;
- no managed staging or production environment;
- no managed encrypted backup/PITR evidence or accepted RPO/RTO exercise;
- no deployed telemetry/alert routing and managed failure exercises;
- stable zero-cost full-product shared hosting remains unresolved in issue `#181`;
- independent security, privacy, legal, domain and operational approvals are absent;
- explicit human production approval is absent;
- `C3-FIRMES-001` remains `spec_ready` with human approval pending.

## Independent Verifier after Fixer

- focused controlled-use/program/release validator suite: **29 PASS**;
- full Python suite after repairs: **872 passed / 13 skipped**, 90.03% coverage;
- Ruff on new/modified Python validation code: PASS;
- supply-chain policy verification: PASS;
- Gitleaks `8.30.1`: official release checksum verified; effective tracked/non-ignored worktree scan PASS/no leaks;
- controlled-use readiness: **11/11 gates PASS**;
- production release readiness remains **DENY_RELEASE** with eight production gates;
- program truth and campaign safety: PASS with production blocked.

## Release gate

C3-RELEASE-002 is eligible for review-branch publication and exact-head hosted verification. Merge remains a human gate. Production deployment remains prohibited and separately human-gated.

## Hosted exact-head verification

PR `#192` implementation/review head `da0c79fe724b4d4d7c811040b936f5d2c8fe2873` passed:

- CampaignOS CI #283 (`33273015280`): **SUCCESS**, all 10 jobs;
- Dynamic frontend contracts and browser review: **SUCCESS**, including the complete PostgreSQL/API/browser journey;
- PostgreSQL migrations/RLS, recovery, constrained stack, dependency audit, supply-chain, secret scan, Terraform plan-only and CodeQL: **SUCCESS**;
- Runtime Visual Review #245 (`33273015296`): **SUCCESS**.

The merge gate is intentionally non-self-referential: GitHub must report CampaignOS CI and Runtime Visual Review green on the **current PR head** at merge time. Exact final-head run IDs are retained in PR #192 release-gate comments. No commit may grant merge or production authority.
