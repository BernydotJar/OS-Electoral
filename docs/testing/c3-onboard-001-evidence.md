# C3-ONBOARD-001 verification evidence

Verified on 2026-07-21 in the persistent `/workspace` checkout on branch `agent/c3-onboard-001-guided-intake`. Production remains `BLOCKED`; no external campaign effect was executed.

## Acceptance coverage

| Requirement | Evidence |
|---|---|
| one tenant/campaign intake and reversible revision `20260721_0005` | `backend/migrations/versions/20260721_0005_guided_intake.py`, `backend/tests/test_database.py` |
| forced RLS and cross-tenant denial under `NOSUPERUSER NOBYPASSRLS` roles | `backend/tests/test_guided_intake_postgres.py`, disposable PostgreSQL gate |
| operational campaign prerequisites | `backend/tests/test_guided_intake_model.py::test_start_requires_operational_campaign_setup_without_partial_evidence` |
| exact-purpose authorization before adapter invocation | `backend/tests/test_guided_intake_api.py` |
| exact replay, distinct-key resume and authority-bound idempotency | `backend/tests/test_guided_intake_model.py`, `backend/tests/test_guided_intake_postgres.py` |
| optimistic concurrency and sanitized conflict behavior | model, API and PostgreSQL guided-intake tests |
| atomic audit, internal no-effect outbox and rollback | `backend/tests/test_guided_intake_model.py` |
| deterministic eight-check assessment and seven research actions | `backend/tests/test_guided_intake_contracts.py` |
| exact frontend runtime validation | `frontend/src/lib/contract-parsers.ts`, `frontend/src/lib/contract-parsers.test.ts` |
| current-campaign navigation projection | `frontend/src/lib/navigation.ts`, `frontend/src/lib/navigation.test.ts` |
| ES/EN, responsive, keyboard and WCAG surface | dynamic-shell browser review and i18n tests |

## Executed gates

```yaml
backend_static:
  ruff: PASS
  format: PASS
  mypy: PASS_40_SOURCE_FILES
focused_guided_intake:
  result: PASS
  passed: 44
full_locked_suite:
  result: PASS
  passed: 425
  skipped: 4
  coverage_percent: 91.58
  coverage_floor: 90
frontend:
  eslint: PASS
  strict_typescript: PASS
  vitest: PASS_16
  next_production_build: PASS
  npm_audit_vulnerabilities: 0
browser_wcag:
  result: PASS
  surfaces:
    - Spanish desktop
    - English desktop
    - Spanish mobile
  keyboard_skip_link: PASS
  reduced_motion: PASS
  horizontal_overflow: 0
  axe_wcag_22_a_aa_violations: 0
  unexpected_external_hosts: 0
  console_or_page_errors: 0
frontend_image:
  result: PASS
  mechanism: Buildah vfs/chroot daemonless
  runtime_uid_gid: 10001:10001
  health_and_smoke: PASS
postgresql:
  result: PASS
  engine: PostgreSQL 15 UTF8 disposable cluster
  selected: 4
  deselected: 5
  consecutive_runs: 2
  database: campaignos_integration_test
security_and_supply_chain:
  actionlint: PASS
  pip_audit: PASS_ZERO_KNOWN_VULNERABILITIES
  gitleaks_effective_worktree: PASS
  gitleaks_origin_main_to_head_commits: PASS_25_COMMITS
  git_diff_check: PASS
program:
  program_truth: PASS_PRODUCTION_BLOCKED
  campaign_safety: PASS
```

## Critic and red-team repairs

1. Runtime parsing originally reconciled check counts, status and actions but did not recompute each check from its source field. RED tests proved that `office=null`, an unassessed budget, empty known-unknowns or missing workspace readiness could be accepted while marked complete. The parser now recomputes all eight completion booleans and exact reason codes and fails closed on contradiction.
2. Intake navigation originally accepted the exact action/resource type/purpose but did not bind visibility to the selected campaign. RED tests proved that a grant for another campaign enabled the module. Navigation now additionally requires exact resource ID, campaign ID and null workspace scope for the current campaign.
3. Raw status codes were replaced as the primary user label with structurally matched Spanish and English descriptions while technical evidence remains available elsewhere.

No CRITICAL or HIGH finding remains open inside this bounded increment.

## Limitations

- The dynamic shell is read-only; an authenticated non-technical mutation flow for starting and editing intake remains future work.
- No live OIDC provider, customer tenant-selection workflow, RDS, dev, staging or production runtime is claimed.
- Research actions are instructions for evidence collection only; no agent runtime, web research, strategy generation or external execution occurs.
- Human review, merge, live environment verification and production approval remain pending.

## Remote and CI receipt

```yaml
implementation_commit: aa6fe239887173f3fb83366b640ad7b3121f361c
remote_sha: aa6fe239887173f3fb83366b640ad7b3121f361c
draft_pr: 92
base: agent/c3-iam-002-identity-lifecycle
merge_state: CLEAN
campaignos_ci:
  run_id: 29865306720
  conclusion: SUCCESS
runtime_visual:
  run_id: 29865306576
  conclusion: SUCCESS
```
