# ADR 002: Modular monolith before microservices

Status: **PROPOSED**
Date: `2026-07-19`

## Context

CampaignOS has many business domains but no measured need for independently scaled services. Early distribution would multiply deployment, authorization, transaction, observability, and incident complexity before core semantics are stable.

## Decision

Use one versioned Python application and one primary PostgreSQL database as a modular monolith. Each bounded context owns its domain model, application interfaces, tables, and events. HTTP and worker entry points call application services; infrastructure adapters implement ports. Cross-context durable side effects use an outbox and idempotent consumers.

The web application is deployed separately but never accesses the database directly.

## Consequences

- Local changes and transactional consistency remain understandable.
- Module-boundary tests and import rules are required to prevent a “big ball of mud.”
- Worker processes may share the same package while using separate runtime commands.
- Service extraction requires measured scaling, reliability, security, data-sovereignty, or ownership evidence plus a new ADR.
- Kubernetes/EKS and a service mesh are excluded from the first production release.
