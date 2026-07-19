# CampaignOS threat model

Status: **DRAFT — technical controls are partial; independent security/privacy review required**
Version: `0.1`
Last updated: `2026-07-19`

## Scope and safety objective

This model covers the target browser, FastAPI application, workers, PostgreSQL, object storage, OIDC provider, AI providers, integration adapters, CI/CD, and AWS control plane. The current repository implements only a subset. A listed mitigation is not proof of implementation; the status and linked evidence control that claim.

Primary safety objective: one compromised input, user, campaign, provider, worker message, or deployment step must not expose another tenant, create unauthorized political action, erase attributable evidence, or bypass a required human/legal/ethical gate.

## Assets

- external identity bindings, sessions, MFA/recovery/invitation state;
- tenant memberships, campaign/workspace access, grants, and support elevation;
- candidate/team information and potentially sensitive political or operational data;
- sources, claims, attachments, consent/lawful-purpose records, strategies, and decisions;
- proposals, approval receipts, incidents, audit records, and integrity anchors;
- model prompts/responses, evidence context, policy versions, and eval results;
- database/object backups, exports, secrets, signing/encryption keys, images, and Terraform state;
- production availability and the integrity of deployment approvals.

## Threat actors and assumptions

- unauthenticated internet attacker;
- authenticated user attempting horizontal or vertical privilege escalation;
- malicious or compromised tenant administrator, support operator, integration client, or CI contributor;
- attacker controlling uploaded content, a research source, webhook payload, email link, or model prompt response;
- compromised dependency, GitHub Action, container, model provider, OIDC key endpoint, or cloud credential;
- accidental operator error or application defect with cross-scope effects.

OIDC, cloud, model, and package services are dependencies, not infallible trust anchors. Authorized insiders still require least privilege, separation of duties, and attributable audit.

## Trust boundaries

See `docs/architecture/system-context.md`. The security-critical transitions are: browser to API; API to OIDC; principal to application grants; application to database/object store; application to queue/worker; evidence to model; repository to CI; CI to AWS; and operator to production approval.

## Threat register

