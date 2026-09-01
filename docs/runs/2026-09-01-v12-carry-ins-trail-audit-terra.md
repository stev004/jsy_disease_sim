# Trail audit — GPT-5 (Codex)

| Check | Result | Evidence |
|---|---|---|
| 1. Trail evidence resolves | PASS | Both branch SHAs exist; reports and brief paths exist. Row 35’s transcript resolves in git at main successor `3b086af…` (the detached audit checkout predates that filing). |
| 2. Accepted-claim reproducibility | PASS | Diagnostics derive `status` from three computed predicates; the hash payload excludes diagnostics ([travel.py](/tmp/jsy-audit-tip/src/jersey_outbreak/travel.py:2975), [travel.py](/tmp/jsy-audit-tip/src/jersey_outbreak/travel.py:3114)). CI steps and real CLI relocation script are present; self-test copies, recursively verifies, compares identities, and rejects in-artifact transcript destinations ([bundle_selftest.py](/tmp/jsy-audit-tip/src/jersey_outbreak/bundle_selftest.py:130)). Focused tests: `6 passed in 4.67s`. |
| 3. Scope | PASS | `a157e12..28067d8` changes exactly seven brief-authorized files. `travel.py` changes only the diagnostics block plus adjacent helper; no science defaults, schema, or version constant changed. |
| 4. State consistency | FLAG | `RUN.md` still says U1 CI is “being watched” although row 33 records it green. G3 remains under `## Open` with an actionable merge/tag procedure despite being resolved. FRONTIER’s carry-in listing is appropriate while the branch remains unmerged. |
| 5. Director conduct | PASS | The DIRECTOR refresh correctly identifies `jos-v1.1.0` at `e502ebf…`; its commit changed only `.claude/DIRECTOR.md` and `RUN.md`. `git log --stat a157e12..main -- . ':!.claude' ':!docs'` is empty. |
| 6. Risk in hindsight | FLAG | Final-tip CI remains incomplete; the relocation check destructively removes a directory under `outputs/`; U2 tests are order-dependent. |

**Attention**

1. **blocking** — The stated predicate is not yet met. At audit close, `gh run list --commit 28067d88a4c21e73cf5ce27e48a859dee9ce274a` reports CI run `33553860048` as `in_progress`. U1’s successful run `33549721657` is not proof for the final tip.

2. **should-fix** — Stale U1 CI state contradicts the trail: [RUN.md](/private/tmp/jsy_v12_trailaudit/.claude/RUN.md:8) says “being watched,” while [decisions.tsv](/private/tmp/jsy_v12_trailaudit/.claude/decisions.tsv:33) records both U1 jobs successful.

3. **should-fix** — G3 is resolved but remains in the `Open` section with an “ACTIONABLE” merge/tag procedure and obsolete default ([GATES.md](/private/tmp/jsy_v12_trailaudit/.claude/GATES.md:5)). This repeats the state-layer ambiguity the Director lessons prohibit.

4. **should-fix** — The CI relocation helper deletes `artifact_directory` after only checking that its parent is `outputs/interventions` ([ci_relocation_check.py](/tmp/jsy-audit-tip/scripts/ci_relocation_check.py:23)). Safe on a fresh GitHub runner, but a local invocation can remove an existing default-location artifact.

5. **should-fix** — The module-scoped `m7_bundle` is shared, while `_transcript()` requires exactly one transcript ([test_v12_bundle_selftest.py](/tmp/jsy-audit-tip/tests/test_v12_bundle_selftest.py:19), [test_v12_bundle_selftest.py](/tmp/jsy-audit-tip/tests/test_v12_bundle_selftest.py:36)). Reordering the first two tests can create two transcripts before the exact-one assertion. The trail itself acknowledges this in [decisions.tsv](/private/tmp/jsy_v12_trailaudit/.claude/decisions.tsv:34).

6. **should-fix** — Accepted rows omit the required Codex session IDs. The standing rule requires one in each evidence cell ([DIRECTOR.md](/private/tmp/jsy_v12_trailaudit/.claude/DIRECTOR.md:45)); rows 32 and 34 cite commits/reports/briefs but no session ID.

Operational disclosure: the requested `git worktree add` was blocked because this host cannot write the repository’s shared `.git/worktrees` directory. Its failed shell sequence created ignored `.venv`/cache files in the audit checkout before I stopped it; no tracked files were modified, and I left those files untouched to avoid further writes.

TRAIL AUDIT VERDICT: FLAGS (6)