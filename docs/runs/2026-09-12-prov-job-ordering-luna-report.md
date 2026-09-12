# REPORT

Implemented retry-2 liveness fix.

- `job_manager.py`: claims FIFO head normally; missing `request.json` is immediately failed with `request_not_persisted`, emits `job_failed`, skips spawning, and continues to B. Documented as non-transient.
- `tests/test_prov_job_ordering.py`: added A/B deletion regression with spawn counter.
- Existing retry-1 changes in `job_registry.py` and `job_finalizer.py` preserved unchanged.

Failing test before fix:

```text
$ uv run pytest tests/test_prov_job_ordering.py::test_missing_head_request_fails_alone_and_scheduler_continues -q
E           AssertionError: ... 
E           assert 'QUEUED' == 'FAILED'
1 failed in 5.39s
```

Passing after fix:

```text
$ uv run pytest tests/test_prov_job_ordering.py::test_missing_head_request_fails_alone_and_scheduler_continues -q
.                                                                        [100%]
1 passed in 3.90s

$ uv run pytest tests/test_prov_job_ordering.py -q
.....                                                                    [100%]
5 passed in 15.47s
```

Existing FIFO/atomic claim and liveness tests:

```text
$ uv run pytest tests/test_prov_job_ordering.py tests/test_m9_api.py::test_registry_state_machine_and_fifo_atomic_claim tests/test_job_liveness.py tests/test_m9_api.py -q
.................                                                        [100%]
17 passed, 1 warning in 20.53s
```

Full suite:

```text
$ uv run pytest
================= 369 passed, 8 warnings in 811.74s (0:13:31) ==================
```

Verification:

```text
$ uv sync --frozen
Checked 75 packages in 0.79ms

$ uv lock --check
Resolved 77 packages in 0.84ms

$ uv run python -m compileall -q src
(no output)

$ uv run ruff check .
All checks passed!

$ uv run ruff format --check .
221 files already formatted

$ uv run mypy --ignore-missing-imports [CI module list + job_manager.py + job_registry.py + job_finalizer.py]
Success: no issues found in 18 source files

$ git diff --check
(no output)

$ uv run python scripts/ci_relocation_check.py
verifier success: m7_intervention jos-intervention-m7-ci-seed-123-c0be3d419f32
```

CI smokes passed: demo, population, structure, and network generation.

```text
$ git status --short
 M src/jersey_outbreak/job_finalizer.py
 M src/jersey_outbreak/job_manager.py
 M src/jersey_outbreak/job_registry.py
?? tests/test_prov_job_ordering.py

$ git diff --stat
 src/jersey_outbreak/job_finalizer.py |  89 +++++++++++++------
 src/jersey_outbreak/job_manager.py   | 161 +++++++++++++++++++++++++----------
 src/jersey_outbreak/job_registry.py  |  23 +++--
 3 files changed, 190 insertions(+), 83 deletions(-)
```

Nothing left undone within scope. No commit created.