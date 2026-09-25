# Phase-0b predeclaration (FROZEN)

**Status:** Frozen Phase-0b predeclaration, accepted with amendments by the model owner under Steven's 2026-09-25 delegation; the ruling is `docs/research/v1_3/2026-09-25-phase0b-owner-ruling-ACCEPTED.md` and is preserved and hashed alongside this document. Immutable once committed; its SHA-256 is fixed in the Phase-0b config and in an independent harness constant. Phase 0b was designed **after** the Phase-0 results were observed. It is a new campaign with fresh seeds. The Phase-0 exit verdict of 2026-09-24 is FAIL and remains FAIL regardless of the Phase-0b outcome.

The Phase-0 exit audit found one determinate failure: P0-1 selected inoculation offsets `0` and `4` for two of five targets, exceeding predicate 8’s `1/5` boundary limit. All other Phase-0 predicates passed. No Phase-0 result is reused as a Phase-0b observation or candidate prediction.

Repository document: `docs/research/v1_3/2026-09-25-phase0b-predeclaration.md`. Its SHA-256 is inserted into the Phase-0b config and checked against an independent harness constant before execution.

## 1. Scope and design basis

Phase 0b tests four-dimensional synthetic recovery, both misspecification arms, and the structural negative control in **one** CI-mode campaign. All four arms must be proven PASS in that campaign for its exit gate to PASS. The accepted G29 ruling governs P0-2 without amendment.

The design flaw is visible from the frozen Phase-0 text alone, without reference to any result: each truth was the middle of a three-point grid and the recovery tolerance was one grid step, so every point on every Phase-0 grid lay within tolerance. Predicate 5 could not fail. Predicate 8 (at most `1/5` boundary selections) therefore carried the entire recovery burden, and any tolerated one-step displacement was simultaneously a boundary selection. For the inoculation offset this happened twice (selections `0, 2, 2, 2, 4`); the same tension existed for beta and both detection probabilities regardless of what was observed there.

Phase 0b changes exactly one design quantity: grid resolution. It retains the four truths and evaluates five equally spaced points per dimension at half the Phase-0 spacing. The Phase-0 rules "recovery tolerance = one grid step" and "absolute mean-bias limit = half a grid step" are retained unchanged and re-evaluated on the new spacing, so both limits halve in absolute terms. A tolerated one-step displacement is now an interior point and a boundary selection is two steps from truth. The correction depends only on grid geometry, not on the direction or count of the observed Phase-0 misses; the Phase-0 selection pattern (two targets at the outer Phase-0 values) fails Phase 0b under predicates 5 and 8 alike.

Predicate 8 is retained verbatim — the same outermost values, the same `1/5` limit — because it is the predicate on which Phase 0 failed and must remain directly comparable. On the Phase-0b grids a boundary selection is outside tolerance, so predicate 5 logically implies predicate 8 whenever all five targets are assessed; predicate 8 is therefore not an independent gate in this design. It is nevertheless computed by its own code path, never derived from predicate 5, and its per-dimension boundary count is reported and gated. No predicate is added, removed, re-thresholded or re-specified. The model owner considered re-specifying predicate 8 as a joint-corner or pooled range-truncation check, or widening the grids to seven points, and rejected both: seven points at half spacing would require a negative inoculation offset and a symptomatic probability above `1`, and a new predicate would add post-result design surface that is not needed to correct the flaw.

The standalone research harness remains separate from production calibration manifests, artifact IDs, hashes, observation schemas, and DATA-9 semantics.

## 2. P0-1 recovery campaign

### Joint fitted dimensions

Evaluate every cell of the `5 × 5 × 5 × 5 = 625` grid. The five-point spacing and tightened limits are **synthetic Phase-0b campaign assumptions**, derived by halving each Phase-0 spacing. They are not Jersey estimates or pathogen defaults.

