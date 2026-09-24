**Implementation verdict: ready for independent review.** The P0-3 negative control and all-arms `execute` path are implemented and mock-tested. This is not a scientific PASS; **no real campaign ran** and `execute` was not invoked.

### Implementation evidence

P0-3 evaluates the full 3 × 3 beta/factor grid, reuses both DATA-9 profiling helpers, and classifies `NON_IDENTIFIED_STRUCTURAL` only when the declared vector, objective, profile, precision, and prediction-hash checks pass. Tests include passing fixtures and deliberately unequal vector, objective-spread, and hash cases.

The mocked P0-1 → P0-2 → P0-3 orchestration uses real config constructors and faithful returned metadata, while mocking simulator and observation calls. It asserts the workload totals: **198 cells, 59 latent calls, 599 observation transforms, and 8 network builds**. P0-3 adds exactly **27 latent calls and 27 transforms**. Mocked results remain `MOCKED` / `NOT_EVALUATED`; they cannot become a scientific PASS.

Bundle publication stages separately from the final path, rejects a non-empty destination before generation, and preserves the destination on failure. Blind estimate records are read back and checked before truth joins.

**Ruling-file limitation:** dry-run reports `g29_ruling_verified: false`. The pinned digest is `06e49aaa7f21564dd6f525941633054fad39cf6714aa74aec0ef1f12dc1eb70c`, but the configured ruling file is absent from this worktree. `execute` requires a ruling file matching that digest; this implementation did not bypass the check.

### Verification

- Dry-run: `198` cells; `59` latent calls; `599` transforms; `8` network builds; CI mode; `30` days; implemented counts equal planned counts.
- `uv run pytest tests/test_phase0_campaign.py -k p0_3`: **2 passed**.
- `uv run pytest tests/test_phase0_campaign.py`: **42 passed**.
- Base comparison against the module loaded from `git show ae885295…`: P0-1 target hashes **5/5**, P0-1 candidates **81/81**, P0-2A candidates **81/81**, and P0-2B candidates **27/27** identical. The blind-estimate hash remained `2ebc1f18a5dac62ec1432fc696e8c885c63cd53e818b8d8fbce0bcf7dad7421a`.
- Ruff format/check, mypy, and compileall passed.
- Full suite, run once on final bytes: **452 passed, 4 skipped, 15 warnings**.
- `git diff --check` passed. HEAD remains `ae885295fca56d60f3e8ed5f33274a752d096d20`; no commit was made.

### Files changed

- [phase0_campaign.py](/home/steven/jos-p0-3-wt/src/jersey_outbreak/phase0_campaign.py)
- [v13_phase0_synthetic.yaml](/home/steven/jos-p0-3-wt/configs/calibration/v13_phase0_synthetic.yaml)
- [test_phase0_campaign.py](/home/steven/jos-p0-3-wt/tests/test_phase0_campaign.py)

Diff: **3 files changed, 1,242 insertions, 83 deletions.** The exact sequential verification output is saved at [jos-p0-3-evidence.log](/tmp/jos-p0-3-evidence.log).