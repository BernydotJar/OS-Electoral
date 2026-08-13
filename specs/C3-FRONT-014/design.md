# C3-FRONT-014 Design

## Principle

Expose the existing evidence-first strategy domain through server-rendered, same-origin, exact-authorized controls. CampaignOS may organize evidence and alternatives; it must not choose a political strategy for the operator.

## Interaction model

The Strategy chapter keeps its current read model and adds a progressive `Construir estrategia` workspace. The editors are ordered by backend readiness dependencies:

1. workspace title/create;
2. evidence register;
3. assumptions;
4. hypotheses;
5. comparable options;
6. measurable objectives;
7. contradictions review;
8. red-team review;
9. human decision.

Each editor replaces only its bounded collection through the existing PATCH contract while preserving all other collections. New record IDs are generated server-side by same-origin UI routes; existing IDs remain stable when edited.

## Evidence and references

The browser renders selectable references from already persisted strategy records. The server-side form parser validates UUID shape, bounded list sizes and basic provenance before calling the backend. The backend remains authoritative for referential integrity and decision readiness.

Verified evidence is submitted only with `ACCEPTED` status plus source reference, authority and jurisdiction. Unknown evidence is never presented as verified and blocks decision readiness by existing domain rule.

## Exact authorization

Frontend capability projection adds the existing grants:

- `create` / `strategy_workspace` / `Create campaign strategy workspace`;
- `read` / `strategy_workspace` / `Review campaign strategy workspace`;
- `update` / `strategy_workspace` / `Maintain campaign strategy workspace`;
- `approve` / `strategy_workspace` / `Approve internal campaign strategy option`.

Role labels never grant mutation authority. Same-origin routes preserve idempotency and `If-Match` optimistic concurrency.

## Human decision

The decision editor is rendered only when the backend reports `READY_FOR_HUMAN_DECISION` and the exact approve grant exists. The operator selects one existing option and one existing team role, then records a reason. The API creates the append-only decision receipt; the UI does not synthesize approval IDs or infer authority.

## Local development

The deterministic local operator seed gains the already-defined four strategy grants so the complete authorized lifecycle can be exercised in the repository's isolated PostgreSQL/API/browser harness. Production authorization policy is unchanged.

## Safety

- `authority_effect` stays `NONE`;
- `external_effects` stays `NONE`;
- decision status `DECIDED_INTERNAL` is not public positioning or publication authority;
- no individual voter records, persuasion, targeting, citizen contact, spending or mobilization are added;
- Firmes and production remain separately gated.

## Verification

- capability/form/parser/API-client/same-origin route/component tests;
- stale version, wrong grant, unknown reference and premature decision red-team cases;
- existing backend strategy contract/API/PostgreSQL tests;
- API-backed Chromium lifecycle from candidate/team prerequisites through `DECIDED_INTERNAL`;
- read-only mutation absence and visible-word guard;
- ES/EN, mobile, keyboard, reduced motion, overflow and axe;
- full repository, supply-chain, Terraform plan-only, security, program and release-readiness gates.
