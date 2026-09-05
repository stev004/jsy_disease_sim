<!-- Cross-model trail audit of foreman run v12-run2. Auditor: Codex gpt-5.6-terra@high (self-reports as "Codex (GPT-5)"), read-only, fresh clone /tmp/jos-trail-audit at main da506548ceab7698bba9840058e7f929f9daa505, launched 2026-09-05 02:41 local via fm.sh exec. Report BODY filed verbatim below this provenance preamble (the auditor could not file it itself: read-only by instruction). Director triage of the 12 items: trail row v12-run2-trail-audit. -->

# Trail audit — Attention

Repo audited: `da506548ceab7698bba9840058e7f929f9daa505` (`origin/main`)  
Auditor: Codex (GPT-5)  
Date: 2026-09-05

I did not file a report because the assignment explicitly forbids modifying files. The RUN.md-linked report file is currently absent.

## A. SHA and CI integrity

```text
$ git fetch origin --prune
error: cannot open '.git/FETCH_HEAD': Read-only file system
```

The pre-existing remote refs resolve. All 12 Git commit identifiers cited in the trail resolve as commits and are contained by the claimed branch; e.g.:

```text
865600e... -> origin/feat/v12-remaining-freezes, origin/feat/v12-denominators-dictionary
9ac9d20... -> origin/feat/v12-denominators-dictionary
03ed6bc... -> origin/feat/v12-denominators-dictionary
4465453... -> origin/feat/v12-denominators-dictionary
c062d20... -> origin/fix/job-liveness-and-snapshot-eol
```

```text
$ gh run view <each cited id> --json headSha,conclusion,jobs
failed to determine base repo ... gh auth login
```

All five distinct CI runs—`33927957826`, `33930873632`, `33932747765`, `33934808135`, `33936072022`—are unverifiable from this checkout.

## B. Evidence-cell rule

```text
$ awk -F '\t' '$1 >= "2026-09-04T23:20" {print NR ":" $2 "\t" $5}' .claude/decisions.tsv
```

All 18 run rows structurally name at least one repository path, commit/run identifier, or explicitly off-repo WSL artifact. None cites prose alone. This does not independently prove the CI claims in rows such as `v12-r2-iter1`, whose evidence cell lacks the CI run ID.

## C. Audit records

```text
$ tail -n +3 docs/audits/... | cmp -s - /home/steven/jos-v12-exit-audit*.last.md
body_cmp_exit=0   # all three
```

All three filed bodies match their executor reports after omitting the two-line director-added preamble. Verdict lines are present, and all three audited SHAs are ancestors of `origin/feat/v12-denominators-dictionary`:

```text
9ac9d20... -> 0
03ed6bc... -> 0
4465453... -> 0
```

## D. Hash neutrality

```text
$ git show origin/feat/v12-denominators-dictionary:tests/fixtures/golden_logical_hashes.json
m2_logical_content_hash:
28a6d90a96454d11dcd6ad9d4531d69f9e4ec4396b802780084d3ae598c839a0
```

The expected fixture hash matches the trail. Iterations 4 and 7 changed `canonical_schemas.py` and `data_pipeline.py`, not the golden fixture. I did not run `uv run --locked pytest -q -k golden`: doing so at the branch tip requires creating a checkout/cache, contrary to the no-modification instruction.

## E. Wayback digests

```text
20240223 bytes=643251 actual=VP7XXH3574O6WTH74AFNV7EJ3UOCOYW7 ... match=True
20240718 bytes=621684 actual=XXYCUEBFI7MCLMJU773M4Y2MQOYT4NB4 ... match=True
20260102 bytes=615649 actual=44QV6WTJNA3CQXZWM4CIU3TLD75T7UTK ... match=True
```

Recomputed SHA-1/base32 values match all three pins in `tests/test_data_pipeline.py`.

## F. State files

```text
$ git rev-parse origin/main
da506548ceab7698bba9840058e7f929f9daa505
```

G16/G17 SHA-first commands point at the actual branch tips; RUN.md correctly says nothing is in flight. Referenced V1.2 reports and audit files exist. FRONTIER’s declared main SHA does not match `origin/main`.

## G. Process flags

```text
$ git log --merges 32e9b95..origin/main
# no output
```

There were no merges to main during this run; post-start main commits are state/trail commits by `stev004`.

The evidence supports nine Codex executions: six luna executions (including the wedged iteration-2 run and fix round, plus robustness) and three sol audits. The wedged run log exists; it contains `byte_identical_processed=PASS`, and the succeeding fix-round commit preserved the work.

## H. Attention

