<!-- IMMUTABLE AUDIT RECORD. Independent cold-start auditor: Codex gpt-5.6-sol@high (self-reports as "OpenAI Codex (GPT-5)"), read-only, fresh clone /tmp/jos-exit-audit-3 at 446545377a49150b6dcb83f1575af023838178f7, brief ~/jos-v12-exit-audit-3-brief.md, launched 2026-09-05 02:25 local via fm.sh exec, report written ~02:49. Filed verbatim by the director. Verdict: FAIL (5 blocking + 2 major; steps 1, 2, 5 PASS; 66/66 sampled rows traced). -->

# V1.2 exit-gate audit

- Audited SHA: `446545377a49150b6dcb83f1575af023838178f7`
- Clone: `/tmp/jos-exit-audit-3`
- Date: 2026-09-05
- Model: OpenAI Codex (GPT-5)
- Mode: independent cold-start, read-only
- Worktree after audit: clean; no tracked files modified

## Step 1 — Registry, snapshot integrity, determinism tests

Command:

```console
$ uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py
.......................                                                  [100%]
23 passed in 16.26s
```

Result: PASS.

## Step 2 — Rebuild committed tables

Commands:

```console
$ uv run jos data build --output-dir /tmp/jos-audit-rebuild
{"build_status": "passed", "quality_report": "/tmp/jos-audit-rebuild/quality_report.json", "table_count": 23, "warning_count": 14}

$ diff -rq /tmp/jos-audit-rebuild data/processed
```

The second command produced no output and exited 0. The rebuild is byte-identical to `data/processed`.

Result: PASS.

## Step 3 — Row-level traceability

I used seed `20260905`, Python’s `random.Random`, zero-based indices, and continued one PRNG across the declared table order. I sampled three rows from every calibration/M1 table, including the full family implied by the Census ellipsis—22 tables and 66 rows total.

Selection command shape:

```console
$ uv run python -
seed=20260905
covid_daily_surveillance: [1370, 4426, 9623]
covid_current_summary: [2577, 4203, 4748]
covid_jhu_daily: [431, 1949, 3201]
covid_serosurvey_2020: [3, 10, 11]
covid_weekly_vaccination: [1344, 6784, 9768]
covid_weekly_eligible_population: [14, 32, 57]
population_estimates_annual: [48, 318, 1786]
population_denominators_by_age_band: [595, 604, 703]
population_totals: [2, 3, 5]
age_sex: [21, 49, 169]
parish_population: [0, 6, 10]
parish_age_sex: [126, 299, 681]
household_types: [0, 6, 9]
housing_controls: [9, 12, 144]
employment_sectors: [6, 24, 33]
workplace_destination: [0, 1, 4]
commute_modes: [25, 71, 75]
communal_settings: [2, 6, 8]
derived_controls: [13, 32, 35]
workplace_sizes: [5, 8, 29]
school_students: [2, 3, 4]
passenger_arrivals: [0, 1, 2]
```

An independent `csv.DictReader` tracer resolved each locator by row key and raw column, without calling pipeline extraction functions. Representative output:

```text
covid_daily_surveillance:csv_row=1372 raw='182777' canonical=182777 status=reported PASS
covid_daily_surveillance:csv_row=4428 raw='-1' canonical='' status=not_reported PASS
covid_daily_surveillance:csv_row=9625 raw='' canonical='' status=not_reported PASS
covid_jhu_daily:csv_row=3203 raw='57541-57541' canonical=0 observation_status=derived PASS
covid_serosurvey_2020:csv_row=5 raw='2.6' locator=pdf_page_6 PASS
covid_weekly_vaccination:csv_row=1346 raw='' status=not_reported PASS
population_denominators_by_age_band:csv_row=597 sum(ages 70..74)=2500 canonical=2500 PASS
derived_controls:csv_row=34 recompute=5258/13991=0.375813022657423 PASS
derived_controls:csv_row=37 recompute=917465/365=2513.60273972603 PASS
```

