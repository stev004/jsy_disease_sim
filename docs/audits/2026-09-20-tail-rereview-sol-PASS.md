TAIL RE-REVIEW: PASS

Reviewed target: `a4a44e3c25a81ac8ff30d733e9cd0d8065f16151`

Corrective comparison base: `d3f4d6434aa2c0158b8d277f1cf61163ee2f8c19`

Scientific A/B base: `6eb05c2dfa88ff1818ec210f76be93c2fd5c7e9f`

Review date: 2026-09-20

No blocking findings. M1 and M2 are closed by the two bounded correctives. The prior report named in the brief is not in the target tree; it was read from its repository object at commit `854d984`.

## Scope

`d3f4d64..a4a44e3` contains exactly two corrective commits and two merge commits:

```text
$ git rev-parse HEAD
a4a44e3c25a81ac8ff30d733e9cd0d8065f16151
$ git rev-list --count d3f4d64..a4a44e3
4
$ git log --oneline --reverse d3f4d64..a4a44e3
c0e9a74 datafix corrective 1: daily_high_risk content hash joins M8 bundle identity; verifier validates persisted hash; stale-reuse regression
f117227 calib corrective 1: per-factor argmin shifts (argmin_by_factor, max_abs_argmin_shift over non-baseline factors); calibration schema 1.3/manifest 1.4
74934ed integ: merge datafix corrective 1
a4a44e3 integ: merge calib corrective 1
```

The complete tree diff is bounded to the requested corrective surfaces:

```text
$ git diff --shortstat d3f4d64..a4a44e3
 9 files changed, 131 insertions(+), 22 deletions(-)
$ git diff --name-status d3f4d64..a4a44e3
M	docs/architecture.md
M	docs/scientific_scope.md
M	src/jersey_outbreak/calibration.py
M	src/jersey_outbreak/calibration_schemas.py
M	src/jersey_outbreak/travel.py
M	src/jersey_outbreak/travel_artifacts.py
M	tests/test_c3_contracts.py
M	tests/test_calibration.py
M	tests/test_scientific_corrections_datafix.py
```

`c0e9a74` changes only `travel.py`, `travel_artifacts.py`, and its datafix test (63 insertions, 2 deletions). `f117227` changes only `calibration.py`, `calibration_schemas.py`, two documentation files, and its two tests (68 insertions, 20 deletions). `travel_schemas.py` was already at manifest schema 2.3 and required no new hunk. `git diff --check d3f4d64..a4a44e3` produced no output. No new unscoped code was found; the disclosed state-layer ancestry issue was not re-raised.

## M1 — M8 immutable identity and stale reuse

Independent setup: each side regenerated CI M2/M3 parents with seed 123, generated M4 with seed 101, and ran `m8_arrival_testing.yaml` for 30 days with run seed 101. Base and head wrote into the same artifact root, so the head write directly exercised a root already holding the base schema-2.2 artifact.

Base `6eb05c2`, verbatim:

```text
{
  "artifact_bundle_hash": "a001296d96d19a40279944b141115d208008fb52a158cda59f4f9a618e83b1d4",
  "artifact_directory": "/tmp/jos-tail-m1-artifacts.L50NIc/jos-travel-m8-ci-seed-101-a001296d96d1",
  "artifact_id": "jos-travel-m8-ci-seed-101-a001296d96d1",
  "computed_detection_total": 2,
  "high_risk_epidemic_hash": null,
  "latent_outcome_hash": "68ce488367cec12459b3cd53cede5a6629288386abb4400a3723e02d460dba8d",
  "m4_logical_content_hash": "7b4f3ab765ede76749152f76b61dd2e40e415347bbf7a56607d04de610e7195d",
  "manifest_schema_version": "2.2",
  "persisted_detection_total": 2,
  "verified_artifact_id": "jos-travel-m8-ci-seed-101-a001296d96d1"
}
```

Head `a4a44e3`, verbatim:

```text
{
  "artifact_bundle_hash": "728456b30c21fbf9a097f16a0091f8a8375e00c8b09a4a57637e4bb9b9ffbfd7",
  "artifact_directory": "/tmp/jos-tail-m1-artifacts.L50NIc/jos-travel-m8-ci-seed-101-728456b30c21",
  "artifact_id": "jos-travel-m8-ci-seed-101-728456b30c21",
  "computed_detection_total": 3,
  "high_risk_epidemic_hash": "1a6cb8ead0c3418c30572200ca8a4c3708989ca6d550b844b6120ec4a9ed42f4",
  "latent_outcome_hash": "68ce488367cec12459b3cd53cede5a6629288386abb4400a3723e02d460dba8d",
  "m4_logical_content_hash": "7b4f3ab765ede76749152f76b61dd2e40e415347bbf7a56607d04de610e7195d",
  "manifest_schema_version": "2.3",
  "persisted_detection_total": 3,
  "verified_artifact_id": "jos-travel-m8-ci-seed-101-728456b30c21"
}
```

