# Graph Harness SDLC runtime mapping for CampaignOS

Status: **ACTIVE AS AN EXTERNAL EXECUTION RUNTIME; PRODUCT GRAPH REMAINS CANONICAL**

Framework:

- repository: `https://github.com/BernydotJar/Graph-harness-sdlc`
- pinned revision for this reconciliation: `0eb0d5fe09e3b1ecaf561b4a1cc9b32510480a26`
- mode: `SHIP`

CampaignOS does not copy or redefine Graph Harness framework concepts. The reusable framework remains in its own repository. CampaignOS keeps its existing typed product state as the canonical target-specific graph:

1. `architecture/program-state.json`
2. `program/task-graph.yaml`
3. `program/task-ledger.yaml`
4. `program/program-state.json`
5. feature specs and evidence

`program/graph-harness-execution.json` is a validated projection. It is not an independent roadmap and may not override canonical product state.

The program-state validator also reconciles delivery state against the reachable first-parent Git history. For every task that records a direct delivery PR (`pull_request`, `draft_pr`, or `hosted_verification.pull_request`), a standard squash subject ending in `(#N)` or merge subject `Merge pull request #N` requires the ledger to say `MERGED_TO_MAIN`. Dependency/base PR references are intentionally excluded. This catches stale post-merge task state without requiring a manifest to contain the SHA of the commit that is currently validating itself.

## Lifecycle mapping

| Graph Harness lifecycle | CampaignOS projection |
|---|---|
| `pending` | candidate feature identified but no complete spec |
| `spec_ready` | complete requirements/design/tasks; no roadmap execution node yet |
| `approved` / `ready` | roadmap `EXECUTABLE_NEXT`; ledger `READY` |
| `running` | roadmap `ACTIVE`; ledger `IN_PROGRESS` |
| `review` | implementation/evidence complete; review artifact pending closure |
| `done` | `MERGED_TO_MAIN` with exact post-merge evidence |
| `blocked` | `BLOCKED_BY_DEPENDENCY` or `HUMAN_BLOCKED` with owner and next valid command |

Exactly one feature may be active across approved, ready, running, or review. A `spec_ready` feature remains outside the executable product roadmap until a human approval receipt is recorded.

## Scheduler rule

1. validate canonical state;
2. repair contradictions locally before selecting product work;
3. exclude nodes with unmet dependencies, policy gates, external credentials, spending, or production authority;
4. rank remaining production gaps by severity and closability;
5. select one node;
6. stop at any required human gate;
7. attach evidence and rerun only the affected subgraph after failure.

## Current selection

The post-training graph repair is complete. `C3-FRONT-012` and `C3-TRAINING-001` are reconciled as merged, and the next selected product feature is `C3-FIRMES-001`, the read-only Firmes source-of-truth integration contract. Its spec is complete, but implementation is not authorized. The executable ready set is empty until human approval moves that feature into the canonical roadmap.

Production deployment remains separately `HUMAN_BLOCKED`.
