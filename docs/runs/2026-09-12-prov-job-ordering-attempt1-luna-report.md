Implemented PROV-7, PROV-9, and heartbeat/stall handling for PROV-10.

Changes:

- [job_manager.py](/home/steven/jos-job-wt/src/jersey_outbreak/job_manager.py:374): persist request files inside the registry transaction before enqueueing; durable JSON writes; missing-request claim precondition; supervisor no longer writes heartbeats; optional `heartbeat_stall_timeout=None`.
- [job_registry.py](/home/steven/jos-job-wt/src/jersey_outbreak/job_registry.py:228): added pre-enqueue persistence callback, FIFO-safe claim precondition, `synchronous=FULL`, and removed non-worker heartbeat publication.
- [job_finalizer.py](/home/steven/jos-job-wt/src/jersey_outbreak/job_finalizer.py:500): stage and verify manifest, commit registry success, then rename; fsync file/directories; clean staged files on failure.
- Added [test_prov_job_ordering.py](/home/steven/jos-job-wt/tests/test_prov_job_ordering.py:1).

Acceptance evidence:

```text
BASE:
FFFF
... final state=FAILED, error=worker_execution_failed
... result_manifest.json exists
... heartbeat changed
... unexpected keyword argument 'heartbeat_stall_timeout'
4 failed in 3.77s

BRANCH:
....                                                                     [100%]
4 passed in 11.03s
```

```text
$ uv run pytest tests/test_m9_api.py::test_registry_state_machine_and_fifo_atomic_claim tests/test_job_liveness.py -q
.....                                                                    [100%]
5 passed, 1 warning in 0.70s
```

```text
$ uv run pytest tests/test_m9_api.py -q
7 passed, 1 warning in 7.91s
```

Final CI verification:

```text
uv lock --check
Resolved 77 packages in 0.77ms

uv run python -m compileall -q src
[no output; exit 0]

uv run pytest
================= 368 passed, 8 warnings in 843.58s (0:14:03) ==================

uv run ruff check .
All checks passed!

uv run ruff format --check .
221 files already formatted

uv run mypy --ignore-missing-imports ... 
Success: no issues found in 18 source files

git diff --check
[no output; exit 0]

uv run python scripts/ci_relocation_check.py
verifier success: m7_intervention jos-intervention-m7-ci-seed-123-c0be3d419f32
```

Status:

```text
 M src/jersey_outbreak/job_finalizer.py
 M src/jersey_outbreak/job_manager.py
 M src/jersey_outbreak/job_registry.py
?? tests/test_prov_job_ordering.py
```

```text
git diff --stat
 src/jersey_outbreak/job_finalizer.py |  89 ++++++++++++++-------
 src/jersey_outbreak/job_manager.py  | 147 +++++++++++++++++++++------------
 src/jersey_outbreak/job_registry.py |  23 ++++--
 3 files changed, 175 insertions(+), 84 deletions(-)
```

The untracked regression file adds 212 lines. No commit made. No wall-clock timeout was added; that remains outside the requested heartbeat-half scope.