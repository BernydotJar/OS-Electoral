# CampaignOS decision log

This log records scoped implementation decisions. It does not grant political, legal, financial, deployment or production authority.

## DEC-2026-07-21-001 — Preserve the active review stack

- `status`: `ACCEPTED`
- `scope`: `C3-RESUME-001`
- `decision`: Preserve PRs `#84` -> `#85` -> `#86` as a stacked review sequence and branch subsequent dependent work from the last validated head rather than merging scopes or creating duplicate PRs.
- `evidence`: `program/iterations/c3-resume-001.md`, `architecture/program-state.json`
- `rationale`: The stack has distinct idempotency, worker and workspace-write review boundaries with green recorded checks.
- `consequences`: New dependent increments remain stacked until humans review/merge; no automatic retarget or force push is allowed.

## DEC-2026-07-21-002 — Readiness is operational setup only

- `status`: `ACCEPTED`
- `scope`: `C3-API-005`
- `decision`: Campaign readiness evaluates only campaign metadata and the presence of an active workspace. It must never imply political viability, strategy quality, legal/finance/security approval, publication readiness, production readiness or citizen/voter assessment.
- `evidence`: `backend/src/campaignos/campaigns/readiness.py`, `docs/api/campaign-readiness.md`
- `rationale`: Readiness is a bounded onboarding prerequisite, not an authority or recommendation engine.
- `consequences`: The response carries fixed limitation codes and no positive result can satisfy a human gate.

## DEC-2026-07-21-003 — Sensitive readiness reads are audited without outbox delivery

- `status`: `ACCEPTED`
- `scope`: `C3-API-005`
- `decision`: Every successful readiness read appends a tenant/campaign audit receipt in the same transaction, while emitting no outbox event.
- `evidence`: `backend/src/campaignos/data/audit.py`, `backend/src/campaignos/campaigns/readiness.py`, `backend/tests/test_campaign_readiness.py`
- `rationale`: Sensitive reads require traceability, but an observation-only operation must not create an external effect or delivery obligation.
- `consequences`: Audit failure fails the read closed; missing/denied/not-found reads do not create a success receipt.

## DEC-2026-07-21-004 — Serialize the tenant audit hash chain

- `status`: `ACCEPTED`
- `scope`: `C3-API-005`
- `decision`: Campaign, workspace and readiness audit appends share a session-bound tenant-row lock, a monotonic timestamp and a canonical hash input.
- `evidence`: `backend/src/campaignos/data/audit.py`, `backend/tests/test_audit_append.py`
- `rationale`: Independent append implementations and pre-lock timestamps could produce chain-head ambiguity under concurrent PostgreSQL transactions.
- `consequences`: Appenders require a valid lock token from the same Session; application-level ordering is deterministic. Database-level append-only enforcement remains a separate risk.

## DEC-2026-07-21-005 — Make coverage and eval inventory executable gates

- `status`: `ACCEPTED`
- `scope`: `C3-API-005`
- `decision`: `make test` must execute pytest-cov with a 90% floor, and `program-verify` must validate the exact 33-item required-eval catalog.
- `evidence`: `Makefile`, `program/eval-catalog.json`, `scripts/architecture/validate_eval_catalog.py`
- `rationale`: Configuration or prose that CI does not execute is not a gate.
- `consequences`: Coverage below 90%, an omitted/duplicate eval ID, unsupported status, missing evidence path or a recorded required-eval failure causes validation failure.


## DEC-2026-07-21-006 — Campaign creation is an internal draft operation

- `status`: `ACCEPTED`
- `scope`: `C3-API-006`
- `decision`: Tenant campaign creation produces only a server-owned `DRAFT` aggregate, an audit receipt, an internal outbox event and a replay receipt. It does not create a workspace, strategy, approval or external political effect.
- `evidence`: `backend/src/campaignos/campaigns/create_model.py`, `docs/api/campaign-create.md`
- `rationale`: Creating the aggregate must not manufacture downstream authority or skip guided intake.
- `consequences`: The route fixes status/version, rejects caller-owned authority fields and records `external_effects=NONE`.

## DEC-2026-07-21-007 — Replay identity includes purpose-bound authority

- `status`: `ACCEPTED`
- `scope`: `C3-API-006`
- `decision`: A campaign-create replay digest binds tenant, normalized request, principal, exact grant, approval receipt and authorization purpose; correlation remains audit metadata rather than replay identity.
- `evidence`: `backend/src/campaignos/campaigns/create_model.py`, `backend/tests/test_campaign_create_model.py`
- `rationale`: The same payload under changed authority or purpose is not the same authorized intent.
- `consequences`: Reusing a key after any bound authority change fails closed with `IDEMPOTENCY_CONFLICT`.

## DEC-2026-07-21-008 — Flush aggregate parent before FK-bound audit append

- `status`: `ACCEPTED`
- `scope`: `C3-API-006`
- `decision`: A newly created campaign is flushed inside the surrounding transaction before appending the audit event that references its composite tenant/campaign key.
- `evidence`: `backend/src/campaignos/campaigns/create_model.py`, `backend/tests/test_campaign_create_postgres.py`
- `rationale`: Real PostgreSQL exposed that independent ORM insert ordering could attempt the audit child before the new parent and violate the composite foreign key.
- `consequences`: Parent and evidence remain atomic; a later failure rolls back the flush and the whole unit of work.

