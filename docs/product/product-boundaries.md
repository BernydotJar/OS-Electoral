# CampaignOS product boundaries

Status: **PROPOSED — human product, legal, privacy, and domain approval required**
Last updated: `2026-07-19`

This record defines what CampaignOS may become. It is not evidence that the target capabilities are implemented, legally approved, or ready for a real campaign. The machine-readable production gates remain authoritative.

## Purpose

CampaignOS is a multi-tenant operating system for consultancies and authorized campaign teams. It helps a team organize evidence, plans, work, learning, approvals, risks, and internal operating rhythms while preserving human judgment and democratic safeguards.

The product may:

- guide a team through campaign intake, readiness, candidate, team, research, strategy, roadmap, daily operations, training, risk, and compliance workflows;
- organize attributable evidence and make uncertainty visible;
- propose alternatives, questions, contradictions, and internal work items;
- enforce tenant, campaign, workspace, role, purpose, and approval boundaries;
- create auditable internal records of recommendations and authorized human decisions;
- support aggregate, consented, purpose-limited analysis that does not infer individual political vulnerability or vote intention.

## Authorized users

- Consultancy administrators who provision and govern tenant access.
- Campaign administrators and managers with explicit campaign membership.
- Candidate, strategist, researcher, communications, finance, legal/compliance, field, training, and authorized reviewer roles with least-privilege grants.
- Support personnel only through time-bounded, approved, auditable access.

An identity-provider account never creates application membership, tenant access, campaign access, or a role by itself. Those grants belong to CampaignOS and must be loaded from durable application data.

## Decisions reserved for authorized humans

AI and deterministic rules may assess eligibility or recommend an action. They may not approve or execute it. Human approval is required for at least:

- candidate positioning and public narrative;
- public content and publication;
- budget ceilings, spending, paid media, and vendor commitments;
- field mobilization and citizen contact;
- selection of sensitive audiences or research methods;
- legal, privacy, security, and jurisdictional sign-off;
- production deployment and irreversible environment changes.

Every approval must bind the authenticated principal, application grants, tenant/campaign/workspace scope, action, object version, decision, time, and authorization evidence. A client-supplied role or actor label is not proof of authority.

## Hard prohibitions

CampaignOS must reject, preserve audit evidence for, and route to human review where appropriate:

- voter-level profiling, individual vote-intention storage, or persuadability inference;
- sensitive or psychological microtargeting, fear exploitation, or biometric persuasion;
- disinformation, impersonation, fake accounts, astroturfing, troll centers, coordinated harassment, or defamatory/private opposition research;
- automated publication, spending, mobilization, or citizen contact;
- non-consensual contact databases, voter-loyalty monitoring, citizen surveillance, or covert team surveillance;
- mixing public resources, municipal data, or public employees with campaign operations;
- deceptive invoicing or optimizing for the cost of violating law;
- any capability that removes a required human, legal, ethical, privacy, or security gate.

These prohibitions are product invariants, not configurable tenant features.

## Data boundary

CampaignOS may retain tenant administration, campaign operations, team assignments, attributable research, decisions, training, risk, audit, and consent records needed for a documented lawful purpose. Tenant-owned records must carry `tenant_id`; campaign-owned records must also carry `campaign_id` where applicable.

The product must not collect data merely because it might be useful. Sensitive or political data requires documented purpose, lawful basis, minimization, provenance, access policy, retention, deletion, export, and incident treatment. Free-text and uploaded evidence remain untrusted inputs until validated.

## AI boundary

Model output is an untrusted recommendation. It must be schema-validated, evidence-linked, purpose-scoped, policy-checked, and reviewable. Strategic recommendations must declare assumptions, institutional constraints, social context, research method, evidence status, affected publics, distributional effects, ethical risks, legal dependencies, and uncertainty.

Models receive the minimum scoped context necessary. Provider prompts and responses must never be a hidden authorization channel. No model may directly publish, spend, mobilize, contact citizens, change application grants, or deploy production.

## Deployment and commercial boundary

GitHub Pages is a static `DEMO_NON_PRODUCTION` surface and can never satisfy a production gate. Production requires reviewed infrastructure, environment separation, security/privacy/accessibility/load/restore evidence, zero open critical or high findings, current documentation, and an explicit authorized human approval receipt.

The first enterprise pilot may use controlled entitlement and tenant provisioning. Payment processing is out of scope until explicitly approved.

## Approval record

This proposal becomes an approved product boundary only when all required reviewers are recorded in a separate, attributable approval receipt. Until then, the production gate `product-boundaries` remains incomplete.

Required reviewers:

- product owner;
- security and privacy owner;
- qualified jurisdictional legal reviewer;
- political-science and research-methodology reviewer;
- communication-ethics and democratic-participation reviewer.
