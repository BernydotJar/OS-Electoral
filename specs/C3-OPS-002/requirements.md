# C3-OPS-002 Requirements

## Summary

Add a fail-closed, versioned release rollback and reversal runbook for CampaignOS. The increment must turn the current informal rollback references into an executable decision contract, sanitized rehearsal receipt and operator procedure without deploying infrastructure, changing production state or claiming that a managed rollback has been proven.

This is a SHIP-mode operations increment. It may move the repository `rollback-runbook` gate from `NOT_IMPLEMENTED` to `PARTIAL` after local and hosted CI evidence passes. Managed staging rollback, production image promotion, RPO/RTO acceptance, point-in-time recovery and human production approval remain separate blocked gates.

## Mode

SHIP.

## Acceptance Criteria

- [ ] A versioned rollback policy distinguishes release abort, application artifact rollback, configuration reversal, database forward-fix, isolated restore and incident containment.
- [ ] Every rollback path declares trigger, owner, prerequisites, prohibited actions, exact artifact or schema evidence, validation steps, stop conditions and escalation path.
- [ ] The runbook never treats an Alembic downgrade or destructive database restore as the default response.
- [ ] Database changes are classified as backward-compatible, explicitly reversible and tested, forward-fix only, or restore-required; unknown classification fails closed.
- [ ] Application rollback permits only a previously verified immutable revision or digest with retained provenance and compatibility evidence.
- [ ] Configuration rollback records exact before/after values without retaining secrets and cannot weaken authentication, authorization, RLS, audit, rate limiting or safety controls.
- [ ] Worker and outbox handling prevents duplicate external delivery, preserves dead-letter evidence and does not replay events automatically.
- [ ] Restore guidance requires a separately named isolated target, integrity checks, tenant/RLS smoke tests and human acceptance before any managed recovery decision.
- [ ] A repository-owned validator rejects missing approvals, mutable artifact references, unknown migration classifications, absent health criteria, destructive commands, secret-bearing receipts and false production claims.
- [ ] A bounded local/CI rehearsal exercises decision selection, application compatibility checks, migration-state inspection, health/readiness verification, evidence generation and cleanup without cloud resources.
- [ ] The machine-readable receipt records source SHA, previous-known-good reference, schema head, scenario, selected action, evidence checks, decision, cleanup and limitations while excluding credentials, URLs with secrets, tenant/principal IDs, request bodies and political content.
- [ ] Failed rehearsals and superseding evidence remain append-only and auditable.
- [ ] Release, security, recovery, supply-chain, Terraform plan-only, frontend and complete repository gates remain green.
- [ ] Production remains `BLOCKED`, release remains `DENY_RELEASE`, and external effects remain `NONE`.

## Required Rollback Scenarios

- release stopped before migration;
- application health failure after a backward-compatible migration;
- application health failure when schema compatibility is unknown;
- stale or failed migration with no committed domain writes;
- suspected data-integrity failure after writes;
- identity-provider or database dependency outage;
- worker retry/dead-letter growth;
- configuration regression;
- recovery from a verified backup into an isolated target;
- rollback attempt that must be refused because evidence or authority is missing.

## Non-Goals

- Terraform apply, AWS account creation, environment provisioning or paid services.
- Production deployment, rollback, database restore or point-in-time recovery.
- Publishing or promoting container images to a registry.
- Automatically running `alembic downgrade`, destructive SQL, queue replay or secret rotation.
- Accepting RPO/RTO, production capacity or managed-environment compatibility.
- Disabling authorization, audit, rate limiting, safety or tenant-isolation controls to recover service.
- Contacting citizens, publishing campaign content, spending, mobilizing or producing any political external effect.

## MVP Criteria

- Versioned policy and scenario catalog.
- Strict validator and sanitized rehearsal receipt.
- Operator runbook with decision tree and exact stop conditions.
- Unit/contract tests plus bounded local/CI rehearsal.
- Explicit staging handoff and unchanged production block.

## SHIP Criteria

- security: authority, immutable artifact, secret handling and control-preservation checks fail closed;
- data correctness: schema compatibility, forward-fix, restore isolation and integrity checks are explicit;
- failure modes: every required scenario selects one bounded action or refuses to proceed;
- observability: health, readiness, metrics, audit and recovery evidence are named without sensitive labels;
- testing: policy, parser, validator, CLI, adverse receipt and complete repository tests pass;
- operations: roles, communications, evidence retention, cleanup and escalation are usable by an operator;
- release: producer, critic/red-team, fixer, independent verifier and exact-head CI evidence are persisted while production stays blocked.
