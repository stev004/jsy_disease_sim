# Independent V1.2 exit-gate audit

- Audited SHA: `71e408ca75c1477851fc8b5a8e8b5337a3429ac8`
- Gate document revision: commit `71e408ca75c1477851fc8b5a8e8b5337a3429ac8`; blob `a35321d01afd3dbe7a6c635b9cffbbf568c32c78`
- Clone: `/tmp/jos-exit-audit-4`
- Date: 2026-09-05
- Model: OpenAI Codex (GPT-5)
- Mode: independent cold-start, read-only
- Repository state after audit: clean; diff stat empty

## Step 1 — Registry, snapshot integrity, and determinism tests

The literal command encountered the runner’s read-only default `uv` cache:

```console
$ uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py
error: Could not acquire lock
  Caused by: Could not create temporary file
  Caused by: Read-only file system (os error 30) at path "/home/steven/.cache/uv/.tmpc9clku"
```

Retried with the cache redirected as instructed by `AGENTS.md`:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py
.......................                                                  [100%]
23 passed in 19.22s
```

Result: passed after an environment-only cache redirect.

## Step 2 — Reproducibility of committed tables

The literal build command hit the same cache restriction:

```console
$ uv run jos data build --output-dir /tmp/jos-audit-rebuild-4
error: Could not acquire lock
  Caused by: Could not create temporary file
  Caused by: Read-only file system (os error 30) at path "/home/steven/.cache/uv/.tmp1G0mmJ"
```

Cache-redirected build:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run jos data build --output-dir /tmp/jos-audit-rebuild-4
/home/steven/.config/matplotlib is not a writable directory
Matplotlib created a temporary cache directory at /tmp/matplotlib-pfhpveja ...
{"build_status": "passed", "quality_report": "/tmp/jos-audit-rebuild-4/quality_report.json", "table_count": 23, "warning_count": 14}
```

Required comparison:

```console
$ diff -rq /tmp/jos-audit-rebuild-4 data/processed
```

Output: empty; exit code 0.

Result: passed. The rebuilt directory is byte-identical to the committed processed data.

## Step 3 — Row-level traceability

I conservatively audited all 22 canonical input/M1 tables used by the dictionary. Seed: `2026090504`; Python `random.Random`; indices are zero-based data-row indices.

```text
covid_daily_surveillance [3671, 5428, 6491]
covid_current_summary [383, 2428, 4635]
covid_jhu_daily [1610, 2088, 2444]
covid_serosurvey_2020 [1, 6, 9]
covid_weekly_vaccination [492, 2480, 15102]
covid_weekly_eligible_population [13, 53, 114]
population_estimates_annual [42, 640, 2577]
population_denominators_by_age_band [75, 499, 709]
population_totals [0, 5, 8]
age_sex [167, 185, 207]
parish_population [4, 7, 11]
parish_age_sex [150, 559, 574]
household_types [1, 5, 8]
housing_controls [1, 42, 57]
employment_sectors [6, 31, 41]
workplace_destination [3, 5, 7]
commute_modes [22, 71, 75]
communal_settings [0, 5, 7]
derived_controls [0, 15, 18]
workplace_sizes [12, 41, 47]
school_students [1, 4, 5]
passenger_arrivals [0, 1, 2]
```

Independent trace command:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run python /tmp/jos_audit4_trace.py
```

Representative output:

```text
PASS covid_daily_surveillance[3671] ... raw='227337' value='227337' status=reported unit=tests
PASS covid_daily_surveillance[5428] ... raw='-1' value='' status=not_reported unit=per_100000
PASS covid_jhu_daily[2444] ... raw/calculation=316-316=0 value=0 status=reported unit=cases observation=derived
PASS covid_serosurvey_2020[9] ... fixture=74.94 PDF=pdf_page_7 status=reported unit=percent
PASS covid_weekly_vaccination[492] ... raw='' value='' status=not_reported unit=percent
PASS population_denominators_by_age_band[709] ... sum ages 16..100 female=44870 status=reported unit=persons
PASS derived_controls[0] ... 5401/103267=0.0523013160060813
PASS workplace_sizes[41] ... fixture='10' PDF=pdf_page_11 censoring=exact unit=undertakings
sample rows traced=66/66; row source hashes matched=66/66
```

Thus the required `not_reported` semantics were confirmed from raw blank/`-1` cells, and derived JHU differences, age-band sums, and M1 shares were recomputed.

PDF text was extracted directly using:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run --with pypdf python -c \
  'from pypdf import PdfReader; ...'
```

