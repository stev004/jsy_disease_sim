**Verdict: STOPPED at seed 42001, classified DIFFERENT.** Its M2 and M3 artifact IDs and directories match the base, and its Parquet files are byte-identical. After the permitted normalization, both manifests still differ in `created_at` and `dirty_worktree_flag`. The explicit stop rule means I did not continue the sweep or run the requested tests.

There is also a problem with the corrected criterion: a seed-123 base-vs-base double build still differs in manifest fields the criterion does not allow removing. The M2 manifest’s `created_at` and three `output_artifacts[*].size_bytes` values differ; M3’s `created_at` and `m2_manifest_hash` differ. Removing the permitted timing, memory, and digest fields therefore does not make that base-vs-base pair equal. I left those unlisted fields intact in the seed-42001 comparison.

**Normalization and base-vs-base evidence.** The fields I removed for comparison were:

- `benchmark.json`: `runtime_seconds` and `peak_memory_bytes`; `diagnostics.json`: `benchmark.runtime_seconds` and `benchmark.peak_memory_bytes`; `diagnostics.md`: lines 9–10, the Runtime seconds and Peak resident memory bytes lines. Each differs in the seed-123 base double build at both M2 and M3.
- `manifest.json`: top-level `runtime_seconds` and `peak_memory_bytes`; `output_artifacts[*].sha256` entries only for `diagnostics.json`, `diagnostics.md`, and `benchmark.json`; and M3’s `m2_manifest_hash`. The digest values differ in the seed-123 base double build. I did not remove `size_bytes`, `created_at`, or any other manifest fields.

**Sweep status:** IDENTICAL 0, FALLBACK 0, BOTH-FAIL 0, DIFFERENT 1. The only classified seed is 42001; all later seeds were left unrun after the stop condition.

The four fallback disclosures remain from attempt 1; this retry stopped before rebuilding them: 62001 Trinity, 11 deferred `other` roles; 62002 St Peter, 3; 62003 Trinity, 8; 63002 Trinity, 7. Attempt 1 reported passed builds for all four.

`tests/test_golden_hashes.py`, the new end-to-end test, and the full suite were **not run** in this retry. Formatting, Ruff check, and mypy had passed on these unchanged files in attempt 1. `git diff --check` passed this turn.

The base clone is at the required HEAD `024caa09c19bbdad0952b09213ed56e6638ad676` and is clean. The worktree HEAD is unchanged; its only changes are the requested population generator and new test. Diff stat: 131 insertions and 42 deletions in the generator, plus the 21-line untracked test. Evidence is in `/tmp/jos-popfix2-evidence.log`; the partial table is `/tmp/jos-popfix2-identity.tsv`.

**Full diff of `population_generator.py`:**