| Dimension | Synthetic truth | Candidate grid | Inclusive recovery tolerance | Absolute mean-bias limit |
|---|---:|---|---:|---:|
| Global transmission `beta` | `0.08` | `0.04, 0.06, 0.08, 0.10, 0.12` | `0.02` | `0.01` |
| One-off inoculation day offset | `2` | `0, 1, 2, 3, 4` days | `1` day | `0.5` day |
| Symptomatic detection probability | `0.75` | `0.50, 0.625, 0.75, 0.875, 1.00` | `0.125` | `0.0625` |
| Asymptomatic detection probability | `0.25` | `0.10, 0.175, 0.25, 0.325, 0.40` | `0.075` | `0.0375` |

`beta=0.08` and symptomatic detection `0.75` come from the pathogen-neutral disease and observation demo configurations. Offset `2` and asymptomatic detection `0.25` remain the Phase-0 synthetic challenge assumptions. The shipped asymptomatic demo value is `0.05`; Phase 0b does not change it.

### Fixed latent scenario

Use `ci` mode with 3,000 synthetic residents, start date `2025-01-06`, and exactly 30 latent days. Set initial seeds to zero. Schedule exactly ten import attempts on `start_date + inoculation_day_offset`; use zero background import rate and no other scheduled imports. Set all eleven route multipliers to `1.0`. Keep symptomatic probability `0.6`, constant latent duration `2` days, constant infectious duration `5` days, disabled waning, and no seasonality or interventions. No natural-history parameter is fitted.

These are pathogen-neutral demonstration scenario assumptions. They do not claim evidence for Jersey or a named pathogen.

### Observations and seeds

Keep detection delay `0`, reporting delay `2` days, seven weekday factors of `1.0`, and a four-day observation tail. Derive daily reported symptomatic and asymptomatic counts solely from `observation_events`. Zero-fill both channels across the common 34-date horizon. No real Jersey data enter the campaign.

The four Phase-0b seed sets below are mutually disjoint and disjoint from every Phase-0 seed. Their numbers are **synthetic reproducibility identifiers**, not scientific parameters.

| Role | Seeds | Observation config ID |
|---|---|---|
| Five target process/network runs | `62001–62005` | `v13-phase0b-target` |
| Five target observation transforms, paired in order | `72001–72005` | `v13-phase0b-target` |
| Three candidate process/network replicates | `63001–63003` | `v13-phase0b-fit` |
| Three candidate observation replicates, paired in order | `73001–73003` | `v13-phase0b-fit` |

Phase-0 seed sets, listed here so that cross-campaign disjointness is checked against a declared constant: targets `42001–42005` / `52001–52005`, candidates `43001–43003` / `53001–53003`, config IDs `v13-phase0-target` / `v13-phase0-fit`. The harness holds these as an independent module constant; a disjointness check whose expected values derive from the supplied config is a defect. All grid values, tolerances and bias limits are declared as decimal strings in the config and parsed with exact decimal arithmetic from those strings, never from binary floats.

Network and outbreak seeds match within each process run. Keep one candidate observation config ID across candidate cells for common random numbers. Candidate predictions may be reused across the five target fits and both P0-2 arms. Target runs may never serve as candidate predictions. There is no optimizer seed, replacement seed, retry, adaptive grid, pruning, refinement, or early stopping.

### Blind fit, objective, and identification

The fitter receives only the two target observed tables, declared grid, and candidate prediction library. It must not receive target truth, latent target events, target seeds, or target latent hashes. Write and hash every blind estimate before joining truth metadata. Score all 625 cells before selection.

For target \(i\), cell \(\theta\), channel \(c\), date \(t\), and candidate replicate \(j\), retain the Phase-0 minimum-distance objective:

\[
m_{\theta ct}=\frac{1}{3}\sum_{j=1}^{3}\sqrt{x_{j\theta ct}+3/8},
\qquad
L_i(\theta)=\frac{1}{2T}\sum_{c=1}^{2}\sum_{t=1}^{T}
\left(\sqrt{y_{ict}+3/8}-m_{\theta ct}\right)^2.
\]

This is not a likelihood. Profile each dimension by minimizing over the other three. Retain the numerical-tie rule
\(\tau_i=10^{-12}\max(1,L_{i,\min})\).
A dimension is identified only if its profile minimum is unique within \(\tau_i\) and its relative gap to the next distinct profile value is at least `0.05`, using denominator \(\max(P_{\min},10^{-12})\). A tied global minimum fails P0-1; no arbitrary tie break supplies an estimate.

