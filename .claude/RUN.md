# RUN — two parallel tracks (started 2026-09-03, Steven's ruling: "we'll do both")

## Steven's rulings this morning (2026-09-03)
- Roadmap reorder: performance work runs in parallel with (not after) V1.2 evidence foundation.
- Speed target for the perf track: **180-day full-mode replicate < 20 min; 44-replicate ensemble < 2.5 h** on this desktop, always behind byte-identical equivalence gates.
- G9 closed (pagefile 34→16 GiB via registry route + reboot; C: now 31 GB free).

## Track A — performance deep consult (R7), IN FLIGHT
Codex Sol @ xhigh, read-only on WSL `~/jsy_disease_sim` (pid 56), brief `~/perf_consult_brief.md` (target, measured ground truth, files to read, 4 deliverables incl. judgement of the three R6 finalists + missed candidates), report → `~/jos-perf-consult.last.md`, log `~/jos-perf-consult.log`. On landing: triage findings → implementation units (each: microbenchmark first, then codex brief with R6 equivalence gates). Findings report gets filed to `docs/runs/` and, per Steven, may also go to Claude Science for a second opinion.

## Track B — foreman run: V1.2 evidence + observation foundation
**Predicate** (exit gate from FRONTIER roadmap item 2): immutable Jersey source snapshots (cases/tests/serology/vaccination/denominators) + canonical epidemiology tables with full provenance columns + observation-time correctness (suppression like `<5` never silently zeroed) + data-quality diagnostics, such that a cold-start auditor reproduces every calibration input from frozen snapshots. Calibration itself is OUT of scope. **Budget:** 5 iterations.
**Iteration 1 — DONE.** Inventory committed: `docs/research/v1_2/2026-09-03-jersey-data-source-inventory.md` (27/28 sources live-verified). Anchors: gov.je `COVID19` daily CSV (917×112, cases/tests/deaths 2020-07→2023-02), `COVID19Weekly` vaccination CSV (132×155, 14 age bands), Statistics Jersey serosurvey PDF (3.1%±1.3%, Apr–May 2020). Hard findings: parish-level cases were NEVER published (island-only; spatial calibration below island scale has no data); first wave only via JHU CSSE; OWID has no Jersey testing/NPI columns. Ops: gov.je WAF requires a browser User-Agent; the ListOpenData endpoints are unversioned live renderings → freeze them first.
**Iteration 2a — DONE (freeze).** The existing M1 machinery (`data/sources.yaml` SourceRecord + sha256 + `jos data build`) was the snapshot layer all along — no new machinery needed. Five priority sources fetched (browser UA for the gov.je WAF) and registered on branch `feat/v12-epi-snapshots` @ `f5fba15bb6ec82765ad1316b6a86578d15182bed`; build passed, data tests 4/4, pushed, **G11 parked (merge, default: after CI green)**. Fetched bytes match the inventory agent's independent same-day verification; inventory's serosurvey page count corrected (8pp, not 20) in the registry notes.
**Iteration 3 (next, after G11 + informed by frozen files):** codex brief for canonical epidemiology tables — daily cases/tests, weekly vaccination by age band, serosurvey parameters — extending `data_pipeline.py`/`canonical_schemas.py` conventions with full provenance columns and explicit suppression semantics (`<5` stays `<5`, never silently zeroed; the daily CSV's blank-vs-zero and `-1` sentinel cells need explicit handling — see the frozen file's first data row). The undated cumulative final row of `covid19_current_summary_csv` needs an explicit loader rule.

## Cold-start resume
1. Check `~/jos-perf-consult.last.md` in WSL (Track A report) — if present, triage it.
2. Check `docs/research/v1_2/` for the inventory (Track B iteration 1) — if present, verify its URLs before trusting, then iteration 2 = snapshot-fetch design.
3. Trail rows from `two-track-start` onward; GATES open: G5 only.
