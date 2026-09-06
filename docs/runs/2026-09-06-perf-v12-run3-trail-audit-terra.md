## Trail audit — perf-v12-run3

Clone: `/tmp/jos-trail-audit-3`  
Main: `a9fa472ee4783089d2b4c35656cebc5d92d6a452`  
Date/model: 2026-09-06, GPT-5 Codex independent read-only audit  
Worktree: clean; no files changed.

### Evidence

1. Trail integrity

```sh
awk -F'\t' '$2=="run-start"{f=1} f' .claude/decisions.tsv
```

Run segment is rows 125–161: 37 rows, timestamps formatted and monotonic. All 16 full Git commit SHAs resolve with `git cat-file -t`; all 17 cited `docs/runs/*` / `docs/audits/*` files exist.

The header has seven columns, including `tokens`; every run-3 row has only six fields and an empty token value.

2. Branches and reports

Current remote-tip comparison:

| Unit | Result |
|---|---|
| perf1, perf2, perf3, corr5, r5afix, r4 | trail SHA = remote tip |
| corr3, corr3b, corr4 | expected historical commits; branch later advanced to corr5 |
| r5a | expected historical commit; branch later advanced to r5afix |

All ten cited executor reports exist. Their new hashes, test counts, and primary measurements generally match the corresponding trail claims. Exceptions are in Attention.

3. CI

```sh
gh run view -R stev004/jsy_disease_sim <id> --json headSha,status,conclusion,jobs
```

All 11 `*-ci` rows resolve to the stated head SHA, with `verify=success` and `frontend=success`. GitHub completion times precede the trail rows when interpreted as the run’s documented BST timestamps. No row was written before the associated run finished.

4. Audit verdicts

The five filed verdicts match the trail:

- Audit 4: FAIL; first blocker is undisclosed/silently omitted Census blanks.
- Audit 5: FAIL; first blocker is vaccination fraction labelled percent.
- Audit 6: FAIL; first blocker is the `overcrowded_households` universe/denominator.
- Tranche-2 Sol review: PASS, two MINOR findings.
- Tranche-2B Sol review: PASS, three MINOR findings.

5. Director-risk review

G20 was applied consistently: four planned run-1 iterations were spent through audit 5, exactly one corrective-plus-audit extension ran (corr5/audit6), then work stopped at G21 awaiting explicit approval.

The actual director conflict resolution is in merge `3e463af`, not `fcf0b0d`: it wraps `_uid_of_index` in `PlainMetadataBoundary` and unwraps it at use. `fcf0b0d` adds ROUTE-4; `0dec469` changes only one test line. The independent Sol review specifically tested this resolution, found NumPy arrays atomic to sciris traversal, and returned PASS. No unreviewed behavioural addition beyond the required integration resolution was found.

`git log origin/main --first-parent --since=2026-09-05` is not literally state/docs-only: authorized pre-run merges `133a099` (G16) and `f5c246c` (G17) touch `data/`, `src/`, and `tests/`. No code-bearing commit appears on `main` after this run started.

## Attention

1. **HIGH — trail rows 125–161: token evidence is absent.** The TSV header declares `tokens`, but all 37 run rows have only six fields; executor, retry, and review rows have no token value. Token figures in RUN.md are unsupported summaries, not trail evidence.  
   Resolve by retaining the originating `fm.sh tokens` result with each executor/reviewer trail row; do not reconstruct values from prose.

2. **HIGH — [RUN.md:6](/tmp/jos-trail-audit-3/.claude/RUN.md:6), [RUN.md:11](/tmp/jos-trail-audit-3/.claude/RUN.md:11), [RUN.md:22](/tmp/jos-trail-audit-3/.claude/RUN.md:22), [RUN.md:26](/tmp/jos-trail-audit-3/.claude/RUN.md:26), [GATES.md:17](/tmp/jos-trail-audit-3/.claude/GATES.md:17).** The current RUN says only G5 is open, but G18/G19/G20/G21 are open. It also retains “In flight,” multiple “CI pending” claims, and a corr4/audit5 recipe after those work items completed. G20 remains open even though its extension is spent; G19 still says FAIL spawns corrective 4, contrary to the G21 pause after audit 6.  
   Resolve by replacing the historical “in flight” ledger heading and stale procedural text with a concise completed-run record; move G20 to Resolved and update G19’s FAIL path to G21.

