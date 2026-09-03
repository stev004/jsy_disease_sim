# P4 — 44-replicate full-scale ensemble: run report

**Date:** 2026-09-03 · **Machine:** DESKTOP-KQTC6VL / WSL2 Ubuntu (26 GB cap) · **Code:** `main` @ `a6fdc192e50633570d3edc5db5f7dbf241027548` (post-G10: R6 bounded snapshot cache + pool-loudness fix) · **Gate lineage:** G8 (≥40 replicates, desktop) → G8 amendment (optimize first) → G10 (merge + launch).

## Run facts (from `manifest.json` / `replicate_records.json`)

- Artifact: `~/Documents/JOS_v1_2_full_scale_evidence/jos-ensemble-m6-p4-v11-full-scale-c0134368bed2/` · logical hash `c0134368bed282b6cd9e71b1147fdb603e29911743e467177a8867f9fe78fba4` · `diagnostics_status=passed`. This directory is now an **immutable comparator**.
- Seeds 101–144 (44), `--mode full` (104,540 residents), 180 dated points (2025-01-06 → 2025-07-08), no scenario (baseline), demo respiratory disease + demo observation config.
- **44/44 replicates successful** — satisfies the M04 rule (n·min(q,1−q) ≥ 1 for 2.5/97.5 with n=44).
- Execution: `execution_mode=process_pool_spawn`, `requested_workers=7`, `planned_workers=actual_workers=4` (bounded by the merged `safe_worker_bound`, loudly warned). Wall 38,117.5 s ≈ 10.6 h; replicate runtimes 53–60 min (median 59) under 4-way contention. No OOM kills, PSI ≈ 0 throughout.

## Headline bands (2.5/97.5 **stochastic replicate quantiles — never confidence intervals**; `interval_class=stochastic_replicate_quantile`, numpy linear method; island-wide key `all`)

| Quantity | Median | 2.5–97.5 band |
|---|---|---|
| Peak daily new latent infections (on 2025-02-03) | 7,088 | 5,886 – 7,507 |
| Peak daily observed reported cases (on 2025-02-07) | 3,298 | 2,790 – 3,501 |
| Final ever-infected fraction (2025-07-08) | 0.7779 | 0.7758 – 0.7812 |
| Final cumulative infections | 81,320 | 81,110 – 81,670 |

**Main scientific finding: seed-to-seed stochastic variation of this configuration is small.** The final attack fraction varies by ~±0.3 percentage points across 44 replicates; peak sizes by roughly ±10%; peak timing is tight (early February). The single-seed V1.1 release baseline is therefore a representative trajectory of this synthetic scenario, and future model changes that move outputs outside these bands are signal, not seed noise. Per-parish and per-age-band summaries are in `ensemble_summary.parquet` (keys: parishes, 0-4/5-17/18-64/65+).

Interpretation limits: synthetic population, demonstration disease/observation parameters, no interventions, no travel; characterizes the model, not Jersey. Bands quantify replicate randomness only — parameter uncertainty is untouched (V1.3+ territory).

## Operational notes

- First production run on the post-R6 code: the bounded snapshot cache held workers ≈ 3.3 GB as measured; the worker-bound guard proved conservative (4 planned where ~7 fit) — V1.2.1 follow-up: tune `memory_safety_fraction`/estimate or expose an override, now that real footprints are known.
- Full provenance chain: `git_commit` recorded in the manifest matches the merged main; launch log `p4-ensemble-launch-20260902T205417Z.log` (first line = the worker-bound warning).
