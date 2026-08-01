# CampaignOS release rollback and reversal runbook

## Scope

This runbook helps an authorized operator decide whether to stop, reverse, forward-fix, contain or refuse a release recovery action. The repository implementation is a decision validator and evidence generator. It is not a deployment controller.

Production remains `BLOCKED`. The runbook does not authorize Terraform apply, image publication, production deployment, database downgrade, restore over a source database, secret rotation, queue replay, citizen contact, campaign publication, spending or mobilization.

## Plain-language decision sequence

1. **Stop additional changes.** Record the exact candidate commit and the previous known-good commit.
2. **Confirm scope and authority.** The local/CI rehearsal accepts only `CONSTRAINED_NON_PRODUCTION_REHEARSAL`. Production authority is never inferred.
3. **Check the artifact.** Both revisions must be immutable full Git commit objects. A tag, branch, `latest` image or missing commit is refused.
4. **Check the database version.** Read `alembic_version` and find an exact classification in `program/rollback-readiness.json`.
5. **Check whether writes happened.** Suspected committed writes move the response toward containment, forward-fix or isolated investigation—not destructive downgrade.
6. **Check health and dependencies.** Use liveness, readiness, identity, database, worker, audit and recovery evidence. Container startup by itself is not health.
7. **Select one response.** The validator either chooses the reviewed response or `REFUSE_UNSAFE_ROLLBACK`.
8. **Verify and retain evidence.** Keep the sanitized receipt, cleanup result and unresolved limitations. Do not copy secrets, identifiers or campaign content.
9. **Escalate managed actions.** Production rollback, managed restore, PITR, RPO/RTO acceptance and cloud changes require separate authorized owners.

## Response classes

| Response | Meaning | What the repository rehearsal does |
| --- | --- | --- |
| `ABORT_BEFORE_CHANGE` | Stop before application, configuration or schema mutation. | Validates evidence and records the stop. |
| `ROLL_BACK_APPLICATION_ARTIFACT` | Select a previously verified immutable application revision while retaining a compatible schema. | Validates the decision only; it does not deploy an artifact. |
| `REVERSE_CONFIGURATION` | Restore an approved non-secret configuration snapshot. | Verifies that protected controls remain enabled; it does not change configuration. |
| `FORWARD_FIX_SCHEMA_OR_APPLICATION` | Correct the application or schema without destructive downgrade. | Records the required response and blocks unsafe commands. |
| `ISOLATED_RESTORE_FOR_INVESTIGATION` | Restore a verified backup into a separately named non-production target. | Requires backup and isolation evidence; the rollback validator itself performs no restore. |
| `CONTAIN_AND_ESCALATE` | Freeze workers/release activity, preserve evidence and require incident authority. | Records containment; it does not replay or delete events. |
| `REFUSE_UNSAFE_ROLLBACK` | Evidence, compatibility, authority or safety is insufficient. | Fails closed and writes a failure receipt. |

## Migration policy

The authoritative catalog is `program/rollback-readiness.json`.

- Revisions `20260719_0001` through `20260721_0010` are `FORWARD_FIX_ONLY` because their downgrade bodies remove domain, identity, audit, candidate, team, War Room, strategy or governed-agent state.
- Revision `20260721_0011` is `FORWARD_FIX_ONLY` with `CRITICAL_CONTROL_LOSS` because downgrade removes append-only enforcement.
- Revision `20260729_0012` is `EXPAND_BACKWARD_COMPATIBLE`: the rate-limit table may remain while a previously verified application artifact is selected. The schema is not downgraded.
- Revision `20260801_0013` is `EXPAND_BACKWARD_COMPATIBLE`: Training Academy tables and the append-only receipt trigger may remain while a previously verified application artifact is selected. No training authority is inferred and the schema is not downgraded.
- A new or unknown revision is refused until the catalog, tests and compatibility evidence are updated and reviewed.

An Alembic downgrade function is not approval to run it.

## Required scenarios

### Release stopped before migration

Use `ABORT_BEFORE_CHANGE`. Confirm that no application, configuration or schema mutation occurred and retain the failed gate.

