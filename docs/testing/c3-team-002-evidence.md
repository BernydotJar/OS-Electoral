# C3-TEAM-002 evidence — role blueprints and progressive cinematic mission

Date: 2026-07-25
Branch: `agent/c3-team-002-role-blueprints-cinematic-hero`
Base: `agent/c3-front-006-cinematic-adaptive-journey@427033c69cf8220821713a13a698232c3e033000`

## Implemented behavior

- Added versioned Spanish and English campaign-role blueprints.
- `LEAN_CAMPAIGN` creates five safe vacant job descriptions.
- `FULL_CAMPAIGN` creates the eight CampaignOS operating stations.
- `CUSTOM` remains empty.
- Added visible role purpose, responsibilities and human vacancy plan.
- Kept all generated roles without principal, capacity, membership, permission, access or external effect.
- Added blueprint locale/version/count to idempotent create evidence.
- Replaced repeated returning-user explanation with a native keyboard-operable contextual hint.
- Added owned cinematic horizon, aurora, signal and chapter-mark layers with reduced-motion cancellation.

## TDD evidence

```text
RED: campaignos.teams.blueprints module missing
RED: LEAN creation returned an empty SETUP_REQUIRED workspace
RED: frontend create payload omitted blueprint_locale
RED: active hero lacked progressive hint and additional cinematic layers
GREEN: 21 focused blueprint/model/contract tests
GREEN: 22 focused frontend contract/rendering/i18n tests
GREEN: 50 focused team backend tests
```

## Full local verification

```text
Python: 712 passed, 10 skipped
Coverage: 90.42% (floor 90%)
Ruff: PASS
Format: PASS
Mypy: PASS, 67 source files
Frontend: 88 tests PASS
ESLint: PASS
TypeScript strict: PASS
Next.js production build: PASS
npm audit: 0 vulnerabilities
Terraform plan-only: PASS
Program/release/safety validators: PASS
```

## Browser evidence

```text
desktop_spanish: PASS
desktop_english: PASS
mobile_spanish: PASS
keyboard_skip_link: PASS
keyboard_context_hint: PASS
reduced_motion: PASS
horizontal_overflow: NONE
wcag_2_2_aa: PASS_ZERO_AXE_VIOLATIONS
browser_storage: EMPTY
unexpected_outbound_hosts: []
console_errors: []
page_errors: []
third_party_cinematic_media: NONE
```

## Environment classification

The local API/PostgreSQL browser journey did not reach product execution because the nested Docker daemon failed while registering an image layer:

```text
failed to register layer: lchown /var/empty: permission denied
```

This is the already documented sandbox limitation. Exact-head hosted CI must prove PostgreSQL 18 persistence, the five seeded role cards, addition of a sixth non-duplicate role, mobile single-column layout, accessibility and recovery before the increment can become CI-green.

## Current decision

```yaml
increment_status: TESTED_LOCAL
production_status: BLOCKED
release_decision: DENY_RELEASE
external_effects: NONE
next_gate: exact-head hosted CI and human product review
```
