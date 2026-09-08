# JOS run-4 independent review

- Candidate: `e26ef918ae09509cf9959af9aaa3f522e825ea56`
- Base: `e8579a91029e933e6c0e47f0fb11e80b060f26b5`
- Role: independent read-only auditor
- Result: protected scientific outputs are exact; safe to merge.

## Findings

MINOR — [network_generator.py:2445](/tmp/jos-run4-review/src/jersey_outbreak/network_generator.py:2445): default/full diagnostics do not retain the base’s literal generation-time call order.

The base runs `_route_diagnostics()` before `baseline_snapshot` and `_route_overlap_matrix`; the candidate constructs the baseline and overlap first. A probe hashing the complete ordered stable-key payload stream therefore differed:

```text
candidate: 73513 calls, digest 302636cc...b922d46
base:      73513 calls, digest 1f67f079...3ee7a1
```

This does not affect scientific state: stable integers are keyed SHA-256 operations, not sequential PRNG draws. When snapshots were invoked in the same route/date order, both trees produced exactly:

```text
snapshot_stable_calls=158227
snapshot_ordered_payload_digest=cd7b9f049dea01a61073a3b751db9b0d29a13831fa89fa3846314abd937f6b7e
```

Final cache keys, counter totals, route fingerprints, M4 hashes, artifacts, and outbreak outputs were identical.

MINOR — [network_generator.py:2636](/tmp/jos-run4-review/src/jersey_outbreak/network_generator.py:2636): internal diagnostics add a `cross_route.route_participation` marker even though full diagnostics never expose that key. It represents a skipped intermediate computation, not an omitted public field, but `route_analysis.omitted_keys` describes it as an omitted key. Internal diagnostics never reach a public artifact or schema, so there is no protected-output impact.

No BLOCKING or MAJOR findings.

## 1. Diff and behavioural review

Commands:

```text
git diff --check e8579a9 e26ef91 -- src tests scripts
git diff --stat e8579a9 e26ef91 -- src tests scripts
git diff e8579a9 e26ef91 -- src tests scripts
```

Result:

```text
7 files changed, 998 insertions(+), 66 deletions(-)
range_diff_check_exit=0
```

The complete tree additionally differs by one `.claude/decisions.tsv` row added to `main` after the candidate was created. The commits diverge at `bb66159`; `git merge-tree` showed no conflict. This explains why the nominated base is not an ancestor without affecting source equivalence or merge safety.

### Hash-key suffix pre-encoding

- `stable_int_prefixed(prefix, suffix)` increments `STABLE_INT_COUNTER` once and hashes exactly `prefix + b"|" + suffix`, retaining the first eight SHA-256 bytes, big-endian and unsigned.
- Actual `agent_id` values are Python strings; `agent_id.encode()` is therefore byte-identical to `str(agent_id).encode("utf-8")`.
- `contact_index` comes from `range()`, hence is a Python integer. `f"{agent_id}|{contact_index}".encode()` exactly matches the old `"|".join(str(...)).encode("utf-8")`.
- The precomputed contact range uses `max(regular_contacts, daily_contacts)`, covering every subsequently indexed contact.
- Map construction performs no stable-hash calls. The four replacements remain at the same nested-loop positions, so per-builder call order is unchanged.
- Independent payload/counter probe:

```text
payload_bytes_equal=True counter_once_each=True
```

- The committed 10,000-triple equality test passed.

### PERF-4 diagnostics switch

Actual omitted full-mode values are:

- The complete 11-route `routes` mapping. Each route’s omitted fields include eligibility/participation/edge counts, degree summaries, components, clustering, age and parish mixing, edge-weight summaries, duplicate/self-edge counts, route metadata, age-mixing matrix, persistence and cross-day turnover diagnostics.
- `cross_route.zero_non_household_contacts`
- `cross_route.agents_by_route_type_count`
- `cross_route.community_participation_by_residence_type`

