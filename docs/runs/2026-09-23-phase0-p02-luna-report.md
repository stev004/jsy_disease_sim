**Verdict: P0-2 implementation complete and ready for independent review.** This is an implementation verdict, not a Phase-0 scientific verdict. No real campaign arm ran; `execute` remains blocked pending P0-3 and independent review.

Implemented both arms, the G29 tie handling, reuse of the P0-1 latent cache, dry-run budgeting, hash-checked ruling provenance, and bundle outputs in [phase0_campaign.py](/home/steven/jos-p0-2-wt/src/jersey_outbreak/phase0_campaign.py:2519) and [v13_phase0_synthetic.yaml](/home/steven/jos-p0-2-wt/configs/calibration/v13_phase0_synthetic.yaml:8). Tests are in [test_phase0_campaign.py](/home/steven/jos-p0-2-wt/tests/test_phase0_campaign.py:373).

**Acceptance evidence**

1. P0-2A generates 81 cells with reporting delay forced to zero; P0-2B generates 27 cells with common probabilities 0.25, 0.50, and 0.75. The mocked adapter test compares generated observation configs field by field against P0-1 configs and confirms only the declared observation assumptions change.

2. Deterministic fixtures cover the R and E denominator floors and inclusive 0.25 boundaries. Reused P0-1 recovery-tolerance checks call the exact-decimal helpers; computed R and E use plain inclusive `>=`, without epsilon.

3. Tied wrong-model minima are never selected. R can establish `TRUE` despite a tie; otherwise undefined selected-candidate clauses produce `UNKNOWN`, with undefined outputs serialized as null.

4. Fixtures cover the G29 tie examples, the P0-2B `[3,4]` indeterminate aggregate, and clean PASS and FAIL aggregates for each arm.

5. Software completion is reported separately from detection. The mocked tie case completes with `software_status=PASS` and indeterminate detection.

6. Fitter-facing functions exclude truth metadata. Mocked tests verify estimate persistence precedes truth joining.

7. P0-2 reuses P0-1 observations and candidate latents. The mock records **zero additional latent outbreak calls** for P0-2.

8. Dry-run reports implemented totals of **189 cells, 32 latent calls, and 572 observation transforms**; all-arms planned totals are **198 cells, 59 latent calls, and 599 transforms**, with 8 network seeds, CI mode, and 30 days. The mock measures P0-2 at 0 latent calls and 324 observation transforms: 243 for P0-2A and 81 for P0-2B.

9. The config records the required ruling path and SHA-256. Temporary-file tests verify a matching ruling and reject a mismatch. The real ruling file is absent from this worktree as instructed; the normal dry-run therefore reports `g29_ruling_verified: false`. Execute requires a verified ruling.

10. The mocked bundle test checks the per-target CSV, complete per-arm loss surfaces, replicate provenance, null values for tied estimates, and ruling provenance. No scientific evidence is produced by the mocks.

**Verification**

- `git rev-parse HEAD` → `367f0324685437c4d2ed4aa0ae4878229da09839`. Final status lists only the three authorized files.
- Ruff format, Ruff check, format check, mypy, compileall, and the required dry-run completed successfully. Dry-run printed the specified predeclaration and ruling hashes and the workload totals above.
- `uv run pytest tests/test_phase0_campaign.py -k p0_2` → **5 passed, 33 deselected**.
- `uv run pytest tests/test_phase0_campaign.py` → **38 passed**.
- The single full-suite run → **448 passed, 4 skipped, 15 warnings** in 821.52s. The known job-ordering test group passed.
- `git diff --check` was clean. Final diff: **3 files changed, 1,378 insertions, 35 deletions**.

An earlier focused attempt failed because a boundary-test fixture used `5/3` where a prediction of `5` was needed to produce E = 0.25 against a target total of 4. The fixture was corrected before the final focused and full-suite runs.

**Open review question:** confirm whether the computed-objective R and E boundary behavior should remain plain floating-point inclusive comparisons, without decimal-grid semantics or epsilon. This implementation follows the brief.

No protected-contract conflict was found. The evidence log, including exact commands and outputs, is at [jos-p0-2-evidence.log](/tmp/jos-p0-2-evidence.log). No commit or push was made.