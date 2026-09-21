# READY FOR IMPLEMENTATION

This is a specification-readiness verdict, not the independent Phase 0 exit verdict. No simulations, fits, pilot runs, or campaign-generating tests were run during this consult.

I recommend filing this report as:

`docs/research/v1_3/2026-09-21-phase0-predeclaration.md`

The specification must be committed before implementation or execution. None of its grids, thresholds, seeds, or predicates may be relaxed after results are seen.

## 1. Scope and code findings

The governing plan requires joint recovery over 3–5 effective dimensions, at least five process seeds, misspecification injection, and a negative control ([V1.3 plan](/home/steven/jos-p0-design-readonly/docs/research/v1_3/2026-09-21-v13-plan.md:7); [audit authority](/home/steven/jos-p0-design-readonly/docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md:633)).

The current implementation cannot represent that campaign directly:

- `CalibrationConfig.hidden_parameter` permits only reporting delay or beta ([calibration_schemas.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/calibration_schemas.py:13)).
- The calibration manifest stores one scalar parameter name, recovered value, and truth ([calibration_schemas.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/calibration_schemas.py:87)).
- Existing beta recovery is one-dimensional, despite its two-dimensional sensitivity surfaces ([calibration.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/calibration.py:432)).
- DATA-9 correctly recomputes beta argmins per nuisance factor, but the production path hard-codes nuisance factors `(0.5, 1.0)` and has no non-identification classifier ([calibration.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/calibration.py:40), [calibration.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/calibration.py:606)).

Therefore Phase 0 should use a standalone research campaign harness. It must not extend the existing calibration manifest, hashes, artifact IDs, or observation schemas.

## 2. P0-1 predeclared recovery campaign

### Joint fitted dimensions

All four dimensions are exercised jointly in one exhaustive `3 × 3 × 3 × 3 = 81`-cell grid.

| Dimension | Synthetic truth | Candidate grid | Recovery tolerance | Absolute mean-bias limit |
|---|---:|---|---:|---:|
| Global transmission `beta` | `0.08` | `0.04, 0.08, 0.12` | `0.04` | `0.02` |
| One-off inoculation day offset | `2` | `0, 2, 4` days | `2` days | `1` day |
| Symptomatic detection probability | `0.75` | `0.50, 0.75, 1.00` | `0.25` | `0.125` |
| Asymptomatic detection probability | `0.25` | `0.10, 0.25, 0.40` | `0.15` | `0.075` |

The beta and symptomatic-detection truths reproduce the demonstration assumptions at [respiratory_seirs_demo.yaml](/home/steven/jos-p0-design-readonly/configs/diseases/respiratory_seirs_demo.yaml:33) and [observation_demo.yaml](/home/steven/jos-p0-design-readonly/configs/observation/observation_demo.yaml:4).

The inoculation offset and asymptomatic truth `0.25` are explicitly synthetic campaign assumptions, not Jersey estimates or pathogen defaults. The higher asymptomatic probability is used only to make both observed symptom-status channels informative at CI scale. It must never replace the shipped demonstration value `0.05`.

### Fixed latent scenario

- Mode: `ci`, using the default 3,000 synthetic residents ([population_schemas.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/population_schemas.py:43)).
- Start: `2025-01-06`.
- Latent duration: `30` days.
- Initial seed count: `0`.
- One-off inoculation: exactly 10 scheduled import attempts on `start_date + inoculation_day_offset`.
- Background import rate: `0`.
- Import schedule: empty except for that one inoculation.
- Route multipliers: all `1.0`.
- Symptomatic probability: `0.6`.
- Latent duration: constant `2` days.
- Infectious duration: constant `5` days.
- Waning: disabled.
- Seasonality and interventions: absent.

These are scenario assumptions from the existing pathogen-neutral demonstration configuration, not named-pathogen evidence ([respiratory_seirs_demo.yaml](/home/steven/jos-p0-design-readonly/configs/diseases/respiratory_seirs_demo.yaml:4)). No natural-history parameter is fitted.

