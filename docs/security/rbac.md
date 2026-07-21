# CampaignOS RBAC and authorization policy

Status: **PARTIAL LOCAL IMPLEMENTATION; tenant grant loading exists, full enforcement and administration absent**
Last updated: `2026-07-19`

## Model

Authorization is deny-by-default and attribute-aware. A decision evaluates:

```text
verified principal
+ active tenant membership
+ active campaign/workspace scope
+ exact grant for action and resource class
+ purpose and contextual constraints
+ target identity/version
+ time and revocation state
```

A role is a managed bundle of candidate grants, not an authorization key. The server expands roles from application persistence; it never accepts effective roles from an OIDC claim, request body, query parameter, background message, or approval command.

## Minimum role catalog

The target catalog includes `platform_admin`, `tenant_owner`, `tenant_admin`, `consultancy_director`, `campaign_director`, `candidate`, `research_lead`, `strategy_lead`, `operations_lead`, `communications_lead`, `finance_lead`, `legal_reviewer`, `trainer`, `team_member`, `viewer`, and `integration_client`.

Each role must have a versioned, human-readable grant matrix. High-risk grants are kept separate even when normally assigned together:

- manage tenant membership and entitlement;
- grant or revoke roles;
- access sensitive evidence;
- approve public content;
- approve spending or paid media;
- approve field mobilization or citizen contact;
- export or delete data;
- manage integrations/secrets;
- elevate support access;
- approve environment promotion or production deployment.

## Enforcement rules

- Every API and worker command declares one action and one resource class.
- Scope comes from verified route/object relationships and server-side membership, never from role labels alone.
- Object lookup and authorization are composed to avoid leaking whether a foreign-scope object exists.
- Mutations authorize the current target version and use optimistic concurrency/idempotency where applicable.
- Sensitive reads produce an audit event without placing sensitive values in logs.
- Support access is separately approved, reasoned, time-bound, revocable, and audited.
- Integration clients have narrow machine grants and cannot inherit human approval authority.
- Platform administrators operate infrastructure; they do not automatically receive campaign-content access.

## Required tests

For each endpoint/action: unauthenticated; valid identity without membership; expired/revoked membership; wrong tenant; wrong campaign/workspace; correct role without exact grant; correct grant against wrong resource/version; client-forged role/actor; support expiry; integration-client misuse; and authorized success. Tests must use foreign IDs that exist to detect broken object-level authorization.

## Current runtime boundary

`/api/v1/me` remains an identity-only projection. `/api/v1/tenants/{tenant_id}/me` treats the path tenant as a selector, opens a transaction with that tenant's RLS scope, maps the verified OIDC issuer and subject to a server-owned principal, and returns only active memberships, unexpired roles and active exact grants. Suspended tenants, disabled principals, absent or expired memberships, mismatched campaign scopes, archived campaigns/workspaces and unavailable persistence fail closed with sanitized errors.

An effective permission matches action, resource type, resource identifier, tenant-selected campaign/workspace scope and purpose exactly. Role labels are returned for display and administration but never imply permission. The PostgreSQL integration test exercises the loader through a non-superuser, non-`BYPASSRLS` application role and denies the same identity in a tenant without membership.

The production RBAC gate remains `PARTIAL`: there is no membership/invitation administration workflow, reviewed role-to-grant catalog, support-elevation path, server session lifecycle, campaign-domain action endpoint, worker reauthorization, audit receipt emission or staging BOLA evidence.
