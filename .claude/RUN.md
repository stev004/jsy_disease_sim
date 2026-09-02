# RUN — R6 performance/memory cycle (foreman)

**Started:** 2026-09-02 ~16:40Z · **Director:** Fable (this session, DESKTOP-KQTC6VL) · **Machine:** WSL2 Ubuntu on DESKTOP-KQTC6VL (26 GB RAM cap, swap 6 GB, host C: ~9 GB free — G9)

## Predicate
44-replicate full-mode ensemble affordable on this desktop: projected ≤20 h wall from measured per-replicate cost at a worker count that fits 26 GB, every adopted optimization passing R6 exact fixed-seed equivalence gates (`docs/research/v1_1/R6_PERFORMANCE_PROFILE.md` §gates + benchmark protocol), then P4 launched. Authority: G8 amendment (Steven 2026-09-02, "optimize then run after").

## Budget
5 iterations. Per implementation unit: 3 codex runs, 2 consults.

## Iteration 1 — DONE (measurement). Evidence: `docs/runs/2026-09-02-r6-mem-profile-desktop.json`
Findings: (a) memory grows ~66 MiB/simulated-day inside `run_outbreak` (terra-corrected from the first-pass "~50 MB") (2.02 GB after 7d → 3.51 GB after 30d; ~10.7 GB extrapolated at 180 d — the day's OOM anatomy explained); (b) marginal wall ≈ 15.6 s/day → ~48 min per 180-day replicate when not memory-starved (the observed 2.2 h was thrash); (c) parent M2/M3/M4 build 896 s, worker M4 regen only 59 s. Payoff if growth is fixed: 10–12 workers ≈ 3–5 h for all 44 replicates.

## Iteration 1b — DONE (attribution). `_snapshot_cache` = 366.7 MB pickled (~1.5 GB RSS) at 30 d, 257 entries; every other retained attribute ≤35 MB. The cache is the growth.

## Iteration 2 — DONE, ADOPTED. Branch `codex/r6-snapshot-cache-bound` @ `79ef7b2aa07d435ffbfc2d04435b9a291fe24f95`, pushed, CI pending.
Bounded LRU snapshot cache (3 entries/route). Verification (all director-run, evidence `docs/runs/2026-09-02-r6-bench-{before,after}.json` + codex report `2026-09-02-r6-cache-codex-report.md`): fail-at-HEAD proven (2 new tests fail on main, soundness test passes both sides) · full suite 238 passed · ruff/format green · all four fixed-seed 7 d logical hashes AND the 30 d latent hash byte-identical (eviction active: cache 257→33 entries) · 30 d RSS growth 1,770,928→216,192 KB (−87.8%) · 30 d wall +4.2%. Retro-diagnosis: the day's "9 GB worker peaks" were cache fill, not regen.

## Predicate status: MET on projection, blocked only on G10 (Steven's merge)
Per-replicate ≈ 50 min, worker ≈ 3.3 GB at 180 d → 7 workers → 44 replicates ≈ 6 h ≪ 20 h. Remaining unit (launch P4) requires the G10 merges; run stops here with digest. On G10 approval: pull main in WSL clone, launch 44 seeds / full / 180 d / `--workers 7` via `~/launch_p4.sh` (edit workers), tripwire `~/p4_tripwire.sh` pattern.

## Cold-start resume recipe
1. Read this file, FRONTIER.md ("P4 — DEFERRED" block has the memory model), decisions.tsv tail (rows p4-launch … p4-defer, r6-*), GATES.md (G9 open).
2. Check `~/Documents/JOS_v1_2_full_scale_evidence/r6/` in WSL for profile JSON; if present, iteration 1 evidence exists — review it, file to docs/runs/, decide iteration 2 (likely: brief the top-ranked R6 prototype that the measurement supports).
3. The fix branch `fix/ensemble-pool-loudness` @ 3617a91 is ready-to-merge (Steven, SHA-first) and independent of this run.
4. No P4 run is in flight; do not launch one until this run's predicate is met.
