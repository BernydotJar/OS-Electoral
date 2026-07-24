# CampaignOS production-gap matrix

Status vocabulary:

- `PASS`: current authoritative evidence satisfies the gate.
- `PARTIAL`: useful implementation exists but does not satisfy production scope.
- `NOT_IMPLEMENTED`: required capability is absent.
- `NOT_VERIFIED`: evidence could not be obtained.
- `BLOCKED`: a prerequisite or human gate prevents completion.

No row marked `PARTIAL` is counted as production-ready.

## Product and application gates

| Gate | Current evidence | Status | Required proof |
|---|---|---:|---|
| Product boundaries approved | Canonical boundaries/non-goals and architecture ADRs exist; human/domain approval is absent | PARTIAL | Approved product boundaries and non-goals |
| Generic consultancy tenant model | Tenant-scoped campaign creation supports multiple campaigns, replay and cross-tenant slug independence under forced RLS | PARTIAL | Controlled tenant provisioning, portfolio administration, entitlements and staging evidence |
| Real authentication | Fixed-algorithm OIDC verifier plus verified-email invitation acceptance; a development-only local verifier enables functional testing but is prohibited outside development | PARTIAL | Live OIDC/Cognito login, delivery, recovery, MFA and provider operations |
| Real session validation | Cryptographic bearer validation plus digest-only application-session registration, expiry and local revocation pass locally/PostgreSQL | PARTIAL | Live login, rotation, recovery, device/session view and provider-token revocation |
| Tenant isolation | Composite schema constraints, transaction-local scope and forced RLS passed an isolated non-superuser test | PARTIAL | Application repository integration plus staging adversarial evidence |
| RBAC | Exact-purpose grants protect current campaign and identity lifecycle routes; invitation creates no implicit authority, membership revoke is atomic, and time-bound support enforces separation of duty and preserves unrelated access | PARTIAL | Reviewed grant-administration catalog, customer UI, live provider integration and enforcement on every remaining domain/worker action |
| PostgreSQL persistence | Identity/tenancy, campaign, workspace, identity lifecycle, guided intake, candidate, team, roadmap and Daily War Room have constrained-role PostgreSQL proof through revision `20260721_0011` | PARTIAL | Broader domains, managed-role rotation and RDS/staging transaction evidence |
| Database migrations | Alembic downgrade/upgrade/check reaches revision `20260721_0011`; lifecycle, intake, candidate, team, roadmap, strategy and Agent Run tables, forced RLS, constraints and indexes are exercised on a disposable PostgreSQL database twice | PARTIAL | Reviewed release policy, representative legacy-data rehearsal and staging forward/compatibility evidence |
| Versioned REST API | `/api/v1` additionally exposes identity, intake, candidate, team, roadmap, War Room, Strategy and Agent Run routes with exact authorization, idempotency/version preconditions, safe errors and typed OpenAPI | PARTIAL | Remaining bounded contexts, rate controls, customer identity UI and deployed verification |
| Dynamic frontend shell | Server-rendered ES/EN shell now includes compact authorized navigation, campaign selection and real guided-intake start/update/reload against PostgreSQL; unavailable modules are absent | PARTIAL | Exact-head PR/CI, live OIDC/session integration, broader mutation journeys, dev/staging deployment and human user acceptance |
| Background jobs | The tenant-explicit internal outbox worker uses leases, `SKIP LOCKED`, expired-claim recovery, bounded retries, dead-letter state and campaign/workspace/Agent Run evidence revalidation; no external delivery exists | PARTIAL | Worker administration, metrics/traces/alerts, staging replay/concurrency proof and reviewed transport contracts |
| Strategy and Decision Room | Revision `20260721_0009`, provenance classes, falsifiable hypotheses, comparable options, measurable objectives, contradiction/red-team gates, exact human decision receipts and ES/EN read-only surface pass local/PostgreSQL/browser gates | PARTIAL | Human review/merge, authenticated editing, independent methodology/domain acceptance, live identity and dev/staging environments |
| Guided onboarding | Revision `20260721_0005` plus a live development PostgreSQL/API/browser journey proves exact-authorized start, update, version conflict protection and persistence after reload in ES/EN | PARTIAL | Live OIDC, campaign creation/access lifecycle, independent human user acceptance and deployed environment evidence |
| Candidate workspace | Revision `20260721_0006`, independent-evidence contracts, contradictions, development, reputation risk, append-only version approvals and a read-only ES/EN executive surface pass local/PostgreSQL/browser and exact-head CI gates in PR `#93` | PARTIAL | Authenticated editing/approval, dedicated reviewer separation, human acceptance and live environments |
| Candidate Workspace | Deterministic candidate-brand aggregate | PARTIAL | Authenticated API-backed candidate experience |
| Team Builder | Revision `20260721_0007`, durable RACI/capacity/vacancy/onboarding/training records, non-authoritative access recommendations and PR `#94` exact-head CI | PARTIAL | Authenticated editing, human staffing acceptance, full Training Academy content and live environments |
| Strategy and Decision Room | Revision `20260721_0009`, provenance classes, falsifiable hypotheses, comparable options, measurable objectives, contradiction/red-team gates, exact human decision receipts and ES/EN read-only surface pass local/PostgreSQL/browser gates | PARTIAL | Human review/merge, authenticated editing, independent methodology/domain acceptance, live identity and dev/staging environments |
| War Room | Append-only exact-version daily snapshots, latest-read API, race protection and read-only ES/EN brief pass local/PostgreSQL/browser gates | PARTIAL | Authenticated creation UI, alerts/telemetry, human acceptance, publication/CI and live environments |
| Approval ledger | In-memory hash-chained prototype | PARTIAL | Durable append-only ledger, concurrency and authorized receipts |
| Training Academy | Static team guidance only | NOT_IMPLEMENTED | Learning paths, content governance, completions and assessments |
| AI runtime guardrails | Revision `20260721_0010`, provider abstraction, strict schema, versioned prompt policy, no-tool guards, append-only journal, exact API, idempotency, audit, RLS and prompt-injection hard evals pass locally/PostgreSQL | PARTIAL | Live provider/privacy review, staging leakage/fallback/load evidence, human disposition UX and independent acceptance |
| Spanish and English | Dynamic shell and functional guided-intake journey have tested ES/EN dictionaries, locale routes, persisted projection parity and browser accessibility | PARTIAL | Complete product dictionaries, locale-aware formats, remaining journeys and human language review |
| Accessibility | Demo and live functional journeys pass keyboard, mobile/reduced-motion, reflow and axe-core WCAG 2.2 A/AA checks; forms have explicit labels and visible focus | PARTIAL | Manual assistive-technology review, remaining critical journeys and independent WCAG 2.2 AA acceptance |

