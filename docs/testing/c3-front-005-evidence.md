# C3-FRONT-005 evidence — parallel team organization

Date: 2026-07-25
Branch: `agent/c3-front-005-team-organization-workflow`
Base: `agent/c3-front-004-candidate-evidence-workflow@2a1aecaf08aa7c568dfc9b6fd3ab82852c141513`

## Implemented behavior

- Added an explicit parallel-preparation state to the campaign journey without skipping the candidate evidence gate.
- Added exact-grant team workspace creation and role-card update routes.
- Added lean, full and custom team templates.
- Added one-function-at-a-time vacancy documentation with purpose, responsibilities and a human coverage plan.
- Added duplicate role rejection, optimistic versioning, idempotency and tenant/campaign reconciliation.
- Extended only the deterministic local-development operator seed from eight to eleven exact bounded grants.
- Kept demo mode read-only and all external effects disabled.

## TDD evidence

```text
RED: parallel team stage remained locked
RED: team form parser missing
RED: exact team capabilities missing
RED: team API mutations missing
RED: local seed expected 11 grants but contained 8
GREEN: 28 focused frontend tests
GREEN: local seed 2 tests
GREEN: 83 total frontend tests
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
local seed: exact_grants=11
journey: campaign_foundation_candidate_evidence_and_team_map PASS
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

- A function is created vacant and cannot smuggle a principal, capacity or permission.
- Organization labels remain separate from application grants.
- Team preparation does not advance the candidate evidence gate or unlock strategy.
- Production remains `BLOCKED`; release remains `DENY_RELEASE`.


## Exact-head hosted CI

```text
implementation head: ecf1168c4ee9c6257596cccf4babbb7c040e6146
draft PR: 120 (stacked on PR 119 branch)
CampaignOS CI: 30167135593 SUCCESS
Runtime Visual Review: 30167135592 SUCCESS
displayed checks: 12/12 PASS
Compose stack E2E: PASS
PostgreSQL migrations/RLS: PASS
PostgreSQL backup/restore: PASS
API-backed browser journey: PASS
CodeQL/secrets/dependencies/Terraform/SBOM: PASS
```

Retained artifacts:

- frontend review `8621911493`, `sha256:8824514e50157cfdb97d04bac350b1b1714fe2e704a743a3d325075d89e75c01`;
- PostgreSQL recovery `8621892887`, `sha256:90a21611ce4285b8b426d724be93ef5d412adc6ec777f03a4e3f186b9932989c`;
- supply chain `8621889767`, `sha256:d756bbdd53c0c3eb79754ef5472e5195cc3c1b004c5b0881a4fc6888c58ff534`;
- visual review `8621898516`, `sha256:dfcdf2633734e36825142e5035774307adc95eca78453775f445c222527acbf3`;
- Gitleaks SARIF `8621890021`, `sha256:f58cfee4390d28a03a13813a10f79036b6ca7bb6c7557cb8abaeac84b1b89135`.

The implementation is CI-green and reviewable. It is not merged, deployed or production-ready.
