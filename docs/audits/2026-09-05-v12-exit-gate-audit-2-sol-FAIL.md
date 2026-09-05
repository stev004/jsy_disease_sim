<!-- IMMUTABLE AUDIT RECORD. Independent cold-start auditor: Codex gpt-5.6-sol@high (self-reports as "OpenAI Codex (GPT-5)"), read-only, fresh clone /tmp/jos-exit-audit-2 at 03ed6bc05961c199cb64a181a9bf98c4475122c9 (gate definition present), brief ~/jos-v12-exit-audit-2-brief.md, launched 2026-09-05 01:22 local via fm.sh exec, report written ~01:52. Filed verbatim by the director. Verdict: FAIL (7 blocking findings; steps 1-2 and all numeric traceability PASS). -->

# V1.2 exit-gate audit

- Audited SHA: `03ed6bc05961c199cb64a181a9bf98c4475122c9`
- Clone: `/tmp/jos-exit-audit-2`
- Audit date: 2026-09-05
- Auditor/model: OpenAI Codex (GPT-5)
- Mode: independent cold start, read-only
- Scope: seven enumerated calibration-input groups plus respiratory-PDF integrity
- Repository changes: none

## Step 1 — Registry, snapshots, and deterministic build tests

Command:

```text
uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py
```

Output:

```text
error: Could not acquire lock
Caused by: Read-only file system ... "/home/steven/.cache/uv/..."
```

This was a runner-cache permission problem before pytest started. Retried without changing the lockfile or repository:

```text
UV_CACHE_DIR=/tmp/jos-audit-uv-cache uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py
```

Output:

```text
....................                                                     [100%]
20 passed in 13.34s
```

Result: PASS after redirecting only the external `uv` cache.

## Step 2 — Reproduce committed tables

Command:

```text
UV_CACHE_DIR=/tmp/jos-audit-uv-cache uv run jos data build --output-dir /tmp/jos-audit-rebuild
```

Output:

```text
{"build_status": "passed",
 "quality_report": "/tmp/jos-audit-rebuild/quality_report.json",
 "table_count": 23,
 "warning_count": 11}
```

Command:

```text
diff -rq /tmp/jos-audit-rebuild data/processed
```

Output:

```text
exit_code=0
```

No differences were printed. Result: PASS; the committed processed directory is byte-identical to the rebuild.

## Step 3 — Row-level tracing

Sampling seed: `1202`, instantiated independently as `random.Random("1202:<table-name>")`. Line numbers include the CSV header.

The row-7 ellipsis was interpreted conservatively as every canonical table containing Census 2021 provenance.

| Table | Sampled lines | Trace result |
|---|---:|---|
| `covid_daily_surveillance.csv` | 2232, 8267, 8402 | Values, statuses, units matched |
| `covid_current_summary.csv` | 322, 1200, 4523 | Values, statuses, units matched |
| `covid_jhu_daily.csv` | 225, 1274, 2865 | Values and units matched; required reporting fields absent |
| `covid_serosurvey_2020.csv` | 3, 6, 13 | Fixture and PDF values/units matched; required reporting fields absent |
| `covid_weekly_vaccination.csv` | 537, 4576, 7703 | Values/statuses matched; units recoverable from source-column/metric |
| `covid_weekly_eligible_population.csv` | 88, 90, 107 | Values, statuses, units matched |
| `population_estimates_annual.csv` | 489, 2384, 3277 | Values/statuses/units matched |
| `population_denominators_by_age_band.csv` | 379, 610, 634 | Derived sums recomputed |
| `age_sex.csv` | 111, 168, 255 | Values matched |
| `parish_population.csv` | 2, 4, 5 | Population and density matched |
| `parish_age_sex.csv` | 129, 148, 450 | Values matched |
| `population_totals.csv` | 4, 6, 10 | CSV/PDF values matched |
| `household_types.csv` | 5, 11, 12 | PDF page 44 matched |
| `housing_controls.csv` | 32, 87, 106 | Values/units matched |
| `employment_sectors.csv` | 6, 23, 42 | CSV/PDF values/units matched |
| `workplace_destination.csv` | 2, 3, 6 | PDF page 81 matched |
| `commute_modes.csv` | 5, 52, 55 | Values/units matched |
| `communal_settings.csv` | 6, 12, 16 | PDF page 46 matched |
| `derived_controls.csv` | 5, 28, 36 | Derived proportions recomputed |

Representative command output from the independent standard-library trace:

