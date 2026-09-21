IMPLEMENTATION READY FOR REVIEW

Implemented only the three authorized paths:

- [phase0_campaign.py](/home/steven/jos-p0-1-wt/src/jersey_outbreak/phase0_campaign.py:1): frozen P0-1 config validation, blind 81-cell scoring, objective, ties, profiles, recovery predicates, budget guard, hashes, bundle writer, and fail-closed execution.
- [v13_phase0_synthetic.yaml](/home/steven/jos-p0-1-wt/configs/calibration/v13_phase0_synthetic.yaml:1)
- [test_phase0_campaign.py](/home/steven/jos-p0-1-wt/tests/test_phase0_campaign.py:1): 13 deterministic acceptance tests.

Evidence:

- Dry-run passed: 81 P0-1 cells, 5 targets, 3 fitting seeds, 32 P0-1 latent calls, 248 P0-1 transforms; full caps 198 cells, 59 latent calls, 599 transforms.
- Focused campaign tests: 13 passed.
- Full suite: 422 passed, 4 skipped, 15 warnings.
- `uv lock --check`, compileall, full ruff check/format, new-module mypy: passed.
- Exact CI pinned mypy list and relocation check: passed.
- `git diff --check`: passed.
- Transcript: [/tmp/jos-p0-1-evidence.log](/tmp/jos-p0-1-evidence.log)

Final scope is exactly three uncommitted files:

```text
1292 phase0_campaign.py
 129 v13_phase0_synthetic.yaml
 357 test_phase0_campaign.py
```

P0-2/P0-3 remain intentionally unimplemented. `execute` fails closed on missing required arms. No campaign, pilot, fitting, or real-data run was executed, and no scientific or gate PASS is claimed.