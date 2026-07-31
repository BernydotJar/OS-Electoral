# Bounded authenticated load verification

This runbook executes C3-PERF-001 only against a disposable PostgreSQL database whose name ends in `_test`. It is a correctness and regression harness, not a capacity benchmark and not production evidence.

## Hard envelope

- no more than 20 workers per scenario;
- no more than 600 requests per scenario;
- no more than 60 seconds per scenario;
- no more than 10 minutes for the focused harness;
- PostgreSQL role is temporary, `NOSUPERUSER`, `NOBYPASSRLS` and receives only the rate-limit table privileges required by the harness;
- role-level `statement_timeout=5s` and `lock_timeout=2s` bound database waits;
- no cloud resources, outbound model calls, publication, citizen contact, targeting, spending or mobilization.

## Execute

```sh
make performance-postgres \
  CAMPAIGNOS_TEST_DATABASE_URL='postgresql+psycopg://.../campaignos_test' \
  SOURCE_REVISION="$(git rev-parse HEAD)"
```

The target rejects non-PostgreSQL URLs and databases that do not end in `_test`. The generated evidence is written to:

```text
artifacts/c3-perf-001/load-verification.json
```

The Make target always runs the independent receipt verifier after the harness. A failing bootstrap or scenario still writes a strict `FAIL` receipt with a stable failure code.

## Scenarios

The versioned catalog covers:

1. authenticated identity read;
2. authenticated draft mutation;
3. authorized expensive readiness read;
4. current-session lifecycle registration;
5. governed agent service unavailable with no provider call;
6. malformed authenticated request validation;
7. cross-tenant/BOLA denial;
8. atomic fixed-window contention with exactly five allowed and fifteen denied requests;
9. rate-limit accounting that survives a forced domain rollback;
10. unavailable rate-limit store fail-closed behavior;
11. bounded stale-bucket cleanup.

## Receipt interpretation

A scenario passes only when all of these pass independently:

- invariant decision;
- latency sanity ceiling;
- cleanup decision;
- pool recovery decision.

Expected 4xx/5xx responses are counted separately from unexpected errors. `governed_agent` and `store_unavailable` deliberately expect sanitized `503` responses. The receipt records aggregate status classes and rate-limit outcomes only. It rejects raw URLs, database URLs, tokens, cookies, request/response bodies, UUIDs, email addresses, IP addresses and political content.

`production_capacity_claim` is always `false`. A passing receipt demonstrates bounded correctness in the recorded local/CI runtime only. It does not establish a production SLO, load ceiling, edge-protection capability or deployment approval.

## Cleanup and failure handling

The temporary application role is dropped in a `finally` path after pool disposal. Current and stale test buckets are deleted under tenant RLS. CI uploads the sanitized receipt for 30 days even when the harness fails. Any missing receipt is itself a CI failure.
