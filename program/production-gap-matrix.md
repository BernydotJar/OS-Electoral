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
| Generic consultancy tenant model | Two deterministic tenant fixtures | PARTIAL | Durable multi-campaign tenant model and provisioning tests |
| Real authentication | Fixed-algorithm OIDC ID-token verifier and protected identity endpoint; no live provider/login flow | PARTIAL | OIDC/Cognito login, invitation and recovery flows |
| Real session validation | Cryptographic bearer ID-token validation is covered; no server session/rotation/revocation lifecycle | PARTIAL | Issuer/audience/signature/expiry validation plus session revocation tests |
| Tenant isolation | Composite schema constraints, transaction-local scope and forced RLS passed an isolated non-superuser test | PARTIAL | Application repository integration plus staging adversarial evidence |
| RBAC | PostgreSQL-backed active membership and exact-purpose grants protect campaign list/get/update, workspace creation and campaign readiness; roles never imply permission | PARTIAL | Grant administration, reviewed role catalog, support elevation and enforcement on every remaining domain/worker action |
| PostgreSQL persistence | Identity/tenancy plus campaign read/write, idempotency, workspace, audit, outbox and readiness adapters are merged, draft-green or locally verified; constrained-role PostgreSQL readiness/audit proof passes | PARTIAL | Campaign creation and broader domain adapters, managed-role rotation and RDS/staging transaction evidence |
| Database migrations | Alembic environment and initial migration pass downgrade/upgrade/check locally | PARTIAL | Reviewed release policy plus staging forward/compatibility rehearsal |
| Versioned REST API | `/api/v1` exposes health, dependency readiness, identity, tenant authorization, protected campaign list/get/update, draft workspace creation and local audited campaign readiness with safe errors and typed OpenAPI | PARTIAL | Campaign creation, broader bounded contexts, reviewed OpenAPI policy, rate controls and deployed verification |
| Background jobs | Draft PR `#85` adds a tenant-explicit internal outbox worker with leases, `SKIP LOCKED`, expired-claim recovery, bounded retries, dead-letter state and evidence revalidation; no external delivery exists | PARTIAL | Worker administration, metrics/traces/alerts, staging replay/concurrency proof and reviewed transport contracts |
| Object storage | Typed configuration and initialized Adobe S3Mock local harness only | PARTIAL | Production adapter, signed operations, MIME/size validation, scan strategy and KMS/retention controls |
| Guided onboarding | Deterministic operational readiness projection exists; no persisted save/resume intake wizard or evidence collection journey | PARTIAL | Save/resume intake, evidence requirements, known unknowns and guided next actions |
| Candidate Workspace | Deterministic candidate-brand aggregate | PARTIAL | Authenticated API-backed candidate experience |
| Team Builder | Static team command-center snapshot | PARTIAL | Durable roles, RACI, capacity, onboarding and authorization |
| Roadmap/workstreams | Program fallback graph; no campaign roadmap service | PARTIAL | Campaign-scoped tasks, dependencies, critical path and owners |
| War Room | Static read-only demo and deterministic brief | PARTIAL | API-backed governed check-ins and live scoped state |
| Approval ledger | In-memory hash-chained prototype | PARTIAL | Durable append-only ledger, concurrency and authorized receipts |
| Training Academy | Static team guidance only | NOT_IMPLEMENTED | Learning paths, content governance, completions and assessments |
| AI runtime guardrails | Deterministic extraction/guard prototypes | PARTIAL | Provider abstraction, schema enforcement, audit metadata and hard eval suite |
| Spanish and English | UI primarily Spanish with hard-coded strings | NOT_IMPLEMENTED | Translation keys, parity tests and locale-aware formats |
| Accessibility | Static Playwright review and draft-PR browser run `29706162740` pass | PARTIAL | WCAG 2.2 AA audit across production critical paths |

## Security, privacy and operations gates

