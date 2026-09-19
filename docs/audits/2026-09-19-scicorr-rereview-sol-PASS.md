SCICORR RE-REVIEW: PASS

# Findings (ranked)

- MAJOR: none.
- MINOR: none.

The sole prior MAJOR is closed. Corrective 1 applies `m4_identity_edge()` at the persisted per-route snapshot-hash identity boundary, and its regression test proves that emitted `workplace_transient` metadata remains the truthful daily value (`1`) while the frozen identity representation remains `7`.

# Review boundary

Reviewed exact head `f1b2b6c1085e82bf7d59ac9df8c76b7c6fce0847`, whose parent is exact prior-reviewed head `aabb2be55c670ecc679eb14bf14e36736de12bca`.

Verbatim evidence:

```text
f1b2b6c1085e82bf7d59ac9df8c76b7c6fce0847 aabb2be55c670ecc679eb14bf14e36736de12bca scicorr corrective 1: route per-route M4 manifest hashes through m4_identity_edge
aabb2be55c670ecc679eb14bf14e36736de12bca ad7b1c68503c87094b69be787d7e635ace73b5dd scicorr: DISEASE-4 no fabricated incidence zeros (M6 schema 1.6) + ROUTE-6 truthful activity_cv declarations + ROUTE-7 truthful workplace persistence metadata
```

# 1. Full corrective diff

Command:

```text
git diff --stat aabb2be55c670ecc679eb14bf14e36736de12bca..f1b2b6c1085e82bf7d59ac9df8c76b7c6fce0847
git diff --name-status aabb2be55c670ecc679eb14bf14e36736de12bca..f1b2b6c1085e82bf7d59ac9df8c76b7c6fce0847
git diff --no-ext-diff --unified=3 aabb2be55c670ecc679eb14bf14e36736de12bca..f1b2b6c1085e82bf7d59ac9df8c76b7c6fce0847
git diff --check aabb2be55c670ecc679eb14bf14e36736de12bca..f1b2b6c1085e82bf7d59ac9df8c76b7c6fce0847
```

Verbatim stat and name-status:

```text
 src/jersey_outbreak/network_artifacts.py |  6 ++++-
 tests/test_m4_hash_stream.py             | 45 ++++++++++++++++++++++++++++++++
 2 files changed, 50 insertions(+), 1 deletion(-)
M	src/jersey_outbreak/network_artifacts.py
M	tests/test_m4_hash_stream.py
```

Verbatim full patch (three lines of context):

```diff
diff --git a/src/jersey_outbreak/network_artifacts.py b/src/jersey_outbreak/network_artifacts.py
index 219d824..2fef3f5 100644
--- a/src/jersey_outbreak/network_artifacts.py
+++ b/src/jersey_outbreak/network_artifacts.py
@@ -18,6 +18,7 @@ from .network_generator import GeneratedNetworks
 from .network_schemas import NetworkArtifactManifest
 from .population_artifacts import portable_artifact_path
 from .provenance import _git_metadata
+from .scientific_hashes import m4_identity_edge
 
 
 @dataclass(frozen=True)
@@ -284,7 +285,10 @@ def write_network_artifact(
                         "snapshots": [
                             {
                                 "date": when.isoformat(),
-                                "edges": list(generated.route_snapshot(route_id, when).edges),
+                                "edges": [
+                                    m4_identity_edge(route_id, edge)
+                                    for edge in generated.route_snapshot(route_id, when).edges
+                                ],
                             }
                             for when in generated.config.snapshot_dates
                         ],
diff --git a/tests/test_m4_hash_stream.py b/tests/test_m4_hash_stream.py
index 1c4f28d..d98eac3 100644
--- a/tests/test_m4_hash_stream.py
+++ b/tests/test_m4_hash_stream.py
@@ -10,6 +10,7 @@ from jersey_outbreak.hashing import (
     iter_canonical_json_chunks,
     sha256_bytes,
 )
+from jersey_outbreak.network_artifacts import write_network_artifact
 from jersey_outbreak.network_generator import generate_networks
 from jersey_outbreak.network_schemas import NetworkGenerationConfig
 from jersey_outbreak.population_artifacts import write_population_artifact
@@ -75,3 +76,47 @@ def test_m4_stream_hash_matches_golden_and_eager_payload() -> None:
         generated.logical_content_hash
         == fixture["generations"]["ci-seed-123"]["m4_logical_content_hash"]
     )
+
+
+def test_m4_artifact_route_hash_uses_identity_projected_snapshots() -> None:
+    with TemporaryDirectory() as directory:
+        output = Path(directory)
+        population = generate_population(ROOT, PopulationGenerationConfig(mode="ci", seed=123))
+        population_artifact = write_population_artifact(population, ROOT, output / "m2")
+        m2_input = load_m2_population_artifact(ROOT, population_artifact.artifact_directory)
+        structure = generate_structure(
+            ROOT, StructureGenerationConfig(mode="ci", seed=123), m2_input
+        )
+        structure_artifact = write_structure_artifact(structure, ROOT, output / "m3", m2_input)
+        m3_input = load_m3_structure_artifact(ROOT, structure_artifact.artifact_directory)
+        generated = generate_networks(
+            NetworkGenerationConfig(mode="ci", seed=123), m2_input, m3_input, ROOT
+        )
+        artifact = write_network_artifact(generated, ROOT, output / "m4")
+
+    route_id = "workplace_transient"
+    emitted_edges = [
+        edge
+        for when in generated.config.snapshot_dates
+        for edge in generated.route_snapshot(route_id, when).edges
+    ]
+    projected_edges = [m4_identity_edge(route_id, edge) for edge in emitted_edges]
+    assert emitted_edges
+    assert all(edge["persistence_days"] == 1 for edge in emitted_edges)
+    assert all(edge["persistence_days"] == 7 for edge in projected_edges)
+    expected_payload: dict[str, Any] = {
+        "spec": generated.route_specs[route_id],
+        "structural": generated.structural_edges[route_id],
+        "snapshots": [
+            {
+                "date": when.isoformat(),
+                "edges": [
+                    m4_identity_edge(route_id, edge)
+                    for edge in generated.route_snapshot(route_id, when).edges
+                ],
+            }
+            for when in generated.config.snapshot_dates
+        ],
+    }
+    expected_hash = sha256_bytes(canonical_json_bytes(expected_payload))
+    assert artifact.manifest.route_logical_hashes[route_id] == expected_hash
```

