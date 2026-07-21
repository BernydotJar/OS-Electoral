# Context7 evidence register

Context7 evidence is advisory development documentation, not proof that a dependency is installed. Installation evidence is the reviewed `pyproject.toml` plus hash-bearing `uv.lock`; runtime behavior is established only by tests.

Retrieval/reconciliation date: `2026-07-19 America/Guatemala`

## C3-FOUND-001A records

### FastAPI

- `task_id`: `C3-FOUND-001A`
- `library`: FastAPI
- `library_id`: `/fastapi/fastapi`
- `installed_version`: `0.139.2` (exact production pin)
- `index_versions_observed`: `0.115.13`, `0_116_1`, `0.118.2`, `0.122.0`, `0.128.0`
- `documentation_version_queried`: `/fastapi/fastapi/0.128.0`
- `query`: application factory, lifespan, `TestClient`, exception handlers and `HTTPBearer`
- `documentation_summary`: use lifespan handlers for application startup and shutdown; test through `TestClient`; centralize structured exception handling; treat bearer-token extraction as input to authentication rather than authorization.
- `implementation_decision`: implemented an application factory, dependency-based readiness, structured exception handling and authenticated identity route; tests use the supported client boundary.
- `official_cross_check`: PyPI reports FastAPI `0.139.2`, released `2026-07-16`, requiring Python `>=3.10`.
- `source_links`: [Context7 library](https://context7.com/fastapi/fastapi), [PyPI](https://pypi.org/project/fastapi/)
- `limitations`: Context7's indexed versions lagged the official PyPI release; `0.128.0` documentation cannot be treated as the latest package contract.

### Pydantic and Pydantic Settings

- `task_id`: `C3-FOUND-001A`
- `library`: Pydantic / Pydantic Settings
- `library_id`: `/pydantic/pydantic`
- `settings_library_id`: `/pydantic/pydantic-settings`
- `installed_version`: Pydantic `2.13.4`; Pydantic Settings `2.14.2` (exact production pins)
- `query`: `BaseSettings`, `SettingsConfigDict`, environment prefixes and secrets
- `documentation_summary`: keep runtime settings typed, define environment-name behavior explicitly, and use supported secret sources rather than embedding credentials in code or repository files.
- `implementation_decision`: typed settings now reject partial OIDC/object-storage/SMTP groups, insecure shared-environment endpoints and invalid database drivers; object-storage secrets use `SecretStr` and are redaction-tested.
- `official_cross_check`: PyPI reports Pydantic `2.13.4`.
- `source_links`: [Context7 Pydantic](https://context7.com/pydantic/pydantic), [Context7 Pydantic Settings](https://context7.com/pydantic/pydantic-settings), [PyPI](https://pypi.org/project/pydantic/)
- `limitations`: Context7 did not establish the current Settings release; the exact compatible pair was resolved by uv and verified through configuration/API tests.

### SQLAlchemy

- `task_id`: `C3-FOUND-001A`
- `library`: SQLAlchemy
- `library_id`: `/websites/sqlalchemy_en_20`
- `installed_version`: `2.0.51` (exact production pin)
- `query`: SQLAlchemy 2.0 session and transaction boundaries
- `documentation_summary`: use explicit unit-of-work transaction scopes and avoid sharing mutable sessions across requests or background jobs.
- `implementation_decision`: added engine/session ownership with `pool_pre_ping`, explicit transaction-local tenant scope and detached application sessions; campaign read/write adapters now use that boundary, while broader domain adapters remain future work.
- `official_cross_check`: PyPI reports SQLAlchemy `2.0.51`.
- `source_links`: [Context7 SQLAlchemy 2.0](https://context7.com/websites/sqlalchemy_en_20), [PyPI](https://pypi.org/project/SQLAlchemy/)
- `limitations`: the Context7 identifier is a documentation-site index rather than the upstream repository identifier; official release metadata remains the version authority.

### Alembic

- `task_id`: `C3-FOUND-001A`
- `library`: Alembic
- `library_id`: `/websites/alembic_sqlalchemy`
- `alternate_library_id`: `/sqlalchemy/alembic`
- `installed_version`: `1.18.5` (exact production pin)
- `query`: migration environment, upgrade/downgrade workflow and schema validation
- `documentation_summary`: migrations require an explicit environment, reviewed revisions and rehearsed upgrade paths; autogeneration output must be reviewed rather than accepted as authoritative.
- `implementation_decision`: added a reviewed initial revision plus downgrade/upgrade/check rehearsal against an isolated PostgreSQL database; environment promotion remains blocked.
- `official_cross_check`: PyPI reports Alembic `1.18.5`.
- `source_links`: [Context7 Alembic docs](https://context7.com/websites/alembic_sqlalchemy), [Context7 upstream index](https://context7.com/sqlalchemy/alembic), [PyPI](https://pypi.org/project/alembic/)
- `limitations`: `/websites/alembic_sqlalchemy` had the stronger index reputation; neither index score replaces official release verification or migration review.

### PyJWT

- `task_id`: `C3-FOUND-001A`
- `library`: PyJWT
- `library_id`: `/jpadilla/pyjwt`
- `query`: `PyJWKClient`, required claims, issuer and audience validation
- `installed_version`: `2.13.0` with the `crypto` extra (exact production pin)
- `documentation_summary`: retrieve signing keys through the supported JWK client and require expected claims, issuer and audience; token decoding alone does not establish application authorization.
- `implementation_decision`: implemented a fixed-`RS256` ID-token verifier requiring signature, key ID, issuer, audience, `exp`, `iat`, optional `nbf`, token use and multi-audience `azp`; authorization remains a separate server-owned decision.
- `source_links`: [Context7 PyJWT](https://context7.com/jpadilla/pyjwt), [PyPI](https://pypi.org/project/PyJWT/)
- `limitations`: no live identity provider, browser login flow or session lifecycle is proven; persistent membership and exact-grant loading are covered separately by authorization and PostgreSQL tests.

### HTTPX

- `task_id`: `C3-FOUND-001A`
- `library`: HTTPX
- `library_id`: `/websites/python-httpx`
- `alternate_library_id`: `/encode/httpx`
- `installed_version`: `httpx2 2.7.0` for current Starlette test-client compatibility (exact development pin)
- `query`: client lifecycle, timeouts and test transport
- `documentation_summary`: use bounded client lifecycles, explicit timeouts and controlled test transports for outbound integrations.
- `implementation_decision`: use only for controlled API tests at present; no outbound production integration is authorized by this record.
- `source_links`: [Context7 HTTPX docs](https://context7.com/websites/python-httpx), [Context7 upstream index](https://context7.com/encode/httpx), [httpx2 repository](https://github.com/pydantic/httpx2), [httpx2 on PyPI](https://pypi.org/project/httpx2/)
- `limitations`: the retrieved HTTPX documentation informs lifecycle/timeout discipline, but `httpx2` is the installed next-generation package under the Pydantic organization; production outbound behavior requires its own documentation and tests.

### PostgreSQL driver

- `task_id`: `C3-DATA-001`
- `library`: Psycopg
- `installed_version`: `3.3.4` with the binary extra (exact production pin)
- `documentation_basis`: official Psycopg/SQLAlchemy PostgreSQL driver guidance, cross-checked against the official PyPI release.
- `implementation_decision`: use the explicit `postgresql+psycopg` dialect only; reject other runtime database schemes; exercise real transactions and RLS against PostgreSQL.
- `source_links`: [Psycopg documentation](https://www.psycopg.org/psycopg3/docs/), [PyPI](https://pypi.org/project/psycopg/), [SQLAlchemy PostgreSQL dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- `limitations`: the binary distribution is a packaging choice for the current container; production image scanning and operational connection evidence remain required.

### Verification tooling

- `task_id`: `C3-CI-001`
- `installed_versions`: `pip-audit 2.10.1`; `Playwright 1.61.0`; `actionlint 1.7.12` runs from a digest-pinned container.
- `implementation_decision`: export hash-locked production requirements for blocking vulnerability audit; install the locked Playwright CLI/browser in visual CI; validate all workflow expressions and embedded shell with actionlint.
- `source_links`: [pip-audit on PyPI](https://pypi.org/project/pip-audit/), [Playwright Python on PyPI](https://pypi.org/project/playwright/), [actionlint releases](https://github.com/rhysd/actionlint/releases)
- `limitations`: local and GitHub clean results are point-in-time. Recorded jobs now pass on merged and draft review heads, but required-check enforcement and alert response remain unverified.

## Index limitation

Context7 is mandatory implementation evidence, but its index can lag package registries and can expose multiple identifiers with different reputation. Every implementation task must therefore record the exact documentation identifier and version used, cross-check the current official release, pin a compatible installed version, and test behavior locally. This register does not authorize automatic upgrades.

## C3-RESUME-001 availability record

- `date`: `2026-07-21 America/Guatemala`
- `task_id`: `C3-RESUME-001`
- `Context7_runtime`: unavailable in the Cloud Sandbox toolset used for this checkpoint.
- `framework_change`: none; this increment reconciles repository, CI and program truth rather than changing a framework contract.
- `evidence_basis`: exact versions in `uv.lock`, official package/release metadata used for environment remediation, existing retained framework records, and executable local/CI tests.
- `limitation`: no new Context7 retrieval is claimed or fabricated. The next framework-affecting increment must add current official documentation evidence and, when available, a Context7 record.

## C3-API-005 official documentation record

- `date`: `2026-07-21 America/Guatemala`
- `task_id`: `C3-API-005`
- `Context7_runtime`: unavailable in the Cloud Sandbox toolset; no Context7 retrieval is claimed.
- `installed_versions`: FastAPI `0.139.2`; Pydantic `2.13.4`; SQLAlchemy `2.0.51` from `pyproject.toml` and `uv.lock`.

### SQLAlchemy transaction and row-lock boundary

- `official_sources`: [transactions and connection management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), [Session basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html), [ORM SELECT statements and `with_for_update`](https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html#using-select-for-update).
- `documentation_summary`: keep the campaign observation and audit append inside one explicit Session transaction; use a row lock to serialize access to a shared mutable chain head; flush pending state without committing outside the transaction owner.
- `implementation_decision`: `Database.tenant_transaction` remains the unit of work. A stable tenant row is locked before audited reads/writes, and a session-bound lock token is required by the shared audit appender. The append assigns a monotonic timestamp and flushes the new head while preserving rollback semantics.
- `limitations`: local SQLite proves adapter contracts but not row-lock behavior; the isolated PostgreSQL test is the authority for forced RLS and `FOR UPDATE` behavior. No RDS or staging concurrency claim is made.

### FastAPI dependency and response contract

- `official_sources`: [dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/), [response model](https://fastapi.tiangolo.com/tutorial/response-model/).
- `documentation_summary`: declare shared authentication/authorization inputs as dependencies so their requirements flow into OpenAPI; use a response model to validate, document and filter the API output.
- `implementation_decision`: tenant authorization and the readiness reader are typed dependencies. The route declares `CampaignReadinessEvidence` as its response model and tests the generated bearer-security/OpenAPI contract.
- `limitations`: OpenAPI and `TestClient` evidence is local API-contract proof, not a live browser session, gateway policy, rate limit or deployment proof.

### Pydantic model invariants

- `official_sources`: [validators](https://docs.pydantic.dev/latest/concepts/validators/), [configuration](https://docs.pydantic.dev/latest/concepts/config/).
- `documentation_summary`: use after-model validators for whole-model invariants and return the validated instance; reject unknown fields and freeze read projections where mutation would undermine trust.
- `implementation_decision`: readiness input/output models use `extra="forbid"`, frozen projections and an after-model validator that reconciles ordered checks, totals, status and the guided-intake boolean.
- `limitations`: model validation prevents malformed projection objects; it does not replace authorization, tenant isolation, evidence review or human approval.

## C3-API-006 official documentation record

- `date`: `2026-07-21 America/Guatemala`
- `task_id`: `C3-API-006`
- `Context7_runtime`: unavailable in the Cloud Sandbox toolset; no Context7 retrieval is claimed.
- `installed_versions`: FastAPI `0.139.2`; Pydantic `2.13.4`; SQLAlchemy `2.0.51` from `pyproject.toml` and `uv.lock`.

### SQLAlchemy atomic transaction and integrity boundary

- `official_sources`: [transactions and connection management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html), [Session basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html), [core exceptions and `IntegrityError`](https://docs.sqlalchemy.org/en/20/core/exceptions.html#sqlalchemy.exc.IntegrityError).
- `documentation_summary`: keep related ORM writes inside one explicit Session transaction; commit only when the context completes; treat integrity exceptions as the database constraint boundary and roll the failed transaction back before reuse.
- `implementation_decision`: campaign, audit, internal outbox and idempotency rows share one `Database.tenant_transaction`. A transaction advisory lock serializes equal idempotency tuples, while the tenant/slug and idempotency unique constraints remain final integrity guards. Constraint failures are mapped to sanitized domain exceptions.
- `limitations`: the isolated PostgreSQL test proves local transaction, concurrency and RLS behavior. No RDS, AWS dev/staging, production concurrency, backup or restore claim is made.

### FastAPI response, dependency and header contract

- `official_sources`: [dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/), [additional responses in OpenAPI](https://fastapi.tiangolo.com/advanced/additional-responses/), [response headers](https://fastapi.tiangolo.com/advanced/response-headers/).
- `documentation_summary`: dependencies can enforce authorization before the operation body; response models validate and document output; explicit response metadata documents non-body headers while a `Response` parameter sets runtime headers.
- `implementation_decision`: the route receives current tenant authorization and the creator as typed dependencies, validates the exact collection grant before persistence, returns `CampaignCreateEvidence`, sets `Location` and quoted `ETag`, and declares both headers in the `201` OpenAPI response.
- `limitations`: local TestClient/OpenAPI evidence is not a gateway, rate-limit, browser-session or deployed environment proof.

### Pydantic pre-validation normalization

- `official_sources`: [validators](https://docs.pydantic.dev/latest/concepts/validators/), [models](https://docs.pydantic.dev/latest/concepts/models/), [configuration](https://docs.pydantic.dev/latest/concepts/config/).
- `documentation_summary`: before-field validators can normalize raw input before standard type, length and pattern validation; extra fields can be forbidden; frozen models prevent post-validation mutation.
- `implementation_decision`: campaign creation normalizes slug case/whitespace and collapses metadata whitespace before bounded validation. `extra="forbid"` rejects caller attempts to set server-owned identifiers, status or version.
- `limitations`: normalization and schema validation do not confer authority; authorization, RLS, database constraints, audit and human gates remain separate controls.
