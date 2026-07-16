# EV-0114 Table Detection Gate

Date: 2026-07-14  
Source: `research/extracted/municipal-core/EV-0114.tables.csv`  
Method: deterministic sample of 25 detections, evenly spaced across the sorted `(page, table_index)` detections.  
Purpose: classify table detections before treating them as reliable structured data.

Important: EV-0114 has **399 table detections**, not 399 validated tables. The pilot must not treat all detections as trustworthy structured tables.

## Classification Labels

- `VALIDATED_TABLE`: coherent table structure in the extraction sample; still needs deeper review before production use.
- `LIKELY_TABLE`: appears to be a real table, but structure is incomplete or should be checked visually.
- `FRAGMENTED_TABLE`: real table content appears split, merged, or structurally degraded.
- `LAYOUT_ARTIFACT`: prose, map labels, bullets, or layout text interpreted as a table.
- `EMPTY_OR_NOISE`: empty, near-empty, or unusable extraction.

## Deterministic Sample

| Sample | Detection Index | Page | Table | Cells | Snippet | Classification | Gate Note |
|---:|---:|---:|---:|---:|---|---|---|
| 1 | 1 | 9 | 1 | 18 | `MUNICIPIO / Habitantes / N.º / Ciudades Intermedias` | `FRAGMENTED_TABLE` | Header/category fragment from Tabla 1; usable only with adjacent detections. |
| 2 | 18 | 11 | 10 | 11 | `Santa Ana / Pozo / Si / No` | `LIKELY_TABLE` | Looks like water-network locality table fragment; visual check needed. |
| 3 | 34 | 17 | 2 | 28 | `Primaria / 7-12 / 6462 / 5217 / 2858 / 125%` | `VALIDATED_TABLE` | Coherent education coverage table sample. |
| 4 | 51 | 25 | 1 | 18 | empty snippet | `EMPTY_OR_NOISE` | No useful visible text in sampled cells. |
| 5 | 67 | 46 | 4 | 3 | `Sector primario / Agricultura / El café, aguacate y maíz` | `LIKELY_TABLE` | Real sector content, but too few cells for validated structure. |
| 6 | 84 | 51 | 7 | 6 | `San Miguel Dueñas / 4.38 / 2.74 / 3.15 / 3.87 / 4.24` | `LIKELY_TABLE` | Numeric row likely from a comparative table; visual header check needed. |
| 7 | 101 | 67 | 2 | 31 | `Identidad cultural / Desarrollo económico / Conservación del patrimonio` | `FRAGMENTED_TABLE` | Multi-column priorities content split awkwardly. |
| 8 | 117 | 75 | 6 | 2 | `tener que dar cobertura a toda la zona conurbada` | `LAYOUT_ARTIFACT` | Sentence fragment, not a table. |
| 9 | 134 | 77 | 6 | 4 | `El municipio cuenta con poca capacidad...` | `LAYOUT_ARTIFACT` | Prose block detected as table. |
| 10 | 150 | 79 | 3 | 2 | `PRIORIDADES / NACIONALES` | `FRAGMENTED_TABLE` | Heading fragment only. |
| 11 | 167 | 90 | 1 | 2 | `Problema central / Causas` | `LIKELY_TABLE` | Likely diagnostic table start; insufficient sampled cells. |
| 12 | 183 | 94 | 1 | 36 | `HUELLA / VIVIENDAS ANUALES / SUBTOTAL INCREMENTO / DENSIDAD` | `VALIDATED_TABLE` | Coherent projection/planning table sample. |
| 13 | 200 | 128 | 1 | 12 | `SUBCATEGORIAS / MINIMO / MAXIMO / MEDIO` | `VALIDATED_TABLE` | Coherent threshold/range table sample. |
| 14 | 217 | 144 | 1 | 80 | `DESPLAZAMIENTOS / SECTOR NOMBRE / RES. ALTO / RES. ASEQU.` | `FRAGMENTED_TABLE` | Real structured content, but extraction merges headers and values. |
| 15 | 233 | 158 | 3 | 8 | `Aparcamiento / Vial unidireccional: 2.2 m` | `LIKELY_TABLE` | Real design/roadway content; structure needs visual check. |
| 16 | 250 | 160 | 1 | 24 | `VÍA LOCAL PRINCIPAL / Anchura comprendida entre 7.5-21 m` | `VALIDATED_TABLE` | Coherent roadway classification table sample. |
| 17 | 266 | 205 | 2 | 48 | `ACCIONES, PROGRAMAS Y PROYECTOS / ÁMBITO / RESPONSABLES / FUENTES` | `VALIDATED_TABLE` | Coherent implementation matrix sample. |
| 18 | 283 | 208 | 2 | 3 | `¿Está provocando algún conflicto social?` | `LAYOUT_ARTIFACT` | Question text detected as table. |
| 19 | 299 | 210 | 1 | 1260 | `EJECUCIÓN / EFICIENCIA / EFICACIA` | `VALIDATED_TABLE` | Large follow-up matrix; structurally coherent but should be sampled further before production. |
| 20 | 316 | 214 | 11 | 9 | `9 / DMP La Antigua Guatemala / Ana Lucia Paiz` | `LIKELY_TABLE` | Participant/stakeholder row; do not treat as PII by label alone. |
| 21 | 333 | 215 | 10 | 9 | `41 / Antigua Viva / Willy Posadas` | `LIKELY_TABLE` | Participant/stakeholder row; needs source-context review. |
| 22 | 349 | 216 | 6 | 5 | `Disminución / de la / pobreza / protección / social` | `FRAGMENTED_TABLE` | Phrase split into cells. |
| 23 | 366 | 218 | 1 | 1476 | `Prioridades / Metas / Temática / Indicadores / Valor / Fuente` | `VALIDATED_TABLE` | Large indicator matrix; good candidate for deeper validation. |
| 24 | 382 | 219 | 3 | 2 | `Metas Estratégicas / de Desarrollo (MED)` | `FRAGMENTED_TABLE` | Heading fragment only. |
| 25 | 399 | 221 | 1 | 8 | `Siglas, acrónimos y abreviaturas / Significado` | `VALIDATED_TABLE` | Coherent acronym table sample. |

## Sample Summary

| Classification | Count |
|---|---:|
| `VALIDATED_TABLE` | 8 |
| `LIKELY_TABLE` | 7 |
| `FRAGMENTED_TABLE` | 6 |
| `LAYOUT_ARTIFACT` | 3 |
| `EMPTY_OR_NOISE` | 1 |

## Gate Decision

EV-0114 table extraction is `PARTIAL` for structured-table reliability:

- The text extraction is usable and page-provenanced.
- Some table detections are usable candidates.
- The 399 detections must be filtered and validated before table-level facts are used in downstream RAG answers.
- No segment, narrative, paid-media audience, or territorial priority is approved from this table extraction.
