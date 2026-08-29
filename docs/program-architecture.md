# CampaignOS program architecture

CampaignOS is a production-readiness program, not a single feature or release. The target is an open-source-first modular monolith on AWS with explicit bounded contexts, multi-tenant authorization, PostgreSQL persistence, governed AI assistance and human approval for sensitive actions.

## Sources of truth

| Artifact | Purpose |
|---|---|
| `architecture/program-state.json` | Validated manifest for merged evidence, findings, CI runs, gates and roadmap |
| `program/program-state.json` | Farmtable-compatible fallback program summary |
| `program/task-graph.yaml` | Dependency graph and acceptance intent |
| `program/task-ledger.yaml` | Ownership, status, evidence and blockers |
| `program/production-gap-matrix.md` | Requirement-by-requirement production gaps |
| `program/controlled-use-readiness.json` | Fail-closed isolated internal-use decision and boundaries |
| `program/iteration-log.md` | Observe/execute/verify/record history |

The repository and verified external state override stale prose. A run ID is not green evidence unless its conclusion and commit SHA are recorded. A merged PR does not prove production readiness.

## Current baseline

Protected `main` is `1b32e46304b47c04cf44510c4b5f1b29bb9391b9` after PR `#183` reconciled the merged Operations lifecycle. The repository now contains a complete governed local product journey: campaign draft/context and intake, Candidate evidence/current-version approvals, Team/Training readiness and human role coverage, Strategy alternatives plus explicit human decision, Operations roadmap, learning and immutable Daily War Room snapshots.

C3-RELEASE-002 is the active final controlled-use review. Its local evidence classifies the product as `READY_FOR_CONTROLLED_INTERNAL_USE` in an isolated internal environment while production remains `BLOCKED` / `DENY_RELEASE`.

Important limits:

- the development identity is local/isolated only; live OIDC login, recovery, MFA and provider operations are not production-verified;
- no managed dev/staging/production runtime, managed backup/PITR, deployed alert routing or accepted RPO/RTO evidence exists;
- independent security, privacy, legal, domain and operational production approvals are absent;
- stable zero-cost shared full-product hosting remains unresolved in issue `#181`;
- `C3-FIRMES-001` remains outside the executable roadmap until explicit human approval;
- the consuming repository remains pinned to Graph Harness `0eb0d5fe...`; migration to the framework's newer typed project/event runtime is separate governance work;
- production status remains `BLOCKED` and external campaign effects remain separately human-gated.

## Workstreams

| ID | Workstream | Current state | Next increment |
|---|---|---|---|
| WS-01 | Product Definition and Architecture | `BASELINE_MERGED` | `C3-IAM-002` |
| WS-02 | Monorepo and Developer Experience | `PROTECTED_SUPPLY_CHAIN_CI_GREEN` | `C3-INFRA-001` |
| WS-03 | Identity, Tenancy and RBAC | `IDENTITY_LIFECYCLE_VERIFIED_POSTGRESQL_LIVE_PROVIDER_PENDING` | `C3-ONBOARD-001` |
| WS-04 | Campaign Domain and Persistence | `CAMPAIGN_CREATE_VERIFIED_POSTGRESQL_OPEN_STACK_ACTIVE` | `C3-ONBOARD-001` |
| WS-05 | API and Background Jobs | `API_BASELINE_CI_GREEN` | `C3-AGENT-001` |
| WS-06 | Frontend, Design System and i18n | `OPERATIONS_UI_MERGED_POSTMERGE_GREEN` | `C3-FIRMES-001_APPROVAL_PENDING` |
| WS-07 | Guided Onboarding and Candidate Workspace | `CANDIDATE_COMPLETION_UI_MERGED` | `C3-FRONT-014` |
| WS-08 | Team Builder and Training Academy | `TEAM_READINESS_UI_MERGED_POST_MERGE_GREEN` | `C3-FIRMES-001_APPROVAL_PENDING` |
| WS-09 | Research, Strategy and Decision Governance | `STRATEGY_UI_MERGED_POSTMERGE_RECONCILED` | `C3-FIRMES-001_APPROVAL_PENDING` |
| WS-10 | Roadmap, War Room and Campaign Health | `OPERATIONS_UI_MERGED_POSTMERGE_GREEN` | `C3-FIRMES-001_APPROVAL_PENDING` |
| WS-11 | Agent Runtime, Guardrails and Evals | `AGENT_CI_GREEN_NO_LIVE_PROVIDER` | `C3-CI-001` |
| WS-12 | AWS Platform and Terraform | `PLAN_ONLY_CI_GREEN` | `C3-SEC-001` |
| WS-13 | Security, Privacy and Compliance | `SECURITY_CI_GREEN` | `C3-SEC-001` |
| WS-14 | Testing, Observability and Operations | `ROLLBACK_POLICY_MERGED_MANAGED_STAGING_PENDING` | `HUMAN_AUTHORIZE_MANAGED_STAGING` |
| WS-15 | Documentation, Migration and Release | `CONTROLLED_USE_REVIEW_ACTIVE_PRODUCTION_BLOCKED` | `C3-RELEASE-002` |

The exact dependency graph lives in `program/task-graph.yaml`; current scheduling and approval state live in `program/graph-harness-execution.json`. The architecture manifest, not prose, is authoritative when any discrepancy appears.

## Delivery classifications

- `DEMO_NON_PRODUCTION`: static demonstration; may never be cited as SaaS readiness.
- `DEV`: application environment created through reviewed infrastructure and CI.
- `STAGING`: production-like environment with migration, security, load, restore and eval evidence.
- `PRODUCTION`: permitted only after every required gate passes and an authorized human records explicit approval.

The Pages workflow accepts only a manual dispatch with the literal confirmation `DEMO_NON_PRODUCTION`. It does not create or promote a production release.

## Completion rule

The manifest validator intentionally accepts a truthful `BLOCKED` state with declared red runs and open findings. It rejects `READY` whenever an unsuperseded failed run, open CRITICAL/HIGH finding, incomplete production gate or missing human production approval remains.
