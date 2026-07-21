# CampaignOS tenancy security

Status: **PARTIAL LOCAL POSTGRESQL/RLS FOUNDATION; application and staging proof incomplete**
Last updated: `2026-07-19`

## Hierarchy

```text
consultancy tenant
└── campaigns
    └── workspaces, members, roles, artifacts and approvals
```

Platform operations are a separate scope. They do not imply access to tenant or campaign content.

## Isolation contract

- A verified internal principal must have an active tenant membership.
- A campaign/workspace request must resolve that resource inside the same tenant before authorization.
- Every tenant-owned repository method requires an immutable scope object and places `tenant_id` in every predicate.
- Every campaign-owned operation also places `campaign_id`; workspace-owned operations also place `workspace_id`.
- Tenant/campaign IDs in request data are assertions to validate, never authority.
- Database constraints prevent cross-tenant foreign keys; RLS provides defense in depth.
- Background jobs, cache keys, object keys, exports, logs, metrics, and model context preserve the same scope.
- Bulk and administrative operations require explicit bounded target sets; an empty scope never means “all.”

## Lifecycle

Tenant provisioning is controlled and attributable. Offboarding blocks access, exports authorized data, applies retention/deletion policy, revokes integration/session credentials, and records completion. Campaign archival does not silently erase audit/consent/legal holds. Support access uses a separate time-bound approval flow.

## Verification

Isolation tests must run against real PostgreSQL using at least two tenants, two campaigns per tenant, multiple memberships, a revoked membership, a worker transaction, an export, and object-storage keys. Each test attempts reads, writes, relationships, counts, search, pagination, caches, jobs, audit queries, and error paths with valid foreign-scope identifiers.

The initial migration creates composite tenant/campaign/workspace relationships and enables and forces RLS on tenant-owned tables. The integration test proves two-tenant campaign visibility, cross-tenant write denial, active membership/exact-grant loading for tenant A and denial for the same verified identity in tenant B under a non-superuser, non-`BYPASSRLS` role. API tests also cover missing, expired, revoked and cross-campaign authorization state with sanitized 403/503 responses.

This is a bounded local proof. It does not yet cover campaign-domain object repositories, multiple simultaneous membership classes in PostgreSQL, workers, exports, object keys, caches, search/pagination, staging configuration or operational role rotation, so the production tenant-isolation gate remains `PARTIAL`.
