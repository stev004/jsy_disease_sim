NUMERICAL CONTRACT: BLOCKED

This is a numerical implementation defect, not a scientific campaign failure. No campaign has run, so no Phase-0 scientific verdict is available.

## Findings

At exact detached HEAD `b5ef032e29c577bce634ce0933b2d7d316ac562e`, YAML decimal values are converted to binary `float` ([phase0_campaign.py:203](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:203)). Recovery error is then calculated by direct float subtraction ([phase0_campaign.py:421](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:421)).

Consequently, the declared inclusive asymptomatic endpoint is rejected:

```text
estimate 0.40 - truth 0.25
float absolute error: 0.15000000000000002
declared tolerance:   0.15
current comparison:   False
exact decimal result: 0.15 <= 0.15, True
```

The frozen specification explicitly requires `absolute error <= tolerance` ([predeclaration.md:157](/home/steven/jos-p01-numeric-readonly/docs/research/v1_3/2026-09-21-phase0-predeclaration.md:157)), with the relevant values declared at [predeclaration.md:30](/home/steven/jos-p01-numeric-readonly/docs/research/v1_3/2026-09-21-phase0-predeclaration.md:30) and [v13_phase0_synthetic.yaml:25](/home/steven/jos-p01-numeric-readonly/configs/calibration/v13_phase0_synthetic.yaml:25).

Affected paths are:

- Descriptive coverage: `error <= tolerance` at [phase0_campaign.py:1371](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:1371) falsely excludes an identified `0.40` estimate.
- Joint coverage: `error > tolerance` at [phase0_campaign.py:1417](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:1417) falsely rejects the entire recovery row.
- Signed error and emitted recovery data record `0.15000000000000002`, not the declared-decimal difference.
- Bias aggregation at [phase0_campaign.py:1395](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:1395) inherits this asymmetry. For one `0.40` and one `0.10` estimate plus three truths, the mathematically cancelling errors produce `5.551115123125783e-18`, not zero.
- The bias predicate at [phase0_campaign.py:1403](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:1403) is not observed to flip for this frozen campaign: exhaustive enumeration of all `3^5` selections for each dimension found that none of the four half-step bias endpoints is reachable on the declared five-seed grids, and no bias-pass mismatches occurred. The descriptive value is nevertheless contaminated.

The other frozen recovery endpoints currently classify correctly. In particular, `0.10−0.25` happens to yield `-0.15`, while `0.40−0.25` yields the larger representation. Beta’s upper error yields `0.039999999999999994` and passes. This asymmetry confirms that relying on incidental binary rounding is not a valid contract implementation.

Boundary counting itself is unaffected: [phase0_campaign.py:1316](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:1316) compares selected values copied directly from the same grid. The `4/5` and `3/5` aggregate comparisons also reproduce identical floats on each side.

A related coverage gap exists at the profile-gap predicate ([phase0_campaign.py:1050](/home/steven/jos-p01-numeric-readonly/src/jersey_outbreak/phase0_campaign.py:1050)): hand-entered decimal values `0.100` and `0.105` produce a float relative gap of `0.049999999999999906`, which fails the inclusive `>= 0.05` test. Unlike the recovery grid, production objective values are computed from square roots and have no frozen exact-decimal representation. I therefore do not recommend silently applying decimal-string semantics there; its exact-boundary meaning remains an untested numerical-specification question, not a demonstrated campaign failure.

## Smallest correct remedy

Keep simulation inputs, objective calculations, schemas, hashes, and candidate cells unchanged. At the truth-joined recovery layer only:

1. Convert selected grid value, truth, tolerance, and bias limit using `Decimal(str(value))`.
2. Compute signed errors, absolute errors, sums, means, and inclusive recovery/bias comparisons in `Decimal`.
3. Convert descriptive values to ordinary floats only when emitting the existing output fields.

This exactly implements the frozen finite-decimal grid without epsilon inflation, altered tolerances, or rounding. `Decimal(str(...))` is appropriate here because selected estimates and truths are direct members of the frozen decimal grid. It is not a generic repair for arbitrary computed floats: for values produced by optimizers, transforms, or irrational objective arithmetic, the original decimal intent cannot be recovered from `str(float)`.