```diff
diff --git a/src/jersey_outbreak/population_generator.py b/src/jersey_outbreak/population_generator.py
index d81287b..0434261 100644
--- a/src/jersey_outbreak/population_generator.py
+++ b/src/jersey_outbreak/population_generator.py
@@ -6,6 +6,7 @@ import math
 import resource
 import time
 from collections.abc import Callable
+from copy import deepcopy
 from dataclasses import dataclass
 from typing import Any
 
@@ -509,7 +510,11 @@ def _draw_non_pensioner_role(
 
 
 def _assign_household_ages(
-    household: dict[str, Any], remaining: dict[tuple[int, str], int], rng: np.random.Generator
+    household: dict[str, Any],
+    remaining: dict[tuple[int, str], int],
+    rng: np.random.Generator,
+    *,
+    defer_other: bool = False,
 ) -> list[tuple[str, tuple[int, str]]]:
     """Assign one household as a relational unit, not as independent role draws."""
 
@@ -577,7 +582,9 @@ def _assign_household_ages(
                     household["_role_relaxations"] = household.get("_role_relaxations", 0) + len(
                         children
                     )
-                    return _assign_household_ages(household, remaining, rng)
+                    return _assign_household_ages(
+                        household, remaining, rng, defer_other=defer_other
+                    )
                 raise DataBuildError("could not form a parent couple for child roles")
             left, right = pair
             remaining[left] -= 1
@@ -613,7 +620,9 @@ def _assign_household_ages(
                     household["_role_relaxations"] = household.get("_role_relaxations", 0) + len(
                         children
                     )
-                    return _assign_household_ages(household, remaining, rng)
+                    return _assign_household_ages(
+                        household, remaining, rng, defer_other=defer_other
+                    )
                 raise DataBuildError("could not form a parent for child roles")
             remaining[chosen_parent] -= 1
             assigned.append((parent_roles[0], chosen_parent))
@@ -657,7 +666,7 @@ def _assign_household_ages(
         assigned.append((role, value))
 
     for role in roles:
-        if role in children or role in parent_roles:
+        if role in children or role in parent_roles or (defer_other and role == "other"):
             continue
         minimum_age, maximum_age = _role_age_bounds(role)
         assigned.append(
@@ -666,7 +675,8 @@ def _assign_household_ages(
                 _draw_age_sex(remaining, rng, minimum_age=minimum_age, maximum_age=maximum_age),
             )
         )
-    if len(assigned) != len(roles):
+    expected_assignments = len(roles) - (roles.count("other") if defer_other else 0)
+    if len(assigned) != expected_assignments:
         raise DataBuildError("household age assignment did not consume every role")
     return assigned
 
@@ -675,53 +685,123 @@ def _assign_private_residents(
     households: list[dict[str, Any]],
     private_counts_by_parish: dict[str, dict[tuple[int, str], int]],
     rng: np.random.Generator,
-) -> list[dict[str, Any]]:
+) -> tuple[list[dict[str, Any]], dict[str, int]]:
     residents: list[dict[str, Any]] = []
+    fallback_parishes: dict[str, int] = {}
+
+    def append_residents(
+        parish: str,
+        household: dict[str, Any],
+        assigned: list[tuple[str, tuple[int, str]]],
+    ) -> None:
+        for role, (age, sex) in assigned:
+            residents.append(
+                {
+                    "agent_id": "",
+                    "age": age,
+                    "sex": sex,
+                    "home_parish": parish,
+                    "household_id": household["household_id"],
+                    "household_role": role,
+                    "dwelling_type": household["dwelling_type"],
+                    "crowding_band": household["crowding_band"],
+                    "car_access": household["car_access"],
+                    "care_setting_id": None,
+                }
+            )
+
     for parish in sorted(private_counts_by_parish):
         remaining = private_counts_by_parish[parish]
         parish_households = [row for row in households if row["home_parish"] == parish]
+        rng_state = deepcopy(rng.bit_generator.state)
+        remaining_snapshot = dict(remaining)
+        household_snapshots = [
+            (
+                household,
+                list(household["_roles"]),
+                "_role_relaxations" in household,
+                household.get("_role_relaxations"),
+            )
+            for household in parish_households
+        ]
+        residents_length = len(residents)
         ordered = list(parish_households)
-        rng.shuffle(ordered)
-        # Couple-with-children and other constrained households get first-class
-        # relational assignment; unconstrained households follow.
-        ordered.sort(
-            key=lambda row: (
-                not any(role == "pensioner" for role in row["_roles"]),
-                not any(role == "dependent_child" for role in row["_roles"]),
-                not any(role in {"dependent_child", "adult_child"} for role in row["_roles"]),
-                "partner" not in row["_roles"],
-                row["household_id"],
+        try:
+            rng.shuffle(ordered)
+            # Couple-with-children and other constrained households get first-class
+            # relational assignment; unconstrained households follow.
+            ordered.sort(
+                key=lambda row: (
+                    not any(role == "pensioner" for role in row["_roles"]),
+                    not any(role == "dependent_child" for role in row["_roles"]),
+                    not any(role in {"dependent_child", "adult_child"} for role in row["_roles"]),
+                    "partner" not in row["_roles"],
+                    row["household_id"],
+                )
             )
-        )
-        for household in ordered:
+            for household in ordered:
+                try:
+                    assigned = _assign_household_ages(household, remaining, rng)
+                except DataBuildError as exc:
+                    raise DataBuildError(
+                        f"{exc} in parish {parish}, household {household['household_id']} "
+                        f"({household['household_type']}, roles={household['_roles']})"
+                    ) from exc
+                append_residents(parish, household, assigned)
+            if any(count != 0 for count in remaining.values()):
+                raise DataBuildError(f"private resident age/sex pool was not consumed in {parish}")
+        except DataBuildError as original_exc:
+            rng.bit_generator.state = deepcopy(rng_state)
+            remaining.clear()
+            remaining.update(remaining_snapshot)
+            for household, roles, had_relaxations, relaxations in household_snapshots:
+                household["_roles"] = list(roles)
+                if had_relaxations:
+                    household["_role_relaxations"] = relaxations
+                else:
+                    household.pop("_role_relaxations", None)
+            del residents[residents_length:]
+
             try:
-                assigned = _assign_household_ages(household, remaining, rng)
-            except DataBuildError as exc:
+                for household in ordered:
+                    try:
+                        assigned = _assign_household_ages(
+                            household, remaining, rng, defer_other=True
+                        )
+                    except DataBuildError as exc:
+                        raise DataBuildError(
+                            f"{exc} in parish {parish}, household {household['household_id']} "
+                            f"({household['household_type']}, roles={household['_roles']})"
+                        ) from exc
+                    append_residents(parish, household, assigned)
+                deferred_other_roles = 0
+                for household in ordered:
+                    minimum_age, maximum_age = _role_age_bounds("other")
+                    for role in household["_roles"]:
+                        if role != "other":
+                            continue
+                        age, sex = _draw_age_sex(
+                            remaining,
+                            rng,
+                            minimum_age=minimum_age,
+                            maximum_age=maximum_age,
+                        )
+                        append_residents(parish, household, [(role, (age, sex))])
+                        deferred_other_roles += 1
+                if any(count != 0 for count in remaining.values()):
+                    raise DataBuildError(
+                        f"private resident age/sex pool was not consumed in {parish}"
+                    )
+            except DataBuildError as fallback_exc:
                 raise DataBuildError(
-                    f"{exc} in parish {parish}, household {household['household_id']} "
-                    f"({household['household_type']}, roles={household['_roles']})"
-                ) from exc
-            for role, (age, sex) in assigned:
-                residents.append(
-                    {
-                        "agent_id": "",
-                        "age": age,
-                        "sex": sex,
-                        "home_parish": parish,
-                        "household_id": household["household_id"],
-                        "household_role": role,
-                        "dwelling_type": household["dwelling_type"],
-                        "crowding_band": household["crowding_band"],
-                        "car_access": household["car_access"],
-                        "care_setting_id": None,
-                    }
-                )
-        if any(count != 0 for count in remaining.values()):
-            raise DataBuildError(f"private resident age/sex pool was not consumed in {parish}")
+                    f"initial parish assignment failed: {original_exc}; "
+                    f"residual-last fallback failed: {fallback_exc}"
+                ) from fallback_exc
+            fallback_parishes[parish] = deferred_other_roles
     rng.shuffle(residents)
     for index, resident in enumerate(residents):
         resident["agent_id"] = f"agent-m2-{index:07d}"
-    return residents
+    return residents, fallback_parishes
 
 
 def _communal_age_bounds(setting_type: str) -> tuple[int, int]:
@@ -1475,7 +1555,9 @@ def generate_population(root: Any, config: PopulationGenerationConfig) -> Genera
                 f"could not allocate {remaining_extra} plausible household members in {parish}"
             )
     _assign_housing_attributes(households, controls, rng)
-    private_residents = _assign_private_residents(households, private_age_sex_by_parish, rng)
+    private_residents, residual_fallback_parishes = _assign_private_residents(
+        households, private_age_sex_by_parish, rng
+    )
     residents = private_residents + communal_residents
     rng.shuffle(residents)
     for index, resident in enumerate(residents):
@@ -1505,6 +1587,13 @@ def generate_population(root: Any, config: PopulationGenerationConfig) -> Genera
         target_household_types,
         target_communal_categories,
     )
+    if residual_fallback_parishes:
+        diagnostics["private_assignment_residual_fallback"] = {
+            "parishes": [
+                {"parish": parish, "deferred_other_roles": deferred_roles}
+                for parish, deferred_roles in sorted(residual_fallback_parishes.items())
+            ]
+        }
     if diagnostics["status"] != "passed":
         raise DataBuildError("population diagnostics did not pass")
     runtime_seconds = time.perf_counter() - started
```