### Application failure with compatible schema

`ROLL_BACK_APPLICATION_ARTIFACT` is available only when:

- the current migration is cataloged as backward-compatible;
- the candidate and previous-known-good revisions are full Git commit objects;
- retained source/provenance evidence exists;
- health or readiness failure is observed;
- production is not the target;
- no protected control is weakened.

### Application failure with unknown schema compatibility

Use `REFUSE_UNSAFE_ROLLBACK`. Do not guess and do not run a downgrade. Preserve evidence and prepare a forward fix or authorized isolated investigation.

### Stale or failed migration without writes

Use `FORWARD_FIX_SCHEMA_OR_APPLICATION`. Confirm no committed domain writes before applying a separately reviewed forward correction in an authorized environment.

### Suspected data-integrity failure after writes

Use `CONTAIN_AND_ESCALATE`. Stop release activity and automated worker processing where an authorized operational control exists. Preserve audit, outbox and database evidence. Do not delete, replay or downgrade.

### Identity or database outage

Use `CONTAIN_AND_ESCALATE`. Read `/health` and `/ready`, dependency details and bounded metrics. Do not bypass identity verification or database readiness.

### Worker retry or dead-letter growth

Use `CONTAIN_AND_ESCALATE`. Preserve dead-letter evidence. Automatic replay is prohibited; any replay requires a separate audited workflow and authority.

### Configuration regression

Use `REVERSE_CONFIGURATION` only with an approved non-secret before/after snapshot and proof that authentication, authorization, RLS, audit, rate limiting and safety remain enabled.

### Verified backup investigation

Use `ISOLATED_RESTORE_FOR_INVESTIGATION` only with a verified backup and separately named non-production target. Follow `docs/operations/observability-and-recovery.md`. Never restore over the source.

### Missing evidence or authority

Use `REFUSE_UNSAFE_ROLLBACK`.

## Commands

Focused policy and rehearsal tests:

```bash
uv run --locked pytest -W error backend/tests/test_release_rollback.py
```

Constrained repository rehearsal:

```bash
make rollback-verify
```

With an already migrated disposable PostgreSQL database, the command may inspect its actual migration head through `CAMPAIGNOS_RECOVERY_DATABASE_URL`. The database is read-only for this check.

The generated file is:

```text
artifacts/c3-ops-002/rollback-rehearsal.json
```

The receipt is owner-only, strict-schema JSON. It excludes credentials, arbitrary URLs, UUIDs, emails, request bodies, tenant/principal/campaign IDs and political content.

## Prohibited recovery shortcuts

- `alembic downgrade` as an automatic or default response;
- destructive SQL, `DROP DATABASE`, `DROP TABLE` or `TRUNCATE`;
- `pg_restore --clean` or restore over the source database;
- branch, tag, mutable image or `latest` as a previous-known-good artifact;
- disabling authentication, authorization, RLS, append-only audit, rate limiting or safety;
- automatic outbox or dead-letter replay;
- Terraform apply, image push or production operation under this runbook;
- deleting failed evidence or replacing it without an explicit supersession record.

## Evidence and communications

Record only:

- exact source and previous-known-good Git SHAs;
- scenario and migration classification;
- low-cardinality health decisions;
- selected and expected response;
- pass/fail evidence checks;
- cleanup result and limitations.

Do not put credentials, connection strings, tokens, cookies, emails, personal identifiers, campaign content or arbitrary external URLs into the receipt, issue, chat or operator log.

## Managed staging handoff

Before a production claim, an authorized isolated staging environment must prove:

- image digest promotion and provenance under the actual registry/runtime identity;
- migration compatibility from representative prior data;
- application rollback and forward-fix under managed networking and roles;
- scheduled backup, PITR and isolated restore;
- tenant/RLS, audit, rate-limit and worker behavior after recovery;
- alert routing, incident ownership and communication;
- measured and human-accepted RPO/RTO;
- security, privacy, legal and operational review;
- explicit production approval.

Until those receipts exist, `rollback-runbook` is at most `PARTIAL`, release stays `DENY_RELEASE`, and production stays `BLOCKED`.
