# C3-FRONT-002 functional onboarding evidence

Verified on 2026-07-22 from `agent/c3-front-002-functional-onboarding`, based on Security receipt `e0b4b5df711f671e8f6a1f711a0a3beff39cf173`.

Production remains `BLOCKED`; external effects remain `NONE`.

## Functional proof

The live E2E uses a disposable PostgreSQL database ending in `_test`, applies every migration through `20260721_0011`, starts the real FastAPI application under a `NOSUPERUSER`/`NOBYPASSRLS` runtime role, starts the production Next standalone server and drives Chromium through the following sequence:

```text
verified development identity
→ server-owned tenant membership and five exact grants
→ authorized campaign projection
→ start guided intake
→ audit/outbox/idempotency evidence committed
→ update all intake fields with If-Match and Idempotency-Key
→ new version returned
→ browser reload
→ persisted values projected from PostgreSQL
```

Observed result:

```yaml
journey: campaign_select_start_and_update_guided_intake
result: PASS
persistence_after_reload: PASS
exact_authorization_controls: PASS
administration_placeholder: ABSENT
desktop_spanish: PASS
desktop_english: PASS
mobile_spanish: PASS
wcag_2_2_aa: PASS_ZERO_AXE_VIOLATIONS
horizontal_overflow: NONE
browser_storage: EMPTY
unexpected_outbound_hosts: []
console_errors: []
page_errors: []
external_effects: NONE
```

The HTML and browser storage contain no development bearer token. The demo mode contains no mutation controls.

## Deterministic gates

```yaml
backend:
  ruff: PASS
  format: PASS_130_FILES
  mypy: PASS_63_SOURCE_FILES
  full_suite:
    passed: 658
    skipped: 10
    coverage_percent: 90.92
frontend:
  lint: PASS
  strict_typescript: PASS
  vitest: PASS_60
  build: PASS
  npm_audit_vulnerabilities: 0
  routes:
    - /api/ui/campaign-context
    - /api/ui/guided-intake/start
    - /api/ui/guided-intake/update
postgresql:
  selected_slices: 10
  consecutive_runs: 2
  migration_head: 20260721_0011
browser_demo_read_only:
  result: PASS
  desktop_spanish: PASS
  desktop_english: PASS
  mobile_spanish: PASS
  keyboard_skip_link: PASS
  reduced_motion: PASS
  wcag_2_2_aa: PASS_ZERO_AXE_VIOLATIONS
browser_live_functional:
  result: PASS
  start_update_reload: PASS
  desktop_spanish: PASS
  desktop_english: PASS
  mobile_spanish: PASS
  wcag_2_2_aa: PASS_ZERO_AXE_VIOLATIONS
frontend_image:
  result: PASS
  builder: Buildah_1.28.2_vfs_chroot
  runtime_user: 10001:10001
security:
  actionlint: PASS
  pip_audit_hash_locked: PASS_ZERO_KNOWN_VULNERABILITIES
  npm_audit: PASS_ZERO_VULNERABILITIES
  gitleaks_effective_worktree: PASS
  gitleaks_history_before_commit: PASS
terraform:
  version: 1.15.8
  linux_arm64_sha256: 8891e9dcedc9e3b8950bc6af9d4d8af1f4cfade3062f53b9dc403a89f6ce8c9c
  bootstrap_mock_plan: PASS
  platform_mock_plan: PASS
  apply: NOT_PERFORMED
program:
  truth: PASS_PRODUCTION_BLOCKED
  open_critical_high: 2
  retained_failed_runs: 6
```

## Critic and Red Team conclusions

1. The development verifier proves identity only and cannot carry roles or grants.
2. Development identity is rejected outside `development` and cannot coexist with OIDC configuration.
3. The token is compared in constant time, never rendered, never placed in browser storage and represented in session evidence only by a digest.
4. The seed refuses remote/non-development database URLs and creates only five exact grants for the bounded journey.
5. Role labels do not enable a control; exact action/resource/purpose/campaign/workspace matching is required.
6. Same-origin validation rejects missing, malformed, cross-host and cross-protocol origins.
7. Locale middleware cannot intercept `/api/ui/*` mutation routes.
8. Campaign selection accepts only a campaign already returned by the tenant-scoped API.
9. Guided intake start and update are independently re-authorized by FastAPI and PostgreSQL RLS.
10. Update uses the current version and stable idempotency key; conflicts never overwrite silently.
11. Unknown or malformed upstream responses fail closed as `INVALID_UPSTREAM_RESPONSE`.
12. Administration and other unavailable modules are absent rather than inert.
13. The live browser journey creates no strategy, public approval, citizen assessment, profiling, targeting, contact, publication, spending, mobilization or external effect.

No CRITICAL or HIGH finding remains open inside this bounded increment.

## Environment limitation and validated alternative

The persistent sandbox Docker daemon cannot register one nested image layer (`lchown /var/empty: permission denied`). The same code is therefore verified locally with PostgreSQL 15 + Uvicorn + Next standalone + Chromium. The PR workflow additionally runs `make frontend-functional-e2e` using the hosted runner Docker engine and remains the final Compose exact-head proof.
