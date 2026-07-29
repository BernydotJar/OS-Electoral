# C3-SEC-002 Requirements

## Summary

Add server-enforced, tenant- and principal-scoped API rate limiting and abuse protection so CampaignOS can bound authenticated request volume without relying on UI state, role labels, raw voter data, or a single application process.

This is a SHIP-mode security increment. It closes the currently `NOT_IMPLEMENTED` rate-limiting gate only for application-layer authenticated traffic. Edge DDoS protection, WAF policy, production sizing, and live-environment acceptance remain separate platform gates.

## Mode

SHIP.

## Acceptance Criteria

- [ ] Every protected `/api/v1` operation is assigned to a reviewed rate-limit policy class: read, mutation, expensive read, identity lifecycle, or governed agent execution.
- [ ] Enforcement keys are derived server-side from authenticated principal, tenant, policy class, and bounded time window; caller-provided role labels or UI context never create exemptions.
- [ ] Cross-tenant requests cannot consume, inspect, reset, or infer another tenant's counters.
- [ ] Limits are enforced consistently across multiple API processes through PostgreSQL-backed atomic mutation under forced tenant isolation.
- [ ] Anonymous health/liveness behavior remains available as designed, while readiness, metrics, and authenticated routes preserve their existing authorization contracts.
- [ ] Rejected requests return a sanitized RFC 9457-style `429` response with `Retry-After`, correlation ID, stable machine code, and no raw counter key or sensitive identity value.
- [ ] Store failure behavior is explicit and fail-closed for protected mutations and governed agent execution; read-only policy classes use only a separately approved bounded fallback, if any.
- [ ] Metrics and logs are low-cardinality and contain no raw bearer token, email, IP address, campaign-sensitive payload, or voter-level information.
- [ ] Concurrency, replay, clock-boundary, cross-tenant, BOLA, configuration, unavailable-store, and recovery tests pass against PostgreSQL.
- [ ] Existing idempotency, authorization, audit, RLS, error, and browser contracts remain green.

## Non-Goals

- Edge-network volumetric DDoS mitigation or replacement for CloudFront/WAF.
- Voter, supporter, volunteer, citizen, or campaign-contact profiling.
- Behavioral scoring, persuasion scoring, or per-person political surveillance.
- Automatic account suspension, membership revocation, or grant mutation.
- A customer-facing rate-limit administration UI.
- Production capacity claims without staging load evidence.
- External Redis, managed cache, or new package dependency in this increment.

## i18n

- English copy: stable localized title and guidance for throttled UI mutations when surfaced by the frontend.
- Spanish copy: equivalent non-technical explanation and retry guidance.
- Layout resilience: error content must fit mobile and desktop without exposing identifiers.
- Validation and error messages: machine code remains locale-neutral; user copy is localized at the UI boundary.
- Empty states: not applicable.
- Accessibility labels: retry guidance and disabled/retry controls remain perceivable without relying on color or motion.

## MVP Criteria

- Bounded policy catalog and server-owned key derivation.
- Atomic PostgreSQL-backed enforcement for selected high-risk routes.
- Unit, API, and PostgreSQL concurrency tests.
- Sanitized `429` contract with `Retry-After`.
- Review evidence and documented limitations.

## SHIP Criteria

- security: exact authorization occurs before scoped counter mutation where resource scope is required; no bypass by labels, headers, or client context; abuse cases documented.
- data correctness: database time, policy version, counter identity, window rollover, concurrency, retry, and cleanup semantics are deterministic.
- performance: bounded index-backed statements, no unbounded scans, measured local/CI contention budget, and explicit staging load gate.
- failure modes: unavailable database, stale policy, invalid configuration, clock boundary, concurrent burst, and transaction rollback are covered.
- observability readiness: low-cardinality allow/deny metrics, sanitized structured events, and alert-hook locations are documented.
- testing: happy path, negative path, invalid input, cross-tenant, BOLA, concurrent burst, replay, expiry, store failure, and regression suites.
- UX/accessibility: localized retry guidance, keyboard-safe retry behavior, mobile reflow, and reduced-motion equivalence when the UI surfaces throttling.
- operations: migration review, rollout/rollback notes, counter-retention policy, configuration ownership, and release evidence are required.
