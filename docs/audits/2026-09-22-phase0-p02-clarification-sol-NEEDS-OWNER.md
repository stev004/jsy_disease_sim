NEEDS OWNER RULING

## P0-2 tied-minimum clarification addendum

The frozen contract does not unambiguously define P0-2 handling when a wrong-model minimum is tied and selected-candidate diagnostics are consequently undefined. An owner ruling is required before implementation. No truth-informed, lexicographic, first-in-grid, “any minimizer,” or “all minimizers” rule may be inferred.

This addendum assumes the tie has already been identified under the declaration’s existing numerical-tie definition; it introduces no new tolerance.

### Contract-supported interpretation

For either P0-2 arm:

- `software_status=PASS` if every declared cell completed, all execution invariants held, and the tie and undefined outputs were reported faithfully. A tied scientific result is not itself a software failure. This follows the required separation of software completion from scientific behavior ([predeclaration lines 194–203](/home/steven/jos-p02-clarify-readonly/docs/research/v1_3/2026-09-21-phase0-predeclaration.md:194)).
- Silently choosing a tied candidate, or fabricating an estimate or `E_i`, would violate the contract and cannot support `software_status=PASS`. Truth-distance selection is expressly forbidden ([lines 101–109](/home/steven/jos-p02-clarify-readonly/docs/research/v1_3/2026-09-21-phase0-predeclaration.md:101)).
- \(R_i\) remains defined from the scalar minimum losses, regardless of which candidate attains the wrong-model minimum ([lines 205–210](/home/steven/jos-p02-clarify-readonly/docs/research/v1_3/2026-09-21-phase0-predeclaration.md:205)).

For P0-2A:

- If \(R_i \ge 0.25\), target-level detection is `TRUE`; the declared OR predicate is satisfied independently of the ambiguous estimate.
- If \(R_i < 0.25\) and the recovered inoculation day or tolerance-error clauses cannot be uniquely evaluated, target-level detection is `UNKNOWN`, not `FALSE`.
- The specification supplies no rule for evaluating those clauses over a set of tied minimizers ([lines 219–225](/home/steven/jos-p02-clarify-readonly/docs/research/v1_3/2026-09-21-phase0-predeclaration.md:219)).

For P0-2B:

- If \(R_i \ge 0.25\), target-level detection is `TRUE`.
- If \(R_i < 0.25\) and no unique selected candidate exists, then \(E_i\) and any selected beta/timing error are undefined. Target-level detection is therefore `UNKNOWN`, not `FALSE`.
- \(E_i\) is explicitly defined for “the selected wrong-model candidate”; the contract does not define it over multiple minimizers ([lines 240–254](/home/steven/jos-p02-clarify-readonly/docs/research/v1_3/2026-09-21-phase0-predeclaration.md:240)).

P0-1’s explicit tie failure cannot silently be imported into P0-2: it is stated specifically as a P0-1 condition ([lines 138–155](/home/steven/jos-p02-clarify-readonly/docs/research/v1_3/2026-09-21-phase0-predeclaration.md:138), [lines 175–188](/home/steven/jos-p02-clarify-readonly/docs/research/v1_3/2026-09-21-phase0-predeclaration.md:175)).

### Fixed five-target aggregates

Unknown targets remain among the fixed five. They must not be removed from the denominator or silently counted as either detection or non-detection.

Let \(D\) be known `TRUE` detections and \(U\) be `UNKNOWN` targets:

- P0-2A is proven `PASS` if \(D \ge 3\).
- P0-2B is proven `PASS` if \(D \ge 4\).
- If \(D+U\) is below the applicable threshold, the arm is proven not to pass.
- If \(D\) is below the threshold but \(D+U\) reaches it, the aggregate is indeterminate.

The frozen contract does not provide a serialized status for that indeterminate case. The owner must authorize one before implementation. Until then, the implementation must preserve \(D\), \(U\), the attainable interval \([D,D+U]\), and leave `misspecification_detection` unset rather than inventing a PASS/FAIL result.

Consequently, overall P0-2 `PASS` is established only when both arms have software `PASS` and scientifically proven detection `PASS`, as required by [line 256](/home/steven/jos-p02-clarify-readonly/docs/research/v1_3/2026-09-21-phase0-predeclaration.md:256).

### Deterministic examples

1. **Loss degradation resolves a tie:** \(L^{correct}_{\min}=1.00\), while distinct wrong-model candidates \(a\) and \(b\) both have loss \(1.30\). Thus \(R_i=0.30\). The selected estimate and, for P0-2B, \(E_i\), may be undefined, but target detection is `TRUE` through \(R_i\). Software status remains `PASS`.

2. **P0-2A unresolved:** \(L^{correct}_{\min}=1.00\); candidates \(a\) and \(b\) tie at \(1.10\). Candidate \(a\) has inoculation day `4`, while \(b\) does not. Hence \(R_i=0.10\), and no unique recovered inoculation day exists. Detection is `UNKNOWN`, not `FALSE`.

3. **P0-2B unresolved and aggregate-preserving:** \(L^{correct}_{\min}=2.00\); candidates \(a\) and \(b\) tie at \(2.20\). Candidate \(a\) would give \(E_i=0.10\) with beta/timing within tolerance; candidate \(b\) would give \(E_i=0.40\). Thus \(R_i=0.10\), but `E_i` and target detection are `UNKNOWN`. If the five target states are `TRUE, TRUE, TRUE, FALSE, UNKNOWN`, P0-2B’s attainable count is `[3,4]`; its `4/5` predicate is indeterminate, not PASS or FAIL.

Adopting a deterministic ordering, set-wise any/all rule, count-as-failure rule, or automatic P0-1-style tie failure would add a scientific/reporting rule not present in the frozen specification. The standing order “explicit unknown beats false precision” and separation of scientific choices from implementation reinforce escalation rather than invention ([DIRECTOR.md lines 28–29](/home/steven/jos-p02-clarify-readonly/.claude/DIRECTOR.md:28)).

### Attestation

- HEAD at start and end: `29d44485c0871b57524a4a26ce38262e57f4ec04`
- Frozen specification SHA-256: `ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104`
- Initial and final `GIT_OPTIONAL_LOCKS=0 git status --porcelain`: empty
- Source, data, schemas, hashes, tracked files, and untracked files changed: none
- Tests, simulations, fits, pilots, and campaign arms executed: none
- Commits, pushes, and external messages: none