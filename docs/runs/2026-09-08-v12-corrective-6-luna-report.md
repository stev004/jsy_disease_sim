Implemented only the requested corrections.

Before → after:

- `population_universe`: `unknown` → `households in the row's tenure category (frozen CSV column "Tenure"; registry title "Proportion of overcrowded households by tenure - 2021 Census"; the "All households" row covers all households)`
- `denominator`: `unknown` → `households in the same tenure category (registry title "Proportion of overcrowded households by tenure - 2021 Census"; frozen CSV column "Tenure")`

Verification:

- Fixture SHA: `16ba6ed70b02fb84bf10757102376348ef89030bdc761a8e6e561163c279525b`; registry matches.
- Build passed: 23 tables, 19 warnings.
- Rebuild `diff -rq`: no output.
- Tests: `27 passed in 18.62s`
- Ruff: `All checks passed!`
- `git diff --check`: clean.
- Locator check: `[]`
- Count-measure check: `[]`

Status:

```text
 M data/processed/measure_dictionary.csv
 M data/processed/quality_report.json
 M data/processed/quality_report.md
 M data/processed/table_manifest.json
 M data/raw/epi_measure_dictionary_manual_fixture/measure_dictionary.csv
 M data/sources.yaml
```

Diff stat: 6 files changed, 99 insertions, 99 deletions. No commit made.