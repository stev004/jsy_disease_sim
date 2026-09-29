# Phase-0b P0-1 ridge diagnostic (EXPLORATORY — not a gate)

## Status and lineage

**Phase 0: FAIL (2026-09-24). Phase 0b: FAIL (2026-09-26).** G34 A+B stops V1.3 before real-data fitting and authorizes successor design work only. This retrospective diagnostic changes no verdict, predicate, threshold, or pass rule. The Phase-0b bundle was produced after a reviewed population-generator fix and a same-seed rerun. **Four of the eight frozen process populations used the popgen fallback:** target seeds 62001, 62002, 62003 and candidate seed 63002.

The calculations below use the retained P0-1 surfaces and observed tables. An offset is the day of a scheduled synthetic import pulse, not a report-date shift. The implemented loss compares both daily report channels over **34 dates**: a 30-day latent run plus a four-day observation tail. It squares differences between the target’s square-root counts and the **mean of three separately square-root-transformed candidate replicates**.

## Q1. Loss profiled over offset

Each entry is the minimum loss at that offset, followed by its argmin `(beta, symptomatic detection, asymptomatic detection)`. The conditional argmin is unique in every column.

| Target | Offset 0 | Offset 1 | Offset 2 | Offset 3 | Offset 4 |
|---|---|---|---|---|---|
| 62001 | 0.708501 `(0.06, 1.00, 0.325)` | 0.441488 `(0.06, 1.00, 0.40)` | 0.373731 `(0.08, 0.75, 0.25)` | 0.356942 `(0.08, 0.75, 0.25)` | **0.226994** `(0.08, 0.75, 0.325)` |
| 62002 | 0.529999 `(0.06, 0.875, 0.25)` | 0.323625 `(0.06, 1.00, 0.325)` | 0.276434 `(0.06, 1.00, 0.325)` | 0.327780 `(0.06, 1.00, 0.325)` | **0.224612** `(0.08, 0.75, 0.25)` |
| 62003 | **0.334549** `(0.08, 0.75, 0.25)` | 0.457098 `(0.10, 0.625, 0.25)` | 0.343390 `(0.10, 0.625, 0.25)` | 0.617815 `(0.12, 0.625, 0.175)` | 0.711067 `(0.12, 0.625, 0.25)` |
| 62004 | 0.324707 `(0.08, 0.75, 0.325)` | 0.349685 `(0.10, 0.625, 0.25)` | **0.282804** `(0.10, 0.625, 0.25)` | 0.448275 `(0.10, 0.625, 0.25)` | 0.474987 `(0.12, 0.625, 0.25)` |
| 62005 | **0.372013** `(0.08, 0.75, 0.25)` | 0.464658 `(0.10, 0.625, 0.25)` | 0.408021 `(0.10, 0.625, 0.175)` | 0.481984 `(0.10, 0.625, 0.175)` | 0.556914 `(0.12, 0.625, 0.175)` |

The spot-check for **62004 is exact**: offset 0 has `(beta, symptomatic detection) = (0.08, 0.75)` and offset 4 has `(0.12, 0.625)`. Across all five targets, beta is nondecreasing and symptomatic detection is lower at offset 4 than at offset 0. The stronger claim that symptomatic detection falls *at every step in every target* is false: 62002 rises from `0.875` to `1.00` between offsets 0 and 1. Asymptomatic detection has no consistent direction.

Only 62001’s loss decreases monotonically. The other four profiles reverse direction; 62002 even has a secondary low point at offset 2. These are **ragged profiles, not flat profiles**. Their global minima reproduce the filed offsets `4, 4, 0, 2, 0`, against truth 2.

## Q2. H2: early exponential timing–detection confound

The following descriptive check uses combined symptomatic and asymptomatic reports on latent days 2–29, excluding the four-day tail. Weekly bins show whether growth continues through the observed run. The \(R^2\) is from an ordinary straight-line fit to `log(daily count + 3/8)` over days 2–29; it is a shape summary, not a fitted epidemic model.

| Target | Reports, days 2–8 / 9–15 / 16–22 / 23–29 | Log-line \(R^2\) | Late shape | Local secondary infections retained |
|---|---|---:|---|---:|
| 62001 | 8 / 55 / 285 / 588 | 0.886 | Still rising | 1,958 |
| 62002 | 6 / 48 / 244 / 521 | 0.905 | Still rising | 1,828 |
| 62003 | 11 / 158 / 474 / 420 | 0.710 | Weekly peak passed | 2,124 |
| 62004 | 12 / 119 / 463 / 488 | 0.778 | Near plateau | 2,124 |
| 62005 | 10 / 123 / 442 / 487 | 0.780 | Near plateau | 2,144 |

