# perf-v12-run4 trail audit

Clone: `/tmp/jos-trail-audit-4`  
Main: `33dddf44cbb2221c6ee0ff4487215ec5d9432ec5`  
Date: 2026-09-09 · Model: Codex/GPT-5 · read-only; worktree clean.

Scope was rows 167–199 (`g18-merge` through `g23-merge`): there is no run-4 `run-start` or `run4-close` row.

## Evidence

1. Trail integrity

   - `awk -F '\t' ...`, scoped to rows 167–199: 33 rows, all seven fields, timestamps monotonic, and no empty token fields. Completion rows for executor work carry nonzero tokens.
   - `git cat-file -t` for all 29 full Git SHAs cited in scope: all `commit`.
   - Normalized cited `docs/runs`/`docs/audits` paths: 14/14 exist on `main`.
   - Git commit timestamps closely corroborate the minute-stamped trail ordering, but machine generation itself cannot be proven from the clone.

2. Units and reports

   - Exact remote-head matches: corr6 `0cf6499`, hk `8c38e11`, p4 `f60d165`, r5b `2dcc57b`, prov8 `284caff`, p9fix `fba9fbf`, p6fix `b720a49`.
   - The reported hashes/test counts/benchmark figures are present in all eight relevant performance reports.
   - p6 and p9 original kept SHAs are historical, not current remote heads: `f74d69e` → `b720a49`, and `729a6b7` → `fba9fbf`.

3. CI

   - There are no `*-ci` trail rows in this scope; the four gate merges explicitly record no CI because billing was exhausted.
   - Attempted `gh run view 33998934843 --json status,conclusion,headSha,jobs`; it failed because this clone has no GitHub-associated remote/authentication.

4. Verdicts

   - Audit 7 says `V1.2 EXIT GATE: PASS` at `0cf6499`.
   - Review 3 says `RUN-4 REVIEW: PASS` at `e26ef91`.
   - Review 4 says `RUN-4B REVIEW: BLOCKED`; its first blocker is targeted/residents-only community interventions being neutralized.
   - The bounded re-review says `RUN-4B RE-REVIEW: PASS` at `a588e22`.

5. State and merge history

   - G18/G19/G21/G22/G23 are headed `RESOLVED`; G5 remains open. FRONTIER and performance history correctly identify the four merged candidates and the `6e9b0e4` code baseline.
   - `git log origin/main --first-parent --since=2026-09-08` contains the four gate merges plus state/docs commits.
   - Each merge has the cited candidate as a direct second parent: G18→`0dec469`, G19→`0cf6499`, G22→`e26ef91`, G23→`a588e22`.
   - RUN has no unsupported clock times; its only `HH:MM` is the trail-derived prior-run timestamp.

## Attention

1. **HIGH — [RUN.md:1](/tmp/jos-trail-audit-4/.claude/RUN.md:1): false `run4-close` reference.** `rg run4-close .claude docs` finds only this line; the trail ends at `g23-merge`. A stranger following the stated evidence pointer will fail. Resolve with an append-only corrective trail row (or change RUN to cite only `g23-merge`).

2. **HIGH — [decisions.tsv:172](/tmp/jos-trail-audit-4/.claude/decisions.tsv:172): corr6 has the wrong report and audit labels.** It cites the corrective-5 report and says “audit 5 running,” while its decision launches audit 7. The actual corrective-6 report exists at `docs/runs/2026-09-08-v12-corrective-6-luna-report.md`. Append a superseding row with that report and `audit 7`.

3. **HIGH — [decisions.tsv:196](/tmp/jos-trail-audit-4/.claude/decisions.tsv:196) and [198](/tmp/jos-trail-audit-4/.claude/decisions.tsv:198): re-review is misidentified as review 3/run4.** The filed report is explicitly “run-4b bounded re-review,” candidate `a588e22`, but row 198 says “review 3 of perf/integration-run4.” This is a materially false trail identity for the merge gate. Append a supersession naming `run4b-rereview-PASS`.

4. **HIGH — G22/G23 authorization is unproven and broader than the recorded one-time instruction.** G18 calls Steven’s 2026-09-08 instruction “one-time, not a standing authorization,” while G22/G23 later treat it as an ongoing default. The filed independent PASSes are real, but the chat record is unavailable and later work was not yet identified when the instruction was made. Obtain Steven’s durable confirmation that the instruction covered G22 and G23, or record a narrower rule approved by him.

5. **MEDIUM — local merge-smoke claims are not independently evidenced.** All four merges have a filed independent PASS and direct-parent proof, but the alleged local smoke runs are supported only by trail/GATES prose; no durable command transcripts were filed. This matters especially because CI was unavailable. File compact smoke transcripts or a reproducible command/result manifest.

6. **MEDIUM — state files retain misleading historical live instructions.** [RUN.md:7](/tmp/jos-trail-audit-4/.claude/RUN.md:7) is headed “In flight” despite the completed header; [RUN.md:14](/tmp/jos-trail-audit-4/.claude/RUN.md:14) still directs a cold start to G18/G19/G21 as open; [roadmap.md:83](/tmp/jos-trail-audit-4/docs/roadmap.md:83) says corrective 6/audit 7 wait on G21 after documenting their completion. Resolution: move the old run ledger to an explicitly archival section and remove executable stale instructions.

7. **MEDIUM — p6/p9 report-to-branch identity is weak.** The original reports end with “No commit created,” do not record their accepted branch SHA, and their cited SHA is not the current branch head after the review-4 repairs. The historical trail is valid, but a resumer could mistake the BLOCKED versions for merge-ready. Add accepted-SHA/final-status metadata or make the report links point to the retry reports.

8. **MEDIUM — “BLOCKED candidate was never merged” is only true in the direct-gate sense.** `ae0c6f8` is an ancestor of `origin/main`, although it was not the direct second parent of G23; `a588e22` is the direct, re-reviewed merge parent. State this distinction to avoid claiming the blocked code was absent from history.

9. **MEDIUM — credential-copy and cherry-pick incidents are only self-reported.** The Windows→WSL token copy cannot be audited safely from this sandbox; it creates a duplicated refresh-token/race risk until rotated. The cherry-pick failure is corroborated by the new DIRECTOR rule, but no durable clean-worktree recovery evidence exists. Rotate/revoke the copied credential and retain a non-secret recovery/status record.

10. **LOW — missing run-start makes automated trail extraction misleading.** The prescribed `awk` starts at the prior run’s `run-start`, not run 4. The task documents the exception, but the trail should include a run-start or explicit continuation marker next time.

## Confirmed

**42 discrete checks held:** 33-row tabular/timestamp integrity, 29 SHA resolutions, 14 cited-path checks, seven current branch-head matches, eight report-number/hash checks, four verdict checks, six gate-status checks, four direct merge-parent checks, and first-parent history discipline. No simulations or ensembles were run.

## Unverifiable

- GitHub job conclusions and timing: `gh` cannot identify/authenticate this clone’s remote, and no run-4 CI rows exist.
- The original Steven chat wording, scope, and whether it authorized later G22/G23 merges.
- Actual execution/output of local smoke commands; no persisted transcript was found.
- Whether timestamps were generated by `fm.sh` rather than manually entered.
- The copied Codex credential, backup, revocation, and concurrent-install state; I did not inspect secrets or external WSL worktrees.