Retain the Phase-0 numerical semantics: ordinary float inclusive comparisons for computed profile gaps and P0-2/P0-3 quantities. Use exact decimal arithmetic on the **declared finite-decimal grid** for signed recovery error, inclusive tolerance, and mean bias. Add endpoint and cancellation regressions for the new decimals. Do not add epsilons or reinterpret equality at `0.05`, `0.25`, or `1e-12`.

### Descriptive results and aggregate gate

For each dimension report signed error, absolute error, identified status, descriptive tolerance hits out of five, mean signed bias, and boundary count. Report joint four-dimensional hits out of five. These are descriptive rates, not confidence intervals.

P0-1 is PASS only if **all** conditions hold:

1. All five target runs, all 625 candidate cells, and all three candidate replicates per cell complete without replacement.
2. Each truth run realizes all ten inoculation acquisitions, at least one local secondary infection, reports in both channels, and at least three nonzero combined-report dates.
3. Observation chronology and latent-incidence conservation diagnostics pass.
4. No target has a numerically tied global minimum.
5. Every dimension is identified and within its tabled tolerance for at least `4/5` targets.
6. At least `3/5` targets are identified and within tolerance jointly in all four dimensions.
7. Every dimension’s absolute five-target mean bias is at or below its tabled limit.
8. No dimension is selected at its grid boundary (an outermost declared value on either side) for more than `1/5` targets. Computed independently of predicate 5 and reported per dimension; on this grid it is implied by predicate 5 (section 1).
9. Seeds, namespaces, grids, objective, dates, fixed parameters, read-back and blind-fit provenance match this declaration.
10. Measured work remains within the caps in section 5.

A poor or extinct candidate is scored. An extinct or uninformative truth is a gate failure and is never resampled.

## 3. P0-2 misspecification injections

**Run both arms again** using the Phase-0b targets and candidate latent cache. Phase-0 P0-2 PASS results cannot be carried forward: they concerned different observations and a different correct-model grid. The Phase-0b all-arms gate requires contemporaneous evidence from one campaign.

Keep separate `software_status` and `misspecification_detection` statuses. A wrong model’s poor fit is an expected scientific result, not a software failure. Define, for each target,

\[
R_i=\frac{L^{wrong}_{i,\min}-L^{correct}_{i,\min}}
{\max(L^{correct}_{i,\min},10^{-9})}.
\]

### P0-2A: wrong reporting delay

Truth uses reporting delay `2`; the fitted arm forces delay `0`. Keep the full Phase-0b `625`-cell fitted grid, all other parameters, seeds, and common-random-number namespace.

A target detects misspecification if any of these holds: its selected inoculation offset is `4` (the same two-day compensating shift specified in Phase 0); any fitted dimension is outside its **Phase-0b** tolerance; or \(R_i\ge0.25\). Detection requires at least `3/5` targets.

Offset `4` is two Phase-0b grid steps from truth, so the first clause is implied by the second on this grid. All three clauses are retained verbatim from Phase 0. Each clause's per-target value (`TRUE` / `FALSE` / `UNKNOWN` under G29) is computed by its own code path and recorded in its own column of `p0_2_misspecification.csv`, so the redundancy is visible in the bundle rather than assumed.

### P0-2B: wrong ascertainment regime

Truth retains separate probabilities `0.75` symptomatic and `0.25` asymptomatic. The fitted model imposes one common probability on both statuses, using the unchanged synthetic common-probability grid `0.25, 0.50, 0.75`. Combine it with the Phase-0b beta and offset grids for `5 × 5 × 3 = 75` cells.

For the selected wrong-model cell, define

\[
E_i=\max_c
\frac{|\overline N^{wrong}_{ic}-N^{target}_{ic}|}
{\max(1,N^{target}_{ic})}.
\]

A target detects misspecification if \(R_i\ge0.25\), \(E_i\ge0.25\), or beta or inoculation timing is outside its Phase-0b tolerance. Detection requires at least `4/5` targets.

