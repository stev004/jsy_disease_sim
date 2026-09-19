SCICORR REVIEW: BLOCKED

# Independent review — `v121/scientific-corrections` @ `aabb2be55c670ecc679eb14bf14e36736de12bca`

## Findings

### MAJOR — the M4 identity shim does not cover the persisted per-route logical-hash path

`m4_identity_edge()` is correct for the aggregate `GeneratedNetworks.logical_content_hash`: it projects only `workplace_transient.persistence_days` back to the frozen legacy value 7, while runtime/emitted edges truthfully carry 1. The golden aggregate M4 hash and all three independently rerun replicate M4 hashes are genuinely preserved.

However, `src/jersey_outbreak/network_artifacts.py:278-295` independently computes the M4 manifest's `route_logical_hashes` directly from emitted snapshot edges and does not call `m4_identity_edge()`. The branch therefore changes `workplace_transient_route_logical_hash` while retaining the same aggregate M4 logical hash. This is an undeclared M4 sub-identity migration; the authority declares only the M6 1.5→1.6 migration, and the review obligation explicitly requires every M4 hash path to pass through the identity boundary.

Independent base/head artifact reproduction:

```text
$ PYTHONPATH=/tmp/jos-scicorr-base-review-safe/src ... /tmp/jos-review-venv/bin/python /tmp/jos_scicorr_routehash.py /tmp/jos-scicorr-base-review-safe /tmp/jos-scicorr-ab-base /tmp/jos-routehash-base
{"m4_logical_content_hash": "749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657", "workplace_transient_route_logical_hash": "7db644ed43a656b40c65a99f3e3e56145050dca5282a015cd161ac0139cdbd2b"}

$ PYTHONPATH=/tmp/jos-scicorr-review/src ... /tmp/jos-review-venv/bin/python /tmp/jos_scicorr_routehash.py /tmp/jos-scicorr-review /tmp/jos-scicorr-ab-head /tmp/jos-routehash-head
{"m4_logical_content_hash": "749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657", "workplace_transient_route_logical_hash": "234ab683672e63fc47dae78a2b9742088857623e38476629b628c256b9d843c7"}
```

Relevant head code:

```text
src/jersey_outbreak/network_artifacts.py:278-295
route_hashes = {
    route_id: sha256_bytes(
        canonical_json_bytes(
            {
                "spec": generated.route_specs[route_id],
                "structural": generated.structural_edges[route_id],
                "snapshots": [
                    {
                        "date": when.isoformat(),
                        "edges": list(generated.route_snapshot(route_id, when).edges),
                    }
                    for when in generated.config.snapshot_dates
                ],
            }
        )
    )
    for route_id in sorted(generated.route_specs)
}
```

This must be resolved deliberately: either all frozen M4 identity hashes must use the shim, or the per-route hash change must be explicitly declared/versioned as an M4 migration. No fix was made during this read-only review.

### MINOR

None.

## Checkout, ancestry, and scope

The authoritative rulings were read first. Target and ancestry check:

```text
$ git rev-parse HEAD
aabb2be55c670ecc679eb14bf14e36736de12bca
$ git rev-parse origin/main
ce35cd247300f7e46b4f923905075325f4f6e565
$ git merge-base --is-ancestor 08960b895ba5dfeaa547ee61c2842955d54ea825 HEAD; printf 'ancestor_exit=%s\n' "$?"
ancestor_exit=0
$ git rev-parse HEAD^
ad7b1c68503c87094b69be787d7e635ace73b5dd
$ git merge-base HEAD origin/main
ad7b1c68503c87094b69be787d7e635ace73b5dd
```

`origin/main` has advanced beyond the stated code baseline on a separate history line. The full branch diff was therefore reviewed with `git diff origin/main...HEAD`, whose merge base is `ad7b1c6`; the scientific A/B used the mandated code baseline `08960b8` directly.

```text
$ git diff --shortstat origin/main...HEAD
 13 files changed, 203 insertions(+), 46 deletions(-)
$ git diff --name-only origin/main...HEAD
benchmarks/ci-fingerprint-fixture.json
docs/architecture.md
docs/progress.md
docs/scientific_scope.md
src/jersey_outbreak/ensemble.py
src/jersey_outbreak/ensemble_schemas.py
src/jersey_outbreak/network_generator.py
src/jersey_outbreak/scientific_hashes.py
tests/test_c3_contracts.py
tests/test_c4_contracts.py
tests/test_ensemble_band_horizon.py
tests/test_m4_hash_stream.py
tests/test_networks.py
```

Every hunk traces to DISEASE-4, ROUTE-6, ROUTE-7, their documentation/tests, or the expected CI fingerprint update. No unrelated scope was found. No assertions were weakened: changed assertions encode the newly ruled incidence-horizon semantics, while the new regression separately retains an internal structural-zero assertion and adds null/non-contribution assertions for the tail.

```text
$ git diff --check origin/main...HEAD
[no output]
$ git status --porcelain=v1
[no output]
```

## Independent 3-seed, 30-day CI A/B

Both checkouts were run independently in CI mode for seeds 101, 102, and 103, duration 30 days, workers 1. Checkpoints and generated artifacts were confined to `/tmp`. The base checkout was a fresh shared clone at `08960b895ba5dfeaa547ee61c2842955d54ea825`; the head checkout was `aabb2be55c670ecc679eb14bf14e36736de12bca`.

Comparison of every scientific field in `replicate_records`:

```text
m4_seed123_equal True 749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657 749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657
seed 101 scientific_fields_equal True
  status passed passed True
  latent_run_logical_content_hash 106e5e4a4a7f520e8185d43c1f71eecec725d1cbffdbbc29e86b6f3b916cfc51 106e5e4a4a7f520e8185d43c1f71eecec725d1cbffdbbc29e86b6f3b916cfc51 True
  observation_logical_content_hash e3d4c092d9e3a58bd9bf539e4b6bc33178d6778dbfb13dae7365820183fd10e5 e3d4c092d9e3a58bd9bf539e4b6bc33178d6778dbfb13dae7365820183fd10e5 True
  m4_logical_content_hash 7b4f3ab765ede76749152f76b61dd2e40e415347bbf7a56607d04de610e7195d 7b4f3ab765ede76749152f76b61dd2e40e415347bbf7a56607d04de610e7195d True
  scenario_hash None None True
  intervention_config_hashes {} {} True
  error None None True
seed 102 scientific_fields_equal True
  status passed passed True
  latent_run_logical_content_hash 58dc87b6ae1c6f280447d2086d33d0ec3a8f69ce0672d22746645995c7233d4a 58dc87b6ae1c6f280447d2086d33d0ec3a8f69ce0672d22746645995c7233d4a True
  observation_logical_content_hash 0194d4cc12913c9bb62488a338c0c28d1c4bd5eacbc54503a6042c31d8ab7740 0194d4cc12913c9bb62488a338c0c28d1c4bd5eacbc54503a6042c31d8ab7740 True
  m4_logical_content_hash a278202093567dac775653f4c31669e98274cff0a66383b32a7741f1c8b4fbd4 a278202093567dac775653f4c31669e98274cff0a66383b32a7741f1c8b4fbd4 True
  scenario_hash None None True
  intervention_config_hashes {} {} True
  error None None True
seed 103 scientific_fields_equal True
  status passed passed True
  latent_run_logical_content_hash 3c94d4fa08aee9b1bdef072cd2c9cef0696894389f379f60db0e24222588f333 3c94d4fa08aee9b1bdef072cd2c9cef0696894389f379f60db0e24222588f333 True
  observation_logical_content_hash 3c7cdb7fa0af745a603f498fc765838bab19b6aa985db4913cec0be76157c28d 3c7cdb7fa0af745a603f498fc765838bab19b6aa985db4913cec0be76157c28d True
  m4_logical_content_hash ee73a9c11cc3943fbea83f81ff412e1607e554f5e8819e9e90ef463f7a298f5c ee73a9c11cc3943fbea83f81ff412e1607e554f5e8819e9e90ef463f7a298f5c True
  scenario_hash None None True
  intervention_config_hashes {} {} True
  error None None True
m6_equal False c20c7348628fee34149d47cbee6d3b9c207e1b05c17f69c14afe4897cf6b353a f998e868f634225b5dbb85af548134aec8c8fb9b926eb30c8f0fa6bd68eefbc4
```

Thus the decisive replicate-level invariant passes: latent, aggregate M4, and observation identities are unchanged for all three seeds. The M6 identity changes as expected from the corrected grid/summary content and is declared by manifest schema 1.6.

## ROUTE-6 RNG neutrality and snapshot comparison

At `activity_cv=0.5`, base versus head snapshot comparison produced:

```text
community_indoor 2025-01-06 full_equal True projected_equal True base_n 5414 head_n 5414 diff_keys []
community_indoor 2025-01-11 full_equal True projected_equal True base_n 5776 head_n 5776 diff_keys []
community_indoor 2025-08-11 full_equal True projected_equal True base_n 5376 head_n 5376 diff_keys []
community_outdoor 2025-01-06 full_equal True projected_equal True base_n 2038 head_n 2038 diff_keys []
community_outdoor 2025-01-11 full_equal True projected_equal True base_n 2805 head_n 2805 diff_keys []
community_outdoor 2025-08-11 full_equal True projected_equal True base_n 2040 head_n 2040 diff_keys []
school_cross_class 2025-01-06 full_equal True projected_equal True base_n 270 head_n 270 diff_keys []
school_cross_class 2025-01-11 full_equal True projected_equal True base_n 0 head_n 0 diff_keys []
school_cross_class 2025-08-11 full_equal True projected_equal True base_n 0 head_n 0 diff_keys []
workplace_transient 2025-01-06 full_equal False projected_equal True base_n 2797 head_n 2797 diff_keys ['persistence_days']
workplace_transient 2025-01-11 full_equal True projected_equal True base_n 0 head_n 0 diff_keys []
workplace_transient 2025-08-11 full_equal False projected_equal True base_n 2756 head_n 2756 diff_keys ['persistence_days']
```

The removed calls did perform hash-keyed `_stable_int` calculations and local `random.Random(...).gammavariate(...)` calculations at nonzero CV, but no mutable/shared RNG stream exists: `stable_int()` is a pure SHA-256 mapping and each gamma generator is locally seeded from that stable key. Removing the inert calls therefore cannot advance or perturb community-route randomness. The A/B confirms both community routes are unchanged. School-cross-class is unchanged; workplace-transient endpoints/weights are unchanged and differs only by the separately ruled truthful `persistence_days` 7→1 metadata correction.

## DISEASE-4 semantics

The implementation emits a structural zero only when `first_observed_date <= date <= last_observed_date`; outside that interval it leaves `value=None`, `contributes=False`, and uses `outside_metric_horizon`.

The head regression executed against base fails at the fabricated tail zero:

```text
$ ... uv run --project /tmp/jos-scicorr-base-review-safe pytest -q /tmp/jos-scicorr-review/tests/test_ensemble_band_horizon.py
F                                                                        [100%]
=================================== FAILURES ===================================
____________ test_ci_incidence_band_does_not_fabricate_tail_zeroes _____________
...
>       assert short_tail["value"] is None
E       assert 0.0 is None

../jos-scicorr-review/tests/test_ensemble_band_horizon.py:67: AssertionError
=========================== short test summary info ============================
FAILED ../jos-scicorr-review/tests/test_ensemble_band_horizon.py::test_ci_incidence_band_does_not_fabricate_tail_zeroes
1 failed in 0.43s
```

The same regression passes at head:

```text
$ ... uv run --project /tmp/jos-scicorr-review pytest -q tests/test_ensemble_band_horizon.py
.                                                                        [100%]
1 passed in 0.07s
```

## Fingerprint fixture

The fixture diff changes exactly two `workplace_transient` dictionary fingerprints:

```text
2025-01-06: 3365797b03d5551e43685adfd62f34ac9cb005a1f484110f8841dfc6d2650649
         -> 9e2609ca0fec820ccfac8c62786acca3b5204fdd4a87e0b08aa84c42797e8227
2025-01-07: 89b9e1ef47b19b09815c3046e6a8c2b934c7299938cd1f6e19e0475b6e4eb27b
         -> ed9045a2a01c1e0ea9e801736f9be7702fad8d0037a586e7cfa90ab4b53cfceb
```

For both days, `array_fingerprint`, `n_edges`, `stable_int_calls`, and all other fixture fields are unchanged. The dictionary fingerprint hashes every edge field and therefore changes solely because emitted `persistence_days` is now 1; the Starsim adapter array fingerprint is unchanged because Starsim already received daily `dur=1`. The full-suite `test_ci_fixture_round_trip` passed.

## Gates

Ruff and formatting:

```text
$ uv run --no-sync ruff check . && uv run --no-sync ruff format --check .
All checks passed!
242 files already formatted
```

Pinned workflow mypy module list:

```text
$ uv run --no-sync mypy --ignore-missing-imports [15 workflow-pinned modules]
Success: no issues found in 15 source files
```

Full head pytest:

```text
$ uv run --no-sync pytest
=========================== short test summary info ============================
SKIPPED [1] tests/test_route4_weekday_memo.py:74: ROUTE-4 parent comparison tree is not present
SKIPPED [2] tests/test_route5_phase2_columns.py:100: phase-2 base comparison tree is not present
SKIPPED [1] tests/test_route_snapshot_columns.py:240: base comparison tree is not present
FAILED tests/test_prov_job_ordering.py::test_missing_head_request_fails_alone_and_scheduler_continues
====== 1 failed, 394 passed, 4 skipped, 9 warnings in 2638.69s (0:43:58) =======
```

The failure is exactly the disclosed pre-existing timing race: the second job was still `RUNNING` at the five-second deadline. Exact baseline reproduction:

```text
$ PYTHONPATH=/tmp/jos-scicorr-base-review-safe/src ... python -m pytest -q tests/test_prov_job_ordering.py::test_missing_head_request_fails_alone_and_scheduler_continues
F                                                                        [100%]
...
>           assert second_job["state"] == "SUCCEEDED", second_job
E           AssertionError: {'bundle_hash': None, 'canonical_request': {'request': {'duration_days': 1, 'kind': 'scenario_run', 'mode': 'ci', 'obs....13', 'starsim_version': '3.5.2'}}, 'created_at': '2026-09-19T18:26:37.700107+00:00', 'dirty_worktree_flag': None, ...}
E           assert 'RUNNING' == 'SUCCEEDED'
E
E             - SUCCEEDED
E             + RUNNING

tests/test_prov_job_ordering.py:176: AssertionError
=========================== short test summary info ============================
FAILED tests/test_prov_job_ordering.py::test_missing_head_request_fails_alone_and_scheduler_continues
1 failed in 5.59s
```

Per the review brief, that base-reproduced flake is disregarded and is not a finding against this branch.

## Review hygiene

No source, test, documentation, frozen data, evidence directory, git ref, or primary checkout was modified. No full/180-day epidemic or 30-replicate ensemble was run. Temporary review scripts, checkouts, checkpoints, and generated CI artifacts were confined to `/tmp`. Final target worktree status was clean.
