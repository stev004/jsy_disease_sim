# V1.2 exit gate — definition and audit protocol

*Director's definition (Fable, 2026-09-04), derived from the roadmap authority `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md` §9 ("V1.2 — Evidence and observation foundation"). This file is the contract the cold-start auditor judges against. Status vocabulary: the gate is PASS/FAIL.*

## The gate, verbatim from §9

> A cold-started auditor can reproduce every calibration input from frozen source snapshots and explain exactly what each row measures.

## What "calibration input" means here (the enumerated set)

The V1.3 target is a bounded COVID-19 era (§9, "First named-pathogen Jersey calibration"). The calibration inputs are therefore the following canonical tables, each produced by `uv run jos data build` from `data/sources.yaml` + `data/raw/**` alone:

| # | Input (canonical table) | What it feeds in V1.3 | Frozen source(s) |
|---|---|---|---|
| 1 | `covid_daily_surveillance.csv` — daily new confirmed cases, cumulative cases, symptomatic/asymptomatic, active cases, 7-day rate, cumulative tests, tests by reason, cumulative deaths (2020-07-30 → 2023-02-01) | fitted case series; tests + ascertainment jointly (§9 item 3) | `covid19_daily_surveillance_csv` |
| 2 | `covid_current_summary.csv` — cumulative tests/cases/deaths + 7-day rate (2020-07-30 → 2026-07-29) | cross-check of #1; post-2023 residual reporting | `covid19_current_summary_csv` |
| 3 | `covid_jhu_daily.csv` — cumulative confirmed + deaths, derived daily new (2020-01-22 → 2023-03-09) | **the only machine-readable first wave (March–July 2020)**, i.e. the serosurvey window | `jhu_csse_confirmed_global_csv`, `jhu_csse_deaths_global_csv` |
| 4 | `covid_serosurvey_2020.csv` — 13 published figures with page locators | cumulative-infection constraint (§9: "use serology to constrain cumulative infection") | `sars_cov2_serosurvey_2020_manual_fixture` ← evidence `sars_cov2_serosurvey_2020_pdf` |
| 5 | `covid_weekly_vaccination.csv` + `covid_weekly_eligible_population.csv` — cumulative doses and percent coverage by dose × age band, weekly (2021-03-14 → 2023-01-29) | vaccination timeline / immunity inputs | `covid19_weekly_vaccination_csv` |
| 6 | `population_estimates_annual.csv` — single year of age × sex × year (2011 → 2024) and the age-band denominators derived from it | denominators for rates and per-band coverage | `annual_population_estimates_by_age_sex_csv` |
| 7 | Census 2021 tables already canonical since M1 (`age_sex.csv`, `parish_population.csv`, `parish_age_sex.csv`, …) | census-day denominators and the synthetic population itself | `census_2021_*` |
| 8 | Respiratory surveillance PDFs (current edition + three Wayback editions; Influenza and Winter Illness Report 2024) | **frozen but NOT tabulated** — chart-only sources; recorded as evidence, not calibration inputs, until a design decision extracts a series | `respiratory_epidemiological_report_*_pdf`, `influenza_winter_illness_report_2024_pdf` |

**Explicitly NOT available as a frozen input (known gaps, to be stated, never filled silently):**
- **Intervention / NPI timeline.** OWID carries no Jersey stringency series (inventory 2026-09-03); the timeline must be hand-reconstructed from gov.je announcements as a dated, cited fixture. Until that fixture exists the calibration cannot treat NPIs as data — it is a V1.3 design task, parked in `docs/roadmap.md`.
- **Parish-level cases** were never published (island-level only).
- **Influenza positives** are excluded from the 2024-25 winter report by the publisher pending QA.
- **`TestsTotalNegativeTests`** in the daily surveillance list is SharePoint `float;#`-rendered in every cell and is excluded (quality-report warning).

## What "explain exactly what each row measures" means (the row contract)

Every canonical row carries `source_id`, `source_sha256`, `evidence_source_id`, `reference_period`, `observation_status` (observed | derived), `source_locator` (cell-level), `transformation_id`, and — for epi tables — `reporting_status` (reported | not_reported | positive_less_than) with `upper_bound`. §9 item 2 additionally requires, per **measure**: event-date definition, geography and population universe, units and denominator, suppression semantics, reporting regime, and known exclusions. Those are measure-level facts, not row-level, so the gate requires a **measure dictionary** (`data/processed/measure_dictionary.csv`, built by the same pipeline, one row per (table, measure)) carrying exactly those columns, with `unknown` as an allowed and honest value where the publisher does not state the fact.

§9 also requires each measure to carry "source ID and immutable hash; extraction date and revision/version". The canonical **row** contract carries `source_id` + `source_sha256` (the immutable hash). Extraction date and revision are carried at the **measure** level, never transcribed: every dictionary row names its primary frozen `source_id`, and the build joins `cited_source_sha256`, `cited_source_retrieved_at` (extraction date) and `cited_source_version` (the registry `reference_period`, which for rolling-URL PDFs is the edition) from `data/sources.yaml`. The row contract itself is deliberately unchanged: its columns feed the M2 population generator's provenance, and widening it would be a contract change on the scientific side of the M1→M2 boundary, not an evidence-foundation change.

Manifest paths are logical, repository-relative labels (`data/processed/<file>`) regardless of the build destination, so a rebuild into any directory is byte-identical to the committed `data/processed/` (audit protocol step 2).

*(Audit 1 at `9ac9d20` — `docs/audits/2026-09-05-v12-exit-gate-audit-1-sol-FAIL.md` — failed on: this file being absent from the audited SHA, non-relocatable manifest paths, the missing measure-level extraction date/revision, and one geography cell that cited data columns instead of the registry title. All four are addressed by the corrective unit that follows; the paragraphs above record the contract the re-audit judges.)*

## Audit protocol (what the cold-start auditor does)

Auditor = a fresh model thread that has never seen this repo (Sol@high, read-only), in a **fresh clone** of `main` at a stated SHA:

1. `git clone` → `uv sync --locked` → `uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py` (registry strictness + every snapshot hash verified + byte-identical rebuild).
2. `uv run jos data build --output-dir /tmp/rebuild` and `diff -rq /tmp/rebuild data/processed` → **must be empty** (the committed tables are reproducible from the frozen files).
3. For every table in the enumerated set (rows 1–7 of the table above; row 8's PDFs are evidence, not calibration inputs, and are checked only for hash + PDF magic): pick ≥3 rows at random, follow `source_locator` back into the frozen file (CSV cell or PDF page) and confirm the value, the `reporting_status`, and the units; confirm the `source_sha256` equals `sha256sum` of the frozen file.
4. For every measure in `measure_dictionary.csv`: confirm the event-date definition, geography/universe, denominator, suppression semantics, and reporting regime are either stated with a page/column citation or marked `unknown` — never inferred.
5. Confirm the "known gaps" list above is present in the quality report / dictionary and that nothing in the tables fills a gap with an unofficial or invented value.
6. Verdict line: `V1.2 EXIT GATE: PASS` or `FAIL — <first failing step and evidence>`; plus a findings list with file:line.

A PASS is recorded in `docs/audits/` (immutable) with the audited SHA; a FAIL spawns the smallest corrective unit and a re-audit at the new SHA (a new head voids the verdict).
