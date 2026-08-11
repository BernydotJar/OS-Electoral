# FIRMES -> CampaignOS integration discovery

Status: `DISCOVERY_COMPLETE_FOR_COORDINADOR_MUNICIPAL_SCOPE`

Date: 2026-08-11

## Sources and method

This discovery uses the public surface previously reviewed plus the user-provided **Manual de usuario FIRMES - Antigua Guatemala, version 1.0 (2026-08-08)**. The manual states that it was prepared from an authenticated, read-only review for a Coordinador Municipal account and that other roles may expose different capabilities.

No FIRMES credentials, cookies, access tokens, active invitation links, DPI values, phone numbers, email addresses, registrant answers, or person-level records are stored in this artifact.

## What FIRMES is the source of truth for

FIRMES should remain the operational source of truth for party/territorial structure and field execution:

- territorial scope, districts, municipalities and communities;
- campaign/operational appointments and the reporting chain;
- UOF, NAF and MAN organization and progress;
- NAF invitation-link lifecycle;
- event draft/publication/registration state;
- alliances and their Identification -> Listening -> Proposal lifecycle;
- billboard location, evidence and contract records;
- operational exports and sharing actions that originate in FIRMES.

The observed organizational chain is:

`Presidenciable -> Dirigencia Nacional -> Coordinador Distrital -> Coordinador Municipal -> Concejal -> UOF -> NAF -> MAN`

The observed UOF/NAF/MAN constants are configuration for the reviewed municipality, not universal product constants. CampaignOS must not hard-code them as global rules.

## What CampaignOS remains the source of truth for

CampaignOS should remain the source of truth for:

- campaign preparation and guided intake;
- candidate evidence/readiness workspace;
- functional campaign team/accountability and internal work items;
- governed Training Academy;
- evidence, hypotheses, options, risks and human strategy decisions;
- launch roadmap/readiness;
- internal Daily War Room / campaign operations review.

This separation avoids double entry. CampaignOS may reference field-operational facts from FIRMES, but it should not recreate FIRMES workflows.

## Source-of-truth contract

| FIRMES concept | CampaignOS treatment | Classification | Boundary |
| --- | --- | --- | --- |
| District / municipality / community IDs and labels | External territorial references | `REFERENCE` | Preserve FIRMES external IDs and source timestamp. |
| Planned vs assigned structure counts | Read-only aggregate context | `POSSIBLE_SYNC` | Counts/status only by default; no duplicated contact directory. |
| UOF / NAF / MAN plan, registered count and progress | Read-only aggregate context | `POSSIBLE_SYNC` | Aggregate only; no MAN identity or affiliation roster. |
| Configured ratios/targets | Versioned external configuration snapshot | `REFERENCE` | Never assume 100/4/25 is universal. |
| Padrón / prior election aggregates | Evidence input with provenance | `POSSIBLE_SYNC` | Aggregate territorial evidence only; never voter-level profiles or outreach scoring. |
| Demographic aggregates | Evidence input with provenance | `POSSIBLE_SYNC` | Descriptive aggregate context only; no automated targeting or persuasion selection. |
| Event metadata/status | Read-only operational reference | `POSSIBLE_SYNC` | Name/time/place/status/aggregate attendance only when authorized. |
| Event registrants, DPI, phone, answers, precise attendee location | Stay in FIRMES | `DO_NOT_BULK_IMPORT` | Person-level political/participation data does not enter CampaignOS baseline. |
| NAF invitation links / QR | Stay in FIRMES | `KEEP_EXTERNAL` | Never persist active invitation links in CampaignOS. |
| Alliances/person or group contacts and conversation notes | Stay in FIRMES | `KEEP_EXTERNAL` | At most coarse aggregate pipeline counts; no contact or relationship dossier sync. |
| Billboard records | Optional aggregate/reference | `POSSIBLE_SYNC` | CampaignOS may reference count/status/cost summary; photos/contracts remain FIRMES. |
| Appointment mutations, delegation, release/desassignment | Stay in FIRMES | `KEEP_EXTERNAL` | CampaignOS must not write organizational mutations to FIRMES. |
| Event publication, WhatsApp, QR, CSV sharing | Stay in FIRMES | `KEEP_EXTERNAL` | No external-effect proxy from CampaignOS. |

## Minimum safe integration shape

The first integration should be **read-only and one-way: FIRMES -> CampaignOS**.

Every imported aggregate/reference must carry:

- source system = `FIRMES`;
- external scope identifiers;
- source-observed timestamp;
- ingestion timestamp;
- staleness state;
- aggregate grain;
- provenance/contract version.

CampaignOS must fail closed when the source is unavailable or a payload exceeds the allow-list. It must not silently substitute stale values for current operational facts.

## Explicit non-goals

The integration does **not**:

- copy the FIRMES user directory;
- ingest MAN/affiliate identity rosters;
- ingest DPI, phone, email, event answers or active invitation links;
- publish events or share WhatsApp/QR/CSV;
- mutate appointments, alliances or billboard records;
- create voter profiles, persuasion scores or person-level targeting;
- convert territorial/demographic aggregates into automatic outreach recommendations;
- grant CampaignOS roles or permissions from a FIRMES role without a separate authorization decision.

## Product opportunities that do not duplicate FIRMES

CampaignOS can add value around FIRMES data without cloning FIRMES:

1. **External operations pulse** - a compact, timestamped read-only panel with territorial progress aggregates and explicit freshness.
2. **Evidence linkage** - attach an aggregate FIRMES snapshot as cited evidence to a roadmap risk, strategy assumption or War Room item.
3. **Staleness / contradiction checks** - flag when an internal CampaignOS assumption conflicts with the latest aggregate snapshot; do not auto-decide.
4. **Handoff links** - deep-link authorized operators back to the relevant FIRMES module instead of rebuilding the mutation screen.
5. **Source boundary labels** - make it obvious which facts are owned by FIRMES vs CampaignOS.

## Decision

Proceed to a governed `C3-FIRMES-001` specification for a read-only aggregate/reference adapter. Do not implement it until the spec receives explicit human approval in the Graph Harness.