| ID | Threat / abuse case | Required controls and verification | Current status |
|---|---|---|---|
| TM-01 | Cross-tenant or cross-campaign object access | server-derived scope on every repository method; composite constraints; RLS defense; BOLA tests using valid foreign IDs | Local composite schema/forced-RLS proof passes under a non-superuser role; application/staging coverage incomplete |
| TM-02 | Vertical privilege escalation through token role, command actor, or client field | OIDC authenticates subject only; database grants; exact action/resource/scope authorization; trusted-principal approval receipts | OIDC/token-role rejection and exact approval binding pass; persisted grant loading absent |
| TM-03 | Invitation abuse or account takeover | single-use short-lived invitation, tenant-bound issuer, MFA capability, recovery controls, enumeration resistance, revoke/audit tests | Not implemented |
| TM-04 | Session theft/replay | HTTPS, secure same-site cookies or bounded bearer handling, short lifetime, rotation/revocation, device/session view, no token logging | Token verification partial; session lifecycle absent |
| TM-05 | Confused deputy in worker/integration | signed/versioned envelope, server-derived principal/scope, action allow-list, idempotency, fresh authorization, delivery receipt | Not implemented |
| TM-06 | Prompt injection or malicious evidence causes disclosure/action | treat evidence as data, minimize scoped context, provider isolation, output schema plus policy checks, no tool authority, adversarial evals | Deterministic evidence guards partial; provider runtime absent |
| TM-07 | Model/provider data leakage | data classification, approved processors/regions, minimization, no-training setting where contractually available, retention controls, redacted logs | Not implemented |
| TM-08 | Malicious attachment, decompression bomb, or unsafe signed URL | type/size/content validation, quarantine, malware strategy, opaque key, short-lived operation, disposition audit | Not implemented |
| TM-09 | SSRF through URL import, JWKS, webhook, or preview | fixed/configured HTTPS origins, DNS/IP egress policy, redirect/timeout/size limits, no user-selected JWKS, metadata endpoint block | OIDC URLs are configured HTTPS; network/egress controls absent |
| TM-10 | XSS, CSRF, clickjacking, or unsafe redirect | output encoding, CSP, secure headers, CSRF design matched to session mechanism, origin checks, dependency review, browser tests | Basic API headers partial; production frontend absent |
| TM-11 | SQL injection or unsafe migration | parameterized SQL/ORM, no raw user fragments, least-privilege DB roles, migration review/rehearsal, SAST | SQLAlchemy/Alembic and isolated role rehearsal exist; CodeQL is unobserved and staging policy absent |
| TM-12 | Audit tampering or false integrity claims | append-only durable records, restricted role, canonical hash/MAC or external anchor, correction events, restore verification | Prototype hash checks only; no signature/immutability proof |
| TM-13 | Export or backup leaks data across scope | fresh authorization, scoped query, encryption, short-lived location, watermark/receipt, retention/deletion, restore isolation | Not implemented |
| TM-14 | Over-privileged support access | explicit request, reason, approver, exact tenant/scope, short expiry, customer-visible audit, no hidden standing role | Not implemented |
| TM-15 | Secret exposure | no committed/static cloud keys, mounted secret store, redaction, rotation, push protection, CI scanning, least-privilege OIDC | GitHub scanning observed, SecretStr config and pinned gitleaks job exist; runtime/cloud rotation pipeline incomplete |
| TM-16 | Supply-chain compromise | locked hashes, immutable Action SHAs, provenance/SBOM, dependency and image scan, reviewed updates, minimal images | Hash lock, full Action SHAs, image digests, audit and update definitions exist; execution, SBOM/provenance/signing remain absent |
| TM-17 | Unauthorized production change | protected branch, required review/checks, short-lived AWS OIDC, separate environments, reviewed plan, explicit approval receipt, rollback | Production blocked; protections/IaC absent |
| TM-18 | Political manipulation or illegal data use encoded as feature | immutable prohibited-capability registry, purpose/consent gates, hard evals, incident escalation, domain/legal review | Prototype prohibitions exist; production enforcement/review incomplete |
| TM-19 | Public-resource/campaign mixing | tenant/integration separation, source classification, blocked municipal/public-employee imports, critical incident and legal routing | Policy/eval target only |
| TM-20 | Covert team or citizen surveillance | prohibit continuous individual location/loyalty/productivity tracking; consented aggregate/task-level alternatives; privacy review | Policy boundary only |
| TM-21 | Denial of service, abusive API use, queue exhaustion | request/body limits, rate quotas by principal/tenant, backpressure, bounded retries, DLQ, WAF, load and failure tests | Not implemented |
| TM-22 | Mutable-reference or partial-commit corruption in prototype adapters | defensive copies, explicit scoped write intent, atomic snapshot/restore, late-failure tests | Repaired and covered in current worktree; independent review pending |
| TM-23 | Evidence from another scope or lexical similarity marked verified | explicit scope/provenance, exact-claim human review, enabling-class/status checks, cross-scope rejection | Repaired and covered in current worktree; durable workflow absent |

## Security invariants

- Deny by default; absence, ambiguity, expiry, or inconsistent scope is a denial.
- Authentication never implies authorization.
- No role name, actor label, tenant identifier, or approval decision supplied by a client is trusted without server-side evidence.
- Every sensitive read and every write is attributable, scoped, authorized, and auditable.
- AI eligibility is not approval, and AI output cannot execute external or sensitive action.
- An unkeyed hash chain is not described as signed, immutable, or independently anchored.
- Production remains blocked with any open critical/high finding, red gate, unsuperseded failed validation evidence, or missing human approval.

## Verification plan

Before staging acceptance, extend the local PostgreSQL/RLS proof through real application repositories and create automated tests for every remaining exercisable row, including invitation/session abuse, attachment and SSRF cases, prompt injection/data exfiltration, support elevation, export isolation, queue replay, audit mutation, secrets, SAST/dependencies, and load/failure behavior. Security and privacy reviewers must accept residual risks and owners; legal/domain reviewers must accept jurisdiction and political-safety boundaries.

## Review record

No independent production security or privacy approval is recorded. This document moves the threat-model gate from absent to draft/partial only.
