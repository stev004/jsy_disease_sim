Implemented ROUTE-5 phase 1.

Design:

- Added `EdgeColumns` and columnar `RouteSnapshot` with `int64` endpoints/persistence and `float64` weights.
- `.edges` is an uncached compatibility view; LRU entries retain columns only.
- Added exact dict-list converter with preserved Python types and M8 `duration_days` compatibility.
- Community builders now use preallocated arrays, string-rank canonicalization, columnar deduplication, and vectorized merge.
- Starsim receives snapshots/columns directly; UID-index arrays are cached per mapping identity.
- Added adversarial converter, dedup/merge, byte-equivalence, unknown-agent, and base-comparison tests.

Evidence:

- Focused tests: `4 passed`.
- Full suite: `312 passed, 5 warnings`.
- Golden tests: `9 passed`.
- Full M4 hash:  
  `49464e77ac5754a114dadcf73b2e79e3bf94607d1d192a4f48229891e7d5b0bd`
- Base/branch simulation hashes matched for full 7-day and CI 30-day runs:
  - Full logical: `2425986db799d2b68b57b16b3726bec753135a716237e2b1ffe78d553da1ed8c`
  - Full latent: `f3c51be00168263c3a31dddc35157645f1912a56a4840e7804d30e543838e8ac`
  - CI logical: `1e9f01ed1d770bbeb592c3d0c69add44040d2e80339b93b884b24701f4ed8a99`
  - CI latent: `a9b1f9713505efecdc2b408d4c959e40545111cac8f9c2004aabaf994ea8f168`

Full harness comparison:

```text
fingerprints identical
standard community_indoor: A_wall/B_wall=1.262842
standard community_outdoor: A_wall/B_wall=1.155484
term-boundary community_indoor: A_wall/B_wall=1.294183
term-boundary community_outdoor: A_wall/B_wall=1.230578
```

All other route fingerprints also reported identical by the harness. The 1.5× soft timing target was not reached; exact equivalence is green.

Memory estimate for full `community_indoor`: 191,770 rows, four arrays = 6,136,640 bytes versus approximately 47,942,500 bytes for dict rows at 250 B each.

CI mirror passed: lock check, compileall, ruff, format, mypy, CLI generation, relocation check, and `git diff --check`.

Status:

```text
 M scripts/bench_dynamic_routes.py
 M src/jersey_outbreak/network_generator.py
 M src/jersey_outbreak/starsim_adapter.py
?? tests/test_route_snapshot_columns.py
```

No commit made.