# Robustness bundle (PROV-2 scheduler lock + liveness adoption, restart-test snapshot, data/raw -text): executor report (Codex gpt-5.6-luna@xhigh, fm.sh exec, 1 run, 2026-09-05 01:24→~02:05 local; foreman v12-run2 iteration 6)

*Verbatim `~/jos-robust.last.md`. Branch `fix/job-liveness-and-snapshot-eol` off `main` 635e8b5. Director gate results in trail row `robust-1`.*

Implemented the three fixes within scope.

- Added scheduler locking, `SchedulerLockError`, worker tokens, liveness adoption, and stale-job allow-list reconciliation.
- Added restart checkpoint namespace snapshotting.
- Added `data/raw/** -text` and its regression test.
- Added T1/T2/T3 in [tests/test_job_liveness.py](/home/steven/jos-robust-wt/tests/test_job_liveness.py).

Verification:

- Focused tests: `32 passed`
- Full suite: `293 passed`
- Ruff: passed
- Format check: passed
- Pinned mypy: passed
- Git attribute: `text: unset`
- Unexpected status lines: `0`
- Data changes: `0`

Criterion 2 note: the requested `git stash` was blocked because linked-worktree Git metadata is read-only:

```text
error: Unable to create .../index.lock: Read-only file system
```

Using a reversible diff reverse/apply equivalent, base tests failed during collection because `SchedulerLockError` was absent; restored branch tests passed (`32 passed`).

Diff stat:

```text
.gitattributes                      |   1 +
src/jersey_outbreak/job_manager.py  | 354 ++++++++++++++++++++++++-------
src/jersey_outbreak/job_registry.py |  23 ++-
tests/test_m9_1_job_integrity.py    |  13 +-
```

The new untracked test file adds 108 lines. No commit was created.