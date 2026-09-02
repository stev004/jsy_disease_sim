# RUN — R6 performance/memory cycle (foreman)

**Started:** 2026-09-02 ~16:40Z · **Director:** Fable (this session, DESKTOP-KQTC6VL) · **Machine:** WSL2 Ubuntu on DESKTOP-KQTC6VL (26 GB RAM cap, swap 6 GB, host C: ~9 GB free — G9)

## Predicate
44-replicate full-mode ensemble affordable on this desktop: projected ≤20 h wall from measured per-replicate cost at a worker count that fits 26 GB, every adopted optimization passing R6 exact fixed-seed equivalence gates (`docs/research/v1_1/R6_PERFORMANCE_PROFILE.md` §gates + benchmark protocol), then P4 launched. Authority: G8 amendment (Steven 2026-09-02, "optimize then run after").

## Budget
5 iterations. Per implementation unit: 3 codex runs, 2 consults.

## In flight (iteration 1 — measurement unit, director-run)
Phase-timed + RSS-sampled single full-mode replicate on this box via the exact ensemble code path (M2/M3 build → M4 generate seed 101 → run_outbreak 7d, then 30d), script `~/r6_mem_profile.py` in WSL (copied from session scratchpad), results JSON → `~/Documents/JOS_v1_2_full_scale_evidence/r6/` then filed to `docs/runs/`. Purpose: attribute the 5.5–9 GB worker footprint (Mac pilot peaked 2.16 GiB) to phases before any optimization is briefed.

## Cold-start resume recipe
1. Read this file, FRONTIER.md ("P4 — DEFERRED" block has the memory model), decisions.tsv tail (rows p4-launch … p4-defer, r6-*), GATES.md (G9 open).
2. Check `~/Documents/JOS_v1_2_full_scale_evidence/r6/` in WSL for profile JSON; if present, iteration 1 evidence exists — review it, file to docs/runs/, decide iteration 2 (likely: brief the top-ranked R6 prototype that the measurement supports).
3. The fix branch `fix/ensemble-pool-loudness` @ 3617a91 is ready-to-merge (Steven, SHA-first) and independent of this run.
4. No P4 run is in flight; do not launch one until this run's predicate is met.
