## Target verification

```text
$ git rev-parse HEAD
84b96763d9c5d6c85839218aba9d3876b96c8f7d

$ git merge-base --is-ancestor ef26e1350b3e0a53c436036b446ffeb819f4a1cd HEAD && echo ancestor-ok
ancestor-ok
```

The same SHA and ancestry result were reproduced after the review. Initial and final `git status --short` were empty.

## 1. Local CI mirror

Environment setup:

```text
$ uv --version
uv 0.12.9 (x86_64-unknown-linux-gnu)

$ uv sync --frozen
Using CPython 3.12.13
Creating virtual environment at: /tmp/jos-review5-head-venv
Installed 75 packages
```

Gate results:

```text
$ uv lock --check
Resolved 77 packages in 1ms

$ uv run python -m compileall -q src
(exit 0; no output)

$ uv run pytest
================= 390 passed, 9 warnings in 872.69s (0:14:32) ==================

$ uv run ruff check .
All checks passed!

$ uv run ruff format --check .
231 files already formatted

$ git diff --check
(exit 0; no output)
```

The warnings were one third-party Starlette deprecation and eight Starsim zero-timestep warnings.

Mypy covered the CI verify-job list plus every touched source module:

```text
mypy module count: 36
src/jersey_outbreak/api.py
src/jersey_outbreak/bundle_selftest.py
src/jersey_outbreak/calibration_artifacts.py
src/jersey_outbreak/cli.py
src/jersey_outbreak/demo.py
src/jersey_outbreak/ensemble.py
src/jersey_outbreak/ensemble_artifacts.py
src/jersey_outbreak/execution_adapter.py
src/jersey_outbreak/intervention_analysis.py
src/jersey_outbreak/intervention_artifacts.py
src/jersey_outbreak/intervention_schemas.py
src/jersey_outbreak/interventions.py
src/jersey_outbreak/job_finalizer.py
src/jersey_outbreak/job_manager.py
src/jersey_outbreak/job_registry.py
src/jersey_outbreak/network_artifacts.py
src/jersey_outbreak/network_generator.py
src/jersey_outbreak/network_schemas.py
src/jersey_outbreak/observation_artifacts.py
src/jersey_outbreak/outbreak_artifacts.py
src/jersey_outbreak/outbreak_runner.py
src/jersey_outbreak/population_artifacts.py
src/jersey_outbreak/population_structure_artifacts.py
src/jersey_outbreak/population_structure_controls.py
src/jersey_outbreak/population_structure_generator.py
src/jersey_outbreak/population_structure_schemas.py
src/jersey_outbreak/provenance.py
src/jersey_outbreak/scenario.py
src/jersey_outbreak/scientific_hashes.py
src/jersey_outbreak/scientific_verification.py
src/jersey_outbreak/staffing_evidence.py
src/jersey_outbreak/staffing_generator.py
src/jersey_outbreak/starsim_adapter.py
src/jersey_outbreak/travel.py
src/jersey_outbreak/travel_artifacts.py
src/jersey_outbreak/verification_archive.py
Success: no issues found in 36 source files
```

Relocation gate:

```text
$ uv run python scripts/ci_relocation_check.py
{"artifact_directory": "/home/steven/jos-review5-wd/outputs/interventions/jos-intervention-m7-ci-seed-123-c0be3d419f32", "artifact_id": "jos-intervention-m7-ci-seed-123-c0be3d419f32", "diagnostics_status": "passed", "logical_content_hash": "1e9f01ed1d770bbeb592c3d0c69add44040d2e80339b93b884b24701f4ed8a99", "runtime_seconds": 3.9499812719996044, "scenario_hash": "7158b33cb7eba93112b1326aacc253d19136a4a85f70c7c4245113a26478665a", "scenario_id": "m7-baseline", "travel_controls": "DEFERRED TO M8"}
verifier success: m7_intervention jos-intervention-m7-ci-seed-123-c0be3d419f32
```

## 2. Base/HEAD exactness

Base snapshot creation and `uv sync --frozen` completed successfully under `/tmp/jos-review5-base`.

All requested commands exited 0. Their primary logical hashes were identical:

