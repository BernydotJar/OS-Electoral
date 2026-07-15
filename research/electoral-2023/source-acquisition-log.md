# C1-ELEC-2023-002 Source Acquisition Log

Program: `C1-ELEC-2023-002`  
Workstream: EV-0112 independent second review  
Session date: 2026-07-14  
Agent station: Electoral Research  
Status: `SOURCE_FOUND_LOCALLY_AND_SECOND_REVIEW_PREPARED`

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
| 7 | Local source root | `POLITICS_ROOT` expected EV-0112 path | Source PDF found and prepared; SHA-256 recorded in committed manifest | Source blocker resolved for visual second review |
| 8 | Local derived dashboards | `/Users/eduardosacahui/Github-Repos/Padron_Electoral` and `/Users/eduardosacahui/Github-Repos/Eduardo_Sacahui_Campaign/public/territorio_electoral` | Both contain derived Antigua values `vv=26091`, `centros=19`, `jrv=100`, and cite TSE/JED/cartography sources | Registered as discovery aids only; not official source material |

## Why Existing Evidence Is Insufficient

The following committed artifacts describe a first visual review:

- `research/curated/electoral-2023/EV-0112-transcription.md`
- `research/curated/electoral-2023/EV-0112-review-log.md`
- `research/curated/electoral-2023/antigua-guatemala-municipal-results-2023.csv`

They are valid inputs for a comparison ledger, but they cannot serve as the independent page image required to confirm or correct the same fields. Re-reading a prior transcription is not an independent visual review.

## Exact Blocker

The three-page source PDF is now accessible inside `POLITICS_ROOT` and review materials were prepared.

Therefore:

- second-review outcomes may be confirmed against rendered pages;
- first-review vote rows were confirmed, not corrected;
- the derived visible-row sum `26,091` remains unchanged and is now based on confirmed visible rows;
- no turnout, ballot-accounting, geography, segment, narrative, paid media, targeting, or mobilization decision is authorized.

## Derived Dashboard Audit

The local dashboards are recorded in:

`research/electoral-2023/derived-territorio-electoral-source-audit.csv`

They are useful because they preserve pointers to likely underlying sources:

- TSE electoral-roll statistics for 2023-2026;
- Junta Electoral Departamental de Sacatepéquez agreements 1-2023 to 16-2023;
- TSE electoral cartography and 2023 voting-center data;
- Atlas Sacatepéquez v01.2 and Cuaderno Antigua v02.1 as campaign-derived models.

They are not sufficient to close ballot-accounting or geography blockers because they are campaign dashboards, not the original official datasets or PDFs.

## Resume Condition

The EV-0112 visual second-review source blocker is resolved. For audit reproduction, either path may be used:

```text
${POLITICS_ROOT}/EV-0112.pdf
${POLITICS_ROOT}/07_Fichas_Comunitarias/ACUERDO 1-2023 Declarar la validez de la elección de la Corporación Municipal de ANTIGUA GUATEMALA, del Departamento de Sacatepéquez..pdf
```

Then run:

```bash
python scripts/evidence/prepare_ev0112_second_review.py
```

Remaining acquisition work should focus on official ballot accounting and electoral geography.
