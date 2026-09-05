# JOS tranche-2B independent review

- Candidate: `0dec469f83ee936b9b68e979e7a927807d7654e0`
- Base: `ac04bbb50aaea1070a4fbd5d645062e7470c4f3c`
- Clone: `/tmp/jos-tranche2b-review`
- Date: 2026-09-06
- Model: OpenAI Codex (GPT-5)
- Role: independent read-only auditor

The candidate preserves all protected scientific outputs exercised by the protocol and is safe to merge into `main`. No BLOCKING or MAJOR findings were found.

## Findings

MINOR — [network_generator.py:175](/tmp/jos-tranche2b-review/src/jersey_outbreak/network_generator.py:175): the compatibility `.edges` view does not preserve non-core fields from arbitrary edge dictionaries.

M8 taxi edges add `transport_unit_id` at [travel.py:1820](/tmp/jos-tranche2b-review/src/jersey_outbreak/travel.py:1820), but `RouteSnapshot.from_edge_dicts()` retains only endpoints, weight, and persistence/duration. Thus `route_view().route_snapshot(...).edges` omits that extra field.

This does not alter a protected output: M8 records exact taxi provenance directly into `route_edge_history` at [travel.py:1601](/tmp/jos-tranche2b-review/src/jersey_outbreak/travel.py:1601), and `temporary_edge_rows()` consumes that history at [travel.py:1927](/tmp/jos-tranche2b-review/src/jersey_outbreak/travel.py:1927). The adapter and interventions use only the four core fields. All prescribed M8 integrity, closure, golden-hash, and artifact tests passed.

MINOR — [network_generator.py:242](/tmp/jos-tranche2b-review/src/jersey_outbreak/network_generator.py:242): `RouteSnapshot.__eq__` is stricter than the base implementation.

The base compared `(route_id, snapshot_date, edges)`. The new implementation also compares the complete `agent_ids` sequence and physical index arrays. Two snapshots with identical reconstructed edges but different unused agent universes therefore compare unequal. All reachable production comparisons use the same agent universe, and the prescribed network tests passed. An independent probe confirmed ordinary same-universe equality remains true.

MINOR — [test_init_metadata_boundary.py:148](/tmp/jos-tranche2b-review/tests/test_init_metadata_boundary.py:148): the committed PERF-1 test explicitly asserts the mapping boundary but not the `_uid_of_index` boundary.

It therefore does not, by itself, prove that both objects are hidden. Independent inspection and probing closed this audit gap: pinned sciris declares `np.ndarray` atomic at [sc_nested.py:20](/tmp/jos-tranche2b-review/.venv/lib/python3.12/site-packages/sciris/sc_nested.py:20), and all eight dynamic networks had both boundaries, shared the same array, and returned no hidden array from `sc.search`.

## Step 1 — diff and behavioural review

Commands:

```text
git diff ac04bbb 0dec469 -- src tests scripts
git diff --check ac04bbb 0dec469
git merge-base --is-ancestor ac04bbb 0dec469
```

Result:

```text
5 files changed, 821 insertions(+), 65 deletions(-)
ancestor_exit=0
range_diff_check_exit=0
```

### ROUTE-5 phase 1

- `EdgeColumns` normalizes all four arrays to one-dimensional, C-contiguous `int64/int64/float64/int64`.
- `.edges` reconstructs `str`, `str`, `float`, and `int` values. Mixed `duration_days`/`persistence_days` rows retain the correct key. Empty snapshots produce `()` with correctly typed zero-length arrays.
- Direct seed-125 comparison checked 632,613 rows for identical key sets and exact Python value types.
- Dictionary key insertion order is immaterial to equality and canonical hashing.
- Columnar deduplication sorts by pair, descending weight, then unique emission order. `np.lexsort` is stable, and the explicit `emit_order` resolves all equal-weight cases. A signed-zero probe retained the first `-0.0` row and its persistence exactly like `_deduplicate_edges`.
- Community-builder weights are constants within each call, so equal-weight duplicates cannot acquire a new floating-point ordering.
- Canonical endpoint ordering uses string rank, not numeric index. The `agent-9`/`agent-10` regression case passed.
- Columnar merge places the first source before the second and selects the second only when its weight is strictly greater. Equal weights—including signed zero—retain the first row, matching `_merge_sorted_edges`.
- The community-loop diff changes only row construction after target selection. Participation, target-band draws, target-choice draws, and `_stable_int_suffix` argument order are unchanged.
- Full harness stable-call counts matched exactly:
  - Standard: `13,779,583 == 13,779,583`
  - Term boundary: `9,494,324 == 9,494,324`