## Security, privacy and operations gates

| Gate | Current evidence | Status | Required proof |
|---|---|---:|---|
| Security review | Identity/BOLA/scope/expiry controls, database append-only role denial, CodeQL, secret, dependency, PostgreSQL and E2E gates pass locally/CI; open findings and human review remain | PARTIAL | Independent threat-based review, alert triage policy and zero critical/high findings |
| Privacy review | Machine-readable inventory covers 12 record types, purpose/owner/classification, review-required retention postures, seven political-data prohibitions and disabled live processors | PARTIAL | Qualified lawful-basis/retention decisions, rights workflows, deletion/restore verification and independent acceptance |
| Threat model | Canonical v0.2 covers 23 threats and links executable privacy/audit controls; no independent acceptance | PARTIAL | Reviewed model, owners, residual risks and independent verification |
| Rate limiting and abuse protection | Network API exists but has no principal/tenant limiter | NOT_IMPLEMENTED | Per-principal/tenant controls and abuse tests |
| Structured operational errors | RFC 9457-style API errors, correlation IDs and sanitized auth failures | PARTIAL | Domain error taxonomy, observability linkage and staging verification |
| Observability | Sanitized JSON logs, validated correlation/W3C trace context, bearer-protected low-cardinality metrics, worker/recovery textfiles and alert rules pass locally and in exact-head CI `30041495912` | PARTIAL | Deployed scraping/OTLP, dashboards, routing, retention, SLOs and staging exercises |
| Audit immutability | Tenant-serialized hash chain plus revision `20260721_0011` deny non-owner UPDATE/DELETE on six append-only journals under constrained PostgreSQL roles | PARTIAL | Owner break-glass governance, external integrity anchor, legal retention and restore verification |
| Backups | Native PostgreSQL 18 backup and isolated restore passed at exact head `bf722ee8e672a9e89a7e74a47465a8e6287602c8`; checksum artifact `8577394363` is retained | PARTIAL | Managed encrypted schedule, PITR, retention/deletion protection and operator evidence |
| Restore test | Exact-head job `89322226244` restored into isolated `*_restore_test`, compared Alembic/all public-table counts and verified cleanup | PARTIAL | Managed staging application/RLS smoke, measured and human-approved RPO/RTO |
| Incident response | Versioned observability/recovery runbook covers readiness, errors, latency, dead letters, backup and restore staleness | PARTIAL | Named on-call ownership, escalation/communications integration and staged exercises |
| Disaster recovery | None | NOT_IMPLEMENTED | Reviewed assumptions, dependencies, RPO/RTO and exercise |
| Load test | None | NOT_IMPLEMENTED | Representative workload, thresholds and results |
| SAST | Pinned CodeQL succeeds at recorded heads and is a required protected-main check | PARTIAL | Define alert ownership/triage SLA and independent security acceptance |
| Dependency scan | Hash lock, production-only `pip-audit`, npm audit, Dependabot updates, vulnerability alerts and automated security fixes are active; the locked audit is required on protected main | PARTIAL | Define alert/update ownership, SLA and production artifact scanning |
| Secret scan | GitHub scanning/push protection was observed previously; full-range CI scans and local Gitleaks `8.30.1` snapshot/stack scans pass | PARTIAL | Reverify repository settings with authenticated access, require the check and complete the response runbook |
| SBOM and image signing | Deterministic CycloneDX 1.6 SBOM, tracked-source manifest, in-toto/SLSA provenance, checksums and exact-source-head GitHub OIDC/Sigstore attestations pass | PARTIAL | Add published-image SBOM/signature/scan and define production retention/verification policy |

