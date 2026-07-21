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
design_variance: 4
motion_intensity: 2
visual_density: 8
```

The current dynamic shell is bilingual, responsive and read-only. It presents an ordered organizational route rather than a generic people directory.

## Core invariants

- every active or blocked work item has exactly one `ACCOUNTABLE` role;
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

## Current limitation

The backend supports exact-authorized create, read and update. The current shell displays a verified read-only projection. Authenticated editing, personnel invitation workflows, dedicated approvers and human user-acceptance testing remain future work.