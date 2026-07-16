# Final Ballot Accounting Reconciliation 2023

Program: `C1-ELEC-2023-005`
Station: Electoral Research
Territory: Antigua Guatemala, Sacatepequez
Election: Corporacion Municipal 2023
Status: `PARTIAL_RECONCILIATION_WITH_IDENTIFIED_MISSING_ACTA`

## Source Authentication

The exact preliminary TREP cut was authenticated without committing raw downloads.

| Source | URL | Encoding | SHA-256 |
|---|---|---|---|
| `ultimoCorte.json` | `https://primeraeleccion.trep.gt/ext/jsonData_gtm2023/ultimoCorte.json` | plain | `4f856d24f0ffebca83696d89a64abba634fae8bd0582ca710f233e65aa07bffa` |
| `gtm2023_datos.json` | `https://primeraeleccion.trep.gt/ext/jsonData_gtm2023/1687736870/1688050101/gtm2023_datos.json` | gzip | raw `c79261df959300834b64a947330999aeab34590a216338ac253a468a425cdd4d`; decoded `55738c7152f01df4907633bd8338bf40b717d193fe652fe6523d29eac2a8527c` |
| `gtm2023_tc4_e2.json` | `https://primeraeleccion.trep.gt/ext/jsonData_gtm2023/1687736870/1688050101/gtm2023_tc4_e2.json` | gzip | raw `9ab26dc34ca151600c97c89359ee36db9f970f2a559c0abcac9994759808d4c4`; decoded `ac3c9630682a00496c127ca51abb86fb4d6afcf06d092cafc4ac61048ad27654` |

Cut metadata:

```text
dpVersion = 1687736870
dir = 1687736870/1688050101
corteUt = 1688050101
terminadas = 121227
hash = 814045fd499aba9958913cf2e899a049
```

The `tc4` node identifies Corporacion Municipal. The `e2` node identifies Sacatepequez, and the `m1` node identifies Antigua Guatemala.

## Preliminary TREP Accounting

The authenticated TREP preliminary aggregate remains:

```text
actas_total = 100
actas_captured = 100
actas_counted = 99
registered_electorate = 39,099
valid_preliminary = 25,827
null_preliminary = 912
blank_preliminary = 89
emitted_preliminary = 26,828
```

Preliminary identity only:

```text
25,827 + 912 + 89 = 26,828
```

These values are not promoted as definitive final accounting.

## Missing Acta Result

The department detail JSON identifies exactly one Antigua Guatemala mesa with a preliminary non-counted status:

```text
seccion = 538
mesa = 5401
status = 1
obs = Acta ilegible
lNominal = 380
imgSha = 93301a333039a54d82a4bf73117e3838765c6299985534b7e55ce87aa94e7072
```

The image URL was reachable and the downloaded image SHA-256 matched `imgSha`. The image is not committed or transcribed because it contains visible personal signer/fiscal information and TREP marks the acta illegible.

Investigation status:

```text
IDENTIFIED_OFFICIAL
```

This means the captured-but-not-counted TREP mesa is identified from official preliminary TREP status data. It does not mean the final votes from that mesa are accepted from TREP.

## Conflict Comparison

The definitive EV-0112 visible organization-row sum remains:

```text
EV-0112 visible organization vote sum = 26,091
```

The preliminary TREP valid/party-vote-like total remains:

```text
TREP preliminary valid/party-vote-like total = 25,827
```

Conflict:

```text
26,091 - 25,827 = 264
```

The organization-by-organization comparison between EV-0112 and preliminary TREP also sums to `264`. This comparison bounds the conflict but does not by itself prove final ballot-accounting categories.

## Promoted Fields

Only two fields are carried in `final-ballot-accounting-fields-2023.csv`:

- `registered_electorate = 39,099`, official denominator from EV-0139;
- `visible_organization_vote_sum = 26,091`, confirmed derived visible sum from EV-0112.

Unresolved final fields remain:

- ballots cast;
- printed valid-vote total;
- null votes;
- blank votes;
- challenged or other categories;
- participation;
- abstention.

## Outcome

`PARTIAL_RECONCILIATION_WITH_IDENTIFIED_MISSING_ACTA`

Resume when a definitive TSE/JED source provides final municipal accounting categories or a competent final reconciliation for mesa `5401`.

## Political Gate

This artifact does not authorize segment selection, territorial ranking, narrative, paid media, targeting, field mobilization, public promises, or attacks.
