# C3-FRONT-008 — Organic campaign flow and command-safe workspace decks

- `branch`: `agent/c3-front-008-organic-role-aware-flow`
- `base`: `agent/c3-team-004-role-operations-board@47119b2ecacbde3cd949d92f39a043ea93769fff`
- `status`: `CI_GREEN`
- `production_status`: `BLOCKED`
- `release_decision`: `DENY_RELEASE`
- `external_effects`: `NONE`

## User problem

Human review found that CampaignOS capabilities still competed inside long pages. Team intake used an ambiguous textarea, candidate evidence mixed profile, review and action guidance, and team operation stacked creation and monitoring instead of behaving as one system. The recurring hero also remained too dominant.

## Bounded objective

1. place the guided starting route before overview and administration;
2. replace free-form current-team intake with localized presets, function/coordination entries and chips while preserving the existing backend contract;
3. separate candidate actions, profile/risk and source/evidence work;
4. derive bounded candidate actions from persisted evidence and review state;
5. alternate team follow-up creation and the operating board as two views of one workspace;
6. compact recurring mission/command heroes without changing first-use cinematic behavior;
7. state the command-view boundary and defer personal visibility until server-side principal/grant projection exists.

## Acceptance criteria

1. Guided team values serialize to the canonical `current_team` field and remain removable and keyboard operable.
2. Candidate actions expose next gate, evidence gaps, contradictions, risk decisions, development and approvals without authorizing public use.
3. Candidate profile, evidence and action surfaces are mutually exclusive tab panels.
4. Team board and creation surfaces are mutually exclusive tab panels; the initial view follows whether work exists.
5. Navigation begins with the guided route when its exact grant exists.
6. Returning hero remains below the defined height gate and reduced motion preserves hierarchy.
7. ES/EN, desktop/mobile, keyboard, WCAG, route isolation and zero external hosts pass.
8. No client-only personal-work filtering or implied permission is introduced.

## Local validation

- 732 Python tests passed with 10 controlled skips and 90.38% coverage.
- 27 frontend test files / 118 tests passed.
- ESLint, strict TypeScript, Next.js production build and zero-vulnerability audit passed.
- Demo ES/EN/mobile/keyboard/reduced-motion browser review passed with zero axe violations and no overflow.
- Hosted PostgreSQL/browser validation remains required because the local nested Docker daemon failed before application startup while registering an upstream image layer.

## Exact-head CI closure

- validated implementation head: `1db72a82a147d8ca9402c370814331879c1ac3a5`
- draft PR: `#126`
- CampaignOS CI: `30400102360` — `SUCCESS`
- Runtime Visual Review: `30400102373` — `SUCCESS`
- quality job: `90412547513`
- API/PostgreSQL/browser job: `90412547652`
- visual job: `90412547343`
- recovery job: `90412547596`
- status: `CI_GREEN`
- production: `BLOCKED`
- release: `DENY_RELEASE`
- external effects: `NONE`
