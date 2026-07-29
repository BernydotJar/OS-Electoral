# CampaignOS rate limiting and abuse protection

Status: **SHIP implementation under review; production remains blocked**
Feature: `C3-SEC-002`
Migration: `20260729_0012`

## Security boundary

CampaignOS assigns every protected API operation to one server-owned policy class:

| Policy class | Default pre-production budget | Current use |
|---|---:|---|
| `read` | 240 requests / 60 seconds | identity and bounded campaign/intake reads |
| `mutation` | 60 requests / 60 seconds | campaign, workspace and governed domain writes |
| `expensive_read` | 30 requests / 60 seconds | readiness and aggregated candidate/team/strategy/operations projections |
| `identity_lifecycle` | 20 requests / 300 seconds | invitation, session, membership and support lifecycle |
| `governed_agent_execution` | 10 requests / 300 seconds | create and read governed internal recommendation runs |

These defaults are policy configuration, not caller input. UI state, role names, request headers, campaign labels and client-selected context cannot create an exemption.

For tenant-scoped resources, the order is:

1. authenticate the principal;
2. resolve server-owned tenant authorization;
3. verify the exact action/resource/purpose grant;
4. consume the tenant/principal/policy budget;
5. execute the domain operation.

`/me` and invitation acceptance have no established application principal before execution. They use a fixed internal preauthorization scope and an opaque UUIDv5 derived from verified issuer and subject. Raw issuer, subject, email, display name, bearer token, IP address and request content are never written to the bucket.

## Persistence and isolation

`rate_limit_buckets` uses the primary key:

```text
(tenant_id, principal_id, policy_class, policy_version, window_start)
```

PostgreSQL determines the window from `transaction_timestamp()`. A single `INSERT ... ON CONFLICT DO UPDATE` increments the counter atomically across API processes. The stored count is capped at `request_limit + 1`; repeated rejected traffic cannot grow one row without bound.

The table has forced row-level security. `campaignos.tenant_id` binds `SELECT`, `INSERT`, `UPDATE` and `DELETE` to one transaction-local tenant. There is no public endpoint for bucket inspection or reset.

The preauthorization scope deliberately has no foreign key to a tenant or principal record. It is an internal security namespace, not a product tenant, membership or identity record.

## Privacy and prohibited uses

The executable policy classifies buckets as `INTERNAL`, `EPHEMERAL` security controls. They may be used only to enforce aggregate service budgets. They must not be used for:

- voter, supporter, volunteer or citizen profiling;
- political preference or persuadability inference;
- employee productivity, loyalty or covert behavior scoring;
- automatic account suspension, membership revocation or grant mutation;
- campaign strategy, audience selection or message targeting.

Metrics and structured events expose only policy class and outcome (`allowed`, `denied`, `unavailable`, `configuration_error`). Tenant IDs, principal IDs, IPs, raw counters and request payloads are prohibited labels.

## Fail-closed behavior

When enforcement is enabled and PostgreSQL is unavailable, protected operations return sanitized `503 RATE_LIMIT_UNAVAILABLE`. There is no permissive read fallback in this increment.

A denied budget returns `429 RATE_LIMIT_EXCEEDED` with `Retry-After`. The response includes the normal correlation ID but excludes the key, tenant, principal, count and limit.

Rate limiting is explicitly optional only in `development` and `test`. `staging` and `production` settings validation rejects `rate_limits_enabled=false`.

## Evidence and limitations

Local PostgreSQL proves atomic concurrency, forced RLS, cross-tenant isolation, class/principal/version separation, rollback and bounded cleanup. Route inventory tests require exactly one reviewed class and one enforcement call for all 41 protected source routes.

This is application-layer authenticated traffic protection. It does **not** provide edge DDoS mitigation, WAF policy, anonymous volumetric protection, production capacity sizing or staging load acceptance. Those remain separate platform and production gates.
