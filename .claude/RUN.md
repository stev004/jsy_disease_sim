# RUN — nothing in flight (R8 closed and merged; validation ensemble COMPLETE 2026-09-04)

**Validation VERDICT: PASS.** 44/44 replicates, **all 132 replicate-level hashes (latent/M4/observation × 44 seeds) byte-identical** to the frozen P4 artifact, wall **81 min at 6 workers** (was 10.6 h) — `docs/runs/2026-09-04-p4-validation-ensemble-report.md`. Repo made PUBLIC by Steven; Actions now free.

**⚠ FIRST UNIT NEXT SESSION — main CI is RED (verify), deterministically, and the no-further-merges rule is active.** One single test fails on GitHub's 2-core public runners (3 runs incl. a rerun; runs 33876939216 + 33903977732): `tests/test_m9_1_job_integrity.py::test_restart_accepts_only_complete_valid_comparison` — job ends `INTERRUPTED` where `SUCCEEDED` is expected. Passes locally (4× full-suite on identical code). Two candidate causes: the audit's open **PROV-2** (startup reconciliation interrupts RUNNING rows with no liveness check — slow-runner hair-trigger), or a real interaction with the **R8/A-1 finalizer-comparison change** that this restart test exercises. Recipe: reproduce locally under constrained CPU (e.g. `taskset -c 0,1` in WSL), read the test alongside the A-1 `job_finalizer.py` diff, fix the root cause (likely = implementing PROV-2's lock/liveness properly), then get `main` CI green and log it. Note: the science is NOT in doubt — the validation ensemble above proves replicate-level identity; this is job-lifecycle robustness.

Next work after that: `docs/roadmap.md` (V1.2 canonical epi tables; R8 leftovers; scientific-corrections track needing Steven's model-owner rulings).

## (superseded — kept for the recipe that was executed) P4 validation ensemble
- Launched 2026-09-04 13:11Z on merged `main` @ `43008ff` (R8 chain): 44 seeds (101–144), `--mode full`, 180 days, `--workers 6`, `--ensemble-id p4-validation-r8`, log `~/Documents/JOS_v1_2_full_scale_evidence/p4v-ensemble-launch-20260904T131139Z.log`, pid file `p4v-ensemble.pid`. Projected ~75–90 min (≈ done 2026-09-04 ~15:00Z).
- **On completion (next session or watcher):** ① compare every per-replicate `latent_logical_content_hash` in the new artifact's `replicate_records.json` against the frozen `jos-ensemble-m6-p4-v11-full-scale-c0134368bed2/replicate_records.json` — they MUST be identical (the R8 chain is proven hash-identical; any mismatch = stop and investigate before anything else). ② Record actual wall + worker RSS (this run IS the missing per-worker memory measurement — terra flag). ③ File a run report to `docs/runs/`, add the performance-history row, tick roadmap THEN item. The ensemble manifest/summary hashes will legitimately differ (schema 1.5 excludes execution fields) — only replicate-level identity is the gate.
- Kill hygiene if needed: `pkill -f 'jos ensemble run'` AND `pkill -f 'multiprocessing.spawn'`. Checkpoints under `.replicates-in-progress/p4-validation-r8/` make any restart a resume, not a loss.

## Blocked on Steven
- **GitHub Actions billing** (Settings → Billing & plans) — CI is dead on all branches; annotation says failed payment or spending limit. Once fixed: re-run CI on `main` @ `43008ff` and log the result.

## Next work (see docs/roadmap.md)
- V1.2 Track B iteration 3: canonical epidemiology tables (independent, ready).
- R8 leftovers: DISEASE-1 step 3 (numpy interventions), ROUTE-5/4 columnar, PROV cluster, Stage-B residue (per-worker footprint closes with the validation run), scientific-corrections track (several need Steven's model-owner decisions — DISEASE-4, ROUTE-6, ROUTE-7 science half).

## Cold-start
`docs/roadmap.md` → this file → GATES.md (open: G5 only) → decisions.tsv tail.