## Platform and delivery gates

| Gate | Current evidence | Status | Required proof |
|---|---|---:|---|
| Reproducible local development | Exact Python/tool pins, `uv.lock`, Make targets, `.env.example`, `make functional-dev`, Mac metadata exclusions and an enforced 90% coverage floor are verified | PASS | Re-run on supported clean developer hosts when pins change |
| Docker Compose baseline | Pinned API/PostgreSQL/S3Mock/Mailpit stack, initial bucket, migrations, health and hermetic E2E pass | PASS | Keep local-only classification; production adapters are separate gates |
| Terraform modules | Exact Terraform `1.15.8`, AWS provider `6.55.0`, locked bootstrap/platform roots, reusable modules, mocked plans and fail-closed policy checks | PARTIAL | Human review/merge, approved account/OIDC role, live plan and controlled environment evidence |
| Separate dev/staging/prod state | Private encrypted S3/KMS bootstrap and partial S3 backend with lockfile are modeled; no backend is created or initialized remotely | PARTIAL | Approved per-environment accounts/roles/state resources, live locking and access-control evidence |
| AWS dev | Plan-only IaC and mocks exist; no AWS account, credential, live provider plan, apply or runtime exists | NOT_VERIFIED | Authorized account/OIDC role, reviewed live plan/apply, smoke/security and cost evidence |
| AWS staging | None | NOT_IMPLEMENTED | Migration, security, load, restore and agent-eval evidence |
| AWS production | No approved deployment | BLOCKED | All gates plus explicit human approval |
| PR CI | Cumulative PR `#106` is in main; implementation checkpoint `bf722ee8e672a9e89a7e74a47465a8e6287602c8` in draft PR `#114` passed CampaignOS CI `30041495912`, visual review `30041495919` and the recovery job | PARTIAL | Human-review/merge C3-OBS and separately authorize desired protected-main check changes |
| Main CI | Integrated baseline is `main@ff38e996ba05b2ea4b5c034b44d084776736dad0`; PR `#114` recovery evidence is green and immutable artifact `8577394363` exists, but the branch is not merged | PARTIAL | Human review/merge, controlled dev deployment and post-deploy verification |
| Branch protection | Authenticated API verifies strict eight-check main protection, one approval, stale-review dismissal, conversation resolution, linear history, admin enforcement, no force push/deletion, selected Actions and mandatory SHA pinning; desired policy now includes a ninth Terraform check | PARTIAL | Human-authorized update to require the Terraform check after its exact-head CI context exists, then verify drift |
| Staging promotion | None | NOT_IMPLEMENTED | Controlled candidate promotion and manual acceptance |
| Production rollout/rollback | None | NOT_IMPLEMENTED | Backup, migration, progressive rollout, health and rollback criteria |
| Deployment runbook | Narrow operator guide | PARTIAL | Environment-specific deploy procedure and evidence capture |
| Rollback runbook | No production rollback runbook | NOT_IMPLEMENTED | Application, database and infrastructure rollback procedures |
| Human production approval | No approval receipt | BLOCKED | Explicit authorized, scoped and auditable approval |

