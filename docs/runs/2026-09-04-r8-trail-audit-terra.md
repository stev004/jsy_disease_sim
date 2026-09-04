Attention list — read-only audit; no files changed.

(a) Cited evidence does not support the claim

- **attention** — `.claude/decisions.tsv:r8-stageB` / `.claude/RUN.md:8`: “M2 513.5s (78%!)”. Campaign JSON has M2/M3/M4 generation times 513.5/139.48/19.3 s: M2 is 76.4% of those three, or 75.9% including recorded M2/M3 writes and loads—not 78%.

- **attention** — `r8-stageB`: “n_events 81,341 … confirming the pilot’s 294k came from the waning-enabled comparator.” The campaign establishes only the current 180-day baseline’s event count. It does not run or identify the historical pilot configuration, so it cannot confirm the cause of the earlier 294k figure.

- **attention** — `r8-stageB` / `RUN.md:8`: “6–7 workers fit” and “DISEASE-5 pessimism dissolved.” The cited JSON contains one process HWM (2.73 GB including parents), not an 180-day per-worker RSS measurement or a concurrent-worker measurement. This is specifically insufficient under the audit’s DISEASE-5 condition.

- **attention** — commit `6e16e4a` (E-1): “3.0 GiB/worker (measured 180-day footprint)” and “On this host: bound 6.” The cited campaign does not measure a worker separately; its only 180-day memory datum is the combined process HWM above.

(b) Claimed verification without resolvable artifacts

- **attention** — `r8-stageA-gate`: “all five logical hashes byte-identical … 30d wall 119.7s.” Its cited JSON is only in a WSL evidence directory, not in this checkout.

- **attention** — `r8-c1`: “M2 full-mode 510.1→77.8s,” rebalancer `579→0.21s`, and full-mode hash identity. The branch commit contains code and golden tests, but no director-run timing/hash artifact.

- **attention** — `r8-d1`: full-scale M7 before/after timings and hash identity rely on `m7gate.log`, which is not resolvable here.

- **attention** — `r8-d2`: full-mode/v2 route fingerprints, arrays, and `46.4→35.6s` rely on `verify_d2.log` and unspecified compare output, neither present here.

(c) Numeric inconsistencies

- **attention** — `r8-stageB`, `RUN.md:8`, `roadmap.md:18`, and `r8-c0` repeat the unsupported 78% M2 share.

- **minor** — `r8-c1`: “parent build now ~230s (was 655).” The only committed pre-C1 campaign totals are 672.28 s for M2/M3/M4 generation, or 677.03 s including recorded load/write phases. Neither supplies 655 s; the claimed after figure has no artifact.

- **minor** — `r8-d1` reports pre-change `m7_combined` at 244.4 s, while the sole Stage-B `m7_combined` record is 259.6 s. Different setups may explain it, but no artifact records the setup or variance.

(d) Risky calls not acknowledged

- **attention** — E-1 changes the worker bound to **6**, while the audit and `roadmap.md:40` specify a corrected **4–5** and expressly say not to raise to 7 before measuring an 180-day worker and adding persistence. No state file acknowledges this departure or its missing measurement.

- **attention** — `6e16e4a` persists all checkpoints as `.replicates-in-progress/seed-<seed>.json`; `_ensemble_id` is deliberately unused in `_replicate_state_path`. Concurrent or successive ensembles sharing a seed can overwrite one another’s checkpoint. Provenance prevents unsafe reuse, but it does not prevent losing a completed checkpoint—the central DISEASE-6 failure being addressed. No trail/state entry notes this namespace risk.

(e) State-file contradictions

- **attention** — `.claude/RUN.md:8` and `docs/roadmap.md:19` say C-0/DATA-6 is “in flight.” `origin/codex/r8-stageA` is actually at `8068e3e`, containing C-0, C-1, D-1, D-2, and E-1; `decisions.tsv:r8-d2` itself records D-2 landed.

- **attention** — `docs/roadmap.md:23`, `:30–35`, and `:39–40` leave DATA-2, DISEASE-1, ROUTE-1/3/7/9, DISEASE-7, DISEASE-5, and DISEASE-6 open, despite their corresponding commits being integrated on `codex/r8-stageA`.

- **attention** — The latest R8 decision row is `r8-d2`, which says E-1 was launched. Git shows E-1 completed and integrated at `6e16e4a`/`8068e3e`; neither `decisions.tsv`, RUN, nor roadmap records that completion.

- **minor** — `.claude/GATES.md` contains no conflicting R8 claim, but also contains no acknowledgement of the E-1 six-worker decision/departure from the audit’s 4–5-worker recommendation.

(f) Audit-mandate items marked done but not actually delivered

- **attention** — `docs/roadmap.md:18` marks CROSS-1/CROSS-2 complete, but the campaign JSON lacks the mandated three-parameter cost model and separate timers for Sim.init, route generation, attribution, post-processing, canonical hashing, and Parquet. It records opaque `run_wall_s`, `observe_wall_s`, parent phases, and one worker-regeneration phase only.

- **attention** — The same done roadmap item requires DISEASE-11 shared-object sizing at 1/7/14/30/60/120/180 days. The JSON has RSS/HWM for runs at 7/14/30/60/180 days and structure weights only at 180; it lacks days 1 and 120 and shared-object measurements across the stated horizons.

- **minor** — The four Stage-A roadmap checkmarks are supported by `4e2e28d`, `95f7393`, and `6194cee`; no branch-content mismatch found for PROV-1, DISEASE-2, ROUTE-2, or ROUTE-10.

AUDITOR: gpt-5.6-terra