Using `import_schedule` for the inoculation is supported by the existing run contract ([outbreak_schemas.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/outbreak_schemas.py:128)) and scheduled-import implementation ([respiratory.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/respiratory.py:523)).

### Observation generation

For every latent infection:

- detection probabilities are the fitted symptomatic/asymptomatic values;
- detection delay is fixed at `0`;
- reporting delay is fixed at `2` days;
- weekday effects are all `1.0`;
- observation horizon tail is explicitly `4` days;
- no real Jersey data enter any calculation.

Two observed channels are derived from `ObservationRunResult.observation_events`:

1. daily reported symptomatic cases;
2. daily reported asymptomatic cases.

Dates are zero-filled over the common latent horizon plus the four-day tail. These channels use already-generated observation events; they do not expose latent counts to the fitter.

The observation RNG is independently namespaced by latent seed, observation seed, and configuration ID ([observation_scheduler.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/observation_scheduler.py:61)). Within each fitting arm, keep one configuration ID across candidates so common random numbers isolate parameter changes, matching the existing calibration convention. Persist the full config hash for each cell.

### Seed schedules

Target truth:

- Process/network seeds: `42001, 42002, 42003, 42004, 42005`.
- Observation seeds: `52001, 52002, 52003, 52004, 52005`, paired in order.
- Observation config ID: `v13-phase0-target`.

Candidate prediction library:

- Process/network seeds: `43001, 43002, 43003`.
- Observation seeds: `53001, 53002, 53003`, paired in order.
- Observation config ID: `v13-phase0-fit`.

The sets are disjoint. Network and outbreak seeds must match because the outbreak runner enforces that invariant ([outbreak_runner.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/outbreak_runner.py:195)).

There is no optimizer seed: every grid cell is evaluated. Candidate simulations may be reused across the five target fits, but target simulations may never be reused as candidate predictions.

### Blind fitting rule

The fitter receives only:

- the two observed target tables;
- the predeclared candidate grid;
- the candidate prediction library.

It must not receive truth values, latent target events, target process seeds, or target latent hashes. Truth metadata is joined only after the selected estimates and their hash have been written.

The fact that the truth lies on the predeclared regular grid is not candidate selection. No grid pruning, refinement, early stopping, or truth-distance tie breaking is permitted.

### Objective

For target process seed \(i\), candidate \(\theta\), channel \(c\), date \(t\), and fitting replicate \(j\), let \(y_{ict}\) be the target count and \(x_{j\theta ct}\) the candidate count.

Define:

\[
m_{\theta ct}=\frac{1}{3}\sum_{j=1}^{3}\sqrt{x_{j\theta ct}+3/8}
\]

\[
L_i(\theta)=\frac{1}{2T}\sum_{c=1}^{2}\sum_{t=1}^{T}
\left(\sqrt{y_{ict}+3/8}-m_{\theta ct}\right)^2
\]

This is a predeclared minimum-distance loss, not a likelihood. It gives the two channels equal weight and prevents a single large stochastic realization from dominating.

All 81 cells must be scored before selection.

### Identifiability

For dimension \(d\), profile over all other dimensions:

\[
P_{i,d}(v)=\min_{\theta:\theta_d=v}L_i(\theta)
\]

Numerical ties use:

\[
\tau_i=10^{-12}\max(1,L_{i,\min})
\]

A dimension is practically identified for target \(i\) only when:

- its profiled minimum is unique within \(\tau_i\); and
- the relative gap to the second-best profile value is at least `0.05`:

\[
\frac{P_{\text{second}}-P_{\min}}{\max(P_{\min},10^{-12})}\ge0.05
\]

The 5% value is a bounded machinery threshold against near-flat grid profiles. It is not a precision or inferential statement.

An exact tied global minimum makes P0-1 fail. No lexicographic estimate may conceal it.

### Descriptive recovery and bias

For dimension \(d\):

- signed error: \(\hat\theta_{i,d}-\theta_d^\*\);
- absolute error: its absolute value;
- descriptive tolerance coverage:

