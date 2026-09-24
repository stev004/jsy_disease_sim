# P0-3 director implementation review: KEEP (pending mirror + all-arms Sol review)

This is an implementation acceptance, not a scientific Phase-0 verdict. No campaign arm has run, and `execute` was not invoked.

- **Candidate:** `29f43d131f568868259d64a459f889e027d31e21` on `codex/v13-p0-3-negative-control`. Its parent is the accepted P0-2 head `ae885295fca56d60f3e8ed5f33274a752d096d20`. The director committed it; it is not pushed.
- **Executor:** gpt-6-luna @ xhigh, attempt 1 of 3, session `01a0d0ba-1277-7f90-80f2-390802b6594d`, **456,047 tokens**. It took about 51 minutes against a 45-minute timebox; it finished with a report rather than being stopped. Report: `docs/runs/2026-09-24-phase0-p03-luna-report.md`. Evidence log: `...-p03-evidence.log`.
- **Scope:** three authorized files, +1242/−83. The YAML adds the declared `negative_control` block and sets `implemented_arms` to all four arms. `calibration.py` is imported only; `_profile_beta_nuisance` and `_record_argmin_shifts` are unmodified.

## Full source diff read against predeclaration §4–§7

- **Grid:** beta (0.04, 0.08, 0.16) × factor (0.5, 1.0, 2.0). The factor replaces all eleven route multipliers uniformly, which is equivalent to multiplying them because the base multipliers are all 1.0. It applies only in `_p03_run_config_for_cell`.
- **Fixed settings:** inoculation timing and ascertainment are held at the P0-1 truths. The arm uses the candidate seed pairs and config id, and reuses the P0-1 `generated_parents`, so no new builds are made.
- **Work guards:** exactly 27 latent calls and 27 transforms, each guarded before dispatch. P0-1 dispatch also gained build, latent and transform cap guards.
- **Ridge products:** 0.16×0.5, 0.08×1 and 0.04×2 are all exact in binary floating point. Whether the simulated vectors actually agree is the empirical question the campaign answers; it is not a code defect.
- **Classifier:** checks all six §4 predicates against the actual flattened prediction vectors (replicate × channel × date) and their SHA-256 hashes, the ridge-objective spread, and full per-factor argmin/shift/profile reporting, with the reference set to the factor-1 argmin. It requires a null `factor_estimate` and no standard error, interval or coverage keys anywhere in the profiles. Tests cover five deliberately failing fixtures.
- **Orchestration:** measured work is checked against the plan (P0-1 32/248; P0-2 0 latent + 243/81 transforms; P0-3 27/27; 8 builds; totals 59/599). Overall Phase-0 status is PASS only if every arm's software and scientific status is PASS; any FAIL makes it FAIL; anything else is NOT_ESTABLISHED. That is consistent with ruling item 5. A mocked run is marked `NOT_EVALUATED`/`MOCKED`.
- **Bundle:** written to a staging directory and then published with an atomic `os.replace`. A non-empty destination is rejected before any generation, and staging is removed on failure. The bundle includes the config and its SHA-256, the declaration and ruling hashes, the ruling copy, `input_hashes.json` (every `src/jersey_outbreak/*.py`, the two demo configs, the config, the declaration and the ruling), the seed ledger, and all §6 files plus SHA256SUMS.
- **Hash stability (executor, vs ae88529):** P0-1 target 5/5, P0-1 candidates 81/81, P0-2A 81/81 and P0-2B 27/27 are identical, and the blind hash `2ebc1f18…7421a` is unchanged.

## Points for the all-arms review (not decided by the director)

1. **Blind-record retention.** Blind estimate JSON records are persisted and read back in a `TemporaryDirectory` workspace that is deleted after publication. The bundle keeps estimate hashes (in the P0-2 provenance and recovery rows) but not the records themselves, so a cold auditor cannot re-verify from the bundle alone that each record was durable before its truth join. Decide whether §6 plus the blind-fitting rule require these records in the bundle.
2. **`execute` is now live.** The frozen unit order runs the campaign only after this review passes. Confirm nothing in the code, tests or CLI runs it implicitly: `mocked_for_test` is a Python keyword and not a CLI flag.
3. **Minor code smell.** The P0-3 transform count is checked against `plan.p03_latent_calls`. The value 27 happens to be right, but it is compared against the wrong field name.
4. **Carried open question.** How exact boundaries on computed quantities should behave (P0-1 profile gap, R_i, E_i). The P0-3 thresholds of 1e-12 are absolute and relative float comparisons.

## Next steps

Director clean-clone CI mirror at `29f43d1`, then the full all-arms gpt-6-sol code review (`367f032..29f43d1`, and optionally from `3ff3734`), then the campaign decision under the frozen unit order.
