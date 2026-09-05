# Independent V1.2 exit-gate audit

- Audited SHA: `5877e426870da2d03380877240c992d167ba1c38`
- Gate-document revision: `31206bc02df6c7631096bc18970427117725382d`
- Clone: `/tmp/jos-exit-audit-5`
- Date: 2026-09-05
- Model: OpenAI Codex (GPT-5)
- Mode: independent cold-start, read-only
- Repository state after audit: clean; no tracked files modified

The current gate document is byte-identical to the specified revision:

```console
$ git diff --exit-code 31206bc02df6c7631096bc18970427117725382d -- docs/research/v1_2/V1_2_EXIT_GATE.md; echo exit_code=$?
exit_code=0
```

## Step 1 — Registry, snapshot integrity, and determinism tests

The literal command encountered the anticipated read-only cache:

```console
$ uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py
error: Could not acquire lock
  Caused by: Could not create temporary file
  Caused by: Read-only file system (os error 30) at path "/home/steven/.cache/uv/.tmpIu586V"
```

Cache-only retry:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py
.......................                                                  [100%]
23 passed in 16.19s
```

Result: PASS after the authorized environment-only workaround.

## Step 2 — Reproducibility of committed tables

```console
$ test ! -e /tmp/jos-audit-rebuild-5 && echo 'precondition: /tmp/jos-audit-rebuild-5 absent'
precondition: /tmp/jos-audit-rebuild-5 absent

$ UV_CACHE_DIR=/tmp/uv-cache uv run jos data build --output-dir /tmp/jos-audit-rebuild-5
{"build_status": "passed", "quality_report": "/tmp/jos-audit-rebuild-5/quality_report.json", "table_count": 23, "warning_count": 19}

$ diff -rq /tmp/jos-audit-rebuild-5 data/processed
exit_code=0
```

The `diff` produced no differences. Result: PASS.

## Step 3 — Row-level traceability

Sampling used `random.Random(20260905)`, one continuous PRNG in the order below. Indices are zero-based data-row indices:

```text
population_totals [1,4,5]
age_sex [161,243,262]
parish_population [1,3,10]
parish_age_sex [42,212,305]
household_types [0,2,3]
housing_controls [1,9,55]
employment_sectors [10,37,43]
workplace_sizes [5,27,42]
workplace_destination [1,3,6]
commute_modes [6,80,85]
school_students [0,2,3]
communal_settings [0,1,16]
passenger_arrivals [0,1,2]
derived_controls [3,11,32]
covid_daily_surveillance [3309,9098,9670]
covid_current_summary [766,2216,3486]
covid_jhu_daily [833,2103,2266]
covid_serosurvey_2020 [0,1,3]
covid_weekly_vaccination [10360,13302,18095]
covid_weekly_eligible_population [82,101,131]
population_estimates_annual [298,775,1427]
population_denominators_by_age_band [265,533,661]
```

Independent standard-library trace:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run python /tmp/jos_audit_trace.py
seed=20260905
...
PASS workplace_sizes[5] ... count=<blank> censoring=positive_less_than upper_bound=5
PASS covid_daily_surveillance[9098] ... raw='-1'; status=not_reported; value=<blank>
PASS derived_controls[3] ... 35822/103267=0.346887195328614; observation_status=derived
PASS population_estimates_annual[1427] ... Male=410 + Female=460 ... value=870
PASS population_denominators_by_age_band[533] ... ages=50..54 sex=all ... total=8310
SUMMARY traced=66/66 tables=22/22 touched_source_ids=18 all_row_hashes_match=yes
```

All sampled values, locators, reporting/censoring states and derivations traced. Direct `sha256sum` checks for all 18 touched sources matched both the registry and canonical `source_sha256`.

Manual fixtures were additionally checked against their evidence PDFs using `pypdf`. The cited population pages 8/18, Census pages 37/44/46/78/81, labour pages 11/13, and serosurvey pages 1/6 contained the sampled values and units.

The five row-8 respiratory evidence files also matched their registered hashes and had valid PDF magic:

```console
$ sha256sum data/raw/respiratory_epidemiological_report_*/epidemiological_report.pdf data/raw/influenza_winter_illness_report_2024_pdf/influenza_winter_illness_report_2024.pdf
7bf3a10d5af2de7620bdd934fd52743b222b930515fffe0d3fab561406bba59b  ...govje_current.../epidemiological_report.pdf
7763aac0fb6b2c018b55455d52add037fa049aa60e9582c0fa765afb45f9479f  ...wayback_20240223.../epidemiological_report.pdf
b75b08d014754d442da41f2e694b80d5bd0f6b8c0a4c9571e939c36a3381005c  ...wayback_20240718.../epidemiological_report.pdf
a84d4b55d57ffbf74a671e794b594b79f9e99afe2afaf0522abf887694a4a759  ...wayback_20260102.../epidemiological_report.pdf
8443a073e9d76496f0e63792f743ebd12d6ab8d488f6428e8e6902c17c4ff93e  .../influenza_winter_illness_report_2024.pdf
```

