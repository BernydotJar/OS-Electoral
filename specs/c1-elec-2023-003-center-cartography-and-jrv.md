# Spec: C1-ELEC-2023-003 — Center Cartography and JRV Resolution

Status: Draft  
Owner: Electoral Research  
Reviewers: Tracking, Risks, and Learning; Territory and Mobilization (research only)  
Parent: `C1-ELEC-2023-002`

## Purpose

Extend the authenticated 2023 Antigua Guatemala municipal electoral-geography summary into a controlled center-level inventory by reviewing official TSE cartography and any authoritative center/JRV records that can be authenticated.

This spec does not authorize territorial ranking, targeting, mobilization, narrative, paid media, public promises, or individual-voter records.

## Accepted Baseline

- Official registered electorate: `39,099`.
- Official JRV count: `100`.
- Official JRV range: `5,337–5,436`.
- Official voting-center count: `18`.
- Official cartography image: `ELEC23-GEO-SRC-002`.
- Dashboard value `centros=19` is rejected as official evidence and remains `DERIVED_DISCOVERY_AID_ONLY`.
- Center names, addresses, JRV-to-center assignments, and community/CEM crosswalks remain unresolved.

## Workstreams

### A. Controlled Cartography Capture

1. Acquire the official cartography image from its authenticated URL or portable local path.
2. Record SHA-256, dimensions, capture date, authority, and source URL.
3. Preserve the original image unchanged.
4. Produce high-resolution review derivatives only under a temporary workspace.
5. Run OCR as assistive evidence only.
6. Visually review every accepted label.
7. Record illegible or ambiguous labels as `UNRESOLVED`.

### B. Center-Level Inventory

Create one row per official center only when the source visibly supports the center identity.

Required columns:

```text
evidence_id,election_year,department,municipality,center_code,center_name,address_or_location,source_id,source_region_or_label,verification_status,limitations
```

Allowed verification statuses:

- `CONFIRMED_FROM_OFFICIAL_CARTOGRAPHY`
- `PARTIAL_LABEL_ONLY`
- `UNRESOLVED`
- `CONFLICT`

Do not create 18 synthetic center rows merely to match the official count.

### C. JRV-to-Center Assignment

Create assignments only from an official record explicitly connecting JRV identifiers or ranges to a center.

Required columns:

```text
evidence_id,center_code,center_name,jrv_initial,jrv_final,jrv_count,source_id,verification_status,limitations
```

The municipality-level range `5,337–5,436` does not by itself establish center-level allocation.

### D. Crosswalk Control

Community, CEM, village, barrio, zone, or territorial-unit crosswalks may be created only when an authoritative source explicitly supports the relationship.

Name similarity, map proximity, campaign knowledge, dashboard labels, or intuitive matching are insufficient.

## Required Artifacts

```text
research/curated/electoral-2023/
├── official-center-cartography-review.md
├── official-center-labels-2023.csv
├── official-center-inventory-2023.csv
├── official-jrv-center-assignment-2023.csv
├── electoral-geography-crosswalk.csv
├── electoral-geography-data-quality.md
└── C1-ELEC-2023-003-implementation-report.md

research/electoral-2023/
├── electoral-geography-source-audit.csv
└── source-acquisition-log.md
```

## Functional Requirements

### FR-01 Source Authentication

Every accepted center label must cite an authenticated official source, stable URL or portable path, source hash, and visible map region or official record location.

### FR-02 Controlled Transcription

For each visible label, record:

```text
record_key,raw_ocr_text,reviewed_text,label_type,source_region,change_type,verification_status,review_note
```

Allowed change types:

- `CONFIRMED`
- `CORRECTED`
- `UNRESOLVED`
- `NOT_PRESENT`

### FR-03 Count Reconciliation

The center inventory may be evaluated against the official count of `18`, but the agent must not fabricate missing rows.

Allowed outcomes:

- `RECONCILED_18_CONFIRMED_CENTERS`
- `PARTIAL_CENTER_CAPTURE`
- `COUNT_CONFLICT`
- `NOT_RECONCILED`

### FR-04 JRV Arithmetic

For any explicit inclusive range:

```text
jrv_count = jrv_final - jrv_initial + 1
```

Every center-level range must have an official source. The municipal range may only be used as a total-level consistency check.

### FR-05 Source Conflict

When official and derived sources disagree, official evidence controls. Preserve the conflicting derived value in the audit; do not silently delete it.

## Acceptance Criteria

1. The official source image is authenticated and hashed.
2. OCR is never accepted without visual review.
3. No center row is invented to reach 18.
4. Every accepted center row has source-region provenance.
5. Center count reconciliation is explicit.
6. No JRV-to-center allocation is inferred.
7. No community/CEM crosswalk is inferred by name or proximity.
8. Dashboard values remain discovery aids only.
9. No individual voter data or personal absolute paths are committed.
10. Political gates remain closed.

## Validation

At minimum:

- CSV schemas parse successfully;
- verification and change statuses use allowed enums;
- duplicate center identities are reported;
- confirmed center count does not exceed 18 without a documented official conflict;
- center-level JRV ranges reconcile arithmetically when present;
- no `/Users/` paths are added;
- `git diff --check` passes;
- existing official municipality summary remains unchanged.

## Stop Conditions

Stop and document a blocker when:

- the official image cannot be acquired or authenticated;
- a label remains illegible after controlled review;
- the cartography labels areas but not voting centers;
- center names are visible but addresses or codes are absent;
- no official source assigns JRV to centers;
- completing a row would require name-only or proximity inference.

A blocker affects only its workstream. Continue any independent workstream that remains executable.

## Definition of Done

The loop is complete when the cartography review is documented, every accepted label has provenance, center inventory and count reconciliation are complete or explicitly partial, JRV assignments and crosswalks are populated only where authoritative evidence exists, all remaining blockers are exact, validation passes, and political gates remain closed.
