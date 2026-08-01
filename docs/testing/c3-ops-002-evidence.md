# C3-OPS-002 evidence

Status: `REVIEWED` locally; exact-head hosted PostgreSQL 18 evidence pending.

## Implemented boundary

- strict rollback policy and migration catalog in `program/rollback-readiness.json`;
- typed fail-closed selector in `backend/src/campaignos/operability/rollback.py`;
- bounded CLI and sanitized receipt writer in `scripts/operations/verify_release_rollback.py`;
- operator decision tree in `docs/operations/release-rollback.md`;
- PostgreSQL 18 hosted rehearsal step in the existing operational-recovery job;
- no deployment, downgrade, restore, cloud action or external effect.

## Local verification

- focused Ruff: PASS;
- focused mypy: PASS;
- `backend/tests/test_release_rollback.py`: 28 PASS;
- local `make rollback-verify`: PASS;
- selected response: `ROLL_BACK_APPLICATION_ARTIFACT`;
- migration head: `20260729_0012`;
- classification: `EXPAND_BACKWARD_COMPATIBLE`;
- receipt decision: `PASS`;
- receipt mode: `0600`;
- source mutation: `NONE`;
- production rollback claim: `false`;
- external effects: `NONE`.

The local receipt was deleted after inspection. Exact-head hosted CI must generate and retain a new receipt tied to the submitted revision.

## Adversarial coverage

The focused tests reject:

- automatic Alembic downgrade and destructive command fragments;
- branch/tag/mutable artifact references or absent commit evidence;
- unknown migration classification;
- configuration reversal that weakens protected controls;
- automatic worker/outbox replay;
- production targets;
- unknown policy/receipt fields;
- secret-bearing or identifier-bearing receipts;
- incomplete migration catalogs and changed scenario decisions.

## Complete repository gate

- Python: 821 passed, 12 controlled skips, 90.11% coverage;
- frontend: 33 files / 144 tests, lint, strict TypeScript, production build and audit PASS;
- npm audit: zero vulnerabilities;
- Terraform: plan/test only PASS; no apply;
- program, release, security, eval, supply-chain and safety validators PASS.

## Pending evidence

- exact-head PostgreSQL 18 rehearsal and retained artifact;
- complete PR checks and independent review;
- final merge and post-merge CI.

Managed staging rollback, production artifact promotion, PITR, RPO/RTO and production approval remain absent and blocked.

## Local environment limitation

The pinned `rhysd/actionlint:1.7.12` image was resolved and its layers downloaded, but the nested Docker daemon failed before container start while registering `/var/empty` (`lchown: permission denied`). This is not a workflow PASS. The versioned CI-policy parser passes locally, and hosted exact-head `Locked quality and contract suite` must execute the same digest-pinned actionlint container successfully before merge.

## Frozen implementation

Implementation commit: `0cb4180d72102c413c368de467090eb3684dfe6a`.
Base main: `e1f9c508c397a6df54a3363dde729375b55edb52`.
