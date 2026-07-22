# CampaignOS dynamic frontend runtime

## Status

`C3-FRONT-001` introduces a local, server-rendered Next.js application shell. It is not a live-authentication, deployed-development, staging, or production claim.

The public `web/` directory remains the static `DEMO_NON_PRODUCTION` surface and a visual reference. The dynamic application lives in `frontend/` and does not import or execute the legacy JavaScript runtime.

## Classification of the legacy frontend

| Asset | Classification | Decision |
|---|---|---|
| Premium Slate visual language | `INTEGRATE` | Re-express tokens, spacing, hierarchy, responsive behavior, and governance language in typed React components. |
| Static HTML snapshots | `PRESERVE` | Keep as read-only reference until explicit parity review. |
| Legacy JavaScript state/runtime | `SUPERSEDE` | Do not import it into the production application shell. |
| GitHub Pages demo | `PRESERVE` | Manual-only, read-only, and never production evidence. |
| Legacy surface after parity | `ARCHIVE_AFTER_PARITY` | Requires human review and preserved historical evidence before any archive action. |

## Runtime trust boundary

```text
browser
  │
  │ no bearer token in JavaScript or browser storage
  ▼
Next.js server components
  │
  │ HttpOnly opaque access-token cookie
  │ no-store internal requests
  ▼
CampaignOS /api/v1
  │
  │ OIDC identity verification
  │ server-owned membership and exact grant evaluation
  ▼
PostgreSQL tenant transaction + forced RLS
```

The current shell reads these server-side cookies:

- `campaignos_access_token` — opaque token material, never rendered or stored client-side;
- `campaignos_tenant_id` — context selector only;
- `campaignos_campaign_id` — context selector only.

Tenant and campaign selectors never create authority. The backend remains authoritative and can deny, sanitize, or return a different visible set according to current memberships and grants.

## Server-only data access

`frontend/src/lib/api-client.ts` is protected by `server-only` and:

- sends bearer material only from the server;
- disables shared caching with `cache: "no-store"`;
- bounds requests with an explicit timeout;
- parses RFC 9457-style problems;
- maps malformed upstream JSON to `INVALID_UPSTREAM_RESPONSE`;
- never returns raw upstream error bodies to the browser.

`frontend/src/lib/contract-parsers.ts` validates runtime JSON rather than trusting TypeScript erasure. It rejects:

- unknown fields;
- malformed UUIDs;
- timezone-free timestamps;
- identity responses that smuggle memberships;
- workspace grants without campaign scope;
- campaign memberships containing cross-campaign grants;
- archived/closed campaign projections;
- campaign pages containing any item outside the requested tenant;
- non-canonical readiness checks;
- readiness summary/status contradictions;
- missing mandatory human-authority limitations.

## Navigation policy

Navigation is a usability projection only. `deriveNavigation` may reveal a module when a relevant current grant exists, but route visibility is never treated as permission. Every sensitive backend operation must independently match principal, tenant, campaign, workspace, action, resource, purpose, validity, and revocation state.

Only implemented, server-authorized destinations render as links. Missing modules such as Administration are omitted rather than presented as inert labels.

## Modes

### `live`

- requires `CAMPAIGNOS_API_BASE_URL`;
- requires a verified server-side session for protected content;
- supports authorized campaign selection plus guided-intake start/update through server-side POST boundaries;
- uses `If-Match` and `Idempotency-Key` for versioned writes;
- enforces same-origin browser submissions and re-authorizes every action in FastAPI;
- fails closed to unauthenticated, context-required, empty, conflict, validation or dependency-unavailable states;
- shared/production environments require a non-local HTTPS API.

A development-only verifier can be enabled for the local functional journey. It is mutually exclusive with OIDC, accepted only in the `development` environment, carries no roles or grants, and never exposes its token to HTML or browser storage. Exact grants remain persisted and server-owned.

### `demo_read_only`

- allowed only in `development` and `test`;
- uses fixed synthetic UUIDs;
- visibly identifies synthetic data and absence of a real campaign;
- contains no forms or domain-action buttons;
- is rejected in `shared` and `production` environments.

## Container boundary

`frontend/Dockerfile` uses:

- digest-pinned Node `22.23.1` Alpine base;
- exact npm lock installation;
- Next standalone output;
- telemetry disabled;
- UID/GID `10001` non-root runtime;
- no shell login for the application user;
- a bounded health check;
- only standalone server, static assets, and public assets in the runtime image.

The local nested Docker daemon cannot prepare the complete Compose stack in this sandbox namespace. The frontend image is nevertheless verified locally through `scripts/frontend/verify_frontend_image_buildah.sh`, using Buildah `1.28.2`, `vfs` storage, `chroot` isolation and Docker image format. The gate verifies UID/GID `10001:10001`, command, health-check metadata and an in-image synthetic-shell response. CI retains an independent Docker-engine build.

## External effects

The live onboarding journey can mutate only the internal guided-intake aggregate. It cannot:

- create or approve political decisions;
- publish content;
- spend funds;
- contact citizens;
- mobilize supporters;
- grant access;
- infer voter preference or persuadability.

All displayed readiness is operational setup only and explicitly not a human approval.
