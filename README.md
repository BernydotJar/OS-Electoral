# CampaignOS / OS Electoral

CampaignOS is an evidence-led campaign operating system with human-gated decisions, tenant isolation and auditable internal operations.

## Current status

**Controlled internal use: under final C3-RELEASE-002 verification. Production readiness: `BLOCKED`.**

The current protected-main baseline includes:

- a versioned FastAPI application with exact authorization, idempotency/version controls, safe errors, correlation/trace handling and tenant/principal rate limiting;
- PostgreSQL/Alembic persistence through Training Academy revision `20260801_0013`, forced row-level security and constrained application-role verification;
- fixed-algorithm OIDC token verification plus a deliberately development-only local identity adapter for isolated functional review;
- governed campaign creation/context, guided intake, Candidate evidence/approval, Team organization/readiness, Training Academy, Strategy human decision, Operations roadmap and immutable Daily War Room snapshot workflows;
- a server-rendered ES/EN Next.js application with exact-authorized mutation controls, mobile/keyboard/reduced-motion behavior and WCAG 2.2 A/AA automated review;
- internal outbox processing, bounded retries/dead-letter state, sanitized observability hooks, recovery verification and fail-closed rollback policy;
- protected GitHub CI covering quality/contracts, PostgreSQL/RLS, dependency audit, SBOM/provenance, browser review, secret scan, CodeQL and constrained-stack E2E.

The complete CI-equivalent PostgreSQL/API/browser journey can create a governed campaign draft and continue through Candidate → Team → Strategy → Operations → War Room with persistence after reload and `external_effects=NONE`. This is evidence for isolated internal product use, not production authorization.

Production remains blocked because CampaignOS does not yet have a production-verified live identity/login/recovery/MFA lifecycle, managed staging/production runtime, managed backup/PITR, deployed telemetry and alert routing, accepted RPO/RTO exercises, independent security/privacy/legal/domain/operational approvals, or explicit human production approval. The development identity must not be exposed as public or production authentication.

The public GitHub Pages site is a static non-production review surface and never satisfies production gates. The authoritative controlled-use decision is `program/controlled-use-readiness.json`; the production decision remains `program/release-readiness.json`.

## Program truth

- [Current-state assessment](program/current-state-assessment.md)
- [Production-gap matrix](program/production-gap-matrix.md)
- [Controlled-use readiness](program/controlled-use-readiness.json)
- [Production release readiness](program/release-readiness.json)
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

To exercise the first real API-backed browser journey locally:

```bash
make functional-dev
# open the URL printed by the command, normally http://127.0.0.1:3000/es or /en
make functional-down
```

Functional mode applies migrations, seeds the bounded development operator with 26 exact grants for the deterministic existing-campaign workflow, and runs the real PostgreSQL/FastAPI/Next.js application. The CI-equivalent isolated full-journey harness adds exactly one tenant campaign-create grant (27 total) and verifies Candidate, Team/Training, Strategy, Operations and War Room persistence. Before startup the local launcher checks loopback ports for PostgreSQL, API, S3Mock, Mailpit and Next.js. Available configured ports are preserved; occupied ports are replaced with unique ephemeral ports and reported explicitly. The development identity is rejected outside `development`; it is not shared or production authentication.

`make test-postgres` requires an explicitly isolated `CAMPAIGNOS_TEST_DATABASE_URL` whose database name ends in `_test`. The end-to-end script creates a unique Compose project, applies and checks the Alembic migration, verifies dependency readiness, and removes its containers and volumes on exit. S3Mock accepts dummy credentials and is strictly a local test service; it is not a production storage design.

Some legacy validation harnesses generate files under `artifacts/`; inspect their behavior before running them in a dirty worktree.

## Safety boundary

AI output is advisory. Eligibility never constitutes human approval. The current repository does not authorize autonomous publishing, spending, political persuasion, field mobilization, citizen contact or production deployment.
