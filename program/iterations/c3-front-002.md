# C3-FRONT-002 — Functional campaign onboarding journey

- `branch`: `agent/c3-front-002-functional-onboarding`
- `base`: `agent/c3-sec-001-security-privacy-baseline@e0b4b5df711f671e8f6a1f711a0a3beff39cf173`
- `status`: `IN_PROGRESS`
- `production_status`: `BLOCKED`
- `external_effects`: `NONE`

## User problem

The current shell is a read-only evidence projection. Navigation items are mostly anchors, Administration has no destination, and the development demo cannot create or maintain a campaign. A non-technical campaign operator cannot complete a useful task.

## Bounded objective

Deliver the first authenticated, API-backed vertical journey:

1. select an existing campaign from the campaigns available to the current tenant;
2. start or resume guided intake when an exact create grant permits it;
3. maintain the intake through an accessible form using `If-Match` and `Idempotency-Key`;
4. refresh the server projection and show clear success, conflict, denial and dependency states;
5. replace the oversized anchor list with compact responsive navigation organized around implemented journeys.

Campaign creation is intentionally deferred until the creation lifecycle can grant or request access through a separate human-authorized workflow. This increment never infers post-create authority.

## Mandatory boundaries

- role labels are never permissions;
- no strategy, public positioning or human approval is inferred;
- no voter profiling, individual targeting or citizen contact;
- no autonomous task execution;
- no publication, spending, mobilization or external effect;
- demo mode remains read-only and is visibly identified as such;
- live mutations require server-owned exact grants and an authenticated bearer session.

## Acceptance criteria

1. No enabled navigation item points to a missing section.
2. Campaign switching persists only the selected campaign cookie and reloads server data.
3. No campaign-creation control is rendered until a separate access lifecycle exists.
4. Guided intake start/update use exact server grants, current version and stable idempotency keys.
5. Update conflicts, validation errors, authorization denials and dependency failures are distinct and accessible.
6. Forms are keyboard operable, labeled, reflow at mobile widths and do not depend on color.
7. ES/EN content is complete.
8. Demo mode contains no active mutation control.
9. Frontend contract tests, build, browser review and backend regression pass.
10. A live PostgreSQL/API/browser E2E proves start, update and persistence after reload.
11. Production remains `BLOCKED` and external effects remain `NONE`.
