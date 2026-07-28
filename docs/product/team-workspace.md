# Campaign team workspace

The team workspace is an internal organizational roadmap for campaign leadership. It makes role purpose, responsibility, availability, vacancies, onboarding, training and access recommendations explicit without turning organization labels into application authority.

## Users and job

Primary users are candidates, campaign directors and authorized operations reviewers. Their job is to answer:

- which roles exist and why;
- which roles are filled or vacant;
- who is accountable and responsible for each work item;
- whether filled roles have usable capacity;
- what onboarding or training remains;
- what access may be appropriate for human authorization review.

```yaml
design_variance: 6
motion_intensity: 4
visual_density: 6
```

The shell is bilingual and responsive. In an exactly authorized live session, team preparation becomes available in parallel after the candidate dossier exists. A user can choose an organizational template and document vacant functions one at a time. Demo mode remains read-only, and candidate evidence remains the primary gate.

## Core invariants

- every active, blocked or completed work item has exactly one `ACCOUNTABLE` role;
- every work item has at least one `RESPONSIBLE` role;
- active accountable and responsible assignments must use filled roles;
- filled roles require a principal, assessed availability and positive weekly capacity;
- vacant roles cannot have a principal or capacity and require a vacancy plan;
- RACI, training and access references resolve only to role cards in the same team workspace;
- campaign-scoped access recommendations use the campaign ID as resource ID;
- workspace-scoped recommendations use the same workspace ID as resource ID and the service verifies that the workspace belongs to the same tenant and campaign;
- access recommendations always declare `authority_effect=NONE`;
- successful writes declare `external_effects=NONE`.

## States

- `SETUP_REQUIRED`: role cards are not yet defined;
- `STRUCTURE_IN_PROGRESS`: accountability, availability, vacancies, onboarding, training or access review remains incomplete;
- `READY_FOR_HUMAN_REVIEW`: the deterministic organization checks are complete.

`READY_FOR_HUMAN_REVIEW` is not permission approval, hiring approval, campaign approval or production approval.

## Required checks

1. organization template selected;
2. role cards defined;
3. RACI accountability defined;
4. availability and capacity assessed;
5. vacancies identified and planned;
6. onboarding complete for filled roles;
7. training complete;
8. access recommendations reviewed or rejected.

## Mandatory limitations

```text
ROLE_LABELS_ARE_NOT_PERMISSIONS
ACCESS_RECOMMENDATIONS_REQUIRE_HUMAN_AUTHORIZATION
NO_VOTER_PROFILING
NO_EXTERNAL_EFFECTS
```

## Non-goals

The team workspace does not:

- create memberships, application roles or permission grants;
- contact citizens;
- score voters, personnel or political preferences;
- activate field operations, content, spending or mobilization;
- replace human hiring, legal, security or access review;
- infer authority from job titles or organization templates.

## Current implemented write path

The backend supports exact-authorized create, read, update, template preview and template application. The live shell now supports three bounded operations:

1. create a campaign team workspace from a lean, full or custom template;
2. preview and append only missing functions from a lean or full template;
3. append a vacant function manually with area, purpose, responsibilities and a human vacancy plan.

The UI deliberately creates no principal assignment, weekly capacity, onboarding completion, membership or permission. Personnel invitations, governed identity assignment, capacity assessment, training, access recommendation review, dedicated approvers and independent human acceptance remain future work. Organizational RACI and planned follow-up are now operable; execution still requires filled human roles.
## Role blueprints

`C3-TEAM-002` adds versioned, bilingual role blueprints at workspace creation time. They reduce blank-page setup without creating employment, identity, capacity, membership, permission, spending, publishing, contact or production authority.

- `LEAN_CAMPAIGN` creates five editable vacant job descriptions: campaign direction, research and evidence, territory and organization, communication and narrative, and administration/legal/finance.
- `FULL_CAMPAIGN` creates the eight CampaignOS operating stations: campaign leadership, electoral research, digital strategy, territory and mobilization, political content, paid media and distribution, storytelling/speech/media training, and tracking/risks/learning.
- `CUSTOM` remains empty and imposes no structure.

Every generated function contains a purpose, at least three responsibilities and a human coverage plan. Every generated function starts as `VACANT`, with no principal, no weekly capacity and no onboarding completion. The blueprint version and seeded role count are included in audit and internal outbox evidence.

The visible role cards now render the job description, responsibilities and human coverage plan. A user may add another non-duplicate vacant function afterward through the existing optimistic-concurrency workflow.

## Progressive campaign guidance

Returning users see the active mission and primary action first. The explanatory paragraph is available through the keyboard-operable `Why this matters` / `Por qué importa` disclosure rather than repeating as open onboarding copy on every visit. The additional cinematic atmosphere is CSS-owned, loads no third-party media and is disabled under reduced-motion preference.

