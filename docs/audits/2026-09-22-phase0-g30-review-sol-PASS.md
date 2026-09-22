G30 NUMERICAL CORRECTION: PASS

No substantive defects found in the bounded correction.

Findings by severity:

- Critical/Major/Minor: none.
- Exact decimal recovery is confined to the truth-joined layer: subtraction and absolute error use `Decimal(str(...))` in [phase0_campaign.py](/home/steven/jos-g30-review-readonly/src/jersey_outbreak/phase0_campaign.py:422).
- Coverage, bias summation/mean, bias predicates, and joint predicates remain exact through comparison at [phase0_campaign.py](/home/steven/jos-g30-review-readonly/src/jersey_outbreak/phase0_campaign.py:1379). Conversion back to `float` occurs only for existing output fields at lines 1408–1419; JSON serialization succeeds with no `Decimal` leakage.
- Blind fitting and hashing remain upstream and unchanged. The estimate is hashed at line 1288, persisted at lines 1670–1684 and 1821–1822, then truth diagnostics and truth joining occur at lines 1823–1838. The mocked orchestration test explicitly checks persistence precedes every truth join.
- The objective, profile rules, grids, seeds, configuration, thresholds, schemas, and dependencies were unchanged. No epsilon, rounding, or threshold relaxation was introduced. The only new dependency is Python’s standard-library `decimal`.
- Tests are additions rather than weakened existing assertions. They directly cover all eight declared dimension endpoints, the asymptomatic upper endpoint, marginal and joint coverage, decisive `3/5`, exact cancellation, and pinned hashes in [test_phase0_campaign.py](/home/steven/jos-g30-review-readonly/tests/test_phase0_campaign.py:366).

Independently reproduced evidence:

- Candidate focused suite: **34 passed**.
- Retained before/after evidence: exact base produced **5 failed, 7 passed, 22 deselected** with real numerical assertion failures; candidate produced **12 passed, 22 deselected**.
- Missing/nonidentified probe: each marginal coverage and joint coverage was exactly `3/5`; a missing estimate left every bias `None`, confirming fail-closed handling and fixed five-seed denominators.
- Exact upper asymptomatic error was `Decimal("0.15")`, inclusive against `0.15`.
- Blind/config hash regression passed against both base and candidate:
  - estimate: `2ebc1f18a5dac62ec1432fc696e8c885c63cd53e818b8d8fbce0bcf7dad7421a`
  - candidate config: `d3a536deb456c471baaaecec59bfd8854483cb288f96f3df22828535a26f71d0`
- Base/head Git blob identities for the campaign configuration and predeclaration are identical. Predeclaration SHA-256 remains `ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104`.

Evidence limits:

- This is a bounded numerical code-review PASS, not a Phase-0 scientific gate PASS, calibration, or validation. No campaign or real-data fit ran.
- The director full suite is explicitly **not all green**: **1 failed, 443 passed, 4 skipped**. The sole job-ordering timing failure was reproduced unchanged on base and falls under the predeclared confirm-on-base exception documented in the [verification gate](/home/steven/jsy_disease_sim/docs/runs/2026-09-22-phase0-g30-verification-gate.md).
- The computed-objective 5% profile-gap exact-boundary question remains open and untouched at [phase0_campaign.py](/home/steven/jos-g30-review-readonly/src/jersey_outbreak/phase0_campaign.py:1049). This correction does not assign decimal-string semantics to computed objectives. G29 remains a separate model-owner ruling.

Final attestation:

- SHA: `367f0324685437c4d2ed4aa0ae4878229da09839`
- Base ancestry verified from `b5ef032e29c577bce634ce0933b2d7d316ac562e`
- Diff: exactly two expected files, **168 insertions, 15 deletions**
- Final `git status --porcelain`: empty
- No files modified, dependencies installed, campaigns run, commits made, or pushes performed.