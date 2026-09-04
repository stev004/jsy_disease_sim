# RUN — Track B (V1.2 evidence foundation) iteration 3 IN FLIGHT: canonical COVID epi tables

**In flight (launched 2026-09-04 20:41 local):** foreman Track B iteration 3 — five canonical COVID-era epidemiology tables (daily surveillance, current summary, weekly vaccination by dose×age band, weekly eligible population, 2020 serosurvey manual fixture) with explicit not-reported/`<N` semantics. Predicate for the Track B run (from the roadmap NEXT section): iteration 3 tables built deterministically from the five frozen snapshots with full provenance, gates green, branch pushed with CI green. Budget: this unit = 3 codex runs; Track B default 5 iterations (2 used before this).
- Executor: Codex gpt-5.6-luna@xhigh via `fm.sh exec`; worktree WSL `~/jos-v12-epi-tables-wt`, branch `feat/v12-epi-tables` based on `d873a80bc9027f2473a4620f1ca828f01c118c85` (= main + the G14 CI fix, so the tree is clean-checkout-safe); brief `~/jos-v12-iter3-brief.md` (WSL); log `~/jos-v12-iter3.log`, final report `~/jos-v12-iter3.last.md`.
- **Cold-start recipe:** `wsl -d Ubuntu`; `pgrep -af 'codex exec'` (running?) → if exited, read `~/jos-v12-iter3.last.md`, then in the worktree run the brief's ACCEPTANCE block (1–8) yourself; full-diff review (scope check, four failure modes, no weakened assertions); if green → commit in the worktree, push `feat/v12-epi-tables`, wait for CI on the pushed SHA (`gh run view --json jobs`), log `v12-iter3` row via `fm.sh log`, tick roadmap NEXT iteration 3, file `.last.md` into `docs/runs/`, park the merge in GATES (after G14). If red → re-brief with the exact failing output (max 3 runs), then escalate to sol@high.
- Zero-write watchdog: no file change in the worktree for 20 min = wedged → `pkill -f 'codex exec'` and relaunch with the same brief.

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
