# RUN — R6 performance/memory cycle (foreman)

**Started:** 2026-09-02 ~16:40Z · **Director:** Fable (this session, DESKTOP-KQTC6VL) · **Machine:** WSL2 Ubuntu on DESKTOP-KQTC6VL (26 GB RAM cap, swap 6 GB, host C: ~9 GB free — G9)

## Predicate
44-replicate full-mode ensemble affordable on this desktop: projected ≤20 h wall from measured per-replicate cost at a worker count that fits 26 GB, every adopted optimization passing R6 exact fixed-seed equivalence gates (`docs/research/v1_1/R6_PERFORMANCE_PROFILE.md` §gates + benchmark protocol), then P4 launched. Authority: G8 amendment (Steven 2026-09-02, "optimize then run after").

## Budget
5 iterations. Per implementation unit: 3 codex runs, 2 consults.

## Iteration 1 — DONE (measurement). Evidence: `docs/runs/2026-09-02-r6-mem-profile-desktop.json`
Findings: (a) memory grows ~50 MB/simulated-day inside `run_outbreak` (2.02 GB after 7d → 3.51 GB after 30d; ~10.7 GB extrapolated at 180 d — the day's OOM anatomy explained); (b) marginal wall ≈ 15.6 s/day → ~48 min per 180-day replicate when not memory-starved (the observed 2.2 h was thrash); (c) parent M2/M3/M4 build 896 s, worker M4 regen only 59 s. Payoff if growth is fixed: 10–12 workers ≈ 3–5 h for all 44 replicates.

## Iteration 1b — DONE (attribution). `_snapshot_cache` = 366.7 MB pickled (~1.5 GB RSS) at 30 d, 257 entries; every other retained attribute ≤35 MB. The cache is the growth.

## In flight (iteration 2 — implementation, Codex)
Branch `codex/r6-snapshot-cache-bound` off origin/main @ 61ed6a6, worktree `~/jos-r6-cache-wt` (WSL), codex pid 684 (luna@high, setsid), brief `~/jos-brief-r6-cache.md` (LRU bound 3 entries/route via OrderedDict; soundness-test-first: recompute-after-eviction must be content-equal or codex stops), report → `~/jos-r6-cache.last.md`, log `~/jos-r6-cache.log`. Director verification after: full-mode 30 d before/after RSS (≥80% growth reduction, wall within 10%) + fixed-seed 7 d logical-hash identity.

## Cold-start resume recipe
1. Read this file, FRONTIER.md ("P4 — DEFERRED" block has the memory model), decisions.tsv tail (rows p4-launch … p4-defer, r6-*), GATES.md (G9 open).
2. Check `~/Documents/JOS_v1_2_full_scale_evidence/r6/` in WSL for profile JSON; if present, iteration 1 evidence exists — review it, file to docs/runs/, decide iteration 2 (likely: brief the top-ranked R6 prototype that the measurement supports).
3. The fix branch `fix/ensemble-pool-loudness` @ 3617a91 is ready-to-merge (Steven, SHA-first) and independent of this run.
4. No P4 run is in flight; do not launch one until this run's predicate is met.
