# C3-FRONT-003 — Campaign launch roadmap and guided campaign foundation

- `branch`: `agent/c3-front-003-campaign-launch-roadmap`
- `base`: `main@38c4cf059acd9690f1f378a340797811ec8dbf12`
- `status`: `CI_GREEN`
- `production_status`: `BLOCKED`
- `external_effects`: `NONE`

## User problem

The authenticated shell exposes a technically correct but product-poor readiness dashboard. It mixes Spanish and English, displays internal reason codes, and leaves a non-technical candidate or representative without a clear understanding of the current campaign phase, next action, rationale, or downstream outcome.

## Bounded objective

Deliver the first product-level campaign launch path:

1. derive five sequential phases from persisted backend state;
2. show one current mission and one honest next action;
3. prevent later data from bypassing earlier gates;
4. distinguish unavailable modules from future locked phases;
5. replace primary internal codes and Spanglish with plain ES/EN copy;
6. make the guided-intake editor explain each campaign question with examples;
7. provide restrained motion with reduced-motion behavior;
8. preserve exact authorization and no-external-effects boundaries.

## File ownership

- `task_id`: `C3-FRONT-003`
- `workstream_id`: `WS-05/WS-06`
- `writer`: frontend implementation role
- `allowed_paths`: frontend components/lib/CSS, frontend review scripts, product/testing/program documentation
- `prohibited_paths`: backend behavior, migrations, infrastructure, production configuration
- `write_lock`: one writer per modified file

## Acceptance criteria

1. Spanish primary UI contains no unexplained English operational labels.
2. Primary surfaces do not expose readiness/intake reason codes or raw next-action enums.
3. The route exposes foundation, evidence, team, strategy, and operations in order.
4. Every phase is `COMPLETE`, `ACTIVE`, `AVAILABLE`, `BLOCKED`, or `LOCKED` from deterministic state.
5. An incomplete earlier phase prevents later phases from becoming actionable.
6. A missing or unauthorized module is visibly blocked rather than presented as a working link.
7. Guided-intake fields contain plain-language help and campaign-relevant examples.
8. ES/EN dictionaries retain structural parity.
9. Desktop, mobile, keyboard, reduced motion, WCAG, persistence, and authorization gates pass.
10. Production remains `BLOCKED`; no external political effect is created.

## Validation record

- focused TDD: initial missing journey module and Spanglish assertion failed as expected;
- journey/i18n focused tests: pass;
- frontend lint and strict TypeScript: pass;
- full frontend suite: 67 tests pass after the blocked-state and final copy repairs;
- production Next.js build: pass;
- npm audit: zero vulnerabilities;
- full repository `make verify`: 708 Python tests, 10 controlled skips, 90.40% coverage, Ruff, format, mypy, Compose model, Terraform plan-only and all program/security validators pass;
- demo browser review: ES/EN/mobile, keyboard, reduced motion, no overflow, zero axe violations, no console/page errors, no unexpected hosts;
- live local PostgreSQL 15 fallback: all migrations, official role bootstrap, deterministic seed, API, production frontend, start/update/reload journey, ES/EN/mobile, exact authorization, zero axe violations, no browser storage, and no external effects pass;
- Docker Compose execution remains delegated to exact-head CI because nested image extraction fails at `lchown /var/empty` in this sandbox.

## Product boundaries

The route describes the desired campaign operating sequence but does not claim that every downstream editing workflow is complete. Candidate evidence, team design, strategy decisions, territorial data ingestion, community profiles, vote-goal tracking, and Daily War Room mutation remain separate increments.

No publication, citizen contact, targeting, spending, mobilization, permission mutation, deployment, infrastructure apply, or production approval is introduced.

## Exact-head CI checkpoint

- implementation head: `55cd6ba81928e3c7d9977803f41c3431b384ab6d`
- draft PR: `#118`
- CampaignOS CI: `30150408085` — success
- runtime visual review: `30150408086` — success
- displayed checks: 12/12 pass
- recovery artifact: `8617439188`, digest `sha256:f1b089fe141278cf4d2cec6f392e36e1a6072ab91ed22aebb8a0771f9134f997`
- supply-chain artifact: `8617435703`, digest `sha256:e12ec6de31ebee77990db4bed49e30abf78b87f97a19bf698a13eca6ed760268`
- frontend review artifact: `8617457524`, digest `sha256:fd62cf8c425fb3a27672f38d04018bcaf58a55ebaf39197e45426f645690f839`
- visual review artifact: `8617446289`, digest `sha256:86a7dfa699c4fe1d11c568a183f5bdcafc11a4e0ac08528efa2ae15d6a950e0e`
- production remains `BLOCKED`; release remains `DENY_RELEASE`; external effects remain `NONE`.
