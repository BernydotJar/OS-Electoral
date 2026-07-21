# CampaignOS identity lifecycle API

Status: **VERIFIED_POSTGRESQL_LOCAL — live provider integration remains absent**
Increment: `C3-IAM-002`
Last verified: `2026-07-21 America/Guatemala`

## Boundary

These routes manage CampaignOS application records after OIDC identity verification. They do not provision a live Cognito user, send email, revoke a provider token, grant political authority, publish, spend, contact citizens or deploy infrastructure.

Every privileged mutation requires a current server-owned tenant authorization context and an exact active grant matching action, resource type, resource identifier, campaign/workspace scope and purpose. Role labels are never authorization.

## Routes

| Route | Exact purpose | Preconditions and result |
|---|---|---|
| `POST /api/v1/tenants/{tenant_id}/identity/invitations` | `Invite tenant member` | Requires one `Idempotency-Key`; creates a bounded, expiring invitation, audit receipt and internal `identity.invitation.planned` outbox event. Delivery remains `NOT_SENT`. |
| `POST /api/v1/tenants/{tenant_id}/identity/invitations/{invitation_id}/accept` | verified invited identity | Requires one `Idempotency-Key`; verifies the token email and `email_verified=true`; accepts once and creates only an empty membership. No role or grant is inferred. |
| `POST /api/v1/tenants/{tenant_id}/identity/invitations/{invitation_id}/revoke` | `Revoke tenant invitation` | Requires exact invitation grant and expected version; transitions only a pending invitation. |
| `POST /api/v1/tenants/{tenant_id}/identity/sessions/current` | current verified identity | Registers or refreshes an application session using a digest of the provider session identifier. The raw identifier is not stored. |
| `POST /api/v1/tenants/{tenant_id}/identity/sessions/{session_id}/revoke` | self-revoke or `Revoke tenant application session` | Self-revoke is bound to the current principal; cross-principal revoke requires the exact grant and purpose. Provider revocation remains `NOT_EXECUTED`. |
| `POST /api/v1/tenants/{tenant_id}/identity/memberships/{membership_id}/revoke` | `Revoke tenant membership` | Requires expected version, bounded reason and exact grant; revokes effective grants, expires roles and revokes local application sessions atomically. |
| `POST /api/v1/tenants/{tenant_id}/identity/support-access` | `Request time-bound support access` | Requires one `Idempotency-Key`; binds requester, target, tenant, campaign/workspace, action, resource, purpose, reason and expiry. |
| `POST /api/v1/tenants/{tenant_id}/identity/support-access/{request_id}/approve` | `Approve time-bound support access` | Enforces separation of duty and expected version; creates or reactivates only lifecycle-owned, expiring exact authority. |
| `POST /api/v1/tenants/{tenant_id}/identity/support-access/{request_id}/revoke` | `Revoke time-bound support access` | Revokes the exact support grant and expires the exact support role. A pre-existing membership and unrelated access remain unchanged. |

## Idempotency and concurrency

Invitation create, invitation accept and support request bind tenant, normalized request, principal or verified identity, exact authorization evidence and purpose into replay identity. Equivalent requests replay committed evidence; changed intent or authority fails with a sanitized idempotency conflict.

PostgreSQL transaction advisory locks serialize equal idempotency keys. Partial unique indexes prevent concurrent active duplicate invitations and support requests. Explicit scope-key constraints prevent redundant campaign/workspace scope columns from drifting from their UUID owners.

## Expiry

Expired invitations, application sessions and support requests transition to `EXPIRED` and append an audit event when observed by the lifecycle. Expired rows no longer occupy active uniqueness slots. Expiring support access disables the exact grant; no broad role or tenant authority is manufactured.

## Errors

Responses use structured, sanitized problem details. The route layer maps denial, not-found, idempotency conflict, version conflict, lifecycle conflict and dependency failure without returning database constraint names, provider details, foreign-resource metadata or raw session identifiers.

## Provider-neutral invitation planning

`LocalInvitationPlanner` returns a no-delivery plan. `CognitoInvitationPlanner` produces a bounded `AdminCreateUser` request description only; no AWS SDK client is wired and no external call occurs. A real provider, email transport, recovery and MFA integration require separate reviewed increments and environment gates.
