# C3-TEAM-001 — Evidence-governed team builder and accountability map

- `workstream`: `WS-07`
- `status`: `IN_PROGRESS`
- `branch`: `agent/c3-team-001-accountability-builder`
- `base`: `agent/c3-candidate-001-evidence-workspace`

## Objective

Persist one campaign-scoped team workspace that makes roles, vacancies, availability, responsibility, onboarding, training and access recommendations explicit for non-technical campaign leadership. The workspace must never create application authority from a role label or recommendation.

## Bounded model

- organization template selected explicitly;
- role cards with purpose, responsibilities, status and optional principal assignment;
- work items with canonical RACI assignments;
- exactly one accountable role and at least one responsible role per work item;
- availability and weekly capacity assessment for filled roles;
- vacancies and hiring/onboarding requirements;
- training requirements and completion state;
- access recommendations with exact resource/action/scope/purpose but `authority_effect=NONE`;
- deterministic readiness, gaps and next action;
- optimistic versioning, exact replay, audit and internal no-effect outbox evidence.

## Exact authorization purposes

```text
Create campaign team workspace
Review campaign team workspace
Maintain campaign team workspace
```

## Acceptance criteria

1. A reversible migration adds one tenant/campaign team workspace under forced RLS.
2. Cross-tenant reads and writes fail under a `NOSUPERUSER NOBYPASSRLS` runtime role.
3. Every work item has exactly one `ACCOUNTABLE` role and at least one `RESPONSIBLE` role.
4. RACI references resolve only to role cards in the same workspace.
5. Filled roles require a principal and assessed availability; vacant roles cannot carry a principal.
6. Duplicate IDs, duplicate role assignments, oversized values and unknown fields are rejected.
7. Training and onboarding requirements distinguish missing, in-progress and complete work.
8. Access recommendations require exact action/resource/resource ID/purpose and never create roles or permission grants.
9. Readiness exposes vacancies, capacity gaps, RACI gaps, onboarding gaps, training gaps and access-review gaps without fabricating authority.
10. Create/read/update are exact-authorized before adapter invocation, versioned and idempotent where applicable.
11. Successful writes append atomic audit and internal outbox evidence with `external_effects=NONE` and `authority_effect=NONE`.
12. API errors are sanitized and adapter scope drift fails closed.
13. The frontend validates the complete projection and presents a read-only ES/EN organization roadmap.
14. No citizen contact, voter profiling, automatic grant, publication, spending, mobilization or external execution occurs.
15. Production remains `BLOCKED`.

## Prohibited actions

- treating role names as authorization;
- automatic creation of memberships, roles or grants;
- voter or persuadability scoring;
- hidden surveillance or sensitive political profiling;
- citizen contact, publication, spending or mobilization;
- live provider calls;
- merge, deployment, force-push or destructive persistent-data migration.

## Verification checkpoint

```yaml
implementation_state: VERIFIED_POSTGRESQL
implementation_commit: d18d89b
checkpoint_commit: 90775f35824a8a2252580be28b274ce345bedc41
branch_publication: PUBLISHED_SHA_VERIFIED
focused_tests: 47
full_suite: 514_passed_6_skipped
coverage_percent: 91.48
frontend_tests: 34
postgresql: PASS_TWICE_6_SELECTED
browser_wcag: PASS_ZERO_VIOLATIONS_ZERO_OVERFLOW
frontend_image: PASS_UID_10001
production_status: BLOCKED
external_effects: NONE
next_increment: C3-OPS-001
```

The checkpoint proves a durable accountability map, not a staffing decision or authorization system. Roles are descriptive records; access recommendations remain non-authoritative until a separate exact human authorization is granted.
