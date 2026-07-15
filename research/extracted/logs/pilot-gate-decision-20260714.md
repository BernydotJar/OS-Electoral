# Cycle 1 Evidence Extraction Pilot — Gate Decision

Last updated: 2026-07-14  
Branch: `cycle1/evidence-extraction-pilot`  
Decision owner: Tracking, Risks, and Learning  
Overall decision: **PASS WITH CONDITIONS**

## Decision Summary

The evidence extraction pipeline is accepted for controlled expansion of Cycle 1 research.

This decision approves the extraction process, validation controls, provenance model, portable configuration, and privacy checks. It does not approve all extracted content as verified evidence and does not open any political strategy, segment, narrative, paid-media, or field-mobilization gate.

## Source Results

| Evidence ID | Gate Result | Approved Use | Restrictions |
|---|---|---|---|
| EV-0111 | PASS | Aggregate electoral-roll baseline with page-level provenance | Must not be interpreted as turnout, preference, or voting intention |
| EV-0105 | PASS | Community inventory and source-field analysis | Must not be used to rank communities until methodology and evidence quality are reviewed |
| EV-0112 | PARTIAL | Extracted text and visible legal context | Non-extractable pages contain substantive information and require controlled OCR or manual transcription |
| EV-0114 | PARTIAL | Page-level text retrieval and individually reviewed tables | The 399 detections are raw candidates, not 399 trusted tables |

## PII Gate

The PII validator passed its self-test.

The validator excludes known false positives such as:

- CUILAPA;
- CUILCO;
- Dirección Municipal;
- chart-scale numbers;
- aggregate numeric totals.

The value `10001437` was reviewed and classified as an aggregate national total from the row `EN LA REPUBLICA`. It is not personally identifiable information.

Passing the automated PII gate does not replace human review before committing newly extracted sources.

## EV-0114 Table Detection Gate

A deterministic sample of 25 table detections was classified as:

| Classification | Count | Share |
|---|---:|---:|
| VALIDATED_TABLE | 8 | 32% |
| LIKELY_TABLE | 7 | 28% |
| FRAGMENTED_TABLE | 6 | 24% |
| LAYOUT_ARTIFACT | 3 | 12% |
| EMPTY_OR_NOISE | 1 | 4% |

The complete set of 399 detections must remain classified as raw extraction output.

Only tables individually classified as `VALIDATED_TABLE` may enter the trusted structured-evidence layer.

`LIKELY_TABLE` detections require review before analytical use.

`FRAGMENTED_TABLE`, `LAYOUT_ARTIFACT`, and `EMPTY_OR_NOISE` detections must not be embedded or used for quantitative analysis.

## Approved Architecture

The pilot establishes three evidence layers:

### Raw extraction

Machine-generated text and table detections preserved for audit and reprocessing.

### Curated evidence

Human-reviewed passages and tables with source, page, section, sheet, row, and evidence ID.

### Decision evidence

Curated evidence explicitly approved to support a campaign decision.

Movement between layers must be explicit and recorded. Extraction success alone cannot promote evidence to the next layer.

## Conditions for Expansion

The pipeline may be applied to additional Cycle 1 sources when:

1. every source receives a manifest;
2. extraction limitations remain explicit;
3. PII validation is executed;
4. raw tables are not automatically classified as trusted;
5. source status is updated in the evidence register;
6. official sources remain separated from campaign research and perception;
7. originals remain unchanged;
8. no strategic gate is opened as a side effect.

## Remaining Work

- Apply controlled OCR or manual transcription to the substantive non-extractable pages of EV-0112.
- Build a curated-table output for EV-0114 containing only reviewed detections.
- Continue the Wave 1 and Wave 2 extraction plan.
- Produce a territorial data-gap brief after the approved sources are curated.
- Maintain priority segment, narrative, paid media, and field mobilization as blocked.

## Political Gates

This pilot does not approve:

- a priority electoral segment;
- a geographic mobilization priority;
- a public narrative;
- campaign claims or promises;
- paid-media audiences;
- field operations.

## Final Decision

**Pipeline:** PASS WITH CONDITIONS  
**Current extracted corpus:** PARTIAL  
**Controlled expansion:** APPROVED  
**Political decision use:** NOT YET APPROVED