```text
covid_daily_surveillance
line 2232 ... raw='141215' -> value='141215', status=reported, unit=tests: PASS
line 8267 ... raw='-1' -> value='', status=not_reported, unit=cases: PASS
line 8402 ... raw='' -> value='', status=not_reported, unit=tests: PASS

covid_jhu_daily
line 2865: raw[8/21/21]-raw[8/20/21]=9051-9017 -> 34 cases,
observation=derived: PASS

population_estimates_annual
line 3277: 2021 age 81 all raw/calculation=270+320 -> 590 persons: PASS

population_denominators_by_age_band
line 610: 2022 ages 16..100 all, sum(170 frozen cells)=87380 persons: PASS

derived_controls
line 5: 35822/103267=0.346887195328614: PASS
line 28: 2310/57340=0.0402860132542728: PASS
line 36: 178/13991=0.0127224644414266: PASS
```

PDF extraction commands used the required form:

```text
UV_CACHE_DIR=/tmp/jos-audit-uv-cache uv run --with pypdf python -c "..."
```

Pages inspected:

- Serosurvey: 1, 2, 5, 6, 7
- Census report: 44, 46, 81
- Population report: 8, 18
- Labour-market report: 13
- Influenza report: 1

Sample-row hash check output:

```text
sample row source_sha256 matches actual frozen file: 57/57
```

All 18 sampled row `source_id` values matched their actual snapshot SHA-256. The associated manual-fixture evidence PDFs also matched.

Respiratory evidence check:

```text
sha256sum <four respiratory reports> <influenza report>
file <four respiratory reports> <influenza report>
```

Output:

```text
7bf3a10d... epidemiological_report_govje_current_pdf/epidemiological_report.pdf
7763aac0... epidemiological_report_wayback_20240223_pdf/epidemiological_report.pdf
b75b08d0... epidemiological_report_wayback_20240718_pdf/epidemiological_report.pdf
a84d4b55... epidemiological_report_wayback_20260102_pdf/epidemiological_report.pdf
8443a073... influenza_winter_illness_report_2024.pdf
...
PDF document, version 1.7, 3 page(s)
...
PDF document, version 1.7, 11 page(s)
```

The full hashes equal the registry values.

Result: FAIL. Numeric traceability passed, but two epidemiology inputs lack the row-contract fields required by [V1_2_EXIT_GATE.md:32](/tmp/jos-exit-audit-2/docs/research/v1_2/V1_2_EXIT_GATE.md:32). Some Census locators are also row-level rather than cell-level.

## Step 4 — Measure dictionary

Command/output for all dictionary rows:

```text
dictionary rows checked: 44
registry join and actual cited-source hash matches: 44/44
errors: []
event_date_definition unknown rows 18
population_universe unknown rows 29
denominator unknown rows 2
reporting_regime unknown rows 0
known_exclusions unknown rows 16
```

The immutable hash, retrieval date, and version joins are correct for all 44 rows.

The semantic audit was performed by common claim group:

- Lines 2–12, daily surveillance: units and column identities are supported; event date and universe are honestly unknown. The asserted “testing regime change” is not established by the cited column names.
- Lines 13–16, current summary: the cited CSV supports dates and values, but does not state “PCR” or define the asserted reporting regime.
- Lines 17–19, JHU: geography and values are supported. “Single regime” is not stated by the cited frozen CSV.
- Lines 20–32, serosurvey: pages 1, 2, 5–7 support most survey facts, but several measure-specific cells are false or misapplied.
- Lines 33–43, vaccination/eligible population: the source identifies a weekly dataset, but neither its `Date` header nor blank `Note` column states that each date is “week ending.”
- Lines 44–45, annual population: the frozen CSV supports annual age/sex counts but does not state the asserted “resident population” universe.

The dictionary contains only these tables:

```text
covid_current_summary
covid_daily_surveillance
covid_jhu_daily
covid_serosurvey_2020
covid_weekly_eligible_population
covid_weekly_vaccination
population_denominators_by_age_band
population_estimates_annual
```

Every row-7 Census table has zero dictionary entries.

Result: FAIL.

## Step 5 — Known gaps

Command/output:

```text
NPI/intervention matching processed filenames: []
parish-case matching processed filenames: []
influenza matching processed filenames: []
daily table has parish column: False
daily measures containing negative: []

npi: quality=0, dictionary=0
intervention: quality=0, dictionary=0
stringency: quality=0, dictionary=0
parish-level cases: quality=0, dictionary=0
parish cases: quality=0, dictionary=0
influenza positives: quality=0, dictionary=0
positive influenza: quality=0, dictionary=0
TestsTotalNegativeTests: quality=1, dictionary=11
```

No unofficial or invented values were found:

- No NPI/intervention timeline is present.
- No parish-level case series is present.
- No influenza-positive series is present.
- `TestsTotalNegativeTests` is absent from the canonical daily measures.

