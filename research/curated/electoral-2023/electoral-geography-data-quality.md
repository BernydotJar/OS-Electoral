# Electoral Geography Data Quality — 2023

Program: `C1-ELEC-2023-003`  
Review date: 2026-07-15  
Status: `RECONCILED_18_CONFIRMED_CENTERS / RECONCILED_100_JRV_ASSIGNED`

## Accepted official baseline

| Field | Value |
|---|---:|
| Registered electorate | 39,099 |
| Unique voting centers | 18 |
| Explicit center-assignment records | 19 |
| JRV | 100 |
| JRV range | 5,337–5,436 |

## Why 18 centers produce 19 assignment rows

Center code `7`, **Escuela Oficial Urbana de Niñas Pedro de Betancourt**, appears in two explicit official records:

- grouping `002`: JRV `5,380–5,381`;
- grouping `999`: JRV `5,431–5,433`.

The inventory deduplicates the center identity. The assignment dataset preserves both official ranges. This is not a duplicate-data error.

## Coverage checks

- 18 unique center codes: PASS.
- 19 official assignment records: PASS.
- Inclusive JRV arithmetic per record: PASS.
- Total JRV count = 100: PASS.
- Range coverage 5,337–5,436: PASS, no gaps or overlaps.
- Registered electorate total = 39,099: PASS.
- Official center count conflict with dashboard `19`: resolved in favor of official TSE count `18`.

## Cartography limitation

The official cartography source remains authenticated, but its binary could not be reacquired in this runtime for a new OCR pass. No cartography OCR output was promoted. Four CEM labels were visually confirmed through a separate official TSE CEM PDF, and center identities were resolved through the official first-round center-by-grouping PDF.

## Crosswalk quality

Confirmed relationships are limited to those printed by TSE:

- voting center → electoral grouping;
- electoral grouping → Cabecera Municipal or named CEM.

No relationship to EV-0105 campaign communities, neighborhoods, zones, voter support, field responsibility, or mobilization is created.

## Privacy

Institutional polling-place locations are public official electoral geography. No individual voter address, DPI, CUI, phone, email, or voter-level assignment is stored.

## Political safety

The datasets must not be used to infer support, rank communities, target voters, create geofences, or plan mobilization. All political activation gates remain closed.
