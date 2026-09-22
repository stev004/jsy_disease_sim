# PROPOSED — G29 P0-2 indeterminate detection handling

Requires Steven's model-owner ruling before P0-2 implementation. No campaign results exist and no thresholds, grids, seeds or fitted dimensions change.

Recommended ruling:

1. Retain the fixed five targets and explicit target-level TRUE / FALSE / UNKNOWN detection values. Do not choose a tied minimizer. Undefined estimate/error/E_i fields are null.
2. Software status is PASS when all declared cells/invariants complete and ties/unknowns are reported faithfully. A tie alone is not software failure.
3. R_i >= 0.25 establishes target detection TRUE regardless of undefined selected-candidate diagnostics. Otherwise unresolved selected-candidate clauses remain UNKNOWN.
4. Record D known detections, U unknown targets and attainable count [D,D+U]. Threshold k remains 3 for P0-2A and 4 for P0-2B. D >= k yields misspecification_detection=PASS; D+U < k yields FAIL; otherwise misspecification_detection=null with reason indeterminate_tied_minima.
5. The overall Phase-0 exit gate remains binary: it can PASS only if every required arm is proven PASS. An indeterminate arm therefore leaves the exit gate FAIL/not established, explicitly due to unresolved evidence, without converting unknown targets into non-detections.
6. Preserve and hash the accepted ruling alongside the unchanged original predeclaration in campaign provenance. Implementation remains ci-only and no execution occurs before independent review.

Alternative: hold P0-2 while Steven requests a different pre-execution specification. No deterministic, first-in-grid, truth-informed, any/all-minimizer or count-as-failure rule is assumed.

Default on no answer: HOLD P0-2 implementation and all campaign execution. Complete already-authorized P0-1 verification and preserve its branch.

Basis: docs/audits/2026-09-22-phase0-p02-clarification-sol-NEEDS-OWNER.md, read-only Sol consult on 29d44485c0871b57524a4a26ce38262e57f4ec04, session 01a0c69e-9418-7b01-9b4f-689a7eb75895; 30431 tokens. The original predeclaration remains immutable with SHA256 ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104.
