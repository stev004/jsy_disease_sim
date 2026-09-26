**Verdict: FAIL at the byte-identity gate; sweep stopped at the first difference.** The fix passes all four requested structure builds, but seed 123’s exact artifact-file hashes differ, so I cannot report the required identity result.

The base diagnosis was reproduced for all four seeds. Seeds 62001, 62003, and 63002 exhausted Trinity’s under-16 pool; 62002 exhausted St Peter’s adult pool.

The implementation snapshots parish state and retries only a parish whose original assignment fails, deferring its `other` roles until constrained roles are placed. It adds the disclosure only when fallback is used. The authorized changes are [population_generator.py](/home/steven/jos-popfix-wt/src/jersey_outbreak/population_generator.py) and the new [test_popgen_residual_fallback.py](/home/steven/jos-popfix-wt/tests/test_popgen_residual_fallback.py).

All four `jos structure generate --mode ci` builds passed with `diagnostics_status: passed`. Their M2 diagnostics report:

| Seed | Parish | Deferred `other` roles |
|---:|---|---:|
| 62001 | Trinity | 11 |
| 62002 | St Peter | 3 |
| 62003 | Trinity | 8 |
| 63002 | Trinity | 7 |

For seed 123, base and fixed builds had the same M2/M3 artifact IDs, logical content hashes, and all Parquet file hashes. However, `benchmark.json`, `diagnostics.json`, `diagnostics.md`, and `manifest.json` differed in each artifact layer. Under the task’s exact-file requirement, seed 123 is **DIFFERENT**, so I stopped the sweep as instructed. No other seeds in the requested identity set were compared; base failures among CI seeds 1–150 remain unknown. The partial table is at [`/tmp/jos-popfix-identity.tsv`](/tmp/jos-popfix-identity.tsv).

Ruff format, Ruff check, mypy, and `git diff --check` passed. The new test, `tests/test_golden_hashes.py`, and the full suite were **not run** after the identity stop. The source diff stat is 131 insertions and 42 deletions; `git diff --stat` excludes the untracked test file.

HEAD remains `024caa09c19bbdad0952b09213ed56e6638ad676`. The worktree contains only the two scoped changes. The transcript and detached base clone are under `/tmp` (`/tmp/jos-popfix-evidence.log`, `/tmp/jos-popfix-base`); this session’s writable roots do not include the requested `/home/steven` destinations.