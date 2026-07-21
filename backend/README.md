# CampaignOS API

This package is the production application boundary being built around the
validated, deterministic domain core. It currently provides:

- a FastAPI application factory;
- `/api/v1/health` and fail-closed `/api/v1/ready` endpoints;
- OIDC JWT verification using a fixed RS256 allow-list, issuer, audience,
  signature and time checks;
- `/api/v1/me` as a minimal identity projection;
- structured problem responses and correlation/security headers.

OIDC claims establish authentication only. Tenant membership, campaign access,
roles and permissions must come from the CampaignOS database; they are not
accepted from a bearer token. Until that persistence boundary is connected,
`/api/v1/me` returns no application memberships and `NOT_LOADED` authorization.

The API is not production-ready yet. PostgreSQL persistence, application
authorization, rate limiting, metrics and deployment infrastructure remain
explicit gates.