Pages opened were serosurvey 1, 2, 4, 5, 6, 7; population 3, 8, 18, 19; Census 9, 37, 44, 46, 78, 81; labour 11, 13; and influenza 1. The sampled fixture values and units were present on their cited pages.

All touched source IDs were checked with `sha256sum`. Representative results:

```text
ea51daa689a851af6fedb45e1520abfc235bc350113cbde1cd49b880d7aa512b  .../covid19_daily.csv
e6234a59eec4359d2577358b5220e1a7e3da74c162913cdb7d882db1413f98c2  .../time_series_covid19_confirmed_global.csv
a74e606e5ef16544a763146249b42fba8ae61fb00526982793c6f9fbc300dd0d  .../prevalence_of_antibodies_2020.pdf
e4f8c38e96330fc60af584b8fae75d3011d29f4992bb2d8031e8baa192a91095  .../R.45-2023.pdf
647cdf53997f66faa36f41036ec9fd904ae729d8bbccc01a97eb23cb5e398fe0  .../R-Labour-Market-June-2025.pdf
```

All 66 canonical `source_sha256` values matched the actual frozen files and registry. The five respiratory PDFs also matched their registry hashes and had valid PDF magic.

Row-contract scan:

```text
canonical_tables_checked=22
row_contract_errors=[]
workplace_sizes censoring=True upper_bound=True
commute_modes censoring=True upper_bound=True
```

Result: passed for all 66 sampled rows.

## Step 4 — Measure dictionary

Mechanical audit of all dictionary rows:

```text
dictionary_rows=92
unique_triples=92
duplicate_triples=0
canonical_triples=92
missing_dictionary=[]
extra_dictionary=[]
citation_metadata_or_actual_hash_mismatches=[]
blank_semantic_cells=[]
multi_source_pairs={
  'age_sex:count': ['census_2021_age_gender_csv', 'jersey_population_2024_manual_fixture'],
  'housing_controls:households': [
    'census_2021_household_property_type_csv',
    'census_2021_household_type_tenure_csv',
    'census_2021_housing_persons_bedrooms_csv'
  ],
  'housing_controls:overcrowded_households': [
    'census_2021_overcrowding_csv',
    'census_2021_report_manual_fixture'
  ],
  'population_totals:population_total': [
    'census_2021_parish_population_density_csv',
    'jersey_population_2024_manual_fixture'
  ]
}
also_sourced_occurrences=0
covid_weekly_vaccination.csv date_present=True week_ending_present=False
covid_weekly_eligible_population.csv date_present=True week_ending_present=False
```

The source-aware key, hashes, retrieval dates, versions, prior mixed-period `age_sex` defect, vaccination key, and “also sourced from” defects are closed.

The semantic audit failed, however. Direct source inspection produced:

```text
census_2021_household_type_tenure_csv blank cells=[
 (8, 'Couple (one pensioner)', 'Registered lodging house'),
 (8, 'Couple (one pensioner)', 'Private lodging'),
 (10, 'Two or more pensioners', 'Registered lodging house')
]
census_2021_household_property_type_csv blank cells=[
 (8, 'Temporary Structure/Tent, boat or PortakabinTM', 'Social housing rent'),
 (8, 'Temporary Structure/Tent, boat or PortakabinTM', 'Qualified private rent')
]
```

Dictionary lines 61 and 63 instead assert `blank cells not present in the frozen CSV`; pipeline lines 1652–1656 and 1683–1687 silently omit them.

Other unsupported or incorrect semantic cells are listed in the findings below. Result: failed.

## Step 5 — Known gaps

