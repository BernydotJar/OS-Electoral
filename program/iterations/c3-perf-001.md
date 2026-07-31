# C3-PERF-001 iteration

## Authorization

Explicit user approval recorded at `2026-07-31T15:35:00-06:00` for the existing SHIP specification. Scope excludes production deployment, cloud resource creation, spending, dependency expansion, live providers, publication, citizen contact, targeting and mobilization.

## Producer

- activated the existing approved node in the canonical graph;
- added the bounded workload catalog, runner, executor and receipt verifier;
- added real FastAPI boundary scenarios and PostgreSQL 18 integration evidence;
- integrated the harness into the existing PostgreSQL CI job with retained sanitized evidence;
- documented primary-source runtime decisions and operations.

## Critic / red team

Findings repaired before review:

1. shared FastAPI lifespan contexts under concurrent workers could race; each operation now owns a client without shared lifespan entry;
2. cleanup could run while timed-out workers were still active; worker shutdown now completes before cleanup;
3. transport errors were initially conflated with returned invalid responses; counters are separate;
4. a partial PostgreSQL runtime initialization could leave a temporary role; initialization and close both revoke the role through fail-safe paths;
5. a failing bootstrap could omit evidence; the CLI now writes a strict sanitized failure receipt;
6. new code initially lowered total coverage below 90%; useful orchestration and failure-branch tests restored the enforced floor without changing it.

## Independent verifier

- strict schema re-loads the artifact independently;
- receipt scan rejects sensitive keys and values;
- program truth remains production-blocked;
- hosted PostgreSQL 18 is required because the local sandbox cannot register the pinned image layer.

## Release gate

Review publication is allowed only after full local verification. Merge is allowed only after exact-head hosted PostgreSQL 18, required checks and review-thread closure. This increment never authorizes production or external effects.

## Pull-request review repair

Three high-severity findings were accepted and fixed:

- exact preauthorization rate-limit calls are now measured rather than inferred;
- real execution is isolated per scenario in killable processes, so a hung worker cannot extend work beyond its deadline;
- receipt PASS is derived from complete catalog evidence and internally consistent child decisions, not trusted from a top-level field.

The previous green exact-head run is superseded. Repaired PostgreSQL 18.3 CI is mandatory.
