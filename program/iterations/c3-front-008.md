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
5. present team follow-up creation and the operating board as physically interleaved cards that exchange front/back positions;
6. keep mission/command heroes in the command overview and remove them from chapter task surfaces;
7. make completed guided intake a collapsed, revisable one-time setup;
8. expose version/digest-bound template application beside the preview summary;
9. state the command-view boundary and defer personal visibility until server-side principal/grant projection exists.

## Acceptance criteria

1. Guided team values serialize to the canonical `current_team` field and remain removable and keyboard operable.
2. Candidate actions expose next gate, evidence gaps, contradictions, risk decisions, development and approvals without authorizing public use.
3. Candidate profile, evidence and action surfaces are mutually exclusive tab panels.
4. Team board and creation remain in one stacked surface; the inactive card is visible behind but inert and hidden from the accessibility tree.
5. Navigation begins with the guided route when its exact grant exists, and completed intake defaults to a collapsed review disclosure.
6. The campaign hero appears only on the command overview; chapter workspaces expose no duplicate mission hero.
7. Template confirmation appears before detailed role dossiers and applies only missing vacant functions.
8. ES/EN, desktop/mobile, keyboard, WCAG, route isolation and zero external hosts pass.
9. No client-only personal-work filtering or implied permission is introduced.

## Local validation

- 732 Python tests passed with 10 controlled skips and 90.38% coverage.
- 27 frontend test files / 119 tests passed.
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

## Human-review feedback closure

- Removed the mission hero from every chapter route while preserving it as the command-overview entry surface.
- Converted completed guided intake into a collapsed native disclosure that can be reopened for authorized edits.
- Rebuilt team operations as two physically interleaved cards; the inactive layer remains visible, inert and behind the active layer.
- Moved template confirmation above the detailed catalog and added the exact missing-function count to the action.
- Updated static, Chromium and hosted-journey contracts for hero isolation, setup collapse, stack geometry, keyboard depth exchange and template persistence.
- Local full verification and hosted exact-head PostgreSQL/API/browser CI passed at `92369e59162a134ed7c64188828fa15b5711a22e`.
- CampaignOS CI `30414864886` and Runtime Visual Review `30414864870` are successful; the two preceding harness-only failures are preserved and superseded.
- Production remains `BLOCKED`, release remains `DENY_RELEASE`, and external effects remain `NONE`.

## Feedback exact-head CI closure

- validated implementation head: `92369e59162a134ed7c64188828fa15b5711a22e`
- CampaignOS CI: `30414864886` — `SUCCESS`
- Runtime Visual Review: `30414864870` — `SUCCESS`
- quality job: `90459048337`
- API/PostgreSQL/browser job: `90459048370`
- visual job: `90459047769`
- recovery job: `90459048330`
- historical harness failures preserved and superseded: `30414156474`, `30414548165`
- status: `CI_GREEN`
- production: `BLOCKED`
- release: `DENY_RELEASE`
- external effects: `NONE`
