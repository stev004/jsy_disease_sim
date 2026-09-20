TAIL REVIEW: BLOCKED

Reviewed target: `d3f4d6434aa2c0158b8d277f1cf61163ee2f8c19`

Pinned comparison base: `6eb05c2dfa88ff1818ec210f76be93c2fd5c7e9f`

Review date: 2026-09-20

## Findings

### MAJOR 1 — DATA-10 corrected content collides with the pre-correction immutable M8 artifact ID

`daily_high_risk.parquet` changes as intended, but the M8 `artifact_bundle_hash` is still
computed only from scenario, latent, and episode hashes
(`src/jersey_outbreak/travel.py:2645`). The new high-risk hash is only a diagnostics entry
(`travel.py:2732`). The artifact ID continues to use the unchanged bundle hash
(`travel_artifacts.py:338`), and an existing directory is returned without comparing the
corrected high-risk result (`travel_artifacts.py:345-349`).

Independent 30-day seed-101 A/B:

```text
base high_risk_detection_total: 2
head high_risk_detection_total: 3
base artifact_bundle: 20a031f86675f263db4228cea0dfb82372780573c53f9d6d678b743c72245944
head artifact_bundle: 20a031f86675f263db4228cea0dfb82372780573c53f9d6d678b743c72245944
head high_risk_epidemic diagnostic hash: 1a6cb8ead0c3418c30572200ca8a4c3708989ca6d550b844b6120ec4a9ed42f4
```

Base artifact followed by head write to the same output root, verbatim:

```text
BASE
{
  "artifact_bundle_hash": "20a031f86675f263db4228cea0dfb82372780573c53f9d6d678b743c72245944",
  "artifact_id": "jos-travel-m8-ci-seed-101-20a031f86675",
  "computed_detection_total": 2,
  "persisted_detection_total": 2,
  "returned_manifest_schema_version": "2.2"
}

HEAD
{
  "artifact_bundle_hash": "20a031f86675f263db4228cea0dfb82372780573c53f9d6d678b743c72245944",
  "artifact_id": "jos-travel-m8-ci-seed-101-20a031f86675",
  "computed_detection_total": 3,
  "persisted_detection_total": 2,
  "returned_manifest_schema_version": "2.2"
}
```

Therefore the declared M8 schema 2.3 correction can silently return the old schema-2.2
artifact and old scientific table. The schema bump and new diagnostics hash do not establish a
new immutable identity.

### MAJOR 2 — DATA-8/9 computes the perturbed surfaces but reports the wrong argmin shifts

The implementation has a real beta × nuisance grid and minimizes nuisance at each beta. However,
the reported `argmin_shift` uses the global profiled argmin over factors `(0.5, 1.0)`
(`calibration.py:586-612`). Because factor 1.0 contains the exact data-generating baseline at the
truth beta, its objective is zero and dominates the profile. This is not the audit authority's
requested beta re-minimization *under the altered nuisance*.

Independent real-model run, seed 125, 8 days, beta grid `(0.04, 0.08, 0.12)`:

```text
ascertainment_factor_argmins: {"0.5": 0.12, "1.0": 0.08}
route_weights_factor_argmins: {"0.5": 0.12, "1.0": 0.08}
reported_argmin_shift:
  ascertainment_beta: 0.08
  ascertainment_beta_delta_from_training: 0.0
  route_weights_beta: 0.08
  route_weights_beta_delta_from_training: 0.0
```

The nuisance perturbation demonstrably moves both beta argmins from 0.08 to 0.12, but the published
diagnostic says neither moved. The new test only checks that the `argmin_shift` key exists; its
synthetic helper test does not assert the real-model perturbed shift.

The held-out gate itself is falsifiable and passed review: the one-day degenerate case has recovered
beta 0.04 within tolerance of truth 0.06 and objective zero, but both beta values tie, so head status
is `failed`. The same case on base returned `passed`.

### MAJOR 3 — The pinned base-to-head integration diff is not tail-scoped