\[
C_d=\frac{1}{5}\sum_i
1\{\text{identified and absolute error}\le\text{tolerance}_d\}
\]

- bias: arithmetic mean signed error across the five target process seeds;
- joint coverage: fraction of target seeds for which all four dimensions are identified and within tolerance.

These are five-seed descriptive hit rates. They do not estimate nominal statistical coverage and must not be presented with confidence-interval language.

### P0-1 aggregate PASS predicate

P0-1 is `PASS` only if all conditions hold:

1. All five target runs and all predeclared candidate cells complete. No replacement seeds.
2. Every truth run realizes all 10 inoculation acquisitions, at least one local secondary infection, at least one report in each symptom channel, and at least three non-zero combined report dates.
3. Observation chronology and latent-incidence conservation diagnostics pass.
4. No global loss minimum has a numerical tie.
5. Each dimension has descriptive tolerance coverage at least `4/5`.
6. Joint four-dimensional coverage is at least `3/5`.
7. Each absolute mean bias is no larger than the tabled half-step limit.
8. No dimension is selected at its grid boundary for more than `1/5` target seeds.
9. Every target and candidate uses the declared seed namespace, grid, objective, dates, and fixed parameters.
10. The workload counters remain within the declared caps below.

A candidate extinction is a valid, usually poor candidate score. A truth extinction or uninformative truth run is a gate failure; it is not resampled.

The one-grid-step tolerances allow one discrete stochastic displacement. The half-step bias limits prevent systematic one-direction error from passing merely through marginal hit rates.

## 3. P0-2 misspecification injections

Both arms reuse the P0-1 target observations, latent candidate runs, seed schedules, grid order, and scoring rule.

Software completion and scientific behavior are reported separately:

- `software_status`: whether the arm executed according to contract;
- `misspecification_detection`: whether the predeclared degradation predicate passed.

A scientifically poor fit under misspecification is expected and does not constitute software failure.

For target \(i\), define relative loss degradation against the correctly specified arm:

\[
R_i=\frac{L^{wrong}_{i,\min}-L^{correct}_{i,\min}}
{\max(L^{correct}_{i,\min},10^{-9})}
\]

### P0-2A: wrong reporting delay

- Truth delay: fixed `2` days.
- Fitted delay: forced to fixed `0` days.
- All four P0-1 fitted dimensions and grids remain unchanged.
- Detection probabilities, process seeds, observation seeds, and common-random-number namespace remain unchanged.

A target seed detects the wrong delay if at least one holds:

- recovered inoculation day is `4`, the declared two-day compensating shift;
- at least one fitted dimension is outside its P0-1 recovery tolerance;
- `R_i ≥ 0.25`.

P0-2A detection is `PASS` when at least `3/5` targets detect it.

### P0-2B: wrong ascertainment regime

Truth retains separate probabilities:

- symptomatic: `0.75`;
- asymptomatic: `0.25`.

The fitted model incorrectly imposes one common probability for both symptom statuses:

- common probability grid: `0.25, 0.50, 0.75`;
- beta and inoculation grids remain unchanged;
- grid size: `3 × 3 × 3 = 27`.

For the selected wrong-model candidate, define channel-total error:

\[
E_i=\max_c
\frac{|\overline{N}^{wrong}_{ic}-N^{target}_{ic}|}
{\max(1,N^{target}_{ic})}
\]

A target detects the wrong regime if at least one holds:

- `R_i ≥ 0.25`;
- `E_i ≥ 0.25`;
- beta or inoculation timing is outside its P0-1 tolerance.

P0-2B detection is `PASS` when at least `4/5` targets detect it.

P0-2 is `PASS` only when both arms have `software_status=PASS` and `misspecification_detection=PASS`. If a wrong model recovers apparently well and evades these predicates, Phase 0 fails scientifically; thresholds must not be relaxed.

## 4. P0-3 negative control

### Non-identified parameter

The negative control is a global multiplier applied uniformly to all 11 route multipliers while beta remains free.

This factor is forbidden as an actual fitted Phase 0 parameter. It is perturbed only for the negative control and otherwise remains fixed at `1.0`.

