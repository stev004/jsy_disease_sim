Implemented within scope.

Files changed:

- [travel.py](/private/tmp/jsy_v12_carryins/src/jersey_outbreak/travel.py:2967): predicate-derived ensemble diagnostics; payload unchanged.
- [test_v12_carry_ins.py](/private/tmp/jsy_v12_carryins/tests/test_v12_carry_ins.py:1): regression coverage.
- [ci.yml](/private/tmp/jsy_v12_carryins/.github/workflows/ci.yml:1): full backend/frontend release gate.
- [ci_relocation_check.py](/private/tmp/jsy_v12_carryins/scripts/ci_relocation_check.py:1): real-CLI relocation verifier.

1. Literal status check

```text
$ grep -n '"status": "passed",$' src/jersey_outbreak/travel.py
(no output)
```

2. Failing-test-first

Against committed base source:

```text
FF
AttributeError: module 'jersey_outbreak.travel' has no attribute '_travel_ensemble_diagnostics'
AttributeError: 'types.SimpleNamespace' object has no attribute 'scenario_hash'
2 failed in 0.53s
```

After implementation:

```text
..
2 passed in 0.16s
```

3. Full locked suite

```text
$ uv run --locked pytest -q
231 passed, 5 warnings in 647.38s (0:10:47)
```

4. Hash unchanged

```text
base logical_content_hash: 5f217004848254f32d4e0d0f812956e962973f5a1ed76b5a4f1b35e5bea549bd
modified logical_content_hash: 5f217004848254f32d4e0d0f812956e962973f5a1ed76b5a4f1b35e5bea549bd
```

5. Ruff and compileall

```text
uv run ruff check .
All checks passed!

uv run ruff format --check .
127 files already formatted

uv run python -m compileall -q src
(exit 0, no output)
```

6. CI checks

```text
grep counts:
1
1
1
1
1
```

These correspond to lock check, compileall, diff check, setup-node, and npm build. Relocation step:

```text
.github/workflows/ci.yml:45: - run: uv run python scripts/ci_relocation_check.py
```

7. Added CI commands

- `uv sync --locked`: passed.
- `uv lock --check`: passed.
- `uv run python -m compileall -q src`: passed.
- `git diff --check`: passed.
- Relocation check: passed.

```text
verifier success: m7_intervention jos-intervention-m7-ci-seed-123-c0be3d419f32
real 14.68
```

Frontend:

```text
npm ci
added 110 packages, and audited 111 packages in 3s

npm run test
Test Files  2 passed | 1 skipped (3)
Tests  15 passed | 6 skipped (21)

npm run typecheck
tsc --noEmit
(exit 0)

npm run build
✓ built in 666ms
```

The workflow clean-worktree assertion was executed locally but necessarily returned nonzero because these intended changes are uncommitted:

```text
test -z "$(git status --porcelain)"
(exit 1; expected until commit)
```

8. Final scope

```text
 M .github/workflows/ci.yml
 M src/jersey_outbreak/travel.py
?? scripts/ci_relocation_check.py
?? tests/test_v12_carry_ins.py
```

No other files changed.

Schema finding: `M8_ARTIFACT_SCHEMA_VERSION = "2.2"` governs the travel artifact manifest and is exposed by the API. There is no separate travel-ensemble diagnostics schema/version constant; `diagnostics.json` is additive under the existing convention. No version was bumped.

Relocation choice: M7 intervention artifact, because `verify_scientific_artifact` recursively verifies its embedded M5 latent bundle. Local wall time: 14.68 seconds.

`git diff --stat`:

```text
 .github/workflows/ci.yml      | 22 ++++++++++++++++++++
 src/jersey_outbreak/travel.py | 48 ++++++++++++++++++++++++++++++++++---------
 2 files changed, 60 insertions(+), 10 deletions(-)
```

Only notable warnings were existing npm audit warnings, sandbox Arrow sysctl warnings, and test-library deprecation/runtime warnings; none caused failures.