The task requires every hunk from pinned base `6eb05c2` to trace to the six findings/ruling or their
tests/docs. It does not. The ancestry includes G27/VHD trail and state commits plus housekeeping
commit `7b22d00`, which deletes 44 P4 checkpoint files.

Verbatim:

```text
$ git diff --shortstat 6eb05c2...HEAD
 70 files changed, 1191 insertions(+), 3384557 deletions(-)

$ git diff --shortstat 6eb05c2...HEAD -- . ':(exclude).replicates-in-progress/**'
 26 files changed, 1191 insertions(+), 121 deletions(-)

$ git log --oneline --reverse 6eb05c2..HEAD
eac7f76 trail: g27-merge — G27 EXECUTED on Steven's chat instruction: git merge --no-ff
fbf4678 trail: vhd-compacted — Steven compacted the Ubuntu VHD via elevated diskpart: 29.1
2ae6083 state: G27 merged (6eb05c2), GATES/FRONTIER reconciled
7b22d00 housekeeping: remove orphaned p4-validation-r8 checkpoints (run completed 2026-09-04; RUN.md sanctioned)
207680c trail: tail-run-start — V1.2.1 tail: three parallel luna@xhigh units launched off 6e
dbb0710 subgrp: canonical covid_vaccination_subgroups (age-band x dose, ruling 4) + dictionary rows + documented exclusions
dccdae9 datafix: DATA-7 observed-stamp fail-closed, DATA-10 arrival-test strata fix + M8 diagnostics bump, DISEASE-10 tri-state agreement + RNG key declarations, CROSS-3 erratum
99e6e62 calib: DATA-8 falsifiable held-out gate, DATA-9 real 2-D beta x nuisance profile, beta=0 delay disclosure (calibration schema bump)
5081ae9 integ: merge v121/tail-subgrp
6a146b1 integ: merge v121/tail-datafix
d3f4d64 integ: merge v121/tail-calib
```

The non-checkpoint unrelated hunks include `.claude/FRONTIER.md`, `.claude/GATES.md`, and
`.claude/decisions.tsv`. The housekeeping may be separately sanctioned, but it does not satisfy this
review's explicit tail-scope predicate.

Note: `origin/main` had advanced to `574f726` and contains the reviewed integration by review time,
so literal `git diff origin/main...HEAD` is empty. I used the exact pinned baseline required by the
brief.

### MINOR 1 — DISEASE-10's declared event-key contract is still not linked “by construction”

`EVENT_STREAM_KEY_INPUTS` is consumed only by the diagnostics in `observation.py:390`.
`event_stream_seed()` separately hand-codes `key_parts` in `observation_scheduler.py:75-85` and
does not reference the constant. The new test compares diagnostics to another hard-coded list; it
does not prove that the declaration equals the fields/order actually hashed. The declaration is
currently correct by inspection, but the audit's required single-source anti-drift property is not
implemented.

Verbatim symbol use:

```text
src/jersey_outbreak/observation_scheduler.py:19:EVENT_STREAM_KEY_INPUTS: tuple[str, ...] = (
src/jersey_outbreak/observation_scheduler.py:72:def event_stream_seed(stream_seed: int, event: Mapping[str, Any]) -> int:
src/jersey_outbreak/observation_scheduler.py:75:    key_parts = (
src/jersey_outbreak/observation_scheduler.py:88:        *key_parts,
src/jersey_outbreak/observation.py:390:            "event_key_inputs": list(EVENT_STREAM_KEY_INPUTS),
```

## Evidence that passed

### Subgroup source verification

I independently opened the frozen PDF (SHA-256
`c8a04fbfa06d9ed23dc71c7a5f46e2914dafd7484b80f104cc6550847c7848f8`), extracted PDF page 8,
and rendered PDF page 24 at 1489×2105 for visual comparison.

Twelve checked canonical cells, verbatim:

