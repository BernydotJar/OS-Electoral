# Program Spec: C1-ELEC-2023-001 and C1-TERR-DQ-001

Status: Draft
Owner: Electoral Research
Reviewers: Territory and Mobilization; Tracking, Risks, and Learning
Cycle: 1 - Electoral Evidence Baseline
Program ID: C1-ELEC-2023-PROGRAM

## 1. Purpose

Build an official 2023 municipal electoral-results and electoral-geography baseline for Antigua Guatemala while, in parallel, resolving whether EV-0105 or EV-0106 should be treated as the canonical community workbook.

This program is research-only. It must not select a priority electoral segment, rank communities for persuasion or mobilization, approve a public narrative, define paid-media audiences, or authorize field operations.

## 2. Program Structure

The program contains two coordinated workstreams:

1. `C1-ELEC-2023-001` — Official 2023 Electoral Results and Geography Baseline.
2. `C1-TERR-DQ-001` — EV-0105 vs EV-0106 Canonical Workbook Check.

The workstreams may run in parallel, but they must publish separate artifacts and separate acceptance results.

## 3. Current Evidence State

### Available

- EV-0112: official municipal election-validity agreement, currently `PARTIAL` because all three substantive pages are image-based.
- EV-0111: official 2026 electoral-roll aggregate baseline for Antigua Guatemala.
- EV-0105: extracted community workbook with seven reviewed community rows.
- EV-0106: alternate or duplicate candidate workbook, not yet extracted or compared.
- C1-TERR-001 territorial data-gap brief and curated artifacts.

### Missing or unresolved

- Complete machine-readable capture of EV-0112.
- Official detailed 2023 municipal vote totals by organization or slate.
- Valid, null, blank, challenged, and total-vote fields where officially available.
- Polling-center, voting-table, district, municipality, community, or locality crosswalks.
- Canonical-version decision for EV-0105 versus EV-0106.

## 4. Program Outcomes

The program must produce a reviewable package that answers:

1. What official 2023 municipal election facts are available for Antigua Guatemala?
2. Which facts come from legal validation, detailed results, electoral-roll records, or geographic records?
3. Which vote totals and participation indicators are actually supported by official sources?
4. Which electoral-geography units can be linked safely to municipal or community units?
5. Which data remain unavailable, ambiguous, unofficial, or not comparable?
6. Which of EV-0105 and EV-0106 is canonical, or why no canonical decision can yet be made?
7. What additional evidence is required before any territorial or segment analysis?

## 5. Workstream A — C1-ELEC-2023-001

### 5.1 Objective

Create a source-provenanced 2023 municipal electoral baseline and electoral-geography inventory for Antigua Guatemala using official sources only for factual totals.

### 5.2 In Scope

- Controlled OCR or manual transcription of EV-0112 pages 1-3.
- Discovery and intake of official TSE result files, agreements, adjudication records, result portals, downloadable datasets, polling-center lists, and voting-table records.
- Separation of legal-validation facts from detailed vote-count facts.
- Municipal-level result table when official totals are available.
- Electoral-geography inventory and crosswalk readiness assessment.
- Evidence-register updates and source manifests.
- Explicit documentation of unavailable fields.

### 5.3 Out of Scope

- Inferring missing totals from press articles or social media.
- Treating Wikipedia, news, campaign claims, or candidate posts as official totals.
- Estimating support by community.
- Mapping individual voters.
- Producing persuasion, turnout, targeting, mobilization, or opposition strategies.
- Declaring a target segment or priority territory.

### 5.4 Functional Requirements

#### ELEC-FR-01: EV-0112 controlled capture

Create:

- `research/curated/electoral-2023/EV-0112-transcription.md`
- `research/curated/electoral-2023/EV-0112-review-log.md`

For each page:

- preserve page number;
- identify manual transcription or OCR method;
- capture visible headings, agreement number, date, legal findings, adjudication language, slate or organization names, and result-table values when legible;
- mark unreadable text with explicit uncertainty;
- preserve line, section, table, row, or visual-region provenance;
- prohibit silent correction or completion.

