# Functional complete-campaign journey

Status: **VERIFIED ON THE CURRENT PRODUCT BASELINE FOR ISOLATED INTERNAL USE; PRODUCTION BLOCKED**

## User and job

The primary user is a campaign operator working inside an already authorized CampaignOS tenant. The current product can:

1. select an authorized campaign context or, with the separate tenant-scoped create grant, create an internal campaign draft;
2. complete persisted guided intake;
3. build the Candidate evidence dossier and current-version internal approvals;
4. organize Team roles, readiness records, Training Academy work and explicit human role coverage;
5. build evidence-first Strategy alternatives and record a version-bound human internal decision;
6. translate the decided strategy into Operations phases, workstreams, tasks, dependencies, blockers, decisions, follow-ups and learning;
7. record an immutable Daily War Room snapshot and reload persisted state.

The complete CI-equivalent journey validates all of those stages. No stage automatically creates political authority or an external campaign effect.

## Authority boundary

Navigation and visible controls are usability projections only. Every write is re-authorized by `/api/v1` against server-owned identity context and exact grants. The application validates tenant/campaign scope, action, resource, purpose, current version where required, and idempotency semantics.

Role labels never become permissions. The regular localhost operator seed contains **26 exact grants** for the current existing-campaign workflow. The isolated full-journey harness adds exactly one tenant-scoped campaign-create grant, for **27 total**, so campaign creation can be tested without making that authority implicit.

## Verified complete journey

The current browser harness verifies:

- same-origin frontend → API readiness;
- governed campaign draft creation with access unchanged;
- chapter routing and browser history;
- role blueprints, consultant role dossiers and operational Team board;
- template preview/deduplication/application;
- Candidate dossier `9/9` complete and current-version approved;
- Team readiness `8/8` plus authenticated human role coverage without new authority;
- Strategy `DECIDED_INTERNAL` through an explicit version-bound human decision;
- Operations roadmap, explicit human decision, learning record and Daily War Room snapshot;
- persistence after reload;
- ES/EN desktop, Spanish mobile, keyboard/reduced-motion behavior and zero automated WCAG 2.2 A/AA violations;
- no browser storage, unexpected outbound host, console error, page error or external effect.

## Political and external-effect boundary

The functional journey is internal preparation and governance. It does **not** authorize or autonomously perform:

- public political positioning;
- voter/citizen profiling or individual targeting;
- citizen contact;
- persuasion automation;
- publication;
- spending;
- field mobilization;
- Firmes synchronization;
- production deployment.

Those actions remain absent or separately human-gated.

## Local functional mode

`make functional-dev` starts the local PostgreSQL/API support stack, applies migrations, seeds the bounded 26-grant development operator for the deterministic existing campaign, and starts Next.js in live mode. It validates loopback ports first and reports any unique ephemeral replacements.

The browser never receives the development bearer token; Next server code uses it when calling the backend. The backend accepts that verifier only when `CAMPAIGNOS_ENVIRONMENT=development` and rejects combining it with OIDC. The versioned `.env.functional.example` values are local fixtures, not deployable credentials.

For the exact full-journey contract used by hosted CI, `scripts/frontend/e2e_functional_onboarding_host.sh` runs against an explicitly isolated `*_test` PostgreSQL database and adds the single campaign-create grant. It is a verification harness, not an operator deployment command.

Stop the Compose-backed local support stack with:

```bash
make functional-down
```

## Remaining limitations

- live OIDC provider login, account recovery, MFA, rotation and provider-operations evidence are not production-verified;
- trusted customer tenant provisioning/portfolio administration remains incomplete;
- no managed dev/staging/production runtime exists;
- rate limiting, observability, recovery and rollback controls are implemented/tested but not proven under a managed production edge/runtime;
- no managed backup/PITR or accepted RPO/RTO exercise exists;
- no independent security/privacy/legal/domain/operational acceptance or explicit production approval is recorded;
- the development identity is **not** shared/public/production authentication.
