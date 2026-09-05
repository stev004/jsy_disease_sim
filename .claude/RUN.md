# RUN — nothing in flight (foreman run `v12-run2` ENDED 2026-09-05 ~02:55: budget spent, predicate partly met)

## START HERE (next thread, cold start)
1. Read `docs/roadmap.md` NEXT → this file → `.claude/GATES.md` (open: G5 only) → `tail -5 .claude/decisions.tsv` (last rows: `v12-run2-close`, `v12-run2-trail-audit`).
2. G16 and G17 are MERGED (2026-09-05: `133a099`, `f5c246c`; `main` @ `f5c246c6b2c78860000fe6124dc018a151bd1a50`). Branch the corrective unit off `origin/main`. CI on the merge commit `f5c246c`: run 33974942892 verify+frontend success.
3. Next unit = **corrective unit 3 for the exit gate** (brief inputs: `docs/audits/2026-09-05-v12-exit-gate-audit-3-sol-FAIL.md` findings 2–7 + `docs/runs/2026-09-05-census-report-pages-for-dictionary.txt` for per-cell census text). Per the graduated lesson: give Codex exact cell text with a frozen citation or `unknown` — never prose examples. Then **audit 4**: fresh clone at the new SHA, Sol@high, brief `~/jos-v12-exit-audit-3-brief.md` (WSL) with `__CLONE_DIR__`/`__AUDIT_SHA__` re-substituted and the gate-doc revision cited.
4. Machine facts: loop home WSL `~/jsy_disease_sim`; briefs/logs/reports live in WSL `~` as `jos-<unit>-brief.md` / `.log` / `.last.md`; worktrees still present: `~/jos-v12-freezes-wt`, `~/jos-v12-iter2-wt` (= branch tip `4465453`), `~/jos-robust-wt`; audit clones `/tmp/jos-exit-audit-{1,2,3}`, `/tmp/jos-trail-audit` (disposable). Launch pattern: `setsid nohup bash ~/.claude/skills/foreman/scripts/fm.sh exec <worktree> <model> <effort> <brief> <stem> &` from a script file (inline `wsl -- bash -c` mangles quoting). Waiters must be file-based on `<stem>.last.md` when two Codex runs overlap.
5. Budget for the next run: state it in the first reply (default 5 iterations); the exit gate needs 2 (corrective + audit).

**Run result.** 8 iterations, 9 codex runs (5 luna implementation, 1 luna robustness, 3 sol audits). Predicate part (1) DONE: JHU first-wave series, respiratory PDFs (+3 authenticated Wayback editions), annual estimates frozen; age-band denominators + measure dictionary built. Part (2) NOT MET: three cold-start exit-gate audits all FAIL — but each narrowed the gap: audit 3 confirms reproducibility (rebuild into any directory byte-identical), hash integrity, and traceability of 66/66 sampled rows across all 22 tables; the remaining blockers are measure-level contract/dictionary items only (`docs/audits/2026-09-05-v12-exit-gate-audit-3-sol-FAIL.md`). Part (3) partly done: PROV-2 + restart-test robustness + `data/raw -text` landed (G17).

**Merged 2026-09-05 on Steven's instruction:** G16 (`feat/v12-denominators-dictionary` @ `4465453` → `133a099`) and G17 (`fix/job-liveness-and-snapshot-eol` @ `c062d20` → `f5c246c`). `main` = `f5c246c6b2c78860000fe6124dc018a151bd1a50`.

**Next run's predicate (obvious):** V1.2 exit gate PASS at a stated SHA, with the audit brief citing the exact gate-doc revision (`git log -1 -- docs/research/v1_2/V1_2_EXIT_GATE.md`) so re-scoping and remediation stay distinguishable (Terra item 5) — corrective unit 3 (M1-table dictionary cells transcribed per cell from census report pages 9/37/44/46/78/81 with exact citations; `age_sex` split into two dictionary rows by source; `week_ending` → `date` in the two vaccination tables; also-sourced notes moved out of `known_exclusions`) then audit 4. The census page text is pre-extracted at `docs/runs/2026-09-05-census-report-pages-for-dictionary.txt` (director, for the next brief).

**Cold-start:** `docs/roadmap.md` → this file → GATES (G16, G17 open; G5 parked) → decisions.tsv tail (rows `v12-run2-start` … `v12-run2-close`). Cross-model trail audit of this run: `docs/runs/2026-09-05-v12-run2-trail-audit-terra.md` (filed at closeout).

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
