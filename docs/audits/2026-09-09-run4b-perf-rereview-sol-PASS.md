# JOS run-4b bounded re-review

Candidate: `a588e22560f43e019f45fc63475b61c904c68cd5`  
Base: `96f21f25019dd15f5712e2bae901029454dbe1c3`  
Previous candidate: `ae0c6f8ddd2abfdb0d66f248721a36c2c375c3a9`

No new BLOCKING, MAJOR, or MINOR findings.

## Previous BLOCKING — PERF-6 targeted community interventions: CLOSED

The corrected vector predicate in [interventions.py](/tmp/jos-run4b-rereview/src/jersey_outbreak/interventions.py:883) applies `_vector_target_adheres()` to resident UIDs, then separately admits visitors only for unrestricted `everyone_present` configurations. No production per-config scalar fallback exists.

Independent overlapping oracle:

```text
config_order=a-targeted,z-general
edge_count=5299 mismatch_count=0 bytes_equal=True
a-targeted: mismatches=0 bytes_equal=True
z-general: mismatches=0 bytes_equal=True
```

The exact previous 14-day targeted/residents-only probe was rerun on both trees:

```text
latent_hash          9109440133594b341989f1a4228a0c5b5852224a7bdcc63910b02d6e252b47e4
latent_outcome_hash  21a162cee0ada695297cc18950f177228185362659eb61c5ea005f5ba4d1ace5
observation_hash     a30bfa5c34bd9cd143ebe946ef042793101361274737bc3c87e21ae3f3cc17ac
transmission events  294
observation events   294
base == candidate    true
```

Day-one `community_indoor` was identical:

```text
edge_count=5299
mean_multiplier=0.5411398377052274
representation=effective
```

All eight emitted parquet hashes also matched.

The new schema grid genuinely covers:

- All 9 intervention kinds.
- Both community scopes.
- Every `TargetPopulation` field through 15 variants, including both non-default care roles.
- Adherence `0.0`, `0.5`, and `1.0`.
- All three care targets.
- Every generated route over seven days, including care routes.
- Targeted/general overlap in both orders.
- A separately injected visitor endpoint.

For every config/route/day it independently invokes the scalar oracle per edge and compares exact float64 bytes.

Command and trimmed output:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q tests/test_perf6_interventions.py -vv
...
20 passed in 235.80s
```

## Previous MAJOR — PERF-9 adapter reuse unreachable: CLOSED

All three real adapter branches now pass the job-owned reuse root:

- Scenario: [execution_adapter.py](/tmp/jos-run4b-rereview/src/jersey_outbreak/execution_adapter.py:282)
- Ensemble: [ Outdoors](/tmp/jos-run4b-rereview/src/jersey_outbreak/execution_adapter.py:330)
- Comparison: [execution_adapter.py](/tmp/jos-run4b-rereview/src/jersey_outbreak/execution_adapter.py:386)

The root is the resolved `state_dir/jobs/<internal UUID>` job directory. Reuse cannot search sibling jobs. Acceptance additionally requires exact artifact ID, generator version, mode, seed, full config hash, verified tables/logical hashes, and the complete M3→M2 provenance tuple in [parent_build.py](/tmp/jos-run4b-rereview/src/jersey_outbreak/parent_build.py:82).

Focused test:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q \
  tests/test_perf9_parent_reuse.py::test_execution_adapter_reuses_job_parent_across_invocations -vv
...
1 passed, 3 warnings in 6.71s
```

Independent two-invocation counter:

```text
first_generator_calls={'m2': 1, 'm3': 1} artifacts=1
second_generator_calls={'m2': 0, 'm3': 0} artifacts_equal=True
```

Independent generator-version mismatch probe:

```text
PARENT REUSE: REJECTED ... no exact M2/M3 manifest pair ...
changed_generator_reused=False generator_calls={'m2': 1, 'm3': 1}
```

## Previous MINOR — sequential diagnostics drift: CLOSED

The pool payload fields are now added only when an actual multi-worker job exists at [ensemble.py](/tmp/jos-run4b-rereview/src/jersey_outbreak/ensemble.py:1176). They are absent from sequential diagnostics.

Sequential CI seeds 123–124, seven days:

```text
logical_hash=caad1948b3474653bc44cbcb4ce75494025b5898e8eefa6f14a758b8a70d7de6
base == candidate scientific records/trajectories=true
```

`ensemble_config.json` and all three parquet files were byte-identical. JSON differences were limited to pre-existing volatile runtime/peak-memory measurements, `created_at`, dependent manifest checksums, and the expected `git_commit` difference because the prescribed base archive has no `.git` directory. The three previously added sequential payload fields were absent.

## Regression and protected outputs

Requested regression batch:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q \
  tests/test_perf6_interventions.py tests/test_m7_interventions.py \
  tests/test_c5_m7_integrity.py tests/test_perf9_parent_reuse.py \
  tests/test_ensemble.py tests/test_job_liveness.py tests/test_m9_api.py \
  tests/test_m9_1_job_integrity.py tests/test_m9_2_provenance.py \
  tests/test_cli_integration.py tests/test_golden_hashes.py tests/test_outbreak.py

146 passed, 6 warnings in 458.44s
```

Full seed-101, 30-day ` reminders Blur Botsupal multiline m7_combined`:

```text
latent_hash          1a72de5dc784beb80ee510b321ff973e6320bd876b7de1b4da982b4671d14211
latent_outcome_hash  247dddb94abc842381fdb6adac8fe0489fcbab75a422644ef14eefa99136357a
observation_hash     dd833218533903421dc96475d48a1d44727114519f7a66eeb2abb362032cbda1
events                1670 transmission / 1670 observation
base == candidate     true
```

All eight latent/intervention parquet files were byte-identical, including:

```text
daily_intervention_state.parquet  953d1d3972eba8df071b95ae165f3bb20fc631deb0e72e2fd24b38851caa0ec2
intervention_events.parquet       99883518a95115986656672457c0f0bc1655dccca38b03f8aebbefc40202d2d4
route_effects.parquet             e034318fbb900b10af658d4f2b6a3d7ce4202628c7fa3c378d32ed289cf00019
```

Two-worker CI ensemble, seeds 125–126, seven days:

```text
execution_mode=process_pool_spawn
actual_workers=2
payload=3766690 -> 21602 bytes
initializer=1782242 bytes
logical_hash=9ae6910802d3206866f8baa9f8888c1d5eefc157d98b40f19ef0fe3014bdb0e5
pool == candidate sequential == base sequential: true
```

Record-core, trajectory, grid, and summary hashes all matched.

Retry diff:

```text
5 files changed, 423 insertions(+), 15 deletions(-)
```

Candidate/base implementation diff:

```text
9 files changed, 1771 insertions(+), 183 deletions(-)
```

`git diff --check` passed and the candidate worktree remained clean. No forbidden long run was performed.

RUN-4B RE-REVIEW: PASS