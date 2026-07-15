# EV-0105 Community Inventory — Data Quality Review

Review date: 2026-07-14  
Evidence ID: `EV-0105`  
Evidence class: Campaign research  
Evidence layer: Curated subset  
Gate result: PASS for sampled cell preservation; methodology remains unverified

## Source and Provenance

Raw structured extraction:

`research/extracted/territorio/EV-0105.sheet-Resumen-Comparativo.csv`

Curated inventory:

`research/curated/territorio/EV-0105-community-inventory.csv`

The raw extraction preserves workbook, sheet, source row, column, column letter, header, value, formula, and blank status.

## Curated Scope

The curated inventory contains seven community records from sheet `Resumen Comparativo`, source rows 2 through 8:

- San Felipe de Jesús;
- San Juan del Obispo;
- San Bartolomé Becerra;
- Santa Ana;
- Santa Inés Monte Pulciano;
- Santa Catarina Bobadilla;
- San Pedro Las Huertas.

Community names are retained as written in the source. The normalized name currently equals the original name because no spelling conflict was established in this reviewed subset.

## Fields Included

The curated CSV includes:

- population labeled by the source as `Población (INE 2018)`;
- registered-elector estimate labeled by the source as `Empadronados Est. (2023)`;
- workbook, sheet, and source-row provenance;
- missing-value indicators;
- evidence class and verification status.

All seven reviewed records contain nonblank values for both included numeric fields.

## Fields Present but Not Promoted

The workbook also contains:

- `Nivel de Acceso`;
- `Prioridad Estratégica`.

These source fields are recorded only in `available_fields`. Their values are not promoted into the curated inventory because:

1. they are campaign-research judgments rather than official facts;
2. no methodology, scoring rule, reviewer, or observation date was established during the pilot;
3. carrying `Prioridad Estratégica` into the curated layer could be misread as an approved community ranking;
4. C1-TERR-001 prohibits priority scoring and mobilization recommendations.

## Verification Assessment

| Quality dimension | Status | Note |
|---|---|---|
| Cell preservation | PASS | Sampled source cells matched the extracted CSV. |
| Row provenance | PASS | Workbook, sheet, row, column, and header were retained in raw extraction. |
| Community-name normalization | PASS WITH LIMITATION | No transformation was required for the seven reviewed names; official geography cross-check remains pending. |
| Population methodology | PARTIAL | The workbook labels values as INE 2018, but this loop did not independently verify each value against an official census table. |
| Registered-elector estimates | PARTIAL | Values are explicitly estimates for 2023 and are not equivalent to the official 2026 electoral roll. |
| Access classification | NOT CURATED | Method and date are not documented in the reviewed output. |
| Strategic priority | NOT CURATED | Campaign judgment; prohibited from becoming an approved ranking in this loop. |
| Canonical-version decision | OPEN | EV-0106 still requires comparison before EV-0105 can be declared the canonical workbook. |

## Missing Evidence

The following fields are absent or unverified for territorial decision-making:

- official community-to-electoral-geography crosswalk;
- official population source row and table citation for every community;
- official current electorate by community;
- age and sex distribution by community;
- field-research date, method, sample, and respondent profile;
- infrastructure and public-service indicators with official provenance;
- organizational presence, volunteer capacity, and access evidence;
- duplicate/version comparison against EV-0106.

## Interpretation Limits

- The inventory confirms that these community names and source values exist in EV-0105; it does not verify the workbook methodology.
- Estimated registered-elector values must not replace official electoral-roll data.
- This artifact must not be used to score, rank, target, or prioritize communities.
- This artifact is curated evidence, not decision evidence.

## Gate

**Curated status:** Curated, pending decision approval  
**Territorial prioritization:** Blocked  
**Segment, narrative, paid media, and mobilization:** Blocked
