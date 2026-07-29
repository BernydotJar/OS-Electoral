# Design — C3-PERF-001

## Boundary

This increment adds verification tooling only. It does not provision infrastructure, apply Terraform, alter production limits, publish campaign material, contact citizens, or claim production capacity.

## Workload model

Use a deterministic workload catalog with bounded concurrency and duration. Each scenario identifies route class, authorization fixture, expected status mix, maximum requests, concurrency, and evidence labels. Use existing API, PostgreSQL, metrics, and test dependencies; prefer standard-library concurrency and current locked tooling.

## Evidence

Emit a versioned JSON receipt containing source SHA, PostgreSQL version, scenario configuration, request totals, latency percentiles, response classes, rate-limit outcomes, pool gauges, threshold decisions, and cleanup result. Exclude tokens, tenant/principal identifiers, request bodies, political content, and raw database URLs.

## Gates

Thresholds must fail closed, be stable in constrained CI, and remain explicitly non-production. Managed staging load remains a separate platform gate. A regression in authorization, RLS, error sanitization, or cleanup fails the node regardless of aggregate throughput.

## Localized repair

Failures repair only the scenario, runner, threshold, or affected product defect. Do not globally tune application limits or database configuration merely to satisfy the harness.