- `_edge_arrays` performs indexed `int64` endpoint copies and a copied `float64` weight array. Independent comparisons established exact dtype, shape, contiguity, and bytes.
- Unknown-agent errors remain `ValueError("route edge references unknown JOS agent: ...")` on both dict conversion and UID-index construction.
- M8’s expanded identity sequence is resident IDs followed by visitor slots. Copied resident column indices therefore remain valid, while temporary dict edges are converted against the expanded mapping.
- M8 `duration_days` rows survive the compatibility conversion with the original key and types. The extra taxi-field caveat is reported above.

### ROUTE-4

- `_job_is_physical_on_date()` depends on the date only through `weekday()`.
- `_job_physical_weekdays()` depends only on job fields, agent ID, and seed.
- `_complete_group()` depends only on its IDs and constant weight/persistence.
- Cached transient groups are consumed through generators and membership tests; no later code mutates the cached lists.
- Daily transient participation and ring ordering still use `snapshot_date.isoformat()`, so daily draws remain daily.
- `route_snapshot()` still checks `active_calendar` before invoking a builder.
- The activated 180-date parent-comparison test matched both workplace routes exactly and matched workplace-team array bytes. Both weekday memos remained bounded to at most five entries.

### Merge resolution

- Sciris 3.3.0 treats `np.ndarray` as atomic, so wrapping `_uid_of_index` was unnecessary for traversal performance but harmless.
- The boundary accessor returns the same array identity and maintains strong ownership.
- Independent result:

```text
dynamic_networks=8
all_mapping_boundaries=True
all_index_boundaries=True
same_shared_index_array=True
hidden_array_not_discovered=True
index_dtype_shape=int64 (3000,)
```

- The boundary remains unpickleable because of its local lambda, as already documented in the tranche-2 review. Repository search found no network, scheduler, or initialized-Sim pickle path.
- Ensemble jobs serialize only M2/M3 inputs and validated configurations; each worker regenerates M4 and constructs its own networks.

## Step 2 — prescribed tests

Command:

```text
UV_CACHE_DIR=/tmp/uv-cache MPLCONFIGDIR=/tmp/matplotlib-cache \
uv run pytest -q \
  tests/test_golden_hashes.py \
  tests/test_route_snapshot_columns.py \
  tests/test_route4_weekday_memo.py \
  tests/test_bench_dynamic_routes.py \
  tests/test_init_metadata_boundary.py \
  tests/test_networks.py \
  tests/test_c2_network_semantics.py \
  tests/test_outbreak.py \
  tests/test_observation.py \
  tests/test_m7_interventions.py \
  tests/test_c5_m7_integrity.py \
  tests/test_m8_travel.py \
  tests/test_m8_1_travel_integrity.py \
  tests/test_m8_2_travel_closure.py \
  tests/test_ensemble.py \
  tests/test_b01_portable_artifacts.py
```

Result:

```text
155 passed, 1 warning in 506.43s (0:08:26)
```

The warning was the expected Starsim one-day-timeline warning.

The comparison fixtures were active and verified:

```text
/tmp/jos-r5a-base network_generator.py == ac04bbb
/tmp/jos-r4-base network_generator.py == 6ff4870
```

## Step 3 — independent probes

### CI seed 125: M4, rows, and arrays

```text
candidate_m4 = 7838aabae149fea58d798f01345b833a2cd8f465c0f4c3e5648a032942d07dd2
base_m4      = 7838aabae149fea58d798f01345b833a2cd8f465c0f4c3e5648a032942d07dd2
routes = 11
dates = 33
route/date direct list equalities = 363
rows with exact keys and value types = 632613
exact p1/p2/beta/dur field comparisons = 1452
```

The 33 dates comprise 12 consecutive dates from `config.start_date` plus the complete 21-day harness term-boundary window.

### CI seed 125: 30-day online observation

Base and candidate both produced:

```text
latent logical hash:
905c5bd277dce851eb71b4544c639457b220c932cd6d8b64f45a72998c2f8f36

latent outcome hash:
406a5cafaa864379be96902d047c80d83b68809a5266166926d2b348642f72af

observation hash:
59c557647414d156650bb553235510dfb6019d9677dd32d1367cd44155b21ea9

transmission/observation events = 2178
detection events = 1036
online/offline agreement = true
```

