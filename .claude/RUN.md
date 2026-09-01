# RUN — in-flight foreman run state (rewritten every iteration; emptied at run end)

**Run:** v1.2-carry-ins · started 2026-09-01 (Steven: "go, fix DIRECTOR and do the carry-ins") · director Fable 5.1
**Predicate:** DIRECTOR.md carries no pre-release hard rule contradicting the released state (DONE this iteration, commit below) AND the three carry-ins — travel.py:3099 predicate-derived status, M03 full release gate in CI, evidence-transcript retention (Sol Pro §12 item 6) — are landed on `codex/v1.2-carry-ins` with suite green and GitHub CI green at the branch tip SHA. Merge to `main` is Steven's, SHA-first.
**Budget:** 5 iterations · 6 codex runs. Spent: 1 run (U1 accepted); U2 launched.

## In flight
- **U1** ACCEPTED, committed `b0ff28702bd62581fff9bc758dd38b83075eb420` on `codex/v1.2-carry-ins`, pushed; GitHub CI at that SHA being watched.
- **U2** (bundle self-test transcript, s12.6): luna@xhigh in `/private/tmp/jsy_v12_carryins` off `b0ff28702bd62581fff9bc758dd38b83075eb420`. Brief + log stem: `/private/tmp/claude-501/-Users-stevenmatson-Documents-jsy-disease-sim/85fe2e4d-79fe-4026-92d6-aade288b6882/scratchpad/briefs/jos-u2-transcript` (`.last.md` = report). Timebox 75 min.

## If cold-starting
1. Read `/private/tmp/claude-501/-Users-stevenmatson-Documents-jsy-disease-sim/85fe2e4d-79fe-4026-92d6-aade288b6882/scratchpad/briefs/jos-u2-transcript.last.md`; if absent, `tail -20` the `.log` and check `ps aux | grep codex`.
2. Review `git -C /private/tmp/jsy_v12_carryins diff --stat` against the U1 acceptance criteria in the brief; scope-check first.
3. Keep → commit on the branch, push, watch `gh run list --branch codex/v1.2-carry-ins`. Revert → `git -C /private/tmp/jsy_v12_carryins checkout -- .` and re-brief (2 runs remain for U2).
4. After U2 lands: confirm CI green at final tip, then run-stop digest + cross-model trail audit. Never touch the other `/private/tmp/jsy_*` worktrees.
