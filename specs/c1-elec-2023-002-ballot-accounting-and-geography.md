# Spec: C1-ELEC-2023-002 — Ballot Accounting, Second Review, and Electoral Geography

Status: Draft  
Owner: Electoral Research  
Reviewers: Tracking, Risks, and Learning; Territory and Mobilization  
Cycle: 1 - Electoral Evidence Baseline  
Parent program: `C1-ELEC-2023-PROGRAM`

## 1. Purpose

Complete the next research-only stage of the 2023 Antigua Guatemala electoral baseline by:

1. performing a second human review of the EV-0112 controlled capture;
2. reconciling the 14 visible organization vote rows, whose current sum is `26,091`, against authoritative ballot-accounting records;
3. obtaining and documenting official 2023 electoral-geography records;
4. preserving a strict separation between official facts, derived calculations, unresolved fields, and campaign research.

This spec does not authorize segment selection, territorial ranking, narrative, paid media, mobilization, targeting, public promises, or attacks.

## 2. Current Baseline

The merged PR #9 established:

- EV-0112 status: `PARTIAL_REVIEWED_CAPTURE`;
- 14 visually reviewed organization vote rows from page 1;
- visible vote-row sum: `26,091`;
- no inferred registered electorate, ballots cast, turnout, null votes, blank votes, abstention, polling centers, voting tables, or geographic crosswalks;
- EV-0105 canonical decision: `EV-0105_CANONICAL`;
- EV-0106 retained as a package-distinct alternate with equivalent extracted worksheet content.

## 3. In Scope

### Workstream A — EV-0112 Second Review

- Review all three rendered pages independently from the first capture.
- Confirm or correct agreement number, authority, municipality, election date, organization names, organization vote values, elected offices, names, legal effect, term, possession date, agreement date, and signatories.
- Record every correction as a before/after entry with page provenance.
- Keep EV-0112 partial unless all substantive content is captured and reviewed with sufficient confidence.

### Workstream B — Official Ballot Accounting

Acquire an authoritative official record containing as many of the following as available:

- registered electorate for the 2023 election;
- ballots cast;
- valid organization votes;
- null votes;
- blank votes;
- challenged or other ballot categories, where applicable;
- abstention or participation;
- printed totals suitable for reconciliation.

The workstream must reconcile, not assume, the relationship between the visible organization-vote sum of `26,091` and official ballot-accounting totals.

### Workstream C — Official Electoral Geography

Acquire official records for Antigua Guatemala covering available identifiers and names for:

- electoral municipality;
- electoral district or circumscription;
- voting centers;
- voting tables or juntas receptoras de votos;
- addresses or location descriptions at an institutional level;
- codes and source identifiers;
- relationships between official electoral units.

No community-to-center or community-to-table relationship may be created from name similarity alone.

## 4. Out of Scope

- Predicting support or persuasion.
- Ranking communities or voting centers.
- Selecting field priorities.
- Building voter-level records.
- Using personal voter data.
- Inferring missing ballot categories.
- Treating EV-0105 estimates as official election data.
- Producing public communications, ads, attacks, promises, or mobilization instructions.

## 5. Required Artifacts

```text
research/curated/electoral-2023/
├── EV-0112-second-review.md
├── EV-0112-corrections.csv
├── antigua-guatemala-ballot-accounting-2023.csv
├── antigua-guatemala-ballot-reconciliation-2023.md
├── electoral-geography-inventory.csv
├── electoral-geography-crosswalk.csv
├── electoral-geography-data-quality.md
└── C1-ELEC-2023-002-implementation-report.md

research/electoral-2023/
├── official-source-register.md
└── source-acquisition-log.md
```

The implementation may also update:

- `research/evidence-register.md`;
- `territory/territorial-data-gap-brief.md`;
- `research/curated/electoral-2023/legal-vs-results-crosswalk.md`;
- validators or tests directly required by this spec.

## 6. Functional Requirements

### FR-01: Independent Second Review

Create `EV-0112-second-review.md` with:

- reviewer role and review date;
- page-by-page review outcome;
- confidence level by field group;
- explicit confirmation or correction of each captured vote row;
- unresolved characters, names, accents, or values;
- final source status.

### FR-02: Correction Ledger

Create `EV-0112-corrections.csv` with columns:

```text
field_group,page,record_key,previous_value,reviewed_value,change_type,review_status,review_note
```

Allowed `change_type` values:

- `CONFIRMED`;
- `CORRECTED`;
- `UNRESOLVED`;
- `NOT_PRESENT`.

### FR-03: Ballot-Accounting Dataset

Create `antigua-guatemala-ballot-accounting-2023.csv` with one row per official accounting field and columns:

```text
evidence_id,election_date,department,municipality,field_name,field_value,unit,source_record,source_page_or_table,verification_status,limitations
```

Do not populate a field without an authoritative source record.

### FR-04: Reconciliation

Create `antigua-guatemala-ballot-reconciliation-2023.md` that evaluates:

- visible organization-vote sum: `26,091`;
- official printed valid-vote total, if available;
- ballots cast;
- null votes;
- blank votes;
- other categories;
- registered electorate;
- derived participation and abstention only when numerators and denominators are verified.

Every equation must show its inputs and source references.

Possible reconciliation outcomes:

- `RECONCILED`;
- `RECONCILED_WITH_DOCUMENTED_CATEGORIES`;
- `PARTIAL_RECONCILIATION`;
- `NOT_RECONCILED`.

