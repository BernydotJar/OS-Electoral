# CampaignOS data ownership

Status: **PROPOSED TARGET**
Last updated: `2026-07-19`

Every table and object has one owning bounded context. Other contexts use an identifier plus a published interface or immutable event. Shared-table writes and cross-module ORM mutation are prohibited.

| Data family | Owning context | Required scope | Key controls |
|---|---|---|---|
| external identities, sessions | Identity and Access | principal | verified OIDC binding, revocation, MFA capability, short lifetime |
| memberships, role grants | Identity and Access | tenant and optionally campaign/workspace | deny by default, server-derived grants, validity interval, audit |
| tenants, entitlements, support access | Tenant and Consultancy | tenant | controlled provisioning, limits, time-bound support elevation |
| campaigns and workspaces | Campaign Workspace | tenant + campaign | lifecycle/version checks, jurisdiction, archival/export |
| candidate records | Candidate | tenant + campaign | provenance, sensitivity classification, versioning |
| team assignments and RACI | Team and Organization | tenant + campaign | least privilege, consented operational data, no covert surveillance |
| sources, claims, evidence objects | Research and Evidence | tenant + campaign/workspace | provenance, purpose, access label, retention, malware strategy |
| strategies and decisions | Strategy and Decisions | tenant + campaign | assumptions, uncertainty, affected publics, approval linkage |
| roadmap items | Roadmap and Tasks | tenant + campaign | dependency integrity, ownership, optimistic concurrency |
| check-ins and daily briefs | Daily Operations | tenant + campaign/workspace | attributable inputs, no unauthorized external execution |
| proposals and approval receipts | Approvals | tenant + campaign/workspace | append semantics, trusted principal/grants, target version |
| training content/completions | Training | tenant/global + principal | content governance, versioned assessments, minimal learner data |
| risks, consents, incidents | Risk and Compliance | tenant + campaign/principal as applicable | immutable evidence references, severity/escalation, retention |
| audit events and telemetry | Audit and Observability | tenant plus operational scope | append-only design, redaction, integrity anchor, restricted access |
| prompts, responses, eval records | AI Orchestration | tenant + campaign/workspace | evidence references, model metadata, schema result, human disposition |
| integration deliveries | Integrations | tenant + campaign/workspace | idempotency, destination allow-list, approval and delivery receipt |

## Storage invariants

- Every tenant-owned row carries a non-null `tenant_id`; campaign-owned rows also carry a non-null `campaign_id`.
- Foreign keys cannot cross tenants. Composite keys or validated triggers/policies must make accidental cross-tenant references impossible.
- Repository methods require an explicit server-derived scope and include it in every read and write predicate.
- PostgreSQL row-level security is defense in depth, not a replacement for application authorization.
- Audit, approval, consent, and incident evidence uses append semantics. Corrections are new records linked to the original.
- Object keys are opaque and tenant-partitioned; access requires an application decision and short-lived signed operation.
- Soft deletion is used only when retention or recovery requirements justify it. Legal deletion workflows must remove or irreversibly anonymize data where required.
- Exports are scoped, authorized, attributable, encrypted, time-limited, and audited.
