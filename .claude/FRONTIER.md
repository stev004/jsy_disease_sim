# FRONTIER — the single current-state pointer for JOS

*Snapshot, not history. Rewritten each time the frontier moves. Lives on `main` (folded from `docs/frontier` 2026-09-01; that branch is now historical). Cold-start: read this, then `docs/handoff/2026-08-31-sol-handoff.md` for deep history.*

**Updated:** 2026-09-03 morning (P4 COMPLETE: 44/44, M04 closed) · **Updated by:** Fable

## Where the project is

**Tier: V1.1 RELEASED; V1.2 cycle open.** `main` = **`a6fdc192e50633570d3edc5db5f7dbf241027548`** (2026-09-02) = tag `jos-v1.1.0` (`e502ebfd366743db8ecbb65f580159bfa1d2a70c`) + state layer + the V1.2 carry-ins merge (`9a2d984`, G7, 2026-09-01) + the G10 merges (`9f51c8b` R6 bounded snapshot cache; `a6fdc19` ensemble pool loudness + 3.5 GB worker estimate; suite 238). The release itself was fast-forwarded, smoked, and pushed 2026-09-01 (merge executed by the agent on Steven's explicit chat instruction — trail row of same date). V1.0 remains tagged `jos-v1.0.0` at `9e9ce3ab...`.

Release provenance, in order (`docs/audits/`): independent RC audit BLOCKED (O2) → O2 fix delta-re-audit PASS → Sol Pro deep audit BLOCKED (contract defects B01–B04 + majors; science explicitly cleared, P2 satisfied) → R0–R5 repair → release-corrections re-audit **PASS**. Release evidence: `~/Documents/JOS_v1_1_full_scale_evidence/run-20260901T131226Z/` — verified in place AND from a relocated copy; trajectory hash-identical to the pre-repair run, so the V1.0↔V1.1 comparison (`docs/runs/2026-09-01-p1-v1-v11-comparison.md`, "no release concern") applies verbatim. Both full-scale evidence dirs + the V1 pilot dir are immutable comparators.

## The one next action

**V1.2 evidence + observation foundation (roadmap item 2 below) — P4 is DONE.** The 44-replicate full-scale ensemble completed 2026-09-03 ~07:30Z: **44/44 successful**, `process_pool_spawn`/4 workers, wall 10.6 h, artifact `jos-ensemble-m6-p4-v11-full-scale-c0134368bed2` (immutable, WSL `~/Documents/JOS_v1_2_full_scale_evidence/`), report `docs/runs/2026-09-03-p4-full-scale-ensemble-report.md`. Finding: stochastic replicate variation is small (final ever-infected 77.8% ± ~0.3 pp; peaks ±~10%; bands labelled stochastic replicate quantiles, never CIs) — the single-seed V1.1 baseline is representative, and the ensemble is the noise floor for judging future changes. M04 closed. Open before next work cycle: G9 (Steven's pagefile shrink + reboot, command in GATES.md); V1.2.1 note — tune the conservative worker bound now that footprints are measured.

Context, compressed (full detail: trail rows `desktop-transfer` → `p4-bounded` of 2026-09-02, `docs/session_log.md` same date, `docs/runs/2026-09-02-*`): the desktop was set up in WSL2 mode; five earlier P4 launches (12→8→5→3→2 workers) failed on memory; the root cause — the unbounded `(route_id,date)` snapshot cache growing ~66 MiB/simulated-day (~10 GB per 180-day replicate) — was found by the R6 foreman run and fixed (bounded LRU, −87.8% growth, fixed-seed hashes byte-identical), merged via G10 together with the ensemble pool-loudness fix. Measured memory model (post-fix): ~2 GB base + ~3.3 GB/worker at 180 d; full-mode route count is 11. Deferred R6 follow-ups for V1.2.1: share generated networks across replicates instead of per-worker regen; expose `--allow-unsafe-workers` / tune `memory_safety_fraction` now that real footprints are measured; attribution-lookup and Starsim-init candidates per the R6 report. Open gate: G9 (Steven runs the pagefile shrink + reboot after P4 completes; command in GATES.md).

**Then, in order (roadmap authority = Sol Pro audit §9–§11):**
1. **P4 — desktop transfer + full-scale ensemble: transfer DONE, run IN FLIGHT (above).** G8 ruling: ≥40 successful replicates for 2.5/97.5 bands (n·min(q,1−q)≥1 rule). Bands are stochastic replicate variation, never confidence intervals. *(The 2026-09-01 machine note claiming 1.8 GB/replicate and ~12 workers was wrong — see the measured memory model above; the Mac release run's memory pressure is explained by the same pre-R6 cache growth.)*
2. **V1.2 proper — evidence + observation foundation:** immutable Jersey source snapshots (cases/tests/serology/vaccination/denominators), canonical epidemiology tables with full provenance columns, observation-time correctness (suppression like `<5` never silently zeroed), data-quality diagnostics. Exit gate: a cold-start auditor reproduces every calibration input from frozen snapshots. Calibration is excluded from this milestone.
3. **Performance (R6): the memory leg landed early** (2026-09-02, bounded snapshot cache — pulled forward on Steven's "optimise then run after" ruling because it blocked P4). Remaining R6 prototypes (dynamic-route edge materialisation, attribution lookup, Starsim init graph, network sharing across replicates, worker-bound tuning) stay in V1.2.1; `docs/research/v1_1/R6_PERFORMANCE_PROFILE.md` remains the brief and every change needs its exact-equivalence gates.
Then V1.2.1 → V1.3 (first named-pathogen Jersey calibration, COVID era, predeclared holdouts, serology-constrained) → V1.3.1 → V1.4 → V2. §11's cut list is binding.

## Branch index (verified 2026-09-02)

**Live:** `main` @ `a6fdc19` (= `jos-v1.1.0` + state layer + V1.2 carry-ins + G10 merges) · `docs/jos-v1-scientific-review` @ `b8aeb8b` (Claude Science V1 reports).
**Merged 2026-09-02, preserve:** `codex/r6-snapshot-cache-bound` (tip `79ef7b2`) · `fix/ensemble-pool-loudness` (tip `3617a91`).
**Historical, preserve (handoff §7.6):** `codex/v1.2-carry-ins` (merged, tip `9711b8e`) · `docs/frontier` (state layer, folded) · `codex/v1.1-release-corrections` (released tip) · `codex/v1.1-o2-denominator` · `codex/v1.1-integration` · the seven `codex/v1.1-*` lanes · all earlier `codex/m*`/`codex/c*` milestone branches · `codex/codex/m8.2-final-travel-closure` (typo, harmless). All pushed to origin.

## Off-repo assets

- `~/Documents/JOS_v1_full_scale_evidence/` (V1 pilot) and `~/Documents/JOS_v1_1_full_scale_evidence/run-20260831T145052Z` (pre-repair, retained as the B01 exhibit) and `run-20260901T131226Z` (release evidence) — all immutable.
- Desktop transfer: **done 2026-09-02, mode=wsl** (DESKTOP-KQTC6VL). Native probe FAIL (codex sandbox + fm.sh launcher) → WSL2 per `docs/desktop-setup.md` §3; Ubuntu 26.04, 27 GB/16-core `.wslconfig`, full gate green in WSL (235 pytest, ruff clean, frontend test+build), codex sandbox smoke PASS. Loop home: WSL `~/jsy_disease_sim`. Evidence: `docs/runs/2026-09-02-desktop-transfer-wsl.md`. P4 run still gated on G8.

## Doc authority map

1. This file — current frontier. 2. `docs/handoff/2026-08-31-sol-handoff.md` — deep history, conventions, prohibitions. 3. `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md` §9–§11 — forward roadmap authority. 4. On `main`: `docs/research/v1_1/V1_1_SCIENTIFIC_DESIGN_SYNTHESIS.md` — V1.1 design authority; `V1_1_IMPLEMENTATION_STATUS.md` + `docs/progress.md` — claims, never audit evidence. 5. `docs/jos-v1-scientific-review` branch — V1.0 scientific verdict.