**Hypothesis assessment:** The first two series have long, approximately exponential rises, although their successive weekly growth factors shrink. The third has passed a weekly peak by day 29; the fourth and fifth are near a plateau. Thus a single early exponential is a useful approximation for part of the data, especially 62001–62002, but not for the whole scored series. The four-day report tail follows the end of latent simulation and should not be treated as independent evidence of natural epidemic decline.

In the simple approximation \(y(t)\approx pA\exp[r(t-t_0)]\), moving \(t_0\) later while holding \(r\) fixed would require **higher**, not lower, detection \(p\) to preserve the same amplitude. The observed fall in symptomatic detection therefore does **not** match a pure \(p\)-versus-\(t_0\) product confound. Beta rises at the same time, plausibly changing growth and amplitude enough to permit a *joint* beta–timing–detection tradeoff. The retained surfaces support that tradeoff as a hypothesis; they cannot establish its causal mechanism. The large local-infection counts make susceptible depletion plausible, but the report curves and counts alone do not isolate depletion from network dynamics, observation delay, and finite-run effects.

## Q3. H3: candidate-replicate noise floor

All three observed candidate tables are retained at each cell. I recomputed the published three-replicate loss at every profile minimizer; the largest absolute discrepancy was below `4×10⁻¹⁶`. At each fixed tuple, I then omitted each candidate replicate in turn and calculated a three-deletion jackknife estimate of the three-replicate loss’s Monte-Carlo standard error. For adjacent offsets I applied the same deletion to both tuples, preserving the shared candidate seed pairing. These are **rough scatter estimates from only three process/observation pairs**, not confidence intervals or tests.

Each cell below is signed adjacent loss change `L(offset + 1) − L(offset)` with its paired jackknife standard error in brackets.

| Target | 0→1 | 1→2 | 2→3 | 3→4 | Jackknife SE at published minimum |
|---|---:|---:|---:|---:|---:|
| 62001 | −0.26701 `[0.27983]` | −0.06776 `[0.08004]` | −0.01679 `[0.09054]` | −0.12995 `[0.01542]` | 0.04191 |
| 62002 | −0.20637 `[0.32574]` | −0.04719 `[0.03980]` | +0.05135 `[0.03471]` | −0.10317 `[0.04617]` | 0.01921 |
| 62003 | +0.12255 `[0.33615]` | −0.11371 `[0.18225]` | +0.27442 `[0.15258]` | +0.09325 `[0.09300]` | 0.18495 |
| 62004 | +0.02498 `[0.15710]` | −0.06688 `[0.02774]` | +0.16547 `[0.06308]` | +0.02671 `[0.06821]` | 0.00536 |
| 62005 | +0.09264 `[0.20350]` | −0.05664 `[0.12335]` | +0.07396 `[0.07857]` | +0.07493 `[0.04079]` | 0.15290 |

Across the 25 fixed profile tuples, median jackknife standard error is **0.05254**; median absolute adjacent profile change is **0.08379**. Only **4 of 20** adjacent changes exceed twice their paired scatter estimate. That comparison is descriptive: profiling selects tuples from the same noisy surface, and three replicates make the jackknife itself unstable.

As a second sensitivity check, I reprofiled all 625 cells after each candidate-replicate deletion. The resulting selected offsets were:

| Target | Published, three replicates | Omit 63001/73001 | Omit 63002/73002 | Omit 63003/73003 |
|---|---:|---:|---:|---:|
| 62001 | 4 | 4 | 4 | 4 |
| 62002 | 4 | 4 | 4 | 4 |
| 62003 | 0 | 0 | 2 | 0 |
| 62004 | 2 | 2 | 2 | 2 |
| 62005 | 0 | 2 | 1 | 0 |

**A generic one-day step is not reliably resolved above the retained scatter.** Some particular contrasts are larger, and 62001–62002 keep their boundary choices under these deletions. The bundle lacks *independent candidate batches at the same fixed tuples*, so it cannot directly measure the sampling distribution of a fresh three-replicate objective or of its selected offset. A successor seeking that measurement must retain each candidate replicate’s two-channel table or transformed vector, seed and population lineage, plus multiple independent, predeclared replicate batches at identical tuples. Separate process and observation variation would require a design that varies those seed streams separately.