| Command | Base | HEAD |
|---|---|---|
| population, ci seed 123 | `28a6d90a96454d11dcd6ad9d4531d69f9e4ec4396b802780084d3ae598c839a0` | same |
| structure, ci seed 123 | `f072042f07db46a94fd61781eb9ee99545a6dc169d34b83d6de21ffdf56e3ce3` | same |
| network, ci seed 123 | `749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657` | same |
| ensemble, seeds 101–103, 7 days, 2 workers | `9ee05d0684e86c776eb67913c4b3129ccebbaec83ad4d0c620fbaa074b25641d` | same |

The recursively produced parent manifests also matched:

```text
population seed 101: 3fbc51a1cf64f895b0e16f658b3b9ba33ec760bd08f742fd54fd1fa90b66af44
population seed 123: 28a6d90a96454d11dcd6ad9d4531d69f9e4ec4396b802780084d3ae598c839a0
structure seed 101:  99f23a51b5fb442b57795749362b666f8cee69499a69dca860d3f6706cf37729
structure seed 123:  f072042f07db46a94fd61781eb9ee99545a6dc169d34b83d6de21ffdf56e3ce3
every manifest logical hash identical: True
```

The ensemble’s scientific files were byte-identical:

```text
ensemble_summary.parquet:       bf5d9358b3903efc0c8e868d68bcbfc5d62bcf2ccd68dcfd50578b4dabbc374b
replicate_trajectories.parquet: ce29b40ce40e8e0df633c9a972fb6e81ad3edc0f78aab3a8e4567637d6f2f9de
replicate_grid.parquet:         6a78aefea947839ba84c6d032561fbf9e914c251af4279915ffb2f6640c58966d
ensemble_config.json:           e2272ed6141fa1138cc94759012bdbf5afaf961d83aba68c71724d2d6df51050
```

Every differing manifest key:

- Ensemble: `created_at`, `git_commit`, `peak_memory_bytes`, `runtime_seconds`, `replicate_records[0..2].runtime_seconds`, and SHA-256 records for `replicate_records.json` and `diagnostics.json`.
- Network: `created_at`, `git_commit`, `peak_memory_bytes`, `runtime_seconds`, and SHA-256 records for `diagnostics.json` and `benchmark.json`.
- Direct population: `created_at`, `git_commit`, `peak_memory_bytes`, `runtime_seconds`, plus SHA-256 and size records for `diagnostics.json`, `diagnostics.md`, and `benchmark.json`.
- Nested populations, seeds 101 and 123: `created_at`, `git_commit`, `peak_memory_bytes`, `runtime_seconds`, plus SHA-256 records for `diagnostics.json`, `diagnostics.md`, and `benchmark.json`.
- Direct structure: `created_at`, `git_commit`, `m2_manifest_hash`, `peak_memory_bytes`, `runtime_seconds`, plus SHA-256 records for `diagnostics.json`, `diagnostics.md`, and `benchmark.json`.
- Nested structure seed 101: the direct-structure set plus size records for those three diagnostic/benchmark files.
- Nested structure seed 123: the direct-structure set.

All unlisted manifest keys—including M2/M3/M4/M5 identities and logical hashes—were equal.

## 3. Independent highest-risk checks

PERF-10, deliberately failed replicate:

```text
BASE:
status=partial
failed_replicates=1
summary_sha256=3f2818e1268b238400957d92cac73e7bd96fdd0cdc0f615bb45c025c4890efd2
grid_sha256=c968cc7a42d77095e273f50a2ca6e51ff6d5e815208d258f15dcfd46d068026d
logical_content_hash=db0f9eec106f35ef849849d38b309db11d78d3fb2b4271ef40c323c398b9154c

HEAD:
status=partial
failed_replicates=1
summary_sha256=3f2818e1268b238400957d92cac73e7bd96fdd0cdc0f615bb45c025c4890efd2
grid_sha256=c968cc7a42d77095e273f50a2ca6e51ff6d5e815208d258f15dcfd46d068026d
logical_content_hash=db0f9eec106f35ef849849d38b309db11d78d3fb2b4271ef40c323c398b9154c
```

The failed seed’s grid cell was `failed_replicate`, `value=null`, `contributes=false`; the summary contained two contributors, one failed replicate, and median `20.0` on both trees.

Verifier fixes, cross-year fail-fast:

