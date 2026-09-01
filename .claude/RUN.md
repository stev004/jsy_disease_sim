# RUN — in-flight foreman run state (rewritten every iteration; emptied at run end)

**Run:** v1.2-carry-ins · started 2026-09-01 (Steven: "go, fix DIRECTOR and do the carry-ins") · director Fable 5.1
**Predicate:** DIRECTOR.md carries no pre-release hard rule contradicting the released state (DONE this iteration, commit below) AND the three carry-ins — travel.py:3099 predicate-derived status, M03 full release gate in CI, evidence-transcript retention (Sol Pro §12 item 6) — are landed on `codex/v1.2-carry-ins` with suite green and GitHub CI green at the branch tip SHA. Merge to `main` is Steven's, SHA-first.
**Budget:** 5 iterations · 6 codex runs. Spent: 3 runs (U1, U2 accepted iter-1; U2b fix launched). Remaining: CI green at final tip + run-stop digest + terra trail audit (in flight).

## In flight
- **U1** ACCEPTED, committed `b0ff28702bd62581fff9bc758dd38b83075eb420` on `codex/v1.2-carry-ins`, pushed; GitHub CI at that SHA being watched.
- **U2** committed `28067d88a4c21e73cf5ce27e48a859dee9ce274a`, but GitHub CI run 33553860048 FAILED on `test_bundle_selftest_requires_safe_transcript_location` (rich-rendered typer error panel on 80-col runner). **U2b** fix in flight: luna@high in `/private/tmp/jsy_v12_carryins`, brief/log stem `/private/tmp/claude-501/-Users-stevenmatson-Documents-jsy-disease-sim/85fe2e4d-79fe-4026-92d6-aade288b6882/scratchpad/briefs/jos-u2b-fix`, timebox 25 min. Scope: cli.py error path -> plain echo + Exit(2); test file order-independent.
- **Trail audit** (terra@high) in flight in `/private/tmp/jsy_v12_trailaudit`, stem `.../briefs/jos-v12-trailaudit`; it will see the false-PASS row and its correction row.

## If cold-starting
1. Read `/private/tmp/claude-501/-Users-stevenmatson-Documents-jsy-disease-sim/85fe2e4d-79fe-4026-92d6-aade288b6882/scratchpad/briefs/jos-u2b-fix.last.md`; if absent, `tail -20` the `.log` and check `ps aux | grep codex`.
2. Review `git -C /private/tmp/jsy_v12_carryins diff --stat` against the U1 acceptance criteria in the brief; scope-check first.
3. Keep → commit on the branch, push, watch `gh run list --branch codex/v1.2-carry-ins`. Revert → `git -C /private/tmp/jsy_v12_carryins checkout -- .` and re-brief (2 runs remain for U2b).
4. After U2 lands: confirm CI green at final tip, then run-stop digest + cross-model trail audit. Never touch the other `/private/tmp/jsy_*` worktrees.
