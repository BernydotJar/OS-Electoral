# C3-FRONT-015 iteration

## Goal

Make the existing Operations and War Room backend lifecycle completable through CampaignOS UI after Strategy reaches `DECIDED_INTERNAL`, with no autonomous execution or external political effect.

## Graph selection

C3-FRONT-014 is integrated and its reconciliation PR #179 is merged at `main@57f0c4649cb5525647850ccc2c75b84240460e0c`. GitHub confirms PR #179 exact-head CampaignOS CI #266 and Runtime Visual #238 succeeded, and post-merge `main@57f0c464…` CampaignOS CI #267 succeeded. This exact main SHA is the C3-FRONT-015 base. Operations/War Room remains the selected highest-priority existing-backend journey dead end.

## Approval

`USER_EXPLICIT_APPROVAL` from the ongoing product-completion instruction. Scope is internal roadmap/War Room UI over existing APIs, tests and evidence. Production, paid cloud resources, Firmes, citizen contact, targeting, persuasion, publication, spending and mobilization remain outside approval.

## Lifecycle

- Producer: complete locally. Existing Operations writes, progressive UI, exact capabilities, same-origin routes and War Room snapshot creation are implemented; the seed is 26 regular grants / 27 in the functional journey.
- Critic / Red Team: complete. Six findings are recorded and resolved: persisted-option decision integrity, the fresh-journey FILLED-owner dead end, stale-Strategy authoring visibility, Spanish snapshot localization, and hosted live-shell handling of backend `409 CAMPAIGN_NOT_READY` before Operations starts.
- Fixer: complete. The Team ownership repair is narrowly scoped to current-session self-coverage with server-owned `principal_id` and creates no membership, grant or additional access.
- Independent Verifier: complete for executable local gates. Frontend 55/250, optimized build, backend 865/13 at 90.03%, focused Operations/Team 99, read-only Chromium, Compose config, supply-chain, Gitleaks, Ruff/mypy/security/program/release/eval/safety all pass.
- Local runner blockers: the API-backed PostgreSQL/browser gate cannot start because the sandbox Docker daemon rejects image-layer `lchown`; Terraform plan-only cannot run because the Terraform CLI is absent. Neither is recorded as PASS. Exact-head hosted CI must execute these gates before merge.
- Persistent Evidence: `docs/testing/c3-front-015-evidence.md`, `program/validations/c3-front-015.json`, `progress/review_C3-FRONT-015.md`.
- Hosted exact-head: PR #182 first head `46c41bf25b4a26f71cd11da0ca440dcf1e4b5dcd` passed every hosted job except the API-backed functional onboarding step. Runtime Visual #239 passed. CampaignOS CI run `32002418220` exposed F5: the live shell treated backend `409 CAMPAIGN_NOT_READY` on a not-yet-started roadmap as a global failure. The Fixer classifies only that exact prerequisite code as Operations `NOT_STARTED`; unrelated 409 conflicts remain fail-closed. The next hosted head confirmed F5 was passed and reached the final Operations persistence checks, where F6 exposed a harness assertion mismatch: learning persisted as an editable input value, but the test searched for a text node. API evidence showed PATCH 200, snapshot POST 201 and latest snapshot GET 200. The verifier now checks the persisted input value before and after reload. Final exact-head revalidation is pending.
- Release Gate: review-branch publication is eligible; production remains `BLOCKED`; release remains `DENY_RELEASE`.
- External effects: `NONE`.
