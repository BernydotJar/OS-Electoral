# C3-OPS-002 primary documentation checkpoint

Reviewed: 2026-08-01

## Sources checked

- Alembic tutorial and operation reference for revision graphs, upgrades and downgrades.
- PostgreSQL 18 `pg_dump` and `pg_restore` documentation for custom archives, restore inspection, ownership/ACL handling and destructive restore risk.
- Docker Compose service documentation for health checks, `service_started`, `service_healthy` and immutable image references.
- GitHub Actions documentation for retained workflow artifacts and build provenance attestations.
- Repository-pinned Terraform plan-only policy and target deployment architecture. No provider API, state backend or apply was used.

## Decisions derived for this increment

1. An Alembic downgrade function proves only that downgrade code exists. It does not prove that downgrading preserves domain data, audit continuity, RLS or compatibility with an older application.
2. The repository therefore never selects `alembic downgrade` as an automatic rollback response. Migrations are explicitly cataloged and unknown classification fails closed.
3. PostgreSQL recovery remains an isolated restore procedure. The rollback rehearsal never restores over its source, never uses destructive clean/drop behavior and never claims managed PITR or production recovery.
4. Application rollback requires full Git commit objects for both the candidate and previous-known-good revision. This proves immutable repository source evidence only; it is not a production image promotion or signed production deployment receipt.
5. Liveness is not readiness. A release decision must inspect the bounded health/readiness and dependency checks rather than treating container startup as service health.
6. Workflow artifacts and attestations are retained evidence, not authority. They cannot approve deployment, production rollback or database recovery.
7. Terraform remains plan-only and is outside the rehearsal. Any cloud or managed-environment action requires a separate scoped approval and cost envelope.

## Safety conclusion

The repository can prove a fail-closed rollback decision contract, migration classification completeness, sanitized receipt generation and constrained local/CI rehearsal. It cannot prove managed staging rollback, production image compatibility, RPO/RTO, PITR or production recovery.
