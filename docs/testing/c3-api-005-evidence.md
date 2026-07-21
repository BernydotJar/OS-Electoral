# C3-API-005 verification and eval mapping

Status: `IMPLEMENTED_LOCAL`

This record maps the campaign readiness slice to the CampaignOS eval catalog. It records executable evidence only; it is not a production approval.

## Required eval coverage

| Eval ID | Scenario | Executable evidence |
|---|---|---|
| `EVAL-AUTHZ-001` | exact action/resource/resource ID/purpose/campaign/workspace matching before persistence | `backend/tests/test_campaign_readiness_api.py::test_readiness_denies_mismatched_or_absent_grants_before_persistence` |
| `EVAL-BOLA-001` | foreign tenant/campaign identifiers and adapter scope leaks fail closed | `backend/tests/test_campaign_readiness_api.py::test_readiness_denies_foreign_tenant_before_persistence`, `::test_readiness_rejects_adapter_scope_leak`, PostgreSQL test below |
| `EVAL-AUDIT-001` | successful sensitive reads append a monotonic immutable receipt and no outbox event | `backend/tests/test_audit_append.py`, `backend/tests/test_campaign_readiness.py::test_sqlalchemy_reader_commits_hash_linked_audits_without_outbox` |
| `EVAL-ONBOARDING-001` | deterministic setup states lead to bounded research-first intake actions without strategy or approval claims | `backend/tests/test_campaign_readiness.py::test_policy_reports_metadata_workspace_and_ready_states_without_approval_claims` |

## Additional contract evidence

- `backend/tests/test_eval_catalog_validator.py`
  - current exact 33-item catalog succeeds;
  - missing required IDs, unsupported evidence claims and production-gate mutation fail closed.
- `backend/tests/test_campaign_readiness_api.py`
  - exact grant binding and correlation propagation;
  - absent/revoked-effective grant denial;
  - wrong action, resource type, resource ID, purpose, campaign and workspace denial;
  - sanitized `404` and `503` responses;
  - typed OpenAPI response and bearer security declaration.
- `backend/tests/test_campaign_readiness.py`
  - deterministic policy states and explicit limitations;
  - in-memory adapter audit contract;
  - tenant/campaign SQLAlchemy scope;
  - archived campaign denial and active-workspace counting.
- `backend/tests/test_database.py::test_migration_and_rls_isolate_existing_foreign_tenant_rows`
  - Alembic head validation;
  - forced RLS under non-superuser/non-`BYPASSRLS` role;
  - exact readiness grant loading;
  - PostgreSQL readiness projection and audit receipt;
  - cross-tenant campaign denial;
  - zero outbox events for readiness reads.
- `backend/tests/test_campaign_write_model.py` and `backend/tests/test_workspace_write_model.py`
  - regression coverage after adopting the shared tenant-serialized audit appender.

## Commands

```bash
uv run --locked pytest -W error \
  backend/tests/test_audit_append.py \
  backend/tests/test_campaign_readiness.py \
  backend/tests/test_campaign_readiness_api.py

CAMPAIGNOS_TEST_DATABASE_URL='<isolated *_test URL>' make test-postgres
make verify
```

## Hard-gate interpretation

- critical failures allowed: `0`;
- high failures allowed: `0`;
- authorization bypasses allowed: `0`;
- cross-tenant leaks allowed: `0`;
- unaudited successful readiness reads allowed: `0`;
- readiness outbox/external effects allowed: `0`;
- unsupported political, legal, finance, security or production approval claims allowed: `0`.

CI green or local PostgreSQL proof remains below `DEPLOYED_DEV`, `DEPLOYED_STAGING`, `APPROVED_PRODUCTION` and `DEPLOYED_PRODUCTION`.
