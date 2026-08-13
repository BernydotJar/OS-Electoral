# C3-TEAM-005 Requirements

## Summary

Remove the final Team Builder readiness dead end so an exactly authorized operator can review training requirements and access recommendations through the existing team workspace contract and reach `READY_FOR_HUMAN_REVIEW` when the backend-derived checks are complete.

## Product finding

The Team workspace is created with `training_requirements=null` and `access_recommendations=null`. Existing UI can define role cards and RACI work, while the backend requires both supporting collections to be explicitly reviewed before Team becomes `READY_FOR_HUMAN_REVIEW`. The UI currently renders those collections read-only and has no mutation path, so the sequential campaign journey keeps Strategy locked.

## Acceptance criteria

- [ ] Exact-authorized users can explicitly record that training requirements were reviewed with no items, producing `training_requirements=[]` rather than leaving the review unassessed.
- [ ] Exact-authorized users can add/edit training requirements tied to an existing team role and maintain their backend-defined progress status.
- [ ] Exact-authorized users can explicitly record that access recommendations were reviewed with no items, producing `access_recommendations=[]` rather than leaving the review unassessed.
- [ ] Exact-authorized users can add/edit campaign-scoped access recommendations tied to an existing team role, with status `PROPOSED`, `REVIEWED`, or `REJECTED`; recommendations never become permissions.
- [ ] Updates replace only the edited supporting collection, preserve all unrelated team records, and use current workspace version plus idempotency.
- [ ] The UI explains that empty review means “reviewed, none recorded,” not “not assessed.”
- [ ] When existing backend checks are otherwise complete, the browser can move Team from `STRUCTURE_IN_PROGRESS` to `READY_FOR_HUMAN_REVIEW` without fabricating a filled role, membership, grant, or external effect.
- [ ] Read-only review mode renders no Team readiness mutation forms and contains no visible `demo` wording.
- [ ] ES/EN, mobile, keyboard, reduced motion, overflow and WCAG checks pass.
- [ ] Focused tests, PostgreSQL/API/browser journey and repository gates pass with `external_effects=NONE`.

## Non-goals

- assigning identities to vacant roles or granting application permissions;
- changing Training Academy authorization or completion receipts;
- Strategy authoring (blocked successor C3-FRONT-014);
- Firmes integration, production deployment, cloud spend or political external effects.
