# Public review parity evidence - 2026-08-12

## Scope

Localized repair of the CampaignOS public-review path. No Firmes sync, political execution, paid infrastructure, or production release is authorized.

## Root cause

The GitHub Pages workflow uploaded `./web`, while `frontend/README.md` defines `frontend/` as the real server-rendered CampaignOS application and the root `web/` surface as a legacy/read-only visual reference. The public Pages root could therefore be healthy while showing a different product surface from the current application.

## Repair

- GitHub Pages now assembles its artifact only from `web/marketing/`.
- The marketing source is copied to the Pages root and `/marketing/` only for URL compatibility.
- CI policy rejects a workflow that again uploads the legacy `./web` root.
- The interactive review surface continues to run from `frontend/`, not from copied legacy code.
- User-facing review UI no longer renders the word `demo`; the internal `demo_read_only` mode remains a safety mechanism and does not imply write authority.

## Functional verification

A local review stack was exercised against native PostgreSQL 15 because nested Docker image extraction is restricted in this sandbox. The same Alembic migrations and application role boundary were used.

Verified:

- Alembic upgraded to `20260801_0013` and `alembic check` reported no new operations.
- Local operator seed created the bounded tenant/campaign context and 17 exact grants.
- FastAPI `/api/v1/ready` returned `READY`.
- Next.js 16.2.11 live frontend returned HTTP 200.
- ESLint: PASS.
- TypeScript: PASS.
- Vitest: 36 files / 161 tests PASS.
- Next production build: PASS.
- Functional browser journey: PASS after a diagnostic-only run filtered one framework-owned Next development `sessionStorage` key named `__next_debug_channel:*`; no CampaignOS token or domain state was present in browser storage. The repository's stricter historical assertion was not weakened.
- The optimized Next standalone build was then started in live development configuration and exposed through an authenticated Cloudflare Quick Tunnel review proxy.
- Public review boundary: unauthenticated request returned `401`; authenticated request returned `200`; visible ES UI contained no `demo` wording.
- Public `Guardar cambios` round trip: PASS. The form submitted through the Cloudflare URL, the server returned the governed `intake_saved` redirect, the browser followed it successfully after reverse-proxy `Location` normalization, PostgreSQL persisted the new value, and a subsequent public-page reload returned the same value.
- Final standalone public-browser checks: browser `localStorage` and `sessionStorage` both empty; no console errors; visible `demo` text absent.
- Guided intake start/update, campaign draft isolation, team role/work-item persistence, ES/EN navigation, mobile layout, WCAG 2.2 AA axe review, console/page errors, and outbound-host checks: PASS.


## Zero-cost review transport

The verified review transport uses an account-less Cloudflare Quick Tunnel only as an ephemeral authenticated review URL. The tunnel terminates at a local Basic-Auth reverse proxy, which removes the review `Authorization` header before forwarding to the CampaignOS frontend. The proxy preserves the external host, sets forwarded HTTPS context, and normalizes absolute redirect locations back to the public HTTPS origin. No review credential is committed to the repository.

The current random `trycloudflare.com` hostname is intentionally not committed because Quick Tunnel hostnames change when the tunnel is recreated.

## Release boundary

This evidence proves a review surface and internal persistence path only. Production remains `BLOCKED`, release remains `DENY_RELEASE`, and external political effects remain `NONE`.