Fix inoculation timing and ascertainment at the P0-1 truths. Evaluate:

- beta: `0.04, 0.08, 0.16`;
- global route factor: `0.5, 1.0, 2.0`;
- full `3 × 3 = 9` surface.

The three pairs:

- `(beta=0.16, factor=0.5)`;
- `(beta=0.08, factor=1.0)`;
- `(beta=0.04, factor=2.0)`;

all produce route beta `0.08`. Because the runner computes route transmission as `beta × route_multiplier` ([outbreak_runner.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/outbreak_runner.py:240)), this is a deliberately structural non-identifiability.

### DATA-9 use and thresholds

Use the existing DATA-9 surface logic to report:

- complete objective surface;
- beta argmin for every factor;
- signed beta shift from the factor-1 reference;
- profiled minima.

Additionally, the campaign wrapper must classify structural equivalence. P0-3 is `PASS` only if:

1. The predicted two-channel vectors for all three equal-product pairs agree within `1e-12` elementwise.
2. Their objective spread is no greater than `10^-12 × max(1, minimum objective)`.
3. The report contains every per-factor beta argmin and signed shift.
4. The factor is reported as `NON_IDENTIFIED_STRUCTURAL`.
5. `factor_estimate` is `null`; no standard error, interval, or coverage value is emitted.
6. Changing only decomposition between beta and factor leaves the target-independent prediction hash identical for the three ridge cells.

The existing DATA-9 computational instrument is sufficient for profiling and per-factor argmins. Its current hard-coded factor set, one-dimensional campaign path, and scalar artifact schema are not sufficient for this control. The standalone wrapper supplies the factor grid and classification without changing DATA-9 or its artifacts.

## 5. Workload and fail-closed budget

Exact planned maximum:

| Work | Maximum |
|---|---:|
| P0-1 grid cells | 81 |
| P0-2 wrong-delay cells | 81 |
| P0-2 wrong-regime cells | 27 |
| P0-3 cells | 9 |
| Total cells across arms | 198 |
| Truth latent outbreak calls | 5 |
| P0-1/P0-2 candidate latent calls | 27 |
| P0-3 latent calls | 27 |
| Total latent outbreak calls | 59 |
| Observation transforms | 599 |
| Distinct population/network seed builds | 8 |
| Duration per outbreak | 30 days |
| Mode | `ci` only |

Before the first simulation, dry-run planning must calculate these counts. Execution fails closed if:

- mode is not `ci`;
- duration exceeds 30 days;
- any grid exceeds its declared cells;
- predicted outbreak calls exceed 59;
- predicted observation transforms exceed 599;
- seeds overlap;
- any undeclared retry, adaptive grid, or replacement seed is requested.

This is not a 30-replicate ensemble and produces no empirical 2.5/97.5 bands. No 180-day run is authorized.

## 6. Outputs and protected contracts

Write the research bundle outside the clone, containing:

- frozen campaign config and SHA-256;
- predeclaration document SHA-256;
- input source/config hashes;
- seed ledger;
- all candidate loss surfaces;
- `p0_1_recovery.csv`;
- `p0_2_misspecification.csv`;
- `p0_3_profile.json`;
- `campaign_summary.json`;
- file-level `SHA256SUMS`.

Do not route this through `CalibrationArtifactManifest` or `write_calibration_artifact`; those contracts are scalar and would misrepresent the joint campaign ([calibration_artifacts.py](/home/steven/jos-p0-design-readonly/src/jersey_outbreak/calibration_artifacts.py:154)).

Any proposal to alter existing calibration/observation schemas, artifact hashes, artifact IDs, or verification rules requires a separate explicitly declared migration brief. It is not authorized here.

## 7. Unit order and dependencies

1. Director files and commits this predeclaration.
2. Implement P0-1 harness, pure scoring, blind fit boundary, dry-run budget check, and unit tests.
3. Implement both P0-2 arms without running them.
4. Implement P0-3 surface and non-identification classifier without running it.
5. Independent code review verifies the implementation against the committed specification.
6. Run one all-arms CI-mode campaign.
7. Independent fresh Sol inspects the immutable result bundle and authors the exit verdict.

