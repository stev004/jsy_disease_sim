Implemented corrective 5 within scope; no commit made.

Before/after changes:

| Row | Locator | Change |
|---|---|---|
| Five vaccination percentage rows | Frozen `VaccinationsPercentagePopulationVaccinated...` columns | `percent` → `proportion in the 0–1 scale (values above 1 occur for the 80+ band), despite column names containing "Percentage"; locator and 2023-01-29 worked example included` |
| Daily seven-day rate | `CasesSeven7DayNumberper100000` | denominator `unknown` → per 100,000 population |
| Current-summary seven-day rate | `CasesSeven7DayNumberper100000` | denominator `unknown` → per 100,000 population |
| Natural change | PDF page 18 | Added rolling previous-12-month definition, resident population, and footnote-3 rounding caveat |
| Net migration | PDF pages 18/19 | Added rolling previous-12-month definition and Jersey resident population |
| Eligible population | `EligiblePopulation` | Moved constant 107,800 description to unit; reporting regime restored to `unknown` |

Verification:

- Fixture SHA and registry SHA match: `766202acd1551d1f76f7abd51e6f246736f88005902e063e927f3015bc4f635f`
- In-place build passed: 23 tables, 19 warnings.
- Fresh rebuild comparison: `diff -rq` silent.
- Focused tests: `27 passed`.
- Ruff check passed; format check: `175 files already formatted`.
- `git diff --check` passed.
- Vaccination `,percent,` matches: `0`.
- Canonical vaccination table diff: none.
- Count-measure rule: `[]`.
- Locator-rule check: `[]`.

Changed files are limited to the permitted fixture, source hash, and regenerated processed outputs.
---
# retry 1
Implemented and regenerated successfully.

Changed cells:

- Five vaccination percentage `unit` cells: `percent` → proportion `0–1` encoding with the requested example.
- Two `event_date_definition` cells now cite the page-5 sentence, Figure 4 caption, and December 2024.
- Natural-change locator → `...pdf_page_18;pdf_page_5;pdf_page_6...`
- Net-migration locator → `...pdf_page_18;pdf_page_19;pdf_page_5...`
- Preserved existing corrective-5 denominator and eligible-population changes.

Verification:

```text
grep count: 0
sha256: 692c1d2c3172598faff67d489fb623f8f027875ee2308b96673991e93e9161fd
registry hash: same
MATCH
```

```text
in-place build: {"build_status": "passed", "table_count": 23, "warning_count": 19}
clean rebuild: {"build_status": "passed", "table_count": 23, "warning_count": 19}
diff -rq: no output
pytest: 27 passed in 19.88s
ruff: All checks passed!
git diff --check: no output
locator one-liner: []
count-measure one-liner: []
```

Status:

```text
 M data/processed/measure_dictionary.csv
 M data/processed/quality_report.json
 M data/processed/quality_report.md
 M data/processed/table_manifest.json
 M data/raw/epi_measure_dictionary_manual_fixture/measure_dictionary.csv
 M data/sources.yaml
```

Diff stat: 6 files changed, 108 insertions, 108 deletions. No commit made.