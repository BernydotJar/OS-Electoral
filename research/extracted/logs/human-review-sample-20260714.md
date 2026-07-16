# Human Review Sample - Extraction Pilot

Date: 2026-07-14  
Run log: `research/extracted/logs/extraction-run-20260714T175706Z.md`  
Validator: `scripts/evidence/validate_pilot.py --input research/extracted`  
Final gate: PARTIAL

This sample review checks selected extracted values against the visible original files. It does not promote any source to `Accepted`, approve a priority segment, approve a public narrative, or authorize mobilization.

## Final Gate Status

| Source | Gate | Basis |
|---|---|---|
| EV-0111 | PASS | Sampled Antigua Guatemala electoral-roll values match the visible PDF, page numbering is preserved, and the reviewed value `10001437` is a national aggregate total, not PII. |
| EV-0112 | PARTIAL | Pages 1-3 are visually substantive but not machine-readable in this pilot; OCR or manual transcription is still required. |
| EV-0105 | PASS | Sampled workbook cells match the extracted CSV, with row/column provenance preserved. |
| EV-0114 | PARTIAL | Text extraction is usable, but the 399 table records are only table detections. A deterministic 25-detection sample found mixed reliability. |
| Overall pilot | PARTIAL | Extraction is traceable enough for gated review, but EV-0112 and EV-0114 structured-table use remain limited. |
| PII scan | PASS | Scanner self-test avoids false positives for CUILAPA, CUILCO, `Dirección Municipal`, graph-style figures, and `10001437`, while still detecting email, phone, DPI, and CUI label patterns. |
| Config portability | PASS | `config/pilot-sources.yaml` uses `relative_path` under the `POLITICS_ROOT` environment variable and does not commit absolute Politics source paths. |

## EV-0111 - Padron electoral 2026

Original rendered page reviewed: page 2 of `/Users/eduardosacahui/Documents/Politics/07_Fichas_Comunitarias/ESTADISTICAS DEL PADRON ELECTORAL POR DEPARTAMENTO Y MUNICIPIO AL 30 DE ABRIL DEL 2026.pdf`

Output reviewed: `research/extracted/territorio/EV-0111.md`

Sample visible values for `ANTIGUA GUATEMALA`:

| Field | Original visible PDF | Extracted output | Result |
|---|---:|---:|---|
| Ciudadanos alfabetos - varones | 19520 | 19520 | Match |
| Ciudadanos alfabetos - mujeres | 20420 | 20420 | Match |
| Ciudadanos alfabetos - total | 39940 | 39940 | Match |
| Ciudadanos analfabetos - varones | 378 | 378 | Match |
| Ciudadanos analfabetos - mujeres | 1266 | 1266 | Match |
| Ciudadanos analfabetos - total | 1644 | 1644 | Match |
| Vigentes - total | 41584 | 41584 | Match |
| Fallecidos | 7568 | 7568 | Match |

Notes:

- PDF text extraction preserved page numbering from 1 to 28.
- `pdfplumber` did not detect structured tables for this source, so the Markdown is the usable extraction output for the pilot.
- Context review for `10001437`: the value appears on page 28 in the national aggregate row `EN LA REPUBLICA`, after total electorate figures. It is a statistical total, not a person-level identifier and not PII.

## EV-0112 - Acuerdo 01-2023

Original rendered page reviewed: page 1 of `/Users/eduardosacahui/Documents/Politics/07_Fichas_Comunitarias/ACUERDO 1-2023 Declarar la validez de la elección de la Corporación Municipal de ANTIGUA GUATEMALA, del Departamento de Sacatepéquez..pdf`

Output reviewed:

- `research/extracted/territorio/EV-0112.md`
- `research/extracted/manifests/EV-0112.yaml`

Visible original facts:

| Field | Original visible PDF | Extracted output | Result |
|---|---|---|---|
| Agreement number | ACUERDO NUMERO 01-2023 | Not extracted | Expected partial |
| Page count | 3 pages visible in source | `page_count: 3` | Match |
| Text extraction | Page is image/scanned | `[NO_EXTRACTABLE_TEXT]` for pages 1-3 | Correct limitation |

Notes:

- The source is readable visually but not machine-readable in this pilot.
- No OCR was run, per Cycle 1 instructions.
- Manifest status correctly remains `partial` with `possible_scanned_pages: [1, 2, 3]`.
- Because the non-extractable pages contain substantive information, including `ACUERDO NUMERO 01-2023` and visible election-result table content, this source must remain PARTIAL until OCR or manual transcription is reviewed.

