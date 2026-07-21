# C3-ONBOARD-001 - Persisted guided campaign intake

- `status`: `VERIFIED_POSTGRESQL_LOCAL_ONLY`
- `branch`: `agent/c3-onboard-001-guided-intake`
- `base`: `agent/c3-iam-002-identity-lifecycle@fecb1d347389eebd08d04be6d38a3f518787e4e4`
- `production_status`: `BLOCKED`
- `external_effects`: none; intake records context and research needs only.

## Agent contract

```yaml
task_id: C3-ONBOARD-001
producer: Campaign Domain Engineer
critic: Product Safety and Authorization Reviewer
fixer: Backend and Frontend Engineer
independent_verifier: PostgreSQL, API and Accessibility Reviewer
objective: implement one persisted, resumable, exact-authorized guided intake that starts from campaign readiness and produces bounded research-first next actions without creating strategy or external effects
allowed_paths:
  - backend/src/campaignos/onboarding/
  - backend/src/campaignos/api/
  - backend/src/campaignos/data/
  - backend/migrations/
  - backend/tests/
  - frontend/
  - docs/product/
  - docs/api/
  - docs/testing/
  - program/
  - Makefile
read_only_paths:
  - RTK.md
  - web/
  - artifacts/c1-front-003/
prohibited_actions:
  - strategy generation
  - voter profiling
  - citizen contact
  - content production or publication
  - budget approval or spending
  - political approval
  - merge
  - force-push
  - deployment
```

## Functional contract

One campaign may own one guided intake. Start is idempotent and resumes the existing aggregate. Update uses optimistic versioning and purpose-bound idempotency. Read, start/resume and update are separately authorized.

The aggregate records only:

- target office;
- candidate-project summary;
- assessed current team;
- assessed current assets;
- budget-documentation status;
- known unknowns;
- evidence requirements.

Campaign name, jurisdiction, stage and active-workspace count remain server-owned campaign context.

## Canonical checks

1. campaign operational setup;
2. target office;
3. candidate project;
4. current team assessed;
5. current assets assessed;
6. budget evidence assessed;
7. known unknowns recorded;
8. evidence requirements defined.

Statuses:

- `BLOCKED_BY_CAMPAIGN_SETUP`;
- `IN_PROGRESS`;
- `READY_FOR_RESEARCH`.

`READY_FOR_RESEARCH` means only that the bounded intake is complete enough to begin evidence collection. It is not strategy, candidate approval, legal approval, budget approval or production approval.

## Acceptance criteria

1. A reversible migration adds one tenant/campaign-owned intake aggregate under forced RLS.
2. Start refuses a new aggregate until campaign operational readiness is complete.
3. A new idempotency key resumes an existing aggregate without creating a duplicate.
4. Same-key replay returns exact committed evidence; changed authority conflicts.
5. Read, start/resume and update require exact action/resource/purpose grants.
6. Update validates bounded normalized fields, rejects duplicate list entries and requires at least one changed field.
7. Optimistic versioning rejects stale writes.
8. Progress, next action and research-first actions are deterministic and canonical.
9. Audit evidence is appended for start, resume, read and update; only create/update emit internal no-effect outbox rows.
10. Audit or outbox failure rolls the transaction back.
11. Cross-tenant and cross-campaign access fails before persistence or remains invisible under RLS.
12. API errors are structured and sanitized; OpenAPI declares bearer, idempotency and version preconditions.
13. The dynamic shell validates the exact intake contract and shows progress, missing sections, research actions and mandatory limitations in ES/EN.
14. Unit, API, PostgreSQL, frontend, browser/accessibility, coverage, security and program gates pass.
15. Production remains `BLOCKED`; no output grants authority or external effect.

## Verification checkpoint

```yaml
verified_at: 2026-07-21 America/Guatemala
implementation_state: VERIFIED_POSTGRESQL_LOCAL_ONLY
branch_publication: PENDING
draft_pr: PENDING
ci: PENDING
full_suite:
  passed: 425
  skipped: 4
  coverage_percent: 91.58
frontend:
  vitest: 16
  lint: PASS
  strict_typescript: PASS
  production_build: PASS
  npm_vulnerabilities: 0
browser_accessibility:
  result: PASS
  axe_violations: 0
  console_errors: 0
postgresql:
  result: PASS
  selected: 4
  deselected: 5
  consecutive_runs: 2
security:
  actionlint: PASS
  pip_audit: PASS_ZERO_KNOWN_VULNERABILITIES
  gitleaks_effective_worktree: PASS
  gitleaks_stack_history: PASS
production_status: BLOCKED
external_effects: NONE
```

The Critic and Red Team closed two contract gaps before this checkpoint: source fields are now reconciled against every canonical check and reason code, and frontend navigation is bound to the exact selected campaign rather than any guided-intake grant. No CRITICAL or HIGH finding remains open inside this bounded slice.

Remaining limitations are the read-only mutation UX, live identity/tenant selection, customer acceptance, remote CI and all production environment/human gates.
