# ADR 003: Separate OIDC authentication from tenant authorization

Status: **PROPOSED; verifier and tenant authorization loader implemented locally, lifecycle and domain enforcement pending**
Date: `2026-07-19`

## Context

An OIDC provider can prove control of an external identity but cannot safely own CampaignOS tenant membership, campaign access, support elevation, or approval authority. Accepting token roles or client-supplied actor labels would enable privilege and cross-tenant confusion.

## Decision

Validate OIDC tokens using a fixed algorithm allow-list, signature, key identifier, issuer, audience, expiry, issued-at, not-before when present, and expected token use. Map the verified subject to an internal principal. Load active tenant membership, campaign/workspace access, and exact grants from CampaignOS persistence on each authorization-sensitive request or a short-lived revocable server session.

Authorization is deny-by-default over the tuple `(principal, tenant, campaign, workspace, action, resource, purpose, time)`. Approval receipts bind the authenticated principal and evaluated grant evidence. Token claims may be retained as identity metadata but never grant application roles directly.

## Consequences

- Identity configuration fails closed in staging and production.
- Invitation, recovery, MFA, revocation, membership expiry, support access, and session audit require explicit workflows.
- `/api/v1/me` exposes verified identity only; `/api/v1/tenants/{tenant_id}/me` separately resolves current server-owned membership and grants.
- Tenant selection is untrusted input. It scopes the database transaction and must match the returned authorization context; it never creates authority.
- Current exact-grant matching includes action, resource type and identifier, campaign/workspace scope, purpose, validity and revocation state. Roles remain non-authoritative labels.
- Tests must cover algorithm confusion, bad keys/issuer/audience/time/use, revoked or expired membership, object-level authorization, and cross-tenant identifiers.
