# Spec: Cycle 1 Curated Territorial Baseline

Status: Draft
Owner: Electoral Research
Reviewers: Territory and Mobilization; Tracking, Risks, and Learning
Cycle: 1 - Electoral Evidence Baseline
Spec ID: C1-TERR-001

## 1. Purpose

Convert the four pilot sources into a curated territorial evidence baseline and produce a territorial data-gap brief without selecting a priority segment, geographic mobilization priority, public narrative, paid-media audience, or field-operation plan.

## 2. Problem Statement

The extraction pilot passed with conditions, but the current corpus remains partial:

- EV-0111 passed and may support aggregate electoral-roll baseline analysis.
- EV-0105 passed and may support community inventory and source-field analysis.
- EV-0112 remains partial because substantive pages are not text-extractable.
- EV-0114 remains partial because only individually reviewed table detections may be trusted.

The campaign needs a curated baseline that distinguishes known facts, partial evidence, unsupported claims, and missing territorial fields before any territorial prioritization can begin.

## 3. Outcome

Produce a reviewable evidence package that answers:

1. Which communities and territorial units are explicitly documented?
2. Which electoral-roll facts are available for Antigua Guatemala?
3. Which community fields exist, which are incomplete, and which are unsupported?
4. Which PDM-OT passages and tables are safe for analytical use?
5. Which legal-election facts are available from EV-0112, and what remains inaccessible?
6. What evidence gaps block territorial prioritization and segment selection?

## 4. In Scope

### Sources

- EV-0111: Electoral roll statistics as of 2026-04-30.
- EV-0112: 2023 municipal election validity agreement.
- EV-0105: Structured community profiles workbook.
- EV-0114: PDM-OT Antigua Guatemala.

### Work

- Curate approved aggregate facts from EV-0111.
- Normalize the EV-0105 community inventory without ranking communities.
- Create a limited manual or OCR-backed supplement for substantive missing pages in EV-0112.
- Promote only individually reviewed EV-0114 table detections into a curated table set.
- Produce a territorial data-gap brief.
- Update evidence statuses and limitations.
- Preserve provenance and evidence-layer boundaries.

## 5. Out of Scope

- Selecting a priority electoral segment.
- Scoring or ranking communities.
- Approving a geographic mobilization priority.
- Producing public narrative, campaign content, attacks, or promises.
- Creating paid-media audiences or budgets.
- Running broad OCR over all source documents.
- Expanding to Wave 2 or the remaining evidence corpus.
- Building embeddings or deploying a production RAG service.

## 6. Evidence Layers

### Raw

Machine-generated extraction outputs retained for audit and reprocessing.

### Curated

Human-reviewed facts, passages, and tables with exact provenance.

### Decision Evidence

Curated evidence explicitly approved for a named campaign decision.

This spec may create Raw and Curated outputs only. It must not promote evidence into Decision Evidence.

## 7. Functional Requirements

### FR-01: EV-0111 Curated Electoral-Roll Baseline

Create `research/curated/territorio/EV-0111-baseline.md` containing only aggregate facts relevant to Antigua Guatemala.

Each fact must include:

- evidence ID;
- source page;
- table or row label;
- date of cut;
- territorial scope;
- interpretation limitation.

The output must explicitly state that electoral roll totals are not turnout, preference, support, or voting intention.

### FR-02: EV-0105 Community Inventory

Create:

- `research/curated/territorio/EV-0105-community-inventory.csv`
- `research/curated/territorio/EV-0105-data-quality.md`

The CSV must preserve:

- normalized community name;
- original community name;
- workbook;
- sheet;
- source row;
- available fields;
- missing-field indicators;
- evidence class;
- verification status.

No priority score, persuasion score, support estimate, or mobilization recommendation may be added.

### FR-03: EV-0112 Partial Supplement

Create `research/curated/territorio/EV-0112-partial-supplement.md`.

For each non-extractable substantive page:

- identify the page;
- record whether the content was manually transcribed or processed with controlled OCR;
- preserve visible headings, dates, resolution identifiers, and legal effect;
- record uncertainty and unreadable fragments;
- avoid inferring detailed vote totals not present in the source.

EV-0112 must remain `PARTIAL` unless all substantive content is accurately captured and human-reviewed.

### FR-04: EV-0114 Curated Tables

Create:

- `research/curated/municipal-core/EV-0114-curated-tables.csv`
- `research/curated/municipal-core/EV-0114-curation-log.md`

Only detections classified `VALIDATED_TABLE` may enter the curated CSV.

`LIKELY_TABLE` detections may be listed in the curation log but must not enter the curated CSV until reviewed.

The curated CSV must preserve:

- evidence ID;
- page;
- table index or source identifier;
- table title when available;
- row and column provenance;
- extracted value;
- validation reviewer;
- validation date;
- limitations.

The source set of 399 detections must continue to be labeled as raw candidates, not trusted tables.

### FR-05: Territorial Data-Gap Brief

Create `territory/territorial-data-gap-brief.md`.

The brief must include:

- confirmed territorial units;
- confirmed aggregate electoral facts;
- available community attributes;
- missing demographic fields;
- missing electoral-history fields;
- missing field-research evidence;
- missing structure and access information;
- source conflicts or version ambiguity;
- decisions still blocked;
- recommended next research actions ranked by decision value and evidence urgency.

The brief must not recommend a winning territory, target segment, or mobilization priority.

