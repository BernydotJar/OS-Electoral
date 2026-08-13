# C3-TEAM-005 review

Review state: `REVIEWED_LOCAL`; implementation commit `7f8f3af141d237efdbf0e588c5a04bc7f17dcfa2`; exact-head hosted CI pending.

## Producer

Completed the existing Team readiness lifecycle through exact-authorized UI controls for training requirements and access recommendations, including explicit reviewed-empty states. The implementation reuses the merged Team PATCH contract, current-version concurrency and idempotency and creates no new backend political model or database schema.

## Critic / Red Team

- repaired Graph Harness branch/active-increment drift after dependency validation selected Team ahead of Strategy;
- corrected the blocked C3-FRONT-014 iteration record so it no longer claims Producer execution;
- verified reviewed-empty requests fail closed over non-empty collections;
- verified access recommendations remain advisory, campaign-scoped and `authority_effect=NONE`;
- verified stale version, unknown role and missing exact Team update grant fail closed;
- verified read-only rendering contains no Team readiness mutations and no visible forbidden review-mode wording.

## Fixer

All critic findings are resolved. The API-backed browser journey reaches Team `READY_FOR_HUMAN_REVIEW` with all 8 checks complete and retains `external_effects=NONE`.

## Independent Verifier

- clean frontend install and verify: 42 files / 186 tests, ESLint, TypeScript, optimized build, audit 0 vulnerabilities;
- backend repository gate: 865 passed, 13 controlled skips, 90.03% coverage;
- marked PostgreSQL gate: 12/12 selected tests PASS under an ephemeral test-cluster administrator;
- host functional browser journey: PASS, candidate 9/9 then Team 8/8;
- read-only dynamic browser: PASS ES/EN/mobile/keyboard/reduced-motion/WCAG/no mutation controls;
- compose config, supply-chain, Gitleaks, security, program/release/eval/safety validators: PASS;
- Terraform 1.15.8 fmt/init/validate/test/policy: PASS, plan-only.

## Release Gate

The increment is eligible for review-branch publication and exact-head CI. Production remains `BLOCKED` and release remains `DENY_RELEASE`; no production, Firmes or external political authority is implied.

## Persistent Evidence

See `docs/testing/c3-team-005-evidence.md`, `program/validations/c3-team-005.json`, this review, the iteration record and task ledger. Hosted CI evidence must be appended after publication.

## Hosted exact-head verification

- exact head: `052dd12f6d2455c17167edb42c3074faf1cbacba`;
- CampaignOS CI run `31662989783` / #258: `SUCCESS`;
- Runtime Visual Review run `31662989806` / #233: `SUCCESS`;
- API-backed functional onboarding on the exact head: `PASS_TEAM_8_OF_8_READY_FOR_HUMAN_REVIEW`;
- exact-head release status: eligible for merge after the evidence-only final head is independently green; production remains `BLOCKED` and global release remains `DENY_RELEASE`.

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
