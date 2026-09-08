# JOS V1.2 exit-gate audit 7

- Audited SHA: `0cf649925191fc9de2037847ac3048f10397a75a`
- Gate-document revision: `31206bc02df6c7631096bc18970427117725382d`
- Gate document at audited SHA: byte-identical to that revision
- Clone: `/tmp/jos-exit-audit-7`
- Date: 2026-09-08
- Model: Codex (GPT-5)
- Authority consulted: `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md` §9

## Step 1 — Registry, snapshot integrity, determinism tests

Command:

```text
uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py
```

Output:

```text
error: Could not acquire lock
  Caused by: Could not create temporary file
  Caused by: Read-only file system (os error 30) at path "/home/steven/.cache/uv/.tmpxGVtK3"
EXIT_CODE=2
```

This was the anticipated audit-environment cache restriction. Gate-authorized retry:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py
```

Output:

```text
.......................                                                  [100%]
23 passed in 17.30s
EXIT_CODE=0
```

Result: PASS. Registry strictness, registered snapshot hashes, schema checks, and deterministic build tests passed.

## Step 2 — Reproduce committed tables

Command:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run jos data build --output-dir /tmp/jos-audit-rebuild-7
```

Output:

```text
{"build_status": "passed",
 "quality_report": "/tmp/jos-audit-rebuild-7/quality_report.json",
 "table_count": 23,
 "warning_count": 19}
EXIT_CODE=0
```

Command:

```text
diff -rq /tmp/jos-audit-rebuild-7 data/processed
```

Output:

```text
EXIT_CODE=0
```

The empty diff proves the committed processed directory is byte-identical to a cold rebuild at another path.

## Step 3 — Row-level traceability

Random seed: `120007`. Indices below are zero-based data-row indices. Three rows were selected independently from each of the 22 canonical tables.

Command:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run python /tmp/trace_audit.py
```

Material output:

```text
seed=120007; indices=0-based data rows
PASS age_sex.csv indices=[0, 63, 190] -> 15410; 507; 1369
PASS communal_settings.csv indices=[2, 12, 14] -> 15; 6; 19 establishments
PASS commute_modes.csv indices=[60, 78, 86] -> 100; 60; 13200 people
PASS covid_current_summary.csv indices=[1906, 3511, 4338]
  -> 663.27/reported; blank/not_reported; 1/reported
PASS covid_daily_surveillance.csv indices=[4812, 9141, 9848]
  -> blank/not_reported; 38/reported; blank/not_reported
PASS covid_jhu_daily.csv indices=[422, 2558, 3006]
  -> 352/observed; 7/derived; 428/derived
PASS covid_serosurvey_2020.csv indices=[3, 5, 12]
  -> 2.6 percent; 855 individuals; 16 years
PASS covid_weekly_eligible_population.csv indices=[45, 85, 94]
  -> 107800; 107800; 107800 persons/reported
PASS covid_weekly_vaccination.csv indices=[3910, 13894, 18677]
  -> 1 fraction; 6567 doses; 1 dose
PASS derived_controls.csv indices=[15, 16, 36]
  -> 0.0444788372249512; 0.176905995558845; 0.1/derived
PASS employment_sectors.csv indices=[4, 42, 45] -> 239; 2160; 6330
PASS household_types.csv indices=[3, 7, 10] -> 1983; 5463; 2191
PASS housing_controls.csv indices=[35, 63, 162] -> 10; 30; 5.2 percent
PASS parish_age_sex.csv indices=[152, 297, 533] -> 700; 199; 428
PASS parish_population.csv indices=[3, 5, 10]
  -> 35822/3716; 5561/566; 13904/1498
PASS passenger_arrivals.csv indices=[0, 1, 2] -> 196623; 720842; 917465
PASS population_denominators_by_age_band.csv indices=[130, 192, 670]
  -> 2830; 1710; 1090/derived
