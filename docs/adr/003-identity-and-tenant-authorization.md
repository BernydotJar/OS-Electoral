# ADR 003: Separate OIDC authentication from tenant authorization

Status: **PROPOSED; initial verifier implemented, application authorization pending**
Date: `2026-07-19`

## Context

An OIDC provider can prove control of an external identity but cannot safely own CampaignOS tenant membership, campaign access, support elevation, or approval authority. Accepting token roles or client-supplied actor labels would enable privilege and cross-tenant confusion.

## Decision

Validate OIDC tokens using a fixed algorithm allow-list, signature, key identifier, issuer, audience, expiry, issued-at, not-before when present, and expected token use. Map the verified subject to an internal principal. Load active tenant membership, campaign/workspace access, and exact grants from CampaignOS persistence on each authorization-sensitive request or a short-lived revocable server session.

Authorization is deny-by-default over the tuple `(principal, tenant, campaign, workspace, action, resource, purpose, time)`. Approval receipts bind the authenticated principal and evaluated grant evidence. Token claims may be retained as identity metadata but never grant application roles directly.

## Consequences

- Identity configuration fails closed in staging and production.
- Invitation, recovery, MFA, revocation, membership expiry, support access, and session audit require explicit workflows.
- `/me` may expose identity and application membership separately; before membership persistence exists it must return no grants.
- Tests must cover algorithm confusion, bad keys/issuer/audience/time/use, revoked or expired membership, object-level authorization, and cross-tenant identifiers.