```text
error_type=ValueError
error=school route date range 2025-07-06 to 2026-01-01 is outside school calendar year 2025
sim_constructor_calls=0
```

Provenance helpers, comparison canonicalization pinned to base:

```text
BASE 9579e685afb804dea42ecba2df4bd7ec0bd1c2507810fdf79745573e55aa56f2
HEAD 9579e685afb804dea42ecba2df4bd7ec0bd1c2507810fdf79745573e55aa56f2
```

Additional direct helper checks:

```text
metric_registry_key_sets_equal=True count=24
git_metadata_repo=('84b96763d9c5d6c85839218aba9d3876b96c8f7d', False)
git_metadata_outside=(None, True)
ensemble_identity_repo=84b96763d9c5d6c85839218aba9d3876b96c8f7d
ensemble_identity_outside=source:41fea7c824eacd183689d82a7ea2849e48f7954da5f371393c3ca71b9600166f
```

Job ordering, deleted FIFO-head request:

```text
A_state=FAILED
A_error_code=request_not_persisted
A_event_types=job_submitted,job_started,job_failed
A_result_manifest_exists=False
B_state=SUCCEEDED
B_error_code=None
B_event_types=job_submitted,job_started,phase_changed,phase_changed,phase_changed,phase_changed,phase_changed,phase_changed,artifact_written,artifact_verified,job_completed
B_result_manifest_exists=True
```

## 4. Scope

Actual diff stat:

```text
 src/jersey_outbreak/api.py                         |  27 +--
 src/jersey_outbreak/bundle_selftest.py             |  58 +++--
 src/jersey_outbreak/calibration_artifacts.py       |  23 +-
 src/jersey_outbreak/cli.py                         |   6 +-
 src/jersey_outbreak/demo.py                        |  33 +--
 src/jersey_outbreak/ensemble.py                    |  68 ++++--
 src/jersey_outbreak/ensemble_artifacts.py          |  23 +-
 src/jersey_outbreak/execution_adapter.py           |  21 +-
 src/jersey_outbreak/intervention_artifacts.py      |  21 +-
 src/jersey_outbreak/job_finalizer.py               |  89 ++++---
 src/jersey_outbreak/job_manager.py                 | 161 +++++++++----
 src/jersey_outbreak/job_registry.py                |  23 +-
 src/jersey_outbreak/network_artifacts.py           |  23 +-
 src/jersey_outbreak/network_schemas.py             |  50 +++-
 src/jersey_outbreak/observation_artifacts.py       |  23 +-
 src/jersey_outbreak/outbreak_artifacts.py          |  23 +-
 src/jersey_outbreak/outbreak_runner.py             |  28 +--
 src/jersey_outbreak/population_artifacts.py        |  24 +-
 .../population_structure_artifacts.py              |  23 +-
 src/jersey_outbreak/provenance.py                  |  35 +++
 src/jersey_outbreak/scientific_hashes.py           |  66 +++---
 src/jersey_outbreak/scientific_verification.py     |   6 +
 src/jersey_outbreak/travel.py                      |  14 --
 src/jersey_outbreak/travel_artifacts.py            |  23 +-
 src/jersey_outbreak/verification_archive.py        |  64 +++---
 tests/test_b01_portable_artifacts.py               |  43 ++++
 tests/test_m9_api.py                               |  18 +-
 tests/test_perf10_grid_once.py                     |  58 +++++
 tests/test_prov_helpers.py                         | 180 +++++++++++++++
 tests/test_prov_job_ordering.py                    | 255 +++++++++++++++++++++
 tests/test_v121_prov_verifier_fixes.py             | 202 ++++++++++++++++
 31 files changed, 1211 insertions(+), 500 deletions(-)
```

Scope conclusions:

- All 25 source files and six tests map to the four declared units.
- No `pyproject.toml` or `uv.lock` change.
- No golden fixture or `tests/test_golden_hashes.py` change.
- No undeclared scientific hash, artifact identity, schema, or provenance change found.
- Final `git diff --check` passed and `git status --short` remained empty.

## Findings

| Severity | File:line | Finding |
|---|---|---|
| — | — | No MAJOR or MINOR findings. All declared gates passed. |

JOS V1.2.1 INTEGRATION-RUN5 REVIEW PASS