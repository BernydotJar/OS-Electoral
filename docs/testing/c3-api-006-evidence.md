# C3-API-006 verification and eval mapping

Status: `VERIFIED_POSTGRESQL_LOCAL_ONLY`

This record maps tenant campaign creation to the CampaignOS required-eval catalog. It records executable evidence only; it is not a political, legal, deployment, or production approval.

## Required eval coverage

| Eval ID | Scenario | Executable evidence |
|---|---|---|
| `EVAL-TENANT-001` | campaign, audit, outbox, and idempotency rows are visible only in the exact forced-RLS tenant scope | `backend/tests/test_campaign_create_postgres.py::test_postgresql_campaign_create_serializes_replay_and_slug_conflicts` |
| `EVAL-AUTHZ-001` | exact tenant collection action/resource/resource ID/purpose/null campaign/null workspace grant is required before persistence | `backend/tests/test_campaign_create_api.py::test_create_denies_mismatched_or_absent_grants_before_persistence` |
| `EVAL-BOLA-001` | foreign tenant selectors, campaign/workspace-scoped grants, foreign adapter output, and metadata/status/version drift fail closed | `backend/tests/test_campaign_create_api.py::test_create_denies_foreign_tenant_before_persistence`, `::test_create_rejects_adapter_contract_drift`, PostgreSQL test below |
| `EVAL-AUDIT-001` | a successful create appends exact actor/authority/correlation evidence and all writes roll back on audit failure | `backend/tests/test_campaign_create_model.py::test_create_commits_draft_campaign_audit_outbox_and_idempotency`, `::test_audit_failure_rolls_back_campaign_and_all_evidence` |
| `EVAL-OUTBOX-001` | create emits one internal `campaign.created` event with `external_effects=NONE` in the same transaction | `backend/tests/test_campaign_create_model.py::test_create_commits_draft_campaign_audit_outbox_and_idempotency`, PostgreSQL test below |
| `EVAL-REPLAY-001` | same normalized request/key/authority replays exactly; different request/authority conflicts; concurrent equal keys serialize | `backend/tests/test_campaign_create_model.py::test_same_key_and_normalized_request_replays_exact_evidence_without_duplicates`, `::test_reused_key_with_different_request_or_authority_fails_closed`, PostgreSQL test below |
| `EVAL-ONBOARDING-001` | creation produces only a `DRAFT` campaign and explicitly omits implicit workspace, strategy, approval, or external action | `backend/tests/test_campaign_create_api.py::test_create_requires_exact_collection_grant_and_forwards_normalized_binding`, `docs/api/campaign-create.md` |

## Additional contract evidence

- `backend/tests/test_campaign_create_model.py`
  - request normalization and whitespace-only rejection;
  - server-owned `DRAFT`/version `1` campaign evidence;
  - atomic campaign, audit, internal outbox, and idempotency writes;
  - exact replay without duplicate evidence;
  - request/grant/approval-receipt/purpose conflict detection;
  - tenant-scoped slug conflict and cross-tenant slug independence;
  - audit-failure rollback;
  - in-memory, unavailable, and broken-database fail-closed behavior.
- `backend/tests/test_campaign_create_api.py`
  - exact collection grant and authorization-before-persistence;
  - foreign tenant, wrong action/resource/resource ID/purpose, campaign scope, and workspace scope denial;
  - required bounded idempotency header;
  - distinct `IDEMPOTENCY_CONFLICT` and `RESOURCE_CONFLICT` responses;
  - sanitized unavailable errors;
  - rejection of adapter tenant/metadata/status/version drift;
  - rejection of caller-owned ID/status/version fields;
  - typed OpenAPI response, bearer security, `Location`, and `ETag` contract.
- `backend/tests/test_campaign_create_postgres.py::test_postgresql_campaign_create_serializes_replay_and_slug_conflicts`
  - Alembic head validation and forced RLS under a non-superuser/non-`BYPASSRLS` role;
  - tenant-level membership and exact campaign-collection grant loading;
  - PostgreSQL create/replay and persisted evidence;
  - cross-tenant campaign/audit/outbox invisibility;
  - two concurrent equal-key requests return one exact committed result;
  - two distinct-key requests racing for the same tenant slug produce exactly one campaign and one sanitized conflict.
- `backend/tests/test_campaign_write_model.py` and `backend/tests/test_workspace_write_model.py`
  - regression evidence after moving all writers to the shared transaction advisory idempotency lock helper.

## Commands

```bash
uv run --locked pytest -W error \
  backend/tests/test_campaign_create_model.py \
  backend/tests/test_campaign_create_api.py \
  backend/tests/test_campaign_write_model.py \
  backend/tests/test_workspace_write_model.py

CAMPAIGNOS_TEST_DATABASE_URL='<isolated *_test URL>' make test-postgres
make verify
```

## Hard-gate interpretation

- critical failures allowed: `0`;
- high failures allowed: `0`;
- cross-tenant leaks allowed: `0`;
- authorization bypasses allowed: `0`;
- campaign/workspace-scoped grants accepted for tenant creation: `0`;
- duplicate campaigns for one idempotency key allowed: `0`;
- duplicate tenant slugs allowed: `0`;
- unaudited successful creates allowed: `0`;
- create outbox events with external effects allowed: `0`;
- caller-controlled status, version, identifiers, or authority allowed: `0`;
- unsupported political, legal, financial, publication, outreach, mobilization, or production approval claims allowed: `0`.

Local or CI green evidence remains below `REVIEWED`, `MERGED`, `DEPLOYED_DEV`, `DEPLOYED_STAGING`, `APPROVED_PRODUCTION`, and `DEPLOYED_PRODUCTION`.
