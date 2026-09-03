# RUN — two parallel tracks (started 2026-09-03, Steven's ruling: "we'll do both")

## Steven's rulings this morning (2026-09-03)
- Roadmap reorder: performance work runs in parallel with (not after) V1.2 evidence foundation.
- Speed target for the perf track: **180-day full-mode replicate < 20 min; 44-replicate ensemble < 2.5 h** on this desktop, always behind byte-identical equivalence gates.
- G9 closed (pagefile 34→16 GiB via registry route + reboot; C: now 31 GB free).

## Track A — performance deep consult (R7), IN FLIGHT
Codex Sol @ xhigh, read-only on WSL `~/jsy_disease_sim` (pid 56), brief `~/perf_consult_brief.md` (target, measured ground truth, files to read, 4 deliverables incl. judgement of the three R6 finalists + missed candidates), report → `~/jos-perf-consult.last.md`, log `~/jos-perf-consult.log`. On landing: triage findings → implementation units (each: microbenchmark first, then codex brief with R6 equivalence gates). Findings report gets filed to `docs/runs/` and, per Steven, may also go to Claude Science for a second opinion.

## Track B — foreman run: V1.2 evidence + observation foundation
**Predicate** (exit gate from FRONTIER roadmap item 2): immutable Jersey source snapshots (cases/tests/serology/vaccination/denominators) + canonical epidemiology tables with full provenance columns + observation-time correctness (suppression like `<5` never silently zeroed) + data-quality diagnostics, such that a cold-start auditor reproduces every calibration input from frozen snapshots. Calibration itself is OUT of scope. **Budget:** 5 iterations.
**Iteration 1 (in flight):** research unit — inventory of real Jersey data sources (Statistics Jersey / gov.je / opendata.gov.je: COVID-era cases, testing, serology if it exists, vaccination, population denominators), each with URL, format, date coverage, licence, fetch method. Run by a web-enabled subagent (codex sandbox has no network). Output → `docs/research/v1_2/2026-09-03-jersey-data-source-inventory.md` (draft, verified before commit). Hard rule: never invent data or fill gaps — explicit unknown beats false precision; a source that doesn't exist is recorded as not existing.

## Cold-start resume
1. Check `~/jos-perf-consult.last.md` in WSL (Track A report) — if present, triage it.
2. Check `docs/research/v1_2/` for the inventory (Track B iteration 1) — if present, verify its URLs before trusting, then iteration 2 = snapshot-fetch design.
3. Trail rows from `two-track-start` onward; GATES open: G5 only.
