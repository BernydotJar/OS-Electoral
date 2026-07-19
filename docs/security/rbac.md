# CampaignOS RBAC and authorization policy

Status: **PARTIAL FOUNDATION; durable grant loading and endpoint enforcement absent**
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

The initial PostgreSQL schema now contains memberships, role assignments and permission grants, and the OIDC boundary refuses to treat token roles as application authority. The protected identity endpoint intentionally returns no memberships until a trusted loader exists. The production RBAC gate remains incomplete until those durable records are administered and loaded for endpoint/worker enforcement and the full matrix is implemented and reviewed.
