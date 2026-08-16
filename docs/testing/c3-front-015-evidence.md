# C3-FRONT-015 evidence

Status: `REVIEWED_LOCAL_WITH_RUNNER_BLOCKERS`; branch `agent/operations-complete-ui-lifecycle`; base `main@57f0c4649cb5525647850ccc2c75b84240460e0c`; hosted exact-head verification pending.

## Implemented

- exact Operations/War Room capabilities use campaign-scoped resource IDs, null workspace scope and exact purposes; the local operator seed now has **26 regular grants** and the functional campaign journey has **27** after its campaign-create grant;
- exactly authorized operators can create the existing campaign roadmap and update it with backend `If-Match` versioning plus idempotency;
- phases, workstreams, milestones, tasks/dependencies, blockers, decisions, follow-ups and learning notes use the existing backend contracts; cross-record references are selected from current projections rather than free-form UUID fields;
- Operations tasks expose only `FILLED` Team roles as owners; task execution state remains an explicit human report and CampaignOS never starts a task automatically;
- a bounded Team self-coverage repair closes the pre-existing owner dead end: an exactly authorized operator may explicitly take one existing vacant function, while the server supplies the authenticated `principal_id`; the form cannot name another principal and the update creates no membership, grant or additional access;
- Operations authoring is visible only while the current Strategy remains `DECIDED_INTERNAL`, Team is ready for human review, at least one human function is filled, and exact Operations grants are present. A stale Strategy leaves the roadmap readable but removes mutation controls;
- a new operational decision is recorded as `REQUIRED` without an implicit selection. A later human choice may select only an option already persisted on the current decision record; changing alternatives and deciding in one request fails closed;
- the Daily War Room snapshot is created only from the exact current roadmap version with snapshot create/read authority and is verified against the current roadmap ID/version;
- backend-derived readiness, ready/blocked tasks and critical path remain authoritative read models;
- demo/read-only review renders no Operations or Team self-coverage mutations;
- ES/EN copy is complete, including the immutable-snapshot boundary; no citizen contact, voter profiling/targeting, persuasion, publication, spend, mobilization, Firmes sync, autonomous execution or production deployment is introduced.

## Producer verification

- frontend final verifier: **54 test files / 248 tests PASS**;
- ESLint: PASS;
- strict TypeScript: PASS;
- optimized Next.js build: PASS;
- npm audit: **0 vulnerabilities**;
- backend complete suite: **865 passed / 13 skipped**, **90.03%** coverage;
- focused Operations + Team backend/API/seed slice: **99 PASS**;
- focused local operator seed: **3 PASS**, proving 26 regular grants;
- Ruff lint / Ruff format / mypy: PASS;
- security/privacy, program truth, release readiness, eval catalog and campaign safety: PASS;
- Docker Compose v2 resolved config: PASS;
- supply-chain policy/evidence: PASS;
- Gitleaks `8.30.1`: official release checksum verified; effective tracked/non-ignored worktree PASS/no leaks.

## Critic / Red Team findings and repairs

1. **C3-FRONT-015-F1 — HIGH — RESOLVED.** An operational decision update could otherwise combine a changed option list with `DECIDED` in one mutation. The route now requires an existing decision record, byte-for-byte ordered equality with its already-persisted alternatives, and a selected value from that existing set. Adversarial tests prove the combined rewrite/decision request fails closed.
2. **C3-FRONT-015-F2 — HIGH — RESOLVED.** The backend requires at least one `FILLED` Team function before any roadmap can exist, while the existing UI could only create `VACANT` functions. This made the Strategy → Operations journey impossible through UI. The repair adds current-session self-coverage over the existing Team update contract, derives `principal_id` only on the server, requires exact Team read/update grants, positive capacity and explicit onboarding confirmation, and creates no identity, membership or permission authority.
3. **C3-FRONT-015-F3 — HIGH — RESOLVED.** An already-created roadmap initially kept its mutation editor visible if Strategy later stopped being `DECIDED_INTERNAL`. Same-origin routes already rejected writes, but UI authoring did not reflect the current gate. The editor now disappears while historical read evidence remains visible, with a component test for the stale-Strategy case.
4. **C3-FRONT-015-F4 — MEDIUM — RESOLVED.** The existing War Room snapshot eyebrow was hardcoded in English on the Spanish route. It is now localized through the Operations dictionary and i18n/chapter tests pass.

## Independent read-only browser verification

The optimized production frontend passed the local Chromium review:

- Spanish desktop: PASS;
- English desktop: PASS;
- Spanish mobile: PASS;
- keyboard skip-link: PASS;
- chapter route isolation and locale preservation: PASS;
- reduced-motion static equivalent: PASS;
- WCAG 2.2 AA axe violations: ZERO;
- horizontal overflow: NONE;
- browser storage: EMPTY;
- unexpected outbound hosts: NONE;
- console errors: NONE;
- page errors: NONE.

The local Runtime Visual run produced desktop/mobile screenshots during verification; generated binary artifacts are not part of the review-branch source diff, while the PASS result is retained here.

## Functional PostgreSQL / API / browser journey

The functional harness is extended through the real public UI contract to cover:

`Candidate approved → Team ready → authenticated human role coverage → Strategy DECIDED_INTERNAL → roadmap create → phase → workstream → evidence-linked task → required human decision → explicit later decision → follow-up → learning note → immutable War Room snapshot → reload persistence`, with ES/EN/mobile/WCAG checks.

Local execution is **BLOCKED_BY_RUNNER**, not PASS. Docker Compose v2 itself works in the sandbox, but the sandbox Docker daemon cannot apply PostgreSQL/API image layers and fails before services start with `lchown /var/empty: permission denied`. No functional assertion ran, so no product success is inferred from this attempt. Exact-head hosted CampaignOS CI must execute this gate.

## Other local tooling limitation

Terraform plan-only verification is **BLOCKED_TOOLING** because the sandbox does not provide the Terraform CLI. No Terraform change is part of C3-FRONT-015 and no apply or cloud action was attempted. Exact-head CI remains the verifier for that repository gate.

## Baseline reconciliation

GitHub confirms PR #179 (`fix(program): reconcile strategy merge and activate operations`) merged to `main@57f0c4649cb5525647850ccc2c75b84240460e0c` on 2026-08-14. Its exact review head `af063d2a67c820377fc1b6a01693889625a5d598` passed CampaignOS CI #266 (`31768884886`) and Runtime Visual Review #238 (`31768884792`); post-merge `main@57f0c464…` passed CampaignOS CI #267 (`31769160111`). This is the exact C3-FRONT-015 base.

## Release Gate

C3-FRONT-015 is eligible for **review-branch publication and exact-head hosted verification only**. It is not a production release. Production remains `BLOCKED`; global release remains `DENY_RELEASE`; external effects remain `NONE`; no paid cloud resource or production deployment is authorized by this increment.
