# CampaignOS current-state assessment

Assessment date: `2026-07-19 America/Guatemala`

Authoritative target: `os_electoral_prod_ready_goal_v2.md`

Repository evidence point: `main` at `8f32bc158003a55a76cb471af45da2193ca71003`; implementation branch `agent/c3-found-001-production-foundation`.

## Executive determination

Production readiness is **BLOCKED**.

The repository now contains a real local application foundation: a versioned FastAPI runtime, fail-closed OIDC token verification, typed configuration, an initial SQLAlchemy/Alembic PostgreSQL schema, transaction-local tenant scope, forced row-level-security policies, a non-root container, a hermetic Compose stack and locked dependencies. Draft PR `#72` has green pinned CI evidence at its recorded head. These are meaningful implementation and review-branch proofs, but they are not deployed or operational production evidence.

The only public deployed surface remains the static, read-only GitHub Pages demonstration. It is classified `DEMO_NON_PRODUCTION`, publishes only through a manual confirmation workflow, and never counts as a production environment.

## Verified in this increment

- The full Python unit/contract suite passed on Python `3.14.2`: `193 passed`, `1 skipped`; the skip is the deliberately isolated PostgreSQL marker.
- The isolated PostgreSQL test passed separately against PostgreSQL `18.3`: Alembic downgrade/upgrade/check, expected tables and policies, non-superuser/non-`BYPASSRLS` access, tenant-A visibility and cross-tenant write denial.
- The Compose end-to-end run built the pinned non-root API image, started PostgreSQL, initialized Adobe S3Mock and Mailpit, applied and checked the migration as the bootstrap administrator, proved that the API used the constrained `campaignos_app` role, verified liveness/readiness behavior, exercised SMTP and removed its unique containers/volumes.
- Ruff, Ruff format, strict mypy, JSON/YAML parsing, Compose validation, shell syntax and actionlint passed locally.
- Hash-locked production requirements were exported and `pip-audit 2.10.1` reported no known vulnerabilities at the check time. This is point-in-time evidence, not a guarantee.
- OIDC verification requires the fixed `RS256` algorithm, a matching key ID, signature, issuer, audience, expiry, issued-at, not-before when present, ID-token use, and `azp` for multi-audience tokens. Readiness fetches JWKS and fails closed.
- `/api/v1/me` returns the verified external identity only; it deliberately returns no memberships or grants until server-owned persistence loading exists. Token role claims are not treated as authorization.
- The initial migration creates tenant, principal, campaign, workspace, membership, role/grant, audit and outbox structures with composite scope constraints and forced RLS on tenant-owned tables.
- Approval transitions now bind an immutable authenticated principal to the exact requested action, option, reason, date, scope and target digest. Repository writes reject scope/identity mutation and persistence authorization is operation-specific.
- Evidence-review receipts bind exact scope, evidence, claim digest, disposition, reviewer authentication and grants; enabling evidence must be verifiable before it can create a contradiction.
- GitHub Actions and runtime container references used in the new foundation are pinned to immutable commits/digests. On draft PR `#72` head `e8adf4ce008bbf4b82fe9d7e6515ee4b37595922`, CampaignOS CI run `29706162737` and visual run `29706162740` completed successfully across quality, PostgreSQL/RLS, dependency audit, Gitleaks, CodeQL, constrained-stack E2E and browser review.

## What remains unproven or absent

- No live OIDC provider, login/invitation/recovery flow, MFA policy, server session lifecycle or revocation path has been integrated.
- Membership, campaign/workspace access and exact grants are not loaded from PostgreSQL on application requests; authenticated domain endpoints do not exist.
- The initial schema is not yet connected to the deterministic campaign-domain repositories. No durable approval/evidence workflow or background worker runtime exists.
- S3Mock and Mailpit are local test dependencies. There is no production object-storage/email adapter, attachment validation, quarantine, malware strategy or signed-operation policy.
- The dynamic application frontend, guided onboarding, i18n, Training Academy and API-backed campaign workspaces remain absent or static prototypes.
- No Terraform, AWS dev/staging/production environment, short-lived deployment federation, backup, restore, load, rollback or disaster-recovery evidence exists.
- Draft PR `#72` is not reviewed or merged. Main branch protection and rulesets were still absent when rechecked after the green run, so none of its checks is required for integration and repository settings do not require Action SHA pinning.
- CodeQL, Gitleaks and dependency-audit jobs executed successfully at the recorded PR head, but protected-main enforcement, alert/response policy evidence, SBOM, provenance and signing remain absent.
- Audit hashes remain unkeyed local integrity links, not digital signatures, immutable external anchors or KMS-backed evidence.
- No independent production security, privacy, legal, political-science, research-methodology or communication-ethics approval is recorded.

## Delivery and repository state

| Area | Evidence | Determination |
|---|---|---|
| C2 integration | PR stack merged to `main` | Integrated deterministic prototype |
| C3 runtime | Local FastAPI/PostgreSQL/OIDC/Compose implementation and tests | Partial foundation; not deployed |
| Local worktree | User-owned `RTK.md` and `artifacts/c1-front-003/` were present | Preserved and excluded from task scope |
| Draft PR CI | Runs `29706162737` and `29706162740` passed at head `e8adf4c` | Green review-branch evidence; not protected-main enforcement |
| Historical PR validation | Six manifest-linked runs retain `FAILURE` conclusions | Still blocking; no history rewriting |
| Main protection | GitHub API returned no branch protection and no rulesets | High release-governance gap |
| Pages | Live HTTPS static site; local workflow is manual-only | `DEMO_NON_PRODUCTION` |
| AWS | Session expired and no Terraform/environment evidence exists | External state not verified |

## Historical CI evidence requiring reconciliation

These recorded run IDs retain conclusion `FAILURE` until explicit, reviewed, scope-equivalent GitHub evidence supersedes them:

```text
29659355550
29659451027
29659542083
29659623156
29659692005
29659733648
```

Later integration runs `29660653755`, `29662896729`, `29706162737` and `29706162740` passed their checked commits, but do not rewrite those six records.

## Program-tool evidence

- AutoSkills `0.3.6` dry-run suggested three skills; no package was installed because provenance, lock and license review had not occurred.
- Context7 identifiers, retrieved guidance, official version cross-checks and installed pins are recorded in `program/context7-evidence.md`.
- Farmtable was unavailable; the JSON-compatible task graph, ledger and state records preserve dependencies and are validated fail closed.
- Specialized production, critic and verification roles were used where agent capacity was available; remaining work preserved explicit separation between implementation, adversarial review and test evidence.

## Next increments

1. Obtain human review of draft PR `#72`, reconcile the six historical failures explicitly, and configure protected-main rules without weakening the now-green checks.
2. Integrate a real OIDC provider and invitation/login/recovery lifecycle; load active membership and exact grants from PostgreSQL on every protected request.
3. Connect campaign-domain repositories and approval/audit/outbox flows to PostgreSQL; add versioned domain endpoints and an idempotent worker runtime.
4. Implement reviewed Terraform for an isolated AWS development environment, then prove staging security, migration, load, backup/restore and rollback gates.

Production deployment remains prohibited until every production gate passes and an authorized human records an explicit scoped approval receipt.
