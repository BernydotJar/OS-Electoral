# C3-TRAINING-001 primary-documentation checkpoint

Reviewed on 2026-08-01 before implementation. Only primary project and standards documentation was used.

## Pydantic

- `ConfigDict(extra="forbid")` is the strict boundary for rejecting unknown catalog, assignment, attempt and receipt fields.
- `frozen=True` is used for immutable projections and repository-owned content values.
- strict validation is preferred at trust boundaries so identifiers, versions and answers are not silently coerced.
- model validators enforce cross-field invariants such as locale parity, bounded questions and no authority effects.

## FastAPI

- hierarchical dependencies remain the shared authentication and tenant-authorization boundary.
- protected endpoints declare one rate-limit policy and then perform exact grant authorization before consuming the tenant budget.
- response models filter and validate all output, including catalog, assignment and receipt projections.

## SQLAlchemy and PostgreSQL 18

- one `Session.begin()` transaction owns assignment, progress, receipt, audit and idempotency changes; exceptions roll the unit of work back.
- every learner table is tenant/campaign scoped and uses forced PostgreSQL row-level security.
- RLS uses both `USING` and `WITH CHECK`; missing applicable policy is treated as default deny.
- cross-row guarantees use unique constraints, foreign keys, row locks and explicit service checks rather than CHECK constraints that inspect other rows.
- completion receipts are protected by the existing append-only trigger boundary.

## Next.js and React

- pages and data loading remain server components by default.
- client components are limited to assessment interaction and form state.
- lessons render reviewed structured text; no `dangerouslySetInnerHTML`, remote embed or arbitrary HTML is permitted.

## Accessibility

- every question has a programmatic label and clear instructions.
- validation feedback is concise, associated with the question and announced through status semantics.
- progress is exposed with native progress semantics and textual context.
- pass/fail feedback is educational and never a person ranking.

## GitHub Actions evidence

- workflow artifacts retain sanitized test and browser evidence after the job.
- artifacts are evidence, not a dependency cache.
- exact-head provenance, secret scanning and existing pinned-action policy remain mandatory.

## Implementation decision

No new runtime, frontend, cloud or paid dependency is required. The academy reuses Pydantic, FastAPI, SQLAlchemy, PostgreSQL, current authorization/audit/idempotency infrastructure, React/Next.js and the locked Playwright toolchain.