All 66 sampled values traced successfully. Units were confirmed from the raw column/page together with the corresponding dictionary measure. The required blank/`-1` preservation and multiple derived recomputations were confirmed.

PDF extraction command:

```console
$ uv run --with pypdf python -
Installed 1 package in 5ms
```

The inline reader extracted serosurvey pages 1, 2, 4, 6 and 7; Census pages 9, 37, 44, 46, 78 and 81; population pages 3, 8, 18 and 19; labour pages 11 and 13; and influenza-report page 1. Sampled serosurvey, household, communal, workplace-destination, population and workplace-size values matched those pages.

Hashes were checked with `sha256sum` for every sampled `source_id` and manual fixture’s evidence PDF. All matched both `data/sources.yaml` and canonical `source_sha256`. Representative output:

```text
ea51daa...aa512b  data/raw/covid19_daily_surveillance_csv/covid19_daily.csv
e6234a59...3f98c2  data/raw/jhu_csse_confirmed_global_csv/time_series_covid19_confirmed_global.csv
a74e606e...00dd0d  data/raw/sars_cov2_serosurvey_2020_pdf/prevalence_of_antibodies_2020.pdf
1b7b14fa...1e368  data/raw/annual_population_estimates_by_age_sex_csv/annual-population-estimates-by-age-and-sex.csv
e4f8c38e...a91095  data/raw/census_2021_report_pdf/R.45-2023.pdf
```

Row-contract scan:

```console
$ uv run python -
age_sex.csv: FAIL missing=reporting_status,upper_bound
communal_settings.csv: FAIL missing=reporting_status,upper_bound
commute_modes.csv: FAIL missing=reporting_status
...
parish_age_sex.csv: FAIL missing=reporting_status,upper_bound
parish_population.csv: FAIL missing=reporting_status,upper_bound
...
```

The explicitly enumerated Census tables therefore fail the required row contract, despite their sampled numbers being traceable.

Result: FAIL.

## Step 4 — Measure dictionary

Command and mechanical output:

```console
$ uv run python -
rows=87 unique_table_measure_pairs=87
blank_required_cells=[]
citation_metadata_or_hash_mismatches=[]
event_date_definition: unknown=31, asserted=56
population_universe: unknown=74, asserted=13
denominator: unknown=13, asserted=74
reporting_regime: unknown=76, asserted=11
known_exclusions: unknown=59, asserted=28
```

I reviewed all 87 rows, grouping repeated citations to the same raw columns/pages. Citation hashes, retrieval dates, versions and table/measure coverage are mechanically complete. Semantic inspection did not pass:

- `age_sex:count` says its event definition is Census day 2021, while [age_sex.csv](/tmp/jos-exit-audit-3/data/processed/age_sex.csv:2) also contains 2024 year-end broad-age and sex rows.
- Several housing denominators are `unknown` or `not applicable` although cited pages/columns explicitly identify households, occupied dwellings, private dwellings or bedrooms.
- Census page 81 explicitly excludes home workers, people with no fixed workplace and people working outside Jersey; dictionary row 77 reports both denominator and exclusions as `unknown`.
- Census page 46 explicitly excludes visitors staying less than one month from communal-establishment residents; dictionary rows 80–81 report exclusions as `unknown`.

Result: FAIL.

## Step 5 — Known gaps

Command:

```console
$ uv run python -
raw TestsTotalNegativeTests SharePoint-rendered=917/917
NPI warning: PASS
parish-case warning: PASS
influenza-positive warning: PASS
negative-tests warning: PASS
no processed filename contains npi: PASS
no processed filename contains intervention: PASS
no processed filename contains stringency: PASS
no processed filename contains influenza: PASS
covid_daily_surveillance.csv has no parish key/value: PASS
covid_current_summary.csv has no parish key/value: PASS
covid_jhu_daily.csv has no parish key/value: PASS
negative-tests measure absent: PASS
```

