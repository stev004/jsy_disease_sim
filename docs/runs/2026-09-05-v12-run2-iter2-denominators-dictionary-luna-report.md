# V1.2 foreman run 2, iteration 2 — age-band denominators + measure dictionary: executor report (Codex gpt-5.6-luna@xhigh, fm.sh exec; run 1 2026-09-04 23:52 wedged after completing implementation + gates (296 passed) and was killed; run 2 = director-review fix round 2026-09-05 00:23→00:38, this report)

*Verbatim `~/jos-v12-iter2-fix.last.md`. Run 1 gate evidence lines preserved in `~/jos-v12-iter2.run1.log` (WSL). Director review corrections: uncited event-date semantics → `unknown`; JHU README not frozen → caveat; serosurvey fieldwork/denominators from the frozen PDF; booster locator fixed.*

Implemented the requested fixture-only corrections and rebuilt the processed outputs.

Fixture diff: 52 changed cells

| Rows/measures | Field | Before → After |
|---|---|---|
| All 11 `covid_daily_surveillance` rows | `event_date_definition` | `Date = the date the daily figures were published/reported for` → `unknown` |
| All 4 `covid_current_summary` rows | `event_date_definition` | Same → `unknown` |
| `covid_daily_surveillance:symptomatic_cases` | `source_locator` | Tests columns → Cases columns |
| `covid_daily_surveillance:asymptomatic_cases` | `source_locator` | Tests columns → Cases columns |
| All 3 `covid_jhu_daily` rows | `event_date_definition` | JHU date assertion → requested frozen-source caveat |
| All 3 `covid_jhu_daily` rows | `source_locator` | `CSSE daily report date definition` → `date headers only` |
| All 13 serosurvey rows | `event_date_definition` | `unknown` → requested fieldwork/registry reference |
| 4 prevalence rows | `denominator` | `unknown` → requested 855-person weighting/sensitivity text |
| 2 response-rate rows | `denominator` | `unknown` → requested eligible-sample text |
| 4 assay rows | `denominator` | `unknown` → requested assay-validation text |
| Autumn booster cumulative doses | `source_locator` | Old locator → requested dose-column pair |
| Autumn booster population percentage | `source_locator` | Old locator → requested percentage-column pair |
| Both population dictionary rows | `event_date_definition` | `unknown` → requested annual-estimate wording |
| Both population dictionary rows | `population_universe` | `unknown` → `resident population of Jersey (Statistics Jersey annual estimates)` |

Fixture SHA-256 updated to:

`da01342aafc4fac30ca3bd9a81b1fb86250c9e9ea64c3fe4579158099a8e7f3d`

Acceptance results:

- Forbidden phrase count: `0`
- Targeted tests: `17 passed`, exit `0`
- Full tests: `296 passed`, exit `0`
- Ruff check/format: passed, exit `0`
- Builds: both passed; `BYTE_IDENTICAL=1`
- Manifest count: `23`
- Registry count: `37`
- Tracked raw diff count: `0`
- Disallowed porcelain status count: `0`

`git diff --stat`:

```text
data/processed/quality_report.json       |  78 +++++++++
data/processed/quality_report.md         |   7 +
data/processed/table_manifest.json      |  46 ++++++
data/sources.yaml                        |  13 ++
src/jersey_outbreak/canonical_schemas.py |  47 ++++++
src/jersey_outbreak/data_pipeline.py     | 276 +++++++++++++++++++++++++++++++
tests/test_data_pipeline.py              | 144 +++++++++++++++-
tests/test_data_sources.py               |   2 +-
8 files changed, 611 insertions(+), 2 deletions(-)
```

The stat reflects the preserved prior-run changes; new untracked fixture/processed files are not included by `git diff --stat`.