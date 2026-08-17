# C3-FRONT-015 Design

## Existing contracts first

Use the merged `campaign_operations` API and Operations contracts without introducing a second roadmap model. Add typed frontend mutation evidence parsers and API client methods for roadmap create/update and War Room snapshot creation.

## Authorization and prerequisites

Derive exact Operations capabilities from server-projected grants. Same-origin routes must fail closed unless Strategy exists at `DECIDED_INTERNAL`; UI role labels never authorize writes. Because the existing Operations service requires at least one filled Team owner, expose a narrowly bounded current-session self-coverage action over the existing Team update contract: the server supplies the authenticated `principal_id`, requires exact Team read/update grants, positive declared capacity and explicit onboarding confirmation, and creates no membership or permission. Preserve backend idempotency and optimistic concurrency.

## Authoring model

Extend the current read-only Operations workspace with progressive forms for phases, workstreams, milestones, tasks/dependencies, blockers, explicit human decisions, follow-ups and learning notes. Select Team owner roles and cross-record references from existing projections rather than accepting free-form identifiers. Preserve unrelated collections on bounded updates.

## War Room

Expose snapshot creation only from a current roadmap projection and exact snapshot-create authority. Render backend-computed readiness, blocked work and critical path as read models; do not infer or execute tasks client-side.

## Safety

All records are internal operational artifacts. No task is executed by the application, no citizen is contacted, no political audience is targeted or scored, and no publication, spending, mobilization, grant creation, Firmes sync or production effect occurs. Read-only mode has no mutation forms.

## Verification

Add parser/client/route/component adversarial tests; extend the PostgreSQL/API-backed onboarding journey from Strategy `DECIDED_INTERNAL` through roadmap persistence and a War Room snapshot; then run the complete Graph Harness lifecycle and release gates.