EV-0112 remains `PARTIAL` unless all substantive content is captured and independently reviewed.

#### ELEC-FR-02: official source discovery register

Create:

- `research/electoral-2023/official-source-register.md`

Each candidate source must record:

- source ID;
- authority and domain;
- title;
- source type;
- URL or repository path;
- publication or election date;
- territorial scope;
- fields available;
- accessibility status;
- content hash when downloaded;
- official-source assessment;
- extraction status;
- limitations.

#### ELEC-FR-03: official municipal result table

Create when supported:

- `research/curated/electoral-2023/antigua-guatemala-municipal-results-2023.csv`

Required columns:

- evidence_id;
- election_date;
- department;
- municipality;
- election_type;
- organization_or_slate;
- candidate_or_slate_name;
- votes;
- result_status;
- source_page_or_record;
- source_url_or_path;
- verification_status;
- limitations.

No row may be created from inference. If detailed totals cannot be located, create the header-only file and document the blocker.

#### ELEC-FR-04: participation and ballot-accounting baseline

Create:

- `research/curated/electoral-2023/antigua-guatemala-participation-2023.md`

Record only officially supported fields such as:

- registered electorate;
- ballots cast;
- valid votes;
- null votes;
- blank votes;
- challenged or disputed votes;
- turnout or abstention.

For every metric, record numerator, denominator, source, scope, and whether the metric is published or calculated. Calculations must show formulas and use only verified official inputs.

#### ELEC-FR-05: electoral-geography inventory

Create:

- `research/curated/electoral-2023/electoral-geography-inventory.csv`
- `research/curated/electoral-2023/electoral-geography-data-quality.md`

Potential unit types include:

- department;
- municipality;
- electoral district;
- polling center;
- voting table;
- zone;
- locality;
- community or village where officially identified.

The inventory must not create a community mapping from name similarity alone. Every crosswalk requires an explicit source or must remain `UNRESOLVED`.

#### ELEC-FR-06: legal versus numerical evidence separation

Create:

- `research/curated/electoral-2023/legal-vs-results-crosswalk.md`

Separate:

- facts established by EV-0112 or another legal agreement;
- facts established by detailed result records;
- facts established by electoral-roll or polling-center records;
- facts unavailable or unsupported.

#### ELEC-FR-07: evidence gap and acquisition brief

Create:

- `research/electoral-2023/electoral-data-gap-and-acquisition-brief.md`

Rank missing evidence by:

- decision value;
- authority;
- acquisition feasibility;
- dependency risk;
- privacy risk;
- urgency.

The ranking applies to research acquisition only, not electoral targeting.

## 6. Workstream B — C1-TERR-DQ-001

### 6.1 Objective

Determine whether EV-0105 or EV-0106 is canonical, whether they are true duplicates, alternates, superseded versions, or materially different workbooks, and what fields may safely enter the curated territorial layer.

### 6.2 In Scope

- Extract EV-0106 using the existing spreadsheet provenance model.
- Compare file hashes, workbook metadata, sheet names, dimensions, headers, formulas, values, blanks, community names, and duplicate rows.
- Document field-level and row-level differences.
- Preserve both originals unchanged.
- Recommend one of: `EV-0105_CANONICAL`, `EV-0106_CANONICAL`, `MERGE_REQUIRED`, or `NO_DECISION`.

### 6.3 Out of Scope

- Selecting communities based on workbook priority labels.
- Averaging conflicting values without a source rule.
- Treating estimated empadronados as official electoral totals.
- Deleting or overwriting either source.

### 6.4 Functional Requirements

#### DQ-FR-01: EV-0106 extraction

Create:

- `research/extracted/manifests/EV-0106.yaml`
- `research/extracted/territorio/EV-0106.md`
- one CSV per sheet using the same cell-level schema as EV-0105.

