*Filed verbatim by the director (Claude Opus 5.5), extracted programmatically from the independent re-review subagent's final message: fresh Claude Opus 5.5 @ high (frozen G43 §12 seat 4; disclosed: same model family as the director and the earlier reviewers; author of none of the code); brief docs/runs/2026-11-25-g44-rereview2-brief.md.txt; reviewed head 2b2cd2a4a8237f93ad8e7d3b800585f4c1c489a8; 134,370 tokens.*

---

Claude Opus 5.5 (claude-opus-5-5) @ high

JOS G43 IMPLEMENTATION RE-REVIEW: PASS

**Basis.** I cloned the review clone into `/tmp/jos-g44-rereview2-20261125`, detached at `2b2cd2a4a8237f93ad8e7d3b800585f4c1c489a8`. I cloned it again into `/tmp/jos-g44-rr2-base-20261125`, detached at `73978427f5dabff70dde4a0a8b06aab372df7f4c`, and copied the new test file in. Each mutant ran in its own `/tmp/jos-g44-rr2-mut-*-20261125` copy.

I also added throwaway probe tests to the `/tmp` copies only. They cover these cases on both heads:
- an intact run
- a VOID evaluation that raises no exception (shared panel P1)
- a marker that already exists when the run finishes
- a hard-link failure on the intact path and on the VOID path
- a marker parent that is a file, a symlink pointing into the bundle, and a relative marker path

The frozen predeclaration still hashes to `67c3c7c0…1094`, both at `fc16adc` and on main. The review clone is clean at `2b2cd2a`. I did not edit the clone or the repo, run any study seed or run the full suite.

## Findings

**Q1 — NOTE — `src/jersey_outbreak/g43_multilibrary.py:2242–2250` (atomic marker write); no test for the no-overwrite rule**
- **Rule:** §12 line 682: "The launcher refuses to start if an exit marker exists."
- **Behaviour now:** the code is correct. I created the marker during generation in a probe. On `2b2cd2a`, `os.link` raised `FileExistsError` and the existing marker ("OTHER") was left alone. The sealed PASS bundle still passed `verify_bundle`, and no temporary file was left behind. On `7397842` the same probe turned the completed campaign into VOID.
- **Test gap:** mutant M15 (`os.link` → `os.replace`, which overwrites silently) survives all 39 marker, execute and VOID tests. No test checks that an existing marker is never overwritten.
- **Failure scenario:** a later refactor to `os.replace` would pass CI and silently overwrite the marker of an earlier launch.
- **Smallest fix:** one test that creates the marker during a mocked run, then asserts `FileExistsError`, the marker bytes unchanged and the bundle still intact.

**Q2 — NOTE — `g43_multilibrary.py:2273–2274` (VOID path without an exception)**
- **Rule:** line 701: "seals a partial bundle with `software_status` VOID".
- **Asymmetry:** the intact-path marker write now sits outside the `try`, but `write_marker("VOID")` after a VOID evaluation is still inside it.
- **Failure scenario (probe):** `os.link` fails after a shared-panel-P1 VOID. The handler re-seals the bundle as VOID with cause `"OSError: injected link failure"`, replacing `"shared panel P1"`. It then raises, and no marker is written.
- **Why it does not block:** the status stays VOID and the bundle still verifies. The behaviour is the same as on `7397842`, where the write was also inside the `try`. The launch-time check on the parent makes it unlikely. It is not new.
- **Smallest fix:** write the VOID marker after the `try` as well, so the recorded cause survives a marker failure.

**Q3 — NOTE — `g43_multilibrary.py:2246` (marker permissions)**
- `NamedTemporaryFile` creates files with mode 0600, and the hard link keeps that mode. The marker is now `0o100600`; on `7397842` it was `0o100644`.
- The frozen text does not govern this. The launch account can still read the marker, and `test_intact_execute_creates_exit_marker_and_refuses_sibling` passes.
- **Fix if wanted:** `os.chmod(stream.name, 0o644)` before the link, or record the 0600 mode in the launcher brief.

**Q4 — NOTE — remaining small windows (reported, not defects)**
- An interrupt after `os.link` but before `NamedTemporaryFile.__exit__` unlinks the temporary file leaves a complete marker plus a stray `tmp*` file. The marker and bundle still agree.
- The directory entry is not fsynced after the link, so after a power loss the marker could be missing, but never partial.
- A second interrupt inside the handler (window 2) stays open as scoped. The new comment at line 2296 says the sealed bundle is the authoritative record.
- After a marker failure on the intact path, no marker exists. A launch into a different empty directory would then not be refused by the exit-marker rule. The launch-time parent check (N1a) makes this unlikely.

