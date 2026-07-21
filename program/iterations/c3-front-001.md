# C3-FRONT-001 - Dynamic authenticated application shell

- `status`: `CHECKPOINT_COMPLETED_TESTED_LOCAL_PUBLISHED_UNREVIEWED`
- `branch`: `agent/c3-front-001-dynamic-shell`
- `base`: `agent/c3-api-006-campaign-create@a21e7353f0a91f8c50a10904d942e03db45b8318`
- `policy_commit`: `0763b7d0b8222043e0cf436c813ebfd61376d970`
- `implementation_commit`: `b21f3d55ca0e89d3e6575076b5affa90732e3438`
- `publication`: `REVIEW_BRANCH_PUBLISHED_NO_PR_NO_CI`
- `production_status`: `BLOCKED`
- `external_effects`: none; the shell is read-only and cannot publish, spend, contact, mobilize or grant authority.

## Agent contract

```yaml
task_id: C3-FRONT-001
producer: Frontend Engineer
critic: Security, Accessibility and UX Reviewer
fixer: Frontend Engineer
independent_verifier: Test and Release Reviewer
objective: establish a real Next.js/TypeScript server-rendered CampaignOS shell with fail-closed identity boundaries, typed backend contracts, tenant/campaign context, accessible Premium Slate foundations and Spanish/English parity
allowed_paths:
  - frontend/
  - scripts/frontend/
  - scripts/security/
  - docs/ux/
  - docs/i18n/
  - docs/testing/
  - .github/workflows/
  - Makefile
  - program/
read_only_paths:
  - web/
  - RTK.md
prohibited_actions:
  - merge
  - deployment
  - live identity provisioning
  - browser token exposure
  - external delivery
  - political approval
  - citizen contact
  - voter profiling
```

## Acceptance criteria

1. A pinned Next.js App Router/React/TypeScript application exists separately from the static `web/` reference.
2. Server-rendered identity uses an HttpOnly opaque token cookie and server-only typed backend client; browser bundles receive no bearer token.
3. Live mode fails closed without API configuration or a verified session. Synthetic demo mode is explicit, read-only and forbidden in shared/production environments.
4. Tenant and campaign selectors are treated only as context; every backend response remains authoritative and tenant scoped.
5. Navigation visibility is derived from server-owned exact grants but never acts as an authorization decision.
6. Spanish and English dictionaries have structural parity, locale-aware routing and correct document language.
7. The shell provides loading, error, unauthenticated, context-required, empty and dependency-unavailable states.
8. Premium Slate visual tokens, responsive behavior, keyboard focus, skip navigation and reduced-motion support are implemented without importing the legacy static runtime.
9. Unit tests cover configuration, locale parity and navigation policy; production-build Playwright covers desktop/mobile, locale, focus and console errors.
10. npm audit, lint, strict typecheck, tests, build, repository regression, program truth, safety and secret scans pass.
11. The static `web/` reference remains preserved until explicit parity and archive review.
12. Production remains `BLOCKED`; no shell state implies political, legal, financial, publication or production approval.

## Implementation evidence

- Added a pinned Next.js/React/TypeScript App Router application under `frontend/` without importing the legacy static JavaScript runtime.
- Added server-only API access, HttpOnly token consumption, no-store requests, bounded timeouts and sanitized problem handling.
- Added exact runtime parsers for identity, memberships, grants, campaigns and readiness evidence.
- Added fail-closed live mode and synthetic read-only demo mode restricted to development/test.
- Added structurally tested Spanish/English dictionaries, locale routes, document metadata/language parity and a full-document locale transition.
- Added responsive Premium Slate components, keyboard focus, skip navigation, reduced-motion support and explicit human-authority limits.
- Added exact npm lock/pins, non-root standalone Dockerfile, frontend Make targets, CI browser/container job, npm/Docker Dependabot and JavaScript/TypeScript CodeQL.

## Critic findings repaired

