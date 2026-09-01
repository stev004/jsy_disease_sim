# RUN — in-flight foreman run state (rewritten every iteration; emptied at run end)

**Run:** V1.1 release repair R0–R5 (started 2026-09-01, Steven resolved G6: go)
**Predicate:** new candidate SHA with B01+B02+B03+M01+M02 closed · full exact-SHA gate green incl. relocation verification · P1 evidence regenerated at that SHA · bounded independent re-audit PASS
**Budget:** used 4/8 implementation runs (U1–U4 all accepted iter-1, one director-side lockfile fixup) · evidence regen in flight · re-audit pending

**Done:** U1 B01 (`46da62c`) · U2 B02 (`559cb79`) · U3 B03+M02 (`ba9749b`) · U4 M01 (`2765160` + lockfile fixup) → **final candidate `e502ebfd366743db8ecbb65f580159bfa1d2a70c`**, gate green locally + GitHub CI run 33510847483. Follow-up flagged for re-audit: second unconditional `"status": "passed"` at travel.py:3099 (ensemble summary block, outside M02's cited scope).

**In flight RIGHT NOW (U6/R4):** 180-day full-population evidence regeneration at `e502ebf` — worktree `/private/tmp/jsy-repair-wt`, evidence dir `~/Documents/JOS_v1_1_full_scale_evidence/run-20260901T131226Z/` (RUN_PLAN pre-recorded; console log inside). Expect ~3–3.5h.

**On completion (cold-start recipe):**
1. Verify in place (`verify_scientific_artifact` over the produced artifact dir, from the repair worktree).
2. **The decisive B01 check:** copy the artifact dir to a fresh /tmp location, rename/move the original evidence dir temporarily, verify the COPY recursively (M7→nested M5) — must PASS. Restore original.
3. Compare headline trajectory vs `run-20260831T145052Z` (same seed/configs; B01–B03 fixes should not alter the epidemic — expect identical or near-identical latent hashes; any trajectory delta must be explained). File a short delta note in `docs/runs/`.
4. U7/R5: bounded re-audit brief (fresh sol@high, fm.sh exec): verify 4 blockers closed at `e502ebf`, no unrelated science change (diff review e3609ff2..e502ebf), schema migrations explicit, relocation evidence, release instructions SHA-first — include the travel.py:3099 follow-up for judgment. Verdict syntax `JOS V1.1 RELEASE-CANDIDATE PASS/BLOCKED`.
5. On PASS: update FRONTIER (releasable SHA = `e502ebf`, G3 actionable), file reports, empty this file, digest to Steven with the merge command.

**Standing:** SHA-first · merges/tags Steven-only · all prior evidence dirs immutable · no science changes.
