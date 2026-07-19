# CampaignOS executable architecture evidence

This document describes what is executable now. It does not describe the target architecture as if it already existed.

## Integrated C2 stack

The following increments are merged into `main`:

```text
C2-PLAT-001 approval binding hardening
└── C2-PROD-001 Candidate Brand
    └── C2-PROD-002 Approval Inbox and Decision Ledger
        └── C2-PROD-003 Daily Operating Workflow
            └── C2-FRONT-001 Governance Workspace
                └── C2-SAAS-001A Authorization Policy Boundary
                    └── C2-ARCH-001 Executable Program State
                        └── C2-SAAS-001B Persistence and Audit Contracts
                            └── C2-SAAS-001C Repository and Transaction Contracts
                                └── C2-OBS-001 Audit Integrity Read Model
                                    └── C2-API-001A Read-Only Service Contracts
                                        └── C2-TEST-001 Adversarial Harness
                                            └── C2-DOCS-001 Operator Guide
                                                └── C2-AI-001A Extraction and Citation Contracts
```

Their original stacked base branches remain historical traceability. Their current code is on `main`; the stack is not awaiting merge.

## Executable bounded contexts

- Campaign Workspace: validates scoped workspace data and evaluates fail-closed strategic prerequisites.
- Candidate Brand: validates evidence-backed, non-fabricated candidate records.
- Approval Ledger: projects approval requests and hash-linked decision history in memory.
- Daily Operations: derives internal briefs without performing external campaign actions.
- Governance Frontend: renders static read-only snapshots.
- Authorization Policy: returns an exact-scope allow/deny decision; it does not authenticate a session.
- Persistence Audit: plans append events and applies them to an in-memory test adapter.
- Repository Transaction: coordinates in-memory repositories and validation.
- Audit Observability: recomputes an unkeyed hash chain to detect inconsistent stored history.
- Application Service: exposes in-process, read-only query contracts.
- Extraction Citation: performs deterministic local claim classification and evidence reference checks.

## Explicit non-capabilities

The current stack does not provide:

- FastAPI or an HTTP API;
- OIDC/Cognito authentication or validated sessions;
- PostgreSQL, RDS, SQLAlchemy or Alembic persistence;
- database-level atomicity, RLS or durable audit storage;
- digital signatures, KMS keys or an externally anchored audit chain;
- background jobs, SQS or EventBridge;
- S3 evidence attachments;
- Terraform or AWS environments;
- production logs, metrics, traces, alerts, backups or restore tests;
- API-backed Next.js workflows;
- autonomous publication, spending, mobilization or citizen contact.

## Validation evidence

Run locally:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/architecture/validate_program_state.py
```

`architecture/program-state.json` records both successful and failed historical GitHub runs. Six previously cited run IDs have `FAILURE` conclusions. Later green integration runs show that their combined commits passed a later workflow, but do not turn those historical records green.

## Deployment evidence

GitHub Pages currently hosts a static demonstration. The workflow is manual-only and requires `DEMO_NON_PRODUCTION` confirmation. Pages is not dev, staging or production and is excluded from production gate satisfaction.

AWS state was not verified during the foundation audit because the available AWS session had expired. No Terraform existed in the repository at that evidence point.

## Next executable work

`program/task-graph.yaml` identifies `C3-ARCH-001` and `C3-DEVEX-001` as ready after this foundation increment. Real identity, persistence, API, infrastructure and release increments remain dependency-gated.