#### DQ-FR-02: structural comparison

Create:

- `research/curated/territorio/EV-0105-vs-EV-0106-structure.csv`

Compare:

- workbook hashes;
- sheet names;
- sheet dimensions;
- column headers;
- formula counts;
- blank rates;
- row counts;
- community counts.

#### DQ-FR-03: value comparison

Create:

- `research/curated/territorio/EV-0105-vs-EV-0106-differences.csv`

Required columns:

- comparison_key;
- community_original_0105;
- community_original_0106;
- normalized_community;
- field;
- value_0105;
- value_0106;
- difference_type;
- source_row_0105;
- source_row_0106;
- review_status;
- reviewer_note.

#### DQ-FR-04: canonical decision memo

Create:

- `research/curated/territorio/EV-0105-vs-EV-0106-canonical-decision.md`

The memo must include:

- relationship classification;
- evidence supporting the classification;
- unresolved conflicts;
- canonical recommendation;
- fields excluded from curated use;
- impact on the existing EV-0105 community inventory;
- whether re-curation is required.

#### DQ-FR-05: safe-field policy

The decision memo must explicitly classify fields as:

- `SOURCE_FACT_CANDIDATE`;
- `CAMPAIGN_ESTIMATE`;
- `CAMPAIGN_PRIORITY_LABEL`;
- `UNVERIFIED_TEXT`;
- `EXCLUDE_FROM_CURATED`.

Campaign priority labels must not become decision evidence.

## 7. Shared Non-Functional Requirements

### NFR-01: provenance

Every factual value must reference an evidence ID and source location.

### NFR-02: reproducibility

Downloaded sources, extraction methods, deterministic seeds, hashes, and review dates must be recorded.

### NFR-03: source authority

Official vote totals must originate from the TSE or another legally authoritative official record. Secondary sources may be recorded only as discovery aids or unresolved corroboration.

### NFR-04: privacy

No individual voter record, DPI, CUI, personal address, phone, email, or other personal identifier may enter committed artifacts.

### NFR-05: portability

No new committed file may contain an absolute personal path. Local source roots must use environment variables and relative paths.

### NFR-06: auditability

Raw files remain unchanged. New extracted, curated, and decision-support artifacts remain in separate directories.

### NFR-07: political safety

Completing this program must not open segment, narrative, paid-media, field-mobilization, opposition-research, or territorial-prioritization gates.

## 8. Required Artifacts

```text
research/
├── electoral-2023/
│   ├── official-source-register.md
│   └── electoral-data-gap-and-acquisition-brief.md
├── curated/
│   ├── electoral-2023/
│   │   ├── EV-0112-transcription.md
│   │   ├── EV-0112-review-log.md
│   │   ├── antigua-guatemala-municipal-results-2023.csv
│   │   ├── antigua-guatemala-participation-2023.md
│   │   ├── electoral-geography-inventory.csv
│   │   ├── electoral-geography-data-quality.md
│   │   └── legal-vs-results-crosswalk.md
│   └── territorio/
│       ├── EV-0105-vs-EV-0106-structure.csv
│       ├── EV-0105-vs-EV-0106-differences.csv
│       └── EV-0105-vs-EV-0106-canonical-decision.md
└── extracted/
    ├── manifests/EV-0106.yaml
    └── territorio/EV-0106*
```

The implementation must also update:

- `research/evidence-register.md`;
- the territorial data-gap brief when the canonical decision changes its conclusions;
- implementation and validation logs.

## 9. Acceptance Criteria

### AC-01

Every published 2023 vote total has an official source and exact record provenance.

### AC-02

EV-0112 is either fully reviewed or remains explicitly `PARTIAL` with page-level gaps.

### AC-03

The municipal result table contains no inferred rows.

### AC-04

Participation metrics distinguish published values from calculated values and show formulas.

### AC-05

The geography inventory distinguishes confirmed crosswalks from unresolved name matches.

