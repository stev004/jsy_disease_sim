Implemented and verified on `perf/hashkey-suffix-preencode`.

Base SHA: `5d0eba4b71115025cbbcb07a20366883b7f53e13`  
HEAD: `cb429488be9a94d171cecd34ccff5d2afe40448e`

Changes:

- Added `stable_int_prefixed()` with identical SHA-256 payload and counter semantics.
- Pre-encoded community agent/contact suffixes once per builder.
- Added 10,000-random-key equivalence and counter tests.

Files changed:

- [hashing.py](/home/steven/jos-hk-wt/src/jersey_outbreak/hashing.py:100)
- [network_generator.py](/home/steven/jos-hk-wt/src/jersey_outbreak/network_generator.py:1932)
- [test_hashkey_suffix.py](/home/steven/jos-hk-wt/tests/test_hashkey_suffix.py:1)

Verification:

- Scoped tests: `46 passed`
- Full suite: `320 passed, 5 warnings`
- Ruff, format, compileall, lock check, mypy: all passed
- `git diff --check`: passed

Full seed-101 7-day proof:

```text
all_route_and_array_fingerprints_equal: true
all_scientific_hashes_equal: true
initialized_arrays_bit_equal: true
lifecycle_and_consumer_order_equal: true
ordered_distribution_and_rate_paths_equal: true
```

Hashes:

```text
M4:             49464e77ac5754a114dadcf73b2e79e3bf94607d1d192a4f48229891e7d5b0bd
latent:         2425986db799d2b68b57b16b3726bec753135a716237e2b1ffe78d553da1ed8c
latent outcome: f3c51be00168263c3a31dddc35157645f1912a56a4840e7804d30e543838e8ac
```

Full two-window route comparison reported `fingerprints identical`. Stable-int totals matched base exactly:

```text
standard total:      13779583
term-boundary total:  9494324
```

Community timing, base/branch:

```text
standard community_indoor:  9.151235s / 7.897780s, ratio 1.158710
standard community_outdoor: 6.516976s / 5.379180s, ratio 1.211518
```

Final status:

```text
 M src/jersey_outbreak/hashing.py
 M src/jersey_outbreak/network_generator.py
?? tests/test_hashkey_suffix.py
```

No commit made.