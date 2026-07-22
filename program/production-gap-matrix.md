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
| Real authentication | Fixed-algorithm OIDC verifier plus verified-email, tenant-scoped local invitation acceptance; no live provider/login/recovery/MFA flow | PARTIAL | Live OIDC/Cognito login, delivery, recovery, MFA and provider operations |
| Real session validation | Cryptographic bearer validation plus digest-only application-session registration, expiry and local revocation pass locally/PostgreSQL | PARTIAL | Live login, rotation, recovery, device/session view and provider-token revocation |
| Tenant isolation | Composite schema constraints, transaction-local scope and forced RLS passed an isolated non-superuser test | PARTIAL | Application repository integration plus staging adversarial evidence |
| RBAC | Exact-purpose grants protect current campaign and identity lifecycle routes; invitation creates no implicit authority, membership revoke is atomic, and time-bound support enforces separation of duty and preserves unrelated access | PARTIAL | Reviewed grant-administration catalog, customer UI, live provider integration and enforcement on every remaining domain/worker action |
| PostgreSQL persistence | Identity/tenancy, campaign, workspace, identity lifecycle, guided intake, candidate, team, roadmap and Daily War Room have constrained-role PostgreSQL proof through revision `20260721_0010` | PARTIAL | Broader domains, managed-role rotation and RDS/staging transaction evidence |
| Database migrations | Alembic downgrade/upgrade/check reaches revision `20260721_0010`; lifecycle, intake, candidate, team, roadmap, strategy and Agent Run tables, forced RLS, constraints and indexes are exercised on a disposable PostgreSQL database twice | PARTIAL | Reviewed release policy, representative legacy-data rehearsal and staging forward/compatibility evidence |
| Versioned REST API | `/api/v1` additionally exposes identity, intake, candidate, team, roadmap, War Room, Strategy and Agent Run routes with exact authorization, idempotency/version preconditions, safe errors and typed OpenAPI | PARTIAL | Remaining bounded contexts, rate controls, customer identity UI and deployed verification |
| Dynamic frontend shell | Draft PRs through `#98` are exact-head CI-green; read-only ES/EN intake, candidate, team, roadmap and War Room surfaces are server-rendered, responsive and fail closed | PARTIAL | Human review/merge, live OIDC/session integration, trusted tenant selection, complete mutation journeys, dev/staging deployment and user acceptance |
| Background jobs | The tenant-explicit internal outbox worker uses leases, `SKIP LOCKED`, expired-claim recovery, bounded retries, dead-letter state and campaign/workspace/Agent Run evidence revalidation; no external delivery exists | PARTIAL | Worker administration, metrics/traces/alerts, staging replay/concurrency proof and reviewed transport contracts |
| Strategy and Decision Room | Revision `20260721_0009`, provenance classes, falsifiable hypotheses, comparable options, measurable objectives, contradiction/red-team gates, exact human decision receipts and ES/EN read-only surface pass local/PostgreSQL/browser gates | PARTIAL | Human review/merge, authenticated editing, independent methodology/domain acceptance, live identity and dev/staging environments |
| Guided onboarding | Revision `20260721_0005`, exact-authorized save/resume/read/update, deterministic eight-step assessment, research-first actions and a read-only ES/EN roadmap pass local/PostgreSQL/browser gates | PARTIAL | Authenticated non-technical editing, human user acceptance and live environment evidence |
| Candidate workspace | Revision `20260721_0006`, independent-evidence contracts, contradictions, development, reputation risk, append-only version approvals and a read-only ES/EN executive surface pass local/PostgreSQL/browser and exact-head CI gates in PR `#93` | PARTIAL | Authenticated editing/approval, dedicated reviewer separation, human acceptance and live environments |
| Candidate Workspace | Deterministic candidate-brand aggregate | PARTIAL | Authenticated API-backed candidate experience |
| Team Builder | Revision `20260721_0007`, durable RACI/capacity/vacancy/onboarding/training records, non-authoritative access recommendations and PR `#94` exact-head CI | PARTIAL | Authenticated editing, human staffing acceptance, full Training Academy content and live environments |
| Strategy and Decision Room | Revision `20260721_0009`, provenance classes, falsifiable hypotheses, comparable options, measurable objectives, contradiction/red-team gates, exact human decision receipts and ES/EN read-only surface pass local/PostgreSQL/browser gates | PARTIAL | Human review/merge, authenticated editing, independent methodology/domain acceptance, live identity and dev/staging environments |
| War Room | Append-only exact-version daily snapshots, latest-read API, race protection and read-only ES/EN brief pass local/PostgreSQL/browser gates | PARTIAL | Authenticated creation UI, alerts/telemetry, human acceptance, publication/CI and live environments |
| Approval ledger | In-memory hash-chained prototype | PARTIAL | Durable append-only ledger, concurrency and authorized receipts |
| Training Academy | Static team guidance only | NOT_IMPLEMENTED | Learning paths, content governance, completions and assessments |
| AI runtime guardrails | Revision `20260721_0010`, provider abstraction, strict schema, versioned prompt policy, no-tool guards, append-only journal, exact API, idempotency, audit, RLS and prompt-injection hard evals pass locally/PostgreSQL | PARTIAL | Live provider/privacy review, staging leakage/fallback/load evidence, human disposition UX and independent acceptance |
| Spanish and English | Dynamic shell has structurally tested ES/EN dictionaries, locale routes, document language and browser parity; legacy/static and future journeys are not fully localized | PARTIAL | Complete product dictionaries, locale-aware formats, error/content parity and human language review |
| Accessibility | Static review remains green; dynamic shell passes keyboard skip-link, mobile/reduced-motion, overflow and axe-core WCAG 2.2 A/AA checks in ES/EN | PARTIAL | Manual assistive-technology review, production critical-path coverage and independent WCAG 2.2 AA acceptance |

