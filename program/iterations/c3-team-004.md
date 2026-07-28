# C3-TEAM-004 — Role operations board

- `branch`: `agent/c3-team-004-role-operations-board`
- `base`: `agent/c3-front-007-guided-chapter-transitions@0a93c27ccb99fec3e4e4ac9f9d2475d098df995c`
- `status`: `CI_GREEN`
- `production_status`: `BLOCKED`
- `release_decision`: `DENY_RELEASE`
- `external_effects`: `NONE`

## User problem

Human review confirmed that the team map described roles but did not operate the campaign. It lacked role-bound tasks, deliverables, blockers, next actions, dates, cadence, explicit health and a usable attention view.

## Bounded objective

1. extend existing RACI work items with operational metadata and backward-compatible defaults;
2. add deterministic work rollups without scoring people;
3. let an authorized user create planned work against an organizational function;
4. require filled human functions before active or blocked execution;
5. record explicit human check-ins, blockers, evidence and next actions;
6. put an interactive operating board before the compact role directory;
7. preserve exact authorization, tenant isolation, optimistic concurrency, audit, outbox and zero external effects.

## Acceptance criteria

1. Historical work items load with safe defaults.
2. Blocked and at-risk states cannot exist without consistent blocker/health/check-in evidence.
3. Projection counts total, planned, active, blocked, complete and attention work deterministically.
4. New work starts planned and receives exact organizational RACI.
5. Active, blocked or completed state remains unavailable while accountable/responsible functions are vacant.
6. Board filters by function, status and attention; mobile is one column without overflow.
7. Role cards expose workload/attention summaries and retain keyboard-operable dossiers.
8. No person score, implicit authority, citizen contact, publishing, spending or deployment is introduced.

## Local validation

- 69 focused backend tests passed with Ruff, format and strict mypy.
- 111 frontend tests passed with lint, TypeScript, production build and zero-vulnerability audit.
- Demo ES/EN/mobile browser review passed with zero axe violations and no overflow.
- Hosted PostgreSQL/browser journey is updated; local nested Docker failed before product execution while registering an upstream image layer.

## Exact-head CI closure

- validated implementation head: `0fb7cadd5f81c4c38a77f195e6b24d20e580cca5`
- draft PR: `#125`
- CampaignOS CI: `30380383123` — `SUCCESS`
- Runtime Visual Review: `30380383149` — `SUCCESS`
- quality job: `90346485479`
- API/PostgreSQL/browser job: `90346485404`
- visual job: `90346485053`
- recovery job: `90346485372`
- status: `CI_GREEN`
- production: `BLOCKED`
- release: `DENY_RELEASE`
- external effects: `NONE`
