**VERDICT: PASS.** The fallback fixes all 22 destination-share failures, and there are no unexpected artifact differences.

### Diff

In [population_structure_generator.py](/home/steven/jos-destfix-wt/src/jersey_outbreak/population_structure_generator.py:390), the fallback runs only when physical primary-worker shares fail the existing 0.01 gate. It reallocates categories by workplace physical-worker weights, uses a separately derived RNG stream for parish draws, updates job parishes before commute assignment, and fails closed if the unchanged gate still fails. Diagnostics disclose before and after shares only when the fallback runs.

Added one real-build CLI end-to-end test in [test_m3_destination_fallback.py](/home/steven/jos-destfix-wt/tests/test_m3_destination_fallback.py:1). The combined scope is those two files; the tracked source diff is 130 insertions and 13 deletions, plus the 46-line test file.

### Before and after destination shares

Values are St Helier / semi-urban / rural.

| Seed | Before | After |
|---:|---|---|
| 34 | 67.107% / 12.448% / 20.445% | 65.994% / 13.004% / 21.001% |
| 47 | 64.812% / 13.561% / 21.627% | 65.994% / 13.004% / 21.001% |
| 54 | 64.951% / 13.839% / 21.210% | 65.994% / 13.004% / 21.001% |
| 65 | 67.038% / 12.448% / 20.515% | 65.994% / 13.004% / 21.001% |
| 73 | 64.743% / 13.282% / 21.975% | 65.994% / 13.004% / 21.001% |
| 77 | 64.951% / 13.282% / 21.766% | 65.994% / 13.004% / 21.001% |
| 79 | 64.673% / 13.282% / 22.045% | 65.994% / 13.004% / 21.001% |
| 81 | 67.038% / 12.517% / 20.445% | 65.994% / 13.004% / 21.001% |
| 93 | 66.481% / 13.630% / 19.889% | 65.994% / 13.004% / 21.001% |
| 118 | 65.090% / 12.656% / 22.253% | 65.994% / 13.004% / 21.001% |
| 119 | 64.882% / 13.352% / 21.766% | 65.994% / 13.004% / 21.001% |
| 156 | 66.690% / 13.352% / 19.958% | 65.994% / 13.004% / 21.001% |
| 159 | 67.455% / 12.656% / 19.889% | 65.994% / 13.004% / 21.001% |
| 168 | 67.038% / 13.143% / 19.819% | 65.994% / 13.004% / 21.001% |
| 177 | 64.673% / 13.978% / 21.349% | 65.994% / 13.004% / 21.001% |
| 192 | 65.508% / 12.378% / 22.114% | 65.994% / 13.004% / 21.001% |
| 218 | 64.812% / 13.352% / 21.836% | 65.994% / 13.004% / 21.001% |
| 254 | 64.673% / 13.839% / 21.488% | 65.994% / 13.004% / 21.001% |
| 263 | 66.551% / 11.752% / 21.697% | 65.994% / 13.004% / 21.001% |
| 273 | 64.951% / 13.561% / 21.488% | 65.994% / 13.004% / 21.001% |
| 277 | 64.951% / 13.352% / 21.697% | 65.994% / 13.004% / 21.001% |
| 299 | 66.898% / 11.961% / 21.140% | 65.994% / 13.004% / 21.001% |

### Identity, downstream, and tests

Against the detached base clone at `628fe72a5284b6f1fea58716421f6041e68a9cb4`, CI identity results are **272 IDENTICAL, 22 FIXED, 6 STILL-FAIL, 0 DIFFERENT**. The fixed seeds are the 22 above; the six remaining failures are the expected M2 seeds **96, 122, 147, 163, 228, 261**. Full pins 101/123 and scaled seeds 101/123 were all IDENTICAL. Comparison covered artifact directory name, artifact ID, logical hash, every Parquet file, and diagnostics JSON with only `runtime_seconds` and `peak_memory_bytes` removed. See the [identity table](/tmp/jos-destfix-identity.tsv).

All 22 requested CI CLI builds passed with the fallback disclosed and no failed M3 checks. Downstream `jos network generate` passed diagnostics for seeds 34 and 263, each producing 11 routes: [seed 34 output](/tmp/jos-destfix-evidence/network-34.json), [seed 263 output](/tmp/jos-destfix-evidence/network-263.json).

The new end-to-end test passed. The single full `uv run pytest` run finished **469 passed, 4 skipped, 0 failed**; `tests/test_prov_job_ordering.py` passed. Post-suite checks passed: Ruff format left both files unchanged, Ruff check passed, mypy reported no issues in both files, and `git diff --check` was clean.

The [evidence log](/tmp/jos-destfix-evidence.log) contains the run summary and output. **Clean scope:** only the requested generator file and one test file changed; no commits or pushes.