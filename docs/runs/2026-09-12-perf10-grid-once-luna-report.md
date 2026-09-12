Implemented PERF-10.

Changed:

- [ensemble.py](/home/steven/jos-p10-wt/src/jersey_outbreak/ensemble.py:562): reuse `replicate_grid` for summary generation; failed cells remain excluded from summary aggregation.
- [test_perf10_grid_once.py](/home/steven/jos-p10-wt/tests/test_perf10_grid_once.py:13): CLI-entry regression test asserting one grid build.

Acceptance evidence:

1. Base count:

```text
F [100%]
E       assert 2 == 1
1 failed in 5.34s
```

Branch:

```text
. [100%]
1 passed in 5.15s
```

2. A/B CLI runs both produced:

```text
logical_content_hash: 9a9ab9378cdd59c834ac9ec34fc285e93dc6115ecfe9d9e0087e5681b6e8d962
artifact_id: jos-ensemble-m6-perf10-ab-9a9ab9378cdd
```

Identical logical hashes and bytes:

```text
ensemble_summary.parquet
replicate_trajectories.parquet
replicate_grid.parquet
ensemble_config.json
date_grid: True
M2/M3/M4/M5 hashes: identical
```

`diff -r` differences were limited to:

```text
diagnostics.benchmark.peak_memory_bytes
diagnostics.benchmark.runtime_seconds
diagnostics.initializer_payload_bytes
diagnostics.job_payload_bytes_after
diagnostics.job_payload_bytes_before
manifest.created_at
manifest.dirty_worktree_flag
manifest.git_commit
manifest.output_artifacts[3].sha256
manifest.output_artifacts[3].size_bytes
manifest.output_artifacts[5].sha256
manifest.peak_memory_bytes
manifest.replicate_records[0..2].runtime_seconds
manifest.runtime_seconds
replicate_records[0..2].runtime_seconds
```

3. Existing failure/resume tests:

```text
.....                                                                    [100%]
5 passed in 2.11s
```

4. CI mirror:

```text
uv lock --check
Resolved 77 packages in 0.89ms

uv run python -m compileall -q src
<no output>

uv run pytest
================= 365 passed, 8 warnings in 974.19s (0:16:14) ==================

uv run ruff check .
All checks passed!

uv run ruff format --check .
221 files already formatted

uv run mypy --ignore-missing-imports ... ensemble.py
Success: no issues found in 16 source files

git diff --check
<no output>

uv run python scripts/ci_relocation_check.py
verifier success: m7_intervention jos-intervention-m7-ci-seed-123-c0be3d419f32
```

Golden fixtures:

```text
9 passed in 129.43s
```

Final status:

```text
 M src/jersey_outbreak/ensemble.py
?? tests/test_perf10_grid_once.py
```

```text
 src/jersey_outbreak/ensemble.py | 16 +++++++++++-----
 1 file changed, 11 insertions(+), 5 deletions(-)
```

New test stat:

```text
 /dev/null => tests/test_perf10_grid_once.py | 58 +++++++++++++++++++++++++++++
 1 file changed, 58 insertions(+)
```

Nothing remains undone. No commit created.