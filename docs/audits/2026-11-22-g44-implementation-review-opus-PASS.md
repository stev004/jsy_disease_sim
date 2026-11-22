*Filed verbatim by the director (Claude Opus 5.5) from the independent-review subagent's final message: fresh Claude Opus 5.5 @ high (frozen G43 §12 seat 4; disclosed: same model family as the director; author of none of the code); brief docs/runs/2026-11-22-g44-review-brief.md.txt; reviewed head c723f71a652ce2d11278f0e2958bb72baf9716da; 292,223 tokens. HTML entities in the relayed text (`&lt;`, `&gt;`) are rendered as `<`, `>`.*

---

Claude Opus 5.5 (claude-opus-5-5) @ high

JOS G43 IMPLEMENTATION REVIEW: PASS

**Basis.** The review clone is at `c723f71a652ce2d11278f0e2958bb72baf9716da` (detached) with a clean tree before and after my runs. Base `9002c59` is an ancestor. Between `0c9c371` and `9002c59`, `src configs tests scripts` is empty. The frozen predeclaration bytes at `fc16adc` hash to `67c3c7c0…1094`.

What I ran myself:
- The G43 dry-run.
- The G35-B, Phase-0 and Phase-0b dry-runs.
- The focused `tests/test_g43_multilibrary.py`: 1053 passed.
- An independent constants and fixture re-derivation from committed bytes and from the retained G35-B bundle.
- Five mutation tests in a `/tmp` copy.

No study seed was built or run. I did not run the full suite, and I edited nothing in the clone.

## Findings

**R1 — MINOR — `src/jersey_outbreak/g43_multilibrary.py:2018–2025`**
- **Rule:** §9 line 627: "The launcher refuses to start unless host free space is at least 5 GB plus the upper size estimate as updated by U3's measurement."
- **Defect:** `--bundle-upper-bytes` replaces the default estimate (1,000,000,000 + the 1,048,576 measured by U3) with any non-negative integer. That includes values below the U3-updated estimate.
- **Failure scenario:** `--bundle-upper-bytes 0` makes the launcher accept 5.0 GB free. The rule requires about 6.0 GB. The host had 9.9 GB free at review time, so this gap is close to the real margin, and a WSL VHD growth crash is exactly the 2026-09-02 lesson.
- **Smallest fix:** refuse an override below `default_upper`, so overrides can only raise the requirement. Add a test with an override of `default_upper - 1`.

**R2 — MINOR — `g43_multilibrary.py:1642`**
- **Rule:** DIRECTOR lesson 2026-09-22: "evidence checks require returned metadata and reject absence". Brief check 6 asks for any literal `True` evidence to be flagged.
- **Defect:** the shared-panel P1 evidence is `IntegrityEvidence(True, provenance_verified, …)`, with `execution_complete` written as a literal `True`. The per-row `TruthDiagnostics.complete` is also a literal `True` in the unchanged `phase0_campaign.py:2533`. So shared P1 reduces to "the roster equals the 20 frozen target seeds". That roster comes from an independent source (`g43_constants.FINAL_SEEDS`), and any failed or raised target run makes the campaign VOID through the exception path. The verdict cannot be wrong today.
- **Failure scenario:** a simulator change that returns a truncated run without raising would still produce P1 = true. `recompute_p3`'s `states.conserved` uses `all(...)` over `daily_epidemic`, so it is also vacuously true on an empty table.
- **Smallest fix:** derive target completion from returned metadata, for example `len(daily_epidemic) == 30`, the observation `status == "passed"`, and a 34-date table. Mirror the length check in `g43_recompute._recompute_panel`. Alternatively, file a one-line attribution note that P1 completion means "no exception plus complete frozen roster".

