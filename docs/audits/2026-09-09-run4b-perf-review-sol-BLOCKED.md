# JOS run-4b independent review

Candidate: `ae0c6f8ddd2abfdb0d66f248721a36c2c375c3a9`  
Comparison tree: `f8d43beb556280eac488b45ceb0621b472cca0db`

## Findings

### BLOCKING — targeted community interventions are silently neutralized

[src/jersey_outbreak/interventions.py:906](/tmp/jos-run4b-review/src/jersey_outbreak/interventions.py:906)

The scalar oracle correctly applies `_target_adheres()` to residents before considering visitor scope at [interventions.py:354](/tmp/jos-run4b-review/src/jersey_outbreak/interventions.py:354). The vector implementation instead creates an all-false vector whenever either:

- `community_scope != "everyone_present"`, or
- any supported target restriction is present.

That means valid `residents_only` and targeted community reductions apply to nobody. These are supported schema values at [intervention_schemas.py:142](/tmp/jos-run4b-review/src/jersey_outbreak/intervention_schemas.py:142) and [intervention_schemas.py:159](/tmp/jos-run4b-review/src/jersey_outbreak/intervention_schemas.py:159).

Independent overlapping-intervention oracle:

```text
config_order=a-targeted,z-general
edge_count=5299 mismatch_count=4863 bytes_equal=False
first_mismatch=agent-m2-0000000,agent-m2-0000565
scalar=0.40000000000000002 vector=0.5
per_config_scalar=0.80000000000000004,0.5
per_config_vector=1,0.5
```

An end-to-end 14-day CI run with a valid age-targeted, residents-only community intervention confirmed protected-output drift:

```text
                                 base                         candidate
latent hash                      910944013359…                 d812b89aee9c…
latent outcome hash              21a162cee0ad…                 d8a9874a0be0…
observation hash                 a30bfa5c34bd…                 7758b06d470b…
transmission/observation events  294                           357
route-effects hash               f3f7ec4216e…                 c288fd9832fd…
```

Day-one `community_indoor` evidence:

```text
base:      mean_multiplier=0.5411398377052274, representation=effective
candidate: mean_multiplier=1.0,                representation=canonical_reused
```

The new parity test only parameterizes repository scenario YAMLs at [test_perf6_interventions.py:48](/tmp/jos-run4b-review/tests/test_perf6_interventions.py:48); none exercises targeted or `residents_only` community semantics, explaining the green suite.

### MAJOR — execution-adapter reuse is unreachable

[src/jersey_outbreak/execution_adapter.py:87](/tmp/jos-run4b-review/src/jersey_outbreak/execution_adapter.py:87)

The private adapter helper accepts `reuse_from`, but every real adapter call omits it at [execution_adapter.py:279](/tmp/jos-run4b-review/src/jersey_outbreak/execution_adapter.py:279), [execution_adapter.py:325](/tmp/jos-run4b-review/src/jersey_outbreak/execution_adapter.py:325), and [execution_adapter.py:379](/tmp/jos-run4b-review/src/jersey_outbreak/execution_adapter.py:379). No API request schema contains a reuse locator.

Therefore CLI reuse is reachable, but the claimed execution-adapter plumbing does not provide reuse across adapter invocations.

### MINOR — sequential ensemble output is not byte-for-byte unchanged

[src/jersey_outbreak/ensemble.py:1135](/tmp/jos-run4b-review/src/jersey_outbreak/ensemble.py:1135)

Sequential execution preserves all scientific hashes, records, and trajectories, but always adds three new diagnostics fields with zero values:

```text
job_payload_bytes_before
job_payload_bytes_after
initializer_payload_bytes
```

Consequently, the complete sequential `EnsembleResult.diagnostics` and serialized diagnostics artifact differ from base. This does not affect the protected ensemble logical hash, but the literal “byte-for-byte old” claim is false.

## Step 1 — source review

Diff scope:

```text
9 files changed, 1360 insertions(+), 180 deletions(-)
```

Only the requested `src`, `tests`, and benchmark-script files changed. `git diff --check` was clean, and the candidate worktree remained clean.

The candidate is not a descendant of the stated base because `f8d43be` is a later state/trail-only commit. Both share merge base `db086aa619206dd0313c6e6e337154973016c9e7`. A read-only `git merge-tree` check found no conflicts.

### PROV-8

