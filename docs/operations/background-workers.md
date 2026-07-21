# Background worker runtime

CampaignOS currently provides a tenant-explicit transactional outbox worker. This is an internal reliability boundary, not an authorization to publish, contact citizens, spend funds, trigger field activity, or invoke third-party campaign systems.

## State machine

```text
PENDING -> PROCESSING -> DELIVERED
                    \-> PENDING (bounded exponential retry)
                    \-> DEAD_LETTER (attempt limit reached)
```

A claim uses `FOR UPDATE SKIP LOCKED`, increments `attempts`, and records `lease_owner` plus `lease_expires_at`. An expired `PROCESSING` lease is recoverable by another worker. Completion and failure transitions require the same worker lease.

The internal handler validates `campaign.updated`, `workspace.created`, and `agent.run.recorded` envelopes against tenant-scoped campaign, audit, workspace, and Agent Run evidence. It produces no network or political effect.

## Tenant scope

Workers never scan all tenants. Every pass receives one or more explicit tenant UUIDs, and every database transaction sets the tenant-local PostgreSQL RLS context. Tenant discovery and worker assignment remain an administrative control-plane responsibility.

## Local one-shot operation

```bash
make worker-once TENANT_ID=<tenant-uuid>
```

Equivalent command:

```bash
uv run --locked campaignos-worker --once --tenant-id <tenant-uuid>
```

For a long-running local process, omit `--once`. `SIGTERM` and `SIGINT` request graceful shutdown between bounded passes.

## Operational limitations

- No external event transport is configured.
- No SQS/EventBridge delivery exists yet.
- No automated tenant assignment exists yet.
- Dead-letter inspection and replay require a future human-audited administrative workflow.
- Production deployment remains blocked pending infrastructure, security, observability, backup/restore, and explicit human approval gates.
