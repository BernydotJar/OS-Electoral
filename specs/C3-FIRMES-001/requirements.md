# C3-FIRMES-001 - Governed FIRMES reference integration requirements

State: `SPEC_READY_APPROVAL_PENDING`

## Goal

Allow CampaignOS to consume a bounded, read-only set of FIRMES territorial/operational aggregates and references without duplicating FIRMES workflows or importing person-level political/affiliation data.

## Functional requirements

1. CampaignOS SHALL treat FIRMES as an external source of truth for territorial organization and field-operation records.
2. The initial integration SHALL be one-way and read-only from FIRMES into CampaignOS.
3. The integration SHALL accept only an explicit allow-list of aggregate/reference fields: territorial identifiers/labels, structure planned/filled counts, UOF/NAF/MAN aggregate progress, versioned configuration values, source timestamps, bounded event metadata/aggregate counts, and bounded billboard summary fields.
4. Every accepted snapshot SHALL retain source, external scope identifiers, observed-at timestamp, ingested-at timestamp, grain, contract version and freshness state.
5. CampaignOS SHALL surface stale/unavailable state instead of presenting stale data as current.
6. CampaignOS SHALL provide handoff/deep-link references back to FIRMES for operational mutations rather than recreating those mutation workflows.
7. CampaignOS MAY cite an approved aggregate snapshot as evidence in internal strategy, roadmap or War Room records, but SHALL preserve human decision authority.

## Data prohibitions

The baseline integration SHALL NOT ingest or persist:

- DPI or other person-level identity numbers;
- phone numbers or email addresses from FIRMES;
- MAN/affiliate/member identity rosters;
- event registrant identity, answers or precise attendee location;
- active NAF invitation links, QR payloads or sharing tokens;
- alliance contact dossiers or conversation notes;
- person-level political affiliation/profiling fields.

## External-effect prohibitions

CampaignOS SHALL NOT use this integration to:

- create/update/release/desassign FIRMES appointments;
- create/publish/close/archive FIRMES events;
- send WhatsApp, QR, public links or CSV exports;
- mutate alliances or billboards;
- trigger spending, contact, mobilization or publication;
- create automated persuasion/targeting recommendations from territorial or demographic aggregates.

## Authorization and failure behavior

- Access remains tenant/campaign scoped and exact-authorized inside CampaignOS.
- A FIRMES role SHALL NOT automatically grant a CampaignOS permission.
- Unknown fields or a scope mismatch SHALL fail closed.
- Partial or malformed source responses SHALL not be projected as trusted evidence.
- No source credentials SHALL be exposed to the browser or persisted in logs/evidence artifacts.

## Acceptance criteria

- Strict contracts reject prohibited/unknown person-level fields.
- Aggregate snapshots preserve provenance and freshness.
- Source-unavailable and stale states are visible and fail closed.
- No write-capable FIRMES client exists in the baseline implementation.
- Unit/contract tests prove prohibited fields and external-effect operations cannot enter the adapter.
- Browser review proves source ownership and freshness are understandable in ES/EN and on mobile.
- Production remains `BLOCKED` and release remains `DENY_RELEASE` unless separately authorized.
