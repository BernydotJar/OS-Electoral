# C3-TEAM-003 evidence — governed template application

## Scope

This increment evolves an existing campaign team map through an authoritative preview and an append-only human-confirmed application. It creates organizational drafts only and never creates identity, capacity, membership, permission, access or external campaign effects.

## RED/GREEN record

Initial tests established that the repository had no canonical bilingual identity, no version-bound preview, no confirmation digest and no dedicated template-application route. The implementation then added:

- canonical lean/full blueprint keys shared across Spanish and English;
- deterministic proposed role IDs and SHA-256 preview receipts;
- exact-title/area fallback deduplication for historical cards;
- audited preview under exact update authorization;
- idempotent append-only application under row and audit-stream locks;
- rollback for stale version, digest drift and no-op application;
- server-rendered preview, impact summary, preserved-role explanation and explicit confirmation;
- responsive one-column behavior and fail-closed frontend parsers.

## Local validation

```text
focused backend template/API/model tests: 49 PASS
full Python suite: 724 PASS, 10 controlled skips
coverage: 90.37% (90% floor)
Ruff lint and format: PASS
strict mypy: PASS, 68 source files
frontend tests: 97 PASS across 20 files
ESLint: PASS
TypeScript: PASS
Next.js production build: PASS
npm audit: 0 vulnerabilities
```

The API-backed browser journey now proves the intended hosted sequence:

```text
lean map: 5 roles
full preview: 5 additions + 3 preserved canonical matches
mobile preview: one column and no overflow
confirmed full map: 10 roles
manual additional function: 11 roles
reload persistence, ES/EN, keyboard, axe and no external hosts
```

Local execution of that persistent journey remains blocked before product startup by the sandbox nested-Docker image-layer `lchown /var/empty` limitation. The exact-head hosted CI runner is required for PostgreSQL 18, Compose and browser evidence.

## Authority and safety findings

- Preview is audited with principal, grant, approval receipt, purpose and correlation ID.
- Apply recomputes the preview under lock; client-provided additions are never accepted.
- Existing role IDs and data are preserved.
- Added roles are `VACANT`, with null principal, capacity and onboarding completion.
- No authorization table is written.
- Audit and outbox evidence record `authority_effect=NONE` and `external_effects=NONE`.
- Production remains `BLOCKED`; release remains `DENY_RELEASE`.
