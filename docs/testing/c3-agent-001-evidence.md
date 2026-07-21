# C3-AGENT-001 verification evidence

Verified on 2026-07-21 in the persistent checkout. This checkpoint implements a provider-neutral internal recommendation runtime only. No provider credential, network request, tool call, campaign action, merge, or deployment occurred. Production remains `BLOCKED`.

## Acceptance evidence

| Requirement | Evidence |
|---|---|
| provider-owned interface, unavailable default | runtime contracts and provider-unavailable test |
| exact persisted Strategy snapshot | SQL service and stale-version rollback tests |
| versioned policy/template/schema envelope | contracts, journal, API projection tests |
| untrusted evidence delimiting | prompt-injection evidence test |
| tools disabled | prompt contract and tool-call rejection tests |
| deterministic pre/post guards | 18 runtime adversarial tests |
| strict evidence/option references | unsupported-claim and unknown-option tests |
| explicit token/latency/cost budgets | provider-budget parameterized tests |
| durable append-only journal | migration `20260721_0010`, ORM and SQLite tests |
| exact replay and one provider call | SQLite and concurrent PostgreSQL tests |
| atomic audit/outbox/idempotency | SQLite/PostgreSQL count and rollback assertions |
| forced tenant RLS | constrained PostgreSQL role and cross-tenant tests |
| exact create/read authorization | API grant near-miss and deny-first tests |
| internal worker validation only | `agent.run.recorded` delivery test |
| no authority/effects | schema, database checks, API drift tests and docs |

## Executed focused gates

```yaml
static:
  ruff: PASS
  format: PASS
  strict_mypy: PASS
local_agent_worker:
  passed: 60
  skipped: 2
postgresql:
  result: PASS
  consecutive_combined_runs: 2
  selected_slices: 9
  migration_head: 20260721_0010
  agent_proofs:
    - equal-key concurrent replay
    - exactly one provider invocation
    - one run/audit/outbox/idempotency record
    - constrained NOSUPERUSER NOBYPASSRLS role
    - cross-tenant read and write denial
```

## Critic and Red Team findings closed

1. Malicious language inside evidence remains delimited data and cannot enable tools or override policy.
2. The same prohibited language in the authorized instruction is refused before provider invocation.
3. Unknown evidence and option references fail closed.
4. A `SUPPORTED` claim cannot rely on unknown or unaccepted evidence.
5. Provider/model identity drift, tool calls, schema drift, refusal, unavailable provider, and budget excess become attributable refusals.
6. A fallback provider is not selected automatically and policy is never weakened.
7. The raw instruction is represented by a digest in durable storage.
8. Equal-key concurrent requests invoke the provider once and replay exact evidence.
9. A changed request or authorization under the same key conflicts without another provider call.
10. Run, audit, internal outbox, and idempotency evidence are atomic.
11. The internal worker revalidates run, audit, tenant, campaign, status, disposition, and no-effect fields before local delivery.
12. RLS denies foreign reads and writes under a constrained application role.
13. Every completed or refused run remains `PENDING` human review with `authority_effect=NONE` and `external_effects=NONE`.

## Residual limitations

- no live provider, privacy/DPA/residency/no-training/retention approval;
- no staging leakage, load, timeout, regional failure, or provider fallback evidence;
- no human disposition workflow or authenticated frontend surface;
- no independent security, privacy, legal, domain, or customer acceptance;
- no production environment, merge, deployment, or external action.
