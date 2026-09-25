**PASS — all four blocking and both major findings are resolved.** No campaign execution or commit was made.

The worktree is on `codex/v13-p0b-implementation`, still at `84228b66aa6adcd0bb4a1f55e8651bb1b1edbd8b`. It was clean at the start. The only modified files are the Phase-0b config, campaign module, and Phase-0b tests.

### Findings

- **B1 — Production P0-1 decimals:** The runner now passes the validated config to the truth join after blind-estimate persistence and read-back in [phase0_campaign.py](/home/steven/jos-p0b-wt/src/jersey_outbreak/phase0_campaign.py:2777). `test_phase0b_production_p01_path_joins_exact_declared_decimals_after_readback` drives that path with mocked simulator boundaries and checks the declared Decimal endpoints for beta, offset, and both detection probabilities, including inclusive hit and non-boundary classification. The focused run passed: **57 passed**.

- **B2 — Recovery predicates:** Phase-0b recovery rows now include per-dimension tolerance hits and boundary flags, joint hit, tie status, and truth viability, chronology, conservation, and namespace values in [phase0_campaign.py](/home/steven/jos-p0b-wt/src/jersey_outbreak/phase0_campaign.py:2242). `test_phase0b_mocked_full_orchestration_and_bundle_cold_recomputation` checks those columns against blind-estimate and retained truth-diagnostic files. Focused run: **57 passed**.

- **B3 — P0-2 clause states:** Phase-0b `as_dict()` and CSV publication emit `TRUE`, `FALSE`, or `UNKNOWN` for clauses while preserving null estimate and error fields in [phase0_campaign.py](/home/steven/jos-p0b-wt/src/jersey_outbreak/phase0_campaign.py:897) and [phase0_campaign.py](/home/steven/jos-p0b-wt/src/jersey_outbreak/phase0_campaign.py:4062). `test_phase0b_p02_clause_serialization_uses_g29_states` and the mocked bundle test passed in the **57 passed** focused run.

- **B4 — Phase-0 lineage:** Historical P0-2A, P0-2B, and P0-3 PASS evidence now sits inside `PHASE0_LINEAGE`; the summary root field was removed in [phase0_campaign.py](/home/steven/jos-p0b-wt/src/jersey_outbreak/phase0_campaign.py:146). The mocked bundle test asserts each requested lineage field individually and passed in the **57 passed** focused run.

- **M1 — Decimal-string grids:** Phase-0b’s P0-2B and P0-3 grids are YAML strings in [v13_phase0b_synthetic.yaml](/home/steven/jos-p0b-wt/configs/calibration/v13_phase0b_synthetic.yaml:146); independent constants are strings and runtime parsing uses `Decimal` before conversion in [phase0_campaign.py](/home/steven/jos-p0b-wt/src/jersey_outbreak/phase0_campaign.py:65) and [phase0_campaign.py](/home/steven/jos-p0b-wt/src/jersey_outbreak/phase0_campaign.py:1095). `test_phase0b_profile_is_independently_frozen_and_workload_is_exact` and the three parameter cases in `test_phase0b_secondary_grids_reject_numeric_yaml_values` passed in the **57 passed** focused run.

- **M2 — Predeclaration filename:** The Phase-0b digest file now names `predeclaration.md` in [phase0_campaign.py](/home/steven/jos-p0b-wt/src/jersey_outbreak/phase0_campaign.py:4003). The mocked bundle test verifies the filename and `SHA256SUMS` coverage; it passed in the **57 passed** focused run.

### Verification

- `ruff check`: **All checks passed**. `ruff format --check`: **2 files already formatted**.
- `mypy --ignore-missing-imports`: **Success: no issues found in 1 source file**. `compileall`: exit 0.
- Phase-0 dry run: **198 cells / 59 latent calls / 599 transforms / 8 builds**. Phase-0b: **1,334 / 107 / 4,007 / 8**.
- Phase-0 tests and Phase-0b tests: **57 passed**.
- Base-versus-head fixture: **20/20 Phase-0 recovery row dictionaries equal**; coverage, bias, boundary, joint, and predicate results equal. Production-config hash comparison: **81/81 P0-1 hashes equal** and **9/9 P0-3 hashes equal**.
- Full `uv run pytest`: **467 passed, 4 skipped, 15 warnings in 961.79s**. The known `test_missing_head_request_fails_alone*` flake did not recur.
- `git diff --check`: passed. Diff stat: **3 files changed, 532 insertions(+), 77 deletions(-)**.

Verification output is saved at [`/tmp/jos-p0b-r1-evidence.log`](/tmp/jos-p0b-r1-evidence.log).