# C3-PERF-001 primary-documentation checkpoint

Reviewed on 2026-07-31 before implementation. Only primary documentation for the pinned runtime contracts is used.

## Python concurrency, timing and percentiles

- `concurrent.futures.ThreadPoolExecutor` uses an explicit worker ceiling; executor context management performs shutdown and waits for pending work. Futures expose bounded result waits and cancellation. Source: https://docs.python.org/3/library/concurrent.futures.html
- Elapsed durations use `time.monotonic_ns()` so wall-clock changes cannot move a scenario deadline backward. Source: https://docs.python.org/3/library/time.html#time.monotonic_ns
- The repository implements and tests nearest-rank percentiles itself; no statistics API is assumed to provide that contract.

## FastAPI ordering and validation

- Request bodies declared with Pydantic models are parsed and validated by FastAPI. Source: https://fastapi.tiangolo.com/tutorial/body/
- Decorator/router dependencies are executed through the same dependency system even when their return values are not injected. Source: https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/
- Direct `Request` access bypasses automatic validation for values read manually. Source: https://fastapi.tiangolo.com/advanced/using-request-directly/
- The harness therefore treats the existing global opaque preauthorization dependency as the malformed-traffic boundary and verifies it without introducing a parallel auth path.

## SQLAlchemy 2.0.51 pool and transaction evidence

- Pool status and checked-out/checked-in behavior are inspected through the existing engine/pool contract; `Engine.dispose()` is not used as a substitute for correct per-request release. Source: https://docs.sqlalchemy.org/en/20/core/pooling.html
- Transaction scopes continue to use the repository's existing session/context management rather than sharing a session across workers. Source: https://docs.sqlalchemy.org/en/20/core/connections.html

## PostgreSQL 18 locks and timeouts

- `pg_locks` can be correlated with `pg_stat_activity` for bounded lock evidence; the receipt stores only aggregate counts and never backend IDs or query text. Source: https://www.postgresql.org/docs/18/view-pg-locks.html
- `statement_timeout` aborts long statements and `lock_timeout` applies while waiting for locks; both are scoped to the disposable verification connection rather than global configuration. Source: https://www.postgresql.org/docs/18/runtime-config-client.html
- Deadlocks are PostgreSQL-detected and are not treated as a timing threshold success. Source: https://www.postgresql.org/docs/18/explicit-locking.html

## GitHub Actions artifacts

- The existing immutable `actions/upload-artifact` pin is reused; evidence is retained as a job artifact rather than committed generated output. Source: https://docs.github.com/actions/using-workflows/storing-workflow-data-as-artifacts
- Artifact retention remains repository-controlled and the receipt is schema-validated before upload.
