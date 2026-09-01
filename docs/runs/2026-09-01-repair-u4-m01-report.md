Implemented M01 with minimal scope.

Changed:

- [pyproject.toml](/private/tmp/jsy-repair-wt/pyproject.toml:7): version `1.1.0`
- [__init__.py](/private/tmp/jsy-repair-wt/src/jersey_outbreak/__init__.py:1): updated docstring and `__version__`
- [frontend/package.json](/private/tmp/jsy-repair-wt/frontend/package.json:4): version `1.1.0`
- [README.md](/private/tmp/jsy-repair-wt/README.md:8): corrected V1.0/V1.1 release status
- [test_m9_api.py](/private/tmp/jsy-repair-wt/tests/test_m9_api.py:149): capability version now cross-checks `pyproject.toml` and `__version__`

API mechanism: `/capabilities` already reads `package_version` from imported `jersey_outbreak.__version__`; no API implementation change was needed.

Verification:

- Scoped `0.1.0` scan: clean
- Backend: `229 passed`
- Frontend: `15 passed`, 6 expected skips
- Frontend typecheck/build: passed
- Ruff check/format: passed
- `git diff --check`: clean
- Only the five intended files changed; no commit created.