### Full seed 101: both route windows

The archive tree initially lacked `.git`, while the benchmark unconditionally calls `git rev-parse HEAD`. Detached scratch metadata was added pointing to `ac04bbb`; no source file was changed.

Command:

```text
uv run python scripts/bench_dynamic_routes.py \
  --mode full --seed 101 --days 30 --window both \
  --out <base-or-candidate.json>

uv run python scripts/bench_dynamic_routes.py \
  --compare /tmp/jos-t2b-full-base-both.json \
            /tmp/jos-t2b-full-candidate-both.json
```

Compare output:

```text
fingerprints identical
standard bus: A_wall/B_wall=0.717758
standard care_resident: A_wall/B_wall=0.039762
standard care_staff: A_wall/B_wall=0.015493
standard community_indoor: A_wall/B_wall=1.264850
standard community_outdoor: A_wall/B_wall=1.108617
standard household: A_wall/B_wall=0.025753
standard school_class: A_wall/B_wall=0.026190
standard school_cross_class: A_wall/B_wall=0.736100
standard shared_vehicle: A_wall/B_wall=0.769160
standard workplace_team: A_wall/B_wall=3.792524
standard workplace_transient: A_wall/B_wall=0.892199
standard total: A_wall/B_wall=1.027445
term-boundary bus: A_wall/B_wall=0.690077
term-boundary care_resident: A_wall/B_wall=0.017658
term-boundary care_staff: A_wall/B_wall=0.015589
term-boundary community_indoor: A_wall/B_wall=1.442548
term-boundary community_outdoor: A_wall/B_wall=1.415899
term-boundary household: A_wall/B_wall=0.038114
term-boundary school_class: A_wall/B_wall=0.030686
term-boundary school_cross_class: A_wall/B_wall=0.743565
term-boundary shared_vehicle: A_wall/B_wall=0.605026
term-boundary workplace_team: A_wall/B_wall=4869.788572
term-boundary workplace_transient: A_wall/B_wall=0.876482
term-boundary total: A_wall/B_wall=1.234162
```

This covers all 561 route/date pairs. Timings were collected under concurrent audit load and are not used as performance evidence.

### Full seed 101: seven-day simulation

Base and candidate both produced:

```text
M4:
49464e77ac5754a114dadcf73b2e79e3bf94607d1d192a4f48229891e7d5b0bd

latent logical hash:
2425986db799d2b68b57b16b3726bec753135a716237e2b1ffe78d553da1ed8c

latent outcome hash:
f3c51be00168263c3a31dddc35157645f1912a56a4840e7804d30e543838e8ac

transmission events = 65
```

The additionally exercised observation hash also matched:

```text
9400c0229e7478bacd26979fc2a651a5cc7d6e7e4a01adc3cec52fa91bf14742
```

### Two-worker process-pool smoke

Candidate, CI mode, seeds 125 and 126, seven days:

```text
sequential_execution_mode = sequential
parallel_execution_mode = process_pool_spawn
parallel_actual_workers = 2
replicate_protected_hashes_equal = true
ensemble_logical_hash_equal = true
```

Both records matched on M4, latent, observation, scenario, intervention hashes, status, and error state.

### Memory estimate

Full seed 101, `community_indoor`, 2025-01-06:

```text
edges / old per-edge dict count = 191770

p1_index:        sys.getsizeof=1534272, nbytes=1534160, int64
p2_index:        sys.getsizeof=1534272, nbytes=1534160, int64
weight:          sys.getsizeof=1534272, nbytes=1534160, float64
persistence_days sys.getsizeof=1534272, nbytes=1534160, int64
```

All four arrays were C-contiguous.

## Step 4 — final state and verdict

```text
HEAD = 0dec469f83ee936b9b68e979e7a927807d7654e0
worktree_diff_exit=0
range_diff_check_exit=0
ancestor_exit=0
git status --short: empty
```

The three MINOR compatibility/test-coverage observations do not reach any protected scientific output. Canonical route rows, all-route fingerprints, adapter arrays, M4 identity, outbreak outputs, online observation, M8 outputs, artifacts, and process-pool replicate hashes remained exact.

TRANCHE-2B REVIEW: PASS