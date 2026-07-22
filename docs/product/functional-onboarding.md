# Functional campaign onboarding journey

Status: **VERIFIED LOCALLY AND ON POSTGRESQL; CI PENDING**

## User and job

The primary user for this slice is a non-technical campaign operator beginning work on an already authorized campaign. The journey lets that person:

1. see only campaigns visible to the verified tenant session;
2. choose the current campaign context;
3. start the persisted guided intake when an exact create grant exists;
4. enter starting information through an accessible Spanish/English form;
5. save with optimistic versioning and idempotency;
6. reload and continue from PostgreSQL state.

The journey does not create campaigns. Campaign creation is deferred until a separate access lifecycle can grant or request post-create access without deriving authority from labels.

## Authority boundary

Navigation and visible controls are usability projections only. Every write is re-authorized by `/api/v1` against server-owned membership and exact grants. The frontend requires exact matches for:

- tenant and campaign scope;
- action;
- resource type and resource ID;
- purpose;
- current version for updates;
- idempotency key.

Role labels never become permissions. The development role label is intentionally insufficient without the five exact seeded grants.

## Functional states

The UI distinguishes:

- selected campaign;
- intake not started;
- editable intake;
- read-only or unauthorized intake;
- validation error;
- version/idempotency conflict;
- missing resource;
- unauthenticated session;
- dependency failure;
- successful start and save.

A failed request never presents a partial-success message.

## Political and external-effect boundary

Saving guided intake records internal preparation only. It is not:

- strategy;
- public positioning approval;
- human political approval;
- voter or citizen assessment;
- profiling or individual targeting;
- citizen contact;
- publication;
- spending;
- mobilization;
- autonomous task execution.

Every downstream political or external action remains absent or separately human-gated.

## Local functional mode

`make functional-dev` starts the real local PostgreSQL/API stack, applies migrations, seeds a bounded development identity plus five exact grants, and starts Next.js in live mode. The browser never receives the development bearer token; it is used only by Next server code. The backend accepts it only when `CAMPAIGNOS_ENVIRONMENT=development` and refuses combining it with OIDC.

The versioned `.env.functional.example` values are local fixtures, not deployable credentials. Shared and production configurations reject the development identity.

Stop the local stack with:

```bash
make functional-down
```

## Remaining limitations

- no live OIDC/Cognito login, recovery or MFA;
- no trusted tenant portfolio-selection lifecycle;
- no campaign-creation/access-request journey;
- no human user-acceptance session recorded;
- no dev/staging deployment;
- no rate limiting or production observability;
- no production approval.
