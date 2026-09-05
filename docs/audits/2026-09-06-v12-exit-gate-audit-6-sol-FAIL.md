# Independent V1.2 exit-gate audit

- Audited SHA: `79cbf41eef9d2f0323da908fe57fea9b8860b503`
- Gate-document revision: `31206bc02df6c7631096bc18970427117725382d`
- Gate blob: `7e8d3f8e815ab7cf7d1930dfc63467abc3e71f33` at both revisions
- Clone: `/tmp/jos-exit-audit-6`
- Date: 2026-09-06
- Model: OpenAI Codex (GPT-5)
- Mode: independent cold-start, read-only
- Final worktree: clean; no tracked or staged changes

## Step 1 — Registry, snapshot integrity, and determinism tests

Literal command:

```console
$ uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py
error: Could not acquire lock
  Caused by: Could not create temporary file
  Caused by: Read-only file system (os error 30) at path "/home/steven/.cache/uv/.tmpMRb9AC"
```

Authorized cache-only retry:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py
.......................                                                  [100%]
23 passed in 17.49s
```

Result: PASS. The initial failure was an external read-only cache restriction.

## Step 2 — Reproducibility of committed tables

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run jos data build --output-dir /tmp/jos-audit-rebuild-6
/home/steven/.config/matplotlib is not a writable directory
Matplotlib created a temporary cache directory at /tmp/matplotlib-66swwd79 ...
{"build_status": "passed", "quality_report": "/tmp/jos-audit-rebuild-6/quality_report.json", "table_count": 23, "warning_count": 19}

$ diff -rq /tmp/jos-audit-rebuild-6 data/processed
```

`diff` printed nothing and exited 0. Result: PASS; the rebuilt directory is byte-identical to the committed processed data.

## Step 3 — Row-level traceability

Sampling used `random.Random(120206)`, one continuous PRNG in the following order. Indices are zero-based data rows:

```text
covid_daily_surveillance [208,5087,6019]
covid_current_summary [2882,4813,4964]
covid_jhu_daily [534,1892,2195]
covid_serosurvey_2020 [2,6,11]
covid_weekly_vaccination [6336,14942,17840]
covid_weekly_eligible_population [6,59,86]
population_estimates_annual [1064,3030,3819]
population_denominators_by_age_band [5,37,616]
population_totals [1,4,7]
age_sex [127,163,275]
parish_population [3,6,9]
parish_age_sex [175,356,493]
household_types [0,1,9]
housing_controls [61,121,159]
employment_sectors [12,33,40]
workplace_sizes [49,61,63]
workplace_destination [0,5,6]
commute_modes [19,28,82]
school_students [0,2,5]
communal_settings [2,4,5]
passenger_arrivals [0,1,2]
derived_controls [4,27,29]
```

Independent standard-library resolver:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run python /tmp/jos_audit6_trace.py /tmp/jos-exit-audit-6
PASS covid_daily_surveillance: indices=[208, 5087, 6019]; 3/3 values, status/censoring, and units traced
...
PASS derived_controls: indices=[4, 27, 29]; 3/3 values, status/censoring, and units traced
SUMMARY traced=66/66 tables=22/22 touched_primary_sources=19 evidence_sources=4 all_hashes_match=yes
NOT_REPORTED confirmed=[('covid_current_summary', 2882, '-1')]
DERIVED examples=['population_estimates_annual[1064] 850+820=1670',
 'population_denominators_by_age_band[5] ages 12..15 all=4360',
 'population_denominators_by_age_band[37] ages 75..79 female=1620',
 'population_denominators_by_age_band[616] ages 12..15 female=2160']
