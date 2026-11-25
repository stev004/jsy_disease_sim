*Filed verbatim by the director (Claude Opus 5.5), extracted programmatically from the independent re-review subagent's final message: fresh Claude Opus 5.5 @ high (frozen G43 §12 seat 4; disclosed: same model family as the director and the earlier reviewers; author of none of the code); brief docs/runs/2026-11-25-g44-rereview3-brief.md.txt; reviewed head 98289b3c04262a513ed2482f9bf18b9e86726435; 105,901 tokens.*

---

Claude Opus 5.5 @ high

JOS G43 IMPLEMENTATION RE-REVIEW: PASS

**Findings**

**R3-1 · NOTE · `src/jersey_outbreak/g43_multilibrary.py:2304–2306`. No shipped test checks a successful VOID marker after a non-exception VOID.**
- **Rule:** predeclaration line 701, "seals a partial bundle with `software_status` VOID". Line 682 governs the exit marker ("The launcher refuses to start if an exit marker exists").
- **What the diff did:** it replaced the literal `write_marker("VOID")` in the VOID branch with the shared `write_marker(summary["software_status"])` in the `else:` clause.
- **The code is correct.** My probe ran a shared-panel-P1 VOID with a working `os.link` on the head. `execute` returned cause `shared panel P1`, `verify_bundle` passed, the marker read `{"output_dir":…, "software_status":"VOID"}` with mode 0644, and the marker directory held only `campaign.exit`.
- **The test gap:** I changed line 2306 to `write_marker("PASS")`, which was the literal on that line before the diff. All 8 marker, execute and VOID tests I selected still pass, including the new Q2 test (it fails the link, so the marker is never written) and both 0644 tests (which cover the intact path and the exception path only). Only my probe caught it: the marker read `"software_status":"PASS"` for a VOID campaign.
- **Failure scenario:** a later refactor reverts the line to `write_marker("PASS")`. CI passes, and a P1-VOID campaign publishes a PASS exit marker next to a VOID bundle.
- **Smallest fix:** one test that runs `VoidCampaign("shared panel P1")` with a working link, then asserts that the marker JSON says `software_status` VOID, the mode is 0644, and no stray temporary file is left. It is the same shape as my probe on the existing `mocked_marker_run` fixture.
- **Why it does not block:** the behaviour is right, and the gap is a missing test for a path the diff reorganised.

**Checks**

1. Scope (OK)
   - `git diff --stat 2b2cd2a 98289b3` touches only `src/jersey_outbreak/g43_multilibrary.py` (+16/−15, all inside `execute`: the `write_marker` chmod, the VOID/else restructure and the `else:` marker call) and `tests/test_g43_multilibrary.py` (+79).
   - Ruff check, ruff format and mypy are clean.

2. Q1 (OK)
   - `test_exit_marker_created_during_intact_run_is_not_overwritten` fails under M15 (`os.link` → `os.replace`) and passes on the head.
   - It asserts `FileExistsError`, unchanged marker bytes, a marker directory holding only the marker, a passing `verify_bundle`, and a PASS summary with the scientific outputs present.

3. Q2 (OK)
   - **Regression:** `test_exit_marker_link_failure_preserves_sealed_shared_panel_void_bundle` fails on `2b2cd2a` and passes on the head. It asserts the original `OSError` by identity, cause `shared panel P1`, summary and `SHA256SUMS` bytes equal to their values at link time, `verify_bundle` passing, and no stray file.
   - **Intact path:** it still writes PASS (`test_intact_execute_creates_exit_marker_and_refuses_sibling` passes).
   - **Exception path:** the `except BaseException` handler is not changed by the diff. The re-raise and original-exception tests (`base_exception[KeyboardInterrupt|SystemExit]`, `marker_failure_preserves…`) pass on the head.
   - **Typing:** `StudyEvaluation.campaign` is typed `IntactCampaign` (line 1602), so the `else` branch always yields PASS.

4. Q3 (OK)
   - The `stat.S_IMODE == 0o644` assertions in the intact test and in `test_execute_seals_partial_void_and_recompute_omits_science` (the exception-path VOID) fail on `2b2cd2a` and pass on the head.
   - The probe confirms 0644 on the non-exception VOID path as well.
   - `os.chmod` comes before the fsync and the link, so the published marker is never 0600.

5. Dry-run (OK)
   - The G43 dry-run stdout is byte-identical between the two heads (`cmp`), SHA-256 `8aafbe644b370850d1caf294cfbba7ef6f9bb41de9ce60cc8fbb27f0565aefec`.
   - A first base run differed only by a one-time matplotlib font-cache notice printed on first import. The rerun was identical.
   - The frozen predeclaration SHA-256 matches `67c3c7c0…5b71094`.

**Method notes**
- **Test totals:** on the clean head clone, 41 passed and 0 failed. With the head tests on the base code, 3 failed: Q2 and the two 0644 assertions. The Q1 test passes on base, as expected, because the base code was already correct.
- **Venv mix-up:** my first mutant and probe copies were made with `cp -a`, and their copied `.venv` made pytest import the head clone's source. I discarded those results, rebuilt each copy's venv, and confirmed by `study.__file__` that each copy used its own source. Only the confirmed reruns are reported.
- **Scope kept:** I edited nothing in the repo or the worktree, made no commits or pushes, ran no study seeds and did not run the full suite. All temporary files were on `/dev/shm/g44rr3-tmp`, and the copies are under `/tmp/jos-g44-rereview3-*` and `/tmp/jos-g44-rr3-*`.
