# C3-FRONT-015 review

Review state: `REVIEWED_LOCAL_WITH_RUNNER_BLOCKERS`; exact-head hosted CI pending.

## Producer

Completed the existing Operations and War Room backend lifecycle through exact-authorized UI controls. Strategy can now progress into a governed human-owned roadmap with versioned phases, workstreams, tasks/dependencies, blockers, decisions, follow-up and learning, then create an immutable Daily War Room snapshot without autonomous execution or external political effect.

A real prerequisite dead end was also closed: Operations requires a filled Team owner, but the UI previously created only vacancies. The bounded repair lets the authenticated operator explicitly self-cover one vacancy through the existing Team update contract; the server owns `principal_id`, and no membership, grant or new access is created.

## Critic / Red Team

- prevented rewriting decision alternatives and selecting the replacement in the same request;
- closed the fresh-campaign VACANT → FILLED ownership dead end without introducing IAM authority;
- hid all existing-roadmap mutation controls when Strategy is no longer current/decided while retaining read evidence;
- localized the immutable War Room snapshot boundary in Spanish;
- verified exact grants, scope, current versions, current references, server-owned principal identity, no auto task execution and no external effects.

## Fixer

All recorded findings are resolved with focused route/component/form tests. Authorization, optimistic concurrency, evidence reference integrity, human decision semantics, read-only behavior and political-safety boundaries remain fail-closed.

## Independent Verifier

- frontend: 54 files / 248 tests, ESLint, strict TypeScript, optimized build, audit 0 vulnerabilities: PASS;
- backend: 865 passed / 13 skipped, 90.03% coverage: PASS;
- focused Operations/Team backend/API/seed: 99 PASS;
- dynamic read-only Chromium: ES/EN/mobile/keyboard/reduced-motion/route isolation/WCAG PASS, zero axe violations, no unexpected hosts/storage/errors;
- Compose config and supply-chain evidence: PASS;
- Gitleaks 8.30.1 checksum-verified effective worktree: PASS;
- Ruff / format / mypy / security / program / release / eval / safety: PASS;
- API-backed PostgreSQL/browser lifecycle: **BLOCKED_BY_RUNNER_DOCKER_LAYER_LCHOWN**, not treated as PASS;
- Terraform plan-only: **BLOCKED_TOOLING_TERRAFORM_CLI_UNAVAILABLE**, no apply attempted.

## Release Gate

Eligible for review-branch publication and exact-head hosted verification. Production remains `BLOCKED`; release remains `DENY_RELEASE`; external effects remain `NONE`. Hosted CampaignOS CI must execute the functional PostgreSQL/API/browser gate before merge.

## Persistent Evidence

See `docs/testing/c3-front-015-evidence.md`, `program/validations/c3-front-015.json`, this review, the iteration record, specs and task ledger.


## Hosted Fixer after first exact-head review

PR #182 first head `46c41bf25b4a26f71cd11da0ca440dcf1e4b5dcd` passed every hosted job except the API-backed functional onboarding journey. The failure occurred before Operations authoring: the backend returned the expected `409 CAMPAIGN_NOT_READY` for a roadmap whose prerequisites were not complete, while the shell read model treated that exact prerequisite response as a global error instead of an Operations `NOT_STARTED` state. The Fixer classifies only that problem code as not-started and preserves fail-closed behavior for unrelated 409 conflicts. Local final frontend verification is 55 files / 250 tests with lint, TypeScript, build and audit 0 PASS. Exact-head hosted revalidation remains the merge gate.


### F6 — hosted persistence assertion repair

The second exact-head run passed the live-shell prerequisite state and reached the end of Operations. API logs prove the learning PATCH and War Room snapshot POST/GET succeeded. The browser harness incorrectly looked for the learning title as a text node even though persisted learning is rendered in an editable input. The Fixer now asserts the persisted form input value both before and after reload; no product persistence contract was weakened.