However, the unit check fails for the sampled vaccination percentage row. The independent resolver identified the source representation as a proportion, while the dictionary calls it percent:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run python -c '...'
Date=2023-01-29 first_doses=84365 eligible_population=107800 ratio=0.782607 raw_percentage_column=0.8 canonical_unit=percent expected_percent=78.26
```

Result: FAIL on vaccination percentage-unit semantics.

## Step 4 — Measure dictionary

Mechanical audit:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run python /tmp/jos_audit_dictionary.py
dictionary_rows=92 unique_triples=92 canonical_triples=92
missing_dictionary=[] extra_dictionary=[] duplicate_triples=0
citation_metadata_or_actual_hash_mismatches=[] blank_semantic_cells=[]
multi_source_pairs={
  'housing_controls:households': [...3 sources...],
  'population_totals:population_total': [...2 sources...],
  'housing_controls:overcrowded_households': [...2 sources...],
  'age_sex:count': [...2 sources...]
}
also_sourced_occurrences=0
row_contract_errors=[]
vaccination_headers_date=[(True, False), (True, False)]
negative_tests_float_rendered=917/917
current_summary_blank_date_rows=1
eligible_population_unique=['107800'] rows=132
housing_source_blank_cells=[...the five cells disclosed at dictionary lines 61 and 63...]
```

Every dictionary row was inspected, grouped by its cited frozen evidence:

- Lines 2–19: COVID/JHU raw headers and cells.
- Lines 20–32: serosurvey PDF pages 1, 2, 5, 6 and 7.
- Lines 33–45: vaccination and annual-population CSVs.
- Lines 46–93: population/Census/labour PDFs and all cited M1 CSV columns.

Structural coverage, source-specific keys, hashes, dates, versions, vaccination-key neutrality and removal of “also sourced from” notes all pass. Audit-4 findings about omitted blanks, density, count/difference denominators, labour universes, serosurvey page 5 and daily-regime placeholders are closed.

Three substantive semantic failures remain:

- Vaccination values from the five `PercentagePopulationVaccinated` measure families retain fractional values such as `0.8` and `1`, while dictionary lines 34, 36, 38, 40 and 42 declare the unit `percent` without documenting the encoding.
- Dictionary lines 7 and 15 mark the denominator of `seven_day_rate_per_100k` unknown, although both the canonical name and frozen columns explicitly state “per 100000.”
- Dictionary lines 49–50 still say the exact flow boundary is unknown and leave the universe unknown. Frozen population-report page 5 defines natural change and net migration as changes in Jersey’s resident population over the previous 12 months and labels the series rolling 12-month.

Result: FAIL.

## Step 5 — Known gaps

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run python -c '...'
warnings {'npi': True, 'parish_cases': True, 'influenza': True, 'negative_tests': True}
gap_named_processed_files []
case_tables_have_parish {'daily': False, 'current': False, 'jhu': False}
negative_test_measures []
influenza_measures []
```

Influenza-report page 1 independently confirms that all positive-test data were excluded pending validation and quality assurance. No NPI timeline, parish case series, influenza-positive series, or negative-test measure was fabricated.

Result: PASS.

## Step 6 — Verdict basis

Steps 1, 2 and 5 pass. Sampled numeric provenance and all hashes pass, but step 3 fails its unit requirement and step 4 fails the exact semantic contract.

Final repository check:

```console
$ git rev-parse HEAD && git status --short && git diff --stat && git diff --cached --stat
5877e426870da2d03380877240c992d167ba1c38
```

No tracked changes or diff stat were produced.

## Findings

1. **BLOCKING — Contract not met:** `data/processed/measure_dictionary.csv:34,36,38,40,42` labels copied vaccination fraction values as `percent`. For example, `data/processed/covid_weekly_vaccination.csv:18870` retains `0.8` from the frozen “Percentage” column; the same raw row contains 84,365 doses and 107,800 eligible persons. The artifact does not explain whether `0.8` means 0.8% or approximately 80%, so a stranger cannot use the value correctly.

2. **BLOCKING — Contract not met:** `data/processed/measure_dictionary.csv:7,15` gives `denominator=unknown` for `seven_day_rate_per_100k`. The frozen columns `CasesSeven7DayNumberper100000` and the canonical measure name explicitly establish the rate scale. The underlying population universe may remain unknown, but the stated 100,000-person scaling may not.

3. **BLOCKING — Contract not met:** `data/processed/measure_dictionary.csv:49-50` says the exact period boundary for natural change/net migration is unknown and leaves their population universe unknown. The frozen population report, page 5, states that these are rolling previous-12-month flows in Jersey’s resident population and defines their components.

4. **MINOR — Contract wording:** `data/processed/measure_dictionary.csv:43` puts the observation that `EligiblePopulation` is constant at 107,800 into `reporting_regime`. The observation is reproducible and located, but it is a value pattern rather than a conventional reporting-regime description.

5. **MINOR — Environment only:** the literal uv commands cannot write to the runner’s default cache. Redirecting `UV_CACHE_DIR` makes them pass without changing the repository.

## What a stranger would still not understand

A stranger would not know the numerical scale of vaccination coverage, would be told that an explicitly per-100,000 rate has an unknown denominator, and would miss the publisher-stated resident-population and rolling-12-month semantics of the population-flow rows. These are input semantics needed before V1.3 can consume the tables safely.

V1.2 EXIT GATE: FAIL — vaccination coverage values are stored as decimal fractions but documented as percent without explaining or converting their scale