```text
CELL ('80_plus', 'dose_1') actual 97 expected 97 PASS True
CELL ('60_to_64', 'dose_1') actual 96 expected 96 PASS True
CELL ('40_to_49', 'dose_1') actual 89 expected 89 PASS True
CELL ('18_to_29', 'dose_1') actual 81 expected 81 PASS True
CELL ('5_to_11', 'dose_1') actual 12 expected 12 PASS True
CELL ('80_plus', 'dose_1_and_2') actual 97 expected 97 PASS True
CELL ('70_to_74', 'dose_1_and_2') actual 96 expected 96 PASS True
CELL ('55_to_59', 'dose_1_and_2') actual 93 expected 93 PASS True
CELL ('30_to_39', 'dose_1_and_2') actual 82 expected 82 PASS True
CELL ('12_to_15', 'dose_1_and_2') actual 52 expected 52 PASS True
CELL ('5_to_11', 'dose_1_and_2') actual 10 expected 10 PASS True
CELL ('all', 'dose_1_and_2') actual 78 expected 78 PASS True
```

Excluded source percentage cells were also checked: Table 2 `50-59=93`, `65-79=96`, and
`all=82`; Table 5 `0-4=1`. All are absent for the documented denominator-band reasons.

There is no suppressed selected age×dose percentage in either cited source table: all 22 selected
cells are published integers and the built table has `SELECTED_SUPPRESSED_CELLS 0`. Therefore a
literal suppressed selected-cell spot check is impossible without inventing one. I instead checked
the source's `NA` cell for Table 2, age 5–11, “days until half”; it is outside the selected
vaccination-percentage measures and is not ingested. The dictionary truthfully says no suppression
marker was observed in the cited percentage cells.

Denominator and citation checks:

```text
NON_TOTAL_RANGES [('5_to_11', 5, 11), ('12_to_15', 12, 15), ('16_to_17', 16, 17), ('18_to_29', 18, 29), ('30_to_39', 30, 39), ('40_to_49', 40, 49), ('50_to_54', 50, 54), ('55_to_59', 55, 59), ('60_to_64', 60, 64), ('65_to_69', 65, 69), ('70_to_74', 70, 74), ('75_to_79', 75, 79), ('80_plus', 80, None)]
TOTAL_AND_NONOVERLAP True
DICTIONARY_ROWS 2 UNCITED_NON_UNKNOWN []
```

Independent full canonical rebuild:

```text
BUILD_STATUS passed
BUILT_FILES 27 COMMITTED_FILES 27 NAMESETS_EQUAL True
BYTE_DIFFERENCES []
SUBGROUP_SHA256 7a36bc5650f4e4c3fdf64373fa06a9f97b4c772b19a7a17348aa349f67d5cacd
```

### Scientific identity A/B

Both sides independently regenerated the seed-123 CI M2/M3 parents, then generated M4 and ran 30
days for seeds 101–103. Seed 101 also ran `m8_arrival_testing.yaml` for 30 days.

```text
seed 101 M4    base=head 7b4f3ab765ede76749152f76b61dd2e40e415347bbf7a56607d04de610e7195d
seed 101 latent base=head 106e5e4a4a7f520e8185d43c1f71eecec725d1cbffdbbc29e86b6f3b916cfc51
seed 102 M4    base=head a278202093567dac775653f4c31669e98274cff0a66383b32a7741f1c8b4fbd4
seed 102 latent base=head 58dc87b6ae1c6f280447d2086d33d0ec3a8f69ce0672d22746645995c7233d4a
seed 103 M4    base=head ee73a9c11cc3943fbea83f81ff412e1607e554f5e8819e9e90ef463f7a298f5c
seed 103 latent base=head 3c94d4fa08aee9b1bdef072cd2c9cef0696894389f379f60db0e24222588f333

M8 M4             base=head 7b4f3ab765ede76749152f76b61dd2e40e415347bbf7a56607d04de610e7195d
M8 latent_outcome base=head 68ce488367cec12459b3cd53cede5a6629288386abb4400a3723e02d460dba8d
M8 travel_config  base=head d0c74696c116fff69e378c7a820ff341ffa8fe9565fb460bb7571728b6a61d07
```

