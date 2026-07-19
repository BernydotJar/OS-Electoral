# CampaignOS bounded contexts

Status: **PROPOSED TARGET MAP**
Last updated: `2026-07-19`

CampaignOS begins as one deployable modular monolith with explicit module ownership. Contexts communicate through application interfaces and recorded domain events, never by importing another context's persistence implementation.

| Context | Owns | Public boundary | Must not own |
|---|---|---|---|
| Identity and Access | external subject links, sessions, membership and grants | authenticate principal; authorize scoped action | campaign content or IdP-only roles |
| Tenant and Consultancy | tenant lifecycle, entitlements, limits, support access | provision/offboard tenant; enforce plan limits | campaign strategy |
| Campaign Workspace | campaign lifecycle, jurisdiction, stage and workspace scope | create/load scoped campaign workspace | identity credentials |
| Candidate | candidate record, brand evidence and readiness | assess candidate data with provenance | fabricated traits or voter profiles |
| Team and Organization | campaign roles, RACI, capacity and onboarding | assign authorized team responsibility | covert productivity/location surveillance |
| Research and Evidence | sources, claims, methods, limitations and attachments | register and verify attributable evidence | unsourced “facts” or private opposition data |
| Strategy and Decisions | hypotheses, options, assumptions and decision records | propose and record reviewed strategy | autonomous public positioning |
| Roadmap and Tasks | workstreams, dependencies, owners and milestones | plan and update campaign work | hidden manipulation goals |
| Daily Operations | check-ins, briefs, risks and coordination | derive governed operating view | external mobilization |
| Approvals | proposals, decisions, receipts and append history | require and record trusted human decisions | trusting actor/role assertions from commands |
| Training | governed content, pathways, assessments and completions | assign and record learning | unreviewed legal or political advice |
| Risk and Compliance | controls, consent, incidents, legal and ethics gates | block/reroute prohibited or risky activity | waiving mandatory review automatically |
| Audit and Observability | attributable events, integrity evidence, telemetry and alerts | record/query protected operational evidence | claiming an unkeyed hash is a signature |
| AI Orchestration | provider adapters, schemas, evidence context, policy and evals | generate bounded recommendations | authorization or direct external action |
| Integrations | email, calendar, storage, export and webhook adapters | execute approved, idempotent integrations | inventing application grants |

## Dependency rule

Domain modules depend inward on stable interfaces. Infrastructure adapters depend on domain/application ports. HTTP and worker entry points call application services. Cross-context writes use an application transaction or reliable outbox; frontend code never accesses the database directly.

Splitting a context into an independent service requires measured scaling, reliability, security, or ownership evidence and a reviewed ADR.