1. **High — CI success is claimed but independently unverified.**  
   Where: trail CI rows; [GATES.md](/tmp/jos-trail-audit/.claude/GATES.md:8).  
   Why: `gh` cannot identify/authenticate the GitHub repository, so none of five run IDs was checked for SHA or job conclusion.  
   Settle: authenticated `gh run view <id> --json headSha,conclusion,jobs` output saved with the trail.

2. **High — FRONTIER’s “current” main SHA is stale.**  
   Where: [FRONTIER.md](/tmp/jos-trail-audit/.claude/FRONTIER.md:9), [FRONTIER.md](/tmp/jos-trail-audit/.claude/FRONTIER.md:15).  
   Why: it says `32e9b95`; actual `origin/main` is `da506548`, a later closeout commit. Cold-start readers can mistake the state pointer for the checked-out main.  
   Settle: update the pointer or explicitly identify `32e9b95` as the code baseline.

3. **High — RUN.md points to a missing trail-audit record.**  
   Where: [RUN.md](/tmp/jos-trail-audit/.claude/RUN.md:9).  
   Why: `docs/runs/2026-09-05-v12-run2-trail-audit-terra.md` does not exist.  
   Settle: file the immutable audit record or remove/correct the pointer.

4. **Medium — “Filed verbatim” is literally false.**  
   Where: audit trail rows `v12-exit-gate-audit-{1,2,3}`; e.g. [audit 3](/tmp/jos-trail-audit/docs/audits/2026-09-05-v12-exit-gate-audit-3-sol-FAIL.md:1).  
   Why: each filed record prepends two director-written lines. The report body is verbatim, but the file is not.  
   Settle: describe it as “body filed verbatim with provenance preamble,” or retain a separately hash-pinned exact copy.

5. **Medium — Exit-gate scope was rewritten after audit 3 found a failure.**  
   Where: [V1_2_EXIT_GATE.md](/tmp/jos-trail-audit/docs/research/v1_2/V1_2_EXIT_GATE.md:33); trail row `v12-exit-gate-audit-3`.  
   Why: the rule covering Census reporting fields was narrowed after the audit applied the prior wording. The rationale may be sound, but this is a moving acceptance criterion.  
   Settle: audit 4 should cite the exact gate revision and explicitly distinguish re-scoping from remediation.

6. **Medium — G16 defaults to merge although the stated exit predicate failed.**  
   Where: [GATES.md](/tmp/jos-trail-audit/.claude/GATES.md:10).  
   Why: merging may be reasonable, but “three FAIL audits” and “default MERGE” invite a reader to infer gate success or full V1.2 completion.  
   Settle: label it explicitly as a partial evidence-foundation merge that does not satisfy the exit gate.

7. **Low — G16’s suite count is stale/ambiguous.**  
   Where: [GATES.md](/tmp/jos-trail-audit/.claude/GATES.md:8).  
   Why: it says “full suite 296,” while the final iteration trail claims 302 passed.  
   Settle: identify the count by commit, or update it to the final branch-tip result.

8. **Low — Roadmap retains a contradictory unchecked freeze item.**  
   Where: [roadmap.md](/tmp/jos-trail-audit/docs/roadmap.md:63) versus [roadmap.md](/tmp/jos-trail-audit/docs/roadmap.md:64).  
   Why: the same remaining-freezes work is both unchecked and recorded complete.  
   Settle: remove or mark the superseded unchecked item.

9. **Medium — The CDX-origin claim remains indirect.**  
   Where: trail rows `v12-r2-iter1-committed` and `v12-r2-iter1`.  
   Why: bytes match repository pins, but this audit could not query Internet Archive CDX itself; the test pin alone does not prove it came from CDX.  
   Settle: preserve the CDX response or its immutable retrieval record alongside the pins.

10. **Medium — Hash neutrality is fixture-confirmed, not execution-confirmed here.**  
    Where: trail rows `v12-r2-iter4`, `v12-r2-iter7`.  
    Why: the fixture value is intact, but no branch-tip golden execution was possible under the read-only constraint.  
    Settle: save a locked golden-test transcript for `4465453`.

11. **Process risk — director prose seeded unsupported dictionary claims twice.**  
    Where: trail rows `v12-r2-iter2-wedge-fix`, `v12-exit-gate-audit-2`.  
    Why: both audit failures trace to brief wording being treated as frozen-source fact.  
    Settle: require citation-or-`unknown` cells in briefs before implementation starts.

12. **Process risk — robustness execution overlapped the re-audit.**  
    Where: trail row `robust-1-start`.  
    Why: the branches were independent, but overlapping executor work complicates resource, log, and state attribution during a gate-critical audit.  
    Settle: retain launch/finish timestamps and resource evidence, or serialize future gate audits.

`TRAIL AUDIT: 12 attention items; 13 confirmed; 8 unverifiable`