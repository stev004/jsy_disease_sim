# ACCEPTED — G29 P0-2 indeterminate detection ruling

**Status:** accepted model-owner ruling, immutable once committed. It supplements, and does not edit, the frozen Phase-0 predeclaration `docs/research/v1_3/2026-09-21-phase0-predeclaration.md` (commit `a4b3200967f34e449bd7ffd4f589a8d30e841e95`, SHA-256 `ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104`).

**Ruling source:** Steven, in chat, 2026-09-23: "approve g29 with your rec then keep going with it". The recommendation approved is `docs/research/v1_3/2026-09-22-p02-tie-ruling-proposal.md` (Recommended ruling, items 1–6), reproduced verbatim below as the binding text. Basis: `docs/audits/2026-09-22-phase0-p02-clarification-sol-NEEDS-OWNER.md`.

**Timing:** accepted before any P0-2 implementation and before any campaign arm has executed. No campaign results exist. No threshold, grid, seed, objective or fitted dimension changes.

## Binding ruling (items 1–6 of the proposal, verbatim)

1. Retain the fixed five targets and explicit target-level TRUE / FALSE / UNKNOWN detection values. Do not choose a tied minimizer. Undefined estimate/error/E_i fields are null.
2. Software status is PASS when all declared cells/invariants complete and ties/unknowns are reported faithfully. A tie alone is not software failure.
3. R_i >= 0.25 establishes target detection TRUE regardless of undefined selected-candidate diagnostics. Otherwise unresolved selected-candidate clauses remain UNKNOWN.
4. Record D known detections, U unknown targets and attainable count [D,D+U]. Threshold k remains 3 for P0-2A and 4 for P0-2B. D >= k yields misspecification_detection=PASS; D+U < k yields FAIL; otherwise misspecification_detection=null with reason indeterminate_tied_minima.
5. The overall Phase-0 exit gate remains binary: it can PASS only if every required arm is proven PASS. An indeterminate arm therefore leaves the exit gate FAIL/not established, explicitly due to unresolved evidence, without converting unknown targets into non-detections.
6. Preserve and hash the accepted ruling alongside the unchanged original predeclaration in campaign provenance. Implementation remains ci-only and no execution occurs before independent review.

## Clarifications the ruling carries (from the Sol basis; no new rule)

- "Tie" means the declaration's existing numerical-tie definition, `tau_i = 1e-12 * max(1, L_i,min)`; no new tolerance.
- A target whose selected-candidate clauses are uniquely evaluable is TRUE or FALSE by the declared predicate; only clauses made undefined by a tied wrong-model minimum yield UNKNOWN.
- Forbidden: truth-informed, lexicographic, first-in-grid, any-minimizer, all-minimizer, or count-unknown-as-failure resolution; importing P0-1's tie-fails rule into P0-2.
- Overall P0-2 PASS = both arms software_status=PASS and misspecification_detection=PASS (declaration §3, line 256).
