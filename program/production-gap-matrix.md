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
| RBAC | PostgreSQL-backed active membership/role/exact-purpose grant loading and tenant identity endpoint; roles never imply permission | PARTIAL | Grant administration, reviewed role catalog and enforcement on every domain/worker action |
| PostgreSQL persistence | Initial SQLAlchemy identity/tenancy/campaign/audit/outbox model and local PostgreSQL proof under a separate constrained runtime role | PARTIAL | Domain adapters, managed-role rotation and RDS/staging transaction evidence |
| Database migrations | Alembic environment and initial migration pass downgrade/upgrade/check locally | PARTIAL | Reviewed release policy plus staging forward/compatibility rehearsal |
| Versioned REST API | `/api/v1` FastAPI health/readiness plus global and tenant-scoped identity/authorization surfaces with safe errors and contract tests | PARTIAL | Authenticated campaign-domain endpoints with reviewed OpenAPI, pagination, concurrency and rate controls |
| Background jobs | None | NOT_IMPLEMENTED | Worker runtime, retry/idempotency/dead-letter behavior |
| Object storage | Typed configuration and initialized Adobe S3Mock local harness only | PARTIAL | Production adapter, signed operations, MIME/size validation, scan strategy and KMS/retention controls |
| Guided onboarding | No persisted wizard | NOT_IMPLEMENTED | Save/resume intake and readiness eval |
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
| Security review | Adversarial code review and regression fixes; CodeQL/secret/dependency jobs passed in draft-PR run `29706162737`; open findings remain | PARTIAL | Independent threat-based review, alert triage policy and zero critical/high findings |
| Privacy review | Prohibited capabilities encoded in prototype | PARTIAL | Data inventory, lawful-purpose controls, retention and deletion verification |
| Threat model | Canonical draft covers 23 threats and current-control status; no independent acceptance | PARTIAL | Reviewed model, owners, residual risks and verification links |
| Rate limiting and abuse protection | Network API exists but has no principal/tenant limiter | NOT_IMPLEMENTED | Per-principal/tenant controls and abuse tests |
| Structured operational errors | RFC 9457-style API errors, correlation IDs and sanitized auth failures | PARTIAL | Domain error taxonomy, observability linkage and staging verification |
| Observability | Offline audit read model | PARTIAL | Logs, metrics, traces, dashboards, alerts and SLOs |
| Audit immutability | Unkeyed in-memory/file hash chains | PARTIAL | Durable append-only storage and protected external integrity anchor |
| Backups | None | NOT_IMPLEMENTED | Automated encrypted backups and retention evidence |
| Restore test | None | NOT_IMPLEMENTED | Successful measured restore with RPO/RTO and audit verification |
| Incident response | Narrow corruption runbook | PARTIAL | Full incident roles, escalation, communications and exercises |
| Disaster recovery | None | NOT_IMPLEMENTED | Reviewed assumptions, dependencies, RPO/RTO and exercise |
| Load test | None | NOT_IMPLEMENTED | Representative workload, thresholds and results |
| SAST | Pinned CodeQL job completed successfully in draft-PR run `29706162737` | PARTIAL | Required-check enforcement and alert triage policy |
| Dependency scan | Hash lock, production-only `pip-audit` and uv Dependabot definition; draft-PR run `29706162737` passed | PARTIAL | Required-check enforcement and alert/update policy evidence |
| Secret scan | GitHub scanning/push protection observed; full-range Gitleaks passed in draft-PR run `29706162737` | PARTIAL | Required-check enforcement and response runbook |
| SBOM and image signing | Pinned non-root image builds locally; no SBOM/provenance/signature | NOT_IMPLEMENTED | Immutable published image, SBOM, provenance/signing policy |

## Platform and delivery gates

| Gate | Current evidence | Status | Required proof |
|---|---|---:|---|
| Reproducible local development | Exact Python/tool pins, `uv.lock`, Make targets and `.env.example` verified | PASS | Re-run on supported clean developer hosts when pins change |
| Docker Compose baseline | Pinned API/PostgreSQL/S3Mock/Mailpit stack, initial bucket, migrations, health and hermetic E2E pass | PASS | Keep local-only classification; production adapters are separate gates |
| Terraform modules | No `infra/` at assessment point | NOT_IMPLEMENTED | Required reusable modules with pinned providers |
| Separate dev/staging/prod state | None | NOT_IMPLEMENTED | Separate credentials/state, encryption and locking |
| AWS dev | AWS session expired; no IaC evidence | NOT_VERIFIED | Reviewed plan/apply and smoke evidence |
| AWS staging | None | NOT_IMPLEMENTED | Migration, security, load, restore and agent-eval evidence |
| AWS production | No approved deployment | BLOCKED | All gates plus explicit human approval |
| PR CI | Draft PR `#72` runs `29706162737` and `29706162740` are green at recorded head `e8adf4c` | PARTIAL | Human review plus required-check enforcement on protected main |
| Main CI | Same workflow triggers on `main`; no observed run yet and no deployment job | PARTIAL | Immutable green build evidence, then controlled dev deploy/post-deploy verification |
| Branch protection | API reported none | NOT_IMPLEMENTED | Ruleset with required review and checks |
| Staging promotion | None | NOT_IMPLEMENTED | Controlled candidate promotion and manual acceptance |
| Production rollout/rollback | None | NOT_IMPLEMENTED | Backup, migration, progressive rollout, health and rollback criteria |
| Deployment runbook | Narrow operator guide | PARTIAL | Environment-specific deploy procedure and evidence capture |
| Rollback runbook | No production rollback runbook | NOT_IMPLEMENTED | Application, database and infrastructure rollback procedures |
| Human production approval | No approval receipt | BLOCKED | Explicit authorized, scoped and auditable approval |

## Program, documentation and domain gates

| Gate | Current evidence | Status | Required proof |
|---|---|---:|---|
| Program ledger | Manifest, graph and ledger reconcile fail closed under local/CI validator | PASS | Continue reconciliation with every GitHub/environment change |
| AutoSkills review | Dry-run reviewed; no install | PASS | Re-review only if installation is proposed |
| Context7 evidence | Foundation guidance, official cross-checks and installed pins are recorded | PASS | Repeat for new implementation dependencies |
| Required documentation tree | Most canonical goal paths absent | NOT_IMPLEMENTED | All required docs current and validated |
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