The intended changed surface is the DATA-10 high-risk diagnostics/table. It is declared with M8
artifact schema `2.3` and diagnostics schema `1.1`, but MAJOR 1 shows that this change is not bound
to artifact identity. Calibration changes are declared by config schema `1.2` and manifest schema
`1.3`; calibration artifact IDs use the changed calibration logical hash.

DATA-7 fail-closed check, verbatim:

```text
OVERRIDE_STATUS scenario_assumption
OVERRIDE_DERIVATION Scenario override 2000000 departs from the canonical M1 2025 air total 720842; the source notes values are rounded to the nearest thousand where applicable.
MISSING_CANONICAL ValueError invalid travel configuration /tmp/tmpwpvh9z10/travel.yaml: cannot read Milestone 1 canonical manifests: [Errno 2] No such file or directory: '/tmp/tmpwpvh9z10/data/processed/table_manifest.json'
```

### Calibration memoization and failing-first evidence

The latent memoization is in scope: the required 2-D surface introduces exact duplicate latent runs,
especially nuisance factor 1.0. Its cache is local to one calibration call; seed, beta, and sorted
route multipliers cover every run control that varies inside that call. Independent base (uncached)
versus head (cached) comparison produced byte-identical `trial_rows`, best parameters, held-out
components, and latent hashes:

```text
best_parameters: {"transmission_beta": 0.08}
target_latent_hash: e02ff337933ecfee423a59a4972fb0647dd6451a644043c0bcdaa80ec2858d0f
heldout_latent_hash: 82a419fcde02935040dc23cd525bafad67bf815e5887c39bb07aae2ed7ee34d6
heldout objective: 0.0
trial objectives: [7064.0, 0.0, 16300.0]
```

Failing-first was reproduced against base source with head tests:

```text
tests/test_scientific_corrections_datafix.py: 8 failed
new subgroup tests: 2 failed
calibration held-out and delay-disclosure tests: 2 failed
beta-profile helper test: collection failed because base has no _profile_beta_nuisance
```

The same focused set on head:

```text
..............                                                           [100%]
14 passed, 6 warnings in 10.26s
```

### Head gates

Full pytest, verbatim:

```text
=========== 409 passed, 4 skipped, 15 warnings in 788.15s (0:13:08) ============
```

The named provenance test did not flake on head. In a clean sparse base clone it passed once as a
file and then passed 10/10 isolated repetitions, so I could not independently reproduce the known
intermittent failure in this review. Repository trail commit `49bbd50` records four prior base and
branch reproductions (“second job RUNNING at assert”). No failure was disregarded in the head run.

```text
$ uv run ruff check .
All checks passed!

$ uv run ruff format --check .
247 files already formatted

$ uv run mypy --ignore-missing-imports [exact 15-module .github/workflows/ci.yml list]
Success: no issues found in 15 source files
```

For completeness, the broader 29-module README command is red on two pre-existing schema assignment
errors (`observation_schemas.py:167`, `outbreak_schemas.py:205`); the same two errors occur at the
pinned base. The exact CI-pinned mypy gate requested here is green.

## Diff accounting

Tail implementation excluding the unrelated checkpoint ancestry:

```text
26 files changed, 1191 insertions(+), 121 deletions(-)
```

The three unit commits otherwise trace as follows:

- `dbb0710`: Ruling 4 subgroup table, schema, dictionary, generated canonical outputs, tests.
- `dccdae9`: DATA-7, DATA-10, DISEASE-10, M8 schema/diagnostics, CROSS-3 erratum, tests.
- `99e6e62`: DATA-8/9 held-out/profile/disclosure, calibration schema, docs, tests, exact local memoization.

No repository source file was modified during this review; no push, full/scaled run, or ensemble was
performed.