### Accepted G29 handling

Apply the accepted G29 ruling exactly. A wrong-arm numerical tie does not itself fail software status. Record target detection as `TRUE`, `FALSE`, or `UNKNOWN`; leave undefined selected-estimate, error, and \(E_i\) fields null. \(R_i\ge0.25\) makes detection `TRUE` even with tied minima. Otherwise unresolved selected-candidate clauses remain `UNKNOWN`. Record known detections \(D\), unknowns \(U\), and attainable interval \([D,D+U]\). For threshold \(k=3\) in A or \(k=4\) in B: \(D\ge k\) gives PASS; \(D+U<k\) gives FAIL; otherwise detection status is null with `indeterminate_tied_minima`. No selected minimizer may be invented.

P0-2 passes only if both arms have `software_status=PASS` and proven `misspecification_detection=PASS`. An indeterminate arm cannot establish the binary overall exit PASS. Preserve and hash the accepted G29 ruling with this new declaration and the result bundle.

## 4. P0-3 negative control

**Run P0-3 again** on the fresh Phase-0b candidate seeds and observations. Its Phase-0 PASS remains valid historical evidence, but cannot supply a PASS for a new one-campaign gate.

Keep the distinct `3 × 3 = 9` negative-control grid: beta `0.04, 0.08, 0.16` and a global factor `0.5, 1.0, 2.0` applied uniformly to all eleven route multipliers. This deliberately separate grid preserves the exact equal-product pairs `(0.16, 0.5)`, `(0.08, 1.0)`, and `(0.04, 2.0)`. Fix inoculation offset at `2` and detection at `0.75`/`0.25`. The route factor remains `1.0` outside this control and is never reported as an identified fitted parameter.

Use the existing DATA-9 profiling instrument to report the complete objective surface, beta argmin at each factor, signed shift from the factor-1 argmin, and profiled minima. P0-3 passes only if all six Phase-0 predicates hold: the three ridge prediction vectors agree elementwise within `1e-12`; objective spread is at most \(10^{-12}\max(1,\min L)\) for each target; all per-factor argmins and shifts are present; classification is `NON_IDENTIFIED_STRUCTURAL`; `factor_estimate` is null without standard error, interval, or coverage; and the three target-independent prediction hashes are identical. Do not alter DATA-9 or production calibration artifacts.

## 5. Exact workload and fail-closed budget

Counts assume five targets, three candidate replicates, reuse of each `(candidate process seed, beta, offset)` latent run across detection probabilities and P0-2, and no reuse of P0-3 latent calls.

| Arm | Grid cells | New latent outbreak calls | Observation transforms | New network builds |
|---|---:|---:|---:|---:|
| P0-1: truth plus correct grid | 625 | `5 + (5 × 5 × 3) = 80` | `5 + (625 × 3) = 1,880` | 8 |
| P0-2A: wrong delay | 625 | 0 | `625 × 3 = 1,875` | 0 |
| P0-2B: common probability | 75 | 0 | `75 × 3 = 225` | 0 |
| P0-3: negative control | 9 | `9 × 3 = 27` | `9 × 3 = 27` | 0 |
| **Total** | **1,334** | **107** | **4,007** | **8** |

The increase from Phase 0 comes chiefly from observation transforms; latent calls remain bounded at 107. This is still a 30-day, 3,000-resident CI campaign. Wall time and storage size are unknown until measured; neither may justify an undeclared shortcut. Measured wall time per arm, total wall time and bundle byte size are recorded in `campaign_summary.json` as disclosures, not caps.

Before any simulation, dry-run planning must compute and enforce the exact per-arm counts and these caps: `625/625/75/9` cells, `5` truth latent calls, `75` shared candidate latent calls, `27` P0-3 latent calls, `107` total latent calls, `1,880/1,875/225/27` transforms, `4,007` total transforms, and eight builds. Reject non-`ci` mode, duration above 30 days, seed overlap with **either** campaign or between Phase-0b roles, incomplete arms, undeclared grids, retries, replacement seeds, adaptive work, or any predicted or measured cap breach. No 180-day wave or 30-replicate ensemble is authorized.

