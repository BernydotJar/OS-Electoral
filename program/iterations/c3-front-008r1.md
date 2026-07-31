# C3-FRONT-008R1 — QA command surface and local readiness repair

- `branch`: `agent/c3-front-008r1-qa-command-surface`
- `base`: `main@a8c61170c55aeba59e3830837c869b572fe84a9a`
- `mode`: `SHIP`
- `status`: `REVIEWED`
- `production_status`: `BLOCKED`
- `release_decision`: `DENY_RELEASE`
- `external_effects`: `NONE`

## Trigger

Human QA confirmed guided setup, candidate workspace, bilingual behavior and responsive behavior, while reporting:

- a frontend-port `/api/v1/ready` request rendered the CampaignOS 404 page;
- the command overview repeated a dominant active-mission hero;
- chapter routes did not put the referenced workspace first enough.

## Decision

Repair presentation and diagnostics locally rather than redesigning the domain or adding generated media:

1. one interactive command overview replaces the hero-plus-roadmap duplication;
2. compact chapter command bars preserve orientation through progressive disclosure;
3. the requested workspace begins immediately after the command bar;
4. same-origin readiness works on the frontend port;
5. functional-development output names each effective URL explicitly.

## Role-separated execution

### Producer

Implemented the command overview, chapter bars, readiness proxy, launcher output, localized copy and deterministic evaluators.

### Critic / red team

Checked misleading authority, broken blocked-stage actions, sensitive readiness leakage, task displacement, keyboard access, mobile overflow, reduced motion and external hosts.

The critic found an unnamed progress control. The implementation was repaired and the gate rerun unchanged.

### Independent verifier

- complete frontend verification passed;
- dynamic production-build Chromium review passed;
- isolated PostgreSQL/API/browser journey passed;
- complete repository `make verify` passed;
- candidate-workspace United States strategist evaluator recorded qualified usability and explicit production limitations.

## Failed and superseded evidence

- Initial dynamic browser review: failed only because the visual progress element lacked an accessible name; superseded by a passing equal-or-broader review after localized repair.
- Nested Docker functional runner: stopped before application startup on sandbox layer registration (`lchown /var/empty: permission denied`); superseded for local product behavior by the isolated host PostgreSQL/API/browser journey. Hosted CI remains authoritative for PostgreSQL 18 and container evidence.
- Repeated functional host run: encountered persisted completed fixtures; an isolated clean database rerun passed first-use plus persistence contracts.

## Result

The node is locally reviewed and ready for exact-head hosted verification. It does not authorize production, media generation, publication, spending, targeting, contact or mobilization.
