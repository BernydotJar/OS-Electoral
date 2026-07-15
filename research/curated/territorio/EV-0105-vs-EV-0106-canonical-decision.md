# EV-0105 vs EV-0106 Canonical Workbook Decision

Program: `C1-TERR-DQ-001`  
Review date: 2026-07-14  
Decision: `NO_DECISION`  
Status: `BLOCKED_PENDING_EV-0106_EXTRACTION`

## Current evidence

EV-0105 has a validated pilot extraction and a curated seven-community inventory.

EV-0106 is registered as an alternate or duplicate candidate, but its original workbook and cell-level extraction are not present on the current remote implementation branch.

A canonical decision cannot be made from filenames, directory placement, or assumptions about recency.

## Evidence required

Before changing this decision, extract EV-0106 and compare:

- source and workbook hashes;
- workbook metadata;
- sheet names and order;
- used dimensions;
- headers;
- formulas and cached values;
- blank rates;
- populated row counts;
- community names and variants;
- field-level values;
- duplicate and missing rows;
- creation and modification metadata when available and reliable.

## Allowed decisions

- `EV-0105_CANONICAL`
- `EV-0106_CANONICAL`
- `MERGE_REQUIRED`
- `NO_DECISION`

## Safe-field policy

| Field class | Current treatment |
|---|---|
| `SOURCE_FACT_CANDIDATE` | May enter curated evidence only with provenance and verification |
| `CAMPAIGN_ESTIMATE` | Retain as campaign research; never substitute for official electoral data |
| `CAMPAIGN_PRIORITY_LABEL` | Exclude from territorial ranking and decision evidence |
| `UNVERIFIED_TEXT` | Retain only with explicit verification status |
| `EXCLUDE_FROM_CURATED` | Do not publish in the curated analytical layer |

The EV-0105 fields `Empadronados Est. (2023)`, `Nivel de Acceso`, and `Prioridad Estratégica` remain campaign-research fields. They are not official TSE values and do not authorize targeting or prioritization.

## Impact on current curated inventory

The existing EV-0105 community inventory remains usable only as a provisional campaign-research inventory with its current limitations.

It must not be declared canonical until EV-0106 is extracted and compared.

## Next action

Locate EV-0106 under `POLITICS_ROOT`, run the existing workbook extraction model, generate its manifest and sheet CSVs, and then produce the structural and value-difference artifacts required by the spec.