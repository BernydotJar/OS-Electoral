# C3-CANDIDATE-001 — Evidence-backed candidate workspace

- `workstream`: `WS-07`
- `status`: `VERIFIED_POSTGRESQL_LOCAL_ONLY`
- `branch`: `agent/c3-candidate-001-evidence-workspace`
- `base`: `agent/c3-onboard-001-guided-intake@05ed4b8825436d1c4cc9b3d35d2c57aeed71ec7c`

## Objective

Persist one campaign-scoped candidate evidence workspace that distinguishes self-report, independent evidence, perception, contradiction, development work, reputation risk and exact-authorized section review. Present a plain-language internal executive projection without approving strategy, public positioning, publication or external action.

## Preserve and harden

The deterministic `core/candidate_brand.py`, schema, fixtures and adversarial tests remain a read-only prototype reference. The production increment adds typed UUID contracts, PostgreSQL ownership, forced RLS, API authorization, concurrency, audit/outbox evidence and a dynamic-shell projection. It does not replace the legacy artifact until parity is demonstrated.

## Initial bounded model

- one candidate workspace per tenant/campaign;
- server-generated candidate and workspace UUIDs;
- evidence inventory with classification, status, source reference, authority and jurisdiction;
- identity, biography and purpose claims;
- values and attributes;
- contradictions;
- development goals;
- reputation risks;
- append-only section review receipts bound to the exact workspace version;
- deterministic readiness and next action;
- public use always blocked in this increment.

## Exact authorization purposes

```text
Create candidate evidence workspace
Review candidate evidence workspace
Maintain candidate evidence workspace
Approve candidate evidence section
```

Roles remain informational. Every operation must match principal, tenant, campaign, action, resource type, resource ID, purpose, validity and revocation state exactly.

## Acceptance criteria

1. Reversible migration adds candidate workspace and version-bound section review receipts under forced RLS.
2. Cross-tenant reads and writes fail under a `NOSUPERUSER NOBYPASSRLS` role.
3. Verified claims require accepted independent evidence from the same aggregate.
4. Candidate self-assessment alone cannot verify an attribute.
5. Perception evidence cannot independently verify a factual attribute.
6. Unknown references, duplicate IDs, oversized inputs and prohibited profiling fields are rejected.
7. Start, read and update are exact-authorized, audited, versioned and idempotent where applicable.
8. Update invalidates current approval completeness by advancing the workspace version; history remains append-only.
9. A section can be approved only when its exact evidence check is complete for the current version.
10. Open CRITICAL/HIGH reputation risks block internal approval readiness.
11. All successful writes append atomic audit and internal outbox evidence with `external_effects=NONE`.
12. API errors are sanitized and authorization failures occur before adapter invocation.
13. The frontend validates the complete projection and shows a plain-language read-only executive view in ES/EN.
14. Public positioning, content, outreach, spending, mobilization and voter profiling remain blocked.
15. Production remains `BLOCKED`.

## Prohibited actions

- voter-level or persuadability scoring;
- psychological or sensitive political profiling;
- automated political approval;
- public positioning approval;
- content generation or publication;
- citizen contact or mobilization;
- live external research or provider calls;
- merge, deployment, force-push or destructive persistent-data migration.

## Verification checkpoint

```yaml
verified_at: 2026-07-21 America/Guatemala
implementation_state: VERIFIED_POSTGRESQL_LOCAL_ONLY
branch_publication: PENDING
draft_pr: PENDING
ci: PENDING
full_suite:
  passed: 467
  skipped: 5
  coverage_percent: 91.67
frontend:
  vitest: 22
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
  consecutive_runs: 2
  revision: 20260721_0006
security:
  actionlint: PASS
  pip_audit: PASS_ZERO_KNOWN_VULNERABILITIES
  gitleaks_effective_worktree: PASS
  gitleaks_stack_history: PASS
production_status: BLOCKED
external_effects: NONE
```

Critic and Red Team closed semantic reference typing, replay-authority binding and approval rollback gaps before this checkpoint. No CRITICAL or HIGH finding remains open inside this bounded slice.

Remaining limitations are authenticated editing/approval UX, dedicated reviewer assignment and author/reviewer separation, live identity/tenant selection, customer acceptance, remote CI and all production environment/human gates.
