# C3-SEC-002 Tasks

## Implementation Tasks

- [ ] Record the human approval receipt and move the feature from `spec_ready` to `approved`.
- [ ] Complete the required primary-documentation checkpoints and record pinned-version evidence.
- [ ] Add strict policy contracts and configuration validation with no permissive production defaults.
- [ ] Add the reviewed PostgreSQL migration, exact indexes, constraints, forced RLS, and bounded cleanup contract.
- [ ] Implement atomic server-owned counter consumption and sanitized decision results.
- [ ] Bind policy classes to selected API routes without changing existing authorization or idempotency authority.
- [ ] Add RFC 9457-style `429` handling and `Retry-After` headers.
- [ ] Add low-cardinality metrics and sanitized structured logging hooks.
- [ ] Document operations, retention, rollout, rollback, limitations, and staging load requirements.
- [ ] Update canonical graph, ledger, risk, decision, eval, and evidence records only for this feature.

## Verification Tasks

- [ ] Run Graph Harness state validation and confirm exactly one active feature.
- [ ] Run Ruff, formatting, and strict mypy.
- [ ] Run focused contract/model/API tests.
- [ ] Run isolated PostgreSQL migration/RLS/concurrency/rollback/cross-tenant tests.
- [ ] Run the complete locked Python suite with the coverage floor.
- [ ] Run applicable frontend verification if user-facing error handling changes.
- [ ] Run `make program-verify`.
- [ ] Run worktree and committed-range secret scans.
- [ ] Collect exact-head hosted CI and artifact receipts.
- [ ] Record localized repairs without invalidating unaffected evidence.

## Review Tasks

- [ ] Reviewer validates implementation against requirements and design without editing production code.
- [ ] Security reviewer examines bypasses, authorization ordering, BOLA, store failure, sensitive logging, and abuse cases.
- [ ] Database reviewer examines atomicity, locks, RLS, indexes, retention, migration rollback, and contention.
- [ ] Production reviewer evaluates performance evidence, observability, operations, rollback, and remaining staging gates.
- [ ] Preserve any failed validation and supersession evidence.
- [ ] Keep production `BLOCKED` unless every separate production gate passes.

## Stop Conditions

- Missing explicit human approval for this spec.
- Any new package dependency is required.
- Schema or migration scope differs from the approved design.
- A route cannot preserve exact authorization and sanitized errors.
- The design requires IP address storage or voter/citizen profiling.
- PostgreSQL contention cannot be bounded under the approved policy catalog.
- Verification failure cannot be repaired inside the affected subgraph.
- Staging, cloud apply, spending, or production deployment becomes necessary without a separate approval.
