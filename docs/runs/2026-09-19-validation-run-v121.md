# 2026-09-19 — authorised validation run on `main` code baseline `08960b8` (V1.2.1 batches merged)

**Authorised:** Steven, chat 2026-09-19 ("start validation run"). **Director:** Fable. **Code:** `main` state head `4659ed8` at launch, code baseline `08960b895ba5dfeaa547ee61c2842955d54ea825` (verified ancestor at run start). **Box:** DESKTOP-KQTC6VL/WSL2, 16 CPUs, 26 GB. **Raw evidence:** WSL `~/jos-validation-20260919/` (run.log, solo-time.txt, ensemble-time.txt, CLI JSONs, VERDICT.txt). Parents reused via the PERF-9 verified path from `~/jos-astra-perf-evidence-20260905/full`.

## Verdict: **PASS** — both targets beaten, zero scientific drift

| leg | target | measured | result |
|---|---|---|---|
| solo 180-day full-mode (seed 101) | ≤390 s | **197.65 s** (maxrss 2.30 GiB) | PASS, 2.0× headroom |
| 44-replicate full-mode ensemble, 6 workers (seeds 101–144) | ≤75 min | **2292.81 s = 38.2 min** (parent maxrss 2.0 GiB) | PASS, ~2× headroom |

## Exactness

- Solo M5 `logical_content_hash` = `a2bcc0a3e52e…63e15727` — identical to the frozen validation artifact's seed-101 `latent_run_logical_content_hash`.
- New ensemble artifact `jos-ensemble-m6-p4-validation-v121-09fcb68de443` (written to `~/Documents/JOS_v1_2_full_scale_evidence/`), 44/44 successful.
- **All 132 replicate-level hashes (latent / M4 / observation × 44 seeds) byte-identical to the frozen `jos-ensemble-m6-p4-validation-r8-1a0e9c7037ad`** — the automated comparison in `VERDICT.txt` reports 132/132, no mismatches. Every unit merged since (G22/G23/G25/G26 chains) is therefore proven exact at full production scale.

## Reading

- Ensemble lineage: 10.6 h (2026-09-03) → 81 min (2026-09-04, R6–R8) → **38.2 min (2026-09-19, full perf tranche + V1.2.1 batches)** on the identical scientific computation. Astra's "only route to ~40 min at 6 workers" (ROUTE-5 columnar) is delivered and measured.
- The C:-space watchdog (armed because host free was 2.1 GB after housekeeping; VHD compaction pending an elevated diskpart) never fired; no OOM, no fallback (`no-watchdog-abort`).
- This closes the "owed validation run" item from the Astra tranche predicate and G25/G26. Bands remain stochastic replicate quantiles, never confidence intervals.
