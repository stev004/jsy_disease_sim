1. Confirmed — audit target was the requested detached clone.

   `git rev-parse HEAD` → `f72a525e2994d68a393d9824f6c4f3ca12b4fcc6`  
   `git status --short` → empty

2. Confirmed — all 15 trail rows (`run-start` through `g25-parked`) have exactly seven TSV fields.

   `awk ... {print NR " NF=" NF}` → rows 205–219 all `NF=7`.

3. Confirmed, subject to stale-ref limitation — all exact 40-character Git SHAs in the scoped rows/state text resolve as commits; unit tips equal their named remote branches and are contained by `origin/v121/integration-run5`.

   `git cat-file -t <sha>` → `commit` for all scoped SHAs.  
   `git rev-parse origin/v121/{perf10-grid-once,prov-verifier-fixes,prov-helpers,prov-job-ordering,integration-run5}` → the five stated tips.  
   `git fetch origin --quiet` was not possible because this clone’s `.git/FETCH_HEAD` is read-only in the sandbox.

4. Confirmed — integration first-parent topology is exact:

   ```text
   ef26e135 → 3fba8100 (p10 9d9bf872)
            → 5600a16c (pver b295e749)
            → 34eb08f2 (phelp e276ebf)
            → 84b96763 (job c3c24e75)
   ```

   `git log --first-parent --format='%H %P%n%s' -8 84b967...` produced that sequence.

   Unit commit file lists also match reports once each report’s explicitly untracked regression test is included:
   p10 2 paths, pver 10, phelp 21, job 4.

5. Confirmed except one weakly retained number — filed paths exist, raw logs support stated suite counts, tokens, hashes, and review count. For example:

   - p10: `365 passed`; token trailer `155,314`
   - pver: `373` then `374 passed`; `321,606 + 166,057 = 487,663`
   - phelp: `371` then `374 passed`; `394,671 + 157,506 = 552,177`
   - job: `368` then `369 passed`; `558,883 + 111,401 = 670,284`
   - independent review: `390 passed`; token trailer `193,668`

   The row `integ5-3units` claim of “39 targeted tests passed” has no retained command transcript; only the later 390-test mirror is retained.

6. Confirmed — remeasure primary artifacts match the filed report.

   `/home/steven/jos-remeasure-20260912/meta.txt`:

   ```text
   run1 wall=68.99 s
   run2 wall=61.92 s
   run3 wall=59.24 s
   ```

   Each `run{1,2,3}.log` contains:

   ```text
   logical_content_hash=bbca602849da80aa04bd2c3bb770d3d5c4486f007d0e14666df4c5087a6e8c81
   ```

7. Confirmed — retry accounting supports the infra-killed exclusion and ≤3 counted runs/unit.

   `stat` gives killed-log mtimes 17:19:14–17:19:20; none has a completion/token trailer. Kept units have one counted attempt (p10) or retry-1 plus retry-2 (pver/phelp/job), matching the trail totals above.

8. Confirmed — the director’s integration resolution was limited to the declared import-block conflict.

   `git merge-tree 0bfc... 5600a16... e276ebf...` reports conflict markers only in `src/jersey_outbreak/verification_archive.py`, between the portable-path import and provenance import.  
   `git show 34eb08f:src/jersey_outbreak/verification_archive.py` retains both imports in sorted order.

9. Not confirmed — state-layer consistency is not clean; see Attention.

10. Confirmed — risk review completed from primary commits, raw mirror log, and state files. No tests were run by this auditor; the task forbids the full suite and existing primary transcripts were available.

## Attention

1. The run exceeded its stated implementation-run budget. Trail `run-start` sets “Budget 6 impl runs”; RUN.md records four counted first attempts plus three counted retries = **7**, explicitly calling one “extra.” Per-unit retry limits were met, but the overall run budget was not.

2. RUN.md is stale/contradictory: line 1 says predicates are MET and closing; line 6 still says “**In flight — four** luna executors.” Its table immediately below says all four are KEPT.

3. FRONTIER.md is stale/contradictory despite its 2026-09-12 update header. Line 15 says the quiet-window remeasure is DONE, while lines 19–20 still call it “Owed”; line 20 calls `main @ 32e9b95` “Current truth,” inconsistent with the run’s `0bfc3c6` state head and later state history.

4. The director mirror was not a clean one-pass green gate. The filed primary log records:

   ```text
   MIRROR_RESULT=FAIL 2026-09-12T18:21:31Z
   ... Duplicate module named "jersey_outbreak.intervention_artifacts"
   MIRROR_RESULT=PASS ... re-run with a deduplicated module list
   ```

   The independent Sol mirror is green, but “Director mirror green” should remain qualified as a corrected director-script invocation, not an unqualified first-pass mirror.

5. The integration branch was pushed and independent review launched before the director’s own full mirror had completed. The mirror’s final pass is timestamped 18:29:03Z; the `review5-launch` row says the branch was already pushed. This is a risky sequencing call, even though the later independent review passed.

6. Backward compatibility of newly fail-closed M7/M8/verification-archive behavior is not demonstrated against a pre-run-5 historical artifact. The new code changes M7 `diagnostics_status` to a literal passed/failed type and adds stricter verifier checks. Tests exercise newly written artifacts and tampering, but no retained test verifies a real older artifact still intended to be supported.

7. `JobRegistry.claim_next_queued` still exposes an unused `precondition` kwarg. Direct inspection shows only its definition and internal conditional; `JobManager` calls `claim_next_queued()` without it. This is small, but it preserves the old silent-queue-starvation mechanism as an available API behavior.

8. The “39 targeted tests passed” quick-gate number in `integ5-3units` is weakly evidenced: no cited command transcript exists for it. The later full 390-test transcript does not independently establish that specific 39-test invocation.

Auditor model: gpt-5.6-terra@high