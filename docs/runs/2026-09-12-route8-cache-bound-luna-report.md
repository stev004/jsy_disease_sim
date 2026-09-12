REPORT

Implemented ROUTE-8 without changing route logic, hashes, fingerprints, or schemas.

Files changed:

- [network_generator.py](/home/steven/jos-r8c-wt/src/jersey_outbreak/network_generator.py:83)
  - Renamed/documented the global runtime LRU bound.
  - Added bounded build-phase capacity: `max(3, len(snapshot_dates)) × route_count`.
  - Restores runtime capacity after M4 construction.
  - Added plain `ValueError` guard.
- [network_artifacts.py](/home/steven/jos-r8c-wt/src/jersey_outbreak/network_artifacts.py:288)
  - Keeps snapshot rows and route-hash passes inside one build-phase cache context.
- [test_networks.py](/home/steven/jos-r8c-wt/tests/test_networks.py:349)
  - Added 2–5-date replay, artifact replay, runtime peak, and truthful global-LRU tests.

Acceptance evidence:

1. Real M4 replay, base vs branch:

```text
branch:
2 dates: constructions=22 ideal=22 runtime_capacity=33
3 dates: constructions=33 ideal=33 runtime_capacity=33
4 dates: constructions=44 ideal=44 runtime_capacity=33
5 dates: constructions=55 ideal=55 runtime_capacity=33

base:
2 dates: constructions=22 ideal=22 runtime_capacity=33
3 dates: constructions=33 ideal=33 runtime_capacity=33
4 dates: constructions=91 ideal=44 runtime_capacity=33
5 dates: constructions=115 ideal=55 runtime_capacity=33
```

```text
$ uv run pytest -q tests/test_networks.py -k 'm4_build_cache or route_snapshot_cache_is_bounded or runtime_snapshot_cache or artifact_build_cache or global_route_snapshot'
........ [100%]
8 passed, 19 deselected in 6.34s
```

2. Truthful cache policy:

```text
# Runtime bound for the single global LRU: three entries per configured route.
SNAPSHOT_CACHE_RUNTIME_ENTRIES_PER_ROUTE = 3

return SNAPSHOT_CACHE_RUNTIME_ENTRIES_PER_ROUTE * max(1, len(self.route_specs))

while len(self._snapshot_cache) > self.snapshot_cache_capacity:
    self._snapshot_cache.popitem(last=False)
```

The prior one-route test is now `test_global_route_snapshot_lru_bound_can_be_filled_by_one_route` and asserts the global cache reaches its full capacity.

3. Golden hashes and fingerprints unchanged:

```text
ci-seed-123:
base    749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657
branch  749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657

scaled-seed-123:
base    a4048ea8269f1df0660d2014663f3b98e3fa0d2213e421fab4bbee37b3811171
branch  a4048ea8269f1df0660d2014663f3b98e3fa0d2213e421fab4bbee37b3811171
```

```text
standard: base=d0b59aa3e971d281d49c18cba7b6dc1d403f27552ebdc07d0bfafedc04a0fca2 branch=d0b59aa3e971d281d49c18cba7b6dc1d403f27552ebdc07d0bfafedc04a0fca2 routes=11 dates=2
term-boundary: base=a354db7689afeb657344e9c365c76f035dc4007371d258498a845a27e33440a7 branch=a354db7689afeb657344e9c365c76f035dc4007371d258498a845a27e33440a7 routes=11 dates=21
```

Harness comparison output:

```text
fingerprints identical
```

4. Runtime bound:

```text
artifact dates= 5 routes= 11 constructions= 55 ideal= 55 runtime_capacity= 33 final_cache= 33
```

The runtime 7-day test passed and measured peak entries equal to 33.

5. Local CI mirror:

```text
uv lock --check
Resolved 77 packages in 0.81ms

uv run python -m compileall -q src
(no output; exit 0)

uv run pytest
================= 370 passed, 8 warnings in 855.48s (0:14:15) ==================

uv run ruff check .
All checks passed!

uv run ruff format --check .
229 files already formatted

uv run mypy --ignore-missing-imports [CI module list]
Success: no issues found in 15 source files

git diff --check
(no output; exit 0)

uv run python scripts/ci_relocation_check.py
{"diagnostics_status": "passed", "logical_content_hash": "1e9f01ed1d770bbeb592c3d0c69add44040d2e80339b93b884b24701f4ed8a99", "scenario_hash": "7158b33cb7eba93112b1326aacc253d19136a4a85f70c7c4245113a26478665a"}
verifier success: m7_intervention jos-intervention-m7-ci-seed-123-c0be3d419f32
```

Final status:

```text
 M src/jersey_outbreak/network_artifacts.py
 M src/jersey_outbreak/network_generator.py
 M tests/test_networks.py
```

```text
 src/jersey_outbreak/network_artifacts.py | 55 +++++++++----------
 src/jersey_outbreak/network_generator.py | 55 +++++++++++++++++--
 tests/test_networks.py                   | 92 ++++++++++++++++++++++++++++++--
 3 files changed, 167 insertions(+), 35 deletions(-)
```

Nothing left undone. No commit made.