3. **HIGH — [FRONTIER.md:5](/tmp/jos-trail-audit-3/.claude/FRONTIER.md:5), [FRONTIER.md:19](/tmp/jos-trail-audit-3/.claude/FRONTIER.md:19), [FRONTIER.md:32](/tmp/jos-trail-audit-3/.claude/FRONTIER.md:32), [roadmap.md:83](/tmp/jos-trail-audit-3/docs/roadmap.md:83).** The supposed current-state pointer stops at `tranche2b-review-launch` and says review 2 is “in flight” / “pending”; the trail and filed review show PASS. It also presents audit 3 → corrective 3 → audit 4 as the next exit-gate step, although audits 4–6 completed and G21 is the actual stop.  
   Resolve by synchronizing FRONTIER and roadmap to trail row `tranche2b-review-PASS` and the audit-6/G21 state.

4. **HIGH — [perf1 report](/tmp/jos-trail-audit-3/docs/runs/2026-09-05-perf1-starsim-discovery-boundary-luna-report.md) versus [perf1 proof](/tmp/jos-trail-audit-3/docs/runs/2026-09-05-perf1-proof.json).** The report’s embedded proof gives CI `101:7` observed hash `70d542…`; the separately filed proof gives `70e537…`. They cannot both be the protected-output evidence.  
   Resolve by recovering the original command output or rerunning the bounded proof, identifying the correct hash, and correcting/superseding the other artifact with an explicit erratum.

5. **MEDIUM — trail rows `perf1-kept`, `perf2-kept`, `perf3-kept`: comparator numbers lack support in their cited reports.** The reports support candidate values (`1.067 s`, `5.129 s`, `3,976,620 B`) but not the trail’s historic comparators: PERF-1’s `48 s`, PERF-2’s `147 s`, or PERF-3’s `~482–505 MiB`. Those numbers appear in state prose, not the cited executor reports.  
   Resolve by filing/linking immutable baseline benchmark artifacts with invocation, environment, and both values, or remove those comparator claims from the trail rows.

6. **MEDIUM — rolling branch names weaken historical verification.** Strict trail-head equality fails for corr3/corr3b/corr4 and r5a because the same remote branch was advanced by follow-up commits. The historical commits remain reachable, so this is not a false historical claim, but a stranger applying the specified check gets four failures.  
   Resolve by adding immutable per-unit tags or a `remote tip at acceptance` field, and explicitly distinguish “branch at this phase” from “current branch tip.”

7. **LOW — protected-main audit command needs a run-start boundary.** The literal since-2026-09-05 condition finds code/data merges `133a099` and `f5c246c`; both predate the 20:35 run start and are documented G16/G17 merges.  
   Resolve by scope the hygiene check from `2026-09-05T20:35` or list G16/G17 as approved exceptions.

## Confirmed

10 checks held: clean clone and pinned main; timestamp monotonicity; 16/16 Git SHA resolution; 17/17 cited-artifact existence; all executor reports present; 6 current immutable branch tips match; 11/11 CI conclusions and heads match; all CI rows postdate completion; all five audit verdicts/findings match; G20/G21 extension discipline and independently reviewed integration resolution held.

## Unverifiable

- Whether timestamps were generated by `fm.sh` rather than entered manually; the repository proves formatting/order, not clock provenance.
- Executor/reviewer token usage, because the authoritative trail token column is empty.
- WSL worktree logs, raw benchmark outputs, and claimed director reruns held under `~/` / external worktrees.
- Steven’s chat authorizations and the asserted “standing instruction”; only their repository summaries are available.
- Whether GitHub was read by the director at the claimed instant; GitHub proves the jobs completed before the rows, not the human/tool read event.