A genuinely obvious one-line director fix does not suffice. Fixing only the coverage comparison leaves joint coverage and bias arithmetic inconsistent. Centralizing corrected subtraction in `signed_error` would still require a new exact representation/import and regression coverage; keeping exact arithmetic through the bias predicate is the robust bounded correction.

The bounded Luna correction should touch only:

- the recovery/error arithmetic within `phase0_campaign.py`;
- focused tests in `test_phase0_campaign.py`.

It must not alter the YAML, predeclaration, declaration hash, blind-fit objective/profile definitions, estimate/config hashes, schemas, seeds, statuses, or campaign orchestration.

## Required regressions

Failing before and passing after:

1. `selected asymptomatic=0.40`, truth `0.25`: exact absolute error is `0.15` and is inside the inclusive `0.15` tolerance.
2. Five identified rows containing one `0.40` and four `0.25` selections: asymptomatic coverage and joint coverage both remain `1.0`, not `0.8`.
3. Exactly three intended joint hits, one using `0.40`, with two independently non-identified rows: joint coverage is exactly `3/5` and its predicate passes. This directly detects the current false `2/5`.
4. Selections `0.40, 0.10, 0.25, 0.25, 0.25`: mean signed asymptomatic bias is exactly zero.
5. Table-driven checks for both endpoints of every frozen dimension, preserving inclusive behavior and preventing one-sided regressions.
6. Confirm blind estimate hashes and declaration/config hashes are unchanged, since recovery arithmetic occurs only after truth join.

## Existing test coverage

There are 21 test functions, with one two-case parametrization, giving 22 focused cases statically.

The closest test is [test_phase0_campaign.py:333](/home/steven/jos-p01-numeric-readonly/tests/test_phase0_campaign.py:333). It exercises beta’s upper endpoint, but that endpoint rounds downward and therefore does not expose the defect. Its asymptomatic selections all equal truth. Its bias assertion uses `pytest.approx(0.032)` and checks only a clearly failing limit, not cancellation or an inclusive endpoint.

[test_phase0_campaign.py:366](/home/steven/jos-p01-numeric-readonly/tests/test_phase0_campaign.py:366) checks beta’s lower error with `pytest.approx`, again not the asymmetric `0.40−0.25` case. No focused test covers the asymptomatic upper endpoint, a joint-coverage threshold made decisive by that endpoint, exact signed-error cancellation, or the exact 5% profile-gap boundary.

Per the brief, I did not run pytest or independently verify the reported 22/432 pass results or CI transcript.

## Probe evidence and attestation

Pure arithmetic probes used `/usr/bin/python3` outside the clone. Relevant verbatim output:

```text
beta
  0.04 0.04 True True
  0.08 0.0 True True
  0.12 0.039999999999999994 True True
  bias_boundary_reachable False bias_predicate_mismatches 0
inoculation_day_offset
  0 2.0 True True
  2 0.0 True True
  4 2.0 True True
  bias_boundary_reachable False bias_predicate_mismatches 0
symptomatic_detection_probability
  0.50 0.25 True True
  0.75 0.0 True True
  1.00 0.25 True True
  bias_boundary_reachable False bias_predicate_mismatches 0
asymptomatic_detection_probability
  0.10 0.15 True True
  0.25 0.0 True True
  0.40 0.15000000000000002 False True
  bias_boundary_reachable False bias_predicate_mismatches 0
decimal_to_float_remedy 0.15 True
```

Additional exact probe output:

```text
errors ['0.15000000000000002', '-0.15', '0.0', '0.0', '0.0']
mean_bias 5.551115123125783e-18
profile_gap_at_declared_endpoint 0.049999999999999906
profile_gap_passes False
coverage_endpoint_passes True
joint_endpoint_passes True
```

Start and end verification:

```text
GIT_OPTIONAL_LOCKS=0 git rev-parse HEAD
b5ef032e29c577bce634ce0933b2d7d316ac562e

GIT_OPTIONAL_LOCKS=0 git status --porcelain
<empty>
```

Final `git diff --check` and `git diff --stat` were empty. No files were written, no dependencies installed, and no simulations, observation transforms, fits, pilots, campaigns, commits, pushes, or external messages occurred.