## Q4. Weighing H1, H2 and H3

| Hypothesis | Assessment from retained evidence |
|---|---|
| **H1: offset carries little information** | **Weak support for a blanket claim.** Profiles are not flat, and 62001, 62002 and 62004 keep their selected offset in every deletion check. Practical one-day resolution can still be poor. |
| **H2: a fitted-parameter ridge** | **Moderate descriptive support** for a joint beta–offset–detection tradeoff: beta rises and symptomatic detection falls between endpoint argmins in all five targets. The pure exponential \(p\)-offset mechanism has the wrong detection direction and does not explain late plateaus or the ragged profiles. |
| **H3: Monte-Carlo noise affects the profile** | **Substantial support**, with limited precision: most adjacent changes are comparable to their estimated scatter, and deleting one candidate replicate changes the selected offset for 62003 or 62005. Noise alone does not explain the stable boundary choices for 62001–62002. |

Predicate 8’s **4/5 boundary count remains the valid, failed gate result**. As a diagnostic, a boundary choice usefully flags that the finite grid may truncate a better fit. Its count is not a measure of offset precision or proof of a structural ridge. In the exploratory deletion exercise the boundary count ranges from **2/5 to 4/5**, while the two offset-4 targets remain at that edge. The noise weakens causal interpretation of the aggregate count; it does not undo the filed FAIL.

## Q5. Successor design input only

- **Longer observation window:** Plausibly helps if it captures growth, peak and decline generated by the same seeding event; a longer tail alone cannot do this. A synthetic comparison should keep population construction, truth, parameters, reporting model, target and candidate seed streams, objective definition and fitting grid fixed, extend the latent trajectory, and compare matched observation prefixes.
- **Independent detection anchor:** A separately modeled serosurvey constraining cumulative infection could help separate infection scale from report detection. It must have its own sampling, timing and measurement semantics; cumulative infection must not be substituted with episode incidence. Compare otherwise identical synthetic fits with and without that anchor while fixing its assumed quality and the target trajectories.
- **More candidate replicates:** Plausibly reduces Monte-Carlo scatter and clarifies small loss differences, but cannot remove a structural tradeoff. Use nested, fresh candidate-replicate sets against the same targets, population rules, candidate cells, observation model and scoring rule. Examine both fixed-tuple scatter and the stability of the **reprofiled** offset.

These are factors to test, not numbers or thresholds for a successor pass rule. All Phase-0b target and candidate process/observation seeds (`62001–62005`, `63001–63003`, `72001–72005`, `73001–73003`) are retired. A successor needs fresh seeds and pass thresholds justified by argument before execution.

## Limitations and provenance

This is a retrospective assessment of five synthetic targets, one target observation realization each, and three paired candidate replicates. It cannot distinguish process noise from observation noise, estimate a reliable sampling distribution from three deletions, inspect losses beyond the offset grid, prove depletion caused a peak, or establish which proposed design change would recover timing. The square-root distance is **not a likelihood**. All replicate spreads here describe stochastic replicate variation, never confidence intervals.

`sha256sum -c SHA256SUMS` passed for all **4,043** listed bundle files. The verified `SHA256SUMS` digest is `a319c5557ffa77c56baebb8341b5fc2e1432f367bdb9d0b34169aa079659032a`. Code semantics were read from clone SHA `e8c33d47f1271d8216d596b1e15f15685e532953`, especially [phase0_campaign.py](/home/steven/jos-ridge-readonly/src/jersey_outbreak/phase0_campaign.py) and [respiratory.py](/home/steven/jos-ridge-readonly/src/jersey_outbreak/respiratory.py), alongside the [Phase-0b exit audit](/home/steven/jos-ridge-readonly/docs/audits/2026-09-26-phase0b-exit-audit-sol-FAIL.md), [failure mode](/home/steven/jos-ridge-readonly/docs/research/v1_3/2026-09-26-phase0b-failure-mode.md), and [G34-B draft memo](/home/steven/jos-ridge-readonly/docs/research/v1_3/2026-09-29-successor-offset-design-memo-DRAFT.md).

**Script used:** `/tmp/phase0b_ridge_diag.py` (SHA-256 `9a1c101e3ca2c0aa8fe907cbc43ba3404dcb62f3641ca0be69cc442620488ecd`). **No simulation and no bundle or clone edits**; the clone remained clean.