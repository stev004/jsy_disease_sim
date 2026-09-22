IMPLEMENTATION READY FOR REVIEW

Implemented all six director findings within scope.

- Added callable mocked P0-1 adapter/orchestration: exact seeds, 8 parent builds, 32 latent calls, 248 observation transforms, 81×3 candidate replicates, blind fitting, diagnostics, and later-arm data return.
- Enforced all frozen YAML declaration fields and actual candidate-config provenance hashing.
- Missing workload, seeds, namespace, calendar, and completion evidence now fail closed.
- Blind estimates are persisted and verified before truth joins.
- Predeclaration tests use the repository-relative committed file.
- Research bundles reject nonempty destinations and verify fresh checksums without hashing `SHA256SUMS` itself.
- CLI execution remains blocked pending P0-2/P0-3 and independent review.

Before/after evidence:

- Before: regression collection failed on checkpoint because `ExecutionEvidence`/adapter symbols were absent (`collected 0 items / 1 error`).
- After: `uv run pytest tests/test_phase0_campaign.py` → `21 passed`.
- Dry-run confirms hash `ef67fe...3a104`, 198 cells, 59 latent calls, and 599 transforms.
- Full suite: `430 passed, 4 skipped, 15 warnings`; this predates the final test-only additions, which are covered by the final 21-test focused run.
- Final lock, compileall, Ruff, format, both mypy checks, relocation check, and `git diff --check` all passed.

Files changed:

- [phase0_campaign.py](/home/steven/jos-p0-1-wt/src/jersey_outbreak/phase0_campaign.py)
- [test_phase0_campaign.py](/home/steven/jos-p0-1-wt/tests/test_phase0_campaign.py)

Diff: `+1120 / -36` lines. Config YAML unchanged. No commit made.

Transcript: `/tmp/jos-p0-1-r1-evidence.log`

No P0-1 campaign, pilot, real-data fit, or unmocked generation was run. No protected modules were changed.