# Supply-chain evidence and protected delivery controls

CampaignOS treats CI configuration and repository settings as production-security boundaries. The controls in this document do not authorize deployment. Production remains `BLOCKED`.

## Versioned repository policy

`.github/campaignos-security-policy.json` is the desired state for:

- universal required status checks on `main`;
- GitHub Actions restricted to GitHub-owned actions plus the exact third-party allow-list;
- immutable 40-character action SHA references;
- one approving review, stale-review dismissal and resolved conversations;
- strict up-to-date required checks, linear history and admin enforcement;
- force-push and branch deletion denial;
- vulnerability alerts and automated security fixes.

`python3 scripts/ci/verify_ci_policy.py` validates workflow source without network access. It rejects `pull_request_target`, unpinned actions, checkout credentials, unpinned service images, missing universal checks and automatic Pages publication.

`python3 scripts/ci/verify_github_security_settings.py` uses authenticated GitHub API reads to compare live repository controls with the versioned policy. It never changes settings.

## Deterministic evidence

Generate reviewable artifacts locally:

```bash
make supply-chain-evidence
```

The output under `artifacts/supply-chain/` contains:

- `cyclonedx-sbom.json`: CycloneDX 1.6 components from `uv.lock` and `frontend/package-lock.json`;
- `source-manifest.json`: SHA-256 and size for every tracked file;
- `provenance.intoto.json`: in-toto Statement v1 with SLSA Provenance v1 predicate;
- `evidence-report.json`: explicit signature and production-status semantics;
- `ci-policy-report.json`: offline workflow-policy result;
- `SHA256SUMS`: digest for every generated evidence file.

The files are byte-deterministic for a fixed revision and `SOURCE_DATE_EPOCH`. The provenance JSON is not itself an embedded signature and must not be described as one.

## Keyless GitHub attestation

The universal CI job `Software bill of materials and source provenance` uses the official, SHA-pinned `actions/attest-build-provenance` action with job-scoped `id-token: write` and `attestations: write`. It attests the SBOM, source manifest, provenance statement and checksum file through GitHub OIDC/Sigstore.

A successful job is required before the signing gate is considered green. The generated `evidence-report.json` says only that GitHub attestation is requested; it does not self-assert success.

A GitHub CLI version with attestation support can verify a downloaded subject, for example:

```bash
gh attestation verify cyclonedx-sbom.json --repo BernydotJar/OS-Electoral
```

Older `gh` versions without the `attestation` command must be upgraded or use GitHub's attestation UI/API. Absence of local CLI support is not attestation evidence.

## Live controls applied on 2026-07-21

Authenticated repository settings now enforce:

- `main` branch protection with eight universal checks and strict up-to-date status;
- one approval, stale review dismissal, conversation resolution and admin enforcement;
- linear history, no force push and no deletion;
- Actions `selected` policy, GitHub-owned actions only plus `astral-sh/setup-uv@*` and `gitleaks/gitleaks-action@*`;
- repository-wide action SHA pinning;
- vulnerability alerts and automated Dependabot security fixes;
- existing secret scanning and push protection remain enabled.

These settings are reversible administrative controls, not a merge, release or deployment.

## Remaining limitations

- Human review and merge of the stacked draft PRs remain pending.
- Historical failed runs remain production-blocking until explicit scope-equivalent supersession.
- No AWS environment, image registry publication, production image attestation, deployment approval or rollback evidence exists.
- Artifact retention is 30 days in the review workflow; production retention policy remains unapproved.