```

The `not_reported` row preserves a frozen `-1` as blank value with `reporting_status=not_reported`. Derived population rows and age-band denominators were recomputed, as were sampled M1 shares.

`sha256sum` was run over all 19 touched primary snapshots and four linked evidence PDFs. Representative output:

```text
ea51daa689a851af6fedb45e1520abfc235bc350113cbde1cd49b880d7aa512b  .../covid19_daily.csv
4566333483a6ac4229e86d009fff97caf8f8c52ef1c4758ad07e9558da3630dd  .../covid19_current.csv
e6234a59eec4359d2577358b5220e1a7e3da74c162913cdb7d882db1413f98c2  .../time_series_covid19_confirmed_global.csv
4e87757a3e059c45650a1e1856614f8e339ee3c70653c378a7ba6f7b0ee8c72e  .../time_series_covid19_deaths_global.csv
a74e606e5ef16544a763146249b42fba8ae61fb00526982793c6f9fbc300dd0d  .../prevalence_of_antibodies_2020.pdf
e4f8c38e96330fc60af584b8fae75d3011d29f4992bb2d8031e8baa192a91095  .../R.45-2023.pdf
647cdf53997f66faa36f41036ec9fd904ae729d8bbccc01a97eb23cb5e398fe0  .../R-Labour-Market-June-2025.pdf
```

Every digest matched `data/sources.yaml` and the sampled canonical `source_sha256`.

PDF text was opened directly using:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run --with pypdf python -c 'from pypdf import PdfReader; ...'
```

Inspected pages were serosurvey 1, 2, 5, 6 and 7; population 3, 5, 6, 8, 18 and 19; Census 9, 37, 44, 46, 78 and 81; and labour 11 and 13. Sampled fixture values, units, universes and exclusions appeared on their cited pages.

Respiratory evidence:

```console
$ sha256sum data/raw/respiratory_epidemiological_report_*/epidemiological_report.pdf \
  data/raw/influenza_winter_illness_report_2024_pdf/influenza_winter_illness_report_2024.pdf
7bf3a10d5af2de7620bdd934fd52743b222b930515fffe0d3fab561406bba59b  ...govje_current...
7763aac0fb6b2c018b55455d52add037fa049aa60e9582c0fa765afb45f9479f  ...wayback_20240223...
b75b08d014754d442da41f2e694b80d5bd0f6b8c0a4c9571e939c36a3381005c  ...wayback_20240718...
a84d4b55d57ffbf74a671e794b594b79f9e99afe2afaf0522abf887694a4a759  ...wayback_20260102...
8443a073e9d76496f0e63792f743ebd12d6ab8d488f6428e8e6902c17c4ff93e  ...influenza_winter_illness_report_2024.pdf

$ file <the same five paths>
... PDF document, version 1.7, 3 page(s)
...
... PDF document, version 1.7, 11 page(s)
```

Result: PASS for all 66 sampled rows and all respiratory evidence files.

## Step 4 — Measure dictionary

Structural audit:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run python - <<'PY'
# independent CSV/YAML/hash and canonical-key checks
PY
dictionary_rows=92 unique_triples=92 canonical_triples=92
missing_dictionary=[]
extra_dictionary=[]
citation_metadata_or_actual_hash_mismatches=[]
multi_source_pairs={
 'age_sex:count': [...2 sources...],
 'housing_controls:overcrowded_households': [...2 sources...],
 'housing_controls:households': [...3 sources...],
 'population_totals:population_total': [...2 sources...]
}
also_sourced_occurrences=0
blank_semantic_cells=[]
covid_weekly_vaccination.csv: date_present=True week_ending_present=False
covid_weekly_eligible_population.csv: date_present=True week_ending_present=False
row_contract_errors=[]
```

All 92 rows were then inspected against their cited raw columns or PDF pages. The source-specific keys, hashes, retrieval dates, versions, vaccination scale explanation, neutral `date` key, per-100,000 denominators, population-flow definitions, Census blank-cell disclosures and prior cited-page corrections pass.

One semantic row does not pass:

```console
$ nl -ba data/processed/measure_dictionary.csv | sed -n '76p'
76 ... housing_controls,overcrowded_households,...
   population_universe=unknown,unit=percent,denominator=unknown,...

$ rg -n -A11 'source_id: census_2021_overcrowding_csv' data/sources.yaml
106:  - source_id: census_2021_overcrowding_csv
107-    title: Proportion of overcrowded households by tenure - 2021 Census
...
117-    notes: Overcrowding percentages by tenure.

