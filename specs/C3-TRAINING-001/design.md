# C3-TRAINING-001 Design

## Approach

Implement the Training Academy as two separated boundaries:

1. a repository-owned, immutable-at-runtime content catalog; and
2. tenant/campaign-scoped learner assignment and completion records.

Content definitions are reviewed source code or strict JSON/YAML loaded at startup and validated against a typed schema. Runtime users cannot upload HTML, scripts, media or arbitrary course bodies in this increment. Per-learner state is persisted in PostgreSQL with RLS, exact authorization, idempotency, append-only audit and bounded attempts.

A role learning path is a recommendation only. Completion is evidence of finishing a bounded internal module; it is not a permission, employment score, professional credential or political decision.

## Product Sequence

The initial catalog mirrors the practical sequence already evaluated from the user-provided Campol source:

1. research before action;
2. evidence-based planning and strategy;
3. accountable team organization;
4. governed communication preparation;
5. measurement, learning and adjustment;
6. safety, privacy and human authority throughout.

The academy does not reproduce the source. Lessons are authored from CampaignOS versioned product, security and operations documentation and cite those repository sources.

## Content Catalog

Proposed package: `backend/src/campaignos/training/`.

Each `TrainingModule` contains:

- stable module ID and semantic content version;
- status: `DRAFT`, `APPROVED` or `RETIRED`;
- locale pair `es` / `en`;
- owner and reviewer role labels;
- title, plain-language summary and learning objectives;
- ordered lessons with stable IDs and Markdown-subset text;
- repository-relative source references;
- bounded deterministic assessment questions;
- passing rule expressed only as a fixed count or percentage;
- review date and content digest;
- explicit `authority_effect=NONE` and `external_effects=NONE`.

### Safe rendering

Allow only a reviewed Markdown subset converted by server-owned components. Reject raw HTML, scripts, iframes, remote images, arbitrary links, tracking parameters and executable embeds. Source references resolve only to an allow-listed repository documentation catalog.

### Locale parity

ES and EN variants share module ID, version, lesson IDs, objective IDs, question IDs, answer keys, passing rule, source references and governance metadata. Text may differ by locale but structure cannot drift.

## Learning Paths

A `LearningPath` defines:

- stable path ID and version;
- ordered module/version references;
- applicable existing role blueprint slugs;
- required versus optional modules;
- plain-language purpose and completion rule;
- `authority_effect=NONE`.

Path recommendation is deterministic from a role slug. An authorized human chooses whether to assign it. No path or completion changes application grants.

## Persistence

Proposed migration: `20260801_0013_training_academy`.

### `training_assignments`

- `id`, `tenant_id`, `campaign_id`, `principal_id`;
- path ID/version, optional role ID/slug;
- assignment status and version;
- assigned by, assigned at, optional due date and completed at;
- exact catalog digest;
- unique active assignment constraint;
- timestamps.

### `training_module_progress`

- assignment, module ID/version and state;
- started/completed timestamps;
- attempt count;
- latest pass/fail result;
- catalog digest and version;
- no raw free-text learner profile.

### `training_completion_receipts`

Append-only receipt containing assignment/module/version, result, completed at, actor, catalog digest, audit ID and `authority_effect=NONE`. Receipts are historical and remain readable after module retirement.

All tables carry tenant/campaign scope and forced RLS. Cross-tenant foreign keys or references fail before disclosure. Audit and domain writes remain atomic.

## Assessment Model

- fixed multiple-choice or multi-select questions only;
- server-owned answer keys and explanations;
- deterministic pass/fail from the approved module version;
- at most ten attempts;
- no adaptive psychological inference, ranking or comparative score;
- persist selected stable answer IDs only as needed for the attempt transaction, then retain the bounded result/receipt rather than a behavioral profile;
- malformed, unknown or stale question IDs fail closed;
- a passed module is immutable except through a separately audited correction/void receipt.

## API Surface

Proposed protected routes under `/api/v1/training`:

- `GET /catalog` — approved modules and paths visible to the session locale;
- `GET /me` — learner assignments, progress and next lesson;
- `GET /assignments/{id}` — exact authorized assignment read;
- `POST /assignments` — authorized same-tenant/campaign assignment;
- `POST /assignments/{id}/modules/{module_id}/start`;
- `POST /assignments/{id}/modules/{module_id}/attempts`;
- `GET /assignments/{id}/receipts`;
- optional authorized content-governance projection for repository catalog state, not runtime content editing.

Every mutation uses idempotency, expected version where applicable, exact authorization and a reviewed rate-limit class. Response models reject unknown fields.

## Authorization

Proposed actions:

- `training.catalog.read` — approved catalog projection;
- `training.self.read` — own assignments/progress;
- `training.self.complete` — own bounded module attempts;
- `training.assignment.read` — authorized learner/manager/reviewer scope;
- `training.assignment.manage` — assign paths in exact tenant/campaign;
- `training.receipt.read` — authorized audit/reviewer scope.

A role label, module completion or recommendation never satisfies authorization. Existing membership/grant checks remain authoritative.

## Team Workspace Integration

The team chapter adds a visible academy entry with:

- current learning path and why it applies;
- progress and next lesson;
- required/optional module distinction;
- clear assessment feedback;
- compact source/governance disclosure;
- historical completion receipts.

Existing `TeamTrainingRequirement` may reference a module/path version through a backward-compatible extension. The read model can show matched completion evidence, but access recommendations, staffing acceptance and role readiness remain separate human decisions.

## Files You May Read

- `AGENTS.md`, `RTK.md`;
- `specs/C3-TRAINING-001/**`;
- `backend/src/campaignos/teams/**`;
- `backend/src/campaignos/identity/**`;
- `backend/src/campaignos/data/**`;
- `backend/src/campaignos/api/**`;
- `frontend/src/components/**`, `frontend/src/lib/**`, `frontend/src/app/**`;
- `docs/product/**`, `docs/security/**`, `docs/operations/**`, `docs/testing/**`;
- `.github/workflows/**`, `program/**`.

## Files You May Touch

- `backend/src/campaignos/training/**`;
- one additive Alembic migration and narrowly required model exports;
- protected training routes and route registration;
- exact authorization/rate-limit inventory changes required by those routes;
- focused training unit, API, PostgreSQL and security tests;
- team contracts/read model only for backward-compatible module/path references;
- frontend academy contracts, parsers, components, routes and tests;
- deterministic browser/functional reviewers;
- Makefile/CI only for existing locked verification and retained evidence;
- Training Academy product/API/operator/testing docs;
- canonical program, graph, ledger, eval and review evidence.

## Files You Must Not Touch

- Graph Harness framework source;
- live identity, AI, social, advertising, messaging or campaign accounts;
- Terraform apply, remote state, cloud resources or production environments;
- voter/citizen/supporter databases, persuasion, turnout, targeting or surveillance modules;
- dependency manifests or lockfiles without separately expanded approval;
- historical evidence except append-only reconciliation/supersession notes.

## Dependencies

No new runtime, paid or cloud dependency is planned. Reuse Pydantic, FastAPI, SQLAlchemy, PostgreSQL, existing safe UI primitives, current audit/idempotency/RLS infrastructure and locked browser tooling.

Implementation is not authorized until a human approves this complete SHIP specification.

## Primary-Documentation Checkpoints

Before implementation, confirm current primary documentation for:

- Pydantic strict/frozen models and validators;
- FastAPI dependency ordering and response validation;
- SQLAlchemy transaction boundaries and PostgreSQL RLS/constraints;
- PostgreSQL append-only and concurrency semantics used by assignments/receipts;
- Next.js server/client boundaries and safe rendering approach;
- WCAG guidance for progress, assessments, feedback and disclosures;
- GitHub Actions artifacts and the repository's pinned CI policy.

## Risks and Localized Repairs

- **Content drift:** require stable IDs, digests, locale parity and approved/retired state.
- **Hidden authority:** hard-code `authority_effect=NONE`; test that completions never create grants.
- **Person scoring:** persist bounded educational pass/fail only; reject ranking and adaptive traits.
- **Unsafe content:** repository-owned allow-listed sources and no raw HTML/remote embeds.
- **Stale assessments:** bind attempts and receipts to exact module version/digest.
- **Cross-tenant disclosure:** forced RLS, exact authorization and BOLA tests.
- **Retry duplication:** idempotency and unique attempt/receipt constraints.
- **False certification:** plain language states internal learning evidence only.
- **Source misuse:** paraphrase the practical sequence; do not copy third-party course content.
- **Scope expansion:** stop if external LMS, media hosting, new dependency, cloud resource or live provider is required.

## Verification Plan

- Graph Harness approval and one-feature invariant;
- strict catalog, locale parity, digest and safe-content tests;
- learning path and role recommendation tests;
- assignment, attempt, completion and receipt lifecycle tests;
- authorization/BOLA/RLS/idempotency/audit failure tests;
- PostgreSQL 18 concurrency and append-only receipt tests;
- ES/EN parser/component/build tests;
- Chromium desktop/mobile/keyboard/reduced-motion/WCAG review;
- functional API/PostgreSQL/browser persistence journey;
- complete locked repository suite, security, supply-chain and secret scans;
- exact-head hosted CI and retained sanitized evidence;
- critic/red-team, fixer, independent verifier and release gate evidence.
