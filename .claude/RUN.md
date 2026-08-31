# RUN — in-flight foreman run state (rewritten every iteration; emptied at run end)

**Run:** P1 full-scale baseline (started 2026-08-31 ~14:52 UTC)
**Predicate:** full-population 180-day V1.1 baseline on `e3609ff2` completes with scientific verification PASS + comparison summary vs the V1 pilot produced
**Budget:** 1 execution attempt + 1 retry; comparison analysis = 1 sol consult

**Done this run:** 180-day baseline COMPLETE (runtime 11,899s, peak 2.179GiB) · scientific verification PASS · artifact `jos-intervention-m7-full-seed-123-f0b18d64a083` in evidence dir `run-20260831T145052Z`, pinned to `e3609ff2`. Note: V1.1 demo config runs waning DISABLED (deliberate R1 outcome) — comparison is an assumption-regime demonstration.

**In flight RIGHT NOW:**
- Sol@high V1↔V1.1 comparison analysis (read-only over both evidence dirs). Report will land at `<scratchpad>/jos-p1-comparison.last.md` (log: `jos-p1-comparison.log`, same dir; scratchpad = the session dir printed in the trail row's evidence cell). Brief: `jos-p1-comparison-brief.md`.

**If cold-starting into this:**
1. If the comparison report exists: review it, file it to `docs/runs/2026-08-31-p1-v1-v11-comparison.md` on the state branch, update FRONTIER (P1 DONE → P2 next: Claude Science delta review of the candidate diff + this comparison), log trail, empty this file, digest to Steven with P2/P3 gates.
2. If not: relaunch from the brief (read-only analysis, safe to rerun; worktree `/private/tmp/jos-v11-full-wave`).
3. Language guard: single stochastic realizations — no uncertainty/CI language anywhere.

**Standing constraints:** V1 evidence dir immutable · candidate `e3609ff2` immutable · merges/tags Steven-only · no ensemble runs (that's P4, desktop).
