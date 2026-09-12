Implemented all five fixes; no commit made.

Changes:

- ROUTE-12: Added excluded operational horizon validation in [network_schemas.py](/home/steven/jos-pver-wt/src/jersey_outbreak/network_schemas.py:58), preserving M4 hashes.
- PROV-6: Verification archives now use portable path helpers for writing and verification.
- PROV-12: Added M8 artifact-ID binding, derived M7/archive statuses, and M7 status reconciliation.
- PROV-3: Dataset responses now return the matched logical label.
- PROV-13: Self-test hashes exclude paths/timings and compare complete source/copy hash dictionaries.

Evidence:

```text
uv run pytest -q tests/test_v121_prov_verifier_fixes.py
6 passed, 1 warning in 7.14s

uv run pytest -q tests/test_b01_portable_artifacts.py::test_relocated_verification_archive_copy_verifies tests/test_b01_portable_artifacts.py::test_verification_archive_rejects_absolute_and_parent_paths
3 passed in 0.20s

uv run pytest -q tests/test_m9_api.py::test_bounded_dataset_read_and_path_safety
1 passed, 1 warning in 0.52s
```

Base A/B evidence showed the expected failures: `9 failed, 1 passed` on the base regression set. Base `_is_school_term` also raised from inside the day-loop path.

```text
uv run pytest -q tests/test_golden_hashes.py
9 passed in 113.73s (0:01:53)

uv run pytest
373 passed, 9 warnings in 1026.26s (0:17:06)
```

CI mirror:

```text
uv sync --frozen
Checked 75 packages in 1ms

uv lock --check
Resolved 77 packages in 0.79ms

uv run python -m compileall -q src
(no output; exit 0)

uv run ruff check .
All checks passed!

uv run ruff format --check .
221 files already formatted

uv run mypy --ignore-missing-imports [19 modules]
Success: no issues found in 19 source files

git diff --check
(no output; exit 0)

uv run python scripts/ci_relocation_check.py
verifier success: m7_intervention jos-intervention-m7-ci-seed-123-c0be3d419f32
```

Self-test fixture scan produced no committed self-test hash matches.

Final status:

```text
 M src/jersey_outbreak/api.py
 M src/jersey_outbreak/bundle_selftest.py
 M src/jersey_outbreak/intervention_artifacts.py
 M src/jersey_outbreak/network_schemas.py
 M src/jersey_outbreak/scientific_verification.py
 M src/jersey_outbreak/verification_archive.py
 M tests/test_b01_portable_artifacts.py
 M tests/test_m9_api.py
?? tests/test_v121_prov_verifier_fixes.py
```

`git diff --stat`:

```text
8 files changed, 170 insertions(+), 23 deletions(-)
```

The untracked regression file is intentionally included in the worktree; `git diff --stat` omits untracked files. Nothing remains undone within scope.