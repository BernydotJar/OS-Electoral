# C3-FRONT-014 evidence

Status: `REVIEWED_LOCAL`; implementation commit `1a7d31d60c3d67705e04d47e0a6fe225bd1f5419`; exact-head hosted review pending.

## Implemented

- Strategy can start from the campaign journey only after Candidate is `INTERNALLY_APPROVED`, Team is `READY_FOR_HUMAN_REVIEW`, and the operator holds the exact Strategy create/read grants;
- exact-authorized operators can create or edit provenance-bearing evidence, assumptions, hypotheses, comparable options, measurable objectives, contradictions, and red-team findings through same-origin UI routes;
- references are bounded to existing Strategy records and Team roles rather than free-form UUID entry;
- contradictions and red-team findings support explicit reviewed-empty assessment, while the mutation route refuses an empty review that would erase an existing collection;
- Strategy readiness is derived by the backend. The UI exposes the decision form only at `READY_FOR_HUMAN_DECISION`, with the exact approve grant and no current-version decision;
- the human decision requires an explicit existing option, explicit existing Team role, and reason. It is append-only, current-version-bound, internal only, and does not increment the Strategy workspace version;
- read-only review exposes no Strategy mutation controls;
- no Strategy UI path creates identity, membership, grant, publication, spend, citizen contact, voter targeting, persuasion, or mobilization.

## Producer verification

- complete frontend verify: **47 test files / 215 tests** PASS;
- ESLint: PASS;
- strict TypeScript: PASS;
- optimized Next.js build: PASS;
- npm audit: **0 vulnerabilities**;
- full backend: **865 passed / 13 skipped**, **90.03%** coverage;
- focused local operator seed: PASS with **21 regular grants**, including all four exact Strategy grants;
- functional seed with campaign-create: **22 exact grants**.

## Critic / Red Team findings and repairs

1. **C3-FRONT-014-F1 — HIGH — RESOLVED.** Successful Strategy section and decision routes redirected to unregistered subanchors. The UI could therefore fall back to the overview after a successful mutation. The Fixer routes both success paths to the registered `strategy-room` chapter anchor and route tests assert pathname, notice, and hash.
2. **C3-FRONT-014-F2 — HIGH — RESOLVED.** The first Strategy option and Team role were initially preselected in the human-decision form, and the first Team role was preselected as an objective owner. Although no ranking was calculated, this weakened explicit human choice. The Fixer added disabled blank placeholders; option and role selection must now be deliberate.
3. **C3-FRONT-014-F3 — HIGH — RESOLVED.** Client-side Next chapter navigation could change the URL while leaving the document body empty after the completed journey. It reproduced for Strategy → Candidate and Team → Candidate while direct SSR returned HTTP 200 with the correct Candidate workspace. Removing only view-transition wrappers did not fix it. The Fixer converted chapter-navigation destinations to native document navigation and removed the experimental view-transition integration. The reproduction then returned the expected `#candidate-workspace` and a populated body.
4. **C3-FRONT-014-F4 — HIGH — RESOLVED BY DESIGN/TEST.** Reviewed-empty operations could be destructive if accepted over non-empty contradiction or red-team collections. The route fails closed and adversarial tests prove no update occurs.
5. **C3-FRONT-014-F5 — HIGH — RESOLVED BY DESIGN/TEST.** Strategy authoring must not become automated political recommendation or authority escalation. The UI does not generate, rank, score, or auto-select options; references are limited to existing records; authorization uses exact grants; external effects remain `NONE`.

## Functional PostgreSQL / API / browser verification

The API-backed optimized-build journey passes end to end:

- governed campaign draft: PASS;
- Candidate: `PASS_9_OF_9_CURRENT_VERSION_APPROVED`;
- Team: `PASS_8_OF_8_READY_FOR_HUMAN_REVIEW`;
- Strategy: `PASS_DECIDED_INTERNAL_VERSION_BOUND_HUMAN_DECISION`;
- Strategy evidence, assumption, two hypotheses, two comparable options, measurable objective, contradiction assessment, red-team assessment and human decision all persist through the public UI contract;
- Strategy decision persists after reload and the current-version decision form disappears;
- Spanish desktop: PASS;
- English desktop Strategy projection: PASS;
- Spanish mobile Strategy projection: PASS, single-column authoring;
- WCAG 2.2 AA axe violations: ZERO;
- horizontal overflow: NONE;
- visible forbidden review-mode wording guard: PASS;
- browser storage: EMPTY;
- unexpected outbound hosts: NONE;
- console/page errors: NONE;
- external effects: `NONE`.

Marked PostgreSQL verification passed **12/12 selected tests** across migration, campaign creation, identity, intake, Candidate, Team, operations, Strategy, agents, append-only security, rate limiting, and Training.

## Independent Verifier

- frontend full verifier: 47 files / 215 tests, lint, TypeScript, optimized build and audit PASS;
- backend complete suite: 865 passed, 13 controlled skips, 90.03% coverage;
- marked PostgreSQL: 12 selected PASS;
- independent dynamic read-only browser: PASS ES/EN/mobile/keyboard/reduced-motion/route isolation/WCAG, browser storage empty, no unexpected outbound hosts;
- Docker Compose v5.4.0 resolved config: PASS;
- supply-chain policy/evidence: PASS;
- Gitleaks 8.30.1 checksum-verified effective-worktree scan: PASS/no leaks;
- Gitleaks history scan: **375 commits**, no leaks;
- Ruff / Ruff format / mypy: PASS;
- security/privacy policy: PASS;
- program truth: PASS with production `BLOCKED`;
- release readiness: PASS with decision `DENY_RELEASE`;
- eval catalog and C2 safety scanner: PASS;
- Terraform 1.15.8 checksum-verified fmt/init/validate/test: PASS; policy `PLAN_ONLY_NO_APPLY`.

## Release Gate

C3-FRONT-014 is eligible for **review-branch publication and exact-head hosted CI only**. It is not a production release. Production remains `BLOCKED`; global release remains `DENY_RELEASE`; Firmes remains human-approval pending; no cloud resource, billing, spend, public political effect, or external campaign action is authorized by this increment.

## Hosted exact-head verification

PR #178 verified exact review head `4fdb4fbf8641a1c39c04f4c93f523d696820c875`:

- CampaignOS CI run #263 (`31767680763`): **SUCCESS**;
- critical `Exercise the API-backed functional onboarding journey`: **SUCCESS**;
- non-root frontend container build: **SUCCESS**;
- CodeQL: **SUCCESS**;
- Runtime Visual Review run #236 (`31767680795`): **SUCCESS**.

A final evidence-only head will be pushed and must pass the same exact-head merge gate before merge.


## Post-merge reconciliation

PR #178 was squash-merged to `main@a2d7aa81455358eb0244b51556ffe3a192455c06`. CampaignOS CI #265 (`31768163466`) preserved the full frontend/API onboarding success, including Strategy `DECIDED_INTERNAL`, but failed the locked quality suite because the live Git reconciliation test correctly detected that the merged PR was still recorded as `REVIEWED`. This is a historical program-state reconciliation failure, not a Strategy functional regression. C3-FRONT-014 is now recorded `MERGED_TO_MAIN`; production remains `BLOCKED`, release remains `DENY_RELEASE`, and external effects remain `NONE`.
