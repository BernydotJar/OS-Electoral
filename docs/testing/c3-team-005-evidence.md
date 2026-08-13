# C3-TEAM-005 evidence

Status: `REVIEWED_LOCAL`; implementation commit `7f8f3af141d237efdbf0e588c5a04bc7f17dcfa2`; exact-head hosted review pending.

## Implemented

- Team chapter now exposes a progressive **Cerrar preparación del equipo** workflow for the two previously unreachable supporting-record checks;
- exact-authorized operators can explicitly persist reviewed-empty `training_requirements=[]` and `access_recommendations=[]` rather than leaving those reviews unassessed as `null`;
- training requirements can be added or edited against an existing Team role with the backend-defined progress states;
- access recommendations can be added or edited against an existing Team role and are normalized server-side to the current campaign scope with `workspace_id=null`, `resource_id=current campaign`, and `authority_effect=NONE`;
- supporting-record saves replace only the edited collection, preserve unrelated Team state, and use current-version optimistic concurrency plus idempotency;
- an empty-review request fails closed instead of erasing a non-empty collection;
- read-only review renders no Team readiness mutation surface and still exposes no user-facing forbidden review-mode wording;
- C3-FRONT-014 remains blocked until this increment is merged and the scheduler re-evaluates the sequential journey.

## Producer and focused verification

- Team readiness parser/component/route tests: PASS, including stale version, unknown role, missing exact grant and non-empty erase rejection;
- focused new tests: 12/12 PASS;
- API-backed optimized-build browser journey: PASS;
- candidate prerequisite remains `PASS_9_OF_9_CURRENT_VERSION_APPROVED`;
- Team reaches `PASS_8_OF_8_READY_FOR_HUMAN_REVIEW`;
- persistence, exact authorization, ES/EN, mobile and accessibility checks remain green.

## Critic / Red Team findings

1. The graph branch and `active_local_increment` still named the initially selected Strategy increment after dependency validation switched the active feature to Team. Fix: rename the local branch to `agent/team-readiness-ui-lifecycle` and reconcile canonical/fallback/harness metadata.
2. The blocked C3-FRONT-014 iteration record still said `Producer: active`. Fix: record Strategy as blocked pending C3-TEAM-005 and keep its Producer lifecycle unstarted.
3. Reviewed-empty mutation could have been destructive if allowed over a non-empty supporting collection. The route explicitly rejects that condition and the adversarial route test proves no update call occurs.
4. Access recommendations must never become grants. The route normalizes them to the current campaign, fixes `workspace_id=null`, fixes `authority_effect=NONE`, and reuses only the existing Team update grant.

No finding required weakening authorization, Team readiness, RLS, release, production or political-safety boundaries.

## Functional PostgreSQL/API/browser verification

Repository host harness result: PASS.

- candidate dossier completion: `PASS_9_OF_9_CURRENT_VERSION_APPROVED`;
- Team readiness completion: `PASS_8_OF_8_READY_FOR_HUMAN_REVIEW`;
- role blueprints and operations board: PASS;
- persistence after reload: PASS;
- exact authorization controls: PASS;
- desktop Spanish / English: PASS;
- mobile Spanish: PASS;
- WCAG 2.2 AA axe violations: ZERO;
- horizontal overflow: NONE;
- browser storage: EMPTY;
- unexpected outbound hosts: NONE;
- console/page errors: NONE;
- external effects: NONE.

The marked PostgreSQL target ran with an ephemeral local cluster administrator because those tests create constrained roles to prove RLS. Result: **12 passed / 5 deselected** across migration, campaign creation, identity, intake, candidate, team, operations, strategy, agents, append-only security, rate limiting and training.

## Complete local repository verification

- backend: 865 passed, 13 controlled PostgreSQL skips in the non-PostgreSQL unit target;
- coverage: 90.03% (required floor 90%);
- frontend clean install: `npm ci` PASS, 388 packages added, 390 audited, 0 vulnerabilities;
- frontend verify: 42 files / 186 tests, ESLint, strict TypeScript, optimized Next.js build and audit PASS;
- dynamic read-only Chromium review: PASS ES/EN/mobile/keyboard/reduced-motion/WCAG; no forms/domain buttons, no visible forbidden review-mode wording;
- Docker Compose config: PASS with workstation Compose v5.4.0;
- supply-chain policy/evidence: PASS;
- Gitleaks 8.30.1: checksum verified, effective worktree PASS/no leaks;
- Ruff, Ruff format and mypy: PASS;
- security/privacy policy: PASS;
- program truth: PASS with production `BLOCKED`;
- release readiness validator: PASS with decision `DENY_RELEASE`;
- eval catalog and C2 safety scanner: PASS;
- Terraform 1.15.8: fmt/init/validate/test bootstrap + platform PASS; policy `PLAN_ONLY_NO_APPLY`.

The first aggregate `make verify` attempt was interrupted by workstation tooling/I/O before tests: Docker Compose was initially unavailable and a concurrent npm reinstall was killed by the outer sandbox timeout. Equal-or-broader component gates were then rerun cleanly and passed. Hosted exact-head CI remains the independent clean-environment publication verifier.

## Boundary and release gate

This increment creates no identity assignment, application membership, permission grant, Firmes integration, production deployment, cloud resource, spend, publication, citizen contact, voter targeting, persuasion or mobilization. Production remains `BLOCKED`; global release remains `DENY_RELEASE`.