No campaign arm may be run before all three arms and predicates are implemented. This prevents P0-2/P0-3 choices from reacting to P0-1 results.

## 8. Implementation briefs

### P0-1 — nine-field Luna brief

**GOAL:** Implement the predeclared four-dimensional CI-mode synthetic-recovery harness, blind scoring boundary, descriptive recovery table, profile-identifiability diagnostics, budget enforcement, and standalone research output.

**SCOPE:** Add only `src/jersey_outbreak/phase0_campaign.py`, `configs/calibration/v13_phase0_synthetic.yaml`, and `tests/test_phase0_campaign.py`. The director-filed predeclaration is read-only. Do not edit existing calibration, observation, outbreak, artifact, hashing, or CLI modules.

**CONTEXT:** Baseline code is `3ff37348f88750470be9f1ccda193b3ff31fb9c3`; consult clone is detached at `94f7f9116f27be0b7604906c774a1e03663c768e`. Current calibration is scalar. Implement the exact P0-1 contract above as a standalone research harness. Fitter-facing functions must not accept truth metadata.

**ACCEPTANCE:** Exact dimensions, grids, seeds, fixed parameters, observation channels, objective, tie rule, 5% profile-gap rule, recovery tolerances, bias thresholds, boundary accounting, truth viability, and aggregate predicate are encoded without substitutions. Dry-run reports 81 cells, 5 target seeds, 3 fitting seeds, 32 latent calls through P0-1, and 248 observation transforms. Unit tests prove seed disjointness, no truth field crosses the fitter interface, complete-grid scoring, tie failure, budget failure, coverage/bias arithmetic, and fixed target/candidate date grids.

**VERIFY:** Run the P0-1 commands in section 9, inspect the implementation, report actual output, changed files, and diff stat.

**TIMEBOX:** 75 minutes. If the existing APIs cannot support the contract without editing a protected module, stop and report the exact conflict.

**FORBIDDEN:** Campaign execution; real data; pilot fitting; adaptive grids; new dependencies; schema/hash migrations; changes to natural history, route semantics, existing artifacts, or existing calibration behavior; tracked result files; commits or pushes.

**REPORT:** Verdict first; per-criterion evidence; dry-run budget table; exact commands and output; files changed; diff stat; unresolved conflicts. Do not claim the scientific gate passed.

**STANDING:** Apply the repository `AGENTS.md` and the exact `DIRECTOR.md` standing block supplied with this task. Smallest root-cause change, no destructive git, no protected-contract change, no invented scientific defaults, and no status-vocabulary drift.

### P0-2 bounded brief

**GOAL:** Add the fixed-zero-delay and common-probability ascertainment misspecification arms and their predeclared detection predicates.

**SCOPE:** Modify only the three P0-1 files. Reuse target observations and latent candidate cache. No core observation changes.

**CONTEXT:** Depends on accepted P0-1 implementation. The arms test scientific sensitivity; poor recovery is expected and is distinct from software failure.

**ACCEPTANCE:** Exact 81- and 27-cell arms; isolated interventions; `R_i` and `E_i` definitions; `3/5` and `4/5` detection thresholds; separate software/detection statuses; no threshold derived from results.

**VERIFY:** Run the P0-2 commands in section 9 and confirm dry-run cumulative totals remain within 198 cells, 59 latent calls, and 599 transforms.

**TIMEBOX:** 45 minutes.

**FORBIDDEN:** Running the campaign, changing P0-1 predicates, adding a temporal-regime observation API, or editing existing schemas/artifacts.

**REPORT:** Per-arm implementation evidence, invariant tests, budget totals, changed files, diff stat, and blockers.

**STANDING:** Same standing orders as P0-1.

### P0-3 bounded brief

**GOAL:** Implement the nine-cell beta × global-route-factor negative control using the DATA-9 per-factor profiler and emit an explicit structural non-identification result.

