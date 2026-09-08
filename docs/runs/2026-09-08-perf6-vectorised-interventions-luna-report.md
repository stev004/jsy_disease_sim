Implemented PERF-6 vectorized intervention route application.

Design:
- Columnar `RouteSnapshot` arrays remain columnar; no per-edge Python loop.
- Per-config endpoint predicate vectors cover isolation, quarantine, school, workplace/WFH, community, and care logic.
- Config factors compose left-to-right with in-place multiplication, NaN guard, clamping, care zero-beta retention, and bit-identical beta multiplication.
- Scalar `_edge_multiplier` remains intact as oracle.

Evidence:

- Base SHA: `34b661c84270bb88d2257f69db51aa0c63c3fa1b`
- Parity tests: `15 passed`; all 13 scenario files checked over 30 days; no differing scenario/day/route/edge.
- Requested regression set: `80 passed`.
- Full suite: `350 passed`.
- Full benchmark:

| Mode | Scalar | Vector | Speedup |
|---|---:|---:|---:|
| full / seed 101 / 30d / m7_combined | 37.504 s | 11.650 s | 3.22× |

Full base/branch hashes and intervention parquet outputs matched for both Astra cases. CI hashes, observation hashes, event counts, state rows, and route-effect rows matched for all 11 M7 scenarios.

CI mirror passed:

- `uv lock --check`
- compileall
- Ruff check/format
- mypy: 15 modules
- `git diff --check`

Files changed:

- [interventions.py](/home/steven/jos-p6-wt/src/jersey_outbreak/interventions.py:854)
- [test_perf6_interventions.py](/home/steven/jos-p6-wt/tests/test_perf6_interventions.py:1)
- [bench_perf6_interventions.py](/home/steven/jos-p6-wt/scripts/bench_perf6_interventions.py:1)

Status:

```text
 M src/jersey_outbreak/interventions.py
?? scripts/bench_perf6_interventions.py
?? tests/test_perf6_interventions.py
```

No commit created.