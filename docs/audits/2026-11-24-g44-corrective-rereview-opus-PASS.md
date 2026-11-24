*Filed verbatim by the director (Claude Opus 5.5) from the independent re-review subagent's final message: fresh Claude Opus 5.5 @ high (frozen G43 §12 seat 4; disclosed: same model family as the director and the first reviewer; author of none of the code); brief docs/runs/2026-11-24-g44-rereview-brief.md.txt; reviewed head 73978427f5dabff70dde4a0a8b06aab372df7f4c; 153,685 tokens.*

---

Claude Opus 5.5 (claude-opus-5-5) @ high

JOS G43 IMPLEMENTATION RE-REVIEW: PASS

**Basis.** I cloned the review clone to `/tmp/jos-g44-rereview-20261124`, detached at `73978427f5dabff70dde4a0a8b06aab372df7f4c`. A second copy, `/tmp/jos-g44-rr-old-20261124`, is at `c723f71` with the new test file copied in. Mutations and probes ran in `/tmp/jos-g44-rr-mut-20261124`. `c723f71` is an ancestor, and exactly one commit separates the two heads. The frozen predeclaration at `fc16adc` hashes to `67c3c7c0…1094` and is byte-identical at HEAD. I did not edit the clone or the repo, build or run any study seed, or run the full suite.

## Findings

**N1 — MINOR — `src/jersey_outbreak/g43_multilibrary.py:2279` (with `_launch_checks`, ~2030–2050)**
- **Rule:** §12 line 701: "A software exception during the campaign … makes the campaign VOID." §12 line 682: "The launcher refuses to start if an exit marker exists."
- **Defect:** the intact-path `write_marker(...)` runs inside the `try`, after `_seal_bundle` has already sealed an intact bundle. `_launch_checks` never checks that the marker location can be written.
- **Failure scenario:** `--exit-marker` points into a read-only directory, or one the user cannot write to. The full 45,020-transform campaign completes and seals as intact. Then `marker.open("xb")` raises `PermissionError`. The `BaseException` handler deletes the scientific outputs and re-seals the bundle as VOID. That converts a completed campaign into an unrecoverable VOID, which needs a new owner-ruled text before any rerun. It gains nothing: the VOID does not stop a second launch, because the marker still does not exist.
- **Why it does not block:** with the default path (`output_dir.parent`), the parent is normally where the output directory was created, so the scenario needs an unusual launch.
- **Smallest fix:** in `_launch_checks`, refuse unless `marker.parent` exists and is writable (`os.access(marker.parent, os.W_OK)`). Alternatively, write the intact marker outside the `try`, so a marker failure is reported without discarding a sealed intact bundle.

**N2 — NOTE — `g43_multilibrary.py:2237–2243, 2280–2295` (R7 edge windows)**
- **Window 1:** an interrupt can arrive inside `write_marker` after the marker bytes `{"software_status":"PASS"}` are written but before `with` exits. The handler then VOIDs the bundle, and `write_marker("VOID")` fails with `FileExistsError`. The result is a VOID bundle with a PASS marker. The original exception is re-raised with a note.
- **Window 2:** a second interrupt can arrive in the instructions between entering the handler and `output_dir.chmod`. That leaves the sealed PASS bundle intact-looking and the marker saying VOID, and the exception is still re-raised.
- **Assessment:** the bundle stays authoritative, the marker's content is not governed by the frozen text, and the original exception is never masked. Both windows are at most a few bytecodes wide, and window 2 needs two interrupts.
- **Possible fix:** write the marker to a temp file and `os.link` it into place, and/or note the windows in the launcher brief.

**N3 — NOTE — test coverage (from mutation)**
- M10: removing the new "exit marker must be outside the bundle directory" refusal survives every launch test. That check has no test.
- M4: replacing `all(row.complete …)` in `IntegrityEvidence` with a literal `True` survives. This is safe, because `evaluate_shared_panel` (line 937) independently requires `row.complete is True` for every row. But it means the evidence-level conjunction is not tested on its own.
- **Smallest fix:** add one launch test with `--exit-marker <output_dir>/x.exit`.

**N4 — NOTE — `g43_multilibrary.py:1732`, `tests/test_g43_multilibrary.py:1808–1818`**
- **Rule:** §10 line 637: "the observation diagnostics keys used by P3".
- **Observation:** the corrective adds `"status"` to the retained `observation_diagnostics`. After the director's fix, no check uses it. The test helper `_incomplete_target_result` keeps an `observation_diagnostics` parameter that is now unused.
- **Assessment:** retaining an extra key is harmless. `status` is also already inside `truth_diagnostics.raw_values`, and the recompute ignores it. It is leftover from the removed condition.
- **Fix:** drop it, or leave it with a one-line note.

## Per-finding verification

Named regressions were run on both heads with the same test file:
- `c723f71`: 14 failed, 7 passed.
- `7397842`: 21 passed.

