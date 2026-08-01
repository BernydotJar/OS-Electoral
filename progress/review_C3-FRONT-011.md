# Review — C3-FRONT-011

## Review disposition

`PASS_LOCAL_REVIEW_EXACT_HEAD_HOSTED_FUNCTIONAL_GATE_PENDING`

## Scope

Bounded SHIP repair for the internal campaign workspace:

- make `Perfil y riesgos` the single primary candidate view;
- preserve next actions and evidence as parts of that profile rather than equal top-level destinations;
- explain current position and next work on every campaign chapter;
- add exact-grant creation of an internal candidacy draft through the existing backend boundary;
- subordinate training, access and audit metadata without removing it;
- simplify ES/EN language;
- evaluate usability against the user-provided Campol transcript while rejecting person-level voter profiling and persuasion targeting.

## Requirements traceability

| Requirement | Evidence | Result |
|---|---|---|
| Candidate workspace has one primary profile-and-risks view | `CandidateWorkspaceDeck`; static and Chromium tests | PASS |
| Next step and evidence are integrated, not competing tabs | inline action brief; keyboard `<details>` evidence section | PASS |
| All five chapters explain position, purpose, status and next action | `ChapterOrientation`; five-phase parameterized test | PASS |
| Current chapter is visually prominent without hiding navigation | enhanced current-chapter card and orientation panel | PASS |
| New candidacy requires the exact tenant grant | `deriveCampaignContextCapabilities`; route and capability tests | PASS |
| Creation is idempotent and remains an internal draft | submitted UUID key, stable slug, strict `DRAFT`/version/tenant parser | PASS |
| New draft does not change context or grant access | route emits no campaign cookie; copy and route tests | PASS |
| Empty authorized tenant can create its first draft | fail-closed shell branch and rendering tests | PASS |
| Training/access/read metadata remains auditable but compact | closed governance disclosure | PASS |
| Plain ES/EN language preserves safety boundaries | dictionary review and production build | PASS |
| Desktop/mobile/keyboard/accessibility contracts remain valid | Chromium ES/EN/mobile, reduced motion and axe | PASS |

## Producer

- Replaced the three-tab candidate deck with one visible profile, inline next action and subordinate evidence disclosure.
- Added a reusable chapter-orientation surface to all five routes.
- Added typed campaign-create input/evidence contracts, strict parsers and API-client support.
- Added a same-origin UI proxy that revalidates exact tenant-level authority before calling the existing protected create endpoint.
- Added stable browser-submitted idempotency and a deterministic 12-hex slug suffix.
- Added first-draft entry for authorized tenants without visible campaigns.
- Grouped team governance metadata under one compact disclosure.
- Simplified Spanish and English copy and updated browser evaluators.
- Added source-based product evaluation and explicit safety correction.

## Critic / red team

Findings and repairs:

1. **HIGH — duplicate creation on retry: resolved.** The initial proxy created a fresh key per POST. The key now travels from the rendered form through the proxy to the backend unchanged.
2. **HIGH — exact authority could not be exercised in an empty tenant: resolved.** Authorized empty tenants receive the governed first-draft flow; all other empty tenants remain fail closed.
3. **MEDIUM — profile hierarchy was inverted: resolved.** Profile and risks now precede action guidance.
4. **MEDIUM — campaign context had ambiguous two-column composition: resolved.** Context actions are stacked and form labels are bound to grouped fields.
5. **MEDIUM — browser evaluators encoded retired tabs: resolved.** They now enforce the single profile, orientation and evidence disclosure.
6. **LOW — short random slug suffix: resolved.** The suffix increased from 8 to 12 hexadecimal characters.
7. **INFO — nested Docker workstation limitation: documented.** PostgreSQL 18 image registration failed before service startup with `lchown /var/empty: permission denied`; hosted exact-head functional verification remains mandatory.
8. **MEDIUM — hosted journey omitted draft creation: resolved.** The default operator remains bounded to 11 grants; an opt-in E2E-only exact tenant grant now proves DRAFT creation, unchanged current context and no implicit read access.
9. **MEDIUM — English journey retained a retired candidate tab selector: resolved.** It now validates the single profile and opens the evidence disclosure directly.

