# Campaign launch roadmap

Status: active localized QA repair; production remains blocked.

## Product intent

CampaignOS behaves as a campaign operating system, not a generic dashboard or marketing landing page. A candidate, representative or campaign director should answer four questions within five seconds:

1. Where is the campaign now?
2. What is the next safe action?
3. What result should that action produce?
4. What remains blocked?

The roadmap converts persisted campaign state into a progressive route. It never invents completion, permission, strategy approval, publication authority, citizen contact, spending authority, mobilization authority, deployment or production readiness.

## Command overview

The locale root renders one restrained command surface. It replaces the former combination of a cinematic active-mission hero plus a second campaign-path section.

The command surface contains:

- the campaign path as the single page heading;
- exact persisted progress and current stage;
- one current-decision card with status, expected outcome and primary action;
- compact stage shortcuts;
- a closed-by-default, keyboard-operable disclosure for the complete five-stage path;
- explicit human-authority and external-effect boundaries.

The visual direction is institutional and operational: strong typography, controlled density, low-noise depth and no third-party or generated campaign media. The interface should feel credible to municipal and national leadership without becoming theatrical or implying authority that does not exist.

## Five-stage path

### 1. Aterrizar la campaña

Capture office, jurisdiction, candidacy purpose, current team, assets, budget evidence, known questions and required evidence.

Completion gate: guided intake reaches `READY_FOR_RESEARCH`.

### 2. Conocer la candidatura y el territorio

Organize candidate evidence, electoral research, public-source data, community profiles, open questions and traceable citations.

Completion gate: candidate workspace reaches `INTERNALLY_APPROVED`.

Public electoral data may inform the campaign only when provenance, jurisdiction, collection date, uncertainty and allowed use are recorded. The roadmap does not scrape, import or approve an external source.

### 3. Organizar el equipo

Make coordinations, departments, owners, vacancies, capability and training needs visible.

Completion gate: team workspace reaches `READY_FOR_HUMAN_REVIEW`.

### 4. Decidir la estrategia

Support a human decision using SWOT/FODA, objectives, hypotheses, evidence and an explicit balance among field, communications, digital and organizational work.

Completion gate: strategy workspace reaches `DECIDED_INTERNAL`.

### 5. Operar y aprender cada día

Track goals, communities, owners, tasks, blockers, decisions and War Room learning.

Completion gate: campaign roadmap reaches `COMPLETE`. This still grants no release or production authority.

## State semantics

- `COMPLETE`: the exact persisted gate passed.
- `ACTIVE`: work exists and remains incomplete.
- `AVAILABLE`: the preceding gate passed and the module is actionable.
- `BLOCKED`: the phase is next, but exact access, configuration or workflow is absent.
- `LOCKED`: an earlier phase remains incomplete.

Later persisted data never allows the route to skip an incomplete earlier gate. Locked and blocked stages render status and corrective explanation, not a misleading action.

## Chapter behavior

Each chapter has a stable route:

```text
/{locale}/campaign/foundation
/{locale}/campaign/evidence
/{locale}/campaign/team
/{locale}/campaign/strategy
/{locale}/campaign/operations
```

A chapter route renders a compact command bar followed immediately by exactly one workspace. The command bar provides overview, current chapter, previous/next and a disclosed full campaign map. The full map does not occupy the initial task viewport.

Browser history, locale switching, form redirects, query parameters and workspace anchors preserve chapter context. A valid but locked chapter request fails closed to the current available mission; an invalid slug returns `404`.

## Local functional diagnostics

`make functional-dev` may assign unique loopback ports when configured ports are occupied. It prints distinct URLs for:

- Spanish and English frontend;
- same-origin browser readiness;
- backend API base;
- backend readiness;
- Mailpit UI.

The frontend path `/api/v1/ready` is a sanitized no-store proxy to the configured backend readiness route. It exists so a user checking the frontend port receives readiness JSON rather than a frontend 404. Raw connection errors, credentials and tenant information are never returned.

## Accessibility and motion

- semantic section and ordered-path structure;
- named progress element;
- exactly one current step;
- keyboard-operable disclosures and links;
- visible focus and state labels independent of color;
- mobile reflow without page overflow;
- ES/EN parity;
- WCAG 2.2 AA automated axe review;
- route motion limited to direction and continuity;
- `prefers-reduced-motion: reduce` removes non-essential movement.

No animation blocks interaction, changes authorization, moves focus or alters persisted state.

## Human review protocol

A reviewer should be able to:

1. identify the current stage, status and expected outcome within five seconds;
2. open the current workspace with one primary action;
3. expand and collapse the complete path using only the keyboard;
4. open a chapter and see its workspace immediately after the compact command bar;
5. navigate previous/next, browser back/forward and locale changes without losing context;
6. distinguish locked and blocked stages without relying on color;
7. verify the same-origin and backend readiness URLs printed by the functional launcher;
8. confirm there is no active-mission hero, external media request or marketing-style duplicate introduction;
9. confirm no copy claims strategy, publication, contact, spending, mobilization, deployment or production authority.

## Current operability and deferred work

Guided intake, candidate dossier creation, source registration, team structure creation, template application, vacant-function documentation and role-bound planning are usable in the local exact-authorized journey.

Candidate claim editing and reviewer disposition, personnel identity assignment, personal work projections, jurisdiction-specific compliance, territorial ingestion, production identity, managed environments and production acceptance remain separate gated increments.
