# C3-FRONT-011 — Design

## Candidate information architecture

`CandidateWorkspaceDeck` becomes a single-profile surface. The profile body contains:

1. profile and risk sections as the first visible content;
2. a compact “Siguiente paso” panel derived from the existing action brief;
3. an evidence disclosure containing the existing source register and editor.

No capability is removed. The top-level three-tab deck is removed because it implies three independent jobs when the intended flow is one evidence-backed profile.

## Chapter orientation

Introduce one reusable `ChapterOrientation` component rendered on every chapter route after compact chrome and before chapter content. It displays:

- `Capítulo n de 5`;
- plain-language chapter title;
- status label;
- why this chapter matters;
- the next human action.

It reuses `CampaignJourneyPhase` state and dictionary copy. It does not unlock unavailable chapters.

## Governed new candidacy

Extend the existing campaign-context form with a collapsed “Nueva candidatura” form.

- capability is derived from exact grant:
  - action `create`;
  - resource type `campaign_collection`;
  - resource ID = tenant ID;
  - purpose `Create tenant campaign`;
  - no campaign/workspace scope.
- same-origin UI route forwards to the existing backend create endpoint;
- the server-rendered form carries one UUID-backed idempotency key;
- the route validates and reuses that submitted key so browser retries resolve to the same backend operation;
- the draft slug is deterministically derived from normalized display name plus a 12-hex key suffix;
- backend remains authoritative for authorization, collision handling and durable idempotency;
- successful creation returns to overview with a calm `campaign_created` notice;
- no campaign cookie is changed automatically;
- an authorized tenant with no visible campaigns can still create its first internal draft.

## Compact governance metadata

Team training, access recommendations and read metadata are grouped in a closed `<details>` element. Summary copy is short and non-technical. Full receipt/timestamp remains available for audit.

## Safety

- transcript-derived evaluation is a usability lens, not an endorsement of person-level voter tracking;
- no new personal-data field;
- no automatic campaign selection after creation;
- no permission inferred from role labels;
- no external effect.
