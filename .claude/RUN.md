# RUN — R8 foreman run: Claude Science audit Stages A→E (started 2026-09-03 evening)

**Ruling:** Steven in chat: "yeah foreman a to e" + roadmap consolidation. **Authority for content:** `docs/audits/2026-09-03-claude-science-audit-findings.md` (51 findings; its "Recommended implementation order" §Stage A–E is the plan; its "Would not do" list is binding). **Living backlog:** `docs/roadmap.md` (new — reconciled at every closeout per CLOSEOUT.md).

## Predicate
Stages A–E implemented and merged (Steven-gated, SHA-first) with every item's own confirm-or-kill measurement honored; scientific corrections (DISEASE-4, CROSS-3, ROUTE-6/7-science, DATA-7/8/9/10, DISEASE-10) land on their own versioned track with hash migrations, never through equivalence gates; Stage-B measurement campaign produces the three-parameter cost model that re-ranks C/D before they are briefed. Then the new full-scale ensemble launches (THEN section of roadmap.md). **Budget: 12 iterations.**

## Iteration 1 — Stage A (gates), two parallel codex units + one queued
- **A-1 (in flight):** PROV-1 — excise the four execution fields from the M6 ensemble logical hash, schema 1.4→1.5, verifier branch, finalizer comparison fix, invariance unit test. Branch `codex/r8-a1-prov1`, worktree `~/jos-r8-a1-wt`, brief `~/jos-brief-r8-a1.md`, report `~/jos-r8-a1.last.md`.
- **A-2 (in flight):** ROUTE-10 + DISEASE-2 — consolidate `_stable_int` into `hashing.py` (equality proof over ≥10⁶ keys in 2 processes FIRST, pinned-digest test), extract the attribution lookup into a module-level pure function, re-point the oracle at it, add packing-bound/beta-difference/permuted fixtures, mutation-proof (3 mutants must go red). Branch `codex/r8-a2-primitives`, worktree `~/jos-r8-a2-wt`, brief `~/jos-brief-r8-a2.md`, report `~/jos-r8-a2.last.md`.
- **A-3 (queued, after A-2 lands — touches the same primitive):** ROUTE-2 harness upgrade (11 routes, Starsim array fingerprints, declared route list, counter inside the consolidated `_stable_int` behind a flag, date-major mode, term-boundary window 2025-02-14…25, committed ci fixture; then re-baseline).
- Director gates per unit: full CI-mirror (pytest, ruff check+format, **mypy over CI's pinned list PLUS respiratory.py**, uv lock check), diff review, and for A-1 the workers=1-vs-2 fixture identity check.

## Cold-start resume
1. Read `docs/roadmap.md` NOW section + the audit's implementation-order section.
2. Check `~/jos-r8-a1.last.md` / `~/jos-r8-a2.last.md` in WSL; review-diff-gate-commit any that landed; A-3 next, then Stage B (the measurement campaign incl. one real 180-day replicate and the two M7 30-day runs).
3. Trail rows from `r8-run-start`. Main @ `df41196`+state; no ensemble in flight.
