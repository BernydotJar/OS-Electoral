# Organic campaign flow and command-safe workspace decks

## Product problem

Human review showed that CampaignOS had strong individual capabilities but still asked the operator to understand the application structure. The guided route, candidate evidence, team work creation, operating board and role directory competed vertically inside long pages. Returning users also received a hero that occupied too much of the viewport before the operational surface.

## Interaction model

CampaignOS now uses a progressive campaign flow:

1. **Ruta de inicio** appears first in navigation when the exact guided-intake read grant exists.
2. The recurring mission hero is compact and points directly to the active chapter.
3. Candidate work opens on **What to do now**, with separate **Profile and risks** and **Sources and evidence** views.
4. Team operations uses two mutually exclusive layers: **Operations board** and **Create follow-up**.
5. The role directory remains available below the operating layer instead of dominating it.

The tabs use native buttons, `tablist`, `tab`, `tabpanel`, `aria-selected`, stable controls and visible focus. Only one panel is visible at a time. Mobile converts pill navigation into full-width stacked controls. Reduced motion removes transitions without removing hierarchy.

## Team intake

The foundation intake stores `current_team` through its existing newline-separated contract, but the user no longer edits a technical textarea. The interface offers localized function presets, a bounded function/coordination entry and removable chips. The hidden canonical field is derived from the selected chips.

Selecting a function describes current organizational capacity only. It does not create a principal, membership, title, permission, capacity allocation or authority.

## Candidate action brief

The candidate chapter separates three concerns:

- **Actions:** deterministic work prepared from the current next action, evidence gaps, open contradictions, critical/high risks, active development goals and pending approvals.
- **Profile and risks:** the candidate record, internal status and bounded review data.
- **Sources and evidence:** the exact-authorized evidence editor and source register.

Action insights are deterministic projections of persisted state. They do not infer ideology, electability, voter preference or persuasion opportunities. They prepare human review and preserve `public_use_status=BLOCKED` and `external_effects=NONE`.

## Visibility policy

This increment exposes a **command view** only when the existing team workspace read/update grants allow it. It does not implement personal visibility by filtering browser data.

The target visibility model for a later backend increment is:

- `MY_WORK`: work assigned to functions occupied by the authenticated principal;
- `TEAM_SHARED`: work deliberately marked for cross-functional coordination;
- `COMMAND`: complete campaign operations for principals with exact command grants.

That later capability must project data server-side. Role labels, UI selections and job titles must never grant visibility. Until governed principal assignments and scoped grants exist, the UI states that individual views are unavailable rather than pretending to enforce them.

## Taste controls

```yaml
design_variance: 7
motion_intensity: 5
visual_density: 5
```

The stacked-card treatment communicates that creation and monitoring are two views of the same operational system. Motion is limited to opacity and transform and is not required to understand state.
