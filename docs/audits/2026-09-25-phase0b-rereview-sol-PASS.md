PHASE-0B CORRECTIVE RE-REVIEW: PASS

**Findings:** The corrective commit resolves all four blocking and two major findings. I found no regression in the bounded review. The one Phase-0b CI campaign may run at this exact SHA.

| Finding | Decision | Evidence |
|---|---|---|
| B1 · production decimal join | PASS | [run_p01_campaign](/home/steven/jos-p0b-rereview-readonly/src/jersey_outbreak/phase0_campaign.py:2773) passes the validated config after blind-estimate persistence and read-back; the production-path test exercises exact decimal endpoints. |
| B2 · per-target CSV predicates | PASS | [evaluate_p01](/home/steven/jos-p0b-rereview-readonly/src/jersey_outbreak/phase0_campaign.py:2223) writes separate tolerance, joint-hit, tie, viability, boundary and diagnostic columns. Bundle tests cross-check them against retained blind estimates and truth diagnostics. |
| B3 · clause states | PASS | Phase-0b clause columns serialize as `TRUE`, `FALSE` or `UNKNOWN`; undefined estimates, errors and \(E_i\) remain `null`. |
| B4 · lineage | PASS | The `lineage` block contains every listed §6 field, including historical P0-2A, P0-2B and P0-3 PASS results; those results are absent from the summary root. |
| M1 · decimal-string grids | PASS | P0-2B and P0-3 grids are strings and are validated string-for-string against independent module constants before numeric use. |
| M2 · digest filename | PASS | `predeclaration.sha256` names `predeclaration.md`; the digest line is covered by `SHA256SUMS`. |

**Verification:** The requested focused command passed **57 tests**. My dry-run passed with the declared 625/625/75/9 cells, 107 latent calls, 4,007 transforms and eight builds. I independently compared all **81/81 Phase-0 candidate configuration hashes** with the prior commit; every hash matched. The retained mirror log reports **467 passed, 4 skipped** and `MIRROR_RESULT=PASS` at this SHA. No campaign or real simulator/observation API was invoked in this review.

Final SHA: `024caa09c19bbdad0952b09213ed56e6638ad676`. Final `git status --porcelain` was empty; `git diff --check` passed. No clone files were edited.