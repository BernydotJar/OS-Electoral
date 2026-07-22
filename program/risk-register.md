# CampaignOS risk register

Production remains `BLOCKED`. Risks are not closed by local tests, green draft checks or documentation alone.

| ID | Severity | Status | Risk | Current controls/evidence | Required treatment | Owner |
|---|---|---|---|---|---|---|
| RISK-PLATFORM-001 | CRITICAL | OPEN | No verified AWS dev/staging/production runtime, Terraform baseline, backup or restore evidence exists. | Local runtime, Compose definition, isolated PostgreSQL proof. | Implement reviewed Terraform, verify dev/staging, backup/restore and recovery evidence before any production gate. | WS-12 / WS-14 |
| RISK-CI-001 | HIGH | RESOLVED | Strict protected main, selected SHA-pinned Actions, vulnerability governance and exact-source-head SBOM/provenance/Sigstore attestation are active. | Versioned policy, 11 tests, 17 live-setting comparisons, CI `29880153335`, job `88799003125` and digest attestation API lookup pass. | Preserve periodic drift verification, required checks and human review; production remains blocked by separate platform/history/environment gates. | WS-02 |
| RISK-AUDIT-001 | HIGH | OPEN | Audit append-only semantics are application-enforced; privileged direct database mutation could rewrite/delete receipts or chain heads. | Tenant-serialized monotonic hash chain; regression and PostgreSQL tests. | Add database-level mutation denial, privileged-access controls, external integrity anchoring, retention and restore verification. | WS-04 / WS-13 |
| RISK-EVAL-001 | HIGH | OPEN | Thirteen required evals are `NOT_RUN` and fifteen are only `PARTIAL`; passing implemented slices cannot imply product-wide safety. | Exact fail-closed 33-item catalog; session/invitation remain partial local/PostgreSQL only. | Implement underlying capabilities and independently review every eval to PASS with zero hard-gate failures. | WS-11 / WS-13 / WS-14 |
| RISK-IDENTITY-001 | HIGH | OPEN | Provider-neutral invitation, application-session, membership-revocation and time-bound support controls are verified locally/PostgreSQL, but no live login/recovery/MFA, email delivery, provider revocation or customer administration exists. | Verified-email invitation acceptance, digest-only sessions, exact grants, separation of duty, RLS, expiry and rollback tests. | Publish/review C3-IAM-002, then integrate a live provider and customer UX under environment/human gates. | WS-03 |
| RISK-DOMAIN-001 | HIGH | OPEN | Guided intake, Candidate Workspace and Team Builder are exact-head CI-green; roadmap, Daily War Room and the evidence-first Strategy Decision Room have local/PostgreSQL/browser proof, but authenticated mutation journeys, human acceptance and broader campaign domains remain incomplete. | Campaign, workspace/readiness, persisted intake, evidence-governed candidate/team records, roadmap/snapshots and read-only shell surfaces pass local/PostgreSQL/browser gates. | Review candidate work under human gates, then continue narrow authorized journeys with BOLA, audit, accessibility and eval evidence. | WS-04 / WS-05 / WS-06 / WS-07 |
| RISK-WORKER-001 | HIGH | OPEN | Internal outbox worker lacks reviewed external transport, administration, production observability and staging concurrency evidence. | Lease/retry/dead-letter and replay tests on draft branch. | Keep external effects disabled; add administration/observability/staging proof before any transport. | WS-05 / WS-14 |
| RISK-LOCAL-DOCKER-001 | MEDIUM | OPEN_LOCAL | The sandbox's nested Docker daemon cannot prepare the complete Compose stack because the outer namespace rejects layer operations. | `docker compose config`, native PostgreSQL, prior stack CI and a daemonless Buildah `vfs`/`chroot` frontend image build plus smoke test pass. | Retain CI or a compatible host for the full Compose proof; do not list frontend image construction as blocked while the validated Buildah path remains green. | WS-02 |
| RISK-FRONT-001 | MEDIUM | OPEN | The dynamic shell is draft-PR CI-green and now includes read-only guided-intake and candidate executive surfaces, but browser context cookies are not a trusted tenant portfolio workflow and complete mutation journeys are absent. | Demo mode is forbidden in shared/production, token access is server-only, runtime contracts fail closed, exact campaign-bound navigation and automated WCAG review pass. | Integrate live session/tenant selection, authenticated onboarding/candidate editing and independent accessibility/user acceptance before any deployment claim. | WS-03 / WS-06 / WS-07 |
| RISK-HISTORICAL-CI-001 | HIGH | OPEN | Six historical failed runs remain unsuperseded and production-blocking. | Manifest preserves IDs and conclusions. | Add explicit scope-equivalent `superseded_by`, evidence, reviewer, date and reason or remediate remaining failures. | WS-02 / WS-15 |
| RISK-HUMAN-GATES-001 | HIGH | OPEN | No independent security/privacy/domain/legal review or authorized production approval exists. | Human gates remain fail-closed in program state. | Obtain scoped independent reviews and explicit production approval only after all technical gates pass. | WS-13 / WS-15 |

## C3-TEAM-001 residual risk — human staffing and access acceptance

- **Status:** OPEN / non-blocking for continued pre-production development.
- **Evidence:** Team Builder is locally/PostgreSQL verified and read-only in the shell, but authenticated editing, customer acceptance and full Training Academy content are not implemented.
- **Mitigation:** preserve `authority_effect=NONE`, require separate exact authorization, and keep production `BLOCKED` until live identity, human review and environment gates pass.


## C3-OPS-001 residual risk — coordination without live operational acceptance

- **Status:** OPEN / non-blocking for continued pre-production development.
- **Evidence:** roadmap and snapshot contracts, APIs, PostgreSQL and read-only browser journey pass; authenticated editing, alerts, strategy approval and customer acceptance are absent.
- **Mitigation:** keep all actions advisory/read-only in the shell, preserve exact authorization and `external_effects=NONE`, and keep production `BLOCKED`.


## C3-STRATEGY-001 residual risk — internal decision without live acceptance

- **Status:** OPEN / non-blocking for continued pre-production development.
- **Evidence:** contracts, durable API/SQL adapter, PostgreSQL races/RLS, read-only ES/EN browser journey and internal exact-version decision receipts pass.
- **Mitigation:** keep the browser read-only, require separate exact authorization for any future mutation, preserve `authority_effect=NONE`/`external_effects=NONE`, and keep production `BLOCKED` until human, identity, environment and release gates pass.


## C3-API-001 residual risk — internal worker without control plane

- **Status:** OPEN / non-blocking for the internal API baseline; production-blocking through existing observability/platform gates.
- **Evidence:** tenant-explicit leases, retries, dead-letter, RLS and internal envelope validation pass; no network transport is registered.
- **Mitigation:** keep external transport absent, require a future human-audited dead-letter/replay workflow, add telemetry and operational ownership in `C3-OBS-001`, and retain production `BLOCKED` until all release gates pass.


## C3-AGENT-001 residual risk — no live provider/privacy acceptance

- **Status:** OPEN / non-blocking for continued bounded pre-production development; production-blocking through privacy, observability and human gates.
- **Evidence:** strict no-tool contracts, prompt-injection guards, append-only journal, exact authorization, one-call idempotent replay and forced RLS pass locally/PostgreSQL with an unavailable no-network provider.
- **Mitigation:** keep live providers and fallback disabled until processor, residency, retention, no-training, leakage, staging and independent privacy/security reviews pass; require a separate authenticated human-disposition workflow and preserve `authority_effect=NONE`/`external_effects=NONE`.
