# P4 validation ensemble — the optimization campaign proven against frozen evidence

**Date:** 2026-09-04 · **Code:** `main` @ `43008ff` (post-G13: R6+R7+R8 chains) · **Machine:** DESKTOP-KQTC6VL/WSL2 · **Artifact:** `jos-ensemble-m6-p4-validation-r8-1a0e9c7037ad` (WSL `~/Documents/JOS_v1_2_full_scale_evidence/`).

## The result
Same 44 seeds (101–144), same full-mode 180-day configuration as the frozen 2026-09-03 P4 artifact (`jos-ensemble-m6-p4-v11-full-scale-c0134368bed2`), rerun on the fully optimized code:

- **All 44 `latent_run_logical_content_hash` values byte-identical to the frozen artifact.**
- **All 44 `m4_logical_content_hash` values identical.**
- **All 44 `observation_logical_content_hash` values identical.**
- 44/44 replicates passed; `actual_workers=6` (the E-1 budget's bound); no OOM, no fallback.

**Wall: 4,865 s (81 min) vs 38,118 s (10.6 h) two days earlier — 7.83× on the identical scientific computation.** Replicate runtimes under 6-way contention: 8.3–10.9 min (median 10.5; solo measurement 7.2 min). This closes the loop on every optimization since 2026-09-02: two audit cycles, eleven landed units, zero scientific drift, proven at full production scale against immutable evidence.

Ensemble manifest/summary hashes legitimately differ from the frozen artifact (schema 1.5 excludes execution-resource fields from scientific identity — audit PROV-1); replicate-level identity, the scientific substance, is exact.

## Terra flag closed
This run doubles as the missing per-worker memory measurement: 6 workers ran a full 180-day ensemble inside the 26 GB cap with zero pressure events — the E-1 worker budget (3 GiB/worker + 3 GiB parent reserve) is validated operationally at the horizon that matters.

## Speed lineage (see `docs/performance-history.md` for the full table)
2026-09-02: ensemble unrunnable (five OOM launches) → 10.6 h at 4 workers → **2026-09-04: 81 min at 6 workers, hash-identical.**
