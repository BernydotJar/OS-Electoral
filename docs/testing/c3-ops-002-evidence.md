# C3-OPS-002 evidence

Status: `MERGED_TO_MAIN`; final exact-head and post-merge PostgreSQL 18 evidence passed.

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

## Remaining managed-environment evidence

Managed staging artifact rollback, production artifact promotion, PITR, accepted RPO/RTO and production approval remain absent and blocked.

## Local environment limitation

The pinned `rhysd/actionlint:1.7.12` image could not start in nested Docker because layer registration rejected `/var/empty` ownership changes. Hosted exact-head `Locked quality and contract suite` subsequently executed the same digest-pinned actionlint container successfully in run `30683477144`; the local limitation is resolved by equal-or-broader hosted evidence.

## Frozen implementation

Implementation commit: `0cb4180d72102c413c368de467090eb3684dfe6a`.
Base main: `e1f9c508c397a6df54a3363dde729375b55edb52`.

## Exact-head hosted gate

PR `#148` head `98faf8ab1f8e614555575bd560e3e593aedb2561` passed CampaignOS CI `30683477144` and Runtime Visual Review `30683477171`.

- digest-pinned actionlint: `SUCCESS`;
- PostgreSQL 18.3 backup/restore and rollback job `91324829967`: `SUCCESS`;
- retained rollback artifact `8813086739`;
- artifact digest `sha256:8f8f7756b4631ced6ba797ca9db7b62736a4e58827bde61aab8afa34eca8523a`;
- candidate revision `98faf8ab1f8e614555575bd560e3e593aedb2561`;
- previous known good `e1f9c508c397a6df54a3363dde729375b55edb52`;
- migration head `20260729_0012`, classification `EXPAND_BACKWARD_COMPATIBLE`;
- authority and immutable source evidence: `PASS`;
- selected and expected response: `ROLL_BACK_APPLICATION_ARTIFACT`;
- decision `PASS`, source mutation `NONE`, restore target `NOT_CREATED`;
- production rollback claim `false`, external effects `NONE`;
- PR review: zero comments, reviews, inline threads or unresolved findings.

The hosted gate resolves the local nested-Docker actionlint limitation. It does not prove managed staging or production rollback.

## Final exact-head and merge closure

- final review head: `b4cbcac58f94aecfe12a1f104d1717677ecbfaf7`;
- CampaignOS CI `30683667307`: `SUCCESS`;
- Runtime Visual Review `30683667313`: `SUCCESS`;
- rollback/recovery job `91325366844`: `SUCCESS`;
- final artifact `8813153523`, digest `sha256:c2fc258d407c9bac39ff9d7bf37c8663a4d6c1991f613ad219e228a21a0f2562`;
- PR `#148` squash-merged at `2026-08-01T04:23:01Z`;
- merged main `db8692d0f830496b413a8f56f2611eb611708545`;
- post-merge CI `30683834955`: `SUCCESS`, all ten jobs green;
- post-merge artifact `8813212488`, digest `sha256:14858f9dabeddb69ef988319b4415bcc5d185887dfb2ecf0a5be4c576d236a25`.

The post-merge receipt is bound to main `db8692d0f830496b413a8f56f2611eb611708545` and previous known good `e1f9c508c397a6df54a3363dde729375b55edb52`. It records `PASS`, `source_mutation=NONE`, `restore_target_state=NOT_CREATED`, `production_rollback_claim=false` and `external_effects=NONE`.
