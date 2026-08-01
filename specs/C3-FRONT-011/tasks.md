# C3-FRONT-011 — Tasks

## Producer

- reconcile C3-PERF-001 merge and activate this increment;
- write Campol-consultant functional evaluation;
- add exact campaign-create capability and typed UI route;
- implement single-view candidate profile with inline action/evidence;
- implement reusable chapter orientation across all chapters;
- compact team governance metadata;
- simplify ES/EN copy and add tests/evaluators.

## Critic / red team

- verify campaign creation cannot bypass exact grant, same-origin, idempotency or backend authorization;
- verify created draft does not auto-select or imply access;
- verify evidence/add-source remains keyboard reachable;
- verify orientation does not duplicate or dominate compact chrome;
- verify transcript evaluation excludes individual voter profiling/targeting;
- verify compact metadata remains auditable.

## Fixer

Repair every severity HIGH/MEDIUM finding and any accessibility, mobile, authorization or state-loss defect before publication.

## Independent verifier

- focused unit/route tests;
- full frontend tests, lint, typecheck and production build;
- dynamic Chromium ES/EN desktop/mobile/keyboard/reduced motion;
- axe WCAG 2.2 AA;
- complete `make verify`;
- exact-head hosted CI and visual review.

## Release gate

Merge only after exact-head checks, zero unresolved review threads and existing user merge authorization. Production remains blocked and external effects remain none.
