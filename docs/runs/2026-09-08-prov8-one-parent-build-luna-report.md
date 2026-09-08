Implemented PROV-8 without committing.

Base recorded:

- Task-start `origin/main`: `b81c65f7dfd1038967194930d5df74c682f876dd`
- Task-start merge-base: `bb66159fe1c0ddde52976a2778bb90845092a98c`
- HEAD: `e26ef918ae09509cf9959af9aaa3f522e825ea56`

Added [`parent_build.py`](/home/steven/jos-prov8-wt/src/jersey_outbreak/parent_build.py:84), centralizing:

- M2 generation/write/reload
- M3 generation/write/reload
- M4 generation, optional artifact writing, custom output paths
- standalone M2/M3/M4 stage wrappers
- internal ensemble diagnostics mode

Updated call sites in `cli.py`, `execution_adapter.py`, `ensemble.py`, and `calibration.py`. No changes to generators, schemas, writers, hashing, data, or scenario normalization.

Inventory included:

| Original site | Replacement |
|---|---|
| `cli.py:155-178` M6 parent | `build_parent(...).generated` |
| `cli.py:221` population CLI | `build_population` |
| `cli.py:264-273` structure CLI | `build_structure` |
| `cli.py:325-355` network CLI | `build_parent(..., write_m4=True, m4_output=destination)` |
| `cli.py:407-418` outbreak CLI | `build_parent(..., write_m4=True)` |
| `execution_adapter.py:98-118` API worker parent | `build_parent(..., write_m4=True)` |
| `ensemble.py:322` replicate M4 regeneration | `build_network(..., diagnostics="internal")` |
| `calibration.py:192-197, 288-293` seeded M4 regeneration | `build_network` |

`api.py`, `travel.py`, `bundle_selftest.py`, and `job_worker.py` contained no duplicate parent-build sequence.

Verification:

- Targeted regressions: 61 passed.
- Full suite: **335 passed**, 5 warnings.
- Base/branch CI hashes identical:
  - M2: `28a6d90a...`
  - M3: `f072042f...`
  - M4: `749e3238...`
  - Ensemble: `87b4d54c...`
- Ensemble replicate latent, observation, and M4 hashes matched for seeds 123/124.
- Demo deterministic summary matched.
- Ruff, format, mypy, lock check, compileall, relocation check, and `git diff --check` passed.
- Direct generator calls remain only in `parent_build.py`, generator implementations, artifact type imports, and the existing ensemble monkeypatch compatibility alias.

Line count: 129 duplicated call-site lines removed versus 128 lines added in `parent_build.py`.

Final status:

```text
 M src/jersey_outbreak/calibration.py
 M src/jersey_outbreak/cli.py
 M src/jersey_outbreak/ensemble.py
 M src/jersey_outbreak/execution_adapter.py
?? src/jersey_outbreak/parent_build.py
```