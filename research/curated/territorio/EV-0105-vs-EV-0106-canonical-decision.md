# EV-0105 vs EV-0106 Canonical Workbook Decision

Program: `C1-TERR-DQ-001`
Review date: 2026-07-14
Decision: `EV-0105_CANONICAL`
Status: `PASS_WITH_EQUIVALENT_EXTRACTED_CONTENT`

## Relationship Classification

EV-0105 and EV-0106 are package-distinct workbook files with equivalent extracted worksheet content for the reviewed sheet `Resumen Comparativo`.

The files do not have the same SHA-256 hash, so they are not byte-identical duplicates. However, the cell-level extraction found no differences across the compared headers, community names, values, formulas, blank flags, rows, or columns.

## Evidence Reviewed

| Artifact | Finding |
|---|---|
| `research/extracted/manifests/EV-0105.yaml` | EV-0105 hash: `sha256:e5bccbacfdae326d7924fb664848fc447e53f551067c8f7b9ef38a2858f6905b` |
| `research/extracted/manifests/EV-0106.yaml` | EV-0106 hash: `sha256:2a4c5a5cccf185829fa0bc30b7e0cb73b800879384b0403592bf42b4c50bbf98` |
| `research/curated/territorio/EV-0105-vs-EV-0106-structure.csv` | Sheet names, sheet count, row count, blank count, PII redactions, dimensions, headers, formula count, cell count, blank rate, community count, and community names match. |
| `research/curated/territorio/EV-0105-vs-EV-0106-differences.csv` | No cell-level value, formula, header, or blank-flag differences were found across the 40 extracted cells. |

## Canonical Recommendation

Use `EV-0105_CANONICAL` for the current curated territorial layer.

Basis:

- EV-0105 already passed the pilot extraction gate and has a curated seven-community inventory.
- EV-0106 adds no new extracted rows, columns, communities, formulas, or values.
- Keeping EV-0105 avoids unnecessary churn in the curated inventory while preserving EV-0106 as a package-distinct backup or alternate copy.

This recommendation does not promote EV-0105's campaign-research estimates into official electoral evidence.

## Unresolved Conflicts

No content conflicts were found in the extracted worksheet.

Remaining limitations:

- Only the available workbook content was compared.
- Neither workbook establishes methodology for estimated registered electorate, access labels, or strategic-priority labels.
- Neither workbook is an official TSE source.

## Safe-Field Policy

| Field | Field class | Current treatment |
|---|---|---|
| `Aldea/Barrio` | `SOURCE_FACT_CANDIDATE` | Retained as campaign-research community name with source-row provenance; not treated as a complete official geography. |
| `Población (INE 2018)` | `SOURCE_FACT_CANDIDATE` | Retained as workbook-labeled INE 2018 value; requires official census/geography cross-check before decision use. |
| `Empadronados Est. (2023)` | `CAMPAIGN_ESTIMATE` | Retained only as campaign research; never substitutes for official TSE electorate or turnout data. |
| `Nivel de Acceso` | `UNVERIFIED_TEXT` | May describe a workbook label only; not a mobilization or access decision. |
| `Prioridad Estratégica` | `CAMPAIGN_PRIORITY_LABEL` | Excluded from territorial ranking and decision evidence. |

## Impact on Current Curated Inventory

The existing EV-0105 community inventory remains the active curated campaign-research inventory.

No re-curation is required from EV-0106 because the compared worksheet content is equivalent.

The inventory remains limited to research use and does not authorize:

- community ranking;
- territorial prioritization;
- mobilization;
- targeting;
- narrative;
- paid media.

## Next Action

Keep EV-0105 as the canonical workbook for the current curated layer, retain EV-0106 as an alternate package-distinct copy, and continue the separate official-evidence path for 2023 results, EV-0112 capture, and electoral geography.