No unresolved HIGH or MEDIUM finding remains in the bounded implementation.

Implementation commit: `8b835e1a64095e92136d5375026075581c8fe02a`.

## Independent verification

- `git diff --check`: PASS
- `make verify`: PASS
- Python: 793 passed, 12 controlled skips, 90.22% coverage
- Ruff lint/format and strict mypy over 80 source files: PASS
- frontend: 33 files / 144 tests PASS
- TypeScript, ESLint, production build and npm audit: PASS; zero vulnerabilities
- dynamic Chromium desktop ES/EN and 390px mobile ES: PASS
- candidate single-profile hierarchy: PASS
- all-chapter orientation: PASS
- keyboard evidence disclosure: PASS
- chapter route isolation and locale preservation: PASS
- reduced motion: PASS
- axe WCAG 2.2 AA: zero violations
- horizontal overflow: none
- browser storage: empty
- unexpected outbound hosts: none
- Terraform: plan/test only, PASS; no apply
- program/security/release/eval/safety validators: PASS
- local PostgreSQL/API/browser functional run: ENVIRONMENT BLOCKED before product startup

## Source evaluation disposition

The Campol transcript supports a staged campaign workflow and a stronger explanation of sequence, ownership and measurement. CampaignOS adopts only the safe aggregate workflow lesson. It does not adopt person-level voter databases, persuasion scoring, individualized targeting or contact execution.

## Hosted critic repair

- CampaignOS CI run `30678840392` passed every job except the API-backed frontend journey.
- PostgreSQL 18, migrations, the 12-grant E2E seed, static browser review, quality, CodeQL, recovery, supply chain, Terraform and stack E2E all completed successfully.
- The journey then timed out on a second Spanish selector for the retired `Fuentes y evidencia` tab after returning to the candidate chapter.
- Repair commit `43d5c3aad7f5b9214a547dcb416f5d8a8efeee6f` opens the current evidence disclosure and adds two static regression tests that reject every retired candidate-tab selector in both browser scripts.
- Local exact-tree verification after repair: `793 passed`, `12 skipped`, `90.22%` coverage; frontend remains `144 passed`.
- The repaired exact head passed hosted CI and the node is `CI_GREEN`.

## Release gate

Exact-head hosted CI and review are complete. Hosted PostgreSQL 18/API/browser evidence, all required checks and zero unresolved review conversations are satisfied.

This review does not authorize production deployment, publication, citizen contact, voter profiling, targeting, spending, mobilization or any external political effect.

Production remains `BLOCKED`; release remains `DENY_RELEASE`; external effects remain `NONE`.

## Exact-head hosted release evidence

Current review head: `d74922ec1a4cb6991a9cb3e91d4fad9953d19c6a`.

- CampaignOS CI run `30679126973`: `SUCCESS`.
- Runtime visual review run `30679126971`: `SUCCESS`.
- Dynamic PostgreSQL 18/API/browser job `91312405534`: `SUCCESS`.
- Runtime visual job `91312405335`: `SUCCESS`.
- Retained artifact `8811608118` (`campaignos-frontend-review`): `sha256:c7f98cb4a55349ce565bd1c99862f57a03424126df40f97cb01bb269b6ec2b26`, 11549427 bytes.
- Functional receipt: `PASS_DRAFT_PERSISTED_CONTEXT_AND_ACCESS_UNCHANGED`.
- Candidate evidence persisted after chapter navigation and reload.
- Spanish, English and 390px mobile journeys passed with zero axe violations, no overflow, no browser storage, no unexpected outbound hosts, no console/page errors and `external_effects=NONE`.
- PR #146 has zero issue comments, zero submitted reviews and zero inline review threads.
- Critic finding `C3-FRONT-011-F10` is `RESOLVED_VERIFIED`.

The node is `CI_GREEN` and ready for its already-authorized merge. Production remains `BLOCKED`; release remains `DENY_RELEASE`.
