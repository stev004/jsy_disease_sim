Implemented the V1.2 corrective.

Changes:

- [data_pipeline.py](/home/steven/jos-v12-corr3-wt/src/jersey_outbreak/data_pipeline.py:1277)
  - Added canonical `(table, measure, source_id)` validation.
  - Duplicate triples and missing canonical source rows now raise `DataBuildError`.
  - Renamed vaccination output keys to `date`.

- [canonical_schemas.py](/home/steven/jos-v12-corr3-wt/src/jersey_outbreak/canonical_schemas.py:244)
  - Renamed both vaccination `week_ending` fields to `date`.

- [test_v12_corr3_dictionary.py](/home/steven/jos-v12-corr3-wt/tests/test_v12_corr3_dictionary.py:12)
  - Added multi-source coverage, duplicate-key, and missing-source tests.

- Dictionary fixture:
  - 92 data rows / 93 lines total.
  - Added five per-source rows.
  - Removed all “also sourced from” notes.
  - Added Census page/header transcriptions and locators.
  - Final SHA-256: `fd8b0c0f15bb8edca5a0a78dc0b6b80bd4f76184645f3f8ef5b6e7117bb8d5ba`.

- Regenerated `data/processed/` through `uv run jos data build`.

Verification:

- Base failing-first test: failed with `AssertionError: assert 1 == 2`.
- Focused tests: `22 passed`.
- `grep -c "also sourced from"`: `0`.
- `wc -l`: `93`.
- Locator scan: `[]`.
- Required phrase checks: all present.
- `week_ending` grep: no output.
- Vaccination and eligible data-row diffs: empty.
- Fresh rebuild: `diff -rq` produced no output.
- `uv lock --check`: passed.
- `compileall`: passed.
- Full suite: `309 passed, 5 warnings`.
- Ruff check/format: passed.
- Mypy: `Success: no issues found in 15 source files`.
- `jos demo --seed 123`: passed.
- `git diff --check`: passed.

Evidence opened:

- Census PDF pages 9, 37, 44, 46, 78, 81.
- Population PDF pages 3, 8, 19.
- Serosurvey PDF pages 1, 2, 6, 7.
- Relevant frozen CSV headers, including `Age`, `Parish`, `Households`, `Mean persons per household`, `Mean bedroooms per household`, `Mean persons per bedroom`, and `TestsTotalNegativeTests`.

Final status:

```text
 M data/processed/covid_weekly_eligible_population.csv
 M data/processed/covid_weekly_vaccination.csv
 M data/processed/measure_dictionary.csv
 M data/processed/quality_report.json
 M data/processed/quality_report.md
 M data/processed/table_manifest.json
 M data/raw/epi_measure_dictionary_manual_fixture/measure_dictionary.csv
 M data/sources.yaml
 M src/jersey_outbreak/canonical_schemas.py
 M src/jersey_outbreak/data_pipeline.py
?? tests/test_v12_corr3_dictionary.py
```

Diff stat: `213 insertions(+), 164 deletions(-)` across 10 tracked files, plus the new 94-line test. No commit made.