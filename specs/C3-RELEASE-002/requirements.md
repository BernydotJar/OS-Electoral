# C3-RELEASE-002 — Final controlled-use readiness requirements

State: `APPROVED_IN_PROGRESS`

## Goal

Produce a fail-closed, evidence-backed decision for using the complete current CampaignOS product in an isolated internal environment now, without conflating controlled internal use with production readiness.

## Requirements

1. The assessment SHALL be based on the actual protected `main` baseline and SHALL reconcile canonical Git/GitHub state before evaluating readiness.
2. Backend quality, frontend quality, independent browser review, and the PostgreSQL/API/browser functional journey SHALL pass against the current product.
3. The functional journey SHALL prove campaign creation/context, Candidate completion, Team readiness and human role coverage, Strategy human decision, Operations lifecycle, War Room snapshot, reload persistence, exact authorization, ES/EN/mobile and WCAG behavior.
4. A machine-readable controlled-use record SHALL fail closed unless every controlled-use gate is `PASS`.
5. `READY_FOR_CONTROLLED_INTERNAL_USE` SHALL require production status `BLOCKED`, production release decision `DENY_RELEASE`, and external effects `NONE`.
6. The development identity SHALL remain localhost/isolated-environment only and SHALL NOT be approved for public or production exposure.
7. FIRMES SHALL remain outside the executable scope while `C3-FIRMES-001` human approval is pending.
8. Operator and release documentation SHALL describe the capabilities and grant model that actually exist on the assessed baseline.
9. The program validator SHALL reject canonical cumulative-main drift when validating a checkout of `main`.
10. No cloud infrastructure, paid service, production deployment, citizen contact, targeting, persuasion, publication, spending, mobilization, or credential rotation is authorized by this increment.

## Acceptance criteria

- Current `main` reconciliation is explicit and covered by a regression test.
- Complete frontend/backend verification passes.
- Independent read-only browser review passes with zero axe violations and no unexpected external hosts/errors.
- The real PostgreSQL/API/browser journey passes through Candidate → Team → Strategy → Operations → War Room with persistence and no external effects.
- Controlled-use readiness validator and adversarial tests pass.
- Operator/release docs no longer claim five grants or unimplemented Training/campaign-creation/rate-limit capabilities that are already present.
- Production remains `BLOCKED`, `DENY_RELEASE`; Firmes remains human-gated.
