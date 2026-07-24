# C3-OBS-001 exact-head evidence — observability and recovery control plane

Date: 2026-07-24
Branch: `agent/c3-obs-001-operational-evidence`
Base: `main@ff38e996ba05b2ea4b5c034b44d084776736dad0`
Validated implementation head: `bf722ee8e672a9e89a7e74a47465a8e6287602c8`
Draft PR: `#114`

## Result classification

`CI_GREEN_EXACT_HEAD_RECOVERY_VERIFIED`

This evidence proves repository implementation, local automated verification and an exact-head PostgreSQL 18 native backup/isolated-restore run in hosted CI. It does not prove a managed backup, deployed telemetry, a staging disaster-recovery exercise, an accepted RPO/RTO, production readiness or human approval.

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

## Exact-head hosted verification

| Evidence | Result |
|---|---|
| CampaignOS CI | PASS, run `30041495912` |
| Runtime visual review | PASS, run `30041495919` |
| PostgreSQL backup and isolated restore | PASS, job `89322226244` |
| Validated head | `bf722ee8e672a9e89a7e74a47465a8e6287602c8` |
| Recovery artifact | `campaignos-postgresql-recovery-evidence` (`8577394363`) |
| Artifact digest | `sha256:7495d52dd030b430c90a51e388838d46e5c7b7a3589ecce41117e6e9783c0469` |
| Artifact retention expiry | `2026-08-22T20:18:20Z` |

The hosted job migrated and seeded PostgreSQL 18, created a native custom-format archive, restored it into a distinct `*_restore_test` database, compared the Alembic revision and all public-table row counts, verified the archive checksum and manifest, removed the restore database and uploaded the retained evidence artifact.

## Local environment limitation and validated alternative

The persistent sandbox could not register the pinned PostgreSQL image layer because the outer user namespace denied `lchown /var/empty`. No database startup or mutation occurred locally. The exact same recovery contract was then executed successfully at the published PR head by hosted CI. The local limitation is therefore recorded as an environment limitation with a validated alternative, not as an open delivery defect for this test-only contract.

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

- no managed PostgreSQL encrypted backup schedule, PITR, retention or deletion-protection evidence;
- no deployed scraper, OTLP collector, dashboard or alert receiver;
- no staging failure exercise or measured and approved RPO/RTO;
- no production rollback proof or incident drill;
- no independent operational, security, privacy, legal or human approval;
- historical production blockers remain recorded.

Production remains `BLOCKED`.
