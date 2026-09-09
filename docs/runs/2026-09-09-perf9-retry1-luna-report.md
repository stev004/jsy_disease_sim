Implemented and verified PERF-9 retry.

- Adapter reuse now uses the existing `job_directory` parent tree for all three adapter modes. Identical invocations reuse M2/M3 with zero generator calls; changed seeds cold-build. See [execution_adapter.py](/home/steven/jos-p9-wt/src/jersey_outbreak/execution_adapter.py:257) and [test_perf9_parent_reuse.py](/home/steven/jos-p9-wt/tests/test_perf9_parent_reuse.py:23).
- Sequential diagnostics no longer include pool-only payload fields. Pool diagnostics remain available only for process-pool execution. See [ensemble.py](/home/steven/jos-p9-wt/src/jersey_outbreak/ensemble.py:1176).
- Pre-fix diff reproduced the three added fields; post-fix protected hashes, parquet, summaries, configuration, and provenance match. Remaining differences are existing runtime/timestamp operational fields only.

Verification:

- Focused suite: `81 passed`
- Full suite: `344 passed, 8 warnings`
- Four-seed base/current hashes match: ensemble `7be9e432…`; per-replicate hashes identical for seeds 123–126.
- Resume smoke: killed status `143`; resumed hash equals clean hash `a38c09a4…`.
- Mypy: 18 files, no issues.
- Ruff: passed; 208 files formatted.
- `git diff --check`: passed.
- No commit created.

Status:

```text
 M src/jersey_outbreak/ensemble.py
 M src/jersey_outbreak/execution_adapter.py
 M tests/test_perf9_parent_reuse.py
?? docs/audits/2026-09-09-run4b-perf-review-sol-BLOCKED.md
```

Diff stat: `3 files changed, 78 insertions(+), 6 deletions(-)`.