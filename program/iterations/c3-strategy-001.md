# C3-STRATEGY-001 — Evidence-first Strategy and Decision Room

- `workstream`: `WS-09`
- `status`: `IN_PROGRESS`
- `branch`: `agent/c3-strategy-001-evidence-decision-room`
- `base`: `agent/c3-ops-001-roadmap-war-room@c81e4282813c0add0c3207f97066f127280e410e`

## Objective

Persist one campaign-scoped internal Strategy and Decision Room that separates verified evidence, inference and unknowns; records falsifiable hypotheses, comparable options, measurable objectives, contradictions and red-team findings; and permits only an exact, version-bound human decision receipt.

The increment does not produce public positioning, targeting, messages, content, contact, spending, mobilization or another external effect.

## Bounded model

- one strategy workspace per tenant/campaign;
- candidate and team version bindings;
- evidence inventory classified as `VERIFIED`, `INFERRED` or `UNKNOWN`;
- assumptions with explicit invalidation signals;
- hypotheses with evidence, assumptions and falsification criteria;
- at least two comparable strategic options before human decision readiness;
- measurable objectives with baseline, target, due date and accountable team role;
- contradiction records with explicit resolution state;
- red-team findings with severity and mitigation;
- append-only human decision receipts bound to the exact strategy version;
- deterministic readiness and next action;
- mandatory no-authority/no-external-effect limitations.

## Exact authorization purposes

```text
Create campaign strategy workspace
Review campaign strategy workspace
Maintain campaign strategy workspace
Approve internal campaign strategy option
```

Roles remain informational. Every operation must match principal, tenant, campaign, action, resource type, resource ID, purpose, validity and revocation state exactly.

## Acceptance criteria

1. Reversible migration adds strategy workspaces and append-only version-bound decision receipts under forced RLS.
2. Cross-tenant reads and writes fail under a `NOSUPERUSER NOBYPASSRLS` role.
3. Verified, inferred and unknown evidence remain distinguishable in storage, API and UI.
4. Verified evidence requires accepted provenance; unknown evidence cannot masquerade as sourced fact.
5. Hypotheses require evidence and explicit invalidation signals.
6. Options reference known hypotheses/evidence and expose benefits, risks and tradeoffs.
7. Objectives contain an accountable Team Builder role and measurable baseline/target/deadline fields.
8. Unknown references, duplicate IDs, cycles or prohibited profiling fields are rejected.
9. Open contradictions and open CRITICAL/HIGH red-team findings block decision readiness.
10. At least two complete options and one measurable objective are required for `READY_FOR_HUMAN_DECISION`.
11. A human decision is accepted only for the exact current version, selected option and exact approval receipt.
12. Updating strategy content invalidates current decision completeness while preserving historical receipts.
13. Create/read/update/decide are exact-authorized, audited, versioned and idempotent where applicable.
14. All successful writes append atomic audit and internal outbox evidence with `external_effects=NONE`.
15. API errors are sanitized and authorization failures occur before adapter invocation.
16. The frontend validates the complete projection and shows a plain-language read-only ES/EN Decision Room.
17. Voter-level scoring, persuadability, psychographic profiling, individual targeting and citizen contact fields are rejected.
18. Public positioning, content, publication, spending, mobilization and production remain blocked.

## Prohibited actions

- voter-level or persuadability scoring;
- individual political preference inference;
- psychographic or sensitive profiling;
- targeting/contact-list construction;
- autonomous strategy approval;
- public positioning or message generation;
- citizen contact, publication, spending or mobilization;
- live provider calls;
- merge, deployment, force-push or destructive persistent-data migration.
