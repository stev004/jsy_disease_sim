Implemented B01 with no scientific computation or data/hash-definition changes.

Design:
- Central `portable_artifact_path()` records paths relative to each artifact root, including nested M5 inside M7.
- Verifiers reject absolute paths, `..` traversal, duplicates, missing files, size mismatches, and hash mismatches.
- Added observation/calibration manifest verification.
- Bumped manifest versions across affected artifact families.
- Legacy M2/M3 and M5/M6 path behavior is explicitly version-gated.
- Existing logical/data-file hash semantics are unchanged; only manifest bytes and dependent manifest-hash provenance values change.

Verification:

- B01 regressions: `11 passed`
- B01 plus M7/M8 integrity tests: `13 passed`
- Full suite: `226 passed, 4 warnings`
- `ruff check .`: passed
- `ruff format --check .`: passed
- `git diff --check`: passed

Diff: 17 tracked source/schema files, `210 insertions / 98 deletions`, plus 190-line regression test file. No commit created.