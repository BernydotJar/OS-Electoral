# C3-FRONT-014 Requirements

## Summary

Remove the strategy-workspace dead end so an exactly authorized campaign operator can build an evidence-first internal strategy, compare at least two alternatives, define measurable objectives, resolve contradictions and red-team blockers, and append the existing version-bound human strategy decision from the CampaignOS UI.

## Product finding

After C3-FRONT-013, the campaign journey can reach Strategy only after the candidate is internally approved and the team reaches human-review readiness. The Strategy chapter currently projects the existing backend workspace read model, but exposes no create, update or decision controls. The backend already implements all three mutation contracts plus the append-only decision receipt, so the UI is the remaining product-completion gap.

## Mode

SHIP localized product-completion repair under the existing Graph Harness program.

## Human authorization

The current user instruction explicitly directs the Graph Harness to continue beyond a single feature until all useful, safe, unlocked and verifiable product-completion work is exhausted. This increment is bounded to internal strategy authoring and decision capture through existing exact authorization contracts.

## Acceptance criteria

- [ ] Exact-authorized users can create the existing campaign strategy workspace from the Strategy chapter after journey prerequisites are satisfied.
- [ ] Exact-authorized users can add and edit provenance-bearing strategy evidence without treating unknown or inferred material as verified fact.
- [ ] Assumptions and hypotheses can link only to existing strategy evidence/assumptions and expose invalidation signals.
- [ ] At least two comparable strategy options can be authored with hypotheses, evidence, benefits, risks and tradeoffs.
- [ ] Measurable objectives can be authored with metric, baseline, target, deadline and an owner selected from existing Team Builder roles.
- [ ] Contradictions and red-team findings can be recorded and resolved; explicit reviewed-empty states are supported without fabricating findings.
- [ ] The UI exposes the backend-derived readiness counts/status/next action and does not claim decision readiness independently.
- [ ] When the backend reports `READY_FOR_HUMAN_DECISION`, an exactly authorized human can append a decision selecting one existing option, one existing team role and a reason.
- [ ] The decision remains internal, append-only and version-bound; subsequent workspace mutation makes the prior decision non-current by existing backend semantics.
- [ ] Read-only review mode renders no strategy mutation forms/endpoints and contains no visible `demo` wording.
- [ ] ES/EN meanings remain equivalent; mobile, keyboard, reduced motion, overflow and WCAG checks pass.
- [ ] No voter profiling, individual targeting, persuasion scoring, citizen contact, publication, spending, mobilization, production deployment or new authority is introduced.
- [ ] Focused tests, API-backed PostgreSQL/browser lifecycle and complete repository gates pass with `external_effects=NONE`.

## Non-goals

- roadmap or War Room authoring (subsequent graph node);
- new strategy database schema or backend decision rules;
- automated strategic choice or recommendation of a winning option;
- voter-level segmentation, targeting, persuasion, contact or mobilization;
- Firmes integration;
- production/cloud deployment or paid services.
