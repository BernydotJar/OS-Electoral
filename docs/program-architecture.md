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
| `program/iteration-log.md` | Observe/execute/verify/record history |

The repository and verified external state override stale prose. A run ID is not green evidence unless its conclusion and commit SHA are recorded. A merged PR does not prove production readiness.

## Current baseline

The C2 increments are merged into `main`. They implement deterministic prototype contracts for campaign workspaces, candidate-brand assessment, approvals, daily operations, authorization decisions, in-memory persistence coordination, audit-event hash chaining, read-only service projections and evidence citation.

Important limits:

- repositories and transactions are in-memory test doubles, not PostgreSQL;
- the service facade is not a network API;
- audit hashes are unkeyed SHA-256 links, not digital signatures or an immutable external ledger;
- frontend data is static and read-only;
- GitHub Pages is a non-production demo;
- production status remains `BLOCKED`.

## Workstreams

| ID | Workstream | Current state | Next increment |
|---|---|---|---|
| WS-01 | Product Definition and Architecture | Active foundation reconciliation | C3-ARCH-001 |
| WS-02 | Monorepo and Developer Experience | Ready | C3-DEVEX-001 |
| WS-03 | Identity, Tenancy and RBAC | Local OIDC and membership authorization; lifecycle pending | C3-IAM-001 |
| WS-04 | Campaign Domain and Persistence | In-memory prototype only | C3-DATA-001 |
| WS-05 | API and Background Jobs | Local versioned health/identity runtime; domain actions and jobs pending | C3-API-001 |
| WS-06 | Frontend, Design System and i18n | Static prototype | C3-FRONT-001 |
| WS-07 | Guided Onboarding and Candidate Workspace | Guided intake and Candidate Workspace draft-PR CI-green with read-only ES/EN surfaces; authenticated editing and dedicated review separation pending | C3-TEAM-001 |
| WS-08 | Team Builder and Training Academy | Static team prototype only | C3-TEAM-001 |
| WS-09 | Research, Strategy and Decision Governance | Partial deterministic prototype | C3-STRATEGY-001 |
| WS-10 | Roadmap, War Room and Campaign Health | Static/deterministic prototype | C3-OPS-001 |
| WS-11 | Agent Runtime, Guardrails and Evals | Deterministic prototype | C3-AGENT-001 |
| WS-12 | AWS Platform and Terraform | Not started | C3-INFRA-001 |
| WS-13 | Security, Privacy and Compliance | Partial policy prototype | C3-SEC-001 |
| WS-14 | Testing, Observability and Operations | In-memory tests only | C3-OBS-001 |
| WS-15 | Documentation, Migration and Release | Active | C3-RELEASE-001 |

The exact dependency graph lives in `program/task-graph.yaml`. It preserves research-before-strategy, identity/data prerequisites for API work, and security/observability prerequisites for release.

## Delivery classifications

- `DEMO_NON_PRODUCTION`: static demonstration; may never be cited as SaaS readiness.
- `DEV`: application environment created through reviewed infrastructure and CI.
- `STAGING`: production-like environment with migration, security, load, restore and eval evidence.
- `PRODUCTION`: permitted only after every required gate passes and an authorized human records explicit approval.

The Pages workflow accepts only a manual dispatch with the literal confirmation `DEMO_NON_PRODUCTION`. It does not create or promote a production release.

## Completion rule

The manifest validator intentionally accepts a truthful `BLOCKED` state with declared red runs and open findings. It rejects `READY` whenever an unsuperseded failed run, open CRITICAL/HIGH finding, incomplete production gate or missing human production approval remains.
