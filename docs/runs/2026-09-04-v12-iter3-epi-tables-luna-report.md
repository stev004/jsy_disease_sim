# V1.2 Track B iteration 3 — executor report (Codex gpt-5.6-luna@xhigh, fm.sh exec, 1 run, 2026-09-04 20:41→21:07 local)

*Verbatim `~/jos-v12-iter3.last.md`. Director verification and the one wording fix are recorded in the trail row `v12-iter3` and `docs/session_log.md`.*

Implemented without committing.

Files changed:

- [data_pipeline.py](/home/steven/jos-v12-epi-tables-wt/src/jersey_outbreak/data_pipeline.py) — parser, COVID loaders, provenance, checks, warnings, manifest entries.
- [canonical_schemas.py](/home/steven/jos-v12-epi-tables-wt/src/jersey_outbreak/canonical_schemas.py) — five COVID row models.
- [sources.yaml](/home/steven/jos-v12-epi-tables-wt/data/sources.yaml) — fixture registration and “20 pages” correction.
- [serosurvey_2020_summary.csv](/home/steven/jos-v12-epi-tables-wt/data/raw/sars_cov2_serosurvey_2020_manual_fixture/serosurvey_2020_summary.csv) — 13-row manual fixture.
- [test_data_pipeline.py](/home/steven/jos-v12-epi-tables-wt/tests/test_data_pipeline.py) — required regression/acceptance tests.
- [test_data_sources.py](/home/steven/jos-v12-epi-tables-wt/tests/test_data_sources.py) — registry count update.
- Regenerated `data/processed/` outputs, including five new `covid_*.csv` tables and updated reports/manifests.

Evidence:

1. Focused tests

```text
uv run --locked pytest -q tests/test_data_pipeline.py tests/test_data_sources.py
..........                                                               [100%]
10 passed in 3.57s
```

2. Broader suite

```text
uv run --locked pytest -q --deselect tests/test_m9_1_job_integrity.py::test_restart_accepts_only_complete_valid_comparison
288 passed, 1 deselected, 3 warnings in 526.42s
```

3. Lint/format

```text
uv run ruff check . && uv run ruff format --check .
All checks passed!
157 files already formatted
```

4. Build/determinism

```text
uv run jos data build
{"build_status": "passed", "table_count": 19, "warning_count": 8}
```

Generated row counts:

```text
covid_daily_surveillance.csv 10087
covid_current_summary.csv 5176
covid_weekly_vaccination.csv 19008
covid_serosurvey_2020.csv 13
covid_weekly_eligible_population.csv 132
```

Byte-identical rebuild verification passed:

```text
byte_identical_rebuild_exit=0
```

5. Manifest/file counts

```text
5
19
```

6. Registry/raw checks

```text
grep -c "source_id: " data/sources.yaml
32
grep -n "20 pages" data/sources.yaml
341: ... PDF is 20 pages.
! grep -n "8 pages" data/sources.yaml
```

The registry itself validates at 28 sources; the literal grep counts four `evidence_source_id:` lines too.

7. SharePoint artifact grep

```text
! grep -rn "float;#" src/jersey_outbreak/data_pipeline.py | grep -v "warning\|anomal\|#"
```

Exited 0 with no output.

8. Scope/status

```text
git status --porcelain | grep -v "^ M\|^??\|^A " | wc -l
0
git diff --name-only -- data/raw | wc -l
0
```

Pinned vaccination pair set contains 73 pairs:

- `dose_1`, `dose_2`: `all` plus all 14 age bands.
- `dose_3`, `dose_4`: `all` plus all bands except `17_and_under`.
- `autumn_2022_booster`: `all`, `50_plus`, plus the 13 age bands present in the frozen header, excluding `17_and_under`.

Exclusion list:

```text
VaccinationsTotalNumberDoses
VaccinationsDosesPer100PeopleInPopulation
EligiblePopulation
7DayRatePercentageChange
InboundTravel
On-islandSurveillanceScreening
SeekingHealthcareSymptomatic
DateTime
DateTimeShort
Note
```

`git diff --stat`:

```text
8 files changed, 1013 insertions(+), 18 deletions(-)
```

Questions requiring director clarification:

- Should the source-count check use `grep -c '^  - source_id: '`? The requested unanchored pattern reports 32 because `evidence_source_id:` contains `source_id:`.
- Should the deterministic check compare first/second build bytes rather than `git diff` against `HEAD`? Byte comparison passes, but `git diff --stat data/processed` necessarily shows the intended unstaged regenerated changes.