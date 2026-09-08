Implemented and shipped all three builders in order: `workplace_transient`, `school_cross_class`, and `bus`.

Base SHA: `60b9c54499437569010be4f084b4fcbe75055c28`

Design:

- Added columnar twins for complete groups, rings, grouped rings, and school staff contacts.
- Pre-mapped excluded pairs to string-rank pairs.
- Preserved all draw calls, ordering, weights, persistence, and deduplication semantics.
- Builders now return `EdgeColumns`, including empty weekend results; dict helpers remain unchanged.

Files:

- [network_generator.py](/home/steven/jos-r5b-wt/src/jersey_outbreak/network_generator.py:545)
- [test_route5_phase2_columns.py](/home/steven/jos-r5b-wt/tests/test_route5_phase2_columns.py:1)

Verification:

- Phase-2 tests: `4 passed`
- Dynamic benchmark tests: `6 passed`
- Named regression suite: `90 passed`
- Full suite: `326 passed, 5 warnings`
- Lock, compileall, ruff, format, mypy-15: passed
- Network CLI diagnostics: `passed`
- Relocation check: passed
- `git diff --check`: passed

Full seed-101 hashes:

```text
M4/network:     49464e77ac5754a114dadcf73b2e79e3bf94607d1d192a4f48229891e7d5b0bd
latent logical: 2425986db799d2b68b57b16b3726bec753135a716237e2b1ffe78d553da1ed8c
latent outcome:  f3c51be00168263c3a31dddc35157645f1912a56a4840e7804d30e543838e8ac
```

The full harness reported `fingerprints identical` for all 11 routes in both windows. Target route ratios:

```text
standard workplace_transient: 1.402363
standard school_cross_class: 1.487338
standard bus:               1.993421
term-boundary workplace_transient: 1.354979
term-boundary school_cross_class: 1.370111
term-boundary bus:               1.955697
```

Stable-int counts matched base for every route and both windows.

Final status:

```text
 M src/jersey_outbreak/network_generator.py
?? tests/test_route5_phase2_columns.py
```

No commit made.