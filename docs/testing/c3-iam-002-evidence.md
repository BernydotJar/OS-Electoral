# C3-IAM-002 verification evidence

Verified: `2026-07-21 America/Guatemala`
Environment: isolated CampaignOS workstation, Python `3.14.6`, PostgreSQL `15.18`
Production status: `BLOCKED`

## Deterministic local gate

`make verify` passed on the active implementation worktree:

- Ruff lint: PASS.
- Ruff formatting: PASS across 66 backend files.
- strict mypy: PASS across 36 source files.
- pytest: `381 passed`, `3 skipped`.
- enforced coverage: `91.34%`, threshold `90%`.
- frontend regression: 12 Vitest tests, ESLint, strict TypeScript and Next.js production build PASS.
- npm audit: zero vulnerabilities.
- program-state validator: PASS while production remains blocked.
- eval-catalog validator: PASS before lifecycle reconciliation at `5 PASS / 10 PARTIAL / 18 NOT_RUN`.
- campaign safety scan: PASS.

## Identity-specific tests

The focused identity suite covers contracts, model transitions, API authorization/error mapping, OIDC claims and adversarial failure/rollback cases. New regression evidence includes:

- verified-email-only invitation acceptance;
- one-time acceptance and empty-membership creation;
- explicit persisted `EXPIRED` invitation/session/support states;
- replacement after expiry;
- no raw provider session identifier in persistence or audit;
- support separation of duty;
- preservation of a pre-existing membership and unrelated role/grant;
- support-owned membership revocation;
- repeated support cycles without duplicate active authority;
- database scope-key drift rejection;
- rollback after audit/persistence failures;
- sanitized integrity and lifecycle failures.

## PostgreSQL gate

A disposable `campaignos_integration_test` database was recreated. `make test-postgres` passed twice consecutively, each run reporting `3 passed`, `5 deselected`.

The selected tests cover:

- Alembic downgrade to base, upgrade to head and `alembic check`;
- revision `20260721_0004`;
- forced RLS policies for lifecycle tables;
- constrained runtime role with `NOSUPERUSER` and `NOBYPASSRLS`;
- cross-tenant invisibility and write rejection;
- equal-key invitation acceptance replay;
- distinct-key acceptance race with one success and one conflict;
- database duplicate-invitation and support-request boundaries;
- provider-session digest persistence without raw identifier;
- exact support grant effectiveness, revocation and a second support cycle;
- campaign-create regression under the same migration head.

## Independent critic findings repaired

1. The first expiration patch lacked direct persistence/replacement regressions; added explicit tests for all three lifecycle record types.
2. Invitation acceptance checked email equality but not OIDC `email_verified`; the principal model and verifier now validate and preserve that claim, and acceptance requires `true`.
3. Redundant scope keys could drift from UUID scope; database check constraints and corruption tests now fail closed.
4. A support-revoke regression now proves pre-existing membership, role and grant preservation.
5. New code initially reduced repository coverage to `87.35%`; adversarial error/rollback tests restored the enforced gate to `91.34%` without weakening the threshold.

## Limits

This is local and isolated PostgreSQL evidence, not Cognito, RDS, staging or production evidence. No external invitation, email, provider token revocation, infrastructure mutation, political effect or human production approval occurred.
