G35-B IMPLEMENTATION REVIEW: BLOCKED
Model: gpt-6-astra @ high.

Step 7 reviewer: gpt-6-astra @ high, substituted under clarification 2 Item 3 because the Opus CLI was unauthenticated. Prior-attempt token count was not supplied.

Reviewed immutable head `6ca52533ee27be51f2cfd06d8b2c00d887d57913`. **Three BLOCKER findings and one MINOR finding. Return the implementation to the executor before step 8.**

1. **Frozen numbers — OK.** Grids, truths, tolerances, limits, seeds, namespaces, H/T, survey design and caps match. All 66 M2/M3/M4 hashes match the frozen table.
2. **Objective — OK.** Report loss preserves Phase-0b arithmetic; generalized R/T, Anscombe transform, augmented weight, profiles and recovery tie rules match.
3. **Predicates — F1, F2.** Integer thresholds, Decimal endpoints, separate predicate 8 and workload caps match; predicate 9 is incomplete.
4. **Blind boundary and ordering — OK.** All-arm generation, blind fitting and blind-record read-back precede joins. Serosurvey observation reads latent events, but its fitter receives only the declared observations. Descriptives do not feed recovery predicates.
5. **Arm specifics — F3.** Sharing, replicate order, nesting, median, 49-day construction, sampling bytes and unique-identity counting match; offset-agreement descriptives do not.
6. **Outcome text — OK.** §7.4/A8 readings, multiplicity text, A9 phrases and verdict lines match. Exception handling suppresses readings; established scientific FAIL results remain recorded. Real-data fitting remains STOPPED.
7. **Bundle — F2.** Committed input digests, corrected ridge binding, ledger, retained tables, lineage, separate directories, SHA256SUMS and sealing are implemented; sample integrity lacks an independent check.
8. **Tests — F1–F3.** Real constructors and mocked execution exercise substantial production paths. Missing provenance cases escape coverage; one test encodes F3. No earlier numerical or provenance assertion was weakened between `aafbbb7` and HEAD.
9. **Protected contracts — OK.** Only the four declared implementation files differ from `main`; protected modules are unchanged. Both historical dry-runs retain their exact counts.

**F1 — BLOCKER: predicate 9 does not verify complete report provenance in arms (ii) and (iii).**

Arm (ii)’s `provenance_verified` expression checks table calendars and latent durations, but omits candidate seed pairing, observation namespaces, replicate order and returned/config-record bindings. See [g35b_design_study.py:1800](/home/steven/jos-g37-review-20261022-clone/src/jersey_outbreak/g35b_design_study.py:1800).

Arm (iii) calls only `_serosurvey_provenance_verified`; it never incorporates B’s report-provenance verification. See [g35b_design_study.py:2159](/home/steven/jos-g37-review-20261022-clone/src/jersey_outbreak/g35b_design_study.py:2159) and [g35b_design_study.py:2270](/home/steven/jos-g37-review-20261022-clone/src/jersey_outbreak/g35b_design_study.py:2270).

A read-only, in-memory probe returned `True` from arm (iii)’s checker with absent report provenance and candidate metadata containing `duration_days=999` and `seed=-1`. Generation-time checks do not make this later predicate a complete verification of its retained inputs. Frozen §7.1 predicate 9 requires those inputs to match independently frozen controls.

The U5 corruption regressions cover B and (i), leaving these corresponding cases uncovered: [test_g35b_design_study.py:2254](/home/steven/jos-g37-review-20261022-clone/tests/test_g35b_design_study.py:2254).

**F2 — BLOCKER: serosurvey infection flags are verified against the same sample record.**

The checker validates `k == sum(observation.ever_infected)`, but never verifies those flags against the sampled residents’ infection histories. See [g35b_design_study.py:2203](/home/steven/jos-g37-review-20261022-clone/src/jersey_outbreak/g35b_design_study.py:2203). Sample persistence likewise compares retained bytes with the same generated sample representation: [g35b_design_study.py:2237](/home/steven/jos-g37-review-20261022-clone/src/jersey_outbreak/g35b_design_study.py:2237).

The isolated probe produced:

```text
Original empty-event samples: True
Changed only sampled infection flags and k: True
Independent source: target transmission-event counts = [0]
```

All 400 target flags were changed to `True`, with `k=400`, while the independent latent events remained empty. The provenance checker still accepted them. This violates the DIRECTOR’s independent-source requirement. Verify sampled statuses against the corresponding latent event evidence after the blind barrier; retain the correct existing observation/fitter separation.

**F3 — BLOCKER: arm-(i) offset descriptives incorrectly depend on global uniqueness.**

`batch_offset_agreement()` rejects every globally tied fit. The reported `selected_offset` also becomes null whenever the global selected cell is null. See [g35b_design_study.py:1195](/home/steven/jos-g37-review-20261022-clone/src/jersey_outbreak/g35b_design_study.py:1195) and [g35b_design_study.py:1388](/home/steven/jos-g37-review-20261022-clone/src/jersey_outbreak/g35b_design_study.py:1388).

