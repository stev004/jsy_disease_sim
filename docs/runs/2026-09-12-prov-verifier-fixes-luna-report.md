Implemented retry 2.

Changes:

- `network_schemas.py`: extracted one reusable school-calendar horizon validator; the Pydantic validator delegates to it.
- `outbreak_runner.py`: invokes the shared validator before travel dispatch, disease construction, or Starsim initialization.
- `tests/test_v121_prov_verifier_fixes.py`: added fail-fast coverage using `default_run_config(...).model_copy(...)`, asserting zero Starsim constructor calls.

Acceptance evidence:

1. Base reproduction (`/tmp/pver-base`):

```text
SIM_CONSTRUCTOR_CALLS=1
ERROR=school route date is outside the configured authoritative reference calendar year
.
1 passed in 7.77s
```

Branch fail-fast test:

```text
SIM_CONSTRUCTOR_CALLS=0
.
1 passed, 6 deselected in 1.85s
```

Exact branch error:

```text
school route date range 2025-07-06 to 2026-01-01 is outside school calendar year 2025
```

2. In-range CLI smoke:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run jos outbreak run --mode ci --seed 123 --duration-days 30 --output-dir /tmp/pver-cli-inrange
```

```json
{"diagnostics_status": "passed", "mode": "ci", "starsim_version": "3.5.2", "target_population": 3000}
```

The CLI has no `start_date` option; the permitted `default_run_config(...).model_copy(...)` path is covered by the regression test.

3. Single message construction:

```text
src/jersey_outbreak/network_schemas.py:63:    calendar_year_error = f"is outside school calendar year {config.school_calendar_year}"
```

4. Verification:

```text
28 passed, 2 warnings in 18.09s
374 passed, 9 warnings in 851.62s (0:14:11)
```

```text
Resolved 77 packages in 0.78ms
All checks passed!
221 files already formatted
Success: no issues found in 16 source files
verifier success: m7_intervention jos-intervention-m7-ci-seed-123-c0be3d419f32
```

`compileall` and `git diff --check` produced no output and exited 0. Golden-hash tests passed unchanged.

`git status --short`:

```text
 M src/jersey_outbreak/api.py
 M src/jersey_outbreak/bundle_selftest.py
 M src/jersey_outbreak/intervention_artifacts.py
 M src/jersey_outbreak/network_schemas.py
 M src/jersey_outbreak/outbreak_runner.py
 M src/jersey_outbreak/scientific_verification.py
 M src/jersey_outbreak/verification_archive.py
 M tests/test_b01_portable_artifacts.py
 M tests/test_m9_api.py
?? tests/test_v121_prov_verifier_fixes.py
```

`git diff --stat`:

```text
9 files changed, 188 insertions(+), 23 deletions(-)
```

Retry-1 changes were preserved. No commit made.