# RUN — in-flight foreman run state (rewritten every iteration; emptied at run end)

**Run:** v1.2-carry-ins · started 2026-09-01 (Steven: "go, fix DIRECTOR and do the carry-ins") · director Fable 5.1
**Predicate:** DIRECTOR.md carries no pre-release hard rule contradicting the released state (DONE this iteration, commit below) AND the three carry-ins — travel.py:3099 predicate-derived status, M03 full release gate in CI, evidence-transcript retention (Sol Pro §12 item 6) — are landed on `codex/v1.2-carry-ins` with suite green and GitHub CI green at the branch tip SHA. Merge to `main` is Steven's, SHA-first.
**Budget:** 5 iterations · 6 codex runs. Spent: 0 runs (U1 launched).

## In flight
- **U1** (travel:3099 relabel + M03 CI): luna@xhigh in `/private/tmp/jsy_v12_carryins` (branch `codex/v1.2-carry-ins` off `a157e12151a9a339dc6c854c9ce67e7fd14cd96a`). Brief + log stem: `/private/tmp/claude-501/-Users-stevenmatson-Documents-jsy-disease-sim/85fe2e4d-79fe-4026-92d6-aade288b6882/scratchpad/briefs/jos-u1-carryins` (`.last.md` = report). Launched 2026-09-01 ~19:00 UTC, timebox 75 min.
- **U2** (evidence-transcript retention, §12.6): not yet briefed; depends on U1 landing (same branch, sequential).

## If cold-starting
1. Read `/private/tmp/claude-501/-Users-stevenmatson-Documents-jsy-disease-sim/85fe2e4d-79fe-4026-92d6-aade288b6882/scratchpad/briefs/jos-u1-carryins.last.md`; if absent, `tail -20` the `.log` and check `ps aux | grep codex`.
2. Review `git -C /private/tmp/jsy_v12_carryins diff --stat` against the U1 acceptance criteria in the brief; scope-check first.
3. Keep → commit on the branch, push, watch `gh run list --branch codex/v1.2-carry-ins`. Revert → `git -C /private/tmp/jsy_v12_carryins checkout -- .` and re-brief (2 runs remain for U1).
4. Then brief U2. Never touch the other `/private/tmp/jsy_*` worktrees.
