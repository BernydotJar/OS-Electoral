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
increment_status: CI_GREEN
production_status: BLOCKED
release_decision: DENY_RELEASE
external_effects: NONE
next_gate: human product review and stacked merge review
```


## Hosted exact-head closure

```yaml
implementation_head: 7735b533b5ebc43d829d881090798fe1b1605295
pull_request: 122
campaignos_ci: 30176654019
runtime_visual_review: 30176653983
quality_job: 89726416944
frontend_api_postgresql_job: 89726416949
visual_job: 89726416707
recovery_job: 89726416935
status: SUCCESS
```

Artifacts retained from the implementation head:

- frontend review `8624422291`, digest `sha256:2cd287e74b1ccad095edccf264faf194202629c0260fff56ab09190637d86b23`;
- PostgreSQL recovery `8624400644`, digest `sha256:7e2090cd09ad992490450efd105f1515fabbbd2363518231992c7f94bde97934`;
- supply chain `8624398004`, digest `sha256:cdadd98387b05ae802ba896fccdc9751c9d4d2fc67022e11e19147a28bd14890`;
- visual review `8624406463`, digest `sha256:cb070dca535e4e2eac18f468b22c432c41b04172eec16964e7a8b6e59b64d967`;
- Gitleaks SARIF `8624397523`, digest `sha256:795df7efb042b02bc723384929c62de2c8fd4a7d1eea99a4d26acc9c4d1c7f89`.