$ nl -ba data/raw/census_2021_overcrowding_csv/proportion-of-overcrowded-households-by-tenurepercent-census2021.csv
1  Tenure,2011,2021
2  Owner occupied,1.9,1.5
3  Qualified rent,5,5.2
4  Social housing rent,3.6,4.7
5  Non-qualified accomodation,15.5,14.6
6  All households,4.5,4
```

The frozen source explicitly identifies these as proportions of overcrowded households by tenure and provides an all-households total. Thus the row universe is households in each listed tenure and the denominator is households in that tenure. Recording both as `unknown` leaves a source-stated semantic unexplained.

Result: FAIL.

Prior-audit re-verification:

- Audit 1 findings are closed: gate present, relocatable rebuild, measure-level retrieval/version metadata, and registry-backed geography.
- Audit 2 findings are closed: JHU/serosurvey reporting fields, locator-plus-row-key clarification, full Census dictionary coverage, corrected serosurvey/vaccination/regime semantics, and all gap warnings.
- Audit 3 findings are closed under the revised M1 reporting-field contract; mixed-period `age_sex`, Census page semantics, vaccination `date`, and “also sourced from” defects are corrected.
- Audit 4’s seven findings are closed at lines 7, 12, 23, 43, 49–50, 58, 61, 63, 79, 81 and 91.
- Audit 5’s vaccination scale, per-100,000 denominator, population-flow definition and eligible-population placement findings are closed at lines 7, 15, 34, 36, 38, 40, 42, 43 and 49–50.

Audits 4 and 5 were absent from the audited tree but were reachable in clone history and inspected with `git show` at filing commits `43844cf` and `75ae719`.

## Step 5 — Known gaps

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run python - <<'PY'
# inspect quality warnings, filenames, case schemas and raw negative-test cells
PY
quality_gap_warnings={'npi': True, 'parish_cases': True, 'influenza': True, 'negative_tests': True}
gap_named_processed_files=[]
covid_daily_surveillance parish_column=False parish_values=0
covid_current_summary parish_column=False parish_values=0
covid_jhu_daily parish_column=False parish_values=0
negative_test_measures=[]
raw_TestsTotalNegativeTests_float_rendered=917/917
```

Direct influenza PDF extraction:

```console
$ UV_CACHE_DIR=/tmp/uv-cache uv run --with pypdf python -c '...pages[0].extract_text()...'
Two newly identified datasets on positive influenza test results for hospital admissions
... are currently undergoing validation and quality assurance. As a result, all positive
influenza test result data have been excluded from this publication ...
```

Quality-report locations:

```text
quality_report.md:131  TestsTotalNegativeTests exclusion
quality_report.md:135  no intervention/NPI timeline
quality_report.md:136  no parish-level case series
quality_report.md:137  influenza positives excluded
```

No NPI timeline, parish-level cases, influenza positives or negative-test series was fabricated. Result: PASS.

## Step 6 — Decision

Steps 1, 2, 3 and 5 pass. Step 4 fails because one canonical Census measure still lacks a publisher-stated universe and denominator, preventing exact row interpretation.

Final integrity check:

```console
$ git rev-parse HEAD
79cbf41eef9d2f0323da908fe57fea9b8860b503

$ git status --short
$ git diff --stat
$ git diff --cached --stat
```

The final three commands produced no output.

## Findings

1. **BLOCKING — Contract not met:** `data/processed/measure_dictionary.csv:76` records both `population_universe` and `denominator` as `unknown` for `housing_controls:overcrowded_households` from `census_2021_overcrowding_csv`. The official frozen source is explicitly titled “Proportion of overcrowded households by tenure,” contains tenure rows and an `All households` total, and therefore supports “households in the row’s tenure” as the universe and denominator. The current dictionary does not explain exactly what values such as owner-occupied `1.5%` are percentages of.

2. **MINOR — Audit-record availability:** the brief’s audit 4 and 5 files are not present in this SHA’s tree, although both remain reachable in clone history and their findings could be re-verified. This does not itself alter the scientific gate result.

3. **MINOR — Environment only:** literal `uv run` commands cannot write to the runner’s default cache. Redirecting `UV_CACHE_DIR` makes them pass without repository changes.

## What a stranger would still not understand

A stranger would still not know whether each tenure-specific overcrowding percentage is a rate within that tenure or a composition share of all Jersey households. The frozen source resolves that question, but the dictionary—the artifact intended to explain it—leaves the universe and denominator unknown.

V1.2 EXIT GATE: FAIL — `measure_dictionary.csv:76` leaves the source-stated universe and denominator of tenure-specific overcrowding percentages unknown.