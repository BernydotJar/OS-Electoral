# Electoral Geography Data Quality — 2023

Program: `C1-ELEC-2023-001`  
Review date: 2026-07-14  
Status: `PARTIAL_OFFICIAL_MUNICIPAL_SUMMARY_INGESTED`

## Current state

The repository now contains an authenticated official 2023 municipality-level JRV summary for Antigua Guatemala. It confirms the municipality code, registered electorate, JRV count, JRV range, and voting-center count.

The repository still does not contain an authenticated official polling-center, voting-table, district, zone, locality, or community crosswalk for Antigua Guatemala.

The accompanying inventory CSV therefore contains one municipality-level summary row and no inferred center, JRV-to-center, or community-crosswalk rows.

## Ingested official summary

| Field | Value |
|---|---:|
| Registered electorate | 39,099 |
| JRV count | 100 |
| JRV range initial | 5,337 |
| JRV range final | 5,436 |
| Voting-center count | 18 |

The official summary source is recorded as `ELEC23-GEO-SRC-001`.

## Crosswalk policy

A geography row may be classified as `CONFIRMED` only when an official source supplies the unit identifier and relationship.

Name similarity is insufficient. For example, a polling-center label resembling a community name does not establish that the center represents the entire community or that its voting tables can be assigned to that community.

Allowed crosswalk statuses:

- `CONFIRMED`: explicit official relationship.
- `PARTIAL`: official unit exists, but parent or locality relationship is incomplete.
- `UNRESOLVED`: name or location appears relevant, but no explicit source-backed relationship exists.
- `CONFLICT`: official sources disagree or use incompatible identifiers.

## Required quality checks

Before analytical use, verify:

1. election year and election type;
2. department and municipality;
3. stable unit identifiers;
4. polling-center name and official location;
5. voting-table identifiers and scope;
6. parent-child relationships;
7. duplicates and renamed units;
8. privacy-safe treatment of addresses;
9. compatibility with territorial units used in EV-0105 or official municipal records.

## Prohibited use

The geography inventory must not be used to:

- infer community support;
- estimate persuasion opportunity;
- rank localities;
- assign individual voters;
- plan mobilization;
- create paid-media geofences.

## Next action

Authenticate and ingest the official 2023 center-level electoral-geography record from the Tribunal Supremo Electoral. Until then, every community or polling-center crosswalk remains unresolved.
