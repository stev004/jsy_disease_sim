PHASE-0 ALL-ARMS CODE REVIEW: BLOCKED

The harness implements the declared arms and budgets, and the focused tests pass. The result bundle would still discard evidence needed for the separate cold audit in step 7. **Do not run the one authorized campaign at this SHA.** This is a code-review verdict, not a scientific exit verdict.

### Findings

**BLOCKING — The published bundle cannot independently substantiate its results.** [phase0_campaign.py](/home/steven/jos-allarms-review-readonly/src/jersey_outbreak/phase0_campaign.py:3686) runs all arms in a temporary workspace, then publishes the files assembled at [line 3795](/home/steven/jos-allarms-review-readonly/src/jersey_outbreak/phase0_campaign.py:3795). The 15 blind estimate or tie records are read back before truth joins, but are deleted with that workspace. The bundle also omits the target and candidate observed tables used to calculate losses and \(E_i\), and the per-target truth diagnostics behind P0-1 viability, chronology, and conservation. Its surfaces, hashes, and status booleans cannot replace those inputs for a cold recalculation. Section 6 does not name the blind records individually, but the blind-fitting rule and the stated requirement for an independently verifiable bundle require retaining them. The smallest correction is to publish the existing blind records and the underlying per-target and per-candidate evidence needed to recalculate the reported predicates, then include every added file in `SHA256SUMS`. This changes bundle retention, not the frozen science.

**MAJOR — The frozen step-6 command lacks a required argument.** [execute_campaign](/home/steven/jos-allarms-review-readonly/src/jersey_outbreak/phase0_campaign.py:3666) correctly rejects execution without `--ruling`; the ruling path declared in the YAML is absent from this clone. The command printed in the predeclaration therefore exits before generation. The run instruction must explicitly supply the accepted `/tmp/g29-ruling.md` copy. No relaxation of the digest check is needed.

**MINOR — The P0-3 measured transform check names the latent-call field.** [phase0_campaign.py](/home/steven/jos-allarms-review-readonly/src/jersey_outbreak/phase0_campaign.py:3705) compares transforms with `plan.p03_latent_calls`. Both frozen values are 27, so this does not miscount the current campaign. Compare against the planned P0-3 transform count explicitly.

### Acceptance decisions

| # | Decision | Evidence |
|---|---|---|
| 1. Identity and scope | **Partial** | HEAD is `29f43d131f568868259d64a459f889e027d31e21`, descended from `3ff3734`; its parent is accepted P0-2 head `ae88529`. Only the three authorized files changed under `src/`, `configs/`, and `tests/`, and no protected module or contract changed. The literal claim that *only three files* differ from `3ff3734` is false: the full stat lists 22 files, including predeclaration and state documents. |
| 2. P0-1 | **Pass as code** | The fixed scenario, seeds, 81-cell blind objective, profiles, exact-decimal grid recovery, diagnostics, and ten aggregate conditions remain implemented. |
| 3. P0-2 and G29 | **Pass as code** | Accepted tie handling, separate software and detection states, 81/27-cell arms, and frozen ruling digest remain intact. |
| 4. P0-3 | **Pass as code** | Nine cells, all eleven uniform route multipliers, fixed timing and ascertainment, candidate seeds, DATA-9 helpers, factor-1 reference, and six evidence-based predicates are present. No path assigns a factor estimate or forces observed ridge vectors equal. |
| 5. Budget | **Pass, minor correction** | Planning reports 198 cells, 59 latent calls, 599 transforms, eight builds, `ci`, and 30 days. Dispatch guards and measured totals are checked before publication; the wrong-field comparison above should be corrected. |
| 6. Outputs | **Blocked** | Listed files, staging, destination rejection, statuses, and file hashes are implemented. The published evidence is insufficient for cold verification. |
| 7. Blind fitting | **Blocked on retention** | Fitter signatures exclude truth; records are written and re-read before truth joins. Those records do not survive publication. |
| 8. Execute | **Pass as code; command correction needed** | Import and CLI defaults do not execute. Tests invoke `execute_campaign` explicitly with mocked APIs. Preconditions reject missing or changed declaration/ruling, incomplete arms, bad budgets, and occupied output. |
| 9. Tests and earlier hashes | **Pass** | The 42 focused tests include adverse classifier, corruption, budget, and mocked orchestration cases. Earlier reports’ P0-1/P0-2 hash comparisons are consistent with the P0-3 hash-payload change, which strips only new negative-control metadata; I did not rerun the earlier independent hash comparison. |
| 10. Other bundle risks | **Blocked** | The same missing observation and truth-diagnostic inputs prevent recalculation of losses, \(E_i\), and P0-1 truth gates from the immutable bundle. |

### Director’s four points

1. **Blind records:** retain them in the hashed bundle. Temporary read-back proves the running code’s order, but leaves the cold auditor only a claimed estimate hash.
2. **Live `execute`:** no implicit real invocation found. The test invocation is explicitly mocked; `mocked_for_test` is not a CLI option. The accepted ruling must be passed explicitly.
3. **Transform count:** the comparison uses the wrong plan field, with no current numerical effect.
4. **Computed boundaries:** **no owner ruling is required before execution for the current semantics.** The code applies the declared inclusive inequalities to its computed floating-point objectives and channel totals, without an added epsilon or threshold change. Exact-decimal arithmetic is used for the separately declared finite-grid recovery values. A different rule for rounding computed quantities would require an owner ruling; none is introduced by this review.

### Integrity and provenance inventory

| Check | Source of truth and limit |
|---|---|
| Frozen controls and caps | Module constants and calculated grid/seed counts are compared with YAML fields; these are independent of a changed supplied YAML. |
| Declaration and G29 | Re-read document bytes are compared with pinned module SHA-256 constants, including the accepted G29 digest. |
| Runtime inputs | Constructed run and observation configs are checked against frozen fields; returned result metadata is checked against those configs. |
| Namespace and calendar | Returned observation diagnostics are compared with a fingerprint recomputed through `observation_stream_seed`; dates are checked against the fixed calendar. The recomputation shares the production scheduler implementation. |
| Candidate and target provenance | Hashes derive from constructed configs and observed tables; latent hashes and RNG fingerprints derive from returned results. These establish internal traceability, not a retained copy of every input table. |
| Blind boundary | The in-memory fit supplies the expected full record; the saved JSON is re-read and compared before truth joins. The estimate hash derives from its selected/tie result, profiles, and complete surface. |
| Truth and status | Truth comes from validated frozen config values; event counts and chronology/conservation flags come from returned latent and observation results. Measured dispatch counts and complete surfaces are checked against the plan. |
| P0-3 and bundle | Ridge vector hashes derive from actual generated vectors; DATA-9 supplies profiles. `SHA256SUMS` is recalculated against published files. It detects file changes, but cannot verify inputs that were never published. |

### Reproduced results and limits

The focused command passed **42/42**. Ruling SHA-256 was `06e49aaa7f21564dd6f525941633054fad39cf6714aa74aec0ef1f12dc1eb70c`; the predeclaration SHA-256 was `ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104`. A ruling-verified dry run reported **198/59/599/8** in `ci` mode for 30 days. The supplied clean-clone mirror exited **0** at this SHA with **452 passed, 4 skipped**; the known job-ordering flake did not occur. I did not rerun the full suite, invoke real execution, or call a simulator or observation API outside the existing mocked tests.

Final SHA: `29f43d131f568868259d64a459f889e027d31e21`. Initial and final `git status --porcelain` were empty; `git diff --check` was clean. No files were edited.