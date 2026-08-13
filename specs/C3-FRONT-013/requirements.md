# C3-FRONT-013 Requirements

## Summary

Remove the candidate-workspace dead end so an exactly authorized, nontechnical campaign operator can complete every existing candidate evidence gate and version-bound internal approval from the CampaignOS UI.

## Product finding

The campaign-completeness evaluation found that the candidacy chapter correctly names identity, biography, purpose, values, attributes, contradictions, development goals, reputation risks and approvals, while the interactive UI only exposes workspace creation and source registration. The backend already supports all candidate sections and section approvals, so the current UI leaves the operator unable to satisfy the gate that unlocks downstream strategy work.

## Mode

SHIP localized repair under the existing Graph Harness program.

## Human authorization

The user explicitly requested continuation of the Graph Harness lifecycle to finish the product gap described as “As the single operating system for a complete real campaign today: NO, not yet.” This increment is bounded to internal repository/UI behavior and existing authorization contracts.

## Acceptance criteria

- [ ] Exactly authorized users can edit identity, biography and purpose as evidence-linked claims.
- [ ] Exactly authorized users can maintain values, candidate attributes, contradictions, development goals and reputation risks without using an undocumented API.
- [ ] Candidate section forms preserve current records unless the user explicitly changes the edited section.
- [ ] Evidence references are selected from the campaign's existing candidate evidence register; the UI never labels an unsupported statement as verified.
- [ ] The UI explains when independent evidence is required for a verified claim and when a high/critical reputation risk blocks approval readiness.
- [ ] Exactly authorized users can append version-bound internal approvals for each currently approvable candidate section.
- [ ] Any candidate update invalidates prior current-version approvals exactly as the existing backend contract requires, and the UI explains that consequence before save.
- [ ] The candidate chapter exposes a direct, actionable path for every incomplete candidate check instead of a read-only checklist.
- [ ] Read-only review mode renders no mutation forms and contains no visible `demo` wording.
- [ ] ES/EN meanings remain equivalent and task-oriented.
- [ ] No voter profiling, persuasion scoring, targeting, citizen contact, publication, spending, mobilization, production deployment or new authority is introduced.
- [ ] Focused tests, frontend verification, browser accessibility/responsiveness, complete repository gates and the API-backed functional journey pass.

## Non-goals

- strategy-workspace authoring (next graph node after this repair);
- roadmap/War Room authoring (subsequent graph node);
- new database schema or migration;
- new dependencies;
- Firmes integration;
- production/cloud deployment or paid services.
