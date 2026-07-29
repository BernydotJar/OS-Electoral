# C3-PERF-001 Tasks

## Approval and Preparation

- [ ] Record explicit human approval and move the node from `spec_ready` to approved/ready.
- [ ] Complete pinned primary-documentation checkpoints.
- [ ] Confirm exactly one active Graph Harness feature and no production/deployment authority.

## Producer

- [ ] Inventory representative protected routes, fixtures, metrics and database boundaries.
- [ ] Add strict typed workload, threshold and receipt contracts.
- [ ] Implement deterministic percentile and decision evaluation.
- [ ] Implement the bounded authenticated runner with hard concurrency, request and time limits.
- [ ] Add mandatory fixture, session and rate-limit cleanup.
- [ ] Add sanitized JSON receipt generation and schema verification.
- [ ] Add Makefile and CI integration without new paid/runtime dependencies.
- [ ] Document operator usage, limitations, staging handoff and rollback/removal.

## Verification

- [ ] Test workload and receipt contracts, unknown-field rejection and sensitive-output denial.
- [ ] Test success, expected denial, unexpected response, timeout, cancellation and cleanup paths.
- [ ] Test malformed authenticated traffic before model binding.
- [ ] Test exact authorization, BOLA and cross-tenant isolation under concurrency.
- [ ] Test PostgreSQL 18 counter contention, rollover, rollback accounting, pool recovery and bounded cleanup.
- [ ] Run Ruff, format, strict mypy and focused tests.
- [ ] Run the complete locked Python suite with the coverage floor.
- [ ] Run applicable frontend verification only if frontend code changes.
- [ ] Run program, release, security, CI-policy, Terraform-policy and supply-chain validators.
- [ ] Run effective-worktree, committed-range and submitted-diff secret scans.
- [ ] Collect exact-head hosted CI and retained receipt evidence.

## Critic / Red Team

- [ ] Attempt unbounded configuration, timeout bypass and concurrent counter drift.
- [ ] Attempt authentication/authorization ordering bypass and BOLA inference.
- [ ] Attempt sensitive data injection into logs and receipts.
- [ ] Attempt false production-capacity claims from constrained evidence.
- [ ] Attempt leaked fixtures, sessions, transactions and rate-limit rows after failure.

## Fixer and Independent Verifier

- [ ] Repair only the affected scenario, runner, threshold or product subgraph.
- [ ] Preserve failed validation and supersession evidence.
- [ ] Independently rerun equal-or-broader focused and complete gates.
- [ ] Record SHIP review decisions for security, data correctness, performance, failure modes, observability, testing and operations.

## Release Gate and Persistent Evidence

- [ ] Persist review, iteration, validation and sanitized load-receipt evidence.
- [ ] Mark only the constrained `load-test` gate complete when every acceptance criterion passes.
- [ ] Keep managed staging capacity, WAF/DDoS, deployed telemetry, alert routing and production approval blocked.
- [ ] Merge only after exact-head CI, resolved review threads and explicit merge authorization.

## Stop Conditions

- Missing explicit human approval for this specification.
- A paid service, cloud resource, Terraform apply or production environment becomes necessary.
- A new dependency or lockfile change is required without expanded approval.
- The harness would contact citizens, publish, spend, mobilize or invoke a live political/AI provider.
- Sensitive identifiers cannot be excluded from retained evidence.
- Exact authorization or tenant-isolation ordering cannot be preserved.
- Timing thresholds cannot be made stable without weakening correctness gates.
- A failure cannot be repaired inside the affected subgraph.
