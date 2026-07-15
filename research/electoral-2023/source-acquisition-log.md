# C1-ELEC-2023-002 Source Acquisition Log

Program: `C1-ELEC-2023-002`  
Workstream: EV-0112 independent second review  
Session date: 2026-07-14  
Agent station: Electoral Research  
Status: `BLOCKED_SOURCE_UNAVAILABLE_IN_WORKSPACE`

## Required Source

| Field | Value |
|---|---|
| Evidence ID | `EV-0112` |
| Authority | Junta Electoral Departamental de Sacatepéquez |
| Document | `ACUERDO NUMERO 01-2023` |
| Expected pages | 3 substantive image-based pages |
| Portable path | `${POLITICS_ROOT}/07_Fichas_Comunitarias/ACUERDO 1-2023 Declarar la validez de la elección de la Corporación Municipal de ANTIGUA GUATEMALA, del Departamento de Sacatepéquez..pdf` |
| Alternative workspace path | `${POLITICS_ROOT}/EV-0112.pdf` |
| Required use | Independent visual second review; OCR is assistive only |

## Acquisition Attempts

| Attempt | Channel | Query or check | Result | Decision |
|---:|---|---|---|---|
| 1 | Workspace filesystem | Searched `external/politics/` recursively | Only `.gitkeep`; PDF absent | Source unavailable locally |
| 2 | Thin Git checkout | Searched tracked files for EV-0112 source PDF | Repository contains derived text/CSV only | Do not treat derivatives as independent visual source |
| 3 | GitHub connector | Repository code search for the exact agreement title and number | No committed PDF match | Source not versioned in GitHub |
| 4 | ChatGPT File Library | Exact title, agreement number, authority, mayor name, and vote-table terms | No matching PDF | Source not available through File Library |
| 5 | Official-domain web discovery | Exact-title and authority searches restricted to `tse.org.gt` | No indexed official document found | No authenticated public copy acquired |
| 6 | Broad web discovery | Agreement number, organization names, and visible vote values | Secondary summaries found; no source document | Secondary material is not promoted to official evidence |

## Why Existing Evidence Is Insufficient

The following committed artifacts describe a first visual review:

- `research/curated/electoral-2023/EV-0112-transcription.md`
- `research/curated/electoral-2023/EV-0112-review-log.md`
- `research/curated/electoral-2023/antigua-guatemala-municipal-results-2023.csv`

They are valid inputs for a comparison ledger, but they cannot serve as the independent page image required to confirm or correct the same fields. Re-reading a prior transcription is not an independent visual review.

## Exact Blocker

The three-page source PDF, or lossless rendered images of all three pages, must be accessible inside `POLITICS_ROOT`.

Until then:

- all second-review outcomes remain `UNRESOLVED`;
- no first-review value is corrected or promoted;
- EV-0112 remains `PARTIAL_REVIEWED_CAPTURE`;
- the derived visible-row sum `26,091` remains unchanged and unpromoted;
- no turnout, ballot-accounting, geography, segment, narrative, paid media, targeting, or mobilization decision is authorized.

## Resume Condition

Resume this workstream automatically when either path exists:

```text
${POLITICS_ROOT}/EV-0112.pdf
${POLITICS_ROOT}/07_Fichas_Comunitarias/ACUERDO 1-2023 Declarar la validez de la elección de la Corporación Municipal de ANTIGUA GUATEMALA, del Departamento de Sacatepéquez..pdf
```

Then run:

```bash
python scripts/evidence/prepare_ev0112_second_review.py
```
