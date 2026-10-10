# CampaignOS / OS-Electoral — Adversarial Product & Agentic Engineering Audit

- **Assessment:** 2026-10-10
- **Scope:** Existing repository, local Cloud Sandbox MCP V2 checkout, supply chain, test/CI controls, Graph Harness governance, identity, AI runtime, frontend browser review, and production readiness.
- **Base revision:** `main@1b32e46304b47c04cf44510c4b5f1b29bb9391b9` (2026-08-17)
- **Review branch:** `audit/adversarial-hardening-20261010`
- **Verdict:** **NOT PRODUCTION READY / RELEASE DENIED.** Most code quality checks pass, but dependency and deployment gates remain open.
**No external effects:** No production deployment, protected merge, cloud spending, political publication, citizen contact, or destructive persistent-data operation occurred.

> This audit distinguishes **observed facts**, **design limitations**, **unverified assumptions**, and **proposed improvements**. A model saying a check passed is never proof; tool receipts and versioned sources are the evidence.

## Executive verdict

CampaignOS demonstrates substantial software implementation and a deliberate safety boundary. However, a green unit-test suite is **not** proof of product readiness. On the original checkout, the frontend dependency gate failed with 18 reported vulnerabilities, including one critical, while the program's canonical release decision remained `DENY_RELEASE`. The audit branch reduced npm advisories to five high-severity findings, all in the Next.js ESLint development-tool chain, and reduced the Python environment audit from 25 advisories to zero. **The full frontend verification command remains red and this branch must not be represented as CI-green or release-ready.**

### Tested facts

| Scope / tool | Baseline | Audit branch / latest evidence | Result |
|---|---|---|---|
| Git | `main@1b32e46`; clean clone | isolated audit feature branch | verified identity |
| Python tests | 865 passed, 13 skipped | **865 passed, 13 skipped** | PASS for executed tests |
| Python coverage | 90.03% | **90.03%**; project floor 90% | PASS but thin margin |
| Ruff + format + strict mypy | PASS | PASS | PASS |
| Program-state validator | one critical open | one critical open | validator PASS / release blocked |
| Release-readiness validator | `DENY_RELEASE` | `DENY_RELEASE` | validator PASS / release blocked |
| Eval catalog | 33 required / 7 PASS / 17 PARTIAL / 9 NOT_RUN | unchanged | incomplete |
| Python `pip-audit --local` | 25 advisories in 5 packages | **0 known vulnerabilities** after audited lock updates | improved |
| `npm audit` (all dependencies) | **18** (1 critical / 14 high / 3 moderate) | **5 high**, 0 critical | FAIL — unresolved |
| `npm audit --omit=dev` | not assessed as independent baseline | **0 known vulnerabilities** | production dependency tree only |
| Frontend lint / TypeScript / unit tests | lint/type/tests pass | **250 tests in 55 files pass**; one non-blocking lint warning | PASS except warning |
| Frontend production build | PASS | PASS with Next.js 16.4.0 | PASS |
| Full `npm run verify` | FAIL at npm audit | **FAIL at npm audit** | **FAIL — must remain gated** |
| Chromium read-only demo E2E | not rerun against initial SHA | desktop ES/EN, mobile ES, keyboard, route isolation, reduced motion, axe WCAG 2.2 AA all PASS; zero console/page errors, no overflow or outbound hosts | PASS only for tested demo surfaces |
| Local authenticated PostgreSQL/API/browser run | 13 tests skipped in unit suite; no new authenticated E2E proof | **NOT RE-EXECUTED** | evidence gap |
| Managed staging, identity provider, PITR, operational alerts, human production approval | not verified | not verified | **BLOCKED** |

Raw local test logs are stored in the active sandbox under `/tmp/campaignos-*` during this review; they are not durable cross-session release receipts. GitHub exact-head CI on this new branch is **not yet proven**.

## P0 — Release-blocking findings

### ADV-001 — No independently verified production platform

- **Type:** Existing confirmed critical gap.
- **Evidence:** `architecture/program-state.json` finding `FND-PLATFORM-001`; `program/release-readiness.json`.
- **Observed:** Plan-only infrastructure exists, but there is no approved, independently verified managed staging/production runtime, backups/PITR, deployed alert receivers, or final approval.
- **Risk:** Passing local tests cannot prove production recoverability, capacity, security, incident response or authority.
- **Closure:** Human authorizes a bounded staging environment; deploy isolated platform; verify OIDC, RLS, alerts, encryption, restore/PITR, RPO/RTO, load, rollback, runbooks and independent approvals. Until then keep `DENY_RELEASE`.

