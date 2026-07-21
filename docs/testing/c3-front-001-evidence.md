# C3-FRONT-001 dynamic shell verification evidence

Evidence date: `2026-07-21 America/Guatemala`

## Classification

```yaml
increment: C3-FRONT-001
status: TESTED_LOCAL
production_status: BLOCKED
external_effects: NONE
static_demo: PRESERVED_AS_REFERENCE
live_oidc: NOT_IMPLEMENTED
current_branch_ci: NOT_RUN
```

## Dependency and supply-chain evidence

- Node `22.23.1` and npm `10.9.8` were used on Debian 12 ARM64.
- Next.js `16.2.10`, React/React DOM `19.2.7`, TypeScript `5.9.3`, ESLint `9.39.5`, Vitest `4.1.10`, and axe-core `4.12.1` are exact pins.
- `npm ci` reproduces the package lock.
- The Next transitive PostCSS version is overridden to exact `8.5.20` because the generated dependency graph initially resolved a version covered by a moderate advisory.
- Final `npm audit --audit-level=moderate`: zero known vulnerabilities.
- Dependabot now covers npm and the frontend Dockerfile.

## Unit and contract tests

`npm run test` executes 12 Vitest tests covering:

- demo-mode prohibition outside development/test;
- live-mode API configuration requirement;
- HTTPS/non-local API requirement for shared environments;
- ES/EN locale allowlist and dictionary structural parity;
- roles never implying navigation permission;
- navigation enabled only from relevant server-owned grants;
- runtime parsing of exact tenant membership and grants;
- unknown-field rejection;
- cross-campaign grant rejection;
- identity-only membership smuggling rejection;
- unsupported campaign-state rejection;
- cross-tenant campaign-page rejection even when another item is valid;
- readiness totals, ordering, status, and mandatory-limitation invariants.

## Static gates

```text
npm run lint       PASS
npm run typecheck  PASS
npm run test       PASS (12 tests)
npm run build      PASS
npm run audit      PASS (0 vulnerabilities)
```

The production build reports dynamic server-rendered routes for `/`, `/_not-found`, and `/[locale]` plus the Next Proxy boundary.

## Browser review

The official Playwright `1.61.0` Chromium runtime was installed for Linux ARM64. `make frontend-e2e` assembles the same standalone/static/public runtime layout used by the frontend Dockerfile, starts it on an automatically selected free loopback port, and runs `scripts/frontend/review_dynamic_shell.py`.

Verified states:

| Context | Result |
|---|---|
| Desktop Spanish, 1440px | PASS |
| Desktop English, 1440px | PASS |
| Mobile Spanish, 390px | PASS |
| Root locale selection | PASS |
| Full-document ES → EN language change | PASS |
| `html[lang]` parity | PASS |
| Keyboard skip link and main focus | PASS |
| Reduced-motion media preference | PASS |
| Horizontal overflow | NONE |
| Browser local/session storage | EMPTY |
| Bearer/cookie marker in rendered HTML | NONE |
| Unexpected outbound browser hosts | NONE |
| Console errors | NONE |
| Page errors | NONE |
| WCAG 2.2 A/AA axe-core violations | ZERO |

Screenshot dimensions:

```text
desktop-es.png  1440 × 1919
desktop-en.png  1440 × 1919
mobile-es.png     390 × 3576
```

Browser evidence is generated under `artifacts/c3-front-001/` in CI and retained for 30 days. Local evidence was generated under `/tmp/c3-front-001` and is not committed.

## Security review

- API access code and synthetic demo data are guarded by `server-only`.
- The browser receives no bearer token and stores no authority material.
- Tenant/campaign cookies select context only; the backend response remains authoritative.
- Runtime parsers reject malformed or cross-scope upstream responses.
- Demo mode is explicit, visibly classified, synthetic, read-only, and forbidden in shared/production environments.
- Security response headers include frame denial, `nosniff`, strict referrer policy, and a restrictive permissions policy.
- The shell contains no forms or domain-action buttons.
- No external transport or political effect exists.

## CI and container review

- `actionlint 1.7.12` was installed from the official Linux ARM64 release after SHA-256 verification; all workflows pass.
- CI adds a dedicated frontend job for exact npm installation, static gates, Playwright browser review, artifact upload, and the non-root frontend container build.
- CodeQL language coverage includes Python and JavaScript/TypeScript.
- `make secret-scan-worktree` snapshots exactly `git ls-files --cached --others --exclude-standard` before Gitleaks, avoiding ignored `.next` output while scanning every deliverable source file. The effective worktree and `origin/main..HEAD` history both pass with no new allowlists.
- `make frontend-image-verify` uses Buildah `1.28.2` with `vfs` storage, `chroot` isolation and Docker image format. It builds the same digest-pinned Dockerfile, verifies runtime UID/GID `10001:10001`, command and health-check metadata, and serves the synthetic Spanish shell inside the image: PASS. The nested Docker limitation is therefore scoped to the full Compose stack; CI retains an independent Docker-engine build.

## Required-eval mapping

| Eval | Evidence | Result |
|---|---|---|
| `EVAL-I18N-001` | dictionary parity plus ES/EN browser review | PARTIAL |
| `EVAL-ACCESSIBILITY-001` | keyboard, mobile, reduced motion, axe-core WCAG 2.2 A/AA | PARTIAL |
| `EVAL-NONTECH-001` | readable synthetic command-center shell | PARTIAL |

These remain partial because full authenticated product journeys, manual accessibility review, complete localization, and real non-technical user acceptance are absent.

## Remaining limitations

- No live OIDC login or durable session lifecycle.
- No trusted tenant portfolio selector endpoint.
- No campaign create/update UI.
- No guided intake, Candidate Workspace, Team Builder, War Room, evidence workflow, Training Academy, or administration journeys.
- No dev, staging, or production deployment evidence.
- No current-branch PR, CI, human review, or merge evidence at this local checkpoint.
