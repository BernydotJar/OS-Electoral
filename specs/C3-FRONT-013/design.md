# C3-FRONT-013 Design

## Principle

Finish the existing candidate domain through the existing exact-authorized API. Do not duplicate candidate business rules in the browser and do not create a new political-data model.

## Interaction model

The candidate chapter remains “Perfil y riesgos”. Beneath the current profile it exposes a progressive “Completar expediente” work area. Each incomplete check points to one editor:

1. identity claim;
2. biography claim;
3. purpose claim;
4. values register;
5. attributes register;
6. contradictions register;
7. development goals register;
8. reputation risks register;
9. internal section approvals.

Each editor submits one bounded replacement for its section through a same-origin UI route. Existing records outside that section are untouched. IDs are generated server-side by the UI route when a new record is created; existing record IDs remain stable when editing.

## Evidence linking

Claim/record editors render checkboxes for existing candidate evidence IDs. Verified claims are only offered when their classification and referenced evidence can satisfy the backend's independent-evidence invariant. Perception evidence can be linked to attribute perception refs but is never treated as verified independent support.

## Authorization

Frontend capability projection adds `canApprove` for the existing exact grant:

- action `approve`;
- resource `candidate_workspace` scoped to the current campaign;
- purpose `Approve candidate evidence section`.

The browser never decides authorization. Same-origin routes call the existing backend through the server-only client and preserve optimistic concurrency plus idempotency.

## Approval lifecycle

Candidate updates increment the workspace version and make previous approvals stale by existing domain rule. The UI warns that saving evidence or claims requires current-version approvals to be collected again. Approval does not increment the candidate workspace version and remains internal-only.

## Local development

The deterministic local operator seed gains the already-defined candidate `approve` grant so the full authorized lifecycle can be verified in the API-backed browser harness. This changes only local development/test seed authority; production authorization policy is unchanged.

## Safety

- external effects remain `NONE`;
- candidate public-use status remains `BLOCKED`;
- no public positioning approval is created;
- no voter-level records, political targeting, persuasion or contact action is introduced.

## Verification

- form parser/route/capability/component tests;
- existing backend candidate contract/API/PostgreSQL tests;
- ESLint, TypeScript, Vitest and production build;
- API-backed Chromium lifecycle proving every candidate check can become complete and approvals reach `INTERNALLY_APPROVED`;
- read-only UI mutation absence and visible-word check;
- mobile, keyboard, reduced-motion, overflow and axe checks;
- full `make verify` and Graph Harness program validators.