### ADV-002 — Frontend supply-chain gate is red

- **Type:** Reproduced security audit failure.
- **Evidence:** `frontend/package.json`, lockfile; `npm audit --json` before/after remediation.
- **Before:** 18 vulnerabilities (1 critical, 14 high, 3 moderate).
- **After:** 5 high, from `eslint-config-next -> @next/eslint-plugin-next -> fast-glob -> micromatch -> braces`.
- **Important nuance:** `npm audit --omit=dev` returns 0; the five residual advisories affect the development/lint chain. Their classification does **not** prove a reachable remote production exploit.
- **What was improved:** Next.js 16.2.11 -> 16.4.0; ESLint config 16.2.10 -> 16.4.0; Vitest 4.1.10 -> 4.1.11; Sharp override 0.35.3 -> 0.35.5; brace-expansion compatibility shim moves to patched 5.0.12; safe transitive updates.
- **What remains wrong:** `npm run verify` correctly fails at `npm audit`. The registry's suggested `npm audit fix --force` would downgrade `eslint-config-next` to 14.2.35: a breaking, unsafe resolution for this Next.js 16 application.
- **Closure:** Obtain an upstream patched `braces`/lint chain, or implement a reviewed lint-engine migration **with equivalent or stronger rules** and regression proof. **Do not suppress or broadly allowlist scanner findings.**

### ADV-003 — Product AI is not connected to a live generation provider

- **Type:** Confirmed implemented boundary / missing production capability, not a model safety bypass.
- **Evidence:** `backend/src/campaignos/api/app.py`: optional `agent_provider`, otherwise `UnavailableStructuredGenerationProvider()`; `backend/src/campaignos/agents/runtime.py`.
- **Observed:** There are provider-neutral contracts, budgets, schema checks, instruction restrictions, zero tool authority and refusal behavior. The default application factory has **no configured live AI provider**.
- **Risk:** It is incorrect to market the in-product agent as operational live Claude/LLM assistance in the default deployment. Engineering use of Claude and an AI feature inside CampaignOS are separate architectures.
- **Closure:** Implement a licensed, explicitly configured provider adapter only after approved business scope, privacy/security review, prompt-injection evals, tenant boundaries, token/cost budgets, latency/fallback tests, nonproduction E2E and human approval. Preserve zero external action authority.

### ADV-004 — Real identity lifecycle and end-to-end authorization are not production-verified

- **Type:** Explicit production readiness gap.
- **Evidence:** `program/program-state.json`, `program/release-readiness.json`, OIDC/tenancy code and tests.
- **Observed:** OIDC verification, role/exact-grant logic, forced PostgreSQL RLS and local identity lifecycle contracts exist. Provider-operated login, recovery/MFA, invitation delivery and revocation remain unverified.
- **Closure:** Integrate and exercise an identity provider in authorized staging; independently red-team session expiration, tenant switching, BOLA/IDOR, privilege revocation, invitation abuse, rate limiting and operator recovery. Require browser -> API -> database receipts.

## P1 — Engineering/governance gaps

### ADV-005 — Graph Harness adoption is documented, but independent verifier/executor provenance is not established

- **Type:** Evidence gap, **not proof that critique never happened**.
- **Evidence:** `program/graph-harness-execution.json` explicitly contains `"projection_only": true`; `docs/architecture/graph-harness-runtime.md`.
- **Observed:** The project preserves task graph, ledger, spec approvals, branch/PR/CI and release-state projections. The current records do not independently prove the identity, model, session, context digest, tool policy or separation of every Producer, Critic and Verifier execution.
- **Risk:** Describing the entire history as "Claude autonomously built and independently verified CampaignOS" overstates evidence. Some commits have different authors or automation surfaces.
- **Closure:** Attach per-node signed or integrity-bound receipts with `executor_provider`, `model_id`, `role`, `spec_revision`, `context_digest`, `tool_permissions`, `head_sha`, `test_receipts`, verifier identity and review decision. Enforce independent verification by role and execution context. Keep provider-neutral provenance.

### ADV-006 — Coverage gate barely passes, and key integration paths remain unproven in this run