Each is replaced by an explicit marker. Internal mode additionally exposes `route_participation` and top-level `route_analysis` markers, as noted above.

Reader audit:

- `network_artifacts.py` is the only consumer of the detailed M4 diagnostic keys; it renders the Markdown report and writes `diagnostics.json`.
- The CLI reads only full-mode benchmark/status values after artifact creation.
- Calibration and execution-adapter M4 builds omit the argument and therefore remain full mode.
- `ensemble.py::_run_replicate_job` is the sole production internal-mode call.
- The worker-local `GeneratedNetworks` is consumed by outbreak/observation code and discarded; only hashes, trajectories and status enter `ReplicateOutput`.
- `ensemble.py` contains no network-artifact writer import or call.
- No frontend reader or API schema references the omitted M4 diagnostic fields.
- Diagnostics are absent from the M4 scientific hash payload.

Independent mode comparison:

```text
hash_equal=True
staffing_equal=True
routes_full_count=11 internal={'omitted': 'internal_replicate_mode'}
cross_common_value_changes=[
  'agents_by_route_type_count',
  'community_participation_by_residence_type',
  'zero_non_household_contacts'
]
```

The default/full artifact comparison is reported under probe 3(f).

### ROUTE-5 phase 2

The columnar twins preserve:

- Complete groups: sorted unique IDs, canonical string order, all unordered pairs, float weight and integer persistence conversion.
- Rings: modulo wrap-around and `min(contacts_per_participant, n-1)` clamp.
- Empty semantics: groups smaller than two and non-positive contact counts produce typed empty columns.
- Exclusions: the base only recognizes already canonical `(min_string, max_string)` pairs; reversed input pairs remain non-excluding. The rank conversion preserves this asymmetric behaviour, as well as unknown-pair no-op behaviour.
- Grouped rings: identical group enumeration and `_ordered_ids()` calls, followed by global pair-sorted deduplication.
- School staff: identical school/year order, pupil ordering, staff sorting, contact clamp, start draw, wrap-around and self-edge removal.
- Deduplication: canonical string-rank pair order, greatest weight, and first-emitted tie winner. Pupil rows precede staff rows as in the base concatenation.
- Bus weekends: typed empty columns reconstruct the same empty snapshot.
- Adapter output: exact endpoint, beta and duration bytes.

Independent randomized oracle:

```text
random_columnar_oracle_cases=1000 complete/ring/grouped exact
school_staff_edge_cases=20 exact incl canonical/reversed/unknown exclusions
```

The original dictionary helpers are byte-unchanged. Remaining callers include structural household/school/work/care/shared-vehicle construction and M8 terminal/taxi route building.

## 2. Prescribed test batch

Command:

```text
UV_CACHE_DIR=/tmp/uv-cache MPLCONFIGDIR=/tmp/jos-run4-mpl \
uv run pytest -q \
  tests/test_golden_hashes.py tests/test_hashing.py \
  tests/test_hashkey_suffix.py tests/test_perf4_diagnostics.py \
  tests/test_route_snapshot_columns.py tests/test_route4_weekday_memo.py \
  tests/test_bench_dynamic_routes.py tests/test_networks.py \
  tests/test_c2_network_semantics.py tests/test_ensemble.py \
  tests/test_outbreak.py tests/test_observation.py \
  tests/test_m7_interventions.py tests/test_m8_travel.py \
  tests/test_m8_1_travel_integrity.py tests/test_m8_2_travel_closure.py \
  tests/test_b01_portable_artifacts.py tests/test_m9_1_job_integrity.py \
  tests/test_route5_phase2_columns.py
```

Result:

```text
166 passed, 4 warnings in 455.61s (0:07:35)
```

The four warnings were one Starlette deprecation and three expected one-day Starsim timeline warnings. The phase-2 base tests were not skipped; `/tmp/jos-r5b-base/network_generator.py` had the exact pinned-base SHA-256.