All replaced cold-build paths retain their original parameters and ordering:

- Population CLI: identical config, generator, destination and writer.
- Structure CLI: identical relative-path resolution; automatic M2 remains under `destination.parent/populations`; M2 is reloaded before M3 generation.
- Network CLI: retains the explicit M3-requires-M2 error; automatic M2/M3 directories and explicit artifact handling are unchanged; M4 is written to the requested destination.
- Outbreak CLI: M2/M3/M4 remain under sibling `populations`, `structures`, and `networks` directories.
- Observation, ensemble, intervention, calibration and non-isolated helpers: M2/M3 remain under `destination.parent`.
- Travel isolated-parent paths: remain under `destination/parents`.
- Execution adapter: remains under `job_directory/parents`, with M4 written.
- Calibration regeneration: same M2/M3 inputs, seed-adjusted network config, full diagnostics, and no M4 artifact write.
- Ensemble regeneration: same seed-adjusted config, same parents, `diagnostics="internal"`, and no M4 artifact write.

Cold-path exceptions are not swallowed. Only explicit reuse verification failures are caught, logged, and converted to a fresh build.

Artifact IDs and directory names remain writer-owned and use the same complete configuration hashes; `parent_build.py` does not construct alternate artifact names or manifests.

### PERF-6

Inspection against the retained scalar oracle found:

- Isolation and household quarantine endpoint state and per-endpoint multiplication: equivalent.
- Masking and gathering reduction: equivalent target/adherence predicates.
- School closure: equivalent endpoint target, school membership and adherence rules.
- Workplace targeting, shared-workplace checks, WFH suppression and commute targeting: equivalent.
- Community reduction: not equivalent for targeted or residents-only configurations—the blocking finding above.
- Care setting targeting, resident-before-staff external priority, explicit route effects, and zero-beta care-edge retention: equivalent.
- Configuration order remains `(intervention_id, version)`.
- In-place vector multiplication preserves left-to-right `math.prod` order.
- Clamp remains `[0,1]`; the NaN guard is additional fail-closed behavior for otherwise-invalid results.
- `touched`, retained-index ordering, canonical-route reuse, and the no-relevant-config fast path are unchanged.

### PERF-9

Reuse prefilter fields are:

```text
artifact_id
generator_version
mode
seed
config_hash
```

Configuration hashes include the full typed configuration, including generator version. A legitimate artifact with a different configuration or generator version cannot pass.

Verification then:

- hashes every M2 declared output and recomputes the M2 logical hash;
- hashes and validates all required M3 parquet tables;
- recomputes the M3 logical hash;
- checks M3’s M2 artifact ID, complete M2 manifest hash, and M2 logical hash.

The tamper/config/seed rejection tests passed.

Pool workers are created with `spawn`; each fresh pool installs its parents once through the initializer. Although the frozen dataclasses contain mutable lists/dictionaries, network generation reads them without mutation. Pool-versus-sequential equality and repeated-seed results showed no leakage.

Checkpoint provenance remains the same tuple of seed, base-config hash, code identity, M2 logical hash and M3 logical hash.

## Step 2 — executor test batch

Command:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q
  tests/test_golden_hashes.py tests/test_hashing.py
  tests/test_perf6_interventions.py tests/test_c5_m7_integrity.py
  tests/test_cli_integration.py tests/test_calibration.py
  tests/test_m9_api.py tests/test_m9_2_provenance.py
  tests/test_job_liveness.py tests/test_route_snapshot_columns.py
  tests/test_route4_weekday_memo.py tests/test_bench_dynamic_routes.py
  tests/test_networks.py tests/test_c2_network_semantics.py
  tests/test_ensemble.py tests/test_outbreak.py tests/test_observation.py
  tests/test_m7_interventions.py tests/test_m8_travel.py
  tests/test_m8_1_travel_integrity.py tests/test_m8_2_travel_closure.py
  tests/test_b01_portable_artifacts.py tests/test_m9_1_job_integrity.py
  tests/test_perf9_parent_reuse.py
