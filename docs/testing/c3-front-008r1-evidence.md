# C3-FRONT-008R1 evidence — QA command surface and local readiness repair

## Scope

This localized SHIP repair closes two human-QA defects without changing campaign domain authority:

1. a dynamically assigned frontend port rendered the CampaignOS 404 page for `/api/v1/ready`, making frontend and backend diagnostics ambiguous;
2. the overview repeated a dominant active-mission hero before the campaign path, while chapter navigation occupied too much of the task viewport.

The repair provides one command overview, compact workspace-first chapter routes, a sanitized same-origin readiness proxy, explicit functional-development URLs and an evaluator report for United States strategist use.

## Producer evidence

- removed the separate `CampaignExperienceHero` from the rendered shell;
- replaced the roadmap with current focus, persisted progress, expected outcome, compact stage shortcuts and a native full-path disclosure;
- replaced the full chapter navigator with a compact command bar and disclosed map;
- added `GET /api/v1/ready` to the frontend as a no-store JSON proxy to the configured backend readiness endpoint;
- added stable fail-closed readiness errors without raw URL, credential, tenant or connection details;
- updated `make functional-dev` output to distinguish frontend, browser readiness, backend API, backend readiness and Mailpit;
- updated ES/EN contracts, static tests and real browser evaluators;
- recorded the candidate-workspace United States strategist evaluation.

## Critic and localized repair evidence

### Accessible progress defect

The first dynamic Chromium review failed because the visual progress meter had no accessible name. The product implementation was repaired by binding `aria-label` to the localized progress label; the evaluator was not weakened. The equal-or-broader rerun passed keyboard, ES/EN, desktop/mobile, reduced motion, overflow and axe WCAG 2.2 AA gates.

### Nested Docker layer defect

The Compose functional runner stopped before CampaignOS startup while the sandbox Docker daemon registered an upstream image layer:

```text
failed to register layer: lchown /var/empty: permission denied
```

This was an isolated workstation runtime limitation, not a CampaignOS assertion failure. The equivalent host functional runner used an isolated local `*_test` database, applied every migration through `20260729_0012`, seeded exact grants and ran the complete PostgreSQL/API/browser journey. Hosted exact-head CI remains required for PostgreSQL 18 and container evidence.

### Persisted fixture rerun

A repeated host functional run initially observed the already-completed deterministic journey and failed the first-use navigation expectation. The isolated database was recreated and the complete fresh-state journey passed. This preserves the distinction between a clean first-use contract and persistence verification rather than weakening either assertion.

## Local verification

```text
make verify: PASS
Python: 753 passed / 11 controlled skips
coverage: 90.39%
Ruff: PASS
format: PASS
strict mypy: PASS (73 source files)
frontend: 28 files / 120 tests PASS
Next.js production build: PASS
npm audit: 0 vulnerabilities
Terraform: PASS_PLAN_ONLY_NO_APPLY
program truth: PASS / production BLOCKED
release gate: DENY_RELEASE
security/privacy policy: PASS
```

Dynamic production-build browser review:

```text
desktop ES/EN: PASS
mobile ES: PASS
command overview: PASS_CURRENT_FOCUS_PROGRESSIVE_PATH
chapter navigation: PASS_ROUTE_ISOLATION_LOCALE_PRESERVATION
keyboard disclosure: PASS
reduced motion: PASS_STATIC_EQUIVALENT
axe WCAG 2.2 AA: 0 violations
horizontal overflow: NONE
browser storage: EMPTY
unexpected outbound hosts: NONE
console/page errors: NONE
```

Isolated PostgreSQL/API/browser review:

```text
same-origin readiness: PASS_FRONTEND_PROXY_TO_BACKEND_READY
chapter history/back/forward isolation: PASS
role blueprints and template application: PASS
consultant role dossiers: PASS
role operations board and persistence: PASS
exact authorization controls: PASS
ES/EN/mobile/reduced motion: PASS
axe WCAG 2.2 AA: 0 violations
horizontal overflow: NONE
unexpected outbound hosts: NONE
external effects: NONE
```

## Candidate workspace evaluator

`docs/testing/c3-front-008r1-us-strategist-eval.md` records:

- `PASS_INTERNAL_RESEARCH_AND_DECISION_PREP`;
- `DENY_COMPLETE_US_CAMPAIGN_OPERATIONS_CLAIM`;
- `DENY_PRODUCTION_RELEASE`.

The current surface is useful for evidence-governed candidate research, contradictions, risk and human decision preparation. Jurisdiction-specific compliance, complete live editing, reviewer disposition, production identity/integrations and independent United States strategist/counsel acceptance remain separate gates.

## Remaining release gates

- exact-head hosted CampaignOS CI;
- exact-head runtime visual review;
- hosted PostgreSQL 18 functional journey and retained artifact evidence;
- review-thread closure;
- merge and successful post-merge CI;
- all separate production infrastructure, security, privacy, legal and human-production gates.

Production remains `BLOCKED`, release remains `DENY_RELEASE`, and external effects remain `NONE`.