```text
quality warning 'no intervention/NPI timeline source is frozen or tabulated': PASS
quality warning 'no parish-level case series is frozen': PASS
quality warning 'positive influenza test results are excluded': PASS
quality warning 'TestsTotalNegativeTests is excluded': PASS
processed filenames containing 'npi': []
processed filenames containing 'intervention': []
processed filenames containing 'stringency': []
processed filenames containing 'influenza': []
covid_daily_surveillance.csv parish_column=False parish_values=0
covid_current_summary.csv parish_column=False parish_values=0
covid_jhu_daily.csv parish_column=False parish_values=0
negative-tests canonical measures=[]
raw TestsTotalNegativeTests float;# rendered=917/917
```

Influenza PDF page 1 independently says the positive-test datasets were excluded pending validation and quality assurance. No NPI timeline, parish case series, influenza-positive series, or negative-test measure was fabricated.

Result: passed.

## Prior FAIL findings re-verification

- Audit 1: gate-document presence, relocatable artifacts, measure-level extraction/revision metadata, and registry-backed geography are closed.
- Audit 2: JHU/serosurvey reporting fields, source-aware Census dictionary coverage, vaccination date uncertainty, and known-gap warnings are closed. The reporting-regime problem is only partially closed; daily rate/death rows still cite non-resolving or irrelevant prior/since placeholders.
- Audit 3: M1 reporting-field wording, mixed-period `age_sex` dictionary rows, cited Census denominators/exclusions, vaccination `date`, and “also sourced from” removal are closed.

## Findings

1. **BLOCKING — Contract not met:** `data/processed/measure_dictionary.csv:61` and `:63` falsely state that blank cells are absent. Five blank household/property cells exist at the cited frozen sources (`2021-census-householdtype-tenure.csv:8,10` and `2021-census-householdtype-propertytype.csv:8`) and are silently discarded by `data_pipeline.py:1652-1656,1683-1687`. Their meaning and exclusion are undocumented.

2. **BLOCKING — Contract not met:** `measure_dictionary.csv:49-50` calls `natural_change` and `net_migration` “year-end 2024 population estimate[s].” The frozen report defines them as rolling 12-month flows from year-end 2023 to year-end 2024, not point-in-time population estimates.

3. **BLOCKING — Contract not met:** `measure_dictionary.csv:58` records the denominator of `density_person_km2` as `not applicable`, although the cited frozen column explicitly measures persons per square kilometre. The denominator is area in km².

4. **BLOCKING — Contract not met:** `measure_dictionary.csv:43` places the measure value, `107,800 constant`, in the denominator field for the `eligible_population` count. Under the gate’s own clarification, a count has no denominator. `measure_dictionary.csv:91` similarly invents a denominator reference for a bedrooms difference, which is not a ratio.

5. **BLOCKING — Contract not met:** `measure_dictionary.csv:79,81` uses `population_universe=unknown` despite the cited labour PDF explicitly identifying private-sector jobs on page 13 and active private-sector undertakings employing staff—including self-employed sole traders—on page 11.

6. **BLOCKING — Contract not met:** `measure_dictionary.csv:23` asserts household- and individual-level weighting but cites only PDF page 6. That detail is on page 5; the cited page supports the 2.6% weighted result but not the asserted weighting levels.

7. **BLOCKING — Contract not met:** `measure_dictionary.csv:7,12` asserts a prior/since-July-2020 reporting regime for the seven-day rate and deaths. Line 7 cites no such columns; line 12 uses literal `...priorto1July2020` placeholders that are not frozen CSV column names. Neither locator supports a regime for its measure.

8. **MINOR — Environment only:** the literal `uv run` commands cannot create locks in the runner’s default cache. Redirecting `UV_CACHE_DIR` makes both commands succeed without repository changes.

## What a stranger would still not understand

A stranger would not know what the omitted Census household/property blanks mean, the correct time basis of natural-change and migration flows, the denominators of density and derived difference/count measures, the published labour universes, or the reporting regime applicable to the daily rate and death series. Those are source-observation semantics required by the gate, not disagreements with the contract’s wording.

V1.2 EXIT GATE: FAIL — the measure dictionary falsely says five frozen Census household/property cells are not blank while the pipeline silently omits them.