### AC-06

EV-0106 has a manifest and cell-level extraction comparable to EV-0105.

### AC-07

The canonical workbook decision is supported by hashes, structure, values, and provenance—not filename preference.

### AC-08

Priority labels and estimated electoral values are not promoted into official or decision evidence.

### AC-09

PII and portability checks pass.

### AC-10

The final report states that all political gates remain closed.

## 10. Validation Commands

Run available project validation plus checks equivalent to:

```bash
python -m py_compile scripts/evidence/extract_pilot.py scripts/evidence/validate_pilot.py
python scripts/evidence/validate_pilot.py --input research/extracted --pii-self-test

grep -Rni '/Users/' research/curated research/electoral-2023 && exit 1 || true
grep -RniE 'target segment|persuasion score|mobilization priority|winning territory' research/curated research/electoral-2023 && exit 1 || true
```

Additional tests must confirm:

- all required artifacts exist and are non-empty;
- result CSV rows reference official evidence;
- no individual voter data are present;
- calculated percentages reconcile with source inputs;
- unresolved geography links remain explicitly unresolved;
- raw EV-0105 and EV-0106 files are unchanged;
- workbook comparison covers every sheet and populated row.

## 11. Long-Loop Execution Sequence

### Loop 0 — readiness

- Read runtime, current state, evidence register, C1-TERR-001 report, and this spec.
- Verify the raw pilot branch and implementation branch.
- Create execution issues and branches.

### Loop 1 — official source discovery

- Search official TSE properties and repository sources.
- Register every candidate source.
- Stop numerical extraction when source authority is uncertain.

### Loop 2 — EV-0112 capture

- Perform controlled OCR or manual transcription.
- Review page by page.
- Update the legal-evidence record.

### Loop 3 — numerical results

- Extract official municipal totals when available.
- Reconcile organizations, totals, and result status.
- Produce a discrepancy log.

### Loop 4 — participation baseline

- Capture official ballot-accounting fields.
- Calculate only derivable metrics with formulas.

### Loop 5 — electoral geography

- Inventory official units and identifiers.
- Build only source-supported crosswalks.

### Loop 6 — EV-0106 extraction

- Produce manifest and cell-level outputs.
- Run the same privacy and provenance gates as EV-0105.

### Loop 7 — workbook comparison

- Compare structure, formulas, values, rows, and communities.
- Produce difference tables and canonical recommendation.

### Loop 8 — synthesis

- Update evidence register and territorial gaps.
- Produce a combined implementation report.

### Loop 9 — acceptance gate

- Evaluate each acceptance criterion as `PASS`, `PARTIAL`, `FAIL`, or `BLOCKED`.
- Open draft PRs without merge.
- Keep political gates closed.

## 12. Stop Conditions

Stop and record `BLOCKED` when:

- an official source cannot be authenticated;
- a source requires credentials not available;
- detailed totals are unavailable;
- OCR confidence is inadequate for legal or numerical facts;
- EV-0106 is not available in the configured source root;
- workbook conflicts cannot be resolved from provenance;
- privacy risk cannot be cleared.

A blocked field must remain empty or explicitly unknown. It must never be inferred.

## 13. Definition of Done

This program is complete when:

- both workstreams have implementation reports;
- required artifacts exist or blocked artifacts contain explicit blocker records;
- official facts, secondary discovery aids, campaign estimates, and unknowns are separated;
- EV-0112 has an accurate final status;
- the workbook relationship has a documented decision or `NO_DECISION`;
- evidence-register entries and limitations are current;
- all political gates remain closed;
- the next research decision is explicit.

## 14. Next Decision

After completion, the Campaign Chief may approve one research-only path:

1. demographic and census baseline by locality;
2. field-research design and evidence collection;
3. Wave 2 municipal authority and institutional-capacity extraction;
4. electoral-geography completion if official records remain incomplete.

No segment, message, paid-media, or mobilization decision may be requested solely from this program.