## 6. Outputs and protected contracts

Publish a fresh, immutable Phase-0b research bundle outside the clone in a new empty destination. Include the frozen campaign config and SHA-256; this predeclaration and SHA-256; the accepted G29 ruling and SHA-256; source/config hashes; the Phase-0b seed ledger; complete candidate loss surfaces and retained observed tables; blind-estimate records and read-back hashes; `p0_1_recovery.csv`; `p0_2_misspecification.csv`; `p0_3_profile.json`; `campaign_summary.json`; measured workload counters; and file-level `SHA256SUMS`. Include the model-owner ruling `docs/research/v1_3/2026-09-25-phase0b-owner-ruling-ACCEPTED.md` and its SHA-256. `campaign_summary.json` and the Phase-0b exit-audit report carry a `lineage` block, separated from Phase-0b observations and verdicts, containing: `phase0_verdict: FAIL`; the Phase-0 exit audit path `docs/audits/2026-09-24-phase0-exit-audit-sol-FAIL.md`; the Phase-0 bundle `SHA256SUMS` digest `72cd9a568598530923e08ce20b013d60eb7a3b26553b87c31685ad623f3faa80`; the Phase-0 predeclaration SHA-256 `ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104`; the failing predicate (P0-1 predicate 8, inoculation offset, boundary count `2/5`, selections `0, 2, 2, 2, 4`); the single design change (grid resolution halved; tolerance and bias rules unchanged); the statement that Phase 0b was designed after Phase-0 results were observed; and the statement that no Phase-0b outcome alters the Phase-0 verdict. Phase-0 P0-2A, P0-2B and P0-3 PASS results appear there as historical evidence only. Every per-target predicate value and every P0-2 detection clause value is written to the CSVs so that each logically redundant clause is independently checkable. The exit-audit verdict line reads `JOS V1.3 PHASE-0B EXIT GATE: PASS` or `FAIL`; it never restates the Phase-0 verdict as anything but FAIL.

Do not write through `CalibrationArtifactManifest` or `write_calibration_artifact`. No existing calibration, observation, outbreak, identity, persistence, artifact-schema, or hashing contract may change. A need to change one is a stop condition requiring a separate owner-rulable migration brief.

## 7. Unit order and dependencies

0. The director applies the amendments in the accepted ruling to produce this document, commits the ruling and this document on `main` via `fm.sh sync`, records both SHA-256 digests in the trail, and fixes this document's digest in the Phase-0b config and in an independent harness constant.
1. Implementation may begin only after step 0's commit exists on `main`. Any inconsistency discovered in this frozen text during implementation is a stop; it is resolved only by a filed clarification ruling in the G29 pattern that changes no grid, threshold, seed, objective or predicate. Anything else is a new gate for Steven.
2. Implement the Phase-0b declaration profile, grid, seeds, strict validation, blind P0-1 path, workload checks, and focused tests without campaign execution.
3. Adapt both P0-2 arms to the new grid sizes and tolerances; retain G29 handling.
4. Reuse the P0-3 path with Phase-0b seeds; retain its separate structural grid.
5. Independently review the complete implementation against the frozen declaration.
6. Only after review and authorization, run **one** all-arms CI-mode Phase-0b campaign.
7. A fresh independent auditor recomputes results from the immutable bundle and issues the Phase-0b exit verdict.

No arm executes early. A failure is reported as a Phase-0b FAIL; there are no replacement seeds or post-result changes.

## 8. Bounded implementation brief outline

**P0-1 brief:** Add `configs/calibration/v13_phase0b_synthetic.yaml` and focused Phase-0b tests. Adapt the reviewed `phase0_campaign.py` harness so campaign ID selects one of two **exact, separately frozen declarations**. Preserve the original Phase-0 declaration and its behavior. Replace Phase-0-only hard-coded grid, seed, hash, cell-count, and dispatch-cap checks with declaration-specific values where needed; keep shared scoring, persistence, and simulation orchestration. Confirm the blind fitter cannot receive truth metadata, all 625 cells are scored, exact-decimal recovery arithmetic works at new endpoints, and dry-run reports 80 P0-1 latent calls and 1,880 transforms. Do not add a second simulation implementation or modify protected modules.

