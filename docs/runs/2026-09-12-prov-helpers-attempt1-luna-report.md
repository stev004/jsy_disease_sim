REPORT

Implemented PROV-5 and PROV-11. PROV-1 confirmed: git provenance fields are not included in M6 logical-hash payloads.

Files changed:

- `provenance.py`: single fail-closed Git helper; unknown/failure returns `(None, True)`.
- 15 provenance call sites: `api.py`, `bundle_selftest.py`, `calibration_artifacts.py`, `demo.py`, `ensemble.py`, `ensemble_artifacts.py`, `execution_adapter.py`, `intervention_artifacts.py`, `network_artifacts.py`, `observation_artifacts.py`, `outbreak_artifacts.py`, `population_artifacts.py`, `population_structure_artifacts.py`, `travel_artifacts.py`, `verification_archive.py`.
- `travel.py`, `outbreak_runner.py`: removed unused duplicate helpers.
- `scientific_hashes.py`: shared typed metric normalizer; unregistered metrics raise.
- `ensemble.py`: explicit `METRIC_TYPES` registry aligned with `METRIC_SEMANTICS`.
- `cli.py`: repository root resolved from package location.
- `demo.py`: typed existing config construction to satisfy required mypy coverage.
- `tests/test_prov_helpers.py`: provenance, CLI relocation, registry equality, unknown metric, and float-preservation tests.

Acceptance evidence:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_prov_helpers.py -q
.......                                                                  [100%]
7 passed in 0.84s
```

```text
rg -n "^def _git|git rev-parse|git status --porcelain" src/jersey_outbreak --glob '*.py'
src/jersey_outbreak/provenance.py:9:def _git_metadata(root: Path) -> tuple[str | None, bool]:
```

A/B logical hashes, base `0bfc3c6` vs branch:

```text
population   "logical_content_hash": "28a6d90a96454d11dcd6ad9d4531d69f9e4ec4396b802780084d3ae598c839a0",    "logical_content_hash": "28a6d90a96454d11dcd6ad9d4531d69f9e4ec4396b802084d3ae598c839a0",
structure    "logical_content_hash": "f072042f07db46a94fd61781eb9ee99545a6dc169d34b83d6de21ffdf56e3ce3",    "logical_content_hash": "f072042f07db46a94fd61781eb9ee99545a6dc169d34b83d6de21ffdf56e3ce3",
network      "logical_content_hash": "749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657",    "logical_content_hash": "749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657",
ensemble     "logical_content_hash": "2da15bd30fe2d00f50db6bfa6fecccc1ab078b831957f7e04431f27783470d7c",    "logical_content_hash": "2da15bd30fe2d00f50db6bfa6fecccc1ab078b831957f7e04431f27783470d7c",
```

Full suite:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run pytest
================= 371 passed, 8 warnings in 892.65s (0:14:52) ==================
```

CI mirror:

```text
uv lock --check
Resolved 77 packages in 0.71ms

uv run python -m compileall -q src
[no output; exit 0]

uv run ruff check .
All checks passed!

uv run ruff format --check .
222 files already formatted

uv run mypy --ignore-missing-imports [CI module list plus all touched modules]
Success: no issues found in 31 source files

git diff --check
[no output; exit 0]
```

Relocation check passed:

```text
{"artifact_directory": "/home/steven/jos-phelp-wt/outputs/interventions/jos-intervention-m7-ci-seed-123-c0be3d419f32", "artifact_id": "jos-intervention-m7-ci-seed-123-c0be3d419f32", "diagnostics_status": "passed", "logical_content_hash": "1e9f01ed1d770bbeb592c3d0c69add44040d2e80339b93b884b24701f4ed8a99", "runtime_seconds": 3.317647434999799, "scenario_hash": "7158b33cb7eba93112b1326aacc253d19136a4a85f70c7c4245113a26478665a", "scenario_id": "m7-baseline", "travel_controls": "DEFERRED TO M8"}
verifier success: m7_intervention jos-intervention-m7-ci-seed-123-c0be3d419f32
```

`git status --short`:

```text
 M src/jersey_outbreak/api.py
 M src/jersey_outbreak/bundle_selftest.py
 M src/jersey_outbreak/calibration_artifacts.py
 M src/jersey_outbreak/cli.py
 M src/jersey_outbreak/demo.py
 M src/jersey_outbreak/ensemble.py
 M src/jersey_outbreak/ensemble_artifacts.py
 M src/jersey_outbreak/execution_adapter.py
 M src/jersey_outbreak/intervention_artifacts.py
 M src/jersey_outbreak/network_artifacts.py
 M src/jersey_outbreak/observation_artifacts.py
 M src/jersey_outbreak/outbreak_artifacts.py
 M src/jersey_outbreak/outbreak_runner.py
 M src/jersey_outbreak/population_artifacts.py
 M src/jersey_outbreak/population_structure_artifacts.py
 M src/jersey_outbreak/scientific_hashes.py
 M src/jersey_outbreak/travel.py
 M src/jersey_outbreak/travel_artifacts.py
 M src/jersey_outbreak/verification_archive.py
?? src/jersey_outbreak/provenance.py
?? tests/test_prov_helpers.py
```

`git diff --stat`:

```text
19 files changed, 87 insertions(+), 398 deletions(-)
```

No golden fixtures, dependencies, generators, route/snapshot logic, job layer, or commits were changed.