PASS population_estimates_annual.csv indices=[797, 1904, 2983]
  -> 1090/derived; 1270/derived; 220/observed
PASS population_totals.csv indices=[1, 3, 6] -> 670; 15410; 52150
PASS school_students.csv indices=[0, 3, 4] -> 6220; 1114; 178
PASS workplace_destination.csv indices=[4, 6, 7] -> 24%; 9%; 8%
PASS workplace_sizes.csv indices=[5, 32, 42]
  -> +/positive_less_than; 10/exact; 300/exact
PASS samples=66 tables=22
PASS touched_source_hashes=19
EXIT_CODE=0
```

Each selected locator plus its row keys resolved to one frozen cell or explicit formula. The required special cases were confirmed:

```text
10/20/20 505 - 10/19/20 498 = 7
1/11/22 24217 - 1/10/22 23789 = 428
2013 Female ages 60-64 [570, 610, 580, 540, 530] sum= 2830
2014 Male ages 80-max [...] sum= 1710
2024 Female ages 16-17 [560, 530] sum= 1090
not_reported raw 2022-12-24 MortalityTotalDeaths= ''
```

Thus:

- `not_reported` represents a genuinely blank frozen source cell.
- JHU `derived` rows are exact adjacent cumulative first differences.
- Population denominator rows are exact sums of cited single-age cells.
- The sampled workplace-size `+` cell is preserved as `positive_less_than`, `upper_bound=5`, not converted to zero or a midpoint.
- The M1 tables correctly retain their original count or `censoring` contracts.

`sha256sum` was run over all 19 touched primary snapshots, their four evidence PDFs, and all five evidence-only respiratory PDFs. Every digest matched `data/sources.yaml`. Representative results:

```text
ea51daa...a512b  data/raw/covid19_daily_surveillance_csv/covid19_daily.csv
45663334...630dd  data/raw/covid19_current_summary_csv/covid19_current.csv
f6708113...a382a  data/raw/covid19_weekly_vaccination_csv/covid19_weekly_vaccination.csv
e6234a59...f98c2  data/raw/jhu_csse_confirmed_global_csv/time_series_covid19_confirmed_global.csv
ba1cc6e6...c355  data/raw/sars_cov2_serosurvey_2020_manual_fixture/serosurvey_2020_summary.csv
a74e606e...0dd0d  data/raw/sars_cov2_serosurvey_2020_pdf/prevalence_of_antibodies_2020.pdf
```

The four respiratory editions and winter report were recognized as valid PDFs; their registry hashes also matched.

Result: PASS.

## Step 4 — Measure dictionary

Command:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run python /tmp/dictionary_audit.py
```

Output:

```text
PASS dictionary_rows=92 unique_(table,measure,source_id)=92 semantic_cells_checked=460
PASS cited metadata: sha256/retrieved_at/version match registry for all 92 rows
PASS canonical_source_keys=92 dictionary_source_keys=92
PASS multi_source_keys=4 {
  ('population_totals', 'population_total'): [...2 sources...],
  ('housing_controls', 'households'): [...3 sources...],
  ('age_sex', 'count'): [...2 sources...],
  ('housing_controls', 'overcrowded_households'): [...2 sources...]
}
PASS no "also sourced from" notes
PASS vaccination canonical key is date (not week_ending); event anchoring remains unknown
PASS epidemiology/reportable tables=8 carry reporting_status+upper_bound; M1 schemas retained
PASS prior-audit semantic corrections rechecked
EXIT_CODE=0
```

I independently opened every cited CSV column or grouped PDF page. PDF extraction command:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run --with pypdf python -c \
  'from pypdf import PdfReader; ...'
```

Pages inspected:

- Serosurvey: 1, 2, 5, 6, 7
- Census report: 9, 37, 44, 46, 78, 81
- Labour market: 11, 13
- Population report: 3, 5, 6, 8, 18, 19

The extracted text supported the dictionary’s non-unknown claims, including:

```text
Census p46: 2,079 residents; visitors staying less than one month excluded;
             guest houses under 10 visitors treated as private dwellings
