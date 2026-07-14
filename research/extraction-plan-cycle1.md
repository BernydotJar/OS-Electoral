# Cycle 1 Evidence Extraction Plan

Last updated: 2026-07-14  
Cycle: 1 - Electoral Evidence Baseline  
Owner: Electoral Research  
Status: Ready for local execution  
Primary register: `research/evidence-register.md`

## Objective

Convert the highest-value sources in `rag_municipal_core` and `rag_territorio` into traceable, retrieval-ready evidence without selecting a priority electoral segment, approving a public narrative, or authorizing paid media or field mobilization.

## Extraction Principles

1. Preserve source provenance at document, page, section, table, sheet, and row level whenever available.
2. Separate official municipal and legal evidence from campaign interpretation.
3. Record extraction failures, unreadable pages, ambiguous dates, duplicate versions, and unsupported claims.
4. Do not treat generated summaries as primary evidence.
5. Do not copy sensitive personal data into the repository or RAG corpus.
6. Every extracted claim must link back to an evidence-register ID.
7. A source marked `Needs verification` cannot be promoted to accepted factual evidence solely because extraction succeeded.

## Priority Order

### Wave 1 - Electoral and Territorial Baseline

| Priority | Evidence ID | Source | Collection | Expected Output |
|---:|---|---|---|---|
| 1 | EV-0111 | Electoral roll statistics as of 2026-04-30 | `rag_territorio` | Antigua Guatemala electorate totals and available demographic breakdowns |
| 2 | EV-0112 | 2023 municipal election validity agreement | `rag_territorio` | Legal result, winning slate, dates, resolution identifiers, and limits of the document |
| 3 | EV-0105 | Structured community profiles workbook | `rag_territorio` | Community inventory, fields, completeness assessment, and normalized territorial table |
| 4 | EV-0103 | Village needs diagnosis | `rag_territorio` | Needs by village, source method, dates, confidence, and unresolved verification questions |
| 5 | EV-0104 | Narrative community profiles | `rag_territorio` | Community-level qualitative claims mapped to location and evidence class |
| 6 | EV-0114 | PDM-OT Antigua Guatemala | Both | Official territorial units, development priorities, land-use context, indicators, and planning horizon |

### Wave 2 - Municipal Authority and Institutional Capacity

| Priority | Evidence ID | Source | Collection | Expected Output |
|---:|---|---|---|---|
| 7 | EV-0113 | Municipal Code | `rag_municipal_core` | Municipal powers, council responsibilities, mayoral authority, procedures, and article-level citations |
| 8 | EV-0120 | Municipal organization chart | `rag_municipal_core` | Institutional unit map and responsibility crosswalk |
| 9 | EV-0118 | Public attention department MOF | `rag_municipal_core` | Citizen-service functions, workflows, responsibilities, and service gaps supported by the document |
| 10 | EV-0119 | Economy and tourism department MOF | `rag_municipal_core` | Economic-development and tourism mandates, roles, and institutional constraints |
| 11 | EV-0117 | Municipal multiannual operational plan 2025-2029 | `rag_municipal_core` | Products, indicators, targets, responsible units, dates, and budget linkages |

### Wave 3 - Budget and Execution Baseline

| Priority | Evidence ID | Source | Collection | Expected Output |
|---:|---|---|---|---|
| 12 | EV-0121 | Annual expenditure budget 2025 | `rag_municipal_core` | Program, unit, object, and amount tables with totals reconciled |
| 13 | EV-0123 | Monthly budget execution collection | `rag_municipal_core` | Monthly execution table, cumulative execution, anomalies, and missing periods |
| 14 | EV-0122 | Alternate annual budget file | `rag_municipal_core` | Duplicate/version comparison against EV-0121 |

### Wave 4 - Campaign Research Cross-Check

| Priority | Evidence ID | Source | Collection | Expected Output |
|---:|---|---|---|---|
| 15 | EV-0101 / EV-0102 | Municipal diagnosis versions | `rag_municipal_core` | Claim inventory, cited sources, unsupported assertions, and version reconciliation |
| 16 | EV-0106 | Alternate community workbook | `rag_territorio` | Duplicate/version comparison against EV-0105 |
| 17 | EV-0115 | Historical PDM | `rag_municipal_core` | Historical comparison only; distinguish superseded planning assumptions |

## Standard Extraction Record

