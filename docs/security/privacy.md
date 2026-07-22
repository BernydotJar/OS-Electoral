# CampaignOS privacy principles and control plan

Status: **DRAFT — qualified privacy and jurisdictional legal review required**
Last updated: `2026-07-21`

CampaignOS applies purpose limitation, minimization, provenance, accuracy, access control, retention, deletion, transparency, and human accountability to all personal or political information.

## Data admission rule

Before a data category or field is enabled, record:

- defined product purpose and affected public;
- lawful basis or verifiable consent where applicable;
- source/provenance and accuracy limitations;
- sensitivity classification and prohibited inferences;
- tenant/campaign/workspace access policy;
- processor/provider and cross-border considerations;
- retention/expiry, withdrawal, export, correction, deletion, and legal-hold behavior;
- incident severity and notification owner.

Unknown purpose or basis fails closed. Free text cannot be used to bypass a structured prohibition. The executable inventory and current non-legal retention postures are versioned in `docs/security/data-policy.json` and validated by `scripts/security/verify_security_policy.py`.

## Political and sensitive data

The product prohibits individual vote-intention storage, persuadability or psychological-vulnerability inference, sensitive microtargeting, biometric persuasion, non-consensual political contact databases, voter-loyalty monitoring, and citizen surveillance. Sensitive attributes may be studied only in aggregate where justified, proportionate, lawful, methodologically reviewed, and protected against re-identification.

Citizen contact may be recorded only for a documented lawful basis or verifiable consent, explicit purpose, minimum fields, expiry, withdrawal, and auditable access. Campaign and government/public-resource data remain separated.

## AI and integration privacy

Only the minimum authorized evidence enters a model or integration. Provider use requires a reviewed data-processing posture, region/retention settings, access restrictions, and an exit/deletion plan. Prompt and response logs inherit source classification. Secrets, tokens, unrelated tenant context, and unsupported sensitive fields are excluded.

## User rights and operations

Production scope requires authenticated export, correction, consent withdrawal, deletion/anonymization, tenant offboarding, retention jobs, legal holds, and completion receipts. Backup retention and restore procedures must honor the deletion model or document bounded exceptions.

No privacy approval is recorded; the privacy production gate remains partial/blocked.
