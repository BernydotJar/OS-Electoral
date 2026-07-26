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

The exact-head hosted API/PostgreSQL browser journey proved:

```text
lean map: 5 roles
full preview: 5 additions + 3 preserved canonical matches
mobile preview: one column and no overflow
confirmed full map: 10 roles
manual additional function: 11 roles
reload persistence, ES/EN, keyboard, axe and no external hosts
```

Local execution of that persistent journey remains blocked before product startup by the sandbox nested-Docker image-layer `lchown /var/empty` limitation. Hosted CampaignOS CI `30225102075` supplied the required PostgreSQL 18, Compose and browser evidence at implementation head `2130f2cd89711aedd710c1e363a4154a48ef5ecb`; Runtime Visual Review `30225102063` also passed.

## Authority and safety findings

- Preview is audited with principal, grant, approval receipt, purpose and correlation ID.
- Apply recomputes the preview under lock; client-provided additions are never accepted.
- Existing role IDs and data are preserved.
- Added roles are `VACANT`, with null principal, capacity and onboarding completion.
- No authorization table is written.
- Audit and outbox evidence record `authority_effect=NONE` and `external_effects=NONE`.
- Production remains `BLOCKED`; release remains `DENY_RELEASE`.


## Retained exact-head evidence

- frontend review: `8638357710`, `sha256:3b545067ed15110098981050aab7c3d6f70cd51bd2c4767e3a1512f8629fd3d6`
- PostgreSQL recovery: `8638329866`, `sha256:2885b536f549c38c8ebb3230837a720b413e1c88911f50f231ffeb5b942775ac`
- supply chain: `8638326099`, `sha256:1dde0e810e269220b1e6ffdd7174ce3ecf167d1d0fed273dd6e038a9209ffd69`
- visual review: `8638336015`, `sha256:c36014383c4db35779258fc6fbfe1c615e3dfbf37a5026a7f1ab899d4870170a`
- Gitleaks SARIF: `8638326247`, `sha256:4624bf468abbc7c35cbab9f691c0a0a0ebe4a9154397a2a9de5772c7049e1c69`