## Evolving an existing map safely

`C3-TEAM-003` lets an authorized campaign operator apply a lean or full blueprint after a team map already exists. The workflow is deliberately two-step:

1. preview missing and preserved functions against the current workspace version;
2. confirm the exact preview digest before any mutation.

The preview is bilingual and canonical: a Spanish role such as `Dirección de campaña` is recognized as the same built-in function as its English variant. Historical cards that exactly match normalized title and area are also preserved. The interface explains both the proposed additions and the functions that will remain untouched.

Application is append-only. It never overwrites an existing role, changes a person, alters RACI, assigns capacity, completes onboarding, creates a membership or grants access. Proposed role IDs and the digest are deterministic for the observed workspace version, while the backend always recalculates the preview under lock before committing.

The live interface keeps this workflow separate from manual function creation. A no-op preview has no confirmation button. On narrow screens the impact summary, proposed job descriptions and preserved-role list reflow to one column without horizontal overflow.

## Consultant-grade function dossiers

`C3-FRONT-007` upgrades every versioned blueprint function from a descriptive card to a reusable operating dossier. In addition to purpose, responsibilities and the human coverage plan, each canonical function now contains:

- decisions it prepares or escalates for human review;
- verifiable deliverables expected from the function;
- key cross-functional interactions;
- observable signals that the function is operating coherently.

The profile is localized by canonical blueprint identity, so a Spanish function preserved during an English preview receives the same operating meaning. Proposed functions, preserved matches and applied functions expose the profile through one keyboard-operable disclosure. A historical role without these fields remains readable and is marked as requiring dossier completion rather than receiving invented content.

Manual function creation now requires the same four blocks. Each is entered as a bounded newline-separated list and rejects empty, duplicate or oversized entries. This keeps custom functions at the same organizational quality level as built-in blueprints.

These descriptors are consultative, not authoritative. They may prepare decisions or identify required approvals, but never create the approval, principal assignment, membership, permission, spending, publishing or external execution they describe.

## Chapter-based workspace experience

The campaign command overview no longer renders every workspace in one continuous document. Team work is available at `/{locale}/campaign/team`, while preparation, evidence, strategy and operations have their own routes. Chapter navigation, previous/next controls, browser history, form redirects and locale switching preserve the selected mission.

Only one campaign workspace is rendered on a chapter route. The hero shows a three-stage operating cadence—evidence, human decision and governed execution—and route transitions communicate forward/backward direction. Reduced-motion users receive the same structure and cadence without animation.


## Role operations board

`C3-TEAM-004` converts the team map from an organizational directory into a bounded operating system for campaign follow-up. Every work item can now record:

- work type: task, deliverable, recurring check-in or decision preparation;
- priority and explicit human-reported health;
- planned, active, blocked or complete state;
- target date, cadence and concrete next action;
- blocker and human check-in note;
- expected evidence or receipts;
- exact RACI assignments to functions inside the same workspace.

The interface puts an operating pulse and the work board before the role directory. Users can filter by function or state, inspect attention items, open evidence and RACI details, and record a governed check-in. Role cards remain available as compact dossiers and display their work count plus attention count instead of forcing every job description open at once.

Planning and execution remain distinct. A new item starts as `PLANNED` and may reference a vacant organizational function. Moving it to `ACTIVE`, `BLOCKED` or `COMPLETE` requires every accountable and responsible function to be `FILLED`; this prevents the system from representing work as underway without an authorized human owner. Blocked work requires a blocker plus at-risk/off-track health, and every status/health update requires a human check-in note.

The board does not calculate personal productivity, rank staff, infer performance or create authority. Health is an explicit human report about the work item. All writes reuse the exact-authorized, optimistic-concurrency team-workspace update, preserving tenant scope, idempotency, audit, internal outbox evidence and `external_effects=NONE`.

## Organic team intake and command-view deck

`C3-FRONT-008` replaces the free-form current-team textarea in guided intake with localized function presets, a bounded custom entry and removable chips. The UI still serializes the existing newline-separated `current_team` contract, so no backend migration or silent data rewrite occurs. Selecting a function describes current capacity and never creates identity, membership, permission or authority.

The team chapter now presents **Operations board** and **Create follow-up** as two mutually exclusive views of one operating system. Existing work opens the board first; an empty workspace opens creation first. The role directory remains available after the operating layer.

The current implementation is explicitly a **command view** backed by the existing exact team-workspace grants. Personal views are not produced by filtering browser data. A future backend increment must project `MY_WORK`, `TEAM_SHARED` and `COMMAND` from authenticated principal assignments and exact scoped grants before CampaignOS can claim per-user work visibility.
