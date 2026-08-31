# RUN — in-flight foreman run state (rewritten every iteration; emptied at run end)

**Run:** P1 full-scale baseline (started 2026-08-31 ~14:52 UTC)
**Predicate:** full-population 180-day V1.1 baseline on `e3609ff2` completes with scientific verification PASS + comparison summary vs the V1 pilot produced
**Budget:** 1 execution attempt + 1 retry; comparison analysis = 1 sol consult

**In flight RIGHT NOW:**
- The 180-day full-population run (104,540 agents, seed 123, generic demo configs — exact mirror of the V1 pilot invocation). Worktree: `/private/tmp/jos-v11-full-wave` (detached @ `e3609ff2`). Evidence dir: `~/Documents/JOS_v1_1_full_scale_evidence/run-20260831T145052Z/` (RUN_PLAN.md recorded pre-execution; console log `run-console.log` inside). Expected ~2h45m wall (V1 measured 9,959s).

**If cold-starting into this:**
1. Check whether the run finished: artifacts populated in the evidence dir + `/usr/bin/time` summary at the end of `run-console.log`. If the process died mid-run (reboot kills it), relaunch the exact command in `RUN_PLAN.md` — deterministic, nothing partial to salvage; recreate the worktree first if `/private/tmp` was wiped (`git worktree add --detach /private/tmp/jos-v11-full-wave e3609ff2...`).
2. On completion: run scientific verification over the artifact dir (per V1 pilot procedure), extract headline metrics from the console log, then brief sol@high for the V1↔V1.1 comparison against `~/Documents/JOS_v1_full_scale_evidence/run-20260830T180202Z/` (READ-ONLY — never write into the V1 evidence dir). File the comparison to `docs/audits/` or `docs/runs/`, update FRONTIER (P1 done → P2 next: Claude Science delta review), log trail via `fm.sh log`, empty this file, digest to Steven.
3. Ensemble bands language guard: any variation numbers are "stochastic replicate variation", never confidence/credible intervals.

**Standing constraints:** V1 evidence dir immutable · candidate `e3609ff2` immutable · merges/tags Steven-only · no ensemble runs (that's P4, desktop).
