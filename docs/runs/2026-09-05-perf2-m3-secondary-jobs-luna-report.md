Implemented PERF-2 exact secondary-job rewrite.

Changed:

- [population_structure_generator.py](/home/steven/jos-perf2-wt/src/jersey_outbreak/population_structure_generator.py:871)
- [test_m3_secondary_jobs_oracle.py](/home/steven/jos-perf2-wt/tests/test_m3_secondary_jobs_oracle.py:21)

Transformations:

- T1: `Counter` tracks remaining slots per workplace; counts decrement/delete on pop.
- T2: `rng.choice` replaced by equivalent indexed `rng.integers` draw.
- T3: primary-job lookup indexed once.
- T4: ordered available-candidate list with incremental removal; filtering only when one workplace remains.

Evidence:

- Oracle: `3 passed`; 200 seeds × 6 lengths = 1,200 draw/state checks.
- Targeted gate: `18 passed in 121.33s`.
- Full suite: `309 passed, 5 warnings in 705.55s`.
- Full seed 101 hash: `b7d2fb34a7e08b6089c21f80b02c44f3f0eb6010c19ef72818f9c24b2ad54ccd`
- Full seed 101 runtime: `5.129s` (≤45s).
- Seed 102 branch/base hashes match: `b20ab2070f0ec2e4533a5c18768746678013a093c0a291f634b8423d684d3dff`.
- Ruff, format, mypy, lock, compileall, CLI generation, and `git diff --check`: passed.

Final status:

```text
 M src/jersey_outbreak/population_structure_generator.py
?? tests/test_m3_secondary_jobs_oracle.py
```

No other files, goldens, dependencies, or commits were changed.