**P0-2 brief:** Adapt grid-completeness, per-arm transform caps, measured counters, and bundle checks to `625` and `75` cells. Keep the wrong-delay compensating-offset clause at `4`, use new P0-1 tolerances for outside-tolerance clauses, and retain every G29 TRUE/FALSE/UNKNOWN rule. Verify both arms reuse the Phase-0b target observations and latent candidate cache.

**P0-3 and integration brief:** Run the unchanged nine-cell structural design on Phase-0b candidate seeds, retain DATA-9 profiling, and verify all six classification predicates. Update all-arm measured-total checks, provenance, and research-bundle naming for Phase 0b. Prove the original Phase-0 config still validates against its own frozen digest and caps. Independent review follows before execution.

Each implementation brief must require changed-file and diff-stat reporting, inspection of the changed implementation, focused regression evidence, and a stop on protected-contract conflicts. No implementation brief authorizes a campaign run.

## 9. Acceptance commands for later implementation and execution

These commands are **proposed gates**, not commands run in this consult. The proposed paths must match the owner-frozen files.

```bash
git rev-parse HEAD
git status --porcelain

UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.phase0_campaign dry-run \
  --config configs/calibration/v13_phase0b_synthetic.yaml \
  --predeclaration docs/research/v1_3/2026-09-25-phase0b-predeclaration.md

UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_phase0b_campaign.py

UV_CACHE_DIR=/tmp/uv-cache uv run python -m compileall -q src
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check \
  src/jersey_outbreak/phase0_campaign.py tests/test_phase0_campaign.py \
  tests/test_phase0b_campaign.py
UV_CACHE_DIR=/tmp/uv-cache uv run ruff format --check \
  src/jersey_outbreak/phase0_campaign.py tests/test_phase0_campaign.py \
  tests/test_phase0b_campaign.py
UV_CACHE_DIR=/tmp/uv-cache uv run mypy --ignore-missing-imports \
  src/jersey_outbreak/phase0_campaign.py

UV_CACHE_DIR=/tmp/uv-cache uv run pytest
git diff --check
git status --porcelain
```

The focused tests must cover both frozen campaign profiles, cross-campaign seed disjointness, independent digest validation, 625-cell completeness, blind persistence/read-back, new decimal endpoints, budget rejection, both P0-2 arm sizes and G29 tie states, P0-3 structural equivalence, and all-arm measured totals. Run the full suite once on final implementation bytes after formatting, lint, type checks, and focused regressions pass.

Only after implementation review passes and execution is authorized, the campaign command is:

```bash
UV_CACHE_DIR=/tmp/uv-cache STARSIM_INSTALL_FONTS=0 MPLCONFIGDIR=/tmp/mpl-cache \
uv run python -m jersey_outbreak.phase0_campaign execute \
  --config configs/calibration/v13_phase0b_synthetic.yaml \
  --predeclaration docs/research/v1_3/2026-09-25-phase0b-predeclaration.md \
  --output-dir /tmp/jos-v13-phase0b-campaign
```

The destination must be empty and unique to this run. Retain command output and the immutable bundle for independent audit.

## 10. Limitations

Five target seeds yield descriptive machinery evidence only, and three candidate seeds provide a bounded prediction library. A Phase-0b PASS would establish this declared synthetic gate, not nominal coverage, Jersey calibration, or named-pathogen validation. The two case channels are not the later cases/tests/positivity/serology objective; a materially changed later objective still needs its own deterministic fixture and synthetic-recovery check before real fitting.

The tighter grid changes the scientific question: Phase 0b demands recovery within half the old step. It may fail even if the original Phase-0 tolerance would have counted a result as recovered. The larger grid also increases the chance of near ties; the tie and profile-gap rules remain fixed. No Phase-0b outcome is predicted here.

## 11. Read-only attestation

Inspected clone HEAD: `f29784dbbbe10828b42d8e334cee4549a99919b7`. The reviewed harness was read at immutable commit `925838ac0077dbc66243cc4934aa1eb5c5b67b04` using `git show`; the Phase-0 campaign config was read from its reference bundle. The clone’s `git status --porcelain` and `git diff --stat` were empty, and `git diff --check` was clean. No files were edited; no simulations, fits, campaign tests, commits, or pushes were performed.

## Changes vs Phase 0 and why

| Item | Phase 0 | Proposed Phase 0b | Design reason |
|---|---|---|---|
| Campaign status | Recorded FAIL | New, separately frozen campaign | Preserve the prior verdict and avoid retroactive relaxation |
| Four recovery grids | Three points each | Five points each, at half spacing | Put every tolerated one-step error inside the grid |
| Recovery and bias limits | One old step; half-step bias | One new step; half-step bias | Keep their meanings while tightening both uniformly |
| Predicate 8 | At most `1/5` boundaries | Same threshold; report all counts | Preserve the edge-truncation diagnostic |
| Seeds and config IDs | Phase-0 namespaces | Four new, mutually disjoint sets and new IDs | Prevent reuse of observed realizations |
| P0-2A, P0-2B, P0-3 | PASS in Phase 0 | All rerun in the single Phase-0b campaign | One-campaign gate requires fresh, contemporaneous evidence |
| Objective, tie, profile and computed-comparison rules | Frozen Phase-0 rules | Unchanged | No result-driven numerical retuning |
| Planned workload | 198 cells; 59 latent calls; 599 transforms; 8 builds | 1,334 cells; 107 latent calls; 4,007 transforms; 8 builds | Exact cost of the declared finer grids and fresh all-arm evidence |

## Model-owner acceptance (2026-09-25)

All six decisions accepted; decisions 3 and 4 accepted with the visibility amendments in sections 1, 2 and 3 (predicate 8 and the P0-2A offset clause retained verbatim, computed independently, reported per target). Ruling text and rationale: `docs/research/v1_3/2026-09-25-phase0b-owner-ruling-ACCEPTED.md`.

## 12. Contingencies, cycle cap and vocabulary

12.1 Cycle cap. This ruling authorizes exactly one redesign cycle: Phase 0b. No Phase 0c may be designed, briefed or run under the standing delegation. If Phase 0b fails its exit audit, the director parks a gate in `GATES.md` for Steven with the default "STOP: V1.3 does not proceed to real-data fitting; the Phase-0b failure mode is filed as a deliverable under `docs/research/v1_3/`". Only Steven's explicit chat decision can open a further cycle.

12.2 Scientific FAIL. A Phase-0b campaign whose `software_status` is PASS in every arm and whose exit audit is FAIL is a recorded scientific FAIL. There are no replacement seeds, no reruns, no post-result changes, and no reinterpretation of any predicate.

12.3 VOID campaign. A campaign rejected by dry-run validation before any simulation has consumed nothing and is not a campaign. A campaign that has run simulations and is then found by the independent auditor or reviewer to have a software defect in a declared code path is VOID, not FAIL: its bundle is retained immutably and cited in lineage; the defect is named in a filed review; a corrected rerun uses the SAME Phase-0b seeds (so no realization can be shopped) and requires Steven's explicit authorization via `GATES.md` before it starts. A scientific FAIL cannot be reclassified as VOID after the fact by an agent; only an independent reviewer naming a specific code defect, followed by Steven's authorization, can do so.

12.4 Vocabulary and gating. State files, plans and reports use the exact phrase "Phase 0: FAIL (2026-09-24); Phase 0b: <PASS|FAIL|not run>". A Phase-0b exit-audit PASS satisfies the V1.3 plan's Phase-0 gate ("nothing in V1.3 fits real data until this gate passes"); the plan is annotated to say so, not rewritten. A Phase-0b PASS is never described as Phase 0 passing, as nominal coverage, as Jersey calibration, or as named-pathogen validation.

12.5 Freeze mechanics. The frozen document's SHA-256 is fixed in `configs/calibration/v13_phase0b_synthetic.yaml` and in an independent module constant; the accepted ruling and the accepted G29 ruling are hashed into the bundle alongside it. Any edit to this document after commit produces a new file with a new name and a new ruling; the committed file is never modified.