## EV-0105 - Fichas comunitarias workbook

Original workbook reviewed: `/Users/eduardosacahui/Documents/Politics/07_Fichas_Comunitarias/2025-10-10__Territorio__Fichas_Comunitarias_Antigua__v01.xlsx`

Output reviewed: `research/extracted/territorio/EV-0105.sheet-Resumen-Comparativo.csv`

Sample cell comparisons from sheet `Resumen Comparativo`:

| Row | Column | Original workbook | Extracted CSV | Result |
|---:|---:|---|---|---|
| 1 | 1 | Aldea/Barrio | Aldea/Barrio | Match |
| 1 | 2 | Población (INE 2018) | Población (INE 2018) | Match |
| 1 | 3 | Empadronados Est. (2023) | Empadronados Est. (2023) | Match |
| 1 | 4 | Nivel de Acceso | Nivel de Acceso | Match |
| 1 | 5 | Prioridad Estratégica | Prioridad Estratégica | Match |
| 2 | 1 | San Felipe de Jesús | San Felipe de Jesús | Match |
| 2 | 2 | 5316 | 5316 | Match |
| 2 | 3 | 3700 | 3700 | Match |
| 2 | 4 | Alta | Alta | Match |
| 2 | 5 | Alta - Turismo/religión | Alta - Turismo/religión | Match |
| 3 | 1 | San Juan del Obispo | San Juan del Obispo | Match |
| 3 | 2 | 4352 | 4352 | Match |
| 3 | 3 | 3000 | 3000 | Match |
| 3 | 4 | Media | Media | Match |
| 3 | 5 | Alta - Agricultura/artesanía | Alta - Agricultura/artesanía | Match |

Notes:

- Workbook, sheet, row, column, column letter, header, value, formula, and blank status are preserved.
- The source remains campaign research and cannot be used to select a priority territory without human verification.

## EV-0114 - PDM-OT Antigua Guatemala

Original rendered pages reviewed:

- page 9 of `/Users/eduardosacahui/Documents/Politics/04_Propuestas/Propuestas estratégicas/Asssets/Plan de Desarrollo Municipal y Ordenamiento Territorial - Antigua Guatemala.pdf`
- page 10 of the same source

Outputs reviewed:

- `research/extracted/municipal-core/EV-0114.md`
- `research/extracted/municipal-core/EV-0114.tables.csv`
- `research/extracted/logs/ev0114-table-detection-gate-20260714.md`

Sample section checks:

| Page | Original visible PDF | Extracted output | Result |
|---:|---|---|---|
| 5 | PDM-OT introduction describing objectives, directives, goals, programs, and norms | Text appears under `## Pagina 5` | Match |
| 9 | Section `2.1.3 Evaluación de la funcionalidad de la regionalización sub municipal actual del municipio` | Text appears under `## Pagina 9` | Match |
| 10 | `Tabla 2 Proyecciones de población` and projection narrative | Text appears under `## Pagina 10` | Match |

Sample table checks:

| Table / page | Original visible PDF | Extracted CSV | Result |
|---|---|---|---|
| Tabla 1, page 9 | La Antigua Guatemala - Ciudad Vieja - Jocotenango - Santa Catarina Barahona - San Antonio Aguas Calientes - San Miguel Dueñas - Alotenango; habitantes 155,383; N.º 3 | `EV-0114.tables.csv`, page 9, table 1 includes the same row and values | Match |
| Tabla 1, page 9 | Santiago Sacatepéquez; habitantes 28,613; N.º 31 | `EV-0114.tables.csv`, page 9, table 2 includes the same row and values | Match |

Notes:

- `pdfplumber` produced 399 table detections for EV-0114. These are not 399 validated reliable tables.
- A deterministic sample of 25 detections was classified as: 8 `VALIDATED_TABLE`, 7 `LIKELY_TABLE`, 6 `FRAGMENTED_TABLE`, 3 `LAYOUT_ARTIFACT`, and 1 `EMPTY_OR_NOISE`.
- Table segmentation is mixed for complex layouts, but row/cell provenance is preserved for review.
- This extraction does not approve campaign promises or territorial priorities.

## Remaining Human Review

Before promoting any of these sources beyond `Extracted, pending validation`, review:

1. EV-0111: additional pages for other demographic cuts.
2. EV-0112: OCR pass or manual transcription of the agreement and results table.
3. EV-0105: remaining community rows and whether the workbook is canonical versus EV-0106.
4. EV-0114: more tables from pages with planning indicators and implementation matrices.
