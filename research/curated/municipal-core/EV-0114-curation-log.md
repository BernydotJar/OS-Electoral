# EV-0114 Table Curation Log

Review date: 2026-07-14  
Evidence ID: `EV-0114`  
Evidence class: Official source  
Evidence layer: Curated partial subset  
Gate result: PARTIAL

## Source

Plan de Desarrollo Municipal y Ordenamiento Territorial — Antigua Guatemala.

Raw structured extraction:

`research/extracted/municipal-core/EV-0114.tables.csv`

Deterministic gate:

`research/extracted/logs/ev0114-table-detection-gate-20260714.md`

Curated table catalog:

`research/curated/municipal-core/EV-0114-curated-tables.csv`

## Curation Rule

The raw extractor produced 399 table detections. They are raw candidates, not 399 trusted tables.

Only detections classified `VALIDATED_TABLE` by the deterministic 25-detection gate were promoted into the curated table catalog.

`LIKELY_TABLE`, `FRAGMENTED_TABLE`, `LAYOUT_ARTIFACT`, and `EMPTY_OR_NOISE` detections were excluded.

## Gate Sample

| Classification | Count | Curated treatment |
|---|---:|---|
| VALIDATED_TABLE | 8 | Included in table-level curated catalog |
| LIKELY_TABLE | 7 | Excluded pending visual review |
| FRAGMENTED_TABLE | 6 | Excluded |
| LAYOUT_ARTIFACT | 3 | Excluded |
| EMPTY_OR_NOISE | 1 | Excluded |

## Included Detections

| Page | Table index | Gate basis | Current use |
|---:|---:|---|---|
| 17 | 2 | Coherent education-coverage table sample | Table discovery and future row-level curation |
| 94 | 1 | Coherent projection/planning table sample | Table discovery and future row-level curation |
| 128 | 1 | Coherent threshold/range table sample | Table discovery and future row-level curation |
| 160 | 1 | Coherent roadway-classification table sample | Table discovery and future row-level curation |
| 205 | 2 | Coherent actions/programs/projects matrix | Table discovery; row-level context and privacy review still required |
| 210 | 1 | Large execution/efficiency/effectiveness matrix | Table discovery; deeper sampling required |
| 218 | 1 | Large priorities/targets/indicators matrix | Table discovery; source-period and row-level review required |
| 221 | 1 | Coherent acronym table | Reference-table discovery |

## Important Limitation

The curated CSV is a **table-level catalog**, not a fully normalized cell-level dataset.

The GitHub gate records provide verified page, table index, sample size, representative content, and classification. Full cell normalization would require reading each selected page/table from the raw CSV and comparing the resulting rows against the visible PDF.

Therefore:

- the eight entries may be used to locate validated table candidates;
- representative snippets may be used only as table-identification evidence;
- no quantitative total should be derived from the catalog alone;
- no row or column outside the gate sample is automatically trusted;
- the 399 raw detections remain unchanged.

## Excluded Categories

### LIKELY_TABLE

These appear structurally plausible but require visual source comparison before promotion.

### FRAGMENTED_TABLE

These contain real table content split or merged in ways that can distort meaning.

### LAYOUT_ARTIFACT

These are prose, map labels, questions, or visual layout interpreted as tables.

### EMPTY_OR_NOISE

These contain no usable structured evidence.

## Downstream Rules

- Only individually reviewed rows from validated detections may later enter a quantitative dataset.
- Named persons or participant lists require context and privacy review before publication or indexing.
- Planning indicators must retain the plan period and must not be presented automatically as current 2026 conditions.
- Programs and projects in the PDM-OT are planning evidence, not approved campaign promises.
- No table in this artifact authorizes territorial ranking, segment selection, narrative, paid media, or mobilization.

## Gate

**Source status:** Partial, curated subset available  
**Curated table detections:** 8  
**Trusted fully normalized tables:** 0 in this loop  
**Political decision use:** Not approved