## 3. Independent probes

### (a) CI seed 126: M4, 12 dates plus snapshots

```text
m4=8a31c8bd17119c66706f8377aa6073bce7f359cd92027bc6c3e4017b6aa47918
routes=11
unique_dates=13
route_date_equalities=143
exact_p1_p2_beta_dur=572
```

Thirteen unique dates result because snapshot dates overlap the 12-day consecutive window.

### (b) CI seed 126: 30-day online observation

Both isolated trees produced:

```text
latent=849a5014bd9f39f44cba2b69d7c00fd4fd11ba109a53de1c3be85849dda8cb4b
outcome=45f9b044bd1170fbd57190d119039bc76b2c9d06388afd309f34548f6727e2e4
observation=10952a5755987477bcc18d0223d93180ef8220eb6fd5dee740ba6ebd23350023
event_count=2184
```

Transmission-event rows were exactly equal.

### (c) Full seed 101 route harness

Command:

```text
uv run python scripts/bench_dynamic_routes.py \
  --compare /tmp/jos-run4-full-base.json \
            /tmp/jos-run4-full-candidate.json
```

Trimmed output:

```text
fingerprints identical
standard: stable_int base=13779583 candidate=13779583 equal=True
term-boundary: stable_int base=9494324 candidate=9494324 equal=True
```

Coverage was all 11 routes over 330 standard and 231 term-boundary route/date pairs.

### (d) Full seed 101, seven days

Both trees produced:

```text
m4=49464e77ac5754a114dadcf73b2e79e3bf94607d1d192a4f48229891e7d5b0bd
latent=2425986db799d2b68b57b16b3726bec753135a716237e2b1ffe78d553da1ed8c
outcome=f3c51be00168263c3a31dddc35157645f1912a56a4840e7804d30e543838e8ac
event_count=65
```

### (e) Two-worker process pool

Commands:

```text
(cd /tmp/jos-review4-base &&
  .venv/bin/python /tmp/run4_ensemble_probe.py --base-only)

(cd /tmp/jos-run4-review &&
  .venv/bin/python /tmp/run4_ensemble_probe.py)
```

Result:

```text
sequential_execution_mode=sequential
parallel_execution_mode=process_pool_spawn
parallel_actual_workers=2
pool_equals_candidate_sequential=True
candidate_sequential_equals_base_sequential=True
```

Seeds 126 and 127 matched on M4, latent, observation, scenario/intervention hashes, status and error.

### (f) Default CLI artifact

Commands:

```text
jos network generate --mode ci --seed 123 --output-dir <base>
jos network generate --mode ci --seed 123 --output-dir <candidate>
diff -qr <base-artifact> <candidate-artifact>
```

Both produced M4 hash:

```text
749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657
```

The file sets matched. Byte-identical files were:

```text
care_staff_assignments.parquet
diagnostics.md
memberships.parquet
route_specs.json
school_staff_assignments.parquet
snapshot_edges.parquet
staffing_provenance.json
structural_edges.parquet
```

Differences were limited to:

- `benchmark.json`: runtime and peak-memory measurements.
- `diagnostics.json`: the same two benchmark values.
- `manifest.json`: runtime, peak memory, `created_at`, expected `git_commit=None` for the archive versus the candidate SHA, and the dependent diagnostics/benchmark hashes.

No scientific or descriptive diagnostic value differed.

## Performance prerequisite

Command:

```text
uv run python scripts/bench_perf4_diagnostics.py \
  --mode full --seed 101 --repeats 5
```

Result:

```text
median(full): 29.134 s
median(internal): 21.081 s
median saving: 8.052 s
ship decision: SHIP (requirement: >= 5.0 s)
```

Final repository state:

```text
HEAD=e26ef918ae09509cf9959af9aaa3f522e825ea56
worktree_diff_exit=0
range_diff_check_exit=0
git status --short: empty
```

RUN-4 REVIEW: PASS