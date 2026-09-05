Implemented and verified.

- Removed `_UID_INDEX_CACHE` entirely.
- Added network-scoped `_uid_of_index`, shared across route networks.
- `_edge_arrays` accepts optional precomputed UID arrays; dict path unchanged.
- Added weakref retention and byte-equivalence coverage.

Verification:

- `62 passed in 51.55s`
- Ruff: all checks passed
- Format: `175 files already formatted`
- Mypy: no issues in 2 files
- `git diff --check`: passed
- No `_UID_INDEX_CACHE` references remain.
- CI seed 123, 7 days: both HEAD and branch:
  - logical: `9c3e7f998ea8642899419686023db79f2f6d77b32134e865937db89d7f108ab2`
  - latent: `05b916a4880f50bebf0aa3528edf0ec7fc08203b6f8b84f477992c505b08149f`

Changed files:

- [starsim_adapter.py](/home/steven/jos-r5a-wt/src/jersey_outbreak/starsim_adapter.py)
- [test_route_snapshot_columns.py](/home/steven/jos-r5a-wt/tests/test_route_snapshot_columns.py)

Status:

```text
 M src/jersey_outbreak/starsim_adapter.py
 M tests/test_route_snapshot_columns.py
```

Diff stat: `88 insertions(+), 26 deletions(-)`.