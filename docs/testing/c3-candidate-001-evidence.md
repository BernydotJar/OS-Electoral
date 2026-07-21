# C3-CANDIDATE-001 verification evidence

Verified on 2026-07-21 in the persistent `/workspace` checkout on branch `agent/c3-candidate-001-evidence-workspace`. Production remains `BLOCKED`; no external campaign effect was executed.

## Acceptance coverage

| Requirement | Evidence |
|---|---|
| reversible revision `20260721_0006` | `backend/migrations/versions/20260721_0006_candidate_workspace.py`, `backend/tests/test_database.py` |
| forced RLS and cross-tenant denial under `NOSUPERUSER NOBYPASSRLS` | `backend/tests/test_candidate_workspace_postgres.py` |
| guided-intake-ready prerequisite | `backend/tests/test_candidate_workspace_model.py` |
| independent evidence and self-assessment boundary | `backend/tests/test_candidate_workspace_contracts.py` |
| semantic perception and contradiction references | backend and frontend candidate contract tests |
| exact replay, authority binding and stable race conflict | model and PostgreSQL candidate tests |
| optimistic concurrency and append-only version approvals | model, API and PostgreSQL candidate tests |
| atomic audit/outbox/idempotency rollback | `backend/tests/test_candidate_workspace_model.py` |
| exact API authorization and adapter-drift rejection | `backend/tests/test_candidate_workspace_api.py` |
| complete frontend runtime reconciliation | `frontend/src/lib/candidate-contract-parser.ts` and tests |
| current-campaign navigation projection | `frontend/src/lib/navigation.ts` and tests |
| ES/EN, responsive, keyboard and WCAG executive surface | browser review and i18n tests |

## Executed gates

```yaml
backend_static:
  ruff: PASS
  format: PASS
  mypy: PASS_44_SOURCE_FILES
focused_candidate_workspace:
  result: PASS
  passed: 42
full_locked_suite:
  result: PASS
  passed: 467
  skipped: 5
  coverage_percent: 91.67
  coverage_floor: 90
frontend:
  eslint: PASS
  strict_typescript: PASS
  vitest: PASS_22
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
  consecutive_runs: 2
  database: campaignos_integration_test
  migration_head: 20260721_0006
security_and_supply_chain:
  actionlint: PASS
  pip_audit: PASS_ZERO_KNOWN_VULNERABILITIES
  gitleaks_effective_worktree: PASS
  gitleaks_origin_main_to_head: PASS
  git_diff_check: PASS
program:
  program_truth: PASS_PRODUCTION_BLOCKED
  campaign_safety: PASS
```

## Critic and Red Team repairs

1. Attribute `contradiction_refs` initially resolved against evidence records. RED tests proved the semantic mismatch. Backend and frontend now require those references to identify candidate contradiction records.
2. `perception_refs` initially enforced `PERCEPTION` classification only when citizen evidence was not unresolved. Every populated perception reference now requires that classification regardless of summary state.
3. Replay is proven bound to exact authority and intent; changing a grant or approval reason under the same key produces a stable idempotency conflict.
4. Synthetic audit failure during section approval proves that receipt, outbox and idempotency evidence roll back atomically.
5. Current-campaign navigation requires exact resource ID, campaign ID, null workspace scope, read action and review purpose.

No CRITICAL or HIGH finding remains open inside this bounded increment.

## Limitations

- The dynamic shell is read-only; authenticated non-technical editing and approval controls remain future work.
- Dedicated reviewer assignment and author/reviewer separation are not yet modeled; exact approval permission and immutable receipts are enforced, but this remains a governance enhancement before real campaign use.
- No live OIDC provider, customer tenant-selection workflow, RDS, dev, staging or production runtime is claimed.
- Internal approval never authorizes public positioning, strategy, content, contact, spending or mobilization.
- Draft PR, exact remote SHA and CI evidence must be added after publication.
