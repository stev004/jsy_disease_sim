PHASE-0B CODE REVIEW: BLOCKED

**Blocking findings**

1. The production P0-1 path does not use the new exact-decimal recovery values. [run_p01_campaign](/home/steven/jos-p0b-review-readonly/src/jersey_outbreak/phase0_campaign.py:2681) calls `join_truth_evaluation` without `config`, leaving `exact_estimate_truth` empty. Signed errors then fall back to converting simulator floats to strings. The endpoint test passes `config` directly, so it misses this path. Pass the validated config after blind-estimate persistence and test the production path’s decimal values.

2. The bundle omits declared per-target P0-1 predicate values. [evaluate_p01](/home/steven/jos-p0b-review-readonly/src/jersey_outbreak/phase0_campaign.py:2133) writes estimates, errors and identification to the CSV, then adds boundary data; it does not write each target’s tolerance hit, joint hit, tie and viability predicate values. Section 6 requires every per-target predicate value in the CSVs. Add those columns and check them against retained evidence.

3. P0-2 clause columns do not use the required `TRUE` / `FALSE` / `UNKNOWN` values. [P02TargetResult.as_dict](/home/steven/jos-p0b-review-readonly/src/jersey_outbreak/phase0_campaign.py:905) supplies booleans or `None`; the [CSV writer](/home/steven/jos-p0b-review-readonly/src/jersey_outbreak/phase0_campaign.py:3952) emits `True`, `False` and `null`. Serialize Phase-0b clause states explicitly, retaining null for the separate undefined estimate, error and \(E_i\) fields.

4. The `lineage` block omits the historical Phase-0 P0-2A, P0-2B and P0-3 PASS results required *inside* that block by §6. [PHASE0_LINEAGE](/home/steven/jos-p0b-review-readonly/src/jersey_outbreak/phase0_campaign.py:167) lacks them; [bundle publication](/home/steven/jos-p0b-review-readonly/src/jersey_outbreak/phase0_campaign.py:4006) places them at the summary root. Move the historical evidence into `lineage` and test the required block fields individually.

**Major findings**

- The Phase-0b config declares the [P0-2B and P0-3 grids](/home/steven/jos-p0b-review-readonly/configs/calibration/v13_phase0b_synthetic.yaml:142) as YAML numbers, although the frozen declaration says all grid values are decimal strings. Their validation uses numeric expected values. Convert these grid declarations and their independent constants to strings, parsing them before simulator use.
- [predeclaration.sha256](/home/steven/jos-p0b-review-readonly/src/jersey_outbreak/phase0_campaign.py:3908) names `predeclaration`, while Phase-0b copies the document as `predeclaration.md`. The digest is correct, but its named file does not exist in the bundle. Use the copied filename for Phase 0b.

**Acceptance decisions**

| Criterion | Decision |
|---|---|
| 1. Identity, scope, Phase-0 preservation | PASS. HEAD descends from `f64c586`; only the expected three files changed. I independently compared all **81/81** Phase-0 candidate config hashes against the base module. |
| 2. Frozen values and independent validation | BLOCKED by the remaining numeric grid declarations. The four recovery grids, seeds, IDs and three document digests are independently fixed and validated. |
| 3. Decimal recovery and aggregate predicates | BLOCKED by the production-path omission. Boundary counting has its own path. |
| 4. P0-2A/B and G29 | BLOCKED by clause-state publication. Grid sizes, offset-4 evaluation and tie handling otherwise follow the declared paths. |
| 5. P0-3 | PASS on code review: nine-cell design, fresh candidate seeds and six predicates are retained. |
| 6. Workload | PASS: planning and dispatch guards enforce 625/625/75/9 cells, 107 latent calls, 4,007 transforms and eight builds; measured totals are checked before publication. |
| 7. Bundle | BLOCKED by the missing CSV predicate values and incomplete lineage; the digest filename also needs correction. |
| 8. Tests | BLOCKED. The 52 focused tests pass, but the decimal test bypasses the production call, and bundle assertions accept the incomplete lineage and CSVs. The cold-recomputation test checks a retained P0-1 surface row and P0-2A row, not those missing fields. |
| 9. Other defects | The numeric grid encoding and digest filename are listed above. |

**Integrity-check inventory.** Config fields are compared with module profile constants; cross-campaign seeds with the other profile’s constants; predeclaration, G29 and owner-ruling bytes with independent digest constants. Grid completeness is checked against the validated profile; namespace evidence against returned result metadata and recomputed RNG fingerprints; blind records against re-read persisted content; planned and measured work against profile counts; retained tables against provenance digests; and `SHA256SUMS` against re-read bundle files with exact file coverage. The findings identify where those checks or their published evidence do not meet the frozen declaration.

**Reproduced evidence and limits.** Focused command: **52 passed**. Supplied director mirror: exit **0**, **462 passed, 4 skipped**, at this SHA; I did not rerun the full suite. The three frozen document digests match their module constants. `git diff --check` passed. This was code review with mocked tests only; no campaign or real simulator/observation API was run.

Final SHA: `84228b66aa6adcd0bb4a1f55e8651bb1b1edbd8b`. Initial and final `git status --porcelain` were empty. No clone files were edited.