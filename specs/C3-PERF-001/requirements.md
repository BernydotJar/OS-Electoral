# C3-PERF-001 Requirements

## Summary

Add a deterministic, bounded and cost-free authenticated load-verification harness for CampaignOS. The harness must measure API behavior, PostgreSQL contention, rate-limit enforcement, failure recovery and evidence quality without creating cloud resources or making a production-capacity claim.

This is a SHIP-mode verification increment. It closes the repository's `load-test` gate only for constrained local and hosted CI evidence. Managed staging capacity, edge DDoS/WAF behavior, deployed telemetry, alert routing and production acceptance remain separate platform gates.

## Mode

SHIP.

## Acceptance Criteria

- [ ] A versioned workload catalog covers authenticated reads, mutations, expensive reads, identity lifecycle operations and governed-agent routes using deterministic server-owned fixtures.
- [ ] Every scenario declares its route class, request count, concurrency, timeout, expected response classes, authorization scope and cleanup behavior.
- [ ] Workloads are bounded to disposable local/CI PostgreSQL 18 and use no paid service, Terraform apply, live campaign account, citizen contact, publishing, spending or mobilization capability.
- [ ] Authenticated malformed traffic is counted before request-model binding while exact tenant authorization remains fail-closed before tenant-scoped budget consumption.
- [ ] Cross-tenant and BOLA attempts never return authorized data, mutate domain state, consume another tenant's scoped budget or expose tenant existence.
- [ ] Concurrent rate-limit scenarios produce exact allowed/denied totals, bounded counters and stable rollover semantics without lost updates.
- [ ] Domain validation, conflict, exception or rollback cannot refund an already consumed abuse budget.
- [ ] Store-unavailable, timeout and injected failure paths return only expected sanitized response classes and leave no leaked sessions, open transactions or fixture residue.
- [ ] Receipts record source SHA, tool/schema version, PostgreSQL version, scenario configuration, totals, latency percentiles, response classes, rate-limit outcomes, pool gauges, threshold decisions and cleanup results.
- [ ] Receipts exclude bearer tokens, cookies, database URLs, request bodies, tenant/principal identifiers, IP addresses, political content and voter-level data.
- [ ] CI thresholds fail closed and are explicitly labeled constrained-environment regression thresholds rather than production SLO or capacity evidence.
- [ ] Existing authorization, RLS, idempotency, audit, error, recovery, supply-chain and browser gates remain green.

## Bounded Verification Envelope

- maximum 20 concurrent workers per scenario;
- maximum 600 requests per scenario;
- maximum 60 seconds per scenario and 10 minutes for the focused harness;
- no unbounded soak, fuzz, scan or full-table workload;
- zero unexpected `5xx` responses;
- zero authorization or cross-tenant invariant violations;
- exact rate-limit allow/deny counts for deterministic fixed-window scenarios;
- no connection-pool leak after cleanup;
- latency sanity ceilings may guard regressions but must not be represented as production SLOs.

## Non-Goals

- Production capacity certification, autoscaling validation or customer concurrency sizing.
- Edge-network volumetric DDoS, CDN or WAF validation.
- Provisioning AWS, managed PostgreSQL, load generators, dashboards or alert receivers.
- Tuning production limits, pool sizes or database parameters merely to satisfy the harness.
- Voter, supporter, volunteer, citizen or campaign-contact profiling.
- Behavioral, persuasion, turnout, mobilization or person-level scoring.
- A general-purpose benchmarking platform or new paid dependency.
- Executing a live agent provider, external publication, outreach or political action.

## MVP Criteria

- Deterministic workload and threshold contracts.
- Bounded authenticated runner with timeout and cleanup.
- PostgreSQL contention and rate-limit correctness scenarios.
- Sanitized machine-readable receipt and regression tests.
- Operator documentation and explicit staging handoff.

## SHIP Criteria

- security: authentication, opaque preauthorization budgets, exact grant ordering, BOLA isolation and sanitized evidence are verified under concurrency;
- data correctness: transaction boundaries, fixed-window counts, rollback accounting, RLS, cleanup and fixture lifecycle are deterministic;
- performance: bounded request generation, latency/throughput observation, pool-pressure evidence and stable constrained-CI thresholds exist;
- failure modes: malformed input, denied authorization, store failure, timeout, connection pressure, cancellation and cleanup are covered;
- observability readiness: low-cardinality metrics and JSON receipts identify scenario and outcome without sensitive labels;
- testing: unit, contract, API, PostgreSQL 18, threshold, receipt-schema and complete regression suites pass;
- operations: repeatable commands, runtime ceilings, cleanup, retained evidence, limitations and staging handoff are documented;
- release: producer, critic/red-team, fixer, independent verifier and release gate evidence are persisted while production remains `BLOCKED`.
