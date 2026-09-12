## REPORT

Implemented DATA-4/DATA-5 in [travel.py](/home/steven/jos-trav-wt/src/jersey_outbreak/travel.py):

- Cached visitor/resident episode partitions once in `TravelPlan`.
- Replaced per-timestep identity dictionaries with per-UID episode intervals.
- Replaced per-resident `initial_away` scans with one resident-episode pass.
- Preserved route evidence as the sole retained edge store; flat artifact rows remain output-only.
- Preserved `event_time_identity_rows` diagnostics and all artifact schemas/hashes.

Added base-reference identity regression coverage and fixture in [test_m8_travel.py](/home/steven/jos-trav-wt/tests/test_m8_travel.py) and [base_travel_identity_ci.json](/home/steven/jos-trav-wt/tests/fixtures/base_travel_identity_ci.json).

### Acceptance evidence

Identity and partition test:

```text
uv run pytest -q tests/test_m8_travel.py::test_returning_resident_absence_is_separate_from_visitor_presence tests/test_m8_travel.py::test_identity_intervals_match_base_event_time_mapping

..                                                                       [100%]
2 passed in 2.61s
```

Base partition allocation count versus branch:

```text
base:
visitor_accesses=5 distinct_materialized_tuple_ids= 5
resident_accesses=5 distinct_materialized_tuple_ids= 1

branch:
visitor_accesses=5 distinct_materialized_tuple_ids= 1
resident_accesses=5 distinct_materialized_tuple_ids= 1
```

Retained-store sizes from the 30-day CI run:

| Store | Base bytes | Branch bytes | Base entries | Branch entries |
|---|---:|---:|---:|---:|
| `route_edge_history` | 569312 | 569312 | 210 | 210 |
| `_identity_by_uid_ti` → interval store | 185589 | 79853 | 217 timestep records | 81 episode records |
| `temporary_edge_history` | 56 | 56 | 0 | 0 |

Hashes matched:

```text
temporary_network: c3326e87849e697fd73a4c9c50adced3d2f4982efcac1a65a19c5af46e0f54e2
latent:            02a98bb6f93fbe7bc48fd3f3519f5b56baec0e067aee77c724c9526f66a1d6fa
artifact_bundle:   2dfe4357a89ce37deeb55447010247c0aab8053a2caee6a814c6184ecf6e500f
```

M8 golden test:

```text
uv run pytest -q tests/test_golden_hashes.py::test_m8_shipped_config_golden_hashes

1 passed in 70.51s
```

CLI CI smoke:

```text
diagnostics_status: passed
latent_outcome_hash: 02a98bb6f93fbe7bc48fd3f3519f5b56baec0e067aee77c724c9526f66a1d6fa
temporary_network_hash: c3326e87849e697fd73a4c9c50adced3d2f4982efcac1a65a19c5af46e0f54e2
visitor_count: 81
```

All 27 artifact files matched after excluding execution metadata:

```text
daily_age.parquet PASS
daily_epidemic.parquet PASS
daily_high_risk.parquet PASS
daily_parish.parquet PASS
daily_route.parquet PASS
daily_travel_intervention_state.parquet PASS
daily_travel_population.parquet PASS
daily_travel_route.parquet PASS
detection_events.parquet PASS
diagnostics.json PASS
high_risk_strata.parquet PASS
manifest.json PASS
observation_config.json PASS
observation_events.parquet PASS
parameters.json PASS
parent_reference.json PASS
run_config.json PASS
scenario_config.json PASS
seasonality_schedule.parquet PASS
temporary_edges.parquet PASS
transmission_events.parquet PASS
travel_config.json PASS
travel_episodes.parquet PASS
travel_intervention_events.parquet PASS
travel_transmission_events.parquet PASS
visitor_events.parquet PASS
visitor_population.parquet PASS
```

The raw `diagnostics.json` differs only in execution fields `runtime_seconds` and `peak_memory_bytes`; the manifest’s propagated diagnostics checksum differs for the same reason.

Golden hashes remained unchanged for all eight shipped configurations.

Timing: CLI CI run was 10.64 seconds on the branch versus 12.90 seconds on the archived base run; not gated.

### Verification

```text
uv sync --frozen
Checked 75 packages in 0.73ms

uv lock --check
Resolved 77 packages in 0.69ms

uv run pytest
================= 365 passed, 8 warnings in 878.70s (0:14:38) ==================

uv run ruff check .
All checks passed!

uv run ruff format --check .
229 files already formatted

uv run mypy --ignore-missing-imports [CI module list + travel.py]
Success: no issues found in 16 source files

git diff --check
PASS

uv run python scripts/ci_relocation_check.py
verifier success: m7_intervention jos-intervention-m7-ci-seed-123-c0be3d419f32
```

### Worktree

```text
 M src/jersey_outbreak/travel.py
 M tests/test_m8_travel.py
?? tests/fixtures/base_travel_identity_ci.json
```

```text
 src/jersey_outbreak/travel.py | 142 +++++++++++++++++++++++++-----------------
 tests/test_m8_travel.py       |  67 ++++++++++++++++++++
 2 files changed, 153 insertions(+), 56 deletions(-)
```

No commits made.