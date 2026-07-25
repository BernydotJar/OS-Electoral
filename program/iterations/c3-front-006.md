# C3-FRONT-006 — Cinematic adaptive campaign journey

- `branch`: `agent/c3-front-006-cinematic-adaptive-journey`
- `base`: `agent/c3-front-005-team-organization-workflow@ecf1168c4ee9c6257596cccf4babbb7c040e6146`
- `status`: `CI_GREEN`
- `production_status`: `BLOCKED`
- `release_decision`: `DENY_RELEASE`
- `external_effects`: `NONE`

## User problem

The launch path is functionally correct but still reads as a conventional dashboard. A candidate, representative or consultant needs an entry that communicates ambition, continuity and the current mission without replaying onboarding on every visit or exposing unavailable modules as if they worked.

## Bounded objective

1. adapt the opening to first use, active work and completed operating path;
2. create an owned five-act visual narrative without third-party runtime media;
3. make one current chapter dominant while preserving the complete route;
4. expose progress and current-step semantics to assistive technology;
5. explain blocked stages with an actionable condition;
6. preserve exact authorization, evidence gates and human authority.

## File ownership

- `task_id`: `C3-FRONT-006`
- `workstream_id`: `WS-06/WS-07`
- `writer`: frontend and motion-design implementation role
- `allowed_paths`: adaptive journey components, i18n, global design tokens/styles, frontend browser review, design/product/testing/program documentation
- `read_only_paths`: backend domain, migrations, infrastructure and production authorization policy
- `write_lock`: one writer per modified file

## Acceptance criteria

1. First use renders a five-act owned storyboard and one primary action.
2. Active work renders the exact current mission and persisted progress rather than replaying the welcome.
3. Complete work renders a command-center entry rather than onboarding.
4. The dominant chapter has `aria-current="step"`; progress has min, max and current values.
5. Blocked chapters render no action link and explain the exact corrective path in human language.
6. ES/EN, desktop/mobile, keyboard, visible focus, reduced motion, zero page overflow and axe WCAG 2.2 AA automation pass.
7. No third-party video, visual asset, tracking, browser storage or outbound host is introduced.
8. Production remains blocked and no external campaign effect occurs.

## Validation record

- RED: five focused rendering tests failed for the intended missing behavior.
- GREEN: five focused rendering tests pass.
- Frontend regression: 88 tests, ESLint, strict TypeScript, production build and zero-vulnerability npm audit pass.
- Browser regression: ES/EN/mobile, keyboard, reduced motion, zero axe violations, zero page overflow, empty browser storage and no external hosts pass.
- Local Docker functional E2E is classified as an environment limitation because image-layer registration failed at `lchown /var/empty` before product execution; hosted exact-head CI is required.

## Product boundaries

This increment changes presentation and orientation only. It does not change campaign state, create evidence, assign people, approve strategy, execute tasks, publish content, contact citizens, spend funds, mobilize, deploy or grant production authority.


## Exact-head hosted closure

- Draft PR `#121` published at `9d98f754924a94a1bfc5be190e8604d51673f99c`.
- CampaignOS CI `30171986190` and Runtime Visual Review `30171986166` succeeded.
- Compose, PostgreSQL 18, RLS, backup/restore, API-backed browser, CodeQL, Terraform, secrets, dependencies and supply-chain checks passed.
- Status is `CI_GREEN`; human product review and merge remain separate gates.
