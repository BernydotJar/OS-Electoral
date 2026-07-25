# C3-FRONT-005 — Parallel campaign team organization workflow

- `branch`: `agent/c3-front-005-team-organization-workflow`
- `base`: `agent/c3-front-004-candidate-evidence-workflow@2a1aecaf08aa7c568dfc9b6fd3ab82852c141513`
- `status`: `CI_GREEN`
- `production_status`: `BLOCKED`
- `external_effects`: `NONE`

## User problem

CampaignOS presents team organization as a later roadmap step, but political campaigns need to begin assembling functions while candidate research is still underway. The backend already owns a governed team workspace, yet the live frontend cannot create a structure or document a vacancy.

## Bounded objective

1. keep candidate evidence as the primary mission while exposing team preparation as explicitly parallel work;
2. create the team workspace through an exact campaign-scoped grant;
3. let an authorized user choose a lean, full or custom organization template;
4. document one vacant campaign function with area, purpose, responsibilities and vacancy plan;
5. preserve idempotency, optimistic concurrency, tenant/campaign scope and duplicate-role rejection;
6. keep people assignment, memberships, permissions, strategy and external execution blocked.

## File ownership

- `task_id`: `C3-FRONT-005`
- `workstream_id`: `WS-05/WS-06/WS-07`
- `writer`: frontend implementation role
- `allowed_paths`: frontend application, frontend runtime reviews, deterministic local-development seed, seed regression test, product/testing/program documentation
- `read_only_paths`: backend team domain, migrations, production authorization policy
- `write_lock`: one writer per modified file

## Acceptance criteria

1. Team preparation is available only after a candidate dossier exists and exact team grants are present.
2. Candidate evidence remains the current phase until its approval gate is complete.
3. Strategy remains locked while candidate/team prerequisites are incomplete.
4. A role created from the UI is always `VACANT`, has no principal and has no capacity or permission effect.
5. Updates use `If-Match` and `Idempotency-Key`; duplicate title/area pairs and stale versions fail closed.
6. Demo remains read-only; live ES/EN/mobile journeys pass WCAG 2.2 AA automation with no overflow.
7. Production remains `BLOCKED`; no hiring, membership, permission, publication, citizen contact, spending, mobilization or deployment occurs.

## Validation record

- RED: missing parallel journey semantics, team parser, capabilities, API mutations and local exact grants.
- GREEN: 28 focused frontend tests; 83 full frontend tests; two local seed tests.
- lint, strict TypeScript, production build and npm audit pass; npm reports zero vulnerabilities.
- demo browser: ES/EN/mobile, keyboard, reduced motion, zero axe violations, no overflow, no external hosts.
- live browser: foundation, candidate dossier, evidence, team map, vacant function, reload, ES/EN/mobile, zero axe violations and no external effects.
- PostgreSQL 15 ephemeral UTF-8 cluster migrated through revision `20260721_0011`; local operator seeded with eleven exact bounded grants.

## Product boundaries

This increment documents organizational intent. It does not assign a person, invite a user, create membership, grant access, complete RACI, assess capacity, approve hiring, activate strategy or execute campaign work. Those remain separate governed workflows.


## Exact-head hosted closure

- Draft PR `#120` published at `ecf1168c4ee9c6257596cccf4babbb7c040e6146`.
- CampaignOS CI `30167135593` and Runtime Visual Review `30167135592` succeeded.
- Compose, PostgreSQL 18, backup/restore, API-backed browser, CodeQL, Terraform, secrets, dependencies and supply-chain checks passed.
- Status is `CI_GREEN`; human product review and merge remain separate gates.
