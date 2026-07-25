# C3-FRONT-004 evidence — adaptive entry and candidate evidence

Date: 2026-07-25
Branch: `agent/c3-front-004-candidate-evidence-workflow`
Base: `agent/c3-front-003-campaign-launch-roadmap@ff7b10fed951f176609c43ad83b501f83d92b810`

## Implemented behavior

- Added `FIRST_USE`, `ACTIVE` and `COMPLETE` campaign-entry modes derived from persisted journey state.
- Added an owned, CSS-based cinematic atmosphere with no third-party media or runtime request.
- Added exact-grant candidate dossier creation and evidence update routes.
- Added HTTPS-only source validation, provenance fields, optimistic versioning, idempotency and duplicate-source rejection.
- Added development-only exact candidate grants to the deterministic local operator seed.
- Removed raw candidate reason codes from primary UI copy.
- Kept demo mode read-only and all external effects disabled.

## TDD evidence

```text
RED: campaign experience module missing
RED: candidate form parser missing
RED: candidate exact capabilities missing
RED: candidate API mutations missing
RED: local seed expected 8 grants but contained 5
GREEN: 21 focused frontend tests
GREEN: local seed 2 tests
GREEN: 76 total frontend tests
```

## Demo browser evidence

```text
status: PASS
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
```

## Persistent functional evidence

```text
PostgreSQL: 15.18 local ephemeral UTF-8 cluster
migrations: 20260719_0001 through 20260721_0011 PASS
local seed: exact_grants=8
journey: campaign_foundation_candidate_dossier_and_evidence PASS
persistence_after_reload: PASS
exact_authorization_controls: PASS
desktop_spanish: PASS
desktop_english: PASS
mobile_spanish: PASS
wcag_2_2_aa: PASS_ZERO_AXE_VIOLATIONS
horizontal_overflow: NONE
browser_storage: EMPTY
unexpected_outbound_hosts: []
console_errors: []
page_errors: []
external_effects: NONE
```

Generated screenshots and logs were inspected by the browser gates and then removed from the Git worktree. Exact-head PostgreSQL 18, Compose, CodeQL, recovery and supply-chain evidence remain required from hosted CI.

## Safety findings

- Candidate creation is not shown before guided intake reaches `READY_FOR_RESEARCH`.
- Role labels never become permissions; each operation matches action, resource, campaign, purpose and scope.
- Evidence status is accepted into the internal dossier, not declared verified.
- Source registration does not authorize strategy, public claims, publication, citizen contact, targeting, spending or mobilization.
- Production remains `BLOCKED`; release remains `DENY_RELEASE`.
