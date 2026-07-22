# C3-CI-001 local and administrative verification evidence

Verified on 2026-07-21 from `agent/c3-ci-001-supply-chain-policy`, based on the final Agent checkpoint `8d6c491a6681ea2395e2f81800dda294e41b69bb`. Production remains `BLOCKED`; no merge or deployment occurred.

## Repository controls

| Control | Evidence |
|---|---|
| immutable Action references | offline policy verifier; 32 references pinned to 40-character SHAs |
| third-party Action allow-list | versioned policy plus live GitHub settings |
| protected `main` | strict eight-check branch protection, admin enforcement and one approval |
| safe checkout | every checkout sets `persist-credentials: false` |
| no privileged PR trigger | mutation test rejects `pull_request_target` |
| manual non-production Pages | source policy rejects push/PR/schedule publication |
| dependency governance | locked installs, audits, vulnerability alerts and automated security fixes |
| SBOM | deterministic CycloneDX 1.6 from Python and npm lockfiles |
| source manifest | every tracked file with SHA-256 and byte size |
| provenance | deterministic in-toto/SLSA statement with lock/workflow/Dockerfile materials |
| signing | SHA-pinned GitHub OIDC artifact attestation step; exact-head CI execution pending |
| drift detection | offline workflow verifier plus authenticated live-settings verifier |

## Executed gates

```yaml
ci_policy_tests:
  passed: 10
  adversarial_mutations:
    - unpinned action
    - pull_request_target
    - persisted checkout credentials
    - missing required supply-chain job
    - automatic Pages trigger
workflow_policy:
  result: PASS
  workflow_count: 3
  action_references: 32
  required_universal_checks: 8
live_github_settings:
  result: PASS
  comparisons: 17
  main_protected: true
  actions_mode: selected
  sha_pinning_required: true
  vulnerability_alerts: true
  automated_security_fixes: true
full_locked_suite:
  result: PASS
  passed: 638
  skipped: 9
  coverage_percent: 90.95
frontend:
  tests: 48
  lint: PASS
  typecheck: PASS
  build: PASS
  vulnerabilities: 0
program:
  truth: PASS_PRODUCTION_BLOCKED
  eval_catalog: PASS_5_15_13
  campaign_safety: PASS
```

## Current checkpoint boundary

The repository and administrative controls are verified. `C3-CI-001` remains `IN_PROGRESS` until the published exact head proves that the new universal job generates artifacts and completes GitHub OIDC attestation. Findings `FND-CI-001`, `FND-SUPPLY-001` and `FND-DEPLOY-001` remain remediation-in-progress until that evidence exists.
