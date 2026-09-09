# Run-4 merge smokes (director, local — GitHub Actions billing was exhausted, so these replace CI rows)

Each merge was SHA-first `--no-ff` in the WSL primary checkout after a filed independent PASS. The lines below are the tail of the director's pre-push smoke output, copied from the session transcript at closeout (trail-audit-4 Attention 5).

| Gate | Candidate → merge | Smoke output (tail) |
|---|---|---|
| G18 | `0dec469` → `95d55fc`-era merge (trail row `g18-merge`) | `41 passed in 119.87s` · `RUFF_OK` · `jos demo` `"cumulative_infections": 37` · `PUSHED` |
| G19 | `0cf6499` → `0f7a0f8` | `36 passed in 119.39s` · `REBUILD_IDENTICAL` (fresh `jos data build` dir == `data/processed`) · `RUFF_OK` · `PUSHED` |
| G22 | `e26ef91` → `d679230` | `39 passed in 134.20s` · `RUFF_OK` · `PUSHED` |
| G23 | `a588e22` → `6e9b0e4` | `56 passed, 3 warnings in 380.80s` · `RUFF_OK` · `PUSHED` |

Test sets: G18 goldens/hash-stream/M3 oracle/init boundary/columns/weekday memo/fingerprints/outbreak; G19 data sources/pipeline/dictionary + goldens; G22 goldens/hashkey/perf4/phase-2 columns/fingerprints/ensemble; G23 goldens/perf6/perf9/ensemble/cli/M7. Every unit had additionally passed the full CI mirror (full suite, ruff, format, mypy 15 modules, lock, compileall) in its executor run and its independent review.
