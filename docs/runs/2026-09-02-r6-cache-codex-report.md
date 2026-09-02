Implemented the bounded LRU snapshot cache.

Files changed:

- [network_generator.py](/home/steven/jos-r6-cache-wt/src/jersey_outbreak/network_generator.py:75)
- [test_networks.py](/home/steven/jos-r6-cache-wt/tests/test_networks.py:76)

New tests:

- `test_route_snapshot_cache_is_bounded`
- `test_route_snapshot_recomputation_preserves_complete_ordered_edges`
- `test_route_snapshot_lru_hits_and_recomputes_content_identically`

Verification:

- `tests/test_networks.py`: `14 passed`
- `tests/test_m8_travel.py`: `13 passed`
- Scoped contract/hash tests excluding existing M9 job tests: `32 passed`
- Ruff: `All checks passed!`
- Format: `2 files already formatted`
- `git diff --check`: passed
- Full exact `uv run --locked` commands were blocked by unavailable network/package downloads; the alternate local environment’s full run stalled in existing M9 job lifecycle tests.

For an 8-route full-mode network, the maximum cache is:

`3 × max(1, 8) = 24 entries`