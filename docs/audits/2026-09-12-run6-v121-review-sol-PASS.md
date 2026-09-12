## Target verification

```text
$ git rev-parse HEAD
7439b9dbde3120c4601cd903d21e408fa7999432

$ git merge-base --is-ancestor 84b96763d9c5d6c85839218aba9d3876b96c8f7d HEAD && echo ancestor-ok
ancestor-ok
```

Final worktree status was clean. The first-parent chain contains the three declared no-ff merges in order: jobkw, DATA-4/DATA-5, then ROUTE-8.

## 1. Local CI mirror

```text
$ uv sync --frozen
Installed 75 packages

$ uv lock --check
Resolved 77 packages in 1ms

$ uv run python -m compileall -q src
(exit 0; no output)

$ uv run pytest
397 passed, 9 warnings in 818.31s (0:13:38)

$ uv run ruff check .
All checks passed!

$ uv run ruff format --check .
234 files already formatted

$ uv run mypy --ignore-missing-imports [CI list + four touched modules]
Success: no issues found in 17 source files

$ git diff --check
(exit 0; no output)
```

Relocation check:

```text
logical_content_hash=1e9f01ed1d770bbeb592c3d0c69add44040d2e80339b93b884b24701f4ed8a99
diagnostics_status=passed
verifier success: m7_intervention jos-intervention-m7-ci-seed-123-c0be3d419f32
```

Focused FIFO/API/liveness gate:

```text
$ uv run pytest -q tests/test_job_liveness.py tests/test_m9_api.py tests/test_m9_1_job_integrity.py
35 passed, 3 warnings in 39.88s
```

No caller passes arguments to `claim_next_queued()`.

## 2. Base/HEAD exactness

All requested CLI commands exited 0.

| Run | Base | HEAD |
|---|---|---|
| M4 network logical hash | `749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657` | identical |
| M8, 7-day latent hash | `77fee21a16fb9bd9b23c582dc4ee3500b11d4caf2e0093aa24d1855ff311698f` | identical |
| M8, 7-day temporary-network hash | `4ada33ca9d0e28799f18dda1ee02e6017832ff71219d467f92b51eafcfb27966` | identical |
| M8, 30-day latent hash | `02a98bb6f93fbe7bc48fd3f3519f5b56baec0e067aee77c724c9526f66a1d6fa` | identical |
| M8, 30-day temporary-network hash | `c3326e87849e697fd73a4c9c50adced3d2f4982efcac1a65a19c5af46e0f54e2` | identical |
| Ensemble, seeds 101–103, 7 days | `b58d169be8e384a52128ae2204f443bd0fbadef359aae909f6a285382139e8c3` | identical |

Across 12 corresponding manifests, all 26 `logical_content_hash` fields were identical. M2–M5 parent identities and every other scientific/configuration hash also matched.

For both 7- and 30-day M8 artifacts:

```text
files=27
byte-identical files=25
Parquet datasets=19
all Parquet datasets byte-identical=True
differing files=['diagnostics.json', 'manifest.json']
```

The 19 datasets were:

```text
daily_age, daily_epidemic, daily_high_risk, daily_parish, daily_route,
daily_travel_intervention_state, daily_travel_population, daily_travel_route,
detection_events, high_risk_strata, observation_events, seasonality_schedule,
temporary_edges, transmission_events, travel_episodes,
travel_intervention_events, travel_transmission_events, visitor_events,
visitor_population
```

The only diagnostics differences were:

```text
performance.peak_memory_bytes
performance.runtime_seconds
```

`event_time_identity_rows` was identical:

```text
7 days:   base=44  HEAD=44
30 days:  base=217 HEAD=217
```

Two-window route comparison:

```text
fingerprints identical
standard:      routes=11 dates=2  aggregate=e​​cbc278eaf81cff061d683e856e6c874f251c10abcbcf78a14d458941c47b2c7
term-boundary: routes=11 dates=21 aggregate=e31e7896323a025acc752eca12e6dcf6adb0aa971c689c7c95173beee996d62b
```

Every differing manifest key:

- M2 manifests: `created_at`, `dirty_worktree_flag`, `git_commit`, `peak_memory_bytes`, `runtime_seconds`, and SHA-256 records for `benchmark.json`, `diagnostics.json`, and `diagnostics.md`.
- M3 manifests: the M2 set plus `m2_manifest_hash`; the same three output SHA-256 records. One direct seed-123 M3 run also differed in those records’ `size_bytes`.
- M4 manifest: `created_at`, `dirty_worktree_flag`, `git_commit`, `peak_memory_bytes`, `runtime_seconds`, and SHA-256/size records for `benchmark.json` and `diagnostics.json`.
- M6 ensemble: `created_at`, `dirty_worktree_flag`, `git_commit`, `peak_memory_bytes`, `runtime_seconds`, `replicate_records[*].runtime_seconds`, the diagnostics SHA-256 record, and the `replicate_records.json` SHA-256/size record.
- Both M8 manifests: `created_at`, `dirty_worktree_flag`, `git_commit`, `peak_memory_bytes`, `runtime_seconds`, and the diagnostics SHA-256/size record.

## 3. Highest-risk checks

Identity intervals, three episodes reusing UID 3000:

```text
episodes_equal True
slot_reuse True uid 3000
contains_DAY_VISITOR True
head_resolved_equals_base_map_every_ti True timesteps 6
inactive_timesteps ['3000:1', '3000:3', '3000:5']
head_interval_count 3
```

ROUTE-8 real four-date M4 construction:

```text
BASE: snapshot_dates=4 routes=11 constructions=91 ideal=44
HEAD: snapshot_dates=4 routes=11 constructions=44 ideal=44
```

HEAD build replay:

```text
snapshot_dates=2 constructions=22 ideal=22 match=True
snapshot_dates=3 constructions=33 ideal=33 match=True
snapshot_dates=4 constructions=44 ideal=44 match=True
snapshot_dates=5 constructions=55 ideal=55 match=True
```

Default CI runtime cache:

```text
default_snapshot_dates=3 routes=11 reported_capacity=33 seven_day_peak=33 bound_ok=True
```

30-day travel peak RSS:

```text
BASE 437344 KB
HEAD 441028 KB
```

## 4. Scope

```text
 .claude/FRONTIER.md                                |   6 +-
 .claude/GATES.md                                   |   5 +
 .claude/RUN.md                                     |  15 +-
 .claude/decisions.tsv                              |   6 +
 docs/audits/2026-09-12-run5-v121-review-sol-PASS.md | 259 +++++++++++++++++++++
 docs/runs/2026-09-12-prov-job-ordering-attempt1-luna-report.md | 82 +++++++
 docs/runs/2026-09-12-prov-job-ordering-luna-report.md | 89 +++++++
 docs/runs/2026-09-12-run5-integration-ci-mirror.log | 67 ++++++
 src/jersey_outbreak/job_registry.py                |   7 +-
 src/jersey_outbreak/network_artifacts.py           |  55 ++---
 src/jersey_outbreak/network_generator.py           |  55 ++++-
 src/jersey_outbreak/travel.py                      | 142 ++++++-----
 tests/fixtures/base_travel_identity_ci.json        |   1 +
 tests/test_m8_travel.py                            |  67 ++++++
 tests/test_networks.py                             |  92 +++++++-
 15 files changed, 841 insertions(+), 107 deletions(-)
```

No dependency file, schema module, existing golden fixture, or `tests/test_golden_hashes.py` changed. The only fixture addition is the declared base travel-identity fixture. No undeclared hash/schema change was found.

## Findings

| Severity | File:line | Finding |
|---|---|---|
| MINOR | [.claude/FRONTIER.md](/home/steven/jos-review6-wd/.claude/FRONTIER.md:5), [.claude/GATES.md](/home/steven/jos-review6-wd/.claude/GATES.md:7), [.claude/RUN.md](/home/steven/jos-review6-wd/.claude/RUN.md:1), [.claude/decisions.tsv](/home/steven/jos-review6-wd/.claude/decisions.tsv:215), four run-5 documents at line 1 | Eight ancillary run-5/trail files appear outside the three unit diffs because the travel and ROUTE-8 branches descend from `c7d3876`. They are byte-exact copies of that mainline state, and the four added documents remain identical on `main`; this is nonblocking for the prescribed merge after run-5. |
| — | — | No MAJOR findings. All declared scientific, API, liveness, exactness, cache-bound, and CI gates passed. |

JOS V1.2.1 INTEGRATION-RUN6 REVIEW PASS