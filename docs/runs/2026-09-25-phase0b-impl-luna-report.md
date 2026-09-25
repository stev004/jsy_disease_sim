**Verdict: Implementation complete; no campaign arms run.** No scientific status is assigned.

The Phase-0b profile is implemented in the existing harness, with shared scoring and orchestration. The Phase-0 test file and frozen documents were not changed. Worktree: `codex/v13-p0b-implementation`, HEAD `f64c586444ffb5788d90ae3b269cef0469f6c0dd`; no commit or push.

### Acceptance evidence

1. **Phase 0 remains unchanged.** Its dry-run reported **198 cells, 59 latent calls, 599 transforms, 8 builds**. All 42 existing Phase-0 tests passed unmodified. The base-versus-head comparison, importing the base module from `git show` without checkout or stash, found the Phase-0 config and blind-estimate hash families byte-identical: 81/81/27/9 config hashes and 5/5/5 blind-estimate hashes. Overall comparison: `phase0_hash_families_byte_identical: true`.

2. **Phase-0b declaration validation.** The new config declares grids, tolerances, and bias limits as decimal strings. Validation checks values and seeds against independent profile constants, including cross-campaign disjointness. The dry-run verified the predeclaration SHA `ec8df646…f257451`, G29 ruling SHA `06e49aaa…1eb70c`, and owner-ruling SHA `ea15ea55…a1f98a39`; all three were verified.

3. **Phase-0b dry-run counts.** It reported P0-1/P0-2A/P0-2B/P0-3 grid sizes **625/625/75/9** (1,334 total), **80/0/0/27** latent calls (107 total), **1,880/1,875/225/27** transforms (4,007 total), and 8 builds. Implemented counts matched planned counts.

4–6. **Shared arm logic and regressions.** Focused tests cover exact-decimal recovery endpoints and bias cancellation, independently computed boundary counts, separate P0-2 detection clauses including offset 4 and G29 tie states, and the unchanged nine-cell P0-3 design on Phase-0b seeds.

7. **Mocked orchestration and bundle.** The end-to-end test uses real config constructors and faithful metadata while mocking expensive calls. It asserts measured totals of 107 latent calls, 4,007 transforms, and 8 builds, checks the lineage block, and cold-recomputes a P0-1 surface and P0-2A clause row from the bundle. Phase-0b execution remains gated on verified declarations and rulings. No real simulator or observation calls were made.

### Verification

- Ruff format/check, mypy, and compileall passed; `git diff --check` was clean.
- Focused tests: **52 passed**.
- Full suite: **462 passed, 4 skipped, 15 warnings**. The skips are for absent comparison trees. An initial full-suite invocation yielded without a verdict; the captured completion run produced the result above.
- No frozen-text inconsistency was found.
- Full command output is saved in [the evidence log](/tmp/jos-p0b-impl-evidence.log).

### Files and diff

- [phase0_campaign.py](/home/steven/jos-p0b-wt/src/jersey_outbreak/phase0_campaign.py)
- [v13_phase0b_synthetic.yaml](/home/steven/jos-p0b-wt/configs/calibration/v13_phase0b_synthetic.yaml)
- [test_phase0b_campaign.py](/home/steven/jos-p0b-wt/tests/test_phase0b_campaign.py)

The module diff is **748 insertions, 111 deletions**. The two new files add **220** and **656** lines; combined change: **1,624 insertions, 111 deletions**.