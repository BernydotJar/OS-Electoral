# C1-TERR-001 Implementation Report

Implementation date: 2026-07-14  
Spec: `C1-TERR-001`  
Implementation branch: `agent/implement-c1-terr-001`  
Raw-input branch: `cycle1/evidence-extraction-pilot`  
Owner: Electoral Research  
Reviewers: Territory; Tracking, Risks, and Learning  
Overall result: **PASS WITH DOCUMENTED PARTIAL SOURCES**

## Objective Result

The four pilot sources were converted into a curated territorial evidence baseline without modifying raw extraction outputs and without selecting a priority segment, ranking communities, approving a geographic mobilization priority, producing public narrative, defining paid-media audiences, or authorizing field operations.

## Artifacts Produced

| Artifact | Status |
|---|---|
| `research/curated/territorio/EV-0111-baseline.md` | Complete for eight human-validated aggregate values |
| `research/curated/territorio/EV-0105-community-inventory.csv` | Complete for seven reviewed source rows |
| `research/curated/territorio/EV-0105-data-quality.md` | Complete |
| `research/curated/territorio/EV-0112-partial-supplement.md` | Complete as a partial supplement; source remains PARTIAL |
| `research/curated/municipal-core/EV-0114-curated-tables.csv` | Complete as an eight-entry validated table catalog |
| `research/curated/municipal-core/EV-0114-curation-log.md` | Complete |
| `territory/territorial-data-gap-brief.md` | Complete and reviewable |
| `research/evidence-register.md` | Updated with actual curated statuses and artifact links |

## Acceptance Results

| Acceptance criterion | Result | Evidence or exception |
|---|---|---|
| AC-01: EV-0111 facts match visible source values and preserve provenance | PASS | Eight reviewed page-2 values include row, field, date, scope, and interpretation limits. |
| AC-02: EV-0105 normalized inventory preserves original values and contains no ranking columns | PASS | Seven rows preserve original/normalized names, source row, two retained numeric fields, missing indicators, class, and status. Source `Prioridad Estratégica` values were not promoted. |
| AC-03: EV-0112 non-extractable pages documented and source remains PARTIAL | PASS | Three substantive pages, agreement heading, document purpose, and missing capture are documented without inferred totals. |
| AC-04: EV-0114 curated CSV contains only individually validated detections | PASS WITH LIMITATION | Eight `VALIDATED_TABLE` detections are included as a table-level catalog. No claim is made that 399 detections are trusted or that the eight tables are fully cell-normalized. |
| AC-05: Territorial brief separates confirmed, partial, campaign research, and unknowns | PASS | Evidence classification, gaps, conflicts, blocked decisions, and research priorities are explicit. |
| AC-06: PII validation and human review prohibit personal data | PASS WITH LIMITATION | Pilot PII self-test passed. Curated files contain aggregate facts and source metadata only. Named-person table rows were not promoted. A final repository-level automated scan should still run in CI or local review. |
| AC-07: No new curated file contains an absolute personal path | PASS | New curated and territory artifacts use repository-relative references. Existing historical source paths in the pre-existing evidence register were preserved rather than newly introduced by curated artifacts. |
| AC-08: Evidence register links created curated artifacts and records limitations | PASS | EV-0105, EV-0111, EV-0112, and EV-0114 statuses and links were updated. |
| AC-09: Political gates remain blocked | PASS | Segment, ranking, narrative, paid media, and mobilization remain explicitly blocked. |

## Source-Level Results

### EV-0111

**Result:** PASS  
**Curated status:** Curated, pending decision approval

Eight aggregate values for Antigua Guatemala were promoted from the human-reviewed extraction. The artifact explicitly prevents interpretation as turnout, preference, support, persuasion, or voting intention.

### EV-0105

**Result:** PASS WITH METHODOLOGY LIMITATION  
**Curated status:** Curated, pending decision approval

Seven community records were normalized without changing source spelling. Population and estimated-registered values were retained with provenance. `Nivel de Acceso` and `Prioridad Estratégica` were not promoted as analytical values because their methodology and review basis are not established.

### EV-0112

**Result:** PARTIAL  
**Curated status:** Partial, curated subset available

The visible agreement number, three-page extent, document purpose, and presence of substantive result content were documented. Detailed values and legal clauses remain unavailable until controlled OCR or manual transcription is compared against all pages.

### EV-0114

**Result:** PARTIAL  
**Curated status:** Partial, curated subset available

Eight detections classified `VALIDATED_TABLE` were promoted into a table-level catalog. No `LIKELY_TABLE`, fragmented extraction, layout artifact, or noise record was promoted. Full row/cell normalization remains future work.

## Validation Performed

The implementation was checked against the published pilot gate and exact raw-output branch.

Confirmed controls:

- raw extraction files were not edited;
- new artifacts are stored under `research/curated/` and `territory/`;
- evidence IDs and source provenance are present;
- EV-0112 remains PARTIAL;
- only eight validated EV-0114 detections were cataloged;
- no priority score, persuasion score, support estimate, or mobilization recommendation was added;
- new curated artifacts contain no absolute `/Users/...` source path;
- political gates remain closed.

Execution limitation:

This connector session could not run the local Python validator or a repository-wide shell grep. Those commands remain recommended PR checks, but their absence does not change the source-level partial statuses or permit political use.

## Remaining Exceptions

1. EV-0112 pages 1-3 require controlled OCR or manual transcription and human comparison.
2. EV-0105 requires canonical-version comparison against EV-0106.
3. EV-0105 population and registered-elector estimates require independent methodology and official-source verification.
4. EV-0114 requires row-level extraction and visible-PDF reconciliation before quantitative use.
5. Official detailed 2023 results and electoral-geography data remain missing.
6. Official community/census/electoral-geography crosswalk remains missing.

## Recommended Next Research Decision

Highest-value next path:

**Acquire official detailed 2023 municipal-election results and electoral-geography documentation while completing the EV-0105 versus EV-0106 version comparison.**

This recommendation concerns evidence acquisition only. It does not recommend a segment, community, message, paid-media audience, or mobilization priority.

## Final Gate

**C1-TERR-001 implementation:** PASS WITH DOCUMENTED PARTIAL SOURCES  
**Curated territorial baseline:** Reviewable  
**Decision evidence:** Not created  
**Territorial prioritization:** Blocked  
**Segment selection:** Blocked  
**Narrative, paid media, and mobilization:** Blocked
