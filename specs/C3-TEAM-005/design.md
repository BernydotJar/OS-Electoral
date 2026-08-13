# C3-TEAM-005 Design

## Principle

Finish the existing Team readiness contract rather than weakening the journey gate. A human review may legitimately conclude that there are no additional training requirements or access recommendations; that reviewed-empty state must be persisted explicitly instead of inferred from `null`.

## Interaction model

The Team chapter gains a compact `Cerrar preparación del equipo` area driven by the two incomplete checks:

1. `training` — edit existing requirements, add a requirement, or record an explicit reviewed-empty list;
2. `access_review` — edit existing campaign-scoped recommendations, add a recommendation, or record an explicit reviewed-empty list.

All forms are progressive disclosures and remain subordinate to the existing role/operations workspace.

## Training requirements

Each record keeps its stable ID and contains existing role ID, title, description and progress status. New IDs are generated server-side by the same-origin UI route. The UI never treats Training Academy completion as an implicit Team requirement completion; these remain separate domain records.

## Access recommendations

Each record keeps its stable ID and contains an existing role ID, action, resource type, purpose and review status. C3-TEAM-005 creates campaign-scoped recommendations only (`workspace_id=null`, `resource_id=current campaign`). A recommendation is advisory and `authority_effect` remains `NONE`; no role, membership or grant is created.

## Authorization and persistence

The existing exact Team grant is reused:

- `update` / `team_workspace` / `Maintain campaign team workspace`.

Same-origin routes load the current workspace, verify scope/version, replace only one supporting collection, and call the existing typed API client with `If-Match` and idempotency.

## Verification

- parser/route/component/adversarial tests;
- API-backed browser journey proving a real Team workspace reaches `READY_FOR_HUMAN_REVIEW`;
- existing Team backend contract/API/PostgreSQL tests;
- read-only mutation absence, ES/EN, mobile, keyboard, reduced motion, overflow and axe;
- repository, supply-chain, Terraform plan-only, security, program and release-readiness gates.
