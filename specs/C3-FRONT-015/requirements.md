# C3-FRONT-015 Requirements

## Summary

Remove the Operations/War Room UI dead end so an exactly authorized campaign operator can turn the internally decided Strategy into a governed execution roadmap and daily War Room snapshot using the already-merged CampaignOS backend contracts.

## Product finding

After C3-FRONT-014 the journey can reach an internal Strategy decision, but the Operations/War Room chapter remains read-only. The backend already supports roadmap create/update, phases, workstreams, milestones, dependency-aware tasks, blockers, human decisions, follow-ups, learning notes and append-only daily War Room snapshots. The highest-value next increment is therefore UI completion over existing work rather than a new domain.

## Acceptance criteria

- [ ] Operations authoring unlocks only after the current Strategy is `DECIDED_INTERNAL` and exact Operations grants are present.
- [ ] Exactly authorized users can create the existing roadmap with idempotency and update it with current-version `If-Match` plus idempotency.
- [ ] Phase, workstream, milestone, task and dependency references use existing records and preserve backend referential validation.
- [ ] Tasks expose owner roles from the existing Team workspace and never execute automatically.
- [ ] Blockers, human decisions, follow-up items and learning notes remain internal operating records with no external effects.
- [ ] Backend-derived readiness, blocked work and critical path remain authoritative; the UI does not invent execution status.
- [ ] Exactly authorized users can create the daily War Room snapshot from the current roadmap version and review the latest snapshot.
- [ ] Read-only review renders no mutation controls and no prohibited visible review-mode wording.
- [ ] ES/EN, mobile, keyboard, reduced motion, overflow and WCAG checks pass.
- [ ] No voter profiling, targeting, persuasion, citizen contact, publication, spending, mobilization, autonomous execution, Firmes integration or production deployment is introduced.
- [ ] Focused tests, PostgreSQL/API/browser lifecycle and complete repository gates pass with `external_effects=NONE`.

## Non-goals

- new Operations persistence schema or backend execution engine;
- autonomous task execution or automated political decision-making;
- voter-level targeting, persuasion, contact or mobilization;
- Firmes integration;
- production deployment or paid cloud services.