## Program, documentation and domain gates

| Gate | Current evidence | Status | Required proof |
|---|---|---:|---|
| Program ledger | Manifest, graph, ledger and exact 33-item eval catalog reconcile fail closed under validators | PASS | Continue reconciliation with every GitHub/environment change |
| Required evals | Exact inventory records `5 PASS`, `17 PARTIAL`, `11 NOT_RUN`; session/invitation are partial local/PostgreSQL only and absent capabilities remain fail-closed | PARTIAL | Implement every underlying capability and obtain 33 reviewed PASS results with zero hard-gate failures |
| AutoSkills review | `autoskills@0.3.6` npm integrity/license/manifest reviewed; pinned dry-run proposed eleven skills, installed none and made no repository mutation | PASS | Per-skill payload, license, path and prompt-safety review plus explicit approval before any install |
| Context7 evidence | Foundation guidance, official cross-checks and installed pins are recorded | PASS | Repeat for new implementation dependencies |
| Required documentation tree | Campaign create/readiness, identity lifecycle, guided intake, candidate workspace and frontend runtime API/product/testing docs exist; broader product and operations paths remain incomplete | PARTIAL | Complete all required docs, ownership and stale-content validation |
| Obsolete-doc release gate | C2/main drift corrected in owned overview docs | PARTIAL | Repository-wide stale-doc scan and ownership policy |
| Political-science review | No approval record | NOT_IMPLEMENTED | Qualified human review |
| Sociological/anthropological review | No approval record | NOT_IMPLEMENTED | Qualified human review |
| Research-methodology review | Evidence methodology work exists, no production review | PARTIAL | Qualified human approval and limitations audit |
| Democratic-participation review | None | NOT_IMPLEMENTED | Qualified human review |
| Communication-ethics review | Prohibitions exist, no complete review | PARTIAL | Qualified human review and behavioral-claims register |
| Campaign–government firewall | Policy prohibition only | PARTIAL | Data/process controls and jurisdiction review |
| Consent and political-data review | Policy prohibition only | PARTIAL | Lawful-basis, expiry, withdrawal and audit controls |
| Team wellbeing and safety | No operational module | NOT_IMPLEMENTED | Workload, safety, incident and anti-surveillance controls |
| Information-integrity workflow | No operational module | NOT_IMPLEMENTED | Evidence-based intake, triage, response and review |
| Jurisdiction legal sign-off | None | BLOCKED | Qualified human sign-off before real campaign use |

## Completion rule

`production_status` may become `READY` only when every required production gate is `PASS`, no unsuperseded CI failure or open CRITICAL/HIGH finding remains, AWS production evidence is verified, and an authorized human records explicit production approval. GitHub Pages never satisfies that rule.
