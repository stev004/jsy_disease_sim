Implemented only the permitted files.

Diff:

```diff
- raise typer.BadParameter(str(exc), param_hint="artifact_dir") from exc
+ typer.echo(f"error: {exc}", err=True)
+ raise typer.Exit(code=2) from exc
```

Tests now use a fresh copied bundle per test and assert plain error messages with exit code 2.

Verification:

```text
COLUMNS=60 ... pytest ... 
.... [100%]
4 passed in 4.97s
```

```text
COLUMNS=200 ... pytest ...
.... [100%]
4 passed in 4.60s
```

Isolation:

```text
requires_safe_transcript_location: 1 passed, 3 deselected
does_not_change_artifact: 1 passed, 3 deselected
records_tampered: 1 passed, 3 deselected
```

Order independence:

```text
... -k "not writes_passed"
... [100%]
3 passed, 1 deselected in 4.38s
```

Lint/typing:

```text
ruff check: All checks passed!
ruff format --check: 129 files already formatted
mypy: Success: no issues found in 2 source files
```

Final status contains only:

```text
M src/jersey_outbreak/cli.py
M tests/test_v12_bundle_selftest.py
```