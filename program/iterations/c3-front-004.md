# C3-FRONT-004 — Adaptive campaign entry and candidate evidence workflow

- `branch`: `agent/c3-front-004-candidate-evidence-workflow`
- `base`: `agent/c3-front-003-campaign-launch-roadmap@ff7b10fed951f176609c43ad83b501f83d92b810`
- `status`: `CI_GREEN`
- `production_status`: `BLOCKED`
- `external_effects`: `NONE`

## User problem

The campaign path is understandable but still behaves like a static roadmap. The full “build your campaign foundation” message repeats after work begins, and the candidate-evidence stage appears blocked because the frontend has no governed create/update journey even though the backend already supports one.

## Bounded objective

1. show the cinematic campaign welcome only before guided work starts;
2. replace it with a compact active mission on later visits;
3. unlock candidate evidence only after guided intake reaches `READY_FOR_RESEARCH`;
4. create the candidate dossier through an exact campaign-scoped grant;
5. add one provenance-preserving evidence source through optimistic concurrency and idempotency;
6. remove candidate reason codes from the primary UI;
7. keep demo mode read-only and production/external effects blocked.

## File ownership

- `task_id`: `C3-FRONT-004`
- `workstream_id`: `WS-05/WS-06/WS-07`
- `writer`: frontend implementation role
- `allowed_paths`: frontend application, frontend runtime reviews, deterministic local-development seed, seed regression test, product/testing/program documentation
- `read_only_paths`: backend candidate domain, migrations, production authorization policy
- `write_lock`: one writer per modified file

## Acceptance criteria

1. First use and returning use render distinct hero modes from persisted state.
2. No remote video, analytics or browser storage is introduced.
3. Candidate creation remains hidden until the foundation gate passes.
4. Candidate create/read/update each require their exact existing grant contract.
5. Source URLs must use HTTPS; evidence records retain classification, authority, jurisdiction, date and note.
6. Updates use `If-Match` and `Idempotency-Key`; duplicate sources and stale versions fail closed.
7. Demo remains read-only; live ES/EN/mobile journeys pass WCAG 2.2 AA automation with no overflow.
8. Production remains `BLOCKED`; no publication, citizen contact, spending, mobilization or deployment occurs.

## Validation record

- RED: missing experience mode, candidate form parser, candidate capabilities and API mutations failed focused tests.
- GREEN: 21 focused tests and 76 full frontend tests pass.
- local seed RED/GREEN: expected eight exact bounded grants failed at five, then passed after adding three development-only candidate grants.
- lint, strict TypeScript, production build and npm audit pass; npm reports zero vulnerabilities.
- demo browser: ES/EN/mobile, keyboard, reduced motion, zero axe violations, no overflow, no external hosts.
- live browser: first-use welcome, foundation start/update, stage transition, candidate create, evidence append, persistence after reload, ES/EN/mobile, zero axe violations and no external effects.
- PostgreSQL 15 ephemeral UTF-8 cluster migrated through revision `20260721_0011`.

## Product boundaries

This increment makes the first evidence operation real. It does not yet edit claims, biography, purpose, values, contradictions, development goals, reputation risks or section approvals. Team, strategy and operations remain separate governed mutation increments. The UI does not ingest electoral data automatically, profile voters, recommend targeting or authorize public action.


## Exact-head hosted verification

- implementation head: `d22d9fac7ce9d59430edff927f5343f8391719f5`;
- stacked draft PR: `#119` over `agent/c3-front-003-campaign-launch-roadmap`;
- CampaignOS CI `30166352329`: `SUCCESS`;
- Runtime Visual Review `30166352316`: `SUCCESS`;
- all 12 displayed checks passed;
- recovery artifact `8621683108`, digest `sha256:2bd00f5d0fafd23a14e4d9d39a5c4fed1052ef45ddcde35b94a8034b39d6b359`;
- supply-chain artifact `8621679234`, digest `sha256:aa9c53da4592c9d487a63369bc0d3d54b156da5c6a9ba4709c64cae998e5fb1e`;
- frontend artifact `8621707850`, digest `sha256:65bd4e1acd0cea215215d4005cefae895e5b4f6e23a2303fe067f9c16baa2a62`;
- visual artifact `8621689050`, digest `sha256:2ac20eb9e608c0ca149b7b324ddfd691a7776fa7d25fee8c4015b85522aa059d`;
- Gitleaks SARIF `8621678726`, digest `sha256:21b74b5151958baa941646d7cad362a4bd62babb8cc61ba8dea7cdce8582a703`.

This verifies the repository increment only. Production remains blocked and release remains denied.
