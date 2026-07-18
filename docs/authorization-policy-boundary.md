# Tenant Context and Authorization Policy Boundary

C2-SAAS-001A defines the policy boundary that a future authentication adapter must call. It does not authenticate users, issue sessions, process tokens or persist grants.

## Decision model

`principal context + resource-scoped request → ALLOW | DENY`

Authorization is deny-by-default and requires one exact, active grant matching tenant, campaign, workspace and permission. Display names are informational and never participate in authorization.

Actor types are `HUMAN`, `AGENT` and `SYSTEM`. Political, legal, financial, publication, spending and mobilization approval permissions are human-only. Agents may read, create drafts and request approval when explicitly granted, but cannot receive approval permissions.

## Run

```bash
python3 scripts/campaign/validate_c2_saas_001a.py

python3 scripts/campaign/run_authorization_policy.py \
  --principal fixtures/authorization/antigua-human.json \
  --request fixtures/authorization/antigua-read-request.json \
  --output artifacts/authorization/antigua-read-decision.json
```

The CLI evaluates policy only and writes below `artifacts/authorization/`. An `ALLOW` result does not perform the action.

## Security invariants

- cross-tenant, cross-campaign and cross-workspace grants do not match;
- revoked, expired or date-invalid grants deny;
- unknown roles or permissions fail closed;
- display-name spoofing grants no authority;
- non-human principals cannot hold human approval permissions;
- context and request inputs are immutable;
- no login, secrets, cookies, tokens, database or deployment are included.
