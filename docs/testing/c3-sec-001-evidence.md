# C3-SEC-001 security and privacy baseline evidence

Verified on 2026-07-21 from `agent/c3-sec-001-security-privacy-baseline`, based on final plan-only infrastructure receipt `c4945db9ae0516f40fa8b8940ee0c0e450c665d2`.

```yaml
production_status: BLOCKED
external_effects: NONE
independent_security_approval: NOT_RECORDED
independent_privacy_approval: NOT_RECORDED
jurisdictional_legal_review: REQUIRED
live_processors: DISABLED
migration_head: 20260721_0011
```

## Database mutation controls

Revision `20260721_0011` installs one fixed-search-path `SECURITY DEFINER` trigger function and enabled `BEFORE UPDATE OR DELETE` triggers on:

- `audit_events`;
- `idempotency_records`;
- `candidate_section_approvals`;
- `war_room_snapshots`;
- `strategy_decision_receipts`;
- `agent_runs`.

A constrained `NOSUPERUSER`/`NOBYPASSRLS` application role can insert scoped evidence but receives SQLSTATE `42501` when attempting update or delete. An application-controlled GUC does not bypass the trigger. Trigger/function metadata is inspected from `pg_catalog`, and PUBLIC has no function EXECUTE privilege.

The database owner or a role inheriting the owner remains a deliberate break-glass boundary for migrations, controlled offboarding and incident recovery. Therefore this is non-owner mutation denial, not cryptographic immutability or independent anchoring.

## Executable data policy

`docs/security/data-policy.json` and `scripts/security/verify_security_policy.py` enforce:

- 12 required record types with classification, owner, purpose, retention posture, deletion mode, processor boundary and legal-review state;
- seven mandatory political/sensitive-data prohibitions;
- all live AI, integration, attachment and export processors disabled;
- no record type may claim production readiness;
- AI runs retain `NO_LIVE_AI_PROVIDER`;
- secrets and bearer tokens remain prohibited application-record content;
- six append-only tables and required migration controls remain declared.

Seven adversarial tests demonstrate fail-closed behavior when a required record or prohibition is removed, a classification is invented, production readiness is claimed, AI is enabled or secret storage is weakened.

## Residual limitations

- No independent security, privacy, legal, domain or production approval.
- No legal retention duration or lawful-basis determination is asserted.
- No export, attachment, backup/restore, rate-limiting, live processor, incident exercise or production environment evidence.
- Owner break-glass can mutate protected rows and requires separate privileged-access governance and audit.
- No cryptographic signature, external integrity anchor or restore verification exists.

## Local regression checkpoint

- Full locked suite: 652 passed, 10 controlled skips, 90.95% coverage.
- Ruff, format and strict mypy over 63 source files: PASS.
- Frontend: 48 tests, production build and npm audit with zero vulnerabilities: PASS.
- Terraform 1.15.8 plan-only validation and both mocked plans: PASS; no credentials or apply.
- PostgreSQL: 10 selected migration/RLS/concurrency/security slices passed twice through revision `20260721_0011`.
- Actionlint 1.7.12, hash-locked production dependency audit and Gitleaks 8.30.1 effective-worktree scan: PASS.
- Program truth remains fail-closed with two CRITICAL/HIGH findings and six historical failed runs.
- Final browser/stack E2E, commit, draft PR and exact-head CI remain pending at this checkpoint.

## Final local E2E

- Production frontend browser review: PASS for ES/EN desktop, ES mobile, keyboard skip link, reduced motion and zero horizontal overflow.
- Axe WCAG 2.2 A/AA: zero violations. Browser storage, console/page errors and unexpected outbound hosts: empty.
- Local Compose stack: environment-blocked before service start because the nested Docker daemon cannot register a pulled layer (`lchown /var/empty: permission denied`). This is the existing local namespace limitation, not a product PASS or FAIL.
- The universal CI `Constrained local stack E2E` remains required on the exact published head.

## Exact-head CI evidence

- Draft PR: `#105`.
- Head: `ab63e19079ac0828fe3555dbbeb9493e94d02829`.
- CampaignOS CI: `29943367172`.
- Runtime visual review: `29943367823`.
- PostgreSQL job: `89002561460`.
- Constrained stack E2E job: `89002561484`.
- Dynamic frontend/browser job: `89002561435`.
- Supply-chain artifact `8539119822` and frontend artifact `8539168996` are bound to the exact implementation head.