### FR-06: Evidence Register Update

Update `research/evidence-register.md` with actual statuses only.

Allowed status changes:

- PASS -> Curated, pending decision approval
- PARTIAL -> Partial, curated subset available
- Needs extraction -> unchanged unless work was performed

Each update must link to the curated artifact and retain limitations.

### FR-07: Privacy and Portability

- Source configuration must use `POLITICS_ROOT` plus relative paths.
- No absolute local user paths may be introduced in new committed files.
- No personal contact information, individual voter records, DPI, CUI, phone, email, or home address may enter curated outputs.
- Aggregate official values are permitted when their context is explicit.

## 8. Non-Functional Requirements

### NFR-01: Reproducibility

Every generated artifact must identify the source evidence ID and generation or review date.

### NFR-02: Traceability

Every factual row or statement must be traceable to page, table, sheet, or row provenance.

### NFR-03: Determinism

Sampling or review selection must use a recorded deterministic seed where applicable.

### NFR-04: Auditability

Raw outputs must remain unchanged. Curated outputs must be produced separately.

### NFR-05: Safety

No political gate may open as a side effect of completing this spec.

## 9. Required Artifacts

```text
research/curated/
├── territorio/
│   ├── EV-0111-baseline.md
│   ├── EV-0105-community-inventory.csv
│   ├── EV-0105-data-quality.md
│   └── EV-0112-partial-supplement.md
└── municipal-core/
    ├── EV-0114-curated-tables.csv
    └── EV-0114-curation-log.md

territory/
└── territorial-data-gap-brief.md
```

The implementation may also update:

- `research/evidence-register.md`
- extraction validation scripts or tests when required by the spec
- logs directly supporting the acceptance evidence

## 10. Acceptance Criteria

### AC-01

EV-0111 curated facts match visible source values and include page-level provenance and interpretation limits.

### AC-02

EV-0105 produces one normalized community inventory with original values preserved, missing fields visible, and no ranking columns.

### AC-03

EV-0112 substantive non-extractable pages are documented, and the source remains PARTIAL unless fully captured and reviewed.

### AC-04

EV-0114 curated CSV contains only individually validated tables. The count of curated tables must not be represented as 399.

### AC-05

The territorial data-gap brief clearly separates confirmed evidence, partial evidence, campaign research, perception, and unknowns.

### AC-06

PII validation passes, and a human review records no prohibited personal data in curated outputs.

### AC-07

No new file contains `/Users/eduardosacahui` or another absolute personal path.

### AC-08

The evidence register links to all created curated artifacts and records remaining limitations.

### AC-09

The final implementation report states that segment, narrative, paid media, and mobilization remain blocked.

## 11. Validation Commands

The implementer must run available project validation plus checks equivalent to:

```bash
python -m py_compile scripts/evidence/extract_pilot.py scripts/evidence/validate_pilot.py
python scripts/evidence/validate_pilot.py --input research/extracted --pii-self-test

grep -Rni '/Users/' research/curated territory research/evidence-register.md && exit 1 || true
grep -RniE 'priority score|persuasion score|mobilization priority|target segment' research/curated territory/territorial-data-gap-brief.md && exit 1 || true
```

Additional validation must confirm:

- required files exist and are non-empty;
- CSV headers match the spec;
- all curated records contain provenance;
- EV-0114 curated rows reference only reviewed validated detections;
- no raw source file was modified.

## 12. Implementation Sequence

1. Read runtime, current state, evidence register, extraction plan, and pilot gate decision.
2. Verify the local pilot branch and existing raw outputs.
3. Create curated directories without modifying raw outputs.
4. Curate EV-0111.
5. Normalize and assess EV-0105.
6. Supplement EV-0112 only for substantive missing pages.
7. Build the validated subset for EV-0114.
8. Produce the territorial data-gap brief.
9. Update the evidence register.
10. Run validation and document evidence.
11. Stop without selecting segments, ranking territories, or producing campaign content.

## 13. Risks

- Controlled OCR may introduce transcription errors.
- Community names may have spelling or accent variants.
- EV-0105 may lack methodology, dates, or provenance for some claims.
- EV-0114 validated samples may not cover all analytically valuable tables.
- Curated evidence may be mistaken for decision approval.
- Public repository exposure requires strict privacy review.

## 14. Human Approval Gates

Human approval is required before:

- changing EV-0112 from PARTIAL to PASS;
- promoting LIKELY_TABLE to VALIDATED_TABLE;
- resolving community-name conflicts where the source is ambiguous;
- using curated evidence for territorial scoring;
- selecting a priority segment;
- opening any public communication, paid-media, or mobilization gate.

## 15. Definition of Done

This loop is complete when:

- all required artifacts exist;
- acceptance criteria pass or documented exceptions remain explicit;
- EV-0111 and EV-0105 have curated outputs;
- EV-0112 and EV-0114 retain correct partial limitations;
- the territorial data-gap brief is reviewable;
- the evidence register is current;
- political gates remain closed;
- an implementation report identifies the next research decision.

## 16. Next Decision

After this spec is implemented, the Campaign Chief may approve one of the following research-only paths:

1. complete the remaining Wave 1 sources EV-0103 and EV-0104;
2. obtain official detailed 2023 vote totals and electoral-geography data;
3. begin Wave 2 municipal authority and institutional-capacity extraction.

No segment or territory-priority decision should be requested until the territorial data-gap brief demonstrates sufficient evidence.