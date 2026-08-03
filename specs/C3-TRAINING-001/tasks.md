# C3-TRAINING-001 Tasks

## Approval and Preparation

- [x] Record explicit human approval and move the node from `spec_ready` to approved/ready.
- [x] Complete the pinned primary-documentation checkpoints.
- [x] Confirm one active Graph Harness feature and no cloud, production or external-action authority.
- [x] Inventory existing team training requirements, role slugs, authorization actions, rate-limit classes and frontend chapter integration.

## Producer — Content Governance

- [x] Add strict module, lesson, assessment, locale-pair and learning-path contracts.
- [x] Add repository-owned ES/EN initial modules with stable IDs, versions, sources, owners, review state and digests.
- [x] Reject raw HTML, scripts, remote embeds, arbitrary URLs and unknown fields.
- [x] Add deterministic role-to-path recommendations with `authority_effect=NONE`.
- [x] Document content approval, versioning, retirement, correction and source attribution.

## Producer — Persistence and API

- [x] Add the additive Training Academy migration, constraints and forced RLS.
- [x] Add assignment, module-progress and append-only completion-receipt models.
- [x] Implement exact tenant/campaign/principal authorization, idempotency and version conflicts.
- [x] Implement bounded deterministic assessment attempts and explanations.
- [x] Register reviewed route classes and one rate-limit enforcement call per protected route.
- [x] Preserve atomic audit/domain behavior and minimal learner data.

## Producer — Product Experience

- [x] Add strict frontend contracts and response parsers.
- [x] Add a plain-language Training Academy entry in the team chapter.
- [x] Show current path, purpose, progress, next lesson, required/optional modules and compact governance metadata.
- [x] Add accessible assessment feedback and historical internal completion receipts.
- [x] Maintain ES/EN parity, mobile/reflow, keyboard, visible focus and reduced motion.
- [x] State clearly that completion creates no permissions or professional accreditation.

## Verification

- [x] Test catalog schema, source allow-list, locale parity, digest stability and retirement behavior.
- [x] Test role recommendations without authority effects.
- [x] Test assignment/start/attempt/complete success, replay, conflict and correction paths.
- [x] Test attempt limits, deterministic pass/fail and no ranking/person-score fields.
- [x] Test exact self/manager/reviewer authorization and BOLA/cross-tenant denial.
- [x] Test PostgreSQL 18 RLS, concurrency, append-only receipts and audit rollback.
- [x] Test that completion never creates memberships, grants, invitations or access approvals.
- [x] Test frontend parsers, components, routing, ES/EN and build.
- [x] Run Chromium desktop/mobile/keyboard/reduced-motion/WCAG review.
- [x] Run the API/PostgreSQL/browser persistence journey.
- [x] Run complete repository, program, release, security, Terraform plan-only, supply-chain and secret gates.
- [ ] Retain exact-head sanitized evidence with no learner or campaign content.

## Critic / Red Team

- [x] Attempt arbitrary HTML/script/remote-content injection.
- [x] Attempt stale module/version and answer-key manipulation.
- [x] Attempt duplicate completion, attempt-limit bypass and idempotency collision.
- [x] Attempt cross-tenant learner/assignment/receipt access.
- [x] Attempt to convert role recommendation or completion into a permission grant.
- [x] Attempt person ranking, behavioral inference, profiling or professional-certification claims.
- [x] Attempt sensitive learner content in logs, receipts and retained artifacts.
- [x] Attempt retired-module assignment and historical-receipt mutation.

## Fixer and Independent Verifier

- [x] Repair only the affected content, authorization, persistence, UI or evidence subgraph.
- [x] Preserve failed runs and explicit supersession evidence.
- [ ] Independently rerun equal-or-broader focused and complete gates.
- [x] Record SHIP decisions for security, data correctness, privacy, accessibility, failure modes, testing and operations.

## Release Gate and Persistent Evidence

- [x] Persist review, iteration, validation and content-catalog evidence.
- [x] Mark only the repository Training Academy baseline complete when every acceptance criterion passes.
- [x] Keep live LMS/provider, managed environment, professional accreditation and production approval blocked.
- [ ] Merge only after exact-head CI, artifact inspection, resolved review threads and authorized merge.

## Stop Conditions

- Missing explicit human approval for this specification.
- A new dependency, lockfile change, paid service, cloud resource or production environment becomes necessary.
- Content requires copying a third-party course, transcript or proprietary slides.
- The design would profile, rank, psychologically assess or surveil a person.
- Completion would automatically create authority, staffing, discipline or campaign action.
- The academy would contact citizens, publish, spend, target or mobilize.
- Sensitive learner/campaign data cannot be excluded from logs and retained evidence.
- Exact authorization, tenant isolation, append-only completion evidence or content integrity cannot be preserved.