| Finding | Correction | On `c723f71` | On `7397842` | Mutation |
|---|---|---|---|---|
| **R1** | `upper < default_upper` is refused, and the floor is taken from `frozen.EXPLORATORY_BUNDLE_UPPER_BYTES + frozen.PARENT_BUILD_DISK_BYTES` | override 0 and `default−1` fail | all pass | M1 (floor removed) killed, 2 failures |
| **R2** (evaluator and recompute) | per-target completion comes from returned metadata | latent_29, latent_empty and dates_33 fail in both | all pass | see below |
| **R3** | the marker is written on both intact and VOID exits, and a sibling launch is refused | marker and sibling tests fail | pass | M9 (intact `write_marker` removed) killed |
| **R4** | test gap only | `table_body` passes (expected, old code was sound) | passes | M6 (the `record["table_sha256"]` check from the first review's M2 removed) now killed in both evaluator-side and recompute-side tests |
| **R5** | stale comment removed | comment test fails | passes | — |
| **R7** | `except BaseException` with best-effort VOID sealing | both `BaseException` tests and the finish-failure test fail | pass | M7 (`except Exception`) and M8 (re-raise condition removed) both killed |

R2 detail:
- **What it checks:** 30 latent rows, `duration_days == 30`, the 34 frozen dates on the table, and the 34 observed dates. The evaluator takes its expected values from `frozen.LATENT_DAYS` and the module date constants. The recompute uses its own stdlib `LATENT_DAYS`/`DATES`.
- **Real-run compatibility:** I checked that real runs would satisfy this. `observation.py:167` derives the observed dates from the latent first and last date plus a four-day tail. So 34 observed dates means exactly 30 `daily_epidemic` rows, and both are lists of dicts with a `"date"` key (`outbreak_runner.py:345–351`, `observation.py:217–227`).
- **Mutations:** M2 (latent length check removed) killed; M3 (observed-date check removed) killed; M5 (recompute length check removed) killed. M4 survived for the benign reason given in N3.

R7 detail:
- The original exception is re-raised by identity: the tests assert `caught.value is failure`.
- Failures during recovery are attached as notes, never substituted for the original.
- Exceptions that are not `Exception` subclasses (`KeyboardInterrupt`, `SystemExit`) are always re-raised.
- `_discard_scientific_outputs` deletes `SHA256SUMS` first, so a recovery that fails part-way leaves a bundle that `verify_bundle` rejects. The finish-failure test confirms this.

**Disclosure (director removed `status == "passed"`).** The removal is correct. `observation.py:311` sets `"status": "passed" if no_report_before_infection else "failed"`, and that flag is one of P3's four inputs. Keeping the condition under P1 would have turned a P3 failure into VOID, against A3 and §7.3 rows 1–2. My probes confirm that the result is now NO-READING:
- **Evaluator:** each P3 input made false on its own (natural-history chronology, `states.conserved`, `no_report_before_infection` with status "failed" and one chronology violation, latent conservation) gives `IntactCampaign`, `NO-READING`, `k = 0` and six FAIL verdicts.
- **Recompute (`_recompute_panel`):** with corrupted chronology rows and with `daily_epidemic` conservation broken, plus status "failed", the result is P1 = True, P3 = False, P9 = True.
- **Recompute, flag only:** changing only the retained `no_report_before_infection` flag leaves P3 True, because the recompute rebuilds it from `observation_events`. The later consistency check (`g43_recompute.py:1063`) would then raise a discrepancy. This is pre-existing design, not a departure.

**No other change.** Every diff hunk is in the four expected files. `classify_campaign`, `evaluate_shared_panel`, the P2/P3 condition functions, the thresholds, the seeds, the readings, S1/S2 and the status phrase are untouched. The new `complete` value is always a Python `bool`. The recompute's `if not latent_days: p3 = False; continue` path happens only when `complete` is already false, so the result is VOID and the P3 setting has no effect.

## Checks

1. Scope: OK. Only four `M` entries in the expected paths; no protected module, config or fixture touched.
2. R1, R2, R3, R4, R5, R7 corrected; regressions fail on `c723f71` and pass on `7397842`: OK (R4 as a test gap, confirmed by mutation).
3. No new departure in the partition or the VOID → NO-READING → class precedence; P3-only failures stay NO-READING in both evaluator and recompute; expected values come from frozen constants: OK.
4. R7 path: OK. The original exception is never masked, non-`Exception` interrupts are re-raised, and a failed recovery leaves a bundle that fails verification. The marker is outside the bundle and written only after launch checks pass (asserted for nonempty and disk refusals). Edge windows in N2, launch-time marker writability in N1.
5. Dry-run counts: OK. 92 builds / 1,820 latent calls / 45,020 observation transforms; 75,000 gate / 375,000 descriptive loss evaluations; 120 gate / 600 descriptive blind records; `ci`, 30 latent days, 34 dates.
