# CampaignOS release-readiness procedure

This procedure prepares evidence for a release decision. It does not authorize merge, infrastructure creation, deployment, spending or any political external effect.

## Current decision

The authoritative machine-readable record is `program/release-readiness.json`.

Current result: `DENY_RELEASE` / production `BLOCKED`.

## Required sequence

1. **Source integrity**
   - Record the exact candidate SHA and base.
   - Require protected-branch checks, secret scanning, dependency audit, SBOM/provenance and visual review.
   - Preserve failed runs and explicit supersession records; never delete adverse evidence.

2. **Controlled staging prerequisites**
   - Obtain explicit authorization for an isolated non-production account and cost envelope.
   - Create remote state and runtime only through reviewed, least-privilege automation.
   - Record environment identity, region, data classification, owners and expiry.

3. **Application and data verification**
   - Run migrations from representative prior data.
   - Verify tenant isolation and exact authorization under managed runtime roles.
   - Exercise backup, isolated restore, application/RLS smoke and cleanup.
   - Measure and obtain human acceptance for RPO and RTO.

4. **Operational verification**
   - Deploy telemetry collection, dashboards and alert routing.
   - Exercise database outage, identity outage, pool exhaustion, stale migration, worker dead-letter and rollback scenarios.
   - Run representative load and abuse tests with accepted thresholds.

5. **Independent review**
   - Obtain scoped security, privacy, accessibility, legal, domain and operational reviews.
   - Resolve every CRITICAL/HIGH finding or record an approved risk treatment that the production policy permits.

6. **Human production approval**
   - Record an authorized, scoped approval receipt only after every required gate is PASS.
   - A role label, UI state, green PR, AI output or release document cannot create this authority.

## Fail-closed rules

- Any unresolved failed validation run blocks release.
- A supersession is valid only when the original failure, root cause, replacement run, exact head, reviewer, date and reason are retained.
- Any non-PASS required gate keeps `release_decision=DENY_RELEASE`.
- Missing or malformed evidence is a failure, not an assumption.
- GitHub Pages is always `DEMO_NON_PRODUCTION` and cannot satisfy staging or production evidence.
- Production deployment remains a separate human-gated action.

## Current next safe action

Human review of the stacked C3-OBS and C3-RELEASE pull requests is safe. Environment creation, Terraform apply and deployment remain prohibited until separately authorized.
