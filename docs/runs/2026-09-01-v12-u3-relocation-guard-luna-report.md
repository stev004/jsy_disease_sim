Implemented only [scripts/ci_relocation_check.py](/private/tmp/jsy_v12_carryins/scripts/ci_relocation_check.py:14).

Diff:

```diff
+    expected_parent = (root / "outputs" / "interventions").resolve()
+    existing_artifacts = set(expected_parent.iterdir()) if expected_parent.exists() else set()
...
+    if artifact_directory in existing_artifacts:
+        print(f"refusing to delete pre-existing artifact: {artifact_directory}")
+        raise SystemExit(3)
```

Verification:

- Clean case: exit `0`; printed `verifier success: m7_intervention ...`; artifact removed.
- Pre-existing case: exit `3`; printed `refusing to delete pre-existing artifact: ...`; artifact remained, then was cleaned up.
- `uv run ruff check .`: `All checks passed!`
- `uv run ruff format --check .`: `129 files already formatted`
- `git status --porcelain`: only `scripts/ci_relocation_check.py` modified.