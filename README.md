# CampaignOS / OS Electoral

CampaignOS is intended to become a guided, evidence-led campaign operating system with human-gated decisions, multi-tenant isolation and auditable internal operations.

## Current status

**Production readiness: `BLOCKED`.**

The merged C2 stack and the current C3 foundation provide:

- deterministic Python domain contracts and in-memory repository test doubles;
- a versioned FastAPI application factory with liveness, dependency readiness, safe errors and correlation/security headers;
- fixed-algorithm OIDC ID-token verification with issuer, audience, time, token-use and key checks;
- an initial PostgreSQL/Alembic identity, tenancy, campaign, membership, grant, audit and outbox schema;
- transaction-local tenant scope plus forced PostgreSQL row-level security, exercised against an isolated non-superuser role;
- server-owned active membership, role and exact-grant loading for the tenant-scoped `/api/v1/tenants/{tenant_id}/me` identity projection;
- a locked Python toolchain, non-root API image and loopback-only Compose stack for PostgreSQL, S3Mock and Mailpit;
- pinned CI definitions for quality, PostgreSQL/RLS, dependency, secret, CodeQL, workflow and disposable-stack E2E checks;
- read-only campaign, candidate, approval and Daily War Room projections;
- authenticated, exact-grant-protected PostgreSQL campaign detail and keyset-paginated list endpoints;
- a static CampaignOS frontend demonstration.

These are local foundations, not a production system. CampaignOS still lacks a live identity/login/recovery and session lifecycle, membership administration, authorization enforcement on campaign-domain writes and workers, broader campaign-domain persistence adapters and APIs, a worker runtime, production object storage, a dynamic application frontend, Terraform/AWS environments, protected-branch evidence, backup/restore evidence, independent security/privacy/domain approvals and production deployment approval.

The public GitHub Pages site is classified as `DEMO_NON_PRODUCTION`. It serves static snapshots, is not a SaaS runtime, and is not evidence of production readiness. Its workflow is manual-only and requires the explicit confirmation value `DEMO_NON_PRODUCTION`.

## Program truth

- [Current-state assessment](program/current-state-assessment.md)
- [Production-gap matrix](program/production-gap-matrix.md)
- [Program state](program/program-state.json)
- [Task graph](program/task-graph.yaml)
- [Task ledger](program/task-ledger.yaml)
- [Executable architecture](docs/executable-architecture.md)

`architecture/program-state.json` is the validated machine-readable manifest for merged C2 evidence, open findings, production gates and the C3 roadmap. Historical failed CI runs remain recorded; a later green integration run does not rewrite their conclusions.

## Repository map

```text
architecture/  Validated program manifest
program/       Program truth, dependency graph, evidence and iteration records
core/          Deterministic domain contracts and in-memory adapters
tests/         Unit and adversarial characterization tests
backend/       FastAPI, OIDC, SQLAlchemy models, Alembic migrations and backend tests
schemas/       JSON schemas for current prototype contracts
web/           Static read-only demonstration
campaign/      Governed Antigua working artifacts
research/      Evidence register, extraction and curated research
docs/          Current bounded-context and operator documentation
compose.yaml   Hermetic local API/PostgreSQL/S3Mock/Mailpit stack
infra/         Target location for future Terraform; absence means AWS platform is not implemented
```

## Current verification

Install [uv](https://docs.astral.sh/uv/) and Docker, then use the reviewed entry points:

```bash
make bootstrap
make verify
make e2e
```

`make test-postgres` requires an explicitly isolated `CAMPAIGNOS_TEST_DATABASE_URL` whose database name ends in `_test`. The end-to-end script creates a unique Compose project, applies and checks the Alembic migration, verifies dependency readiness, and removes its containers and volumes on exit. S3Mock accepts dummy credentials and is strictly a local test service; it is not a production storage design.

Some legacy validation harnesses generate files under `artifacts/`; inspect their behavior before running them in a dirty worktree.

## Safety boundary

AI output is advisory. Eligibility never constitutes human approval. The current repository does not authorize autonomous publishing, spending, political persuasion, field mobilization, citizen contact or production deployment.