```

Output:

```text
234 passed, 4 warnings in 524.08s (0:08:44)
```

## Step 3 — independent probes

### (a) CI seed 126 route gate

Base and candidate network probes compared 11 routes across 12 consecutive dates plus configured snapshot dates:

```text
snapshot_records=143 exact_equal=True
array_fields_compared=572
m4_hash=8a31c8bd17119c66706f8377aa6073bce7f359cd92027bc6c3e4017b6aa47918
```

Canonical edge rows and exact `p1/p2/beta/dur` dtype, shape and bytes matched.

### (b) CI seed 126, 30-day online observation

```text
latent_hash=849a5014bd9f39f44cba2b69d7c00fd4fd11ba109a53de1c3be85849dda8cb4b
latent_outcome_hash=45f9b044bd1170fbd57190d119039bc76b2c9d06388afd309f34548f6727e2e4
observation_hash=10952a5755987477bcc18d0223d93180ef8220eb6fd5dee740ba6ebd23350023
transmission/observation events=2184
detection events=1039
base == candidate: true
```

### (c) Full seed 101 route harness

Command:

```text
uv run python scripts/bench_dynamic_routes.py --compare \
  /tmp/jos-audit-full-base-routes.json \
  /tmp/jos-audit-full-candidate-routes.json
```

Output:

```text
fingerprints identical
standard:      stable_int_calls base=13779583 candidate=13779583 equal=True
term-boundary: stable_int_calls base=9494324  candidate=9494324  equal=True
```

All 11 routes were covered in both windows.

### (d) Full seed 101, seven days

```text
m4_hash=49464e77ac5754a114dadcf73b2e79e3bf94607d1d192a4f48229891e7d5b0bd
latent_hash=2425986db799d2b68b57b16b3726bec753135a716237e2b1ffe78d553da1ed8c
latent_outcome_hash=f3c51be00168263c3a31dddc35157645f1912a56a4840e7804d30e543838e8ac
observation_hash=9400c0229e7478bacd26979fc2a651a5cc7d6e7e4a01adc3cec52fa91bf14742
events=65
base == candidate: true
```

### (e) Two-worker CI ensemble

Candidate pool, candidate sequential, and base sequential:

```text
logical_content_hash_all_equal=True
records_all_equal=True
trajectories_all_equal=True
pool_mode=process_pool_spawn workers=2
payload=3765504->21598 initializer=1781648
ensemble_hash=69a9e341912d5a392fb5b3cfa36cb55fed96756cc66c1e28b1cdfa4eb502eca6
```

### Resume after termination

The first process was sent SIGTERM immediately after the first checkpoint appeared:

```text
killed=1 first_status=143 checkpoint_count=1
```

Rerun:

```text
ENSEMBLE RESUME: resumed=1 run=2 ignored=0
logical_content_hash_equal=True
records_equal=True
trajectories_equal=True
```

The resumed and clean three-seed ensemble hash was:

```text
44e8dad9a91cec88121e4857d134dfb83f58e55e51439d1624b63002ea42ea9d
```

### (f) Standalone CI CLI artifacts

Base and candidate produced the same artifact IDs and logical hashes:

```text
M2 28a6d90a96454d11dcd6ad9d4531d69f9e4ec4396b802780084d3ae598c839a0
M3 f072042f07db46a94fd61781eb9ee99545a6dc169d34b83d6de21ffdf56e3ce3
M4 749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657
```

For population, structure and network outputs:

```text
file_set_equal=True
normalized_equal=True
binary_scientific_differences=[]
```

Every parquet file was byte-identical. JSON/Markdown matched after excluding creation/runtime/peak-memory values and their dependent hashes; `git_commit` was also normalized because the prescribed base archive has no `.git` directory.

Verified reuse produced:

```text
PARENT REUSE: REUSED M2=… M3=…
M4 logical_content_hash=749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657
```

### (g) Full seed 101, 30-day `m7_combined`

Base and candidate payloads, including every intervention and latent parquet SHA-256, were exactly equal:

```text
latent_hash=1a72de5dc784beb80ee510b321ff973e6320bd876b7de1b4da982b4671d14211
latent_outcome_hash=247dddb94abc842381fdb6adac8fe0489fcbab75a422644ef14eefa99136357a
observation_hash=dd833218533903421dc96475d48a1d44727114519f7a66eeb2abb362032cbda1
route_effects.parquet=e034318fbb900b10af658d4f2b6a3d7ce4202628c7fa3c378d32ed289cf00019
events=1670
full_run_payload_exact_equal=True
```

No 180-day or 30-replicate run was performed.

RUN-4B REVIEW: BLOCKED — targeted/residents-only community interventions are silently neutralized by the PERF-6 vector path