**SCOPE:** Modify only the P0-1 files. Import/reuse the existing profiling helper; do not change existing DATA-9 constants or production calibration output.

**CONTEXT:** The route factor is a negative-control nuisance only. It remains fixed everywhere outside P0-3.

**ACCEPTANCE:** Exact beta/factor grids; complete surface; three equal-product ridge cells; `1e-12` vector and objective thresholds; per-factor argmins and shifts; `NON_IDENTIFIED_STRUCTURAL`; null factor estimate; failure if false precision is emitted.

**VERIFY:** Run the P0-3 commands in section 9 and inspect the exact equivalence assertions.

**TIMEBOX:** 30 minutes.

**FORBIDDEN:** Campaign execution, fitting route multipliers in P0-1/P0-2, changing DATA-9 semantics, or migrating calibration artifacts.

**REPORT:** Surface/classifier unit evidence, proof that no factor point estimate can be serialized, files changed, diff stat, and blockers.

**STANDING:** Same standing orders as P0-1.

## 9. Exact acceptance commands

Implementation checks:

```bash
git rev-parse HEAD
git status --porcelain

UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.phase0_campaign dry-run \
  --config configs/calibration/v13_phase0_synthetic.yaml \
  --predeclaration docs/research/v1_3/2026-09-21-phase0-predeclaration.md

UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_phase0_campaign.py \
  -k 'p0_1 or blind or budget'

UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_phase0_campaign.py -k p0_2
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_phase0_campaign.py -k p0_3

UV_CACHE_DIR=/tmp/uv-cache uv run python -m compileall -q src
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check \
  src/jersey_outbreak/phase0_campaign.py tests/test_phase0_campaign.py
UV_CACHE_DIR=/tmp/uv-cache uv run ruff format --check \
  src/jersey_outbreak/phase0_campaign.py tests/test_phase0_campaign.py
UV_CACHE_DIR=/tmp/uv-cache uv run mypy --ignore-missing-imports \
  src/jersey_outbreak/phase0_campaign.py

UV_CACHE_DIR=/tmp/uv-cache uv run pytest
git diff --check
git status --porcelain
```

Only after the implementation review passes, the authorized campaign command is:

```bash
UV_CACHE_DIR=/tmp/uv-cache STARSIM_INSTALL_FONTS=0 MPLCONFIGDIR=/tmp/mpl-cache \
uv run python -m jersey_outbreak.phase0_campaign execute \
  --config configs/calibration/v13_phase0_synthetic.yaml \
  --predeclaration docs/research/v1_3/2026-09-21-phase0-predeclaration.md \
  --output-dir /tmp/jos-v13-phase0-campaign
```

## 10. Limitations and unresolved risks

- Five target seeds support only a descriptive machinery check. They cannot establish nominal statistical coverage.
- Three fitting seeds give a bounded candidate prediction library, not a stable characterization of process uncertainty.
- The two symptom-status case channels are supported by the current observation event model, but they are not the later V1.3 cases/tests/positivity/serology objective. If Phase 2 materially changes the objective or adds streams, its objective requires a new deterministic fixture and synthetic-recovery check before real fitting.
- The disease configuration is pathogen-neutral and synthetic. Passing cannot be described as Jersey calibration or named-pathogen validation.
- The `0.25` asymptomatic ascertainment truth is challenge-only and must not become a default.
- P0-3 establishes deliberate structural confounding in the implemented route-beta product. It does not establish real-data identifiability for beta or any route effect.

No scope-owner ruling is required for the default standalone-harness route. A ruling would be required only if the director wants Phase 0 results incorporated into the existing versioned calibration artifact contract.

## 11. Repository attestation

- Inspected HEAD: `94f7f9116f27be0b7604906c774a1e03663c768e`
- Declared code baseline is an ancestor: `3ff37348f88750470be9f1ccda193b3ff31fb9c3`
- Initial `git status --porcelain`: empty
- Final `git status --porcelain`: empty
- Final `git diff --stat`: empty
- Final `git diff --check`: clean
- Tracked files edited: none
- Simulations/fits/campaign tests executed: none