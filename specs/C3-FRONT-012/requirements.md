# C3-FRONT-012 Requirements

## Summary

Clarify the campaign journey so a first-time user sees one ordered path instead of duplicated preparation concepts and specialist terminology.

## User finding

The user observed that:

- “Preparación inicial” appeared after candidacy and team in the lateral menu even though it is chapter 1;
- “Preparación” and “Preparación inicial” represented the same mental stage in two different locations;
- the candidate header mixed summary, progress and next action with the actual profile workspace;
- “Workspace ejecutivo” is specialist jargon and does not explain the decision being made.

## Mode

SHIP.

## Acceptance criteria

- [x] The visible sidebar order is Resumen, Preparación inicial, Candidatura, Equipo, Estrategia, War Room and Campañas when all exact grants exist.
- [x] “Preparación” is not a separate sidebar entry.
- [x] The “Base operativa / Preparación operativa” card is rendered inside chapter 1 before guided intake.
- [x] The overview contains a “Resumen de candidatura” with progress and “Qué hacer ahora”.
- [x] The candidacy chapter has “Perfil y riesgos” as its only primary heading.
- [x] Candidate next-action cards are absent from the candidacy chapter and remain available in the overview.
- [x] Sources and evidence remain a subordinate disclosure under the profile.
- [x] Spanish and English preserve equivalent meaning using plain language.
- [x] Exact-grant navigation, route isolation and tenant/campaign authorization remain unchanged.
- [x] Desktop, mobile, keyboard, reduced motion, zero overflow and WCAG 2.2 AA browser gates pass.

## Terminology decision

“Workspace ejecutivo de candidatura” is rejected because:

1. “workspace” describes software architecture rather than a user task;
2. “ejecutivo” suggests a management dashboard but the section contains evidence review;
3. the phrase competes with the chapter title and the profile title;
4. it does not tell a candidate or consultant whether they should review progress, evidence or risk.

The overview therefore uses **Resumen de candidatura**. The chapter uses **Perfil y riesgos**.

## Non-goals

- no authorization changes;
- no new campaign data or mutation;
- no voter profiling, targeting, publication, contact, spending or mobilization;
- no production deployment or cloud resource;
- no dependency or lockfile change.