## DEC-2026-07-21-009 — Keep bearer material server-only in the dynamic shell

- `status`: `ACCEPTED`
- `scope`: `C3-FRONT-001`
- `decision`: The Next.js shell reads opaque access-token material only from an HttpOnly server-side cookie and performs protected API calls from server-only modules with `cache: "no-store"` and bounded timeouts.
- `evidence`: `frontend/src/lib/api-client.ts`, `frontend/src/lib/shell-view-model.ts`, `scripts/frontend/review_dynamic_shell.py`
- `rationale`: Browser storage or rendered bearer material would expand token theft and cross-tenant exposure risk.
- `consequences`: No client component can import the API client or demo authority data; browser review verifies empty local/session storage and no bearer marker in HTML.

## DEC-2026-07-21-010 — Context selectors never create authority

- `status`: `ACCEPTED`
- `scope`: `C3-FRONT-001`
- `decision`: `campaignos_tenant_id` and `campaignos_campaign_id` select UI context only. The backend tenant identity, visible campaign page, exact grants and returned tenant/campaign identifiers remain authoritative.
- `evidence`: `frontend/src/lib/shell-view-model.ts`, `frontend/src/lib/contract-parsers.ts`
- `rationale`: Treating a selector or URL as authorization would create a BOLA boundary failure.
- `consequences`: Scope mismatches fail closed; navigation visibility is informational and every sensitive backend route must authorize independently.

## DEC-2026-07-21-011 — Preserve the static demo until explicit parity review

- `status`: `ACCEPTED`
- `scope`: `C3-FRONT-001`
- `decision`: The dynamic shell lives under `frontend/`; `web/` remains the manual-only `DEMO_NON_PRODUCTION` surface and visual reference. The dynamic runtime does not import legacy JavaScript.
- `evidence`: `docs/architecture/frontend-runtime.md`, `frontend/README.md`
- `rationale`: Replacing or deleting the static surface before parity would destroy review evidence and risk regressions.
- `consequences`: Legacy runtime is classified `SUPERSEDE`, visual assets `INTEGRATE`, and archive is permitted only after human parity acceptance.

## DEC-2026-07-21-012 — Validate upstream JSON at runtime

- `status`: `ACCEPTED`
- `scope`: `C3-FRONT-001`
- `decision`: TypeScript contracts are paired with exact runtime parsers for identity, membership, grants, campaign pages and readiness evidence.
- `evidence`: `frontend/src/lib/contract-parsers.ts`, `frontend/src/lib/contract-parsers.test.ts`
- `rationale`: TypeScript types disappear at runtime and cannot protect against malformed or cross-scope API responses.
- `consequences`: Unknown fields, cross-campaign grants, unsupported states and inconsistent readiness produce sanitized `INVALID_UPSTREAM_RESPONSE` failures.

## DEC-2026-07-21-013 — Locale changes load a new document

- `status`: `ACCEPTED`
- `scope`: `C3-FRONT-001`
- `decision`: The locale selector uses a dedicated client control with `window.location.assign` rather than an App Router soft transition.
- `evidence`: `frontend/src/components/locale-switcher.tsx`, `scripts/frontend/review_dynamic_shell.py`
- `rationale`: Next.js preserves root layouts during soft navigation; browser review exposed stale `html[lang]` after ES-to-EN transitions.
- `consequences`: Language changes recompute document language and metadata and are verified in the production build.

## DEC-2026-07-21-014 — Synthetic demo mode is local, visible and read-only

- `status`: `ACCEPTED`
- `scope`: `C3-FRONT-001`
- `decision`: `demo_read_only` uses fixed synthetic data, visibly labels every page and is rejected outside `development` and `test`.
- `evidence`: `frontend/src/lib/config.ts`, `frontend/src/lib/demo-data.ts`, `frontend/src/lib/config.test.ts`
- `rationale`: A convenient demo must never be confused with live authentication, campaign data or application authority.
- `consequences`: Shared/production configuration fails closed, and the shell exposes no domain forms or action buttons.


## DEC-2026-07-21-015 — Use daemonless image verification when nested Docker is unavailable

- `status`: `ACCEPTED`
- `scope`: `C3-FRONT-001`
- `decision`: When the sandbox namespace prevents the nested Docker daemon from preparing layers, verify the frontend Dockerfile with Buildah using `vfs` storage, `chroot` isolation and Docker image format rather than leaving image construction untested.
- `evidence`: `scripts/frontend/verify_frontend_image_buildah.sh`, `docs/testing/c3-front-001-evidence.md`
- `rationale`: The environment limitation concerns the daemon wrapper, not the Dockerfile; a daemonless build exercises the same stages, ownership, health metadata and runtime filesystem.
- `consequences`: Frontend image construction is locally evidenced and CI remains an independent Docker-engine check. The full Compose stack still requires CI or a compatible host.
