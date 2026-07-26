# C3-TEAM-003 — Governed template application preview

- `branch`: `agent/c3-team-003-template-application-preview`
- `base`: `agent/c3-team-002-role-blueprints-cinematic-hero@e0ca30589f610361254e5348e9b9fd3c77e42b57`
- `status`: `CI_GREEN`
- `production_status`: `BLOCKED`
- `release_decision`: `DENY_RELEASE`
- `external_effects`: `NONE`

## User problem

A campaign that starts compactly needs to grow without recreating its team map, overwriting real organization data or guessing which bilingual functions are duplicates. A generic patch does not provide an understandable preview or bind human confirmation to the state that was reviewed.

## Bounded objective

1. preview template additions against the current workspace version;
2. recognize built-in functions across Spanish and English;
3. preserve exact historical title/area matches;
4. bind confirmation to a deterministic digest;
5. apply only missing vacant functions under idempotency and row locking;
6. audit preview and application with exact authorization evidence;
7. expose a responsive, keyboard-operable two-step live workflow;
8. preserve all authority and production boundaries.

## Acceptance criteria

1. Full preview over a Spanish lean map proposes five and preserves three functions.
2. Proposed IDs and digest are stable for the same version and change when the version changes.
3. Preview records an audit receipt but no external or authorization effect.
4. Apply requires `If-Match`, `Idempotency-Key` and the exact digest.
5. Apply is append-only, idempotent and atomically audited/outboxed.
6. Stale versions, digest drift and no-op templates fail closed with rollback.
7. The live UI separates preview/confirm from manual role creation.
8. Mobile preview reflows to one column without overflow.
9. Production remains blocked and no campaign execution occurs.

## Validation record

- Backend focused suite: 49 PASS.
- Full Python suite: 724 PASS, 10 controlled skips, 90.37% coverage.
- Ruff and strict mypy: PASS across 68 source files.
- Frontend: 97 PASS, lint, TypeScript, production build and zero-vulnerability audit.
- Exact-head CampaignOS CI `30225102075` and visual review `30225102063` passed.
- Hosted PostgreSQL/browser evidence proved lean 5 → full 10 → manual 11, bilingual deduplication, one-column mobile preview, reload persistence, keyboard interaction and zero axe violations.

## Product boundaries

This increment does not assign people, alter existing people, create capacity, RACI, onboarding, memberships, permissions, access, content, contact, spending, mobilization, deployment or production authority.


## Exact-head CI receipts

- implementation head: `2130f2cd89711aedd710c1e363a4154a48ef5ecb`
- draft PR: `#123`
- CampaignOS CI: `30225102075` — `SUCCESS`
- Runtime Visual Review: `30225102063` — `SUCCESS`
- quality job: `89853902939`
- API/PostgreSQL browser job: `89853902928`
- visual job: `89853902732`
- recovery job: `89853902951`
- production remains `BLOCKED`; release remains `DENY_RELEASE`; external effects remain `NONE`.
