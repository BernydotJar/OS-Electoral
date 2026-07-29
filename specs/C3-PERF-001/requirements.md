# C3-PERF-001 — Authenticated load and contention verification

## Objective

Create a deterministic, cost-free SHIP verification harness that measures CampaignOS authenticated API capacity, PostgreSQL rate-limit contention, failure behavior, and recovery thresholds before any managed staging or production claim.

## Requirements

- [ ] Exercise representative authenticated reads, mutations, expensive reads, identity lifecycle, and governed-agent budgets.
- [ ] Generate bounded concurrent traffic against a disposable local/CI PostgreSQL runtime; never contact citizens, publish content, spend, or create cloud infrastructure.
- [ ] Measure throughput, latency percentiles, error classes, pool pressure, rate-limit decisions, and database contention with low-cardinality evidence.
- [ ] Prove malformed authenticated traffic is counted, exact authorization remains fail-closed, and cross-tenant/BOLA isolation remains intact under concurrency.
- [ ] Define explicit pass/fail thresholds derived from the existing constrained CI environment and label them non-production capacity evidence.
- [ ] Produce machine-readable evidence, operator guidance, and a repeatable CI gate without adding an external paid service.
- [ ] Preserve production `BLOCKED` until managed staging capacity, WAF/DDoS, deployed telemetry, alert routing, and human production approval exist.

## Acceptance

- deterministic workload catalog and seed state;
- repeatable bounded runner with timeout and cleanup;
- PostgreSQL 18 contention and rollback evidence;
- regression tests for thresholds and sanitized output;
- documented limitations and staging handoff;
- full local and exact-head hosted verification.