Every extracted document must produce a manifest with at least:

```yaml
evidence_id: EV-XXXX
source_path: /absolute/or/repository/path
source_title: ""
source_type: pdf|docx|xlsx|md|folder
collection: rag_municipal_core|rag_territorio
source_class: official_source|campaign_research|perception
review_status_before: needs_extraction|needs_verification
extracted_at: YYYY-MM-DDTHH:MM:SSZ
extractor: human-or-agent-name
source_date: YYYY-MM-DD|unknown
territory: ""
language: es
page_count: null
sheet_names: []
content_hash: ""
version_relationship: canonical|duplicate_candidate|alternate|historical|unknown
contains_personal_data: false
extraction_status: complete|partial|failed
limitations: []
```

## Required Outputs

Store generated outputs outside the original source directory and preserve originals unchanged.

Recommended local structure:

```text
research/extracted/
├── manifests/
│   └── EV-XXXX.yaml
├── municipal-core/
│   ├── EV-XXXX.md
│   └── EV-XXXX.tables.csv
├── territorio/
│   ├── EV-XXXX.md
│   └── EV-XXXX.tables.csv
└── logs/
    └── extraction-run-YYYYMMDD.md
```

Only sanitized, non-sensitive extraction outputs should be committed.

## Chunking and Retrieval Rules

- Legal documents: chunk by article or coherent article group; retain article number and page.
- Plans and diagnoses: chunk by heading/subheading; retain page range and planning period.
- MOFs: chunk by organizational unit, function, process, or responsibility.
- Budgets: preserve tables as structured rows; do not rely only on prose summaries.
- Spreadsheets: preserve workbook, sheet, row range, column names, formulas-versus-values status, and blank-rate statistics.
- Community profiles: use one community as the default semantic boundary; retain the source field for each claim.
- Election documents: distinguish legal validation from detailed vote totals; never infer unavailable totals.

## Quality Gates

An extraction passes only when:

- the output opens and is readable;
- source and content hashes are recorded;
- page, section, table, sheet, or row provenance is retained;
- tables reconcile against visible source totals where applicable;
- claims are labeled by evidence class;
- limitations and missing fields are explicit;
- duplicate candidates are not silently merged;
- personal data has been excluded or safely aggregated;
- the evidence register is updated with the extraction result.

## Acceptance Tests

### `rag_municipal_core`

The corpus must answer, with exact citations:

1. What powers and responsibilities legally belong to the municipality, council, and mayor?
2. Which municipal units own citizen service, tourism, economic development, and planning functions?
3. What programs, indicators, budgets, and execution levels are documented?
4. Which campaign diagnosis claims are supported by official sources, unsupported, or contradicted?

### `rag_territorio`

The corpus must answer, with exact citations:

1. What territorial units and communities are explicitly documented?
2. What needs are attributed to each community, by which source and method?
3. What electorate and historical election information is actually available?
4. Which territorial fields remain missing before prioritization can begin?

## Definition of Done

This extraction phase is complete when:

- Wave 1 and Wave 2 sources have manifests and readable outputs;
- EV-0105 and EV-0106 have a documented version decision;
- EV-0121 and EV-0122 have a documented version decision;
- official facts are separated from campaign research and perception;
- the evidence register reflects extraction status and limitations;
- a territorial data-gap brief can be produced without selecting a priority segment;
- no public narrative, paid-media audience, or mobilization priority has been approved as a side effect.

## Risks

- PDFs may contain scanned pages, malformed tables, or inconsistent encodings.
- Campaign documents may cite outdated or circular sources.
- Workbook formulas may not have cached values or may depend on unavailable external links.
- Multiple files may be alternate versions rather than true duplicates.
- Community-level claims may lack dates, methods, or sample definitions.
- Official legal validation documents may not contain detailed electoral totals.

## Human Approval Required

Human review is required before:

- choosing the canonical version of duplicate workbooks or budgets;
- promoting a `Needs verification` source to `Accepted`;
- using extracted community claims to prioritize territory;
- selecting a priority segment;
- using any extracted material in public communication.

## Next Recommended Action

Run a pilot extraction on EV-0111, EV-0112, EV-0105, and EV-0114. Validate the manifests, structured tables, citations, and privacy controls before processing the remaining corpus.

## Next Agent

Electoral Research, supported by Territory and Tracking/Risks.