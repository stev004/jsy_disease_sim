P0-2 IMPLEMENTATION REVIEW: BLOCKED

**BLOCKING**

1. **The accepted G29 digest is not frozen.** [phase0_campaign.py](/home/steven/jos-p02-review-readonly/src/jersey_outbreak/phase0_campaign.py:760) accepts the digest from the supplied config, and ruling verification compares against that same value. I replaced both in `/tmp` with an unrelated ruling; dry-run returned `g29_ruling_verified: true`. The same validator serves execute and bundle. Pin validation to the accepted digest `06e49a…eb70c` and test rejection of a changed config digest.

2. **The P0-2 blind record is not hash-checked before truth joining.** [phase0_campaign.py](/home/steven/jos-p02-review-readonly/src/jersey_outbreak/phase0_campaign.py:2653) compares `persist_blind_estimate`’s return value with `fit.estimate_hash`, but the persistence function returns that very value without validating the saved content. In a `/tmp` probe, a non-JSON blind file passed this comparison and truth evaluation proceeded. Read back and verify the persisted selection or tie record and its hash before passing truth and the correct-arm minimum to evaluation; add a corruption regression.

**MAJOR**

- [phase0_campaign.py](/home/steven/jos-p02-review-readonly/src/jersey_outbreak/phase0_campaign.py:637) emits `selected_estimates` as the string `"null"` in JSON provenance for a tie, rather than a native null. Keep the CSV representation as needed, but serialize undefined estimates as null in JSON, as G29 requires.

**MINOR**

- The third G29 worked-example test checks `UNKNOWN` and `[3,4]`, but supplies no predictions showing the stated candidate errors `E=0.10` and `E=0.40` ([test_phase0_campaign.py](/home/steven/jos-p02-review-readonly/tests/test_phase0_campaign.py:493)). Add those contrasting values to the fixture.

| Acceptance | Decision |
|---|---|
| 1. Identity, scope, declaration | **PASS.** HEAD’s direct parent is `367f032…`; only the three authorized files changed. Grids, thresholds, k values and counts match. |
| 2. Isolated arms and namespace | **PASS.** The field-by-field mock comparison and construction path show delay alone changes in A, and the two detection probabilities alone change in B. |
| 3. \(R_i\), \(E_i\) | **PASS.** Floors, selected-candidate library, three-replicate mean, two-channel maximum and inclusive comparisons match the formulas. |
| 4. G29 | **BLOCKED on JSON null serialization.** Tie selection, TRUE/FALSE/UNKNOWN logic, fixed-five aggregation and overall PASS logic otherwise match; the three example outcomes are tested, with the fixture gap noted above. |
| 5. Blind boundary and reuse | **BLOCKED on persisted-record verification.** Fitter inputs exclude truth; ordering, zero new latent calls and 243+81 guarded transforms check out. |
| 6. Provenance and bundle | **BLOCKED on digest freezing.** Files, SHA256SUMS, nonempty-output rejection and the P0-3 execution block are present. |
| 7. Tests and P0-1 stability | **PASS for P0-1; BLOCKED for the new persistence assertion.** No P0-1 assertion was weakened. All 86 constructed P0-1 candidate/target hashes matched base, and a blind-estimate hash matched base; the P0-2 persistence comparison is tautological. |
| 8. Other result risks | **No further computational defect identified.** The findings above prevent a verifiable P0-2 result. |

**Director points:** Plain float `>=` faithfully implements the declared \(R_i/E_i\) comparisons; the broader computed-boundary question remains for all-arms review. Stripping later-arm metadata preserved all 86 sampled P0-1 input hashes; independently constructed hash sets had 81/81/27 unique P0-1/A/B cells and zero cross-arm overlaps. An arm exception fails closed without a serialized `software_status=FAIL`; the declaration and ruling require PASS only for completed arms, so I do not treat that behavior as an additional blocker.

**Verification:** The accepted `/tmp/g29-ruling.md` hash matched `06e49aaa7f21564dd6f525941633054fad39cf6714aa74aec0ef1f12dc1eb70c`. Real-ruling dry-run reported implemented **189/32/572** and planned **198/59/599**. Focused tests: **38 passed** after directing external Numba/Matplotlib caches to `/tmp`; the first invocation stopped during import because of the read-only external cache. The supplied [CI mirror log](/home/steven/jos-p02-mirror.log) reports exit 0, **448 passed, 4 skipped**; the known job-ordering test passed. No simulator or campaign arm was run in this review.

Final SHA: `4df879d2f4357614148f6932e22e0c80fe760025`. Diff: **3 files, +1,378/−35**. Initial and final `git status --porcelain` were empty.