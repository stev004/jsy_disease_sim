# RUN — foreman run `v12-run2` IN FLIGHT (started 2026-09-04 23:20 local) — iteration 1/8: V1.2 remaining freezes

**Predicate:** (1) JHU first-wave series frozen+registered, census denominators refreshed into epi tables, respiratory surveillance PDFs snapshotted; (2) V1.2 exit gate PASS by a cold-start auditor (every calibration input reproduced from frozen snapshots alone); then (3) roadmap units needing no Steven ruling (iteration-3 follow-ups incl. restart-test robustness; R8 leftovers e.g. PROV-2), parking the rest in GATES. **Budget:** 8 iterations / 12 codex runs — used: 0 iterations complete, 1 codex run in flight.

**In flight — iteration 1 (freezes + JHU table + annual estimates table):** Codex gpt-5.6-luna@xhigh via `fm.sh exec`, launched 23:28 local; worktree WSL `~/jos-v12-freezes-wt`, branch `feat/v12-remaining-freezes` off `origin/main` (5d6ffb1); brief `~/jos-v12-freezes-brief.md`; log `~/jos-v12-freezes.log`; report `~/jos-v12-freezes.last.md`. Unit: 8 new registry entries (JHU confirmed+deaths, respiratory report current + 3 Wayback editions with CDX SHA-1 authentication, winter illness report, annual population estimates) + tables `covid_jhu_daily` and `population_estimates_annual`; registry 28→36, tables 19→21.
- **Cold-start recipe:** `wsl -d Ubuntu`; `pgrep -af 'codex exec'`; if exited read `~/jos-v12-freezes.last.md`; in the worktree run the brief's ACCEPTANCE 1–7 (full suite ~9 min) + full-diff review (scope, four failure modes, no weakened assertions, every new sha256 re-verified with `sha256sum`); green → commit, push, CI on the SHA, `fm.sh log` row `v12-r2-iter1`, file `.last.md` to `docs/runs/`, roadmap tick, GATES entry for the merge; red → re-brief with exact failing output (≤3 runs) then sol@high.
- Zero-write watchdog: 20 min without worktree writes = wedged → `pkill -f 'codex exec'`, relaunch same brief.
- **Planned next iterations:** 2 = age-band denominators table (vaccination bands + 16+ + 50+) derived from the annual estimates; 3 = write `docs/research/v1_2/V1_2_EXIT_GATE.md` (what counts as a calibration input) + Sol@high cold-start audit in a fresh clone; 4+ = restart-test snapshot-before/after robustness, PROV-2 liveness lock, PROV-9/PROV-7, iteration-3 follow-ups not needing rulings.

## Previous state (still true)

**Validation VERDICT: PASS.** 44/44 replicates, **all 132 replicate-level hashes (latent/M4/observation × 44 seeds) byte-identical** to the frozen P4 artifact, wall **81 min at 6 workers** (was 10.6 h) — `docs/runs/2026-09-04-p4-validation-ensemble-report.md`. Repo made PUBLIC by Steven; Actions now free.

**Main CI red — ROOT-CAUSED AND FIXED 2026-09-04 (fix branch pushed, CI green; merge = G14).** The failing test was deterministic, not a flake and not PROV-2: R8 E-1 wrote replicate checkpoints to `<project root>/.replicates-in-progress`, dirtying a clean checkout mid-job, so artifact provenance (`dirty=True`) disagreed with the submitted identity (`dirty=False`) → `artifact_provenance_mismatch` → INTERRUPTED. Reproduced in a fresh clone; local trees were already dirty, hence 'passed 4× locally'. Fix `fix/checkpoint-root-outside-worktree` @ `d873a80bc9027f2473a4620f1ca828f01c118c85`: `run_ensemble(checkpoint_root=...)`, default `outputs/.replicates-in-progress`, job-owned `job_directory/checkpoints` in the adapter; 284 passed, CI run 33910950203 verify+frontend success. Report: `docs/runs/2026-09-04-ci-red-checkpoint-root-fix.md`. **Steven: merge G14, then main CI is green again.**

Next work after that: `docs/roadmap.md` (V1.2 canonical epi tables; R8 leftovers; scientific-corrections track needing Steven's model-owner rulings).

## (superseded — kept for the recipe that was executed) P4 validation ensemble
- Launched 2026-09-04 13:11Z on merged `main` @ `43008ff` (R8 chain): 44 seeds (101–144), `--mode full`, 180 days, `--workers 6`, `--ensemble-id p4-validation-r8`, log `~/Documents/JOS_v1_2_full_scale_evidence/p4v-ensemble-launch-20260904T131139Z.log`, pid file `p4v-ensemble.pid`. Projected ~75–90 min (≈ done 2026-09-04 ~15:00Z).
- **On completion (next session or watcher):** ① compare every per-replicate `latent_logical_content_hash` in the new artifact's `replicate_records.json` against the frozen `jos-ensemble-m6-p4-v11-full-scale-c0134368bed2/replicate_records.json` — they MUST be identical (the R8 chain is proven hash-identical; any mismatch = stop and investigate before anything else). ② Record actual wall + worker RSS (this run IS the missing per-worker memory measurement — terra flag). ③ File a run report to `docs/runs/`, add the performance-history row, tick roadmap THEN item. The ensemble manifest/summary hashes will legitimately differ (schema 1.5 excludes execution fields) — only replicate-level identity is the gate.
- Kill hygiene if needed: `pkill -f 'jos ensemble run'` AND `pkill -f 'multiprocessing.spawn'`. Checkpoints under `.replicates-in-progress/p4-validation-r8/` make any restart a resume, not a loss.

## Blocked on Steven
- **G14 — merge the main-CI fix** (`d873a80bc9027f2473a4620f1ca828f01c118c85`; exact command in `.claude/GATES.md`). Billing is no longer an issue (repo public since 2026-09-04).

## Next work (see docs/roadmap.md)
- V1.2 Track B iteration 3: canonical epidemiology tables (independent, ready).
- R8 leftovers: DISEASE-1 step 3 (numpy interventions), ROUTE-5/4 columnar, PROV cluster, Stage-B residue (per-worker footprint closes with the validation run), scientific-corrections track (several need Steven's model-owner decisions — DISEASE-4, ROUTE-6, ROUTE-7 science half).

## Cold-start
`docs/roadmap.md` → this file → GATES.md (open: G5 only) → decisions.tsv tail.
