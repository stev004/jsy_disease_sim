Implemented PERF-4 and shipped the ensemble wiring.

Base SHA: `36e1945e2d0b9ee5db95daa9611a9ed3f6df44a3`  
Current `origin/main`: `53a5ea62843dca2ece814b1cd5e0f8e98c7b7b36`

Design:

- Added keyword-only `diagnostics="full" | "internal"`; default remains `full`.
- Internal mode skips `_route_diagnostics` and descriptive participation summaries only.
- Hash inputs, snapshots, staffing diagnostics/provenance, contact activity, calendars, and route-overlap validation remain unchanged.
- Ensemble replicate construction passes `diagnostics="internal"`.
- Internal M4 objects are never written as public network artifacts; the worker test guards this.
- CLI and artifact-generation paths retain default full diagnostics.

Consumer audit:

| Consumer/key | Internal behavior |
|---|---|
| `network_artifacts.py`: `diagnostics["routes"]` | Internal marker; internal objects are not passed to the public writer. |
| `network_artifacts.py`: `zero_non_household_contacts` | Explicit omission marker. |
| `cross_route.agents_by_route_type_count` | Explicit omission marker; no production reader found. |
| `cross_route.community_participation_by_residence_type` | Explicit omission marker; only full-mode tests read it. |
| `cross_route.route_participation` | Explicit omission marker; no existing reader. |
| Staffing, provenance, calendars, shared vehicles, route-overlap validation | Preserved unchanged. |

Benchmark command:

`scripts/bench_perf4_diagnostics.py --mode full --seed 101 --repeats 5`

| Repeat | Full | Internal |
|---:|---:|---:|
| 1 | 28.929 s | 20.888 s |
| 2 | 29.049 s | 20.862 s |
| 3 | 29.392 s | 21.038 s |
| 4 | 29.702 s | 21.195 s |
| 5 | 28.711 s | 20.741 s |
| Median | 29.049 s | 20.888 s |

Median saving: **8.161 s**. Ship threshold passed; ensemble wiring retained.

Verification:

- `tests/test_perf4_diagnostics.py`: **7 passed**
- Required focused suite: **82 passed, 3 warnings**
- Full suite: **328 passed, 5 warnings**
- Mypy: **no issues in 15 source files**
- `uv lock --check`: passed
- Compileall: passed
- Ruff check/format: passed
- CLI network generation: passed
- Relocation check: passed
- `git diff --check`: passed
- Two-seed, 7-day, `workers=2` ensemble hash comparison: passed
- Default/full artifact parity confirmed, excluding timing fields: manifest `created_at`, `runtime_seconds`, `peak_memory_bytes`; benchmark construction runtime/peak memory; diagnostics benchmark runtime/peak memory.

Changed files only:

- `src/jersey_outbreak/network_generator.py`
- `src/jersey_outbreak/ensemble.py`
- `tests/test_perf4_diagnostics.py`
- `scripts/bench_perf4_diagnostics.py`

Current status:

```text
 M src/jersey_outbreak/ensemble.py
 M src/jersey_outbreak/network_generator.py
?? scripts/bench_perf4_diagnostics.py
?? tests/test_perf4_diagnostics.py
```

No commit created.