| Gate | Current evidence | Status | Required proof |
|---|---|---:|---|
| Security review | Adversarial review and regression fixes are retained; CodeQL, secret, dependency, PostgreSQL and E2E checks pass at merged and active draft heads through run `29807878943`; open findings remain | PARTIAL | Independent threat-based review, alert triage policy and zero critical/high findings |
| Privacy review | Prohibited capabilities encoded in prototype | PARTIAL | Data inventory, lawful-purpose controls, retention and deletion verification |
| Threat model | Canonical draft covers 23 threats and current-control status; no independent acceptance | PARTIAL | Reviewed model, owners, residual risks and verification links |
| Rate limiting and abuse protection | Network API exists but has no principal/tenant limiter | NOT_IMPLEMENTED | Per-principal/tenant controls and abuse tests |
| Structured operational errors | RFC 9457-style API errors, correlation IDs and sanitized auth failures | PARTIAL | Domain error taxonomy, observability linkage and staging verification |
| Observability | Offline audit read model | PARTIAL | Logs, metrics, traces, dashboards, alerts and SLOs |
| Audit immutability | PostgreSQL campaign/workspace/readiness events use a tenant-serialized monotonic hash chain; application enforcement can still be bypassed by privileged direct database mutation | PARTIAL | Database-level append-only controls, protected integrity anchor, retention and restore verification |
| Backups | None | NOT_IMPLEMENTED | Automated encrypted backups and retention evidence |
| Restore test | None | NOT_IMPLEMENTED | Successful measured restore with RPO/RTO and audit verification |
| Incident response | Narrow corruption runbook | PARTIAL | Full incident roles, escalation, communications and exercises |
| Disaster recovery | None | NOT_IMPLEMENTED | Reviewed assumptions, dependencies, RPO/RTO and exercise |
| Load test | None | NOT_IMPLEMENTED | Representative workload, thresholds and results |
| SAST | Pinned CodeQL succeeds at recorded Foundation, IAM and active API-stack heads | PARTIAL | Required-check enforcement and alert triage policy |
| Dependency scan | Hash lock, production-only `pip-audit` and uv Dependabot are active; recorded merged and draft CI heads pass the locked audit | PARTIAL | Required-check enforcement and alert/update policy evidence |
| Secret scan | GitHub scanning/push protection was observed previously; full-range CI scans and local Gitleaks `8.30.1` snapshot/stack scans pass | PARTIAL | Reverify repository settings with authenticated access, require the check and complete the response runbook |
| SBOM and image signing | Pinned non-root image builds locally; no SBOM/provenance/signature | NOT_IMPLEMENTED | Immutable published image, SBOM, provenance/signing policy |

## Platform and delivery gates

| Gate | Current evidence | Status | Required proof |
|---|---|---:|---|
| Reproducible local development | Exact Python/tool pins, `uv.lock`, Make targets, `.env.example` and an enforced 90% coverage floor are verified | PASS | Re-run on supported clean developer hosts when pins change |
| Docker Compose baseline | Pinned API/PostgreSQL/S3Mock/Mailpit stack, initial bucket, migrations, health and hermetic E2E pass | PASS | Keep local-only classification; production adapters are separate gates |
| Terraform modules | No `infra/` at assessment point | NOT_IMPLEMENTED | Required reusable modules with pinned providers |
| Separate dev/staging/prod state | None | NOT_IMPLEMENTED | Separate credentials/state, encryption and locking |
| AWS dev | AWS session expired; no IaC evidence | NOT_VERIFIED | Reviewed plan/apply and smoke evidence |
| AWS staging | None | NOT_IMPLEMENTED | Migration, security, load, restore and agent-eval evidence |
| AWS production | No approved deployment | BLOCKED | All gates plus explicit human approval |
| PR CI | PRs `#72`, `#73` and `#83` merged with green recorded checks; draft stack `#84` -> `#85` -> `#86` is green; current readiness branch has no PR or CI yet | PARTIAL | Publish current branch for review, obtain green checks, human review and required-check enforcement on protected main |
| Main CI | CampaignOS CI push run `29803405277` succeeded at `main@d0719c9`; no controlled environment deployment follows it | PARTIAL | Required-check enforcement, immutable artifact evidence, controlled dev deployment and post-deploy verification |
| Branch protection | Public rulesets are empty; branch-protection and Actions-permission endpoints require authenticated repository-settings access, so current enforcement is unverified | NOT_VERIFIED | Authenticated ruleset evidence with required review and checks |
| Staging promotion | None | NOT_IMPLEMENTED | Controlled candidate promotion and manual acceptance |
| Production rollout/rollback | None | NOT_IMPLEMENTED | Backup, migration, progressive rollout, health and rollback criteria |
| Deployment runbook | Narrow operator guide | PARTIAL | Environment-specific deploy procedure and evidence capture |
| Rollback runbook | No production rollback runbook | NOT_IMPLEMENTED | Application, database and infrastructure rollback procedures |
| Human production approval | No approval receipt | BLOCKED | Explicit authorized, scoped and auditable approval |

## Program, documentation and domain gates

| Gate | Current evidence | Status | Required proof |
|---|---|---:|---|
| Program ledger | Manifest, graph, ledger and exact 33-item eval catalog reconcile fail closed under validators | PASS | Continue reconciliation with every GitHub/environment change |
| Required evals | Exact inventory records `5 PASS`, `8 PARTIAL`, `20 NOT_RUN`; absent capabilities remain fail-closed | PARTIAL | Implement every underlying capability and obtain 33 reviewed PASS results with zero hard-gate failures |
| AutoSkills review | `autoskills@0.3.6` npm integrity/license/manifest reviewed; pinned dry-run proposed eleven skills, installed none and made no repository mutation | PASS | Per-skill payload, license, path and prompt-safety review plus explicit approval before any install |
| Context7 evidence | Foundation guidance, official cross-checks and installed pins are recorded | PASS | Repeat for new implementation dependencies |
| Required documentation tree | Campaign readiness API/testing docs now exist, but most canonical goal paths remain absent | PARTIAL | Complete all required docs, ownership and stale-content validation |
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
