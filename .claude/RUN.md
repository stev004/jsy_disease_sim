# RUN — in-flight foreman run state (rewritten every iteration; emptied at run end)

**Run:** v1.2-carry-ins · started 2026-09-01 (Steven: "go, fix DIRECTOR and do the carry-ins") · director Fable 5.1
**Predicate:** DIRECTOR.md carries no pre-release hard rule contradicting the released state (DONE this iteration, commit below) AND the three carry-ins — travel.py:3099 predicate-derived status, M03 full release gate in CI, evidence-transcript retention (Sol Pro §12 item 6) — are landed on `codex/v1.2-carry-ins` with suite green and GitHub CI green at the branch tip SHA. Merge to `main` is Steven's, SHA-first.
**Budget:** 5 iterations · 6 codex runs. Spent: 5 of 6 runs (U1, U2, U2b, U3 all accepted iter-1). Nothing in flight except the CI watch. Remaining: CI green at final tip + run-stop digest + terra trail audit (in flight).

## In flight
- **U1** ACCEPTED, committed `b0ff28702bd62581fff9bc758dd38b83075eb420` on `codex/v1.2-carry-ins`, pushed; GitHub CI run 33549721657 green (both jobs).
- **U2** `28067d8` + **U2b** fix `449605da0fd9ef19b54d2cf654391f5f24fd1689` pushed; CI at `449605da0fd9ef19b54d2cf654391f5f24fd1689` being watched (read the job conclusions before logging).
- **U3** accepted, FINAL TIP `9711b8e3937b3ff18aec86523ed4769ff78cfd4c` pushed. Predicate closes when GitHub CI at `9711b8e3937b3ff18aec86523ed4769ff78cfd4c` is green on both jobs (read the job conclusions before logging). Then: run-stop digest, FRONTIER rewrite (carry-ins done on branch, merge = Steven SHA-first), RUN emptied.
- **Trail audit** DONE (terra): FLAGS (6) — filed `docs/runs/2026-09-01-v12-carry-ins-trail-audit-terra.md`. Actioned: G3 removed from Open, RUN stale line, session IDs logged. Pending: U2b (CI + test order), then **U3** = relocation script must refuse to run if the default artifact dir pre-exists (brief drafted at `.../briefs/jos-u3-relocation-guard-brief.md`).

## If cold-starting
1. Read `/private/tmp/claude-501/-Users-stevenmatson-Documents-jsy-disease-sim/85fe2e4d-79fe-4026-92d6-aade288b6882/scratchpad/briefs/jos-u3-relocation-guard.last.md`; if absent, `tail -20` the `.log` and check `ps aux | grep codex`.
2. Review `git -C /private/tmp/jsy_v12_carryins diff --stat` against the U1 acceptance criteria in the brief; scope-check first.
3. Keep → commit on the branch, push, watch `gh run list --branch codex/v1.2-carry-ins`. Revert → `git -C /private/tmp/jsy_v12_carryins checkout -- .` and re-brief (1 run remains in budget).
4. After U2 lands: confirm CI green at final tip, then run-stop digest + cross-model trail audit. Never touch the other `/private/tmp/jsy_*` worktrees.
