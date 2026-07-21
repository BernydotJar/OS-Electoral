# CampaignOS dynamic frontend

This directory contains the real server-rendered CampaignOS application shell. The legacy `../web/` surface remains a read-only visual reference until an explicit parity and archive review; the dynamic app does not import or execute its JavaScript.

## Runtime boundary

The App Router shell is intentionally read-only in this increment.

- Bearer material is read only from the server-side `campaignos_access_token` HttpOnly cookie.
- The browser never receives the token and no token is stored in local or session storage.
- `campaignos_tenant_id` and `campaignos_campaign_id` cookies select context only. The backend remains authoritative and re-evaluates tenant membership and exact grants.
- Navigation visibility is a usability projection from server-owned grants. It is not an authorization decision.
- No route publishes, spends, contacts citizens, mobilizes, grants access, or records political approval.

## Modes

### Live

```bash
CAMPAIGNOS_FRONTEND_MODE=live
CAMPAIGNOS_FRONTEND_ENVIRONMENT=development
CAMPAIGNOS_API_BASE_URL=http://127.0.0.1:8000
npm run dev
```

Live mode fails closed when the API URL or verified session is absent. Shared and production environments require a non-local HTTPS API URL.

### Synthetic read-only demo

```bash
CAMPAIGNOS_FRONTEND_MODE=demo_read_only
CAMPAIGNOS_FRONTEND_ENVIRONMENT=test
npm run dev
```

Demo mode uses fixed synthetic UUIDs and visibly labels every page. Configuration rejects demo mode in `shared` and `production` environments.

## Verification

```bash
npm ci
CAMPAIGNOS_FRONTEND_MODE=demo_read_only \
CAMPAIGNOS_FRONTEND_ENVIRONMENT=test \
NEXT_TELEMETRY_DISABLED=1 \
npm run verify
```

`verify` runs ESLint, strict TypeScript, Vitest, a production Next build, and npm audit. Browser review is owned by `scripts/frontend/review_dynamic_shell.py` and exercises the production build in Spanish and English on desktop, mobile, keyboard, and reduced-motion contexts.

## Current limitations

- No live OIDC login, invitation, recovery, rotation, or revocation lifecycle is implemented.
- There is no tenant portfolio endpoint, so live tenant selection must be provisioned by a trusted server-side session workflow.
- Campaign create/update UI, guided intake, team, War Room, evidence workflows, administration, and Training Academy remain future increments.
- This shell is local and review-branch evidence only. It is not deployed dev, staging, or production evidence.
