Implemented the requested API cleanup.

Changed:

- `src/jersey_outbreak/job_registry.py`: removed `precondition` and its conditional queue-starvation path.

Acceptance evidence:

1. `grep -rn "precondition" src/jersey_outbreak/job_registry.py src/jersey_outbreak/job_manager.py`

```text
```

2. Targeted tests:

```text
16 passed, 1 warning in 30.49s
```

3. Static checks:

```text
All checks passed!
231 files already formatted
Success: no issues found in 2 source files
```

4. Final status/stat:

```text
 M src/jersey_outbreak/job_registry.py
 src/jersey_outbreak/job_registry.py | 7 +------
 1 file changed, 1 insertion(+), 6 deletions(-)
```

Additional checks passed: `uv sync --frozen`, lock check, compileall, CI smoke commands, relocation check, and `git diff --check`.

The full pytest run exceeded the execution window and did not produce a completed summary. No commit was created.