- **Type:** Observed quality-evidence gap.
- **Evidence:** `pytest --cov`: 865 pass, 13 skip, 90.03% overall; `security/rate_limits.py` ~71.76%, `identity/oidc.py` ~82.95%, `worker_main.py` ~44.94%.
- **Risk:** A passing aggregate threshold can conceal low-confidence security and lifecycle branches, especially when isolated PostgreSQL tests are skipped locally.
- **Closure:** Set risk-weighted module/branch targets, add negative-path OIDC/rate-limits/worker tests, and re-run isolated PostgreSQL RLS/migration and authenticated browser E2E on exact PR head. Raise aggregate threshold only after adding meaningful tests; do not game coverage.

### ADV-007 — Agentic engineering documentation can conflate workflow design with historical proof

- **Type:** Accuracy/governance finding.
- **Observed:** Graph Harness is a provider-neutral reference architecture. A documented Producer -> Critic -> Fixer -> Independent Verifier lifecycle is an **execution contract**, not automatic proof that each role actually ran independently on every historical feature. The previous narrative also attributes implementation specifically to Claude without complete machine-readable executor-attribution receipts.
- **Closure:** Use three assertion classes in architecture documentation: **AS-BUILT/VERIFIED**, **DEFINED POLICY**, and **TARGET/PROPOSED**. Include immutable run receipts before claiming specific model ownership or independent verification.

### ADV-008 — Documentation drift / false impressions of product state

- **Type:** Confirmed documentation integrity issue.
- **Evidence:** Root `README.md` and `docs/executable-architecture.md` describe earlier C2/static snapshots; the current repository includes Next.js 16 server-rendered routes, FastAPI, authenticated APIs and PostgreSQL-backed workflows.
- **Risk:** Architects, consultants and reviewers may trust stale "not implemented" statements or assume static demo = deployed SaaS.
- **Closure:** Mark historical snapshots, link to canonical `architecture/program-state.json` and active program truth, publish a date-stamped as-built capability matrix with explicit local/CI/staging/production evidence levels.

### ADV-009 — The release validator records a hard DENY decision, not a generic promotion mechanism

- **Type:** Design limitation, deliberately fail-closed.
- **Evidence:** `scripts/release/validate_release_readiness.py` asserts `BLOCKED`, `DENY_RELEASE` and absence of human approval.
- **Risk:** It is misleading to say "a green validator means the system can release"; the validator confirms **correct denial** at this stage. A separate, approved versioned release-candidate gate is needed when the environment exists.
- **Closure:** Preserve this deny validator; later implement a separate audited release-candidate state machine with exact-head technical gates and scoped human authorization. Never turn a hard deny into an unchecked toggle.

## P2 — UX/CX findings and opportunities

### ADV-010 — Mobile hierarchy is dense even though automated accessibility checks pass

- **Type:** Human visual review hypothesis, not an automated WCAG failure.
- **Evidence:** Screenshot `/tmp/campaignos-adversarial-browser/mobile-es.png`, 390 x 4564. The navigation card and green introductory card both repeat "CAPÍTULO ACTUAL 2/5". The substantive evidence sections appear below multiple orientation cards.
- **Risk:** Mobile users may need excessive scrolling before completing the next action. Repetition increases cognitive load for nontechnical campaign operators.
- **Closure:** Run moderated task-based usability review with nontechnical users. Consolidate duplicate chapter orientation, move the primary next-action control above the fold, shorten labels, and keep evidence gates visible. Preserve keyboard navigation and locale persistence.

### ADV-011 — A new lint rule warns about legacy full-page locale navigation

- **Type:** Low-priority code quality finding.
- **Evidence:** `frontend/src/components/locale-switcher.tsx` calls `window.location.assign` for an internal route, flagged by Next.js 16.4.0 lint.
- **Closure:** Use tested Next.js `useRouter().push`/client navigation while preserving query string, hash and locale, with an explicit regression test. Do not make a cosmetic change without verifying navigation behavior.

## What worked (do not lose these strengths)

- Persistent canonical program state, dependency/approval boundaries and fail-closed release status.
- Deterministic correctness tooling and locked dependencies.
- Backend 865-pass suite, strict mypy, Ruff and program validators.
- Frontend 250 tests, Next.js production build, ES/EN and mobile browser paths.
- Simulated no-effect campaign agent, bounded output schemas, provider-identity checks, prompt/tool budgets and no automatic external political effects.
- Consistent exact-grant authorization, tenant isolation contracts, PostgreSQL RLS and audit architecture in local/CI tests.
- Manual-only, explicitly labeled **non-production** static marketing Pages deployment.

## Reference architecture: AS-BUILT versus TARGET

```text
                  HUMAN ENGINEER / PRODUCT OWNER
             intent, scope, approval, risk acceptance
                                  |
                        AUTHORIZED SPEC + POLICY
                         AGENTS.md / RTK.md
                                  |
                      CANONICAL PROGRAM STATE
               task graph / ledger / decisions / gates
                                  |
                   GRAPH HARNESS LIFECYCLE MODEL
                    (project projection_only)
                                  |
                  AGENT EXECUTOR(S) / TOOLS
             Claude, Codex, other agents: attribution
                must be evidenced, not assumed
                                  |
           Cloud Sandbox / Git / GitHub / code edits
                                  |
        deterministic pytest / mypy / lint / build / scan
                 browser E2E / DB isolation / CI
                                  |
                        EXACT-HEAD EVIDENCE
                           PR + receipts
                                  |
                HUMAN MERGE / RELEASE GATE
                    current decision = DENY

  CAMPAIGNOS PRODUCT RUNTIME (separate system):
    Next.js dynamic UI -> FastAPI -> PostgreSQL/RLS/audit
                                  |
                    agent recommendation boundary
                                  |
              Unavailable provider by default (AS-BUILT)
                                  |
          target provider integration after approval/evals
```

**Correct answer to the Claude architecture questions:** Claude may perform adaptive implementation tasks through a coding-agent entry point; deterministic tooling establishes pass/fail; Graph Harness constrains the execution model; the human approves scope and consequential effects. In this repository, attribution of a **specific** model to **specific past work** is unverified unless a run receipt exists.

## Recommended work order

1. **Keep release denied.** No production rollout on this audit branch.
2. **Resolve five high ESLint-chain advisories without a breaking downgrade or weakening scanning.** If upstream fix unavailable, preserve blocked gate and supplier-dependency finding.
3. **Run exact-head CI on the remediation PR.** Enforce fresh lockfile and quality evidence for both Python and frontend.
4. **Strengthen provider/authn and PostgreSQL RLS integration tests** in an authorized isolated environment. Add risk-weighted security coverage.
5. **Establish verifiable independent reviewer + executor attribution** in the agentic delivery graph.
6. **Perform manual mobile CX acceptance** for core workflows; automated axe results alone are insufficient.
7. **Authorize cost-bounded staging** and verify real identity, backup/PITR, telemetry/alerts, recovery, load, rollback and incident response before reassessing production.

## Remediation changes made on audit branch

```text
frontend/package.json and package-lock.json
  Next 16.2.11 -> 16.4.0
  eslint-config-next 16.2.10 -> 16.4.0
  vitest 4.1.10 -> 4.1.11
  sharp override 0.35.3 -> 0.35.5
  safe transitive audit updates

frontend/vendor/brace-expansion-compat/
  patched delegate 5.0.9 -> 5.0.12
  updated compatibility metadata

pyproject.toml and uv.lock
  PyJWT 2.13.0 -> 2.15.1
  httpx2 dev 2.7.0 -> 2.13.1
  transitive httpcore2, urllib3, pip updated
```

### Verification after remediation

- Python **865 passed, 13 skipped; 90.03% coverage**.
- Python `pip-audit --local`: **no known vulnerabilities**.
- Ruff, formatter, mypy, program and release-deny validators: **PASS**.
- Next.js frontend 55 test files / **250 PASS**; TypeScript and build: **PASS**.
- Demo-only Chromium accessibility/browser review: **PASS**.
- `npm audit --omit=dev`: **0**.
- `npm audit` and `npm run verify`: **FAIL (five high advisories, development tooling)**.
- Production: **DENY_RELEASE**.

### Explicit evidence limitations

- No fresh GitHub CI run, independent human security review or production approval is implied by local output.
- The audit does not prove that all historic tasks were executed by Claude, or that a Critic/Verifier was independent.
- The audit does not prove application-level vulnerabilities are exploitable simply because a dependency advisory exists.
- The clean browser E2E targets demo/read-only screens, not provider login or production data.
- The initial missing Chromium Playwright binary was fixed in the local test environment and is **not** a product defect.
- The audit did not obtain authority for production deployment, cloud resource provisioning or real political external effects.

**Final status: PARTIAL_WITH_DOCUMENTED_BLOCKERS — security dependency chain, managed platform, human gate, provider integration and independent verification require further evidence.**