## Security, privacy and operations gates

| Gate | Current evidence | Status | Required proof |
|---|---|---:|---|
| Security review | Adversarial identity rollback/BOLA/scope/expiry tests pass locally; CodeQL, secret, dependency, PostgreSQL and E2E checks pass through frontend run `29856835515`; open findings remain | PARTIAL | Independent threat-based review, alert triage policy and zero critical/high findings |
| Privacy review | Prohibited capabilities encoded in prototype | PARTIAL | Data inventory, lawful-purpose controls, retention and deletion verification |
| Threat model | Canonical draft covers 23 threats and current-control status; no independent acceptance | PARTIAL | Reviewed model, owners, residual risks and verification links |
| Rate limiting and abuse protection | Network API exists but has no principal/tenant limiter | NOT_IMPLEMENTED | Per-principal/tenant controls and abuse tests |
| Structured operational errors | RFC 9457-style API errors, correlation IDs and sanitized auth failures | PARTIAL | Domain error taxonomy, observability linkage and staging verification |
| Observability | Offline audit read model | PARTIAL | Logs, metrics, traces, dashboards, alerts and SLOs |
| Audit immutability | PostgreSQL campaign create/update, workspace and readiness events use a tenant-serialized monotonic hash chain with purpose-bound authority evidence; privileged direct database mutation can still bypass application enforcement | PARTIAL | Database-level append-only controls, protected integrity anchor, retention and restore verification |
| Backups | None | NOT_IMPLEMENTED | Automated encrypted backups and retention evidence |
| Restore test | None | NOT_IMPLEMENTED | Successful measured restore with RPO/RTO and audit verification |
| Incident response | Narrow corruption runbook | PARTIAL | Full incident roles, escalation, communications and exercises |
| Disaster recovery | None | NOT_IMPLEMENTED | Reviewed assumptions, dependencies, RPO/RTO and exercise |
| Load test | None | NOT_IMPLEMENTED | Representative workload, thresholds and results |
| SAST | Pinned CodeQL succeeds at recorded heads and is a required protected-main check | PARTIAL | Define alert ownership/triage SLA and independent security acceptance |
| Dependency scan | Hash lock, production-only `pip-audit`, npm audit, Dependabot updates, vulnerability alerts and automated security fixes are active; the locked audit is required on protected main | PARTIAL | Define alert/update ownership, SLA and production artifact scanning |
| Secret scan | GitHub scanning/push protection was observed previously; full-range CI scans and local Gitleaks `8.30.1` snapshot/stack scans pass | PARTIAL | Reverify repository settings with authenticated access, require the check and complete the response runbook |
| SBOM and image signing | Deterministic CycloneDX 1.6 SBOM, tracked-source manifest, in-toto/SLSA provenance, checksums and exact-source-head GitHub OIDC/Sigstore attestations pass | PARTIAL | Add published-image SBOM/signature/scan and define production retention/verification policy |

## Platform and delivery gates

| Gate | Current evidence | Status | Required proof |
|---|---|---:|---|
| Reproducible local development | Exact Python/tool pins, `uv.lock`, Make targets, `.env.example` and an enforced 90% coverage floor are verified | PASS | Re-run on supported clean developer hosts when pins change |
| Docker Compose baseline | Pinned API/PostgreSQL/S3Mock/Mailpit stack, initial bucket, migrations, health and hermetic E2E pass | PASS | Keep local-only classification; production adapters are separate gates |
| Terraform modules | Exact Terraform `1.15.8`, AWS provider `6.55.0`, locked bootstrap/platform roots, reusable modules, mocked plans and fail-closed policy checks | PARTIAL | Human review/merge, approved account/OIDC role, live plan and controlled environment evidence |
| Separate dev/staging/prod state | Private encrypted S3/KMS bootstrap and partial S3 backend with lockfile are modeled; no backend is created or initialized remotely | PARTIAL | Approved per-environment accounts/roles/state resources, live locking and access-control evidence |
| AWS dev | Plan-only IaC and mocks exist; no AWS account, credential, live provider plan, apply or runtime exists | NOT_VERIFIED | Authorized account/OIDC role, reviewed live plan/apply, smoke/security and cost evidence |
| AWS staging | None | NOT_IMPLEMENTED | Migration, security, load, restore and agent-eval evidence |
| AWS production | No approved deployment | BLOCKED | All gates plus explicit human approval |
| PR CI | PRs `#72`, `#73`, `#83` are merged; draft stack through `#99` is exact-head CI-green; the C3-INFRA branch defines a ninth plan-only Terraform check | PARTIAL | Publish C3-INFRA, pass exact-head CI/E2E, human-review the stack and separately authorize the protected-main check change |
| Main CI | CampaignOS CI push run `29803405277` succeeded at `main@d0719c9`; no controlled environment deployment follows it | PARTIAL | Required-check enforcement, immutable artifact evidence, controlled dev deployment and post-deploy verification |
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
| Required evals | Exact inventory records `5 PASS`, `12 PARTIAL`, `16 NOT_RUN`; session/invitation are partial local/PostgreSQL only and absent capabilities remain fail-closed | PARTIAL | Implement every underlying capability and obtain 33 reviewed PASS results with zero hard-gate failures |
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
