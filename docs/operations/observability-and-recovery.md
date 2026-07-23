# CampaignOS observability and recovery runbook

## Scope and safety boundary

This runbook covers the API, the internal outbox worker, PostgreSQL backup and isolated restore verification. It does not authorize deployment, Terraform apply, public communication, citizen contact, campaign execution, grant changes, or production release. Production remains `BLOCKED` until staging, security, privacy, operational and human gates are independently accepted.

Telemetry is operational evidence only. Correlation IDs, trace IDs, metrics, alerts and logs never grant access and never replace persisted permission grants or human approval receipts.

## Structured logs

The API and worker emit one JSON object per line. Every event includes:

- UTC timestamp, level, event, logger, service, version and environment;
- approved operational fields such as correlation ID, trace ID, server span ID, bounded route template, status and duration;
- no bearer tokens, request bodies, tenant IDs, campaign IDs, principal IDs, arbitrary URLs or exception messages.

Unexpected exceptions record only the exception type and the sanitized RFC 9457 response correlation ID. Operators must use the correlation and trace IDs to join application events without placing political or personal data in logs.

## Trace and correlation contract

`X-Correlation-ID` accepts a bounded safe identifier or is replaced with a server UUID. CampaignOS also accepts W3C version `00` `traceparent` values. A valid trace ID is continued with a new server span; malformed or all-zero identifiers are discarded. Both identifiers are returned to the caller and included in the structured completion event.

The current increment provides trace-context propagation and correlated structured spans at the API boundary. A future staging increment must select and approve an OTLP collector, retention, residency and processor contract before any exporter is enabled.

## Metrics access

`GET /api/v1/metrics` publishes Prometheus text format with bounded labels only:

- build and process start information;
- active requests;
- request totals by method, route template and status;
- request duration histogram;
- dependency readiness;
- bounded SQLAlchemy pool state.

Set `CAMPAIGNOS_METRICS_ENABLED=false` to disable the endpoint. `CAMPAIGNOS_METRICS_BEARER_TOKEN` protects it with constant-time bearer-token verification. Staging and production configuration fails closed when metrics are enabled without a token of at least 24 characters. The token is a scrape credential only and confers no product authority.

The outbox worker can publish a Prometheus textfile using `--metrics-file`. Backup/restore verification publishes `campaignos-recovery.prom`. A staging telemetry agent may collect those files after its filesystem, identity and retention controls are reviewed.

## Dependency readiness

Alert: `CampaignOSDependencyNotReady`.

1. Confirm `/health` remains `UP`; otherwise treat the process as unavailable.
2. Inspect `/ready` and identify the failed dependency without copying credentials into tickets or chat.
3. For identity failure, verify JWKS reachability, issuer/audience configuration and clock health.
4. For database failure, verify managed database availability, TLS, pool saturation and migration state.
5. Do not bypass readiness or switch to development identity in a shared environment.
6. Record the incident, correlation window, human owner and recovery evidence.

## HTTP errors

Alert: `CampaignOSHighHttpErrorRate` when 5xx exceeds two percent for ten minutes.

1. Compare error rate with latency, readiness and pool metrics.
2. Search structured events by trace/correlation ID and bounded route, not by citizen or campaign data.
3. Roll back only through the approved release procedure and exact artifact receipt.
4. Keep write APIs fail closed if authorization, persistence or idempotency evidence is uncertain.

## Latency

Alert: `CampaignOSHighRequestLatency` when p95 exceeds one second for ten minutes.

1. Check database pool checked-out/overflow values and managed database metrics.
2. Separate one slow bounded route from system-wide saturation.
3. Do not increase pool limits without checking database connection capacity and cost.
4. Capture before/after metrics and human approval for any runtime configuration change.

## Outbox dead letter

Alert: `CampaignOSOutboxDeadLetterDetected`.

1. Stop automated retries for the affected event after the bounded retry policy has completed.
2. Inspect internal event type, attempts and sanitized failure class under exact tenant authorization.
3. Never replay through an external transport; CampaignOS currently has no external delivery transport.
4. Require a separate human-audited replay workflow before clearing dead-letter evidence.

## Native backup and isolated restore

The repository command is:

```bash
CAMPAIGNOS_RECOVERY_DATABASE_URL='postgresql+psycopg://...' make recovery-verify
```

The verifier is deliberately limited to a source database whose name ends in `_test`; it is a recovery proof and cannot be pointed at production. It:

1. requires a pinned PostgreSQL client container by default;
2. requires client and server major versions to match;
3. reads the source through native `pg_dump` custom format;
4. validates the archive catalog;
5. creates only a separately named `*_restore_test` database;
6. restores with owner and ACL replay disabled;
7. compares Alembic version and every public-table row count;
8. writes a SHA-256 manifest and Prometheus recovery metrics;
9. removes the isolated restore database in `finally` unless an operator explicitly retains it for investigation.

The verifier refuses a mutable client image, malformed Git revision, unsafe target name, or a target equal to the source. Passwords are supplied through the process environment and are not included in the manifest or command output. Backup and manifest files are created with owner-only permissions.

The CI job `PostgreSQL backup and isolated restore` performs this proof against PostgreSQL 18.3 with representative migrated and seeded rows. Its retained artifact is test evidence, not a production backup.

## Backup staleness

Alert: `CampaignOSBackupStale` after 26 hours without successful evidence.

1. Confirm whether the scheduler, database or encrypted destination failed.
2. Do not delete the last known-good backup while investigating.
3. Run a new backup only through the approved service identity and encrypted destination.
4. Verify checksum, retention lock and inventory receipt.
5. Keep production release blocked if the accepted recovery point objective is not demonstrated.

## Restore staleness

Alert: `CampaignOSRestoreVerificationStale` after eight days without an isolated restore proof.

1. Restore into an isolated non-production database with no public ingress.
2. Run schema, row-count, application smoke and authorization/RLS checks.
3. Destroy the restored database after evidence capture unless incident review requires retention.
4. Record measured restore duration and compare it with the human-approved recovery time objective.

## Staging requirements not satisfied by local or CI evidence

Before production, staging must prove all of the following with retained receipts:

- managed PostgreSQL encryption, automated backups, point-in-time recovery and deletion protection;
- an approved backup destination, KMS policy, retention schedule and restore operator role;
- scheduled backup and restore verification using non-production data;
- telemetry transport, authenticated scraping, alert routing and on-call ownership;
- log/metric/trace retention, residency, access review and deletion policy;
- failure injection for database outage, identity outage, pool exhaustion, stale migration, worker retry/dead letter and rollback;
- measured and human-approved RPO/RTO;
- security and privacy review with no voter profiling, citizen targeting or external campaign effects.

Passing repository tests or CI does not satisfy these staging and human gates.