### FR-05: Electoral-Geography Inventory

Update or create `electoral-geography-inventory.csv` with columns:

```text
evidence_id,election_year,department,municipality,geography_type,official_code,official_name,official_parent_code,official_parent_name,address_or_location,source_record,verification_status,limitations
```

Allowed verification states:

- `CONFIRMED`;
- `PARTIAL`;
- `UNRESOLVED`;
- `CONFLICT`.

### FR-06: Geography Crosswalk

Create `electoral-geography-crosswalk.csv` only for relationships explicitly supported by authoritative records.

Columns:

```text
from_type,from_code,from_name,to_type,to_code,to_name,relationship,source_record,verification_status,limitations
```

Name similarity is not evidence.

### FR-07: Data-Quality Report

Create `electoral-geography-data-quality.md` documenting:

- source coverage;
- missing codes;
- duplicate names;
- address ambiguity;
- historical-versus-current geography issues;
- unresolved community crosswalks;
- prohibited inferences.

### FR-08: Evidence Register

Update evidence status only according to completed review:

- EV-0112 may move beyond partial only after the second review and complete substantive capture;
- detailed results and geography sources require separate evidence IDs;
- every new official source must record authority, date, scope, URL or portable path, and limitations.

## 7. Calculation Rules

- `organization_vote_sum = sum(verified organization vote rows)`.
- `valid_vote_total` must come from an official printed field or be clearly marked as a derived sum.
- `ballots_cast` must not be equated with valid organization votes.
- `participation_rate = ballots_cast / registered_electorate` only when both are verified for the same election and territorial scope.
- `abstention_rate = 1 - participation_rate` only under the same condition.
- Null, blank, challenged, and other categories must never be inferred as residual values unless an official accounting formula and complete totals support the derivation; any such derivation must be labeled `DERIVED`, not `PRINTED`.
- The 2026 electoral roll must not be used as the 2023 denominator.

## 8. Non-Functional Requirements

### NFR-01: Provenance

Every value must identify evidence ID and page, table, record, or official dataset row.

### NFR-02: Auditability

First-review artifacts remain unchanged. Second-review results and corrections are stored separately.

### NFR-03: Privacy

No individual voter records, DPI, CUI, personal phone, personal email, or residential voter address may enter the repository.

### NFR-04: Portability

No personal absolute path may be introduced. Local files must use `POLITICS_ROOT` plus relative paths.

### NFR-05: Political Safety

Completion of this spec must not open any strategy or activation gate.

## 9. Acceptance Criteria

### AC-01

All 14 organization vote rows receive a second-review status.

### AC-02

The value `26,091` is reproduced from the reviewed rows and labeled as a derived visible-row sum, not automatically as ballots cast or total valid votes.

### AC-03

Every published ballot-accounting field has authoritative provenance.

### AC-04

Participation and abstention remain uncalculated unless verified matching inputs exist.

### AC-05

No electoral-geography relationship is inferred from names alone.

### AC-06

EV-0112 final status accurately reflects capture completeness and review confidence.

### AC-07

No personal voter data or personal absolute path is committed.

### AC-08

The evidence register and territorial data-gap brief reflect the completed work and remaining blockers.

### AC-09

Segment, ranking, narrative, paid media, targeting, and mobilization remain closed.

## 10. Validation

The implementer must run available repository validation and checks equivalent to:

```bash
python scripts/evidence/validate_pilot.py --input research/extracted --pii-self-test

python - <<'PY'
import csv
from pathlib import Path
p = Path('research/curated/electoral-2023/antigua-guatemala-municipal-results-2023.csv')
rows = list(csv.DictReader(p.open(encoding='utf-8')))
assert len(rows) == 14
assert sum(int(r['votes']) for r in rows) == 26091
print('[OK] 14 reviewed rows; visible sum = 26091')
PY

grep -Rni '/Users/' research/curated/electoral-2023 research/electoral-2023 research/evidence-register.md && exit 1 || true
```

Additional validation must confirm:

- second-review coverage for all captured fields;
- equations reconcile against available official totals;
- geography codes and relationships have source records;
- raw and first-review artifacts remain unchanged;
- political-gate language is absent except in explicit prohibition statements.

## 11. Stop Conditions

Stop and record a blocker when:

- the official source cannot be authenticated;
- the same field has unresolved conflicting official values;
- a page or value remains illegible after second review;
- registered electorate and ballot totals refer to different territorial scopes;
- geography records do not contain enough identifiers for an explicit crosswalk;
- completing the task would require inferring a missing electoral fact.

## 12. Definition of Done

This loop is complete when:

- second review of EV-0112 is documented;
- all 14 visible rows are confirmed, corrected, or unresolved;
- ballot-accounting fields are populated only where authoritative evidence exists;
- the `26,091` visible-row sum is reconciled or explicitly remains partial;
- electoral-geography inventory and explicit crosswalks are produced or blockers are documented;
- evidence and gap registers are current;
- validation passes or exceptions are explicit;
- all political gates remain closed.

## 13. Next Decision

After completion, the Campaign Chief may approve one research-only path:

1. acquire missing official ballot-accounting records;
2. acquire or complete official electoral-geography records;
3. proceed to demographic and census crosswalk research.

No segment or territorial-priority decision may be requested solely from this loop.