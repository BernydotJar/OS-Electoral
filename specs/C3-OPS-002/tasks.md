# C3-OPS-002 Tasks

## Approval and Preparation

- [ ] Record explicit human approval and move the node from `spec_ready` to approved/ready.
- [ ] Complete the pinned primary-documentation checkpoints.
- [ ] Confirm exactly one active Graph Harness feature and no deployment, cloud-spend or production authority.

## Producer

- [ ] Inventory current migrations, application artifacts, health/readiness checks, recovery evidence, worker semantics and release gates.
- [ ] Define the strict rollback policy, migration classification and scenario catalog.
- [ ] Implement the validator, response selector and sanitized receipt writer.
- [ ] Add bounded local/CI rehearsal fixtures without executing destructive rollback.
- [ ] Document application, configuration, schema, worker, restore and containment procedures.
- [ ] Add Makefile and hosted CI integration without new dependencies.
- [ ] Update release-readiness references while preserving every unsatisfied managed gate.

## Verification

- [ ] Test every required scenario and response class.
- [ ] Test missing authority, mutable artifact, unknown schema, committed writes, destructive command and secret-bearing receipt refusal.
- [ ] Test migration classification completeness and compatibility-window decisions.
- [ ] Test health/readiness, authorization/RLS, audit continuity and cleanup evidence.
- [ ] Test failed receipt persistence and supersession handling.
- [ ] Run Ruff, format, strict mypy and focused tests.
- [ ] Run the complete locked Python suite with the coverage floor.
- [ ] Run applicable frontend verification only if frontend behavior changes.
- [ ] Run program, release, security, recovery, Terraform-policy and supply-chain validators.
- [ ] Run effective-worktree, committed-range and submitted-diff secret scans.
- [ ] Collect exact-head hosted CI and retained sanitized receipt evidence.

## Critic / Red Team

- [ ] Attempt default Alembic downgrade and destructive restore selection.
- [ ] Attempt rollback to a branch, tag or mutable image without provenance.
- [ ] Attempt configuration reversal that disables authorization, audit, RLS, rate limiting or safety.
- [ ] Attempt worker/outbox replay without exact human authority.
- [ ] Attempt sensitive data injection into the receipt and operator log.
- [ ] Attempt to infer production readiness from local/CI evidence.

## Fixer and Independent Verifier

- [ ] Repair only the affected policy, validator, rehearsal or documentation subgraph.
- [ ] Preserve failed validation and supersession evidence.
- [ ] Independently rerun equal-or-broader focused and complete gates.
- [ ] Record SHIP review decisions for security, data correctness, failure modes, observability, testing and operations.

## Release Gate and Persistent Evidence

- [ ] Persist review, iteration, validation and sanitized rehearsal evidence.
- [ ] Move only the repository `rollback-runbook` gate from `NOT_IMPLEMENTED` to `PARTIAL` after all criteria pass.
- [ ] Keep managed staging rollback, RPO/RTO, PITR, live environments and production approval blocked.
- [ ] Merge only after exact-head CI, resolved review threads and explicit merge authorization.

## Stop Conditions

- Missing explicit human approval for this specification.
- A cloud resource, paid service, Terraform apply, registry publication or production environment becomes necessary.
- A new dependency or lockfile change is required without expanded approval.
- The implementation would execute destructive database commands or restore over a live database.
- Existing authorization, RLS, audit, rate-limit or safety controls would need to be weakened.
- Sensitive evidence cannot be excluded from retained receipts.
- The work would contact citizens, publish, spend, mobilize or create political external effects.
- A failure cannot be repaired inside the bounded rollback-policy subgraph.
