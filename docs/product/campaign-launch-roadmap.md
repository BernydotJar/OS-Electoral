# Campaign launch roadmap

Status: implemented local slice; production remains blocked.

## Product intent

CampaignOS should behave as a campaign operating system, not as a generic dashboard. A candidate or representative who is not technically sophisticated must be able to answer four questions within five seconds:

1. Where is the campaign now?
2. What is the next safe action?
3. Why does that action matter?
4. What becomes available after it is completed?

The launch roadmap converts persisted campaign state into a progressive route. It never invents completion, permission, strategy approval, publication authority, citizen contact, spending authority, mobilization authority, or production readiness.

## Primary users

- candidate beginning or professionalizing a campaign;
- authorized representative helping the candidate;
- campaign director coordinating research, team, strategy, and operations;
- non-technical operator who needs plain Spanish and explicit next steps.

## Five-stage path

### 1. Aterrizar la campaña

Capture office, jurisdiction, candidacy purpose, current team, assets, budget evidence, known questions, and required evidence.

Completion gate: guided intake reaches `READY_FOR_RESEARCH`.

### 2. Conocer la candidatura y el territorio

Organize candidacy evidence, electoral roll and historical-result research, public-source data, community profiles, open questions, and traceable citations.

Completion gate: candidate workspace reaches `INTERNALLY_APPROVED`.

Public electoral data may inform the campaign only when provenance, jurisdiction, collection date, uncertainty, and allowed use are recorded. The roadmap does not itself scrape, import, or approve any external source.

### 3. Organizar el equipo

Make coordinations, departments, owners, vacancies, capability, and training needs visible.

Completion gate: team workspace reaches `READY_FOR_HUMAN_REVIEW`.

### 4. Decidir la estrategia

Support a human decision process using SWOT/FODA, objectives, hypotheses, evidence, and an explicit balance among field, communications, digital, and organizational work.

Completion gate: strategy workspace reaches `DECIDED_INTERNAL`.

### 5. Operar y aprender cada día

Track campaign goals, communities, owners, tasks, blockers, decisions, and War Room learning.

Completion gate: campaign roadmap reaches `COMPLETE`. This still does not grant release or production authority.

## State semantics

- `COMPLETE`: the exact persisted gate for the phase passed.
- `ACTIVE`: work exists and is still incomplete.
- `AVAILABLE`: the preceding gate passed and the module is actionable.
- `BLOCKED`: the phase is next, but access, configuration, or an implemented workflow is absent.
- `LOCKED`: an earlier phase remains incomplete.

Later persisted data never allows the route to skip an incomplete earlier gate.

## Content rules

- Show human language, never raw reason codes or internal enum names in the primary experience.
- Explain outcomes and consequences rather than implementation details.
- Use Spanish as a first-class language and preserve complete English parity.
- Distinguish guidance from authority.
- Do not present unfinished modules as clickable actions.
- Keep audit identifiers in dedicated evidence surfaces, not in the task explanation.

## Taste controls

- `design_variance: 7/10` — asymmetric campaign narrative and a strong route hierarchy rather than a symmetric card grid.
- `motion_intensity: 6/10` — a restrained first-use atmosphere, one mission entrance, short hover confirmation and substantially reduced motion when requested.
- `visual_density: 5/10` — one dominant route surface, concise phase summaries, and detailed forms only when the user enters the active phase.

The visual direction should communicate consequence, discipline, and ambition without becoming theatrical noise.

## Motion contract

The roadmap uses shared duration, easing, and distance tokens. Motion is limited to opacity and transform, never blocks interaction, preserves focus, and is removed or substantially reduced under `prefers-reduced-motion: reduce`.

## Accessibility contract

- semantic `section`, heading hierarchy, and ordered phase list;
- keyboard-operable links and controls;
- visible focus;
- state labels that do not depend on color;
- mobile reflow without horizontal overflow;
- accessible form labels, help text, and placeholders;
- WCAG 2.2 AA automated review with axe;
- reduced-motion verification.

## Human review protocol

A reviewer should complete the following without reading source code:

1. State the current phase and next action after five seconds on the page.
2. Explain why the next action matters and what it unlocks.
3. Confirm that no visible primary copy contains internal codes or unexplained English.
4. Complete the form without asking what each field means.
5. Save, reload, and confirm persistence.
6. Switch languages and confirm equivalent meaning.
7. Navigate with keyboard only and observe visible focus.
8. Test mobile reflow and reduced motion.
9. Confirm that blocked phases explain the missing access or configuration instead of pretending to work.
10. Confirm that no copy claims strategy approval, public authority, citizen contact, spending, mobilization, deployment, or production readiness.

## Current operability and deferred product work

The foundation and the first candidate-evidence operation are now usable: a live authorized user can complete guided intake, create a candidate dossier and register traceable sources. The full welcome appears only before work starts; returning users receive the current mission instead.

Claim editing and approval, team design, strategy decisions, territorial data ingestion, community profiles, vote-goal tracking and Daily War Room mutations remain separate API-backed increments with exact authorization, provenance, privacy, legal, accessibility and human-review gates.
