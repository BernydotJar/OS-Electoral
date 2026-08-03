# C3-TRAINING-001 review

Review state: `REVIEWED_LOCAL`.

## Producer

Implemented a repository-owned bilingual Training Academy with strict content contracts, six initial paths, exact-authorized assignment/progress/assessment APIs, PostgreSQL RLS, append-only receipts, and an accessible Team-chapter experience.

## Critic / red team

The focused review attempts:

- HTML, script, remote URL, and unknown-field content injection;
- Spanish/English structure and answer-key drift;
- unknown module/path references;
- answer-key disclosure to the frontend;
- stale catalog, assignment, and progress versions;
- missing/duplicate/mismatched idempotency;
- cross-tenant and cross-principal reads or completion;
- invalid option IDs, missing questions, duplicate answers, and attempt-limit bypass;
- authority effects, role/grant mutation, ranking, profiling, and accreditation claims;
- update/delete mutation of completion receipts.

Each path fails closed or remains explicitly outside the implementation.

## Local decisions

- Content integrity: PASS.
- Security and authorization: PASS in focused API/service tests.
- Data correctness: PASS in lifecycle and PostgreSQL 18 tests.
- Tenant isolation: PASS under forced RLS and NOBYPASSRLS role.
- Append-only completion evidence: PASS.
- Privacy/data minimization: PASS for the repository baseline.
- Accessibility/i18n: PASS in strict frontend tests and clean browser review.
- External effects: NONE.
- Production: `DENY_RELEASE` / `BLOCKED`.

## Independent verifier pending

Exact-head hosted CI and retained evidence must independently rerun the PostgreSQL, dynamic browser, functional browser, security, supply-chain, dependency, CodeQL, secret, and complete repository gates.

This review authorizes no merge, production deployment, cloud resource, paid service, external LMS, professional accreditation, voter profiling, targeting, publication, spending, contact, or mobilization.

## Final fixer verification

The final fixer closes two verification gaps rather than weakening gates: the development operator now receives the five exact Training Academy grants needed by the authenticated journey, and the browser creates its own assignment through the protected UI. Coverage is measured with two-decimal precision and passes at 90.03% with 862 tests. New adversarial cases prove another principal cannot submit the learner's assessment or read the learner's completion receipts. Hosted PostgreSQL and browser review remains required because the current sandbox cannot run the pinned PostgreSQL container image.
