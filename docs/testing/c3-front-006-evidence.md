# C3-FRONT-006 evidence — cinematic adaptive campaign journey

Date: 2026-07-25
Branch: `agent/c3-front-006-cinematic-adaptive-journey`
Base: `agent/c3-front-005-team-organization-workflow@ecf1168c4ee9c6257596cccf4babbb7c040e6146`

## Implemented behavior

- Added explicit `opening`, `mission` and `command` layouts derived from persisted campaign progress.
- Added a CSS-owned five-act first-use storyboard: territory, evidence, team, strategy and operation.
- Replaced the flat route list with one dominant current chapter and a summarized chapter horizon.
- Added an exact progressbar, `aria-current="step"`, visible focus and textual blocked-state remediation.
- Kept all visual assets local to the application; no video, SceneAI runtime asset, browser storage, tracking request or external host was introduced.
- Kept every political, legal, publication, spending, contact, mobilization, deployment and production decision under explicit human authority.

## TDD evidence

```text
RED: 5 focused tests failed for missing adaptive layouts, storyboard, progress semantics, dominant chapter and blocked explanation
GREEN: 5 focused component-rendering tests pass
REGRESSION: 88 frontend tests pass
```

## Deterministic frontend evidence

```text
ESLint: PASS
TypeScript strict: PASS
frontend tests: 88 PASS
Next.js production build: PASS
npm audit: 0 vulnerabilities
```

## Browser evidence

```text
desktop_spanish: PASS
desktop_english: PASS
mobile_spanish: PASS
keyboard_skip_link: PASS
reduced_motion: PASS
horizontal_overflow: NONE
wcag_2_2_aa: PASS_ZERO_AXE_VIOLATIONS
browser_storage: EMPTY
unexpected_outbound_hosts: []
console_errors: []
page_errors: []
adaptive_active_mission: PASS
campaign_progress_semantics: PASS
dominant_chapter: PASS
current_chapter_semantics: PASS
third_party_cinematic_media: NONE
```

## Environment classification

The local Docker functional E2E did not reach product execution because the nested daemon failed while registering an image layer:

```text
failed to register layer: lchown /var/empty: permission denied
```

This is an environment limitation with a required hosted-CI alternative. Exact-head CI must prove Compose, PostgreSQL 18, the API-backed browser journey, recovery, CodeQL, Terraform and supply-chain evidence before the increment can become CI-green.

## Independent review

### Specification compliance

PASS. The first-use experience is cinematic, returning users receive the current mission, completed routes lead to the command center, and campaign gates remain server-owned.

### Code quality and production readiness

PASS with residual scope. Motion uses opacity/transform, has reduced-motion cancellation, blocked stages cannot render action links, and no external visual dependency exists. The global stylesheet remains a future modularization opportunity, but no critical or high defect was found in this slice.

## Current decision

```yaml
increment_status: TESTED_LOCAL
production_status: BLOCKED
release_decision: DENY_RELEASE
external_effects: NONE
next_gate: exact-head hosted CI and human product review
```
