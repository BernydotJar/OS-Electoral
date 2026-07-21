# C3-STRATEGY-001 verification evidence

Verified on 2026-07-21 in the persistent `/workspace` checkout. Production remains `BLOCKED`. No voter profiling, targeting, citizen contact, publication, spending, mobilization, provider call, merge, or deployment occurred.

## Acceptance evidence

| Requirement | Evidence |
|---|---|
| reversible revision `20260721_0009` | migration, metadata test, PostgreSQL gate |
| one workspace per tenant/campaign under forced RLS | SQL model, migration, SQLite and PostgreSQL tests |
| append-only decision receipt per exact version | contracts, SQL lifecycle and concurrency tests |
| verified/inferred/unknown provenance separation | backend and frontend parser tests |
| falsifiable hypotheses and comparable options | deterministic contracts and Decision Room UI |
| measurable objective with Team Builder owner | contract, SQL and frontend reconciliation tests |
| contradiction/red-team blockers | contract and parser adversarial tests |
| exact create/read/update/approve authorization | API wrong-action/purpose/resource/scope tests |
| optimistic versioning and exact idempotent replay | model, SQL and PostgreSQL race tests |
| atomic audit, internal outbox and idempotency | SQLite/PostgreSQL counts and rollback assertions |
| ES/EN read-only Decision Room | parser, i18n, navigation, build and browser gate |
| no profiling or external authority | prohibited-field validation, API drift checks and UI limitations |

## Executed gates

```yaml
backend_static:
  ruff: PASS
  format: PASS
  mypy: PASS_57_SOURCE_FILES
focused_strategy:
  result: PASS
  passed: 37
full_locked_suite:
  result: PASS
  passed: 585
  skipped: 8
  coverage_percent: 90.70
  coverage_floor: 90
frontend:
  eslint: PASS
  strict_typescript: PASS
  vitest: PASS_48
  next_production_build: PASS
  npm_audit_vulnerabilities: 0
  sharp_override: 0.35.3
browser_wcag:
  result: PASS
  surfaces: [Spanish desktop, English desktop, Spanish mobile]
  keyboard_skip_link: PASS
  reduced_motion: PASS
  horizontal_overflow: 0
  axe_wcag_22_a_aa_violations: 0
  browser_storage: EMPTY
  unexpected_external_hosts: 0
  console_or_page_errors: 0
frontend_image:
  result: PASS
  builder: Buildah vfs/chroot daemonless
  runtime_uid_gid: 10001:10001
  health_and_smoke: PASS
postgresql:
  result: PASS
  consecutive_combined_runs: 2
  selected_slices: 8
  migration_head: 20260721_0009
  strategy_proofs:
    - equal-key concurrent replay
    - update race with one stable version conflict
    - one decision receipt per exact version
    - forced RLS under NOSUPERUSER NOBYPASSRLS
    - cross-tenant read and write denial
program:
  program_truth: PASS_PRODUCTION_BLOCKED
  eval_catalog: PASS
  campaign_safety: PASS
```

## Critic and Red Team findings closed

1. Unknown evidence cannot claim source, authority, jurisdiction, or verified status.
2. Rejected evidence cannot support a decision option.
3. Unknown references, duplicate IDs, prohibited profiling keys, stale decisions, and inconsistent derived counts fail closed in both runtimes.
4. Decision readiness requires two complete options, measurable objectives, no unresolved contradiction, and no open HIGH/CRITICAL finding.
5. The decision action requires an exact `approve` grant, current `If-Match`, selected declared option, known Team Builder role, and approval receipt.
6. Any strategy update creates a new version and invalidates current decision completeness while preserving historical receipts.
7. Concurrent equal-key writes replay exactly; concurrent versioned writes yield one success and one stable conflict.
8. Forced RLS denies cross-tenant access under a constrained PostgreSQL role.
9. Audit, outbox, idempotency and decision records roll back atomically when governance validation fails.
10. Invalid Strategy upstream responses become sanitized `502 INVALID_UPSTREAM_RESPONSE` errors.
11. The browser exposes no mutation or execution control and labels the Decision Room as internal evidence only.
12. `authority_effect=NONE` and `external_effects=NONE` are enforced through domain, adapter, API and frontend validation.

No CRITICAL or HIGH finding remains open inside this bounded increment.

## Limitations

- The browser surface is read-only; authenticated non-technical editing and decision submission UI are not implemented.
- An internal decision receipt is not public strategy, positioning, legal, content, publication, spending, targeting, contact, or mobilization approval.
- No live OIDC, cloud environment, telemetry, customer acceptance, merge, or deployment is claimed.
- Draft PR `#96` still requires a corrected published head and green CI before `CI_GREEN` may be recorded.
