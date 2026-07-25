# C3-FRONT-003 evidence — campaign launch roadmap

Date: 2026-07-25
Branch: `agent/c3-front-003-campaign-launch-roadmap`
Base: `main@38c4cf059acd9690f1f378a340797811ec8dbf12`

## Implemented behavior

- Added a deterministic five-phase campaign journey derived from persisted backend status.
- Added explicit `BLOCKED` semantics for the next phase when access, configuration, or an implemented module is absent.
- Added a dominant campaign roadmap with current mission, progress, phase outcomes, and honest next actions.
- Replaced primary Spanglish and internal reason/next-action codes with complete ES/EN user-facing copy.
- Added guided-intake help text and campaign-relevant examples for office, budget, candidacy purpose, team, assets, open questions, and evidence.
- Added motion tokens and restrained phase/mission transitions with reduced-motion support.
- Preserved exact-grant authorization and no-external-effects boundaries.

## TDD evidence

RED:

- `campaign-journey.test.ts` initially failed because the derivation module did not exist.
- Spanish i18n test initially failed because navigation rendered `Readiness`.
- The unavailable-module test initially received `AVAILABLE` instead of required `BLOCKED`.

GREEN:

- five journey state tests pass;
- three i18n tests pass, including ES/EN dictionary parity and Spanish terminology.

## Browser evidence

Demo production build review:

```text
status: PASS
desktop_spanish: PASS
desktop_english: PASS
mobile_spanish: PASS
keyboard_skip_link: PASS
reduced_motion: PASS
horizontal_overflow: NONE
wcag_2_2_aa: PASS_ZERO_AXE_VIOLATIONS
browser_storage: EMPTY
unexpected_outbound_hosts: []
console_errors: []
page_errors: []
```

Artifacts are generated under `artifacts/c3-front-003-demo/` and are intentionally untracked.

## Persistent functional evidence

The workstation's nested Docker daemon could not register a pulled layer because its namespace rejected `lchown /var/empty`. This occurred before application startup. A local PostgreSQL fallback was then executed using the same repository migration, bootstrap, seed, API, production frontend, and browser-review code.

```text
PostgreSQL: 15.18 local ephemeral cluster, UTF-8
migrations: 20260719_0001 through 20260721_0011 PASS
role bootstrap: scripts/dev/postgres-init.sh PASS
seed: scripts/dev/seed_local_operator.py PASS
journey: campaign_select_start_and_update_guided_intake PASS
persistence_after_reload: PASS
exact_authorization_controls: PASS
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

Exact-head hosted CI remains required for the repository's pinned PostgreSQL 18 and Docker Compose gates.

## Safety and product findings

- The route never converts role labels into permissions.
- Later persisted data cannot bypass an incomplete earlier gate.
- Unavailable modules are blocked instead of presented as active.
- Raw readiness and intake codes are rejected by browser assertions.
- The route does not authorize strategy, public messaging, citizen contact, profiling, spending, mobilization, deployment, or production.
- Downstream mutation workflows remain incomplete and are documented as open product work rather than hidden behind visual polish.

## Final local frontend verification

```text
frontend test files: 15 passed
frontend tests: 67 passed
ES/EN dictionary parity: PASS
ES primary operational terminology scan: PASS
ES/EN/mobile demo browser review: PASS
PostgreSQL start/update/reload browser journey: PASS
Next.js production build: PASS
npm audit: 0 vulnerabilities
```

## Repository-wide regression

```text
make verify: PASS
Python tests: 708 passed, 10 skipped
coverage: 90.40% (required 90%)
Ruff: PASS
format: PASS
mypy: PASS (66 source files)
Docker Compose model: PASS
Terraform 1.15.8 fmt/init/validate/tests/policy: PASS, plan-only
security/privacy policy: PASS
program truth: PASS, production BLOCKED
release readiness: PASS, decision DENY_RELEASE
campaign safety scan: PASS
```

The workstation tools used for the final local gate were obtained from their official releases and checksum-verified: Docker Compose `v5.3.1`, Terraform `1.15.8`, and Gitleaks `8.30.1`.

## Remaining delivery verification

- complete the final diff and secret review;
- commit and push the authorized branch;
- verify remote SHA and create a draft PR;
- require exact-head Docker Compose/PostgreSQL 18 CI and visual review;
- keep merge, staging, deployment, spending and production approval human-gated.

## Exact-head hosted verification

```text
implementation head: 55cd6ba81928e3c7d9977803f41c3431b384ab6d
draft PR: 118
CampaignOS CI 30150408085: SUCCESS
Runtime Visual Review 30150408086: SUCCESS
displayed checks: 12/12 PASS
Docker Compose stack E2E: PASS
PostgreSQL 18 migrations/RLS: PASS
PostgreSQL backup/isolated restore: PASS
frontend API-backed journey: PASS
CodeQL/secret/dependency/Terraform/SBOM: PASS
```

Retained artifacts:

- recovery `8617439188`, `sha256:f1b089fe141278cf4d2cec6f392e36e1a6072ab91ed22aebb8a0771f9134f997`;
- supply chain `8617435703`, `sha256:e12ec6de31ebee77990db4bed49e30abf78b87f97a19bf698a13eca6ed760268`;
- frontend review `8617457524`, `sha256:fd62cf8c425fb3a27672f38d04018bcaf58a55ebaf39197e45426f645690f839`;
- visual review `8617446289`, `sha256:86a7dfa699c4fe1d11c568a183f5bdcafc11a4e0ac08528efa2ae15d6a950e0e`.

This checkpoint proves the repository increment, not staging or production readiness.
