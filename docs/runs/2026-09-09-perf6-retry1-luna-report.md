Implemented and verified. No commit created.

Root cause: `_vector_community_adheres()` returned all-false for targeted or `residents_only` configs, suppressing valid resident reductions.

Fix in [interventions.py:883](/home/steven/jos-p6-wt/src/jersey_outbreak/interventions.py:883):

- Resident endpoints use `_vector_target_adheres()`.
- Untargeted `everyone_present` visitors use `_intervention_adheres()`.
- Targeted visitors and `residents_only` visitors remain false.
- All scalar target restrictions and adherence caching remain aligned.

Tests:

- Failing-first: 4 failures on HEAD.
- After fix: `4 passed`.
- Schema grid: 990 generated configurations, 7 days, all routes, all target fields, scopes, kinds, adherence values, care targets, and both overlap orders: passed in 234.56s.
- Focused gate batch: `74 passed`.
- Full suite: `355 passed, 5 warnings`.

End-to-end review probe (`ci`, seed 123, 14 days, `age_min=18`, residents-only):

| Metric | Base | Candidate |
|---|---|---|
| Latent logical hash | `a8665686…` | `a8665686…` |
| Latent outcome hash | `301baed3…` | `301baed3…` |
| Observation hash | `a4ace7ae…` | `a4ace7ae…` |
| Transmission events | 298 | 298 |
| Day-one mean multiplier | 0.5411398377052274 | 0.5411398377052274 |

Full seed-101, 30-day runs matched the archived base for both `m7_combined` and `m7_community_indoor`; all 8 parquet files were byte-identical in each run.

Benchmark:

| Scenario | Scalar | Vector | Speedup |
|---|---:|---:|---:|
| `m7_combined` full | 37.337633s | 11.368594s | 3.28× |
| `m7_community_indoor` full | 15.667411s | 0.448884s | 34.90× |

Static gates passed: Ruff, format, lock check, compileall, 15-module mypy, and `git diff --check`.

Changed files:

- [interventions.py](/home/steven/jos-p6-wt/src/jersey_outbreak/interventions.py)
- [test_perf6_interventions.py](/home/steven/jos-p6-wt/tests/test_perf6_interventions.py)

Diff stat: `345 insertions(+), 9 deletions(-)`. The benchmark script was unchanged.