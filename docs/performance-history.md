# JOS performance history — what we did and how much faster it made things

*One row per landed optimization, measured on DESKTOP-KQTC6VL (Ryzen 7 5800X, 26 GB WSL2) unless noted. Every number links to primary evidence. Updated at closeout whenever a performance change merges (owned via `.claude/CLOSEOUT.md`). Projections are marked as such; only measured numbers are stated as fact.*

## The headline series: one 180-day full-mode replicate (104,540 agents)

| Date | State | Marginal cost | 180-day replicate | Evidence |
|---|---|---:|---:|---|
| 2026-08-30 | V1.0 pilot (Mac M4) | 51.4 s/day | 2.75 h | frozen pilot report |
| 2026-09-02 morning | V1.1 on desktop, pre-optimization | 15.6 s/day | ~59 min solo (memory-starved runs hit 2.2 h; 5 launches failed on OOM) | `2026-09-02-r6-mem-profile-desktop.json` |
| 2026-09-02 | **R6: bounded snapshot cache** | unchanged | unchanged, but memory growth −87.8% (66 MiB/day → ~7) — made parallel workers possible at all | `2026-09-02-r6-bench-{before,after}.json` |
| 2026-09-03 | **R7 chain** (see below) | **2.26 s/day** | **~7.5 min** (projected from 7/30-day; baseline scenario, no interventions) | `2026-09-03-r7-chain-hash-gate.json` |
| 2026-09-04 | **R8 chain** (see below) | ~2.1 s/day measured pre-D-2; D-2 adds +1.30× on routes | **7.2 min measured solo** (433.7 s); 8.3–10.9 min under 6-way ensemble contention | `2026-09-04-r8-stageB-campaign.json` + validation report |

## The 44-replicate full-scale ensemble

| Date | State | Wall | Evidence |
|---|---|---:|---|
| 2026-09-02 | five failed launches (12→8→5→3→2 workers): OOM kills, silent sequential fallback, WSL VM crash, thrash | DNF | trail rows `p4-launch`…`p4-relaunch-4` |
| 2026-09-02→03 | attempt 6 on R6 code, 4 workers | **10.6 h** (44/44 passed) | `2026-09-03-p4-full-scale-ensemble-report.md` |
| 2026-09-04 | **validation rerun on R6+R7+R8 code, 6 workers** | **81 min (44/44; ALL 132 replicate-level hashes byte-identical to the frozen artifact) — 7.83× measured** | `2026-09-04-p4-validation-ensemble-report.md` |

## What each landed change was (all proven byte-identical output before merge)

| Change | Landed | Measured effect | Proof + evidence |
|---|---|---|---|
| **R6: bounded route-snapshot LRU** (3/route; was unbounded `(route,date)` dict) | `9f51c8b`, 2026-09-02 | 30-day RSS growth 1,770,928 → 216,192 KB (−87.8%); cache 257→33 entries | all logical hashes identical; `2026-09-02-r6-bench-*.json` |
| **R6-adjacent: loud pool degradation + worker estimate** | `a6fdc19` | silent-sequential fallback (cost: three wasted launch days) now warns + aborts on broken pool | CI 33630012570 |
| **R7 S1a: community O(1) target selection** (index arithmetic replaces per-contact source-excluding list rebuild) | `92e634d`, 2026-09-03 | community_indoor 7.31×, community_outdoor 4.79×, all routes 3.12× (242→77.7 s/30 d) | fingerprints identical 7 routes × 30 dates; adversarial side-by-side test |
| **R7 S1b: workday-set cache + all-one participation bypass + primary-job precompute** | `bd75671` | routes cumulative 5.11× (242→47.3 s/30 d); `_stable_int` calls down ~64% in ci | fingerprints identical; per-transformation equivalence tests |
| **R7 S2: attribution via numpy pair filtering + per-pair FIFO** (replaces full-edge Python hazard build) | `3213314` | lookup 25.5× (1M-edge fixture); zero-success days 1,453×; real 30-day wall 444→114 s | bit-identical hazards vs committed oracle; five full-scale hashes reproduced byte-identically |
| Killed honestly along the way | — | R7 S2 run 1 (pure-Python FIFO): only 1.96×, killed under its own ≥5× rule | trail row `r7-s2-run1` |
| **R8 C-1: M2 rebalancing memoization** | `codex/r8-c1-m2`, 2026-09-04 | M2 full-mode generation 510→78 s (6.6×); parent build 655→~230 s | identical logical hash director-verified pre/post; golden hashes |
| **R8 D-1: intervention predicate memoization** | `codex/r8-d1-interventions` | honest −6.5% at full scale (ci micro said 3.5×; per-edge loop dominates) — numpy step 3 still open | M7 scenario hashes identical pre/post |
| **R8 D-2: exact route tranche** (prefix-hoisted hashing, merge-not-rededup, dead-sort deletion, preamble pre-index, isin dispatch) | `codex/r8-d2-route-tranche` | route generation +1.30× (46.4→35.6 s/30 d) on top of R7 | fingerprints + Starsim arrays identical, all 11 routes, both windows |
| **R8 E-1: replicate persistence + honest worker budget** | `codex/r8-e1-ensemble-robustness` | robustness, not speed: broken pools no longer lose completed replicates; measured bound = 6 workers | fixture ensembles hash-identical sequential vs parallel |
| **R8 Stage-B measurement campaign** | `docs/runs/2026-09-04-r8-stageB-campaign.json` | ground truth: 180 d replicate = 433.7 s measured; intervention tax +1.4…+4.7 s/day; memory flat ~2.7 GB peak | the numbers that re-ranked the whole plan |

## Context and caveats
- Baseline numbers exclude interventions/travel. Stage B (2026-09-04) measured the intervention tax at +1.4 (empty manager) to +4.7 s/day (`m7_combined`); R8 D-1 memoization recovered only −6.5% of it — the numpy vectorization (DISEASE-1 step 3, roadmap) remains the open M7 prize. M7-scenario replicates therefore run ~1.5–2.5× the baseline time today.
- Every optimization above shipped behind the same regime: measured hotspot first, byte-identical outputs (edge fingerprints / logical hashes / bit-level hazards) or it dies, full suite + CI, immutable evidence filed in `docs/runs/`.
- The complete decision trail is `.claude/decisions.tsv`; the forward plan is `docs/roadmap.md`.
