# ADR 004: Layered PostgreSQL tenant isolation

Status: **PROPOSED; partial local implementation, application and staging proof pending**
Date: `2026-07-19`

## Context

CampaignOS stores operational and potentially sensitive political information for multiple consultancies and campaigns. A missing filter, reused session, forged identifier, or background-job error must not expose one tenant to another.

## Decision

Use PostgreSQL with non-null `tenant_id` on every tenant-owned row and `campaign_id` on campaign-owned rows. Repository interfaces require an immutable server-derived scope and include it in every query and mutation. Foreign keys and uniqueness rules include tenant scope where needed. Apply PostgreSQL row-level security to tenant-owned tables as defense in depth, with transaction-local scope set by a narrowly privileged application role.

Use SQLAlchemy 2.x request/job-scoped sessions and Alembic migrations. Never reuse a mutable ORM entity across scopes or requests. An application unit of work commits database state, append audit evidence, and outbox records atomically.

## Consequences

- Administrative maintenance uses separate, audited roles and cannot silently bypass application authorization.
- Connection-pool reset behavior and transaction-local scope require adversarial integration tests against real PostgreSQL.
- Migration tests must prove new tables, policies, indexes, constraints, and downgrade/forward-recovery policy.
- RLS is not a substitute for API authorization or object-level checks.
- Cross-tenant backup, restore, export, deletion, and incident procedures need explicit evidence.
