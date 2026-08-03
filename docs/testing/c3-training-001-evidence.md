# C3-TRAINING-001 evidence

Status: `REVIEWED_LOCAL`; exact-head hosted review remains pending.

## Implemented boundary

- strict bilingual repository-owned catalog with six approved modules and paths;
- deterministic catalog digest and safe localized projection without answer keys;
- tenant/campaign assignment, progress, attempts, and append-only receipts;
- exact authorization, idempotency, optimistic versions, audit, outbox, and bounded limits;
- forced RLS for all three Training Academy tables;
- accessible Training Academy surface inside the Team chapter;
- real assign/start/attempt/receipt flow through server-owned frontend proxies;
- explicit `authority_effect=NONE` and `external_effects=NONE` throughout.

## Content and assessment verification

Focused catalog tests prove:

- Spanish/English structural and answer-key parity;
- deterministic SHA-256 catalog digest;
- rejection of raw HTML, remote URLs, unknown fields, unknown modules, and locale drift;
- answer keys absent from frontend catalog responses;
- deterministic pass/fail requiring every question exactly once;
- unknown option IDs fail closed.

The catalog paraphrases CampaignOS product, security, operations, and prior source-evaluation documentation. It does not copy the user-provided transcript and excludes person-level voter databases, persuasion scoring, microtargeting, and surveillance.

## Service and API verification

Focused tests cover:

- assignment creation and exact replay;
- active-principal and eligible-role validation;
- principal/campaign assignment limits;
- learner-only start and assessment;
- stale catalog, assignment, and progress versions;
- bounded failed attempt without a receipt;
- passing attempt with one receipt;
- no membership, role, or permission-grant mutation;
- exact grant action/resource/purpose/campaign checks before service invocation;
- required idempotency header;
- response scope and authority checks;
- public catalog without correct answer IDs.

## PostgreSQL 18 verification

The PostgreSQL gate upgrades and checks migration head `20260801_0013` and proves:

- forced RLS and one `tenant_isolation` policy on assignments, progress, and receipts;
- full assignment → start → pass flow under a `NOSUPERUSER NOBYPASSRLS` runtime role;
- another tenant cannot observe the assignment;
- `UPDATE` and `DELETE` on a completion receipt fail with SQLSTATE `42501`;
- migration and policy checks remain green with the existing repository suite.

## Frontend and browser verification

Frontend tests cover strict response parsers, scope escapes, authority drift, progress consistency, form field allow-lists, duplicate answers, demo read-only behavior, assignable paths, active lessons, and assessment rendering.

A clean production build and dynamic browser review prove:

- Training Academy is visible inside Team in ES/EN;
- the demo has no mutation controls;
- desktop, mobile, keyboard, reduced-motion, and WCAG checks remain green;
- no unexpected outbound hosts, page errors, or horizontal overflow.

The functional PostgreSQL/API/browser journey uses the real local seed and protected routes to:

1. load the seeded assignment;
2. start the module;
3. choose the reviewed answer;
4. submit the attempt;
5. observe the passing state and internal receipt;
6. verify the authority boundary and English projection.

## Privacy and authority review

The persisted learner record is minimal. Raw answer bodies, free-text learner profiles, rankings, psychological traits, and professional-accreditation claims are absent. Audit records retain bounded result counts, versions, receipt linkage, and authorization evidence—not selected answers.

Training creates no membership, role assignment, permission grant, publication, contact, spending, or mobilization effect.

## Remaining gates

- complete repository `make verify` on the final local tree;
- exact-head hosted PostgreSQL, browser, CodeQL, dependency, secret, SBOM/provenance, and stack checks;
- retained artifact inspection;
- independent PR review and human merge decision.

Managed environments, external LMS/provider integration, professional accreditation, and production approval remain absent and blocked.

## Hosted repair activation

The first hosted review exposed integration and verification defects after the stacked frontend base was merged: the Team shell had not rendered the academy surface, the PostgreSQL fixture omitted the required tenant version, multi-option form keys needed deduplication, and the API boundary tests did not provide enough coverage for the repository threshold. A guarded, one-shot repair runner on `main` is authorized only to apply those deterministic fixes, run focused checks, remove its branch-only payload, and publish a new exact head. Production and external effects remain blocked.

## Final main reconciliation

The repaired branch was reconciled with the merged frontend hierarchy and its Training scheduler projection was restored after independent critic review. A final pull-request CI completion now triggers the already validated one-shot reconciler so the latest `main` becomes an ancestor, the temporary runner is deleted from the Training tree, and the final exact-head review can run against the true merge base.
