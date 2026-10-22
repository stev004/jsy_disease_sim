G35-B IMPLEMENTATION RE-REVIEW: PASS
Model: gpt-6-astra @ high; substituted under clarification 2 Item 3.

- **F1 — OK.** Predicate 9 now verifies report provenance for both arms: seed pairing, namespaces, replicate order, config/record/table bindings, 49/30-day durations, 53/34-date calendars, RNG fingerprints and candidate config hashes. Independent controls and checks: [g35b_design_study.py:959](/home/steven/jos-g37-rereview-20261022-clone/src/jersey_outbreak/g35b_design_study.py:959); join integration at lines 1817 and 2289.
- **F2 — OK.** Sample flags and k are recomputed from retained transmission events using unique identities and the inclusive survey-date cutoff. The fitter’s serosurvey inputs remain counts k and n. [g35b_design_study.py:2216](/home/steven/jos-g37-rereview-20261022-clone/src/jersey_outbreak/g35b_design_study.py:2216).
- **F3 — OK.** Agreement uses four non-null, equal offset-profile minimizers under the unchanged τ rule. This implements frozen §7.2(b); global selection and identification are disclosed separately. Predicate 4 and hit rules remain unchanged. [g35b_design_study.py:1202](/home/steven/jos-g37-rereview-20261022-clone/src/jersey_outbreak/g35b_design_study.py:1202).
- **F4 — OK.** `implemented_arms` lists B/i/ii/iii. The independent config digest matches committed bytes. `git diff 6ca5253 0c68982 -- configs` shows only the three added arm entries.
- **No regression — OK.** All changes serve F1–F4; no recovery-gate assertion is weakened. G35-B dry-run stdout is byte-identical to the previous-head planner’s output; historical counts are unchanged. `phase0_campaign.py` is byte-identical to main. Focused tests pass.

Reviewed head: `0c689825675aba8d414b6c7bd41951fc97aba6fc`. No unresolved findings or new departures identified within this bounded review.

The independent probes produced:

```text
                                                Previous  Corrected
F1 arm iii: candidate seed=-1                    True      False
F1 arm iii: candidate duration_days=999           True      False
F1 arm iii: both corruptions                     True      False
F2 empty events, all flags=True, k=400            True      False
F3 four agreeing offset profiles, global tie     False     True

Valid report provenance: ii 49/53=True; iii 30/34=True
Both arms reject each corrupted seed, namespace, run record,
RNG fingerprint, observation seed, table binding, replicate order,
candidate config hash and calendar.

F2 valid empty-event samples=True
F2 duplicate identity + inclusive cutoff + excluded later event=True, k=1
F3 global_tie=True; selected=None; reprofiled_offset=2
F3 offset-profile tie agreement=False
F3 differing offsets agreement=False
```

Commands and key outputs:

- Read the original review using `git show origin/main:docs/audits/2026-10-22-g37-implementation-review-astra-BLOCKED.md`; inspected the binding documents, full corrective diff and test diff with `git show`, `git diff`, `sed` and `nl`.
- `tail -n 35 /home/steven/jos-g37-mirror2.log` confirmed `MIRROR_RESULT=PASS SHA=0c689825675aba8d414b6c7bd41951fc97aba6fc`.
- `git merge-base --is-ancestor 6ca5253 0c68982`: exit 0.
- `git show HEAD:configs/calibration/v13_g35b_design_study.yaml | sha256sum`: `4259c45f01cf122521f6853dba5059415a0ca6317a02d3f883be18e3263105d0`, matching `CONFIG_SHA256`.
- Committed predeclaration SHA-256: `2e8358abd9e275a5cf04a58b4ad76313c10964f2da06d46cd0f8a7190733216e`.
- `git rev-parse` for `phase0_campaign.py` at HEAD, main and origin/main returned the same blob: `b790983edb63b62923a6103e5c8930d2fece2851`.
- `.venv/bin/python -B /tmp/g37-rereview-probes.py`: final run exit 0; also confirmed unchanged gate, hit-rule, fitting/objective and workload ASTs. [Probe script](/tmp/g37-rereview-probes.py), [final output](/tmp/g37-rereview-probes-final.log).
- Focused tests, with bytecode disabled and caches under `/tmp`: `uv run pytest tests/test_g35b_design_study.py -q` → **236 passed in 438.76s (0:07:18)**. [Test output](/tmp/g37-rereview-pytest.log).

All three authorized dry-runs exited 0:

```bash
uv run python -m jersey_outbreak.g35b_design_study dry-run --config configs/calibration/v13_g35b_design_study.yaml --predeclaration docs/research/v1_3/2026-10-22-g35b-predeclaration.md
uv run python -m jersey_outbreak.phase0_campaign dry-run --config configs/calibration/v13_phase0_synthetic.yaml --predeclaration docs/research/v1_3/2026-09-21-phase0-predeclaration.md
uv run python -m jersey_outbreak.phase0_campaign dry-run --config configs/calibration/v13_phase0b_synthetic.yaml --predeclaration docs/research/v1_3/2026-09-25-phase0b-predeclaration.md
```

| Profile | Cells | Latent calls | Transforms | Builds | Samples |
|---|---:|---:|---:|---:|---:|
| G35-B | 2,500 | 395 | 9,395 | 22 | 85 |
| Phase 0 | 198 | 59 | 599 | 8 | — |
| Phase 0b | 1,334 | 107 | 4,007 | 8 | — |

G35-B also retained 25,000 gate and 31,250 descriptive loss evaluations.

`git diff 6ca5253 0c68982 --stat`:

```text
 configs/calibration/v13_g35b_design_study.yaml |   3 +
 src/jersey_outbreak/g35b_constants.py          |   2 +
 src/jersey_outbreak/g35b_design_study.py       | 133 ++++++++++--------
 tests/test_g35b_design_study.py                | 183 ++++++++++++++++++++++---
 4 files changed, 244 insertions(+), 77 deletions(-)
```

Auditor tracked-file changes: none. No real build or simulation ran. Final `git diff --check`: exit 0, no output.

Final `git status --porcelain`: exit 0; stdout empty.