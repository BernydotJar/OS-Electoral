# C3-FRONT-012 Design

## Information architecture

### Overview

The overview answers “where is the campaign now?” It owns cross-chapter summaries:

- campaign journey and current chapter;
- campaign context;
- candidate progress;
- what the team should do next;
- authority and evidence boundaries.

### Chapter 1 — Preparación inicial

The chapter owns both layers of preparation:

1. the minimal operational base (campaign name, territory, stage and active workspace);
2. the guided intake (office, project, team, assets, budget evidence and unknowns).

The operational base is not a separate product destination.

### Chapter 2 — Candidatura

The chapter answers “what is confirmed, contradictory, underdeveloped or risky?” It contains:

- one visible heading: Perfil y riesgos;
- status and evidence checks;
- identity, biography, purpose, values, attributes, contradictions, development and reputation risk;
- a subordinate sources/evidence disclosure.

It does not repeat progress or the next-action dashboard already present in Resumen.

## Components

- `CampaignReadinessPanel`: moves readiness into preparation without changing its contract.
- `CandidateOverviewPanel`: owns candidate progress and next-action summary.
- `CandidateWorkspaceDeck`: renders profile plus subordinate evidence only.
- `deriveNavigation`: orders the visible campaign journey and removes duplicated readiness navigation.

## Safety

Navigation remains a projection of exact server-owned grants. Moving or relabeling a link creates no authority. Candidate progress and next actions remain internal and create no external effect.

## Verification

- focused component/navigation/i18n tests;
- ESLint and strict TypeScript;
- production build;
- dynamic Chromium review in ES/EN, desktop/mobile, keyboard and reduced motion;
- axe WCAG 2.2 AA and overflow checks;
- complete repository gate;
- exact-head hosted CI and review evidence.
