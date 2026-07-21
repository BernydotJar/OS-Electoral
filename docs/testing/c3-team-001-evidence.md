# C3-TEAM-001 verification evidence

Verified on 2026-07-21 in the persistent `/workspace` checkout. Production remains `BLOCKED`; no membership, role, permission grant, citizen contact, publication, spending, mobilization or other external effect was executed.

## Acceptance coverage

| Requirement | Evidence |
|---|---|
| reversible revision `20260721_0007` | migration and `backend/tests/test_database.py` |
| forced RLS and cross-tenant denial under `NOSUPERUSER NOBYPASSRLS` | `backend/tests/test_team_workspace_postgres.py` |
| one team workspace per tenant/campaign and candidate prerequisite | model and PostgreSQL tests |
| exact RACI with one accountable and at least one responsible | backend and frontend contract tests |
| active accountability only on filled roles | backend and frontend contract tests |
| availability, capacity, vacancies, onboarding and training | contracts, model and shell projection |
| recommendations scoped to campaign/workspace with `authority_effect=NONE` | contracts, API, PostgreSQL and frontend parser tests |
| zero automatic roles or permission grants | PostgreSQL assertions against `role_assignments` and `permission_grants` |
| exact create/read/update authorization | API tests with wrong action, purpose, resource, campaign and workspace scope |
| replay, optimistic concurrency and stable race conflicts | model and PostgreSQL tests |
| atomic audit, internal outbox and idempotency evidence | model and PostgreSQL tests |
| ES/EN non-technical read-only organization roadmap | frontend parser, i18n, navigation and browser review |

## Executed gates

```yaml
backend_static:
  ruff: PASS
  format: PASS
  mypy: PASS_48_SOURCE_FILES
focused_team_workspace:
  result: PASS
  passed: 47
full_locked_suite:
  result: PASS
  passed: 514
  skipped: 6
  coverage_percent: 91.48
  coverage_floor: 90
frontend:
  eslint: PASS
  strict_typescript: PASS
  vitest: PASS_34
  next_production_build: PASS
  npm_audit_vulnerabilities: 0
browser_wcag:
  result: PASS
  surfaces: [Spanish desktop, English desktop, Spanish mobile]
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
  selected_slices: 6
  migration_head: 20260721_0007
program:
  program_truth: PASS_PRODUCTION_BLOCKED
  campaign_safety: PASS
```

## Critic and Red Team repairs

1. Active `ACCOUNTABLE` and `RESPONSIBLE` assignments now require filled roles; vacant roles may only remain informed or consulted.
2. Campaign-scoped access recommendations require the campaign UUID as resource ID; workspace-scoped recommendations require the exact workspace UUID.
3. The frontend parser reconciles RACI, lifecycle, capacity, progress, status, limitations and `authority_effect=NONE` instead of accepting shape-only payloads.
4. Candidate and Team parser failures are converted to one sanitized `502 INVALID_UPSTREAM_RESPONSE` boundary.
5. Long mandatory governance codes wrap on mobile without truncation; the browser gate proves zero horizontal overflow.
6. PostgreSQL proves that Team Builder creates no application roles or permission grants.

No CRITICAL or HIGH finding remains open inside this bounded increment.

## Limitations

- The dynamic shell is read-only; authenticated non-technical editing remains future work.
- Role cards and access recommendations do not provision identity, membership or authorization.
- Training requirements are tracked, but a full Training Academy content runtime is not claimed.
- No live OIDC, customer acceptance, RDS, dev, staging or production runtime is claimed.
- Human review, merge and all production gates remain pending.
