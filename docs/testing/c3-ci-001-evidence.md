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
| signing | SHA-pinned GitHub OIDC/Sigstore attestation step succeeded for artifacts generated from exact source head `0501c4b`; Rekor/repository upload and digest API lookup verified |
| drift detection | offline workflow verifier plus authenticated live-settings verifier |

## Executed gates

```yaml
ci_policy_tests:
  passed: 11
  adversarial_mutations:
    - unpinned action
    - pull_request_target
    - persisted checkout credentials
    - missing required supply-chain job
    - automatic Pages trigger
    - missing exact PR source-head checkout
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

The repository, administrative controls and exact-source-head supply-chain attestation are verified. `C3-CI-001` is `CI_GREEN`. `FND-CI-001`, `FND-SUPPLY-001` and `FND-DEPLOY-001` are resolved; Platform and Historical CI findings remain production-blocking.


## Initial attestation scope defect and correction

CampaignOS CI run `29879794354` and supply-chain job `88797869680` completed successfully for implementation head `26b8e24f03e16c309ad20976bd8632627ecd734f`. The official GitHub OIDC/Sigstore step created four attestations and uploaded them to Rekor and the repository. However, the generated artifact recorded revision `e4346e591352584a45ef310c564974578998dd3a`, the temporary `refs/pull/99/merge` commit, rather than the PR source head. This evidence is cryptographically valid for the merge ref but insufficient for an exact-source-head claim.

The workflow now checks out `${{ github.event.pull_request.head.sha || github.sha }}` and passes the same expression explicitly to the evidence generator. A sixth mutation test removes that binding and proves the policy verifier fails. The initial run remains recorded as scope-insufficient evidence and does not close the CI or supply-chain findings. A corrected exact-head run is required.


## Corrected exact-source-head checkpoint

```yaml
head_commit: 0501c4bd4bfac4a6e762c65aa191cf7290a5d448
draft_pr: 99
merge_state: CLEAN
campaignos_ci_run: 29880153335
runtime_visual_run: 29880153340
supply_chain_job: 88799003125
supply_chain_artifact: 8514429538
artifact_revision: 0501c4bd4bfac4a6e762c65aa191cf7290a5d448
attestation_step: SUCCESS
attestations_created: 4
sigstore_rekor: UPLOADED
sbom_sha256: 68cd72f616ef5853bb59cfd7d8ecce49980c9b2d5213ec73013ec0bef58693d0
attestation_api_count_for_sbom_digest: 1
status: CI_GREEN
production_status: BLOCKED
```

`evidence-report.json`, `source-manifest.json` and the SLSA external parameter all equal the exact source head. SHA256SUMS verifies every downloaded evidence file. The attestation REST API returns one repository attestation for the SBOM digest.
