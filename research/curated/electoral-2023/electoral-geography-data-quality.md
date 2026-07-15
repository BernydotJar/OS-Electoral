# Electoral Geography Data Quality — 2023

Program: `C1-ELEC-2023-001`  
Review date: 2026-07-14  
Status: `BLOCKED_PENDING_OFFICIAL_GEOGRAPHY_SOURCE`

## Current state

The repository does not yet contain an authenticated official 2023 polling-center, voting-table, district, zone, locality, or community crosswalk for Antigua Guatemala.

The accompanying inventory CSV therefore contains only the required schema and no inferred rows.

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

Authenticate and ingest the official 2023 electoral-geography record from the Tribunal Supremo Electoral. Until then, every community or polling-center crosswalk remains unresolved.