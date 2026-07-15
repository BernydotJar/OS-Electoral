# EV-0112 Independent Second Review

Program: `C1-ELEC-2023-002`
Evidence ID: `EV-0112`
Review date: 2026-07-14
Reviewer role: Electoral Research — independent review pass
Workstream status: `SECOND_REVIEW_COMPLETED_FROM_RENDERED_SOURCE`
Evidence status after this iteration: `CONFIRMED_SECOND_REVIEW_FOR_VISIBLE_EV0112_FIELDS`

## Review Objective

Independently review all three pages of EV-0112, confirm or correct the 14 visible organization-vote rows, and record every captured legal field in a separate correction ledger without overwriting the first-review artifacts.

## Independence Rule

The following are comparison inputs only:

- `EV-0112-transcription.md`;
- `EV-0112-review-log.md`;
- `antigua-guatemala-municipal-results-2023.csv`.

They cannot serve as the independent visual source. A second review must compare those values against the original three-page PDF or lossless rendered page images.

## Source Availability Check

The required source became available in the local workspace through `POLITICS_ROOT` after the blocker was recorded.

Checked locations:

```text
${POLITICS_ROOT}/EV-0112.pdf
${POLITICS_ROOT}/07_Fichas_Comunitarias/ACUERDO 1-2023 Declarar la validez de la elección de la Corporación Municipal de ANTIGUA GUATEMALA, del Departamento de Sacatepéquez..pdf
```

The source was prepared by:

```bash
POLITICS_ROOT=... python scripts/evidence/prepare_ev0112_second_review.py
```

Preparation created a committed audit manifest:

`research/curated/electoral-2023/EV-0112-second-review-manifest.json`

Additional acquisition attempts and derived dashboard checks are recorded in:

`research/electoral-2023/source-acquisition-log.md`

## Page-by-Page Outcome

| Page | Required review | Independent source available | Outcome |
|---:|---|---|---|
| 1 | agreement identity, authority, legal context, 14 vote rows | Yes | `CONFIRMED` for visible fields |
| 2 | operative articles, mayor, slate, elected offices and names | Yes | `CONFIRMED` for visible fields |
| 3 | term, possession date, entry into force, agreement date, signatories | Yes | `CONFIRMED` for visible fields |

## Vote-Row Coverage

All 14 first-review vote rows are represented in `EV-0112-corrections.csv` and have the second-review status:

```text
CONFIRMED / CONFIRMED_FROM_RENDERED_SOURCE
```

This status means:

- the first-review value remains unchanged;
- the value was independently confirmed against rendered pages from the source PDF;
- the value was not contradicted;
- no correction was made;
- the row may be treated as confirmed for the visible EV-0112 result table.

The existing derived visible-row sum remains:

```text
26,091
```

It is now a derived sum of second-review-confirmed visible EV-0112 vote rows. This iteration does not reclassify it as a printed official total, valid-vote total, ballots cast, participation, or turnout.

## Field-Group Coverage

The correction ledger also covers agreement number, issuing authority, municipality, election date association, electoral-system context, validity declaration, mayor and slate, elected corporation members, term length, possession date, entry into force, agreement date, and signatories.

All visible field groups were confirmed except `election_date`, which was classified as `NOT_PRESENT` because the reviewed agreement pages do not visibly print `2023-06-25`.

## Automated Preparation

The repository now contains `scripts/evidence/prepare_ev0112_second_review.py`.

When the PDF becomes available, the script will resolve the portable source path, verify three pages, compute hashes, render at 300 DPI, run assistive OCR using `spa+eng`, and create a local review manifest without modifying curated evidence.

OCR output is never accepted without visual review.

## Acceptance Evaluation

| Criterion | Status | Basis |
|---|---|---|
| AC-01: all 14 rows receive a second-review status | PASS | All are explicitly `CONFIRMED` in the correction ledger |
| AC-02: 26,091 remains correctly labeled | PASS | Preserved as a derived visible-row sum, now from second-review-confirmed rows |
| AC-06: EV-0112 final status is accurate | PASS | Visible EV-0112 fields are second-review confirmed; ballot accounting and geography remain unavailable |
| AC-07: no PII or personal absolute path | PASS | Portable paths and aggregate/legal records only |
| Independent visual confirmation | PASS | Rendered pages generated from the source PDF were reviewed |
| Promotion beyond partial | PARTIAL | Visible EV-0112 fields confirmed; participation and geography still blocked |
| Political gates | PASS — CLOSED | No segment, ranking, narrative, media, targeting, or mobilization output |

## Gate Decision

```text
SECOND_REVIEW_ATTEMPT: PASS
EV-0112 EVIDENCE STATUS: CONFIRMED_SECOND_REVIEW_FOR_VISIBLE_FIELDS
VOTE ROWS CONFIRMED: 14
VOTE ROWS CORRECTED: 0
VOTE ROWS UNRESOLVED: 0
SOURCE STILL REQUIRED TO RESUME OTHER WORKSTREAMS: OFFICIAL BALLOT ACCOUNTING AND ELECTORAL GEOGRAPHY
```

The EV-0112 visual second review is complete for visible fields. Separate workstreams still need official ballot-accounting and electoral-geography sources.
