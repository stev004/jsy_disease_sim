Implemented the retry-2 fixes.

Changes:

- [scientific_hashes.py](/home/steven/jos-phelp-wt/src/jersey_outbreak/scientific_hashes.py:61): comparison differences now preserve base behavior—float metrics use `float()`, all other registered metrics use `int()`, including `intervention_route_active`.
- [ensemble.py](/home/steven/jos-phelp-wt/src/jersey_outbreak/ensemble.py:426): restored commit → `source:<sha256 ensemble.py>` → `None` identity fallback.
- [tests/test_prov_helpers.py](/home/steven/jos-phelp-wt/tests/test_prov_helpers.py:124): added pinned base-hash fixture and inside/outside Git identity tests.
- [provenance.py](/home/steven/jos-phelp-wt/src/jersey_outbreak/provenance.py:9): remains the sole Git subprocess helper.

Failing-test-first:

```text
$ uv run pytest tests/test_prov_helpers.py -q
..FF.....F [100%]
...
E AttributeError: module 'jersey_outbreak.ensemble' has no attribute '_code_identity'
...
E AssertionError: assert '6d6dee38166e...' == '9579e685afb8...'
...
3 failed, 7 passed
```

Base digest command, run in `/tmp/phelp-base`:

```text
$ uv run python - <<'PY'
from jersey_outbreak.scientific_hashes import m6_comparison_logical_hash
...
print(m6_comparison_logical_hash(...))
PY
9579e685afb804dea42ecba2df4bd7ec0bd1c2507810fdf79745573e55aa56f2
```

After fix:

```text
$ uv run pytest tests/test_prov_helpers.py -q
.......... [100%]
10 passed in 0.98s

$ uv run pytest tests/test_prov_helpers.py::test_m6_comparison_hash_preserves_base_canonicalization -q
. [100%]
1 passed in 0.13s

$ uv run pytest tests/test_prov_helpers.py -k ensemble_code_identity -q
.. [100%]
2 passed, 8 deselected in 0.16s
```

Producer evidence:

```text
"metric": "pair_status",
"date": None,
"status": "missing_or_failed",
"value_a": None,
"value_b": None,
"difference": None,
```

Verification:

```text
$ uv lock --check
Resolved 77 packages in 0.97ms

$ uv run python -m compileall -q src
(exit 0, no output)

$ uv run ruff check .
All checks passed!

$ uv run ruff format --check .
222 files already formatted

$ uv run mypy --ignore-missing-imports [CI module list + ensemble.py scientific_hashes.py provenance.py]
Success: no issues found in 18 source files

$ git diff --check
(exit 0, no output)

$ grep -R -n --include='*.py' -E 'rev-parse|status --porcelain' src/
src/jersey_outbreak/provenance.py:14:            ["git", "rev-parse", "HEAD"],
```

```text
$ uv run pytest
================= 374 passed, 8 warnings in 828.76s (0:13:48) ==================

$ uv run pytest tests/test_golden_hashes.py -q
9 passed in 94.34s (0:01:34)
```

CI smokes and relocation check all exited 0; population, structure, network, and intervention diagnostics reported `passed`.

`git status --short`:

```text
 M src/jersey_outbreak/api.py
 M src/jersey_outbreak/bundle_selftest.py
 M src/jersey_outbreak/calibration_artifacts.py
 M src/jersey_outbreak/cli.py
 M src/jersey_outbreak/demo.py
 M src/jersey_outbreak/ensemble.py
 M src/jersey_outbreak/ensemble_artifacts.py
 M src/jersey_outbreak/execution_adapter.py
 M src/jersey_outbreak/intervention_artifacts.py
 M src/jersey_outbreak/network_artifacts.py
 M src/jersey_outbreak/observation_artifacts.py
 M src/jersey_outbreak/outbreak_artifacts.py
 M src/jersey_outbreak/outbreak_runner.py
 M src/jersey_outbreak/population_artifacts.py
 M src/jersey_outbreak/population_structure_artifacts.py
 M src/jersey_outbreak/scientific_hashes.py
 M src/jersey_outbreak/travel.py
 M src/jersey_outbreak/travel_artifacts.py
 M src/jersey_outbreak/verification_archive.py
?? src/jersey_outbreak/provenance.py
?? tests/test_prov_helpers.py
```

`git diff --stat`:

```text
19 files changed, 92 insertions(+), 389 deletions(-)
```

No golden fixtures, commits, or out-of-scope files were changed. Existing retry-1 edits remain intact.