1. The generated npm graph initially contained a moderate PostCSS advisory; exact `8.5.20` override reduced final audit to zero vulnerabilities.
2. TypeScript-only contracts did not validate remote JSON; exact runtime parsers and adversarial tests now fail closed.
3. Next App Router soft locale navigation preserved stale root `html[lang]`; locale changes now load a new document.
4. The first standalone E2E omitted `.next/static`, so CSS/JS returned 404 and hydration failed; the harness now mirrors the Docker runtime layout.
5. Fixed stale Next-server collisions by selecting a free loopback port and managing the standalone PID directly.
6. Added axe-core WCAG 2.2 A/AA review in addition to layout, keyboard, mobile and reduced-motion checks.
7. Added explicit synthetic-data and no-real-campaign labels, empty browser storage verification and unexpected-outbound-host rejection.
8. The independent BOLA review found that one valid selected campaign could coexist with a foreign-tenant item in the same upstream page. The runtime parser now binds every page item to the requested tenant and has an adversarial regression test.
9. A clean-checkout review found that an empty `frontend/public/` directory would not survive Git while Docker and E2E copy it. A tracked placeholder now preserves the runtime layout, and build/browser/image gates pass on that exact tree.

## Verification evidence

- `npm ci`: PASS.
- ESLint: PASS.
- Strict TypeScript: PASS.
- Vitest: `12 passed`.
- Next production build: PASS.
- npm audit: zero vulnerabilities.
- Playwright production-shell review: Spanish/English desktop, Spanish mobile, keyboard, reduced motion, no horizontal overflow, empty storage, no external hosts, no console/page errors: PASS.
- axe-core WCAG 2.2 A/AA: zero violations in the tested shell.
- actionlint `1.7.12`: PASS after checksum-verified ARM64 installation.
- AutoSkills `0.3.6`: dry-run only, eleven suggestions, zero installs, unchanged worktree.
- Program truth and eval catalog: PASS with production `BLOCKED`, five open CRITICAL/HIGH findings, six retained failed runs, `5 PASS`, `10 PARTIAL`, `18 NOT_RUN` evals.
- Buildah `1.28.2` with `vfs`/`chroot`: digest-pinned Docker-format image build, non-root metadata, health-check contract and in-image synthetic-shell smoke PASS.
- Gitleaks `8.30.1`: effective tracked/non-ignored worktree snapshot and `origin/main..HEAD` history PASS without new allowlists.

## Remaining release boundaries

- No live OIDC login, invitation, recovery, rotation, revocation or trusted tenant-selection lifecycle.
- No campaign mutation UI, persisted guided intake, candidate, team, roadmap, approval, evidence or training journey.
- The review branch is published and its GitHub SHA matches the implementation commit; no draft PR, current-head CI, human review, dev, staging or production evidence exists.
- Draft PR creation is blocked by the external absence of an authenticated GitHub mutation session; public inspection reports zero open PRs and zero workflow runs for the exact implementation head.
- Nested Docker remains unavailable for the complete Compose stack, but daemonless Buildah now provides a validated local alternative for the frontend Dockerfile; CI still owns the independent Docker-engine build.
- Automated accessibility evidence does not replace manual assistive-technology review.
- Production remains `BLOCKED`; the shell is read-only and authorizes no external effect.

## Publication checkpoint

- Published `agent/c3-front-001-dynamic-shell` at `b21f3d55ca0e89d3e6575076b5affa90732e3438`; local, origin and public GitHub branch SHAs match.
- Public GitHub inspection found zero open pull requests and zero workflow runs for that exact head. The workflow runs on pull requests and main pushes, so no branch-push CI result is inferred.
- `gh auth status` confirms no authenticated GitHub mutation session; draft PR creation remains an external dependency, not a code or credential-attribution failure.
- An initial wrapper call targeted the stale IAM branch. The accidental fast-forward is retained for auditability and `e7304e61242280482f402bdfe047665d2c62fe4d` restores the exact `5b203ec7d52c87950778b67b298de5d9b0a7a6fb` tree without force-push or history rewrite.
- Production remains `BLOCKED`; no deployment or external campaign effect occurred.
