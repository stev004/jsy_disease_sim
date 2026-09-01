# RUN — in-flight foreman run state (rewritten every iteration; emptied at run end)

**Run:** V1.1 release repair R0–R5 (started 2026-09-01, Steven resolved G6: go)
**Predicate:** new candidate SHA on `codex/v1.1-release-corrections` with B01+B02+B03+M01+M02 closed · full exact-SHA gate green incl. relocation verification · P1 evidence regenerated at that SHA · bounded independent re-audit PASS
**Budget:** 8 implementation runs + 1 evidence regeneration + 1 re-audit
**Authority:** `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md` §8 (recovery sequence) — unit specs derive from its B01/B02/B03/M01/M02 sections.

**Unit plan (sequential on one branch, director reviews+commits each):**
- **U1 (in flight):** B01 portable artifact paths + relocation regression tests — luna@xhigh, worktree `/private/tmp/jsy-repair-wt` (branch @ base `e3609ff2`), brief `jos-u1-b01-brief.md`, report will land at `jos-u1-b01.last.md` (scratchpad dir in trail evidence).
- **U2:** B02 cohort-correct daily ascertainment + M6 schema bump (audit B02 "Required correction" is the spec).
- **U3:** B03 API schema versions from schema constants + consistency tests; M02 travel diagnostics (real resident-ID check, derived status).
- **U4:** M01 version identity (product/package/frontend coherent or explicitly documented domains) + README current-status rewrite.
- **U5:** director runs the full exact-SHA gate (audit R3 list: backend + frontend tests/typecheck/build + ruff + mypy scope + lock + compileall + default-CLI artifact generate/verify + copied-relocation verify + API contract tests + clean HEAD attestation).
- **U6:** regenerate 180-day P1 evidence at the final SHA (~3.5h, mirror RUN_PLAN discipline, new evidence dir), verify in place AND from a copied directory; refile comparison with schema-delta vs trajectory-delta distinguished.
- **U7:** bounded independent re-audit (fresh sol@high; verdict syntax `JOS V1.1 RELEASE-CANDIDATE PASS/BLOCKED`) — checks the audit's R5 list.

**If cold-starting:** check `jos-u1-b01.last.md` (then successive unit reports); review diff in the repair worktree before committing anything; after each unit commit+push branch, log trail via fm.sh, update this file. If worktree gone (reboot): `git worktree add /private/tmp/jsy-repair-wt codex/v1.1-release-corrections` and continue from the last committed unit.

**Standing:** no science/model changes in this run · SHA-first (G3) · merges/tags Steven-only · V1/V1.1 evidence dirs immutable · old candidates immutable.
