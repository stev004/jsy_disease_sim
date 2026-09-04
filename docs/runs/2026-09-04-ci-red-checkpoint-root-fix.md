# 2026-09-04 — main CI red: root cause + fix (checkpoints inside the git worktree)

**Verdict: main CI verify was red DETERMINISTICALLY (3/3 runs on distinct SHAs), cause = R8 E-1 checkpoint location, NOT PROV-2 timing and NOT the A-1 finalizer change.** Fix branch `fix/checkpoint-root-outside-worktree` @ `d873a80bc9027f2473a4620f1ca828f01c118c85` — CI run 33910950203 verify+frontend **success**. Awaiting Steven's SHA-first merge (G14).

## Symptom
Every real CI run of `main` after the R8 merge failed one test:
`tests/test_m9_1_job_integrity.py::test_restart_accepts_only_complete_valid_comparison` —
`assert 'INTERRUPTED' == 'SUCCEEDED'`. Runs 33876939216 (3a81e45), 33903975387 (729227a), 33904951872 (f565245); frontend green throughout; last green verify on main = c6fea68 (pre-R8). Passed locally 4× on identical code.

## Root cause (reproduced, not inferred)
1. Reproduced in a **fresh clone** in WSL (`git clone ~/jsy_disease_sim /tmp/jos-clean`, clean tree) with the test body instrumented to print the registry row: state `INTERRUPTED`, `error_code=artifact_provenance_mismatch`, "baseline scientific artifact has mismatched engine provenance". The same script on the dirty primary checkout: `SUCCEEDED`.
2. After the run the clean clone showed `?? .replicates-in-progress/`. R8 E-1 (`6e16e4a`, DISEASE-6 per-replicate persistence) wrote checkpoints to `<root>/.replicates-in-progress/<ensemble>/seed-N.json` where `root` = **project root** at every production call site (cli.py ×2, execution_adapter.py ×3).
3. Mechanism: `observed_engine_identity()` runs `git status --porcelain` at submission (clean → `dirty_worktree_flag=False`); the worker's scientific artifacts record identity **after** the baseline ensemble ran (tree now dirty → `True`); `JobFinalizer._verify_artifacts` compares `checked.dirty_worktree_flag is not submitted_dirty` → raises → `_reconcile_startup` records the failure and `reconcile_stale_jobs` marks the row INTERRUPTED. Local dev trees were already dirty (untracked `.replicates-in-progress/` from the P4 validation run), so both flags were `True` and the test passed — the reason the "flake / slow-runner" hypothesis looked plausible.
4. Why PROV-2/A-1 were ruled out: the reconciliation path is synchronous with no liveness or timing check (nothing for a slow runner to race); the A-1 finalizer hunk changes only the ensemble-config comparison, which is reached after the provenance check that actually fired.

## Fix (Codex gpt-5.6-luna@xhigh, session `01a06dab-e421-7be2-8069-50b592ebae58`, log `~/jos-fix-ckpt-codex1.log` in WSL)
- `run_ensemble(..., checkpoint_root: Path | None = None)`; default `root / "outputs" / ".replicates-in-progress"` (`outputs/*` is gitignored). `_replicate_state_path` / `_load_replicate_checkpoints` take the checkpoint root directly; all five persist/load sites threaded.
- `execution_adapter.py`: all three `run_ensemble` calls pass `checkpoint_root=job_directory / "checkpoints"` (job-owned, outside `artifacts/`). CLI keeps the default.
- Namespacing, resume, provenance authentication, schemas and hashes unchanged (checkpoint path enters no manifest/hash).
- Tests: restart test now asserts no `<comparison_id>-{baseline,treated}` namespace appears under `ROOT/.replicates-in-progress` and the job-dir checkpoints exist; `test_ensemble` asserts the default location; two `test_c4_contracts` checkpoint tests updated to the helper's new contract. Diff: 5 files, +38/−12.

## Evidence
| Check | Result |
|---|---|
| Failing-test-first: new assertion vs pre-change `src/` in the clean clone | `1 failed` — `assert not (root_checkpoint_directory / baseline_ensemble_id).exists()` → `assert not True` |
| End-to-end in clean clone with the branch diff applied | `STATE: SUCCEEDED`, `git status --porcelain` unchanged, no root `.replicates-in-progress` |
| Full suite in worktree (`uv run --locked pytest -q`) | `284 passed` in 533 s |
| `ruff check .` / `ruff format --check .` | clean / 157 files already formatted |
| mypy over CI's pinned module list | no issues in 15 files |
| Acceptance 4/5/6 (kwarg count 15 ≥ 5; old derivation absent; worktree clean after suite) | all pass |
| CI on pushed SHA `d873a80` (run 33910950203) | verify **success**, frontend **success** |

## Follow-ups
- After merge: the orphaned `~/jsy_disease_sim/.replicates-in-progress/p4-validation-r8/` (WSL loop home) is no longer a resume location; the run it belonged to completed, so it can be moved/deleted at leisure (untracked, harmless).
- PROV-2 (liveness lock) remains a real, separate Stage-E item — it was not the cause here.
- Pipeline lesson recorded (dev-delegate LESSONS): never place the spec as an untracked file inside the worktree.
