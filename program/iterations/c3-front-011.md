# C3-FRONT-011 — Clear candidate guidance and governed campaign entry

- `branch`: `agent/c3-front-011-candidate-guidance-and-campaign-entry`
- `base`: `main@1b8c9be5f2ba5dcdb522e0b7cdba0687af993297`
- `status`: `REVIEWED_LOCAL`
- `production_status`: `BLOCKED`
- `release_decision`: `DENY_RELEASE`
- `external_effects`: `NONE`

## User problem

The candidate chapter showed three equal destinations even though the user wanted one understandable candidate profile. Chapter position was too subtle, the campaign selector lacked a first-class way to start another candidacy, and training/access/audit metadata competed with daily work.

The user also supplied a Campol podcast transcript and asked for an evaluation as those consultants. The source supports a staged workflow—research, strategy, organization, communication and measurement—but also contains person-level voter-database practices that CampaignOS explicitly excludes.

## Bounded objective

1. make `Perfil y riesgos` the only primary candidate view;
2. integrate the next action and evidence into that profile;
3. explain current chapter, purpose, status and next human action on all five routes;
4. expose exact-grant creation of an internal candidacy draft through the existing API;
5. preserve idempotency, tenant scope, backend authorization and no automatic context change;
6. compact team governance metadata while retaining auditability;
7. simplify Spanish and English language without weakening safety boundaries.

## Acceptance criteria

1. No candidate top-level tablist remains.
2. Profile and risks are visible before action guidance; evidence remains keyboard reachable.
3. Every chapter shows `Capítulo n/5`, its outcome and its next human action.
4. Campaign creation appears only with the exact tenant collection grant.
5. One browser-submitted UUID idempotency key binds the route, slug and backend operation.
6. The response must be a version-one `DRAFT` for the expected tenant.
7. Creation changes no active-campaign cookie and grants no access.
8. An authorized empty tenant can create the first draft; unauthorized empty tenants remain closed.
9. Training, access recommendations and audit metadata remain available in a closed disclosure.
10. Full repository, browser, accessibility and hosted functional gates pass before merge.

## Critic repairs

- moved idempotency generation from POST handling to the rendered form so retries cannot create a second operation;
- opened a governed first-draft path for authorized empty tenants;
- reordered candidate content so profile precedes actions;
- repaired campaign-context composition and field grouping;
- updated stale browser contracts from tabs to a single profile/disclosure model;
- expanded the slug suffix from 8 to 12 hexadecimal characters;
- added an opt-in E2E-only exact tenant grant and browser assertions for DRAFT creation without broadening the default local operator;
- removed the final English functional-browser selector for the retired candidate tabs.

Implementation commit: `8b835e1a64095e92136d5375026075581c8fe02a`.

## Local validation

- `make verify`: PASS;
- Python: 791 passed, 12 skipped, 90.22% coverage;
- frontend: 33 files / 144 tests PASS;
- ESLint, TypeScript, Next.js build and npm audit: PASS;
- Chromium desktop ES/EN and mobile ES: PASS;
- keyboard, reduced motion, route isolation and locale preservation: PASS;
- axe WCAG 2.2 AA: zero violations;
- horizontal overflow, browser storage and unexpected outbound hosts: none;
- Terraform: plan/test only; no apply;
- production: `BLOCKED`; release: `DENY_RELEASE`.

## Environment limitation

The local PostgreSQL/API/browser functional runner failed before product startup while Docker registered the PostgreSQL 18 layer: `lchown /var/empty: permission denied`. No application assertion ran. Exact-head hosted CI remains the authoritative functional gate.

## Next gate

Publish the reviewed branch, require exact-head hosted PostgreSQL 18/API/browser and runtime visual checks, repair every review finding, then merge only with all required checks green and zero unresolved conversations.
