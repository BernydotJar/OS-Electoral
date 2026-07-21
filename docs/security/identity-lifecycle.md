# Identity, session and time-bound support security model

Status: **PARTIAL — local and PostgreSQL controls verified; live identity operations absent**
Increment: `C3-IAM-002`
Last verified: `2026-07-21 America/Guatemala`

## Security invariants

1. OIDC authenticates external identity; application persistence owns authority.
2. Invitation acceptance requires a cryptographically verified token with the same normalized email and `email_verified=true`.
3. Invitation acceptance creates an empty membership only. Roles and grants require separate authorized administration.
4. Application sessions persist only a SHA-256 digest derived from issuer, subject and provider session identifier. Raw identifiers are not stored or returned.
5. Tenant, campaign, workspace, action, resource, purpose, validity and revocation state must match exactly.
6. Support access requires requester/target separation from the approver, bounded expiry, reason, exact scope and an approval receipt.
7. Support revocation or expiry cannot revoke a pre-existing membership or unrelated access.
8. Every successful lifecycle mutation and every persisted expiry is attributable and appended to the tenant audit stream.
9. Outbox rows are internal intent evidence, not proof of email delivery or provider execution.
10. Ambiguous, stale, missing, malformed or cross-scope state fails closed.

## Persistent records

- `identity_invitations`: tenant/campaign-bound, normalized email, provider-neutral reference, expiry, acceptance/revocation state and optimistic version.
- `application_sessions`: tenant/principal-bound digest, authenticated/last-seen/expiry timestamps, revocation state and optimistic version.
- `support_access_requests`: requester, target, exact scope/action/resource/purpose, reason, decision evidence, lifecycle-created authority references and optimistic version.
- `memberships.version`: optimistic revocation control.

All three new tables use forced PostgreSQL RLS. Scope-key check constraints and tenant-leading relationships reject inconsistent redundant scope. Runtime integration is exercised with a `NOSUPERUSER`, `NOBYPASSRLS` role.

## Support access ownership

A support approval may create an empty membership solely when the target has no membership in the exact scope. That ownership is recorded on the request. A later support cycle may reactivate only authority proven to belong to an earlier terminal support request. Existing non-support grants are never adopted or revived.

The support role name contains the request identifier, is expiring and does not authorize by itself. The exact `PermissionGrant` remains the sole effective permission evidence.

## Verified abuse cases

The tests cover wrong tenant, campaign and workspace; wrong action/resource/purpose; missing or disabled principal; wrong or unverified invitation email; invitation replay; stale versions; same-key replay; distinct-key races; self-approval; cross-principal session revocation without authority; duplicate active support; scope-key corruption; audit failure rollback; cross-tenant visibility and writes; expired authority; repeated support cycles; and preservation of unrelated access.

## Residual risks

- No live OIDC login, recovery, MFA, token rotation or provider revocation exists.
- No email is sent and no invitation secret/link lifecycle is integrated.
- Direct privileged database mutation can still alter audit rows; database-level append-only enforcement and external integrity anchoring remain open.
- No staging/RDS proof, customer-visible support-access UI, independent security/privacy approval or production incident drill exists.
- Rate limiting and production abuse controls remain incomplete across the API.

Production therefore remains `BLOCKED`.