The five respiratory PDFs also matched their registered hashes and were recognized as PDFs. Influenza-report page 1 directly confirms that positive influenza-test data were withheld pending validation and QA.

Result: PASS. No invented NPI timeline, parish case series, influenza positives or negative-test series was found.

## Step 6 — Decision

The deterministic build and sampled numeric provenance pass, but the gate requires every enumerated row to expose reporting/suppression state and every measure to be explained accurately. Those requirements are not met.

## Findings

1. **BLOCKING** — Explicitly enumerated Census canonical rows lack the mandatory `reporting_status` and `upper_bound` contract. This is visible in [age_sex.csv](/tmp/jos-exit-audit-3/data/processed/age_sex.csv:1), [parish_population.csv](/tmp/jos-exit-audit-3/data/processed/parish_population.csv:1), and [parish_age_sex.csv](/tmp/jos-exit-audit-3/data/processed/parish_age_sex.csv:1). Their schemas likewise omit the fields at [canonical_schemas.py](/tmp/jos-exit-audit-3/src/jersey_outbreak/canonical_schemas.py:46), [canonical_schemas.py](/tmp/jos-exit-audit-3/src/jersey_outbreak/canonical_schemas.py:59), and [canonical_schemas.py](/tmp/jos-exit-audit-3/src/jersey_outbreak/canonical_schemas.py:72).

2. **BLOCKING** — Dictionary row 54 assigns the 2021 Census event-date definition to every `age_sex:count`, but the same table contains five 2024 year-end rows beginning at [age_sex.csv](/tmp/jos-exit-audit-3/data/processed/age_sex.csv:2). The single measure row therefore gives a false event definition for part of the table.

3. **BLOCKING** — Dictionary rows 60–72 leave source-stated housing denominators `unknown` or call them `not applicable`. The cited Census pages 9, 37 and 78 explicitly identify the relevant denominators; for example page 78 labels its percentages as percentages of all households in each parish. See [measure_dictionary.csv](/tmp/jos-exit-audit-3/data/processed/measure_dictionary.csv:60).

4. **BLOCKING** — Dictionary row 77 omits directly published denominator/exclusion semantics for workplace destination. Its cited Census page 81 explicitly excludes home workers, people without a fixed workplace, and people working outside the Island. See [measure_dictionary.csv](/tmp/jos-exit-audit-3/data/processed/measure_dictionary.csv:77).

5. **BLOCKING** — Dictionary rows 80–81 say communal-setting exclusions are `unknown`, while their cited Census page 46 explicitly states that visitors staying less than one month are excluded. See [measure_dictionary.csv](/tmp/jos-exit-audit-3/data/processed/measure_dictionary.csv:80).

6. **MAJOR** — `covid_weekly_vaccination.csv` and the eligible-population table name the raw `Date` key `week_ending`, while dictionary rows 33–43 correctly admit that the frozen source does not state whether `Date` is week-starting or week-ending. V1.3 must not rely on the unsupported column-name interpretation. See [covid_weekly_vaccination.csv](/tmp/jos-exit-audit-3/data/processed/covid_weekly_vaccination.csv:1) and [measure_dictionary.csv](/tmp/jos-exit-audit-3/data/processed/measure_dictionary.csv:33).

7. **MAJOR** — `known_exclusions` is used to record “also sourced from” relationships in dictionary rows 51, 54, 59 and 72. Those cells neither describe exclusions nor cite the secondary source’s immutable metadata. See [measure_dictionary.csv](/tmp/jos-exit-audit-3/data/processed/measure_dictionary.csv:51).

## What a stranger would still not understand

A future calibrator would still have to guess the reporting/suppression state of Census/M1 rows, which event-date definition applies to mixed-period `age_sex` observations, whether vaccination `Date` anchors the start or end of a week, and several source-stated housing, workplace and communal denominators/exclusions. The raw values are reproducible, but their complete observational meaning is not.

V1.2 EXIT GATE: FAIL — `reporting_status`/`upper_bound` are absent from explicitly enumerated Census rows