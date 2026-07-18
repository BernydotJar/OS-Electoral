# Campaign Workspaces — operator guide

## Validate and run

Run the complete domain contract suite:

```bash
python3 scripts/campaign/validate_c2_plat_001.py
```

Run Antigua's research-only cycle:

```bash
python3 scripts/campaign/run_cycle.py \
  --workspace campaigns/antigua-guatemala/workspace.json \
  --request fixtures/cycle-requests/antigua-evidence-priority.json \
  --output artifacts/cycle-runs/antigua-evidence-priority-result.json
```

Run the portable synthetic tenant with the same engine:

```bash
python3 scripts/campaign/run_cycle.py \
  --workspace fixtures/workspaces/rio-claro-demo.json \
  --request fixtures/cycle-requests/rio-claro-research-gap.json \
  --output artifacts/cycle-runs/rio-claro-research-gap-result.json
```

The CLI exits `2` and writes no success output when validation fails. All paths must be repository-relative, remain inside the checkout, contain no `..`, and traverse no symbolic links. Inputs must be regular JSON files; output cannot overwrite an input.

## Create or extend a workspace

1. Copy the synthetic fixture, never Antigua-specific core code.
2. Replace tenant, campaign and workspace IDs everywhere; keep namespaced stable IDs.
3. Configure all eight stations and seven gates.
4. Add evidence with an explicit classification and repository-safe provenance.
5. Add decisions separately from approvals. Every approval must identify a human actor, a non-empty role and one or more canonical gate IDs in `supports_gates`.
6. Declare gate signals as `{value, source_refs}`. Every true signal source must be local, enabling, and list that exact name in `supports_signals`.
7. Add one agent assignment for each station a request may route to.
8. Validate before committing.

Evidence sources may support a decision; recommendations are never evidence. Do not place personal paths, PII, voter-level data or credentials in fixtures.

### Approval binding

Human approval is scoped to the strategic gate it explicitly supports. A record such as:

```json
{
  "actor_type": "HUMAN",
  "role": "campaign_chief",
  "status": "APPROVED",
  "supports_gates": ["gate:field-mobilization"]
}
```

can satisfy the `campaign_chief` requirement only for `gate:field-mobilization`. It cannot substitute for paid media, narrative change or another gate requiring the same role. Missing, empty or unknown `supports_gates` values are invalid and fail closed.

## Interpret gate results

- `CLOSED`: one or more prerequisites or gate-scoped human approvals are missing.
- `ELIGIBLE_FOR_HUMAN_APPROVAL`: evidence-backed prerequisites and any required gate-scoped reviews exist, but a human still decides. It is not `APPROVED`, `AUTHORIZED`, `PUBLISHED`, `FUNDED` or `ACTIVATED`.

Unknown, missing, cross-scope, contradictory or semantically unrelated sources and approvals fail closed. Error messages identify the failed invariant without logging raw sensitive documents.

## Add cycle types

Add the artifact enum to both the request schema and core allowlist, define deterministic station routing, configure a matching agent, and add tests for one valid, one malformed and one authority-injection case. The pure core must continue to return exactly one draft artifact with no external side effects.

## Tenant isolation checklist

- unique tenant/campaign/workspace IDs;
- ownership repeated on every domain object;
- every reference resolves inside the validated graph;
- every human approval is bound to explicit canonical gates;
- no display name or role alone is used as an authorization key;
- cross-tenant, cross-campaign, cross-workspace and cross-purpose approval adversarial tests pass;
- API authentication remains a future boundary and is not implied by this local model.
