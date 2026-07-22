# CampaignOS dynamic frontend

This directory contains the real server-rendered CampaignOS application shell. The legacy `../web/` surface remains a read-only visual reference until an explicit parity and archive review; the dynamic app does not import or execute its JavaScript.

## Runtime boundary

The App Router supports two explicit modes: a read-only synthetic review mode and a live server-side functional mode. The live mode currently supports authorized campaign selection plus guided-intake start/update.

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

Live mode fails closed when the API URL or verified session is absent. Shared and production environments require a non-local HTTPS API URL. For local development only, `make functional-dev` supplies a server-only development verifier and persisted exact grants; this path is rejected outside `development`.

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

`verify` runs ESLint, strict TypeScript, Vitest, a production Next build, and npm audit. Browser review is owned by `scripts/frontend/review_dynamic_shell.py` for read-only regression and `scripts/frontend/review_functional_onboarding.py` for the real PostgreSQL/API-backed journey. The functional review starts and updates guided intake, reloads the page, verifies persistence, and checks Spanish/English desktop plus Spanish mobile accessibility.

## Current limitations

- No live OIDC login, recovery, MFA, rotation, or provider revocation exists.
- The local development verifier is identity-only and not deployable authentication.
- Campaign creation, candidate/team/War Room mutations, administration, Training Academy and broader user journeys remain incomplete.
- This shell is local and review-branch evidence only. It is not deployed dev, staging, or production evidence.