**R3 — NOTE — `g43_multilibrary.py:2011–2013`**
- **Rule:** §12 line 682: "The launcher refuses to start if an exit marker exists".
- **Observation:** `execute` checks for `<output parent>/jos-g43-campaign.exit` (or `--exit-marker`) but never writes it.
- **Failure scenario:** the refusal only works if the director's launcher writes exactly that path. Otherwise a second `execute` into another empty sibling directory is not refused by the code.
- **Smallest fix:** state the marker path in the campaign launcher brief, written with `|| die` on exit. Or have `execute` create the marker after sealing.

**R4 — NOTE — `tests/test_g43_multilibrary.py:1736–1789` (test gap, not a code defect)**
- **Rule:** DIRECTOR lesson 2026-09-23 (an independent source of truth for each integrity check).
- **Observation:** two single mutations survived the four candidate-corruption cases:
  - removing `record["table_sha256"] == table_sha256(table)` from `g43_recompute.provenance_matches` (M2);
  - neutralising the fit-surface binding check in `_library_evidence` (M5).
- **Why the code is still sound:** each check covers the other for the corruptions that are tested. I read the unmutated code: P9 does reject a table body that differs from its recorded digest.
- **Gap:** no test corrupts a candidate table body while keeping its recorded `table_sha256`. That is the case only the table-hash check catches.
- **Smallest fix:** add that corruption case.

**R5 — NOTE — `src/jersey_outbreak/g43_constants.py:8`**
- **Observation:** the comment "Exact LF bytes of the U1 config, pending the director's commit" is stale. `CONFIG_SHA256` `118d990b…02d2` equals the committed config bytes at HEAD, which I verified.
- **Fix:** drop "pending the director's commit".

**R6 — NOTE — `g43_recompute.py:697–703, 908–933`**
- **Rule:** §7.2/A9: "P10 reads the operational work ledger".
- **Observation:** the recompute script takes P10's measured counts from `campaign_summary.json.measured_work`. That is the only retained copy of the ledger, and the expected caps are parsed independently from the frozen §9 table.
- **Fix:** the exit-audit brief should say this, and the auditor may cross-check the counts against file counts, which `read_candidate_library` and the blind-path set checks already do.

**R7 — NOTE — `g43_multilibrary.py:2241`**
- **Observation:** `except Exception` does not catch `KeyboardInterrupt`/`SystemExit`. An exception raised inside the VOID `finish()` itself is not handled either. In those cases the partial bundle would be left unsealed, against §12 line 701 ("seals a partial bundle").
- **Fix:** the launcher should treat an unsealed destination as VOID (`verify_bundle` fails). Or use `except BaseException` plus best-effort sealing.

## Verification detail

1. **Scope.** The diff adds exactly the 6 expected paths: the three modules, the config, the test file and one fixture. There are no M/D/R entries. The protected modules, including `g35b_design_study.py`, `g35b_constants.py` and `phase0_campaign.py`, are unchanged. The G35-B pure functions (`loss`, `_fit_scored_grid`, `_offset_descriptive`, `batch_offset_agreement`, `batch_objective_spread`, `_persist_fit`/`_verify_blind_readback`, `committed_document_bytes`, `_GenerationAdapter`) are imported, not copied.
2. **Constants.** I parsed the committed frozen text independently:
   - all 92 final-seed rows match `FINAL_SEEDS`, including 87351 at L3 position 1, 87352 at L3 position 5 and 87551 at L5 position 6, with their inherited observation seeds;
   - all 92 M2/M3/M4 hash triples match;
   - the 22 earlier ranges, 43 unused reserves and 3 exclusions match;
   - the ruling, clarification, pre-check and config digests match committed bytes.

   Config validation is an exact `_compare` of type, keys and values plus the LF/SHA check. The dry-run gave 20/20/20 shared, and 12/300/7500/625/12500/20/62500/100/0 per library. Totals were 92/1820/45020/3750/75000/120/375000/600/0, with `ci`, 30 latent days and 34 dates. The G35-B, Phase-0 and Phase-0b dry-runs report their frozen counts.
