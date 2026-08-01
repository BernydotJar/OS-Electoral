# C3-OPS-002 Design

## Approach

Implement a repository-owned rollback decision boundary rather than a deployment controller. A strict policy catalog describes which response is allowed for each release failure class. A validator inspects the catalog and one bounded rehearsal input, selects or refuses a response, and writes a sanitized JSON receipt. The human-readable runbook explains the same contract for operators.

The current repository has plan-only Terraform, local Compose, PostgreSQL 18 migration/recovery tests, health/readiness endpoints, SBOM/provenance evidence and no authorized managed environment. Therefore the implementation can prove decision quality and local rehearsal only. It cannot claim that production rollback works.

## Decision Order

1. freeze additional release actions and record the exact candidate revision;
2. verify human authority for the environment and incident scope;
3. identify the last known-good immutable artifact and retained provenance;
4. inspect migration head, compatibility classification and whether committed writes occurred;
5. inspect health, readiness, error, pool, worker and audit evidence;
6. choose one allowed response or refuse to proceed;
7. execute only the bounded local rehearsal action;
8. verify health, authorization/RLS, migration state, audit continuity and cleanup;
9. persist a sanitized receipt and unresolved risks;
10. escalate managed restore, production rollback or approval to an authorized human.

## Response Classes

- `ABORT_BEFORE_CHANGE`: stop before application or schema mutation.
- `ROLL_BACK_APPLICATION_ARTIFACT`: restore a previously verified immutable application revision only when the current schema remains compatible.
- `REVERSE_CONFIGURATION`: restore an approved non-secret configuration snapshot without weakening controls.
- `FORWARD_FIX_SCHEMA_OR_APPLICATION`: preferred when writes occurred or downgrade safety is unproven.
- `ISOLATED_RESTORE_FOR_INVESTIGATION`: restore a verified backup only into a separate non-production target.
- `CONTAIN_AND_ESCALATE`: stop workers or release activity, preserve evidence and require incident authority.
- `REFUSE_UNSAFE_ROLLBACK`: missing evidence, mutable artifact, unknown schema compatibility, destructive request or absent authority.

## Migration Safety Model

Every migration in scope must be classified in a versioned catalog as:

- `EXPAND_BACKWARD_COMPATIBLE`;
- `REVERSIBLE_TESTED_NO_DATA_LOSS`;
- `FORWARD_FIX_ONLY`;
- `RESTORE_REQUIRED_FOR_DATA_RECOVERY`.

Unknown or conflicting classifications fail closed. The catalog records migration revision, compatibility window, application revisions tested, data-loss risk and required evidence. The validator does not execute downgrade SQL. A future managed-staging exercise may execute an explicitly approved reversible path in an isolated database.

## Evidence Contract

Proposed receipt: `artifacts/c3-ops-002/rollback-rehearsal.json`.

Required fields:

- `schema_version`;
- `source_revision`;
- `environment_classification` = `CONSTRAINED_NON_PRODUCTION`;
- `scenario_id`;
- `candidate_revision`;
- `previous_known_good_revision`;
- `migration_head`;
- `migration_classification`;
- `committed_writes_observed`;
- `authority_check`;
- `artifact_provenance_check`;
- `health_checks`;
- `selected_response`;
- `decision`;
- `cleanup`;
- `limitations`;
- `production_rollback_claim` = `false`;
- `external_effects` = `NONE`.

The receipt rejects unknown fields and must not contain bearer tokens, cookies, database URLs, secret values, tenant/principal/campaign identifiers, request bodies, arbitrary external URLs or political content.

## Proposed Files

- `program/rollback-readiness.json`: versioned policy and scenario catalog;
- `scripts/operations/verify_release_rollback.py`: strict validator and bounded decision runner;
- `backend/tests/test_release_rollback.py`: policy, scenario and adverse-path tests;
- `docs/operations/release-rollback.md`: operator decision tree and escalation runbook;
- `docs/testing/c3-ops-002-evidence.md`: implementation evidence;
- `progress/review_C3-OPS-002.md`;
- `program/iterations/c3-ops-002.md`;
- `program/validations/c3-ops-002.json`;
- `Makefile` and `.github/workflows/campaignos-ci.yml` only for a bounded validation command and retained sanitized receipt;
- existing release-readiness, eval and program records only where required to reference the new evidence.

## Files You May Read

- `AGENTS.md`, `RTK.md` and `specs/C3-OPS-002/**`;
- `docs/operations/**`, `docs/architecture/deployment-architecture.md` and security runbooks;
- `program/release-readiness.json`, program state, task graph, ledger, eval and risk records;
- `backend/migrations/**`, recovery tooling, health/readiness and observability code;
- `compose.yaml`, container files and `.github/workflows/**`;
- supply-chain, PostgreSQL recovery, rate-limit and load-verification evidence.

## Files You Must Not Touch

- Terraform apply/state or live cloud resources;
- production credentials, environments, databases, queues, buckets or registries;
- historical migration files except append-only classification metadata;
- authentication, authorization, RLS, audit, rate-limit or safety controls to make a rehearsal pass;
- campaign strategy, persuasion, targeting, contact, publication, spending or mobilization modules;
- dependency manifests or lockfiles without expanded human approval.

## Dependencies

No new runtime or paid dependency is planned. Reuse Python standard library, Pydantic/JSON patterns already in the repository, Alembic metadata, PostgreSQL 18 recovery tooling, Compose health checks, current CI artifact upload and existing supply-chain manifests.

Implementation is not authorized until the human approval gate accepts this specification.

## Primary-Documentation Checkpoints

Before implementation, confirm current primary documentation for:

- Alembic revision and downgrade semantics for the pinned version;
- PostgreSQL 18 backup/restore, transaction and recovery behavior used by the rehearsal;
- Docker Compose health and immutable image reference behavior;
- GitHub Actions artifact/provenance retention used as release evidence;
- the repository-pinned Terraform and AWS target architecture boundaries, without performing apply.

## Risks and Localized Repairs

- false safety from a document-only runbook: require executable schema validation and adverse tests;
- data loss from downgrade: default to forward-fix or refusal unless explicit reversible evidence exists;
- mutable artifact rollback: require full SHA or digest plus provenance;
- secret leakage: strict receipt schema and secret scan before retention;
- duplicate worker effects: prohibit automatic replay and preserve dead-letter evidence;
- stale runbook: bind checks to current migration head, health endpoints and CI policy;
- false production claim: label every receipt constrained non-production and keep managed gates blocked;
- environment drift: fail closed when the runtime cannot prove the expected source or schema revision.

## Verification Plan

- Graph Harness state and approval-gate validation;
- strict policy/schema unit tests and adverse mutation tests;
- CLI success, refusal, malformed input and failure-receipt tests;
- migration classification completeness for the current head;
- bounded local Compose/PostgreSQL 18 rehearsal where the environment permits;
- recovery-manifest, health/readiness, authorization/RLS and cleanup assertions;
- Ruff, formatting, strict mypy and complete Python coverage gate;
- existing frontend/build verification unchanged unless user-facing docs are surfaced;
- release, security, supply-chain, Terraform plan-only and program validators;
- worktree, committed-range and submitted-diff secret scans;
- exact-head hosted CI with retained sanitized receipt;
- independent critic/red-team and release review.