## Per-finding verification (focused selections only)

| | On `7397842` (new test file copied in) | On `2b2cd2a` | Mutation |
|---|---|---|---|
| **N1(a)** launch refuses a missing or non-writable parent (chmod 0500, ran as UID 1000, not skipped) | `missing_parent` and `unwritable_parent` FAIL | PASS | M11 (parent check disabled) kills both |
| **N1(b)** a marker failure after the intact seal keeps the bundle | `PermissionError` case FAIL (bundle was VOIDed) | PASS: bundle verifies, `software_status` PASS, all six PASS verdicts, matrices and across-library file present, `SHA256SUMS` byte-identical to the sealed one, same exception object raised | — |
| **N2** atomic marker | `KeyboardInterrupt` case FAIL (partial marker left) | PASS: marker directory empty | M14 (`delete=False`, temporary file not cleaned) killed; M15 survives (Q1) |
| **N3** inside-bundle refusal | passes (old guard sound) | PASS | M10 killed (`inside_bundle`) |
| **N3** P1 evidence conjunction | passes | PASS | M4 (`all(row.complete …)` at line 1657 → `True`) killed: `assert True is False` on `execution_complete` |
| **N4** | — | `status` dropped from `observation_diagnostics`; `g43_recompute.py:1054–1060` and the test readers use only `no_report_before_infection` and `latent_incidence_conservation`; the unused helper parameter and both call sites removed | — |

Totals:
- Base: 4 failed, 24 passed (exactly the four N1/N2 regressions).
- Head: 28 passed.

**Frozen line 637 check.** P3's keys are retained and `status` is not one of them. Removing it is consistent with retaining "the observation diagnostics keys used by P3". `status` is still disclosed in `truth_diagnostics.raw_values`.

**Launch probes on `2b2cd2a`:**
- A marker parent that is a regular file is refused with the new message; on `7397842` launch went on into the work.
- A symlink pointing into the bundle is refused as "inside the bundle" on both heads.
- A relative `campaign.exit` in a writable working directory is accepted on both heads.

## Checks

1. Scope: **OK.** `git diff --name-status` shows only the two expected `M` paths. `g43_constants.py`, `g43_recompute.py`, configs, fixtures and protected modules are untouched (empty diff stat).
2. N1–N4 corrected as lines 637, 682 and 701 require, and the regressions fail on `7397842` (or under M10/M4) and pass on `2b2cd2a`: **OK** (one test gap in Q1).
3. No new departure: **OK.** I ran the same mocked inputs on both heads, once intact and once as a shared-panel-P1 VOID.
   - The bundles have the same file sets, the same `campaign_summary.json` once disclosures and timing are excluded, and the same `measured_work`.
   - The only differing files are the source hashes (the code changed), timing-dependent `SHA256SUMS` and summary bytes, and `targets/latent_truth/*.json`. The latent-truth files differ only by the removed `observation_diagnostics.status` key; every other field is equal.
   - The VOID run without an exception still seals VOID with cause `shared panel P1` and writes a VOID marker.
   - An intact campaign whose marker write fails keeps its sealed bundle and scientific outputs and propagates the error.
   - No predicate, threshold, seed, reading or S1/S2 rule changed. `classify_campaign` and `evaluate_shared_panel` are not in the diff.
4. Marker semantics: **OK.**
   - Launch refuses a missing, non-directory or non-writable parent and a marker inside the bundle, before `_execution_inputs` runs.
   - The `os.link` publish never overwrites (probe), and an interrupt leaves no partial marker (test).
   - The temporary file is removed on success, on link failure and on interrupt (probe directories hold only `campaign.exit`, or are empty).
   - The earlier R7 tests pass unchanged on the head: the original exception is re-raised by identity, `KeyboardInterrupt`/`SystemExit` are re-raised after the VOID seal, and a failed first VOID finish leaves a bundle that `verify_bundle` rejects.
5. Dry-run counts: **OK.** The G43 dry-run stdout is byte-identical between `7397842` and `2b2cd2a` (`cmp`): 92 / 1,820 / 45,020; 75,000 / 375,000; 120 / 600. Ruff and mypy are clean on the changed module.
