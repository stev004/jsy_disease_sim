Implemented PERF-9 on base `284caff4c3eab14acf8c8abe882e9d1307ff5f5b`.

Design:

- [`parent_build.py`](/home/steven/jos-p9-wt/src/jersey_outbreak/parent_build.py:78): exact M2/M3 manifest matching, verified loader reuse, M2 linkage and M3 logical-hash checks, clear rejection/fresh-build logging.
- [`ensemble.py`](/home/steven/jos-p9-wt/src/jersey_outbreak/ensemble.py:89): spawn-pool initializer transfers immutable parents once; jobs omit parent payloads. Resume provenance is unchanged.
- Added `--reuse-from` plumbing through CLI and execution adapter.
- Added [`test_perf9_parent_reuse.py`](/home/steven/jos-p9-wt/tests/test_perf9_parent_reuse.py:21).

Verification:

- Full suite: `343 passed`, 5 existing warnings.
- `uv lock --check`, compileall, Ruff, mypy (17 modules), and `git diff --check`: passed.
- Sequential/parallel seeds 123–126, 7 days: hashes equal; `process_pool_spawn`, `actual_workers=2`.
- Payload measured: before `7,524,144` bytes; after `43,200` bytes; initializer `1,779,964` bytes.
- Resume: `resumed=4 run=0`, identical ensemble hash.
- Parent CLI timing: cold `4.87s`, verified reuse `3.87s`.
- Base/branch ensemble logical hash: `40b4f7f993e129e421ff5742a37fa794d154e6e5b64f890c6cd8bd9fc1828760`; per-replicate hashes matched.

Working tree contains only the four source changes and the new PERF-9 test; no commit created.