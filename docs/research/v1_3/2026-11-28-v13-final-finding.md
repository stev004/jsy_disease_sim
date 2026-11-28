# JOS V1.3 — final finding: outbreak timing is not reliably recoverable (synthetic studies, 2026-09 → 2026-11)

**Status:** FINAL. V1.3 STOPS before real-data fitting (G51 = A, Steven, 2026-11-28). This is a synthetic, research-software finding about the designs tested. It is not a validated statement about Jersey, and nothing in JOS is calibrated or validated.

**Status phrase:** Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL; G43: L1 FAIL, L2 FAIL, L3 FAIL, L4 FAIL, L5 PASS, L6 FAIL

## The question

V1.3 was meant to fit JOS to real Jersey surveillance data. Before doing that, each study asked a simpler question on synthetic data, where the true values are known: given daily symptomatic and asymptomatic case reports from a simulated outbreak, can the fitting procedure recover four quantities? The four were transmission strength (beta), the day the outbreak was seeded (inoculation-day offset), and the two detection probabilities. Every study was predeclared and frozen before running, had an independent implementation review, ran exactly once, and was confirmed by a separate exit audit.

## What the four studies found

| Study | Design (one change at a time) | Result | Where it failed | Exit audit |
|---|---|---|---|---|
| Phase 0 | 5 targets, 3-point grids, R = 3 candidate replicates | FAIL | inoculation offset at a grid edge for 2/5 targets (max 1/5) | `docs/audits/2026-09-24-phase0-exit-audit-sol-FAIL.md` |
| Phase 0b | fresh seeds, wider grids | FAIL | offset selections 4, 4, 0, 2, 0 against truth 2; 4/5 at grid edges | `docs/audits/2026-09-26-phase0b-exit-audit-sol-FAIL.md` |
| G35-B | baseline vs (i) R = 12 replicates, (ii) 49-day window, (iii) serosurvey anchor; 10 targets | B FAIL, i PASS, ii FAIL, iii FAIL | every failure includes offset hits (P5); arm i passed with four counts exactly at threshold | `docs/audits/2026-11-19-g35b-campaign-exit-audit-opus-CONFIRMED.md` |
| G43 | arm (i) repeated: six independent R = 12 libraries on 20 shared fresh targets | MIXED: 1 of 6 PASS (L5, one-target margin) | all five failing libraries missed on the offset (13–15/20 hits; 16 needed), four also on a detection probability (L1, L2, L4, L6), and the same four had joint-hit and/or boundary failures; 0 of 24 R = 3 batches met the criteria | `docs/audits/2026-11-27-g43-campaign-exit-audit-astra62-CONFIRMED.md` |

Across all four, beta and the two detection probabilities were usually recovered within tolerance. The outbreak start day was not. G43 was the decisive test of the one hopeful sign (G35-B arm i). On byte-identical targets, whether the frozen gate passed depended on which candidate library was drawn, so the arm-i pass is not a property of using more replicates.

## The finding

Under these designs (CI-mode synthetic Jersey populations of 3,000 residents, 30-day windows, two reported case channels, the frozen grids and loss), **the outbreak start day is not reliably identifiable from daily case reports**. It trades off against transmission strength and detection, as the exploratory ridge diagnostic showed (`docs/research/v1_3/2026-09-29-phase0b-ridge-diagnostic-EXPLORATORY.md`). More candidate replicates per cell did not fix it (G43), a longer window did not fix it, and neither did the serosurvey anchor as designed (G35-B ii, iii).

What this does **not** show:
- that timing is unrecoverable from any data: other observation streams or designs were not tested beyond G35-B's arms;
- anything about the real Jersey epidemic;
- a probability that a library passes: "1 of 6" is an observed count, not an estimate with an interval.

## Consequences

- **Real-data fitting stays STOPPED** (G34 A+B; G51 = A). No JOS output may be described as fitted, calibrated or validated against Jersey data.
- **JOS remains a scenario tool.** Scenario runs ("if an outbreak were seeded like this and these interventions applied, what follows?") do not depend on this fit, and their caveats are unchanged. Ensemble bands remain stochastic replicate variation, not confidence intervals.
- **Re-opening** needs a new Steven decision and a fresh owner-ruled, frozen predeclaration. The options recorded at G51 were conditional fitting with timing fixed as a stated assumption (a labelled demo, no recovery claim), or a design using a different observation stream, for example a real serosurvey, if such data exist.

## Evidence

- Frozen G43 predeclaration: `docs/research/v1_3/2026-11-20-g43-predeclaration.md` (`fc16adc`, sha256 `67c3c7c0…1094`). Harness merged to main at `c0821180d73b258ad29fa5578b1fbf5643a4b8cb` (G49).
- G43 bundle: `/home/steven/jos-g43-campaign-20261127/bundle` (sealed read-only; SHA256SUMS sha256 `a8c51550490a1fdd956d7615fdd93408b558d19737efb0299e333711c104fdc3`); copies of the summary and manifest under `docs/runs/2026-11-27-g50-*`.
- G35-B bundle: `/home/steven/jos-g35b-campaign-20261022T234254Z` (SHA256SUMS sha256 `e6649a4b…c8fc`).
- Decision trail: `.claude/decisions.tsv`, gates G31–G51 in `.claude/GATES.md`.
