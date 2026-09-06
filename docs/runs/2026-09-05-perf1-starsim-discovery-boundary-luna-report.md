<!-- DIRECTOR ERRATUM 2026-09-06 (trail-audit Attention 4): the proof JSON embedded below is an intermediate bench pass; its ci:101:7 observed_hash 70d54219... differs from the filed authoritative proof docs/runs/2026-09-05-perf1-proof.json (70e537b3...). Director probe on perf/integration-tranche2b @ 0dec469: two consecutive ci seed-101 7-day runs -> observed 70e537b3dc495a1674edc34386d48fc8f1fa87f99e68471e7e2257a27bc18f5f both times (latent 46d4e82c..., outcome ddcd298e..., 90 events), equal to the proof file. Trail row trail-audit-errata. -->
Implemented PERF-1.

Design: `PlainMetadataBoundary` stores mappings in a closure behind a `__slots__` callable. sciris’s `check_iter_type()` descends into `__dict__`/`__slots__` objects (`sc_nested.py:149–156`) and `iteritems()` enumerates slots (`:490–504`), but does not inspect callable closure cells. Consumers access mappings through `.value` or scheduler properties.

Changed:

- [starsim_adapter.py](/home/steven/jos-perf1-wt/src/jersey_outbreak/starsim_adapter.py:18): boundary class; dynamic networks wrap `_uid_by_agent_id`; `_replace_edges()` unwraps it.
- [observation_scheduler.py](/home/steven/jos-perf1-wt/src/jersey_outbreak/observation_scheduler.py:144): scheduler metadata wrapped while preserving public lookup properties.
- Added [test_init_metadata_boundary.py](/home/steven/jos-perf1-wt/tests/test_init_metadata_boundary.py).
- Added [bench_init_metadata_boundary.py](/home/steven/jos-perf1-wt/scripts/bench_init_metadata_boundary.py).

Evidence:

- Exact acceptance batch: `122 passed, 1 warning in 474.23s`.
- Full suite: `307 passed, 5 warnings in 538.83s`.
- Mypy: `Success: no issues found in 15 source files`.
- Ruff, format, lock, compileall, demo, and `git diff --check`: passed.
- Forbidden monkeypatch grep: no output.
- Boundary test confirms a 104,540-entry mapping containing an actual `ss.Dist` is undiscovered in under 10 ms.
- Required seed-101/full/30 hashes match exactly.
- Hard-gate booleans: all `true`.
- Soft timing: init `1.067s` (pass); 30-day `73.193s` (target missed by ~3.2s in this environment).

Proof JSON:

```json
{
  "all_route_and_array_fingerprints_equal": true,
  "all_scientific_hashes_equal": true,
  "base_sha": "a3caccf2d37d2462880e6ae349f042d4d9893501",
  "cases": {
    "ci:101:30": {
      "event_count": 2236,
      "event_sha256": "dc5d2770ac38e08350290cc7783c845bd1b82e0f23c418e3e1aa12b51759a986",
      "latent_hash": "e243fee31ff77ed6f78bb5f7980a68c1178acc5880792cea9ce88665e3fdd19e",
      "latent_outcome_hash": "954c3b63f443d7f5b51a2b3a0422b7734ab351e681c00223a1d8f5a048e9dc2a",
      "network_hash": "601b44baaf4f48109da03f8ccc9992e8e0a2903861e27bf3d40b8c96e00bbef2",
      "observed_hash": "87d54219b2dfd09eeb34b76941a20bf90a359d39bd00f34ed6d00d35c6bfe6da"
    },
    "ci:101:7": {
      "event_count": 90,
      "event_sha256": "0b1cbfe8addc4b92b01d38aab6001f69f83fc2775fdbd0e787ba466a5ecb8925",
      "latent_hash": "46d4e82c60a9b3ee64107ab838f02443fa0ad629b53aca21a4b141ef1d0ae990",
      "latent_outcome_hash": "ddcd298e5c64689a839979b3f565544c2a30c7886142450e3f61dee5efbc0008",
      "network_hash": "601b44baaf4f48109da03f8ccc9992e8e0a2903861e27bf3d40b8c96e00bbef2",
      "observed_hash": "70d54219bd495a1674edc34386d48fc8f1fa87f99e68471e7e2257a27bc18f5f"
    },
    "ci:123:30": {
      "event_count": 2147,
      "event_sha256": "95121741d8a62d5134b6c7f2e8582056944dfc8b6eeebcfa624336b0bfe984cc",
      "latent_hash": "1e9f01ed1d770bbeb592c3d0c69add44040d2e80339b93b884b24701f4ed8a99",
      "latent_outcome_hash": "a9b1f9713505efecdc2b408d4c959e40545111cac8f9c2004aabaf994ea8f168",
      "network_hash": "749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657",
      "observed_hash": "65cec1b32085a3185b6ff10f39349d6f00f90fa8913dbbd10f80c74b0cfa6609"
    },
    "ci:123:7": {
      "event_count": 53,
      "event_sha256": "5ea4bb6837a17e5439a3728cc18dc930e433a19798af96ab120ba6b1d3278a82",
      "latent_hash": "9c3e7f998ea8642899419686023db79f2f6d77b32134e865937db89d7f108ab2",
      "latent_outcome_hash": "05b916a4880f50bebf0aa3528edf0ec7fc08203b6f8b84f477992c505b08149f",
      "network_hash": "749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657",
      "observed_hash": "ceebf2291574a30aef02ed980b8be122d20974ef0ed87f01cfcd6d9a4eefa8c3"
    },
    "full:101:30": {
      "event_count": 42760,
      "event_sha256": "812210751ba3cdae6ca789aed8bdf2457b729fb1c17db961b68323fdccd9d861",
      "latent_hash": "bbca602849da80aa04bd2c3bb770d3d5c4486f007d0e14666df4c5087a6e8c81",
      "latent_outcome_hash": "b8433f0d9240d81aff5526eb223e024fbc184d7fd99ca55f408e8750dd69d66a",
      "network_hash": "49464e77ac5754a114dadcf73b2e79e3bf94607d1d192a4f48229891e7d5b0bd",
      "observed_hash": "03778389a32bc04c5c9b50b6a0be487a5c659ba5f108ce6ef7b12f8eee280798"
    },
    "full:101:7": {
      "event_count": 65,
      "event_sha256": "93de520a5870fec9449a7a05a47e47b3081bf6c526f123b15cddace3b575cfd6",
      "latent_hash": "2425986db799d2b68b57b16b3726bec753135a716237e2b1ffe78d553da1ed8c",
      "latent_outcome_hash": "f3c51be00168263c3a31dddc35157645f1912a56a4840e7804d30e543838e8ac",
      "network_hash": "49464e77ac5754a114dadcf73b2e79e3bf94607d1d192a4f48229891e7d5b0bd",
      "observed_hash": "9400c0229e7478bacd26979fc2a651a5cc7d6e7e4a01adc3cec52fa91bf14742"
    },
    "full:123:30": {
      "event_count": 49418,
      "event_sha256": "0da8471f8bedf4aa67648b3d0f1f7771bb444d9531317112d7dba0e4e423f2c1",
      "latent_hash": "3be1bf60ddd72f0acf05db0c025e87e730b08a937790a06c2e3034f6f7839285",
      "latent_outcome_hash": "f9ac1f20f77ac4b1d22432d3586b430359aee6f8d865b3e1f681e656390398a8",
      "network_hash": "425924a480b2f9035ac059128e87509c26d489a80b64740a5dc284b05b64079c",
      "observed_hash": "d7f0cfd617f87381f7e773bba36bc0756d600a2889b930f23efd4b3b45b32a7c"
    },
    "full:123:7": {
      "event_count": 59,
      "event_sha256": "0469a24d1a2090f55bf628cd3a8c808a1fd2a740a734f26e37345fa25515dbd4",
      "latent_hash": "487a9a76907c4cb69a21d8bf43471b4268960d1ce54ea5db30a2953d8b5e9d45",
      "latent_outcome_hash": "bd5f0fe1c6cb3eba3c39ea794d634bc85ac25311c7a1023797f9c4b70ae9c1de",
      "network_hash": "425924a480b2f9035ac059128e87509c26d489a80b64740a5dc284b05b64079c",
      "observed_hash": "9c7bca92b197a6fe988e61caa5c3ce860f84d398ffdd782377019bd78d6a20a3"
    }
  },
  "distribution_seeds_and_rng_states_equal": true,
  "full_online_30d_median_s": 73.19256941000009,
  "full_online_7d_median_s": 14.066117978500017,
  "full_online_init_median_s": 1.067442025499986,
  "initialized_arrays_bit_equal": true,
  "lifecycle_and_consumer_order_equal": true,
  "ordered_distribution_and_rate_paths_equal": true,
  "route_test_exit_code": 0
}
```

Final status:

```text
 M src/jersey_outbreak/observation_scheduler.py
 M src/jersey_outbreak/starsim_adapter.py
?? scripts/bench_init_metadata_boundary.py
?? tests/test_init_metadata_boundary.py
```

No commit made.