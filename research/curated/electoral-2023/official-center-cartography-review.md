# Official Center Cartography Review — C1-ELEC-2023-003

Program: `C1-ELEC-2023-003`  
Review date: 2026-07-15  
Status: `PARTIAL_CARTOGRAPHY_CAPTURE / CENTER_RECORDS_RECONCILED`

## Sources

- `ELEC23-GEO-SRC-002`: official TSE Antigua Guatemala cartography image. The previously registered URL and SHA-256 remain the authenticated source record.
- `ELEC23-GEO-SRC-003`: official TSE *Listado de Circunscripciones Electorales Municipales*, visually reviewed at PDF pageno 14.
- `ELEC23-GEO-SRC-004`: official TSE *Centros de Votación 2023 por Agrupación — primera vuelta*, relevant PDF pagenos 278–286.

## Cartography acquisition and OCR result

The official image identity was re-authenticated through the TSE gallery and directory index. This runtime could not reacquire the image bytes because direct binary download returned a DNS/cache failure. Therefore:

- no OCR output from `ELEC23-GEO-SRC-002` was accepted;
- no map label was silently normalized;
- no map label was converted automatically into a voting-center row;
- the prior registered source hash remains unchanged rather than being recomputed or guessed.

The controlled OCR workstream remains reproducible when the image is available under `POLITICS_ROOT`.

## Visual label review

The official CEM PDF was visually reviewed. It confirms four Antigua Guatemala CEM community labels:

1. San Pedro Las Huertas — Aldea;
2. San Juan del Obispo — Aldea;
3. San Mateo Milpas Altas — Aldea;
4. San Felipe de Jesús — Aldea.

These labels are electoral-community/CEM identities. They are not voting centers.

## Stronger center-level source

During the same loop, the official first-round center-by-grouping PDF was authenticated. It provides explicit center codes, establishment names, institutional locations, JRV ranges, JRV counts, registered electorate, grouping codes, and community/CEM labels.

This source supports:

- `18` unique voting-center identities;
- `19` explicit assignment records because center `7` appears in two grouping/range records;
- `100` JRV covering the inclusive municipal range `5,337–5,436` without gaps or overlaps;
- `39,099` registered electorate across the explicit assignment rows.

## OCR and review discipline

OCR remained assistive-only. No OCR text was accepted without visual review. Center rows were not produced from cartography OCR; they were transcribed from the extractable official center PDF with page/group provenance. The four CEM labels were visually confirmed from the official CEM PDF.

## Decisions

- Cartography OCR outcome: `PARTIAL_SOURCE_BYTES_UNAVAILABLE_IN_RUNTIME`.
- Center capture outcome: `RECONCILED_18_CONFIRMED_CENTERS`.
- JRV assignment outcome: `RECONCILED_100_JRV_ASSIGNED`.
- Community/CEM relationships: confirmed only where the official center record prints the relationship.
- No relationship is inferred from name similarity or proximity.
- Political gates remain closed.
