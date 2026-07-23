# C3-OBS-001 local evidence — observability and recovery control plane

Date: 2026-07-23  
Branch: `agent/c3-obs-001-operational-evidence`  
Base: `main@ff38e996ba05b2ea4b5c034b44d084776736dad0`

## Result classification

`ACTIVE_LOCAL_VERIFIED_CI_RECOVERY_PENDING`

This evidence proves repository implementation and local automated verification. It does not prove a managed backup, a deployed telemetry stack, a staging restore, an accepted RPO/RTO, production readiness or human approval.

## Verified locally

| Control | Result |
|---|---|
| Full locked Python suite | `686 passed, 10 skipped` |
| Coverage gate | `90.40%`, floor `90%` |
| Ruff | PASS |
| Formatting | PASS |
| Strict mypy | PASS, 66 source files |
| GitHub workflow YAML | PASS |
| Prometheus alert-rule YAML | PASS |
| CI policy verifier | PASS, 3 workflows, 39 SHA-pinned action references, 10 desired checks |
| Metrics authentication/configuration | PASS |
| Correlation and trace-context tests | PASS |
| Low-cardinality/no-sensitive-label tests | PASS |
| Recovery safety and evidence-contract tests | PASS |
| Recovery runtime orchestration tests | PASS |
| Program production block | PRESERVED |

## PostgreSQL recovery execution status

The exact pinned PostgreSQL 18.3 image could not start in the persistent sandbox. Docker failed while registering an image layer because the outer user namespace denied `lchown /var/empty`. The recovery command did not reach database startup, migration, dump or restore. Its cleanup trap removed temporary output and any test container reference.

Therefore:

- local PostgreSQL 18 backup/restore: **not claimed**;
- source database mutation: **none**;
- external effects: **none**;
- exact-head CI PostgreSQL 18 proof: **required and pending**.

The new CI job uses a real PostgreSQL 18.3 service, native `pg_dump`/`pg_restore`, representative migrated and seeded data, isolated restore, Alembic and row-count comparison, cleanup verification, checksum validation and retained evidence.

## Security review notes

- Logs use an explicit field allowlist and omit tokens, request bodies, arbitrary paths and exception messages.
- Metrics labels are bounded and exclude tenant, campaign, principal, citizen and voter identifiers.
- Shared environments fail closed when metrics are enabled without a sufficiently long bearer token.
- Recovery accepts only an isolated source ending in `_test` and a distinct target ending in `_restore_test`.
- The PostgreSQL client image must be bound to a 64-character SHA-256 digest.
- Credentials are supplied through connection libraries or `PGPASSWORD` and are not written to the manifest.
- Backup and manifest files use owner-only permissions.
- The restore database is removed in `finally` unless explicitly retained for test investigation.

## Residual production blockers

- no managed PostgreSQL backup schedule, encrypted destination, PITR or retention evidence;
- no deployed scraper, OTLP collector, dashboard or alert receiver;
- no staging failure exercise or measured RPO/RTO;
- no production rollback proof;
- no independent operational, security, privacy, legal or human approval;
- historical production blockers remain recorded.

Production remains `BLOCKED`.
