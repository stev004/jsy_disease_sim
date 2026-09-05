Implemented PERF-3 with no commit.

Contract: [`iter_canonical_json_chunks`]( /home/steven/jos-perf3-wt/src/jersey_outbreak/hashing.py:25) frames M4’s large containers, encodes leaves via `canonical_json_bytes`, supports lazy iterator arrays, and asserts string keys. [`sha256_of_canonical_stream`]( /home/steven/jos-perf3-wt/src/jersey_outbreak/hashing.py:72) incrementally updates SHA-256. M4 now lazily yields snapshots at [`network_generator.py:2075`]( /home/steven/jos-perf3-wt/src/jersey_outbreak/network_generator.py:2075).

Evidence:

1. Hashing/property tests: `514` values covered; `4 passed in 2.33s`.

2. M4 CI seed 123 eager reconstruction and golden comparison passed.

3. Focused suite: `40 passed in 149.81s`.

4. Full seed-101 proof:

```text
logical_content_hash: 49464e77ac5754a114dadcf73b2e79e3bf94607d1d192a4f48229891e7d5b0bd
streamed_hash: 49464e77ac5754a114dadcf73b2e79e3bf94607d1d192a4f48229891e7d5b0bd
streamed_tracemalloc_peak_bytes: 3976620
eager_payload_bytes: 252689441
stream_equals_eager: True
```

5. Benchmark tests: `6 passed in 10.58s`; benchmark help runs. Diagnostics and artifact schema unchanged.

6. CI mirror passed:

- `uv lock --check`
- compileall
- Full suite: `308 passed, 5 warnings`
- Ruff and formatting
- Mypy: `Success: no issues found in 15 source files`
- CI population, structure, and network CLI generation

7. Final status contains only:

```text
 M src/jersey_outbreak/hashing.py
 M src/jersey_outbreak/network_generator.py
 M tests/test_hashing.py
?? tests/test_m4_hash_stream.py
```

`git diff --check` is clean. No acceptance criterion remains undone.