`git diff --check` produced no output and exited 0:

```text
DIFF_CHECK_EXIT=0
```

Conclusion: the range contains only the allowed identity-boundary fix and focused regression test.

# 2. Independent route-hash A/B

Method: exported exact source snapshots with `git archive` for base `08960b895ba5dfeaa547ee61c2842955d54ea825` and head `f1b2b6c1085e82bf7d59ac9df8c76b7c6fce0847`; in each snapshot independently generated M2, M3, and an M4 artifact using `mode="ci", seed=123`; serialized the M4 logical hash and sorted complete `route_logical_hashes`; asserted the complete JSON strings equal; then asserted the exact required `workplace_transient` value.

Verbatim evidence:

```text
BASE={"m4_logical_content_hash":"749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657","route_logical_hashes":{"bus":"7e7d2ba34d9260418bcd70beab553a74b13f22624cfbce6ca011273ec48d3581","care_resident":"be78717a7b39e58d3f54cf32375e7d078edade874211854bfc2af5f3497210d7","care_staff":"201830fffe6c21a7b2a5194e68f54e8cbe5fda7ed0796bedb822293cdec23a07","community_indoor":"5ffb5eaa04f111a652b99acc36a09e2a9ad73290801e1628ce97e792214dfbd2","community_outdoor":"df75bef60cba0031169f736d7809bc3421daf39da36dd8249bc90142c32773cb","household":"1e229d1a741f9a1b6ce1d0d0b56448bf21f30eeb354c412a504ba6dc3ef7fc12","school_class":"e18f0617905ab458bf776e650019adb088dd74ad4c4955f0e4774ba2399eb796","school_cross_class":"e72c3b0faff0b424803b88c1c66c09962f5c5389aa9d2037342331b6eca26975","shared_vehicle":"4f5a0a5639b947c38e1d03e563161c3edd95beae208b4ad809ed7a23a70d2bfc","workplace_team":"574ab2cca9d9d883321ca5f69fb39489a264f4d62095c39de53091de8ee4d154","workplace_transient":"7db644ed43a656b40c65a99f3e3e56145050dca5282a015cd161ac0139cdbd2b"}}
HEAD={"m4_logical_content_hash":"749e32383cbcfa5973cd2680e09b175267b12d72963cc286e6c4dd720ae53657","route_logical_hashes":{"bus":"7e7d2ba34d9260418bcd70beab553a74b13f22624cfbce6ca011273ec48d3581","care_resident":"be78717a7b39e58d3f54cf32375e7d078edade874211854bfc2af5f3497210d7","care_staff":"201830fffe6c21a7b2a5194e68f54e8cbe5fda7ed0796bedb822293cdec23a07","community_indoor":"5ffb5eaa04f111a652b99acc36a09e2a9ad73290801e1628ce97e792214dfbd2","community_outdoor":"df75bef60cba0031169f736d7809bc3421daf39da36dd8249bc90142c32773cb","household":"1e229d1a741f9a1b6ce1d0d0b56448bf21f30eeb354c412a504ba6dc3ef7fc12","school_class":"e18f0617905ab458bf776e650019adb088dd74ad4c4955f0e4774ba2399eb796","school_cross_class":"e72c3b0faff0b424803b88c1c66c09962f5c5389aa9d2037342331b6eca26975","shared_vehicle":"4f5a0a5639b947c38e1d03e563161c3edd95beae208b4ad809ed7a23a70d2bfc","workplace_team":"574ab2cca9d9d883321ca5f69fb39489a264f4d62095c39de53091de8ee4d154","workplace_transient":"7db644ed43a656b40c65a99f3e3e56145050dca5282a015cd161ac0139cdbd2b"}}
ALL_HASHES_IDENTICAL=PASS
WORKPLACE_TRANSIENT_EXPECTED=PASS
```

# 3. Requested tests and Ruff

Command:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_m4_hash_stream.py tests/test_networks.py tests/test_ensemble_band_horizon.py -q
```

Verbatim result:

```text
...............................                                          [100%]
31 passed in 19.60s
```

Command and verbatim result:

```text
$ UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .
All checks passed!
```

Command and verbatim result:

```text
$ UV_CACHE_DIR=/tmp/uv-cache uv run ruff format --check .
242 files already formatted
```

# Diff stat

```text
 src/jersey_outbreak/network_artifacts.py |  6 ++++-
 tests/test_m4_hash_stream.py             | 45 ++++++++++++++++++++++++++++++++
 2 files changed, 50 insertions(+), 1 deletion(-)
```

No full/scaled run was performed. Nothing was pushed or committed.
