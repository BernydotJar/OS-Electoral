# C2-PLAT-001 — Design

## Boundaries

`core/campaign_workspace.py` is a standard-library, persistence-free domain boundary. JSON files are adapters/configuration. `scripts/campaign/run_cycle.py` is the explicit file adapter. Static frontend data remains unchanged.

```text
workspace JSON + cycle request JSON
  -> strict structure and scope validation
  -> semantic signal/source validation
  -> deterministic gate evaluation
  -> deterministic station routing
  -> one governed draft artifact result
```

## Domain and tenancy

Every aggregate carries tenant, campaign and workspace ownership. IDs are stable namespaced identifiers, globally unique inside a workspace, and display names never authorize access. All `*_ref`/`*_refs` resolve in the same validated object graph. The synthetic tenant proves configuration portability, not production authentication; authorization remains a future API concern.

## Authority model

Recommendations, decisions, approvals and execution are distinct. Only stored approvals with `actor_type=HUMAN` can satisfy approval prerequisites. Requests reject unexpected authority fields. Results are drafts, have `external_effect=NONE`, and do not persist.

## Gates

Seven canonical rules are declarative and fail closed. A true signal must cite one or more local objects whose state is enabling and whose explicit `supports_signals` includes that exact semantic signal. This prevents a generic approved decision from substituting for an approved segment or evidence review. `ELIGIBLE_FOR_HUMAN_APPROVAL` is the strongest engine result.

## Loop and routing

Artifact type deterministically routes to Electoral Research or Tracking/Risks. Exactly one assigned agent must exist at that station. The core deep-copies and compares the input, limits summary lines to five, emits exactly one primary artifact summary, exposes unknowns and gates, and returns canonical JSON without time-dependent values.

## Error and security model

Malformed version, fields, enums, IDs, ownership, references, evidence class, station/gate sets, personal paths, traversal strings, contradictory decisions and unsupported signal sources raise `WorkspaceValidationError`. The CLI writes only after successful evaluation, refuses input overwrite and symlink inputs/outputs. It is a local adapter, not an OS sandbox.

## Tradeoffs and rejected alternatives

- Python stdlib matches repository policy and avoids dependency supply-chain cost.
- JSON Schema documents the wire shape; domain invariants remain executable Python because JSON Schema alone cannot express scoped reference ownership.
- No database, web API, AI model, frontend rewrite or generative decision engine is introduced.
- Antigua-specific output branching is rejected; all variation is fixture/request configuration.

## Future API compatibility

The pure functions accept/return JSON-compatible dictionaries and can back REST, GraphQL, CLI, batch eval or frontend read adapters. Production authentication, persistence, concurrency and billing are explicitly outside this increment.