The influenza PDF’s first page independently confirms that positive-test data were excluded pending validation/QA. The negative-tests exclusion is disclosed at [quality_report.md:126](/tmp/jos-exit-audit-2/data/processed/quality_report.md:126).

However, the quality report/dictionary do not disclose the other three gate-listed gaps. Result: FAIL.

## Step 6 — Repository integrity and verdict basis

Final read-only check:

```text
git status --short
git diff --exit-code
git rev-parse HEAD
```

Output:

```text
exit_code=0
03ed6bc05961c199cb64a181a9bf98c4475122c9
```

No tracked or untracked repository changes were made.

## Findings

1. **BLOCKING — Two epidemiology inputs violate the explicit row contract.** `CovidSerosurveyRow` and `CovidJhuDailyRow` omit both `reporting_status` and `upper_bound`; see [canonical_schemas.py:271](/tmp/jos-exit-audit-2/src/jersey_outbreak/canonical_schemas.py:271) and [canonical_schemas.py:287](/tmp/jos-exit-audit-2/src/jersey_outbreak/canonical_schemas.py:287). Consequently, the required status cannot be confirmed for any row in those inputs.

2. **BLOCKING — Census locators are not consistently cell-level.** For example, [age_sex.csv:111](/tmp/jos-exit-audit-2/data/processed/age_sex.csv:111) uses `csv_age_34`, shared by male, female, and all-sex cells. [parish_age_sex.csv:129](/tmp/jos-exit-audit-2/data/processed/parish_age_sex.csv:129) uses a locator shared by 18 age-band cells. This contradicts the cell-level requirement at [V1_2_EXIT_GATE.md:32](/tmp/jos-exit-audit-2/docs/research/v1_2/V1_2_EXIT_GATE.md:32).

3. **BLOCKING — The measure dictionary omits the row-7 Census calibration inputs.** Its authoritative table list is restricted to eight epidemiology/denominator tables at [data_pipeline.py:531](/tmp/jos-exit-audit-2/src/jersey_outbreak/data_pipeline.py:531). There are no dictionary rows for `age_sex`, `parish_population`, `parish_age_sex`, or the other audited Census-derived tables.

4. **BLOCKING — Serosurvey dictionary cells contradict the frozen PDF.** [measure_dictionary.csv:22](/tmp/jos-exit-audit-2/data/processed/measure_dictionary.csv:22) describes the “observed unweighted” prevalence denominator as weighted and sensitivity-adjusted, while PDF page 6 distinguishes unweighted 2.9%, weighted 2.6%, and the later sensitivity-adjusted 3.1%. Lines 28–31 assign the Jersey private-household population and Jersey fieldwork dates to assay-characteristic measures sourced from an independent WHO hospitalized-patient assessment.

5. **BLOCKING — Vaccination event-date semantics are asserted without frozen-source support.** [measure_dictionary.csv:33](/tmp/jos-exit-audit-2/data/processed/measure_dictionary.csv:33) through line 43 say `Date = week ending`. The frozen CSV provides only `Date`, `DateTime`, `DateTimeShort`, and a blank `Note`; it never defines the date as a week end. Under the audit instruction, this must be `unknown` unless a supporting frozen source is added.

6. **BLOCKING — Other reporting-regime and universe claims are unsupported.** Lines 2–12 infer a “testing regime change” from before/since columns; lines 13–16 call residual reporting “PCR”; lines 17–19 assert a “single regime”; and lines 44–45 assert a resident-population universe. The cited frozen CSVs do not state these facts, and none is marked `unknown`.

7. **BLOCKING — Three required known-gap disclosures are missing.** [quality_report.md:117](/tmp/jos-exit-audit-2/data/processed/quality_report.md:117)–129 discloses the negative-tests problem but not the absent NPI timeline, unpublished parish-level cases, or excluded influenza positives. The same three gaps are absent from the dictionary.

8. **MINOR — The literal locked-test command could not use the runner’s read-only default `uv` cache.** Redirecting only `UV_CACHE_DIR` allowed the locked tests to pass. This is an audit-environment issue, not a repository defect.

## What a stranger would still not understand

A future calibrator would still have to guess what the surveillance dates represent, whether the vaccination `Date` is genuinely a week-ending date, what reporting-regime changes apply to each case/test series, and what population universe the annual estimates cover. They would also lack measure definitions for the Census inputs and could not derive an exact frozen cell solely from several Census `source_locator` values.

V1.2 EXIT GATE: FAIL — `covid_jhu_daily.csv` and `covid_serosurvey_2020.csv` omit the required `reporting_status` and `upper_bound` row-contract fields