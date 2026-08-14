# C3-FRONT-015 iteration

## Goal

Make the existing Operations and War Room backend lifecycle completable through CampaignOS UI after Strategy reaches `DECIDED_INTERNAL`, with no autonomous execution or external political effect.

## Graph selection

C3-FRONT-014 is integrated at `main@a2d7aa81455358eb0244b51556ffe3a192455c06`. The post-merge functional onboarding job is green; its only failed gate is stale Graph Harness merge reconciliation, repaired by the current branch. Operations/War Room is the highest-priority remaining existing-backend journey dead end.

## Approval

`USER_EXPLICIT_APPROVAL` from the ongoing product-completion instruction. Scope is internal roadmap/War Room UI over existing APIs, tests and evidence. Production, paid cloud resources, Firmes, citizen contact, targeting, persuasion, publication, spending and mobilization remain outside approval.

## Lifecycle

- Producer: active after reconciliation merge and post-merge green gate.
- Critic / Red Team: pending.
- Fixer: pending.
- Independent Verifier: pending.
- Release Gate: production remains `BLOCKED`; release remains `DENY_RELEASE`.
- External effects: `NONE`.