Census p78: "percent of all households in parish"
Census p81: home workers, no-fixed-workplace workers, and outside-Island workers excluded
Labour p11: 8,500 active private-sector undertakings; "+: non-zero less than 5"
Labour p13: private-sector jobs and the sampled 2,160/6,330 values
Population p5: resident population; natural change/net migration over previous 12 months
Serosurvey p5–7: weighting, 438 households/855 individuals, 2.9% unweighted,
                  2.6% weighted, sensitivity adjustment, assay validation universe
```

The prior audit-6 defect is closed at `measure_dictionary.csv:76`: the overcrowding row now identifies “households in the row’s tenure category” as its universe and denominator, supported by the registry title and frozen `Tenure` column.

All earlier blocking findings were rechecked:

- Audit 1: gate file, relocatable output, extraction/version metadata, and registry-title geography are present.
- Audit 2: JHU/serosurvey reporting fields, Census dictionary coverage, corrected serosurvey semantics, unknown vaccination anchoring, honest regimes, and gap warnings are present.
- Audit 3: M1 scope is clarified; mixed-source `age_sex` has separate rows; housing/workplace/communal semantics are transcribed; the key is `date`; “also sourced from” notes are absent.
- Audit 4: five omitted Census blanks are disclosed; flow, density, labour, serosurvey, denominator, and regime defects are closed.
- Audit 5: vaccination fractions, per-100,000 denominators, and population-flow semantics are corrected.
- Audit 6: overcrowding universe and denominator are corrected.

Result: PASS.

## Step 5 — Known gaps

Relevant quality-report output:

```text
data/processed/quality_report.md:131:
- covid daily surveillance anomaly: TestsTotalNegativeTests is excluded because
  917 of 917 cells use SharePoint calculated-field rendering...

data/processed/quality_report.md:135:
- known gap: no intervention/NPI timeline source is frozen or tabulated...

data/processed/quality_report.md:136:
- known gap: no parish-level case series is frozen...

data/processed/quality_report.md:137:
- positive influenza test results are excluded ... pending quality assurance
```

Counts:

```text
intervention/NPI=1
parish-level case=1
positive influenza test=1
TestsTotalNegativeTests=1
```

Searches of processed filenames and headers found no NPI/stringency timeline, parish-case series, influenza-positive series, or `TestsTotalNegativeTests` canonical column.

Direct raw checks:

```text
negative-test rows 917; float;# values 917; float;#0 values 418; special value 1
```

The frozen winter-report page 1 states that positive influenza-test datasets were undergoing validation and quality assurance and had been excluded.

Result: PASS.

## Step 6 — Findings and decision

1. **MINOR — audit-record availability, not a gate-contract failure:** `docs/audits/2026-09-05-v12-exit-gate-audit-{4,5}-sol-FAIL.md:1` and `docs/audits/2026-09-06-v12-exit-gate-audit-6-sol-FAIL.md:1` are absent from this SHA’s tree. They remain reachable in clone history and all their findings were independently rechecked. The brief’s stated 2026-09-05 filename for audit 6 also differs from its historical 2026-09-06 filename.

No BLOCKING or MAJOR findings were found. The default-cache failure is an audit-environment issue resolved by the expressly authorized `UV_CACHE_DIR` prefix.

Final repository-integrity check:

```text
git rev-parse HEAD
0cf649925191fc9de2037847ac3048f10397a75a

git status --porcelain=v1
[empty]
```

### What a stranger would still not understand

The frozen publishers do not define several surveillance event dates or reporting regimes, the vaccination `Date` week anchor, vaccination band denominators, or some population universes. The dictionary now exposes these as `unknown` instead of inventing semantics, so a stranger can distinguish reproducible observations from facts that remain unavailable.

V1.2 EXIT GATE: PASS