3. **Evaluator.**
   - Integer tests: `5·hits ≥ 4N`, `5·joint ≥ 3N`, `5·boundary ≤ N`.
   - Bias is an exact `Decimal` under an `Inexact` trap, and P7 is undefined unless all N targets have a selected cell.
   - P8 has its own flags.
   - P2 is computed from its five fields and P3 from the four raw flags, never from `viable`.
   - Endpoint tests cover 16/15, 12/11, 4/5 and decimal cancellation.
   - Historical fixture: I verified that all 27 source digests equal the retained G35-B bundle bytes and its `SHA256SUMS`, which digests to `e6649a4b…`. All 20 gate records (selected cell, tie, estimate_hash, profiles, 625 cells) equal the bundle's blind files. The test reproduces B FAIL (P5, P8; 10/7/9/10, 7, 0/3/0/0) and i PASS (10/8/8/10, 6, 0/2/0/0) against expected values transcribed from the audit, so they are not derived from the input.
4. **Classification and readings.**
   - `classify_campaign` checks VOID first: exception, departure, missing library, inconsistent panel, then any false shared or library P1/P9/P10. Next comes NO-READING (P2 or P3 false) with six FAIL verdicts, `k = 0`, `k′` reported and the `shared_panel` cause. Then the class is chosen by `k`.
   - The readings are verbatim §7.4 and are checked against the frozen text.
   - S1/S2 use exact integers, are suppressed for NO-READING and VOID, and run S1 before S2.
   - The status phrase follows §7.11, and "(exit audit pending)" sits outside it.
   - A forbidden-word test runs over every reading class.
   - A VOID bundle omits the across-library payload, the matrices and the per-library scientific files.
5. **Generation and barrier.**
   - Target tables are written once and re-read with a hash check before each of the 720 fits.
   - The fitter receives only target tables, the grid and one library.
   - `_read_back_all` re-reads all 720 blind records before the first `_truth_diagnostics_from_result`, and a test asserts that order.
   - The ledger reserves each slot before dispatch, an exception consumes its slot, and exact equality is checked per scope and per column.
6. **Integrity sources.**
   - P9 build hashes are checked against `g43_constants.PROCESS_HASHES`, which itself matches the frozen text.
   - Roster, pairing and grid come from `FINAL_SEEDS` and the frozen grid.
   - Candidate provenance comes from re-read files compared against the constant roster.
   - Target tables are rebuilt from retained `observation_events` in the recompute.
   - P10 caps come from the constants and, in the recompute, from the frozen §9 table.
   - The only literal `True` is shared P1 (R2).
   - I found no check whose expected value derives from the input under test.
7. **Retention, bundle and recompute.**
   - The §10 layout is complete. Latent truth includes `daily_observed_cases` and `benchmark.n_agents`, and the A8 P3 recompute matches the source expressions at `outbreak_runner.py:453–456, 513–524` and `observation.py:277–329`.
   - Sealing removes write bits and calls `verify_bundle`.
   - `g43_recompute.py` imports only the standard library. It recomputes loss surfaces in the same summation order as `loss`, plus profiles, P1–P10, k, k′, m, m_ℓ, the triggers, the class and the reading.
   - The launcher refuses a non-empty directory, an existing exit marker and insufficient host disk.
   - Disk estimate: 1,001,048,576 bytes upper, measured on non-study seed 123. Builds are transient, one parent at a time.
8. **Licensing.** I found no path that changes science or produces a verdict the frozen text does not license.

**Mutation tests (`/tmp` copy):**
- M1, P5 changed from `≥` to `>`: killed.
- M3, one hash digit changed: killed.
- M4, the `states.conserved` P3 input dropped: killed.
- M2 and M5: survived individually, each because the other check covers it (R4).

1. Scope: OK
2. Frozen declaration: OK
3. Evaluator: OK
4. Classification, readings, S1/S2, phrase: OK
5. Generation and blind barrier: OK
6. Integrity sources: FLAG (R2 literal `True`; R4 test gap; both minor or note)
7. Retention, bundle, recompute, launcher: FLAG (R1 override; R3 and R7 notes)
8. Unlicensed verdicts or silent science changes: OK
