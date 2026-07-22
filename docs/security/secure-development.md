# CampaignOS secure development standard

Status: **ACTIVE BASELINE; pipeline enforcement partial**
Last updated: `2026-07-19`

## Change rules

- Define assets, scope, authorization, external effects, failure modes, and evidence before high-risk implementation.
- Preserve unrelated user changes and use small, reviewable branches/PRs.
- Resolve dependencies through Context7 plus official current metadata; lock versions and hashes before use.
- Never dynamically install validation dependencies inside a validator.
- Pin third-party GitHub Actions by full immutable commit SHA and review updates.
- Keep secrets out of source, tests, artifacts, logs, images, Terraform variables/state where avoidable, and command output.
- Use typed structured inputs, parameterized database operations, safe output encoding, explicit timeouts/size limits, and deny-by-default policy.
- Treat tokens, role labels, tenant IDs, object IDs, webhook/job fields, uploads, research evidence, and model output as untrusted.
- No production deployment or destructive data/infrastructure action without the explicit gate and exact target evidence.

## Required review by risk

Identity, tenant authorization, approvals, exports/deletion, payments, integrations, AI tools, public content, political data, production infrastructure, and migration/restore changes require an independent critic plus relevant security/privacy/domain review. Threat-model rows and hard evals must be updated with the change.

## Automated gates

The target PR pipeline blocks on locked installation, lint/format/type checks, unit/integration/tenant/contract/API/migration tests, frontend/build/browser/accessibility checks, hard evals, SAST, dependency/secret scanning, container/SBOM checks, and Terraform validation. A skipped or inapplicable gate needs an explicit reviewed reason; absence is not success.

## Vulnerability handling

Do not place undisclosed exploit details in public issues. Record severity, affected versions/environments/tenants, containment, owner, due date, verification, disclosure decision, and residual risk in a restricted process. Security fixes require regression tests and independent verification. Rotate exposed secrets and preserve incident evidence.

The CI definition covers locked quality/tests, PostgreSQL/RLS, actionlint, CodeQL, dependency/secret checks and a disposable constrained-role Compose E2E; draft PR `#72` runs `29706162737` and `29706162740` passed at their recorded head. Branch enforcement, complete frontend coverage, SBOM/provenance, Terraform, staging and operational gates remain incomplete. This standard is therefore an implementation requirement rather than production proof.


## CI and supply-chain controls

- Treat `.github/campaignos-security-policy.json` as reviewed desired state; run `make supply-chain-verify` for every workflow or dependency change.
- Every Action and service image must use an immutable SHA/digest. `pull_request_target` and persisted checkout credentials are forbidden.
- Generate CycloneDX SBOM, source manifest, in-toto/SLSA provenance and checksums from the exact revision. Never describe the generated provenance JSON as signed by itself.
- Require the GitHub OIDC attestation job to succeed for the exact SBOM/provenance subjects before claiming a signing gate.
- Live repository controls must match `scripts/ci/verify_github_security_settings.py`; drift in protection, reviews, checks, allowed Actions, SHA pinning or vulnerability alerts is a release blocker.
- Protected-main success is not deployment approval. AWS environments and production promotion remain separate explicit-human gates.


## Development identity boundary

A local development verifier may be used only when `CAMPAIGNOS_ENVIRONMENT=development`. It is mutually exclusive with OIDC, requires a token of at least 24 characters, compares bearer material in constant time and stores only a digest-derived session identifier. It proves identity only: memberships and exact grants remain PostgreSQL-owned and are re-evaluated on every API call.

The versioned functional environment is a localhost fixture. Shared and production environments must reject it. The token must never enter HTML, client JavaScript, browser storage, logs, artifacts or a deployable secret bundle.