Result: artifact bundle hashes, IDs, and returned directories differ. The head write did not return the base directory. Head computed total equals persisted total at 3 and independently verifies under schema 2.3. M4 and latent hashes are unchanged. Inspection confirms that `high_risk_epidemic_hash` is now an input to `artifact_bundle_hash`, `daily_high_risk.parquet` is covered by persisted-file verification, and its recomputed logical hash must match diagnostics.

## M2 — per-factor beta argmin shifts

Independent real-model reproduction used the CI network, 8-day run, beta grid `(0.04, 0.08, 0.12)`, training seed 123, held-out seed 125, and nuisance factors `(0.5, 1.0)`. The written artifact diagnostics were read back before reporting.

```text
{
  "artifact_id": "jos-calibration-m6-tail-rereview-beta-97e914f3faa7",
  "ascertainment": {
    "argmin_by_factor": {
      "0.5": 0.12,
      "1.0": 0.08
    },
    "argmin_shift_by_factor": {
      "0.5": 0.039999999999999994,
      "1.0": 0.0
    },
    "argmin_shift_reference_beta": 0.08,
    "max_abs_argmin_shift": 0.039999999999999994
  },
  "best_parameters": {
    "transmission_beta": 0.08
  },
  "config_schema_version": "1.3",
  "duration_days": 8,
  "heldout_seeds": [
    125
  ],
  "manifest_schema_version": "1.4",
  "route_weights": {
    "argmin_by_factor": {
      "0.5": 0.12,
      "1.0": 0.08
    },
    "argmin_shift_by_factor": {
      "0.5": 0.039999999999999994,
      "1.0": 0.0
    },
    "argmin_shift_reference_beta": 0.08,
    "max_abs_argmin_shift": 0.039999999999999994
  },
  "top_level_argmin_shift": {
    "ascertainment": 0.039999999999999994,
    "route_weights": 0.039999999999999994
  }
}
```

Result: both per-factor argmins are `0.5 -> 0.12` and `1.0 -> 0.08`; both factor-0.5 shifts and both maximum-absolute shifts are nonzero at approximately 0.04. `argmin_by_factor`, `argmin_shift_by_factor`, and `max_abs_argmin_shift` are present and correct. Config schema 1.3 and manifest schema 1.4 are declared and persisted.

## Head gates

Full pytest, verbatim:

```text
$ env UV_CACHE_DIR=/tmp/uv-cache STARSIM_INSTALL_FONTS=0 MPLCONFIGDIR=/tmp/mpl-cache uv run pytest
=========================== short test summary info ============================
SKIPPED [1] tests/test_route4_weekday_memo.py:74: ROUTE-4 parent comparison tree is not present
SKIPPED [2] tests/test_route5_phase2_columns.py:100: phase-2 base comparison tree is not present
SKIPPED [1] tests/test_route_snapshot_columns.py:240: base comparison tree is not present
=========== 410 passed, 4 skipped, 15 warnings in 789.18s (0:13:09) ============
```

`test_missing_head_request_fails_alone_and_scheduler_continues` passed in the full run; no flake was disregarded.

Static gates, verbatim:

```text
$ env UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .
All checks passed!
$ env UV_CACHE_DIR=/tmp/uv-cache uv run ruff format --check .
247 files already formatted
$ env UV_CACHE_DIR=/tmp/uv-cache uv run mypy --ignore-missing-imports src/jersey_outbreak/population_structure_schemas.py src/jersey_outbreak/population_structure_controls.py src/jersey_outbreak/population_structure_artifacts.py src/jersey_outbreak/population_structure_generator.py src/jersey_outbreak/network_schemas.py src/jersey_outbreak/network_generator.py src/jersey_outbreak/network_artifacts.py src/jersey_outbreak/intervention_schemas.py src/jersey_outbreak/interventions.py src/jersey_outbreak/intervention_artifacts.py src/jersey_outbreak/intervention_analysis.py src/jersey_outbreak/scenario.py src/jersey_outbreak/staffing_evidence.py src/jersey_outbreak/staffing_generator.py src/jersey_outbreak/starsim_adapter.py
Success: no issues found in 15 source files
```

Final checkout state, verbatim:

```text
$ git status --short --branch
## HEAD (no branch)
```

No tracked repository file was modified, no commit or push was made, and no full/scaled run or ensemble was performed.
