# C3-TEAM-005 iteration

## Goal

Make the existing Team readiness contract completable through the UI so the sequential campaign journey can legitimately unlock Strategy.

## Graph selection

Pre-Producer dependency validation for C3-FRONT-014 found that Team remains `STRUCTURE_IN_PROGRESS`: the service initializes training requirements and access recommendations as unassessed `null`, while the UI exposes no mutation path for either required review. C3-FRONT-014 is therefore blocked behind this localized Team repair.

## Approval

`USER_EXPLICIT_APPROVAL` from the current Graph Harness product-completion instruction. Scope is internal Team readiness UI/API proxy/tests/evidence only; no identities, permissions, Firmes, production or external political effects.

## Lifecycle

- Producer: complete.
- Critic / Red Team: complete; four findings resolved.
- Fixer: complete.
- Independent Verifier: complete locally; hosted exact-head CI pending.
- Release Gate: production remains `BLOCKED`; global release remains `DENY_RELEASE`.

## Local verification

- functional browser: candidate 9/9 then Team 8/8 `READY_FOR_HUMAN_REVIEW`;
- frontend: 42 files / 186 tests, lint, typecheck, optimized build and audit PASS;
- backend: 865 passed / 13 controlled skips / 90.03% coverage;
- PostgreSQL marked: 12/12 PASS;
- read-only browser, compose, supply-chain, Gitleaks, security, program/release/eval/safety and Terraform 1.15.8 plan-only gates: PASS.

## Hosted exact-head verification

- review head: `052dd12f6d2455c17167edb42c3074faf1cbacba`;
- CampaignOS CI #258 / run `31662989783`: `SUCCESS`;
- Runtime Visual Review #233 / run `31662989806`: `SUCCESS`;
- API-backed functional onboarding on the exact head: `PASS_TEAM_8_OF_8_READY_FOR_HUMAN_REVIEW`;
- production remains `BLOCKED`; global release remains `DENY_RELEASE`.

## Post-merge Critic / Fixer cycle

PR #176 was squash-merged to `main@570549119537c0298e4da476ef01b3de8fa53903` after both final-head workflows passed. The first post-merge CampaignOS CI run `31663558148` / #260 then failed only in **Exercise the API-backed functional onboarding journey**. PostgreSQL/RLS/load, quality/contracts, Compose and the other repository jobs were green.

The uploaded browser artifact showed the failure before Candidate or Team work: after creating a draft and clicking **Cerrar aviso**, Playwright waited for `/es#campaigns` and timed out. The API and Next server logs were healthy. Critic analysis found a progressive-enhancement race: the client handler preserves the live fragment, but the server-rendered fallback href on the command overview was only `/es`. A click before hydration therefore lost `#campaigns`.

Fixer repair: the overview now renders a truthful `/es#campaigns` (or `/en#campaigns`) fallback even without JavaScript hydration. A static shell test locks that invariant. The existing strict E2E expectation remains unchanged; the product is fixed instead of weakening the verifier.

### Fixer verification

- static CampaignShell fallback regression tests: 9/9 PASS;
- strict TypeScript check: PASS before the later workstation dependency reinstall was interrupted;
- the functional E2E assertion remains strict at `/es#campaigns`; it was not weakened;
- program truth, release readiness and Graph Harness validator: PASS;
- a subsequent local `npm ci` attempt was interrupted by prolonged workstation I/O and left only local `node_modules` incomplete. No dependency or lockfile change is part of the repair. Clean dependency installation and the full API-backed browser journey are delegated to exact-head hosted CI.

## Closure after post-merge repair

- feature PR #176 merged to `570549119537c0298e4da476ef01b3de8fa53903`;
- historical post-merge CampaignOS CI #260 / `31663558148` failed only at the pre-hydration notice fallback and is retained as superseded evidence;
- repair PR #177 exact head `41d8932d7b7fa240addb025a453ca927c78aed07` passed CampaignOS CI #261 / `31664661462` and Runtime Visual #235 / `31664661420` with the strict functional journey green;
- repair merged to `main@f1dacd9625019664add60b89bff728f3f17d7cc9`;
- final post-merge CampaignOS CI #262 / `31664890643`: `SUCCESS`, including the API-backed functional onboarding journey;
- C3-TEAM-005 is `MERGED_TO_MAIN`; C3-FRONT-014 is now the active Graph Harness node.