Frozen §7.2(b) requests **re-profiled offsets and agreement of those offsets**. A nuisance-dimension tie can coexist with a unique, identified offset-profile minimum. A pure four-cell fixture confirmed:

```text
global_tie = True selected = None
offset profile: minimum at 2; numerical_tie=False; identified=True
four identical uniquely minimized offset profiles: agreement = False
```

Thus four agreeing offset profiles are reported as non-agreement. The test explicitly encodes this additional rule: [test_g35b_design_study.py:889](/home/steven/jos-g37-review-20261022-clone/tests/test_g35b_design_study.py:889). Derive these descriptives from the offset profiles while preserving the declared global-tie recovery failure.

**F4 — MINOR: implementation metadata still declares only B implemented.**

The final config lists `implemented_arms: [B]`, and strict validation requires that stale value, although `run_all_arms` executes all four arms. See [v13_g35b_design_study.yaml:335](/home/steven/jos-g37-review-20261022-clone/configs/calibration/v13_g35b_design_study.yaml:335) and [g35b_design_study.py:169](/home/steven/jos-g37-review-20261022-clone/src/jersey_outbreak/g35b_design_study.py:169). The retained implementation metadata should describe U1–U5 accurately.

**Commands and key outputs**

- `git rev-parse HEAD origin/codex/g35b-design-study`: both returned the requested full SHA.
- `git show HEAD:docs/research/v1_3/2026-10-22-g35b-predeclaration.md | sha256sum`:

  ```text
  2e8358abd9e275a5cf04a58b4ad76313c10964f2da06d46cd0f8a7190733216e  -
  ```

- Read-only `git show origin/main:<path>` reads covered clarification 2 and all five unit reports and acceptance logs. `nl`, `sed` and `rg` inspections covered the binding documents, implementation, tests and imported helpers.
- A read-only Python comparison of the frozen §8 table against the constants returned: `all 22 seeds / 66 hashes match`. Committed-byte hashing confirmed all seven expected input digests, including binding ridge digest `8cf4c76612434cbd90c5de4ca9dfd1326422b94a72bd4a63ccff71e95f34908a`.
- `git log -p aafbbb7..HEAD -- tests/`: earlier assertion changes only replaced unimplemented-arm checks and renamed the execute-argument test.
- Focused test command, with bytecode disabled and caches directed to `/tmp`:

  ```text
  uv run pytest tests/test_g35b_design_study.py -q
  224 passed in 368.22s (0:06:08)
  ```

  [Retained test output](/tmp/g37-review-pytest.log).

- Authorized dry-runs, all exit 0:

  ```bash
  uv run python -m jersey_outbreak.g35b_design_study dry-run --config configs/calibration/v13_g35b_design_study.yaml --predeclaration docs/research/v1_3/2026-10-22-g35b-predeclaration.md
  uv run python -m jersey_outbreak.phase0_campaign dry-run --config configs/calibration/v13_phase0_synthetic.yaml --predeclaration docs/research/v1_3/2026-09-21-phase0-predeclaration.md
  uv run python -m jersey_outbreak.phase0_campaign dry-run --config configs/calibration/v13_phase0b_synthetic.yaml --predeclaration docs/research/v1_3/2026-09-25-phase0b-predeclaration.md
  ```

  | Profile | Cells | Latent calls | Transforms | Builds | Serosurvey samples |
  |---|---:|---:|---:|---:|---:|
  | G35-B | 2,500 | 395 | 9,395 | 22 | 85 |
  | Phase 0 | 198 | 59 | 599 | 8 | — |
  | Phase 0b | 1,334 | 107 | 4,007 | 8 | — |

  G35-B also reported `25,000` gate and `31,250` descriptive loss evaluations, with all per-arm caps matching.

- Read-only `.venv/bin/python -B -` probes exercised the provenance checker and pure offset-profile functions, producing the outputs quoted in F1–F3. No build or simulation ran.
- `git rev-parse HEAD:src/jersey_outbreak/phase0_campaign.py main:src/jersey_outbreak/phase0_campaign.py origin/main:src/jersey_outbreak/phase0_campaign.py`: all three blobs were `b790983edb63b62923a6103e5c8930d2fece2851`.
- `git diff --stat origin/main HEAD -- src configs tests scripts`:

  ```text
   configs/calibration/v13_g35b_design_study.yaml |  347 +++
   src/jersey_outbreak/g35b_constants.py          |  177 ++
   src/jersey_outbreak/g35b_design_study.py       | 2973 ++++++++++++++++++++++++
   tests/test_g35b_design_study.py                | 2855 +++++++++++++++++++++++
   4 files changed, 6352 insertions(+)
  ```

- `git diff --check`: exit 0, no output. Auditor changes: none.

Final `git status --porcelain`: exit 0; stdout empty.

```text
```