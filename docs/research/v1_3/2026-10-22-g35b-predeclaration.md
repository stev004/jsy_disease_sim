# G35-B synthetic design-study predeclaration (FROZEN 2026-10-22)

## 1. Status and lineage

**Status:** FROZEN 2026-10-22 after the model-owner ruling (ACCEPT WITH AMENDMENTS, A1–A11 applied verbatim below) and the pre-freeze build pre-check and horizon probe (§8 and §4.2 frozen values). This document is not a Phase 0c and not a V1.3 gate. Phase 0: FAIL (2026-09-24). Phase 0b: FAIL (2026-09-26). G35-B: not run. Real-data fitting stays STOPPED (G34 A+B). This study was designed **after** both Phase-0 and Phase-0b results were seen, and after the exploratory ridge diagnostic. No outcome of this study changes either FAIL verdict.

**Authority:** G35 was resolved B on 2026-10-22 (`.claude/GATES.md`, Resolved). That resolution authorized a synthetic design study with no real data. The Phase-0b §12.1 cycle cap is spent. This study opens no recovery cycle, and no outcome of it can satisfy the V1.3 plan's Phase-0 gate.

**What any outcome authorizes:** nothing beyond input to a separate, later owner decision by Steven. In particular:
- **No outcome licenses:** real Jersey fitting; a claim that Phase 0 or Phase 0b passed; nominal coverage; Jersey calibration; or named-pathogen validation.
- **A PASS in any arm** is a screening result. A decision may rely on it only after a separately owner-ruled, fresh-seed confirmatory campaign (§7.4). Any such confirmatory campaign is itself synthetic. Neither this study nor a confirmatory campaign can reopen G34, satisfy the V1.3 plan's Phase-0 gate, or license real-data fitting; reopening real-data fitting would require Steven's explicit chat decision on a new gate and a new owner-ruled predeclaration of its own.

**Lineage block** (copied into `campaign_summary.json` and the exit audit, kept apart from G35-B results):

| Item | Value |
|---|---|
| Phase-0 verdict / audit | `phase0_verdict: FAIL` · `docs/audits/2026-09-24-phase0-exit-audit-sol-FAIL.md` |
| Phase-0 bundle `SHA256SUMS` digest | `72cd9a568598530923e08ce20b013d60eb7a3b26553b87c31685ad623f3faa80` |
| Phase-0 predeclaration SHA-256 | `ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104` |
| Phase-0b verdict / audit | `phase0b_verdict: FAIL` · `docs/audits/2026-09-26-phase0b-exit-audit-sol-FAIL.md` |
| Phase-0b bundle `SHA256SUMS` digest | `a319c5557ffa77c56baebb8341b5fc2e1432f367bdb9d0b34169aa079659032a` |
| Phase-0b predeclaration SHA-256 | `ec8df64630dd50c83b0866a096fba4980453c34232d18114129587274f257451` (re-hashed by this consult) |
| Phase-0b failing predicates | P0-1 predicates 5, 6, 8. Inoculation offset selections `4, 4, 0, 2, 0` against truth 2; boundary count 4/5; joint 1/5 |
| Ridge diagnostic SHA-256 | `de13913b85afa3578f3fcea2e460448909132133a30735eb3cae2609780079d6` (`docs/research/v1_3/2026-09-29-phase0b-ridge-diagnostic-EXPLORATORY.md`) |
| G34-B memo | `docs/research/v1_3/2026-09-29-successor-offset-design-memo-DRAFT.md`. Its Option 2 is withdrawn |

## 2. Scope and design basis

**Question.** Does any one of three design factors make the inoculation-day offset recoverable in synthetic data under the unchanged Phase-0b P0-1 recovery predicates, where Phase 0 and Phase 0b could not? Beta and both detection probabilities must recover jointly. The three factors are:
- (i) more candidate replicates per cell;
- (ii) a longer latent window that crosses the epidemic peak;
- (iii) an independently modelled serosurvey anchor on cumulative infection.

**Why these factors.** The diagnostic weighed three hypotheses (§Q4):
- **H3, Monte-Carlo noise at three replicates: substantial support.** Factor (i) targets it.
- **H2, a joint beta–offset–detection ridge: moderate support.** Factors (ii) and (iii) target it: (ii) adds growth/peak/decline shape, and (iii) separates infection scale from detection.
- **H1, little timing information: weak support for a blanket claim.**

The three factors come from the diagnostic's Q5 and the G35 ruling. None was chosen from a recovery number.

**Design rules:**
- One fixed fresh-seed baseline arm (B).
- Each factor arm changes exactly one quantity relative to B and shares B's targets and candidate streams wherever the factor allows.
- No combined-factor arm.
- P0-2 and P0-3 are not rerun. Both passed in both campaigns, they are not the question, and this study is not a gate that needs all-arms evidence. G29 governs P0-2 only and is not invoked.
- Research harness only. Nothing is written through `CalibrationArtifactManifest` or `write_calibration_artifact`.

**Synthetic only.** No real Jersey data enter. The frozen Jersey 2020 serosurvey table (`covid_serosurvey_2020`, `src/jersey_outbreak/canonical_schemas.py:307`, `data_pipeline.py:1403–1449`) must not be read, imported or used to set any value.

## 3. Baseline arm (B)

B re-instantiates the frozen Phase-0b P0-1 design (Phase-0b predeclaration §2) verbatim, with fresh seeds and one argued change: ten targets instead of five (§7.3, owner decision 3). The Phase-0b seeds are retired.

- **Dimensions, truths, grids, tolerances, bias limits:** exactly the Phase-0b table, as decimal strings with exact decimal arithmetic.

  | Dimension | Truth | Grid | Tolerance | Bias limit |
  |---|---:|---|---:|---:|
  | beta | `0.08` | `0.04, 0.06, 0.08, 0.10, 0.12` | `0.02` | `0.01` |
  | offset (days) | `2` | `0, 1, 2, 3, 4` | `1` | `0.5` |
  | symptomatic detection | `0.75` | `0.50, 0.625, 0.75, 0.875, 1.00` | `0.125` | `0.0625` |
  | asymptomatic detection | `0.25` | `0.10, 0.175, 0.25, 0.325, 0.40` | `0.075` | `0.0375` |

- **Grid:** 625 cells, all scored before selection.
- **Fixed latent scenario (verbatim):**
  - `ci` mode, 3,000 residents, start `2025-01-06`, exactly 30 latent days.
  - Initial seeds 0. Ten import attempts at `start_date + offset`; background import rate 0; no other imports.
  - All eleven route multipliers `1.0`. Symptomatic probability `0.6`.
  - Constant latent duration 2 days and infectious duration 5 days. Waning disabled. No seasonality or interventions.
- **Observation (verbatim):** detection delay 0, reporting delay 2, weekday factors `1.0`, four-day tail, 34 zero-filled dates. Reports come solely from `observation_events`.
- **Objective, tie and identification rules:** verbatim, with three candidate replicates (§6).
- **Pairing:** network and outbreak seeds match within each process run. One candidate observation config ID is used across cells, giving common random numbers. Candidate latent runs are reused across detection probabilities. Target runs never serve as candidates.
- **Forbidden:** optimizer seed, post-freeze replacement, retry, adaptive grid, pruning, early stopping.

## 4. Factor arms

### 4.1 Arm (i): more candidate replicates

**Single change:** candidate replicates per cell go from 3 to **R = 12**. Targets are B's ten target tables, byte-shared.

**Nested, batched design.** The twelve candidate process/observation pairs form four independent batches of three:
- A = B's own candidates;
- B′, C′ and D′ are fresh.

Every batch is evaluated at all 625 cells, so all four batches sit at identical fixed tuples. The gate objective uses all 12. Nesting is A ⊂ A∪B′ (6) ⊂ A∪B′∪C′∪D′ (12).

**Why R = 12 (argued, not taken from Phase-0b numbers):**
- **Precision.** The candidate mean m = (1/R)Σⱼ√(xⱼ+3/8) has Monte-Carlo standard deviation ∝ 1/√R. Going from 3 to 12 halves the replicate-noise component of every per-date candidate mean, and so of every between-cell loss difference.
- **Cost.** A four-fold reduction needs R = 48: 1,200 candidate latent calls, about 16× B. That is not modest.
- **Why four batches of three.** Each batch has B's replicate count, so each is an independent draw of a Phase-0b-shaped objective at every fixed tuple, and of its re-profiled offset. Four batches is the smallest number that halves the candidate-mean Monte-Carlo SD (R = 4 × 3); the next halving needs sixteen. The batch spread is stochastic replicate variation, never an interval.
- **What R = 12 does not do.** It cannot remove a structural trade-off (diagnostic Q5). A FAIL at R = 12 is evidence against H3 as the sole cause. It is not proof of H2.

### 4.2 Arm (ii): longer latent window crossing the peak

**Single change:** the latent run lasts **H** days instead of 30. The observation tail stays 4 days, so the fitter sees T = H + 4 dates.
- Unchanged: population builds, truth, grids, reporting model, the target and candidate process/observation seed streams (B's own), the objective form and R = 3.
- Target trajectories cannot be byte-shared, because the latent runs are longer.

**Choosing H: declared pre-freeze probe.** The model's dynamics bound the outcome only qualitatively. It is a closed 3,000-resident SEIR population with no waning and no imports after the pulse, so the epidemic must end. Its generation interval is fixed by the 2-day latent and 5-day infectious durations. The network's reproduction number is not available analytically. H is therefore fixed by a probe that runs before freezing and is outside every study set:

0. **Freeze before probe.** The probe rule (steps 1–6) is fixed by the committed owner ruling before any probe simulation runs; the probe record cites that commit and the ruling's SHA-256. The probe computes and records only p_s, e_s, H, the prefix-identity result and per-call `runtime_seconds`. It computes no loss, no profile and no candidate cell. Probe seeds `81001–81006` and `91001–91003` are retired after the probe and may never serve as target or candidate seeds in this or any later campaign.
1. **Probe seeds:** process seeds `81001–81003` (reserves `81004–81006`), observation seeds `91001–91003`, config ID `v13-g35b-probe`. Each probe runs the truth cell (beta 0.08, offset 2, B's scenario) at 30 days and at 91 days.
2. **Peak and decline marks.** On each 91-day run, compute the 7-day trailing sum of latent `new_infections` from `daily_epidemic`. Let p_s be the earliest day index of its maximum. Let e_s be the first day index ≥ p_s at which it is ≤ 10% of that maximum.
3. **Rule:** H = the smallest multiple of 7 that is ≥ max_s(e_s) + 8, and ≥ 35. The 10% mark is a **synthetic campaign assumption** defining "crossed the peak and captured the decline" (diagnostic Q5). The 8-day margin is derived from the frozen observation model, not chosen: infections on day e_s are reported at most 2 (latent) + 0 (detection delay) + 2 (reporting delay) = 4 days later, plus the 4-day observation tail, so the decline through e_s is present in the report series the fitter sees. Rounding to a multiple of 7 is a convention only (weekday factors are 1.0). None of these is an epidemiological claim.
4. **Stop rule.** If any probe has no e_s within 91 days, or ends with fewer than 10 local infections, the draft returns as NEEDS OWNER INPUT. H is never chosen ad hoc.
5. **Prefix-identity check, same probe.** For each probe seed, test whether `transmission_events` with `infection_date ≤ start+29`, and report counts on dates ≤ start+29 under one fixed observation config, are identical between the 30-day and 91-day runs.
   - The code makes this plausible: observation draws are keyed per event (`observation_scheduler.py:61–90`).
   - It is unverified for the Starsim latent RNG.
   - The result is written into the frozen text. If identity holds, arm (ii) shares B's realizations on days 0–29 and differs only by extension. If it fails, the comparison is labelled "seed-stream matched, realization not matched" and proceeds unchanged.
6. **Bounds.** `OutbreakRunConfig.duration_days` allows ≤ 366 (`outbreak_schemas.py:136`). The probe's 91-day cap is a cost bound: about 3× B per latent call. It is a synthetic campaign assumption.

**Frozen values (filled mechanically from the probe record, 2026-10-22):**
- **H = 49** days (max e_s = 41; 41 + 8 = 49; ≥ 35; multiple of 7; ≤ 91). Arm (ii) therefore scores T = 53 dates. The stop rule did not fire.
- **Prefix identity: IDENTICAL** for all three probe seeds. Prefix transmission-event hashes and prefix report-count hashes for dates ≤ 2025-02-04 were byte-identical between the 30-day and 91-day runs. Arm (ii) shares B's realizations on days 0–29 and differs only by extension.
- Per seed: `81001`/`91001`: p_s 26, e_s 41, local infections 2281, runtime_seconds 30 d 2.088 / 91 d 2.505; `81002`/`91002`: p_s 22, e_s 38, local infections 2272, runtime_seconds 30 d 0.980 / 91 d 2.638; `81003`/`91003`: p_s 23, e_s 41, local infections 2248, runtime_seconds 30 d 0.973 / 91 d 2.718.
- Record: `docs/runs/2026-10-22-g35b-horizon-probe.json` (sha256 `03ac0906e68e424277538c9e938bb68e88db96406269cab692c39d384846a3d7`), script `docs/runs/2026-10-22-g35b-horizon-probe.py.txt`, log `docs/runs/2026-10-22-g35b-horizon-probe.log`. The probe ran on ruling commit `2cfb9f6d249c64fe78e0716a6a6ff6208ac681b5` (ruling sha256 `f84738a9594312f3371f4bb469c5cfaafed265dc5d233ee34f1f0be564d99643`). Probe seeds `81001–81006` and `91001–91003` are now retired.

**Manipulation check (reported, not gating).** For each target, report whether its latent 7-day peak day is ≤ H − 8. If fewer than 10/10 targets crossed, the arm-(ii) reading carries "factor delivered for k/10 targets". The gate verdict does not change.

**Wall time.** Unmeasured, so it is measured and disclosed, never capped:
- The probe records `diagnostics["benchmark"]["runtime_seconds"]` per latent call at 30 and 91 days (`outbreak_runner.py:624–630`). It is filed with the probe record.
- The campaign records per-arm and per-phase (build, latent, transform, scoring) `time.perf_counter()` totals, plus every latent call's `runtime_seconds`, in `campaign_summary.json.disclosures`.

### 4.3 Arm (iii): serosurvey anchor on cumulative infection

**Single change:** the objective gains one serosurvey datum (§5.2, §6).
- Targets, candidate latent runs and report tables are B's, byte-shared. No new latent calls or report transforms.
- R = 3 (batch A). The window is 30 days.

## 5. Observation models

### 5.1 Report channels (B, i, ii, iii)

Verbatim Phase-0b: two channels (symptomatic, asymptomatic) from `observation_events` `report_date` and `symptomatic` (`phase0_campaign.py:1691–1721`), zero-filled over the declared calendar.

### 5.2 Synthetic serosurvey (arm iii only)

**What the model exposes today, read from the code:**
- **Per-agent infection history.** `OutbreakRunResult.transmission_events` (`outbreak_runner.py:323–337, 713`) carries `infected_agent_id`, `infection_date` and `natural_history_episode_index` for every seeded, imported or local episode (`respiratory.py:285–335, 602–661`).
- **Population-level ever-infected series.** `daily_epidemic[*]["ever_infected_fraction"]` is computed from **unique resident identities** (`outbreak_runner.py:341–367`). The `output_semantics` text (`:586–591`) says so.
- **Episode counts that must not be used.** `cumulative_infections` (non-seeded `cum_infections`), `cumulative_incidence_per_capita` and `attack_rate` count episodes, not ever-infected identities.
- **Per-agent Starsim state is not exported.** The `susceptible/exposed/infected/recovered` and `ti_exposed` arrays (`respiratory.py:194–203`) live inside the sim, and `ti_exposed` is overwritten on each episode (`:622`). It is not an ever-infected marker under waning.

**What is missing:**
- No per-agent ever-infected field is exported. It is derivable without touching protected code.
- No serology observation model, serosurvey sampling frame or serosurvey RNG namespace exists. `ObservationConfig` has only detection probabilities, delays, the weekday effect, the horizon tail and `observation_seed` (`observation_schemas.py:102–119`).
- No seroconversion delay, assay sensitivity or assay specificity parameter exists anywhere.

None of these may be added to protected modules. The serosurvey is built in the study harness only.

**Estimand:** for resident a and survey date d, everInfected(a, d) = 1 if any `transmission_events` row has `infected_agent_id == a` and `infection_date ≤ d`. This is unique identities, never episode counts. The sampling frame is `latent_result.generated.agent_ids`, the same denominator as `ever_infected_fraction`.

**Sampling.** One simple random sample without replacement of n residents:
- Order residents by the SHA-256 of the UTF-8 bytes of the string `f"{process_seed}|{serosurvey_seed}|{serosurvey_config_id}|serosurvey|{agent_id}"` (seeds as decimal integers, no whitespace), ascending by hex digest, and take the first n. Agent IDs are unique, so the ordering is total.
- The sample depends only on the seed, the config and the population, never on the latent run. Candidate samples are therefore common random numbers across all cells of one process seed.
- k = the number of sampled residents with everInfected = 1.

**Synthetic campaign assumptions, labelled and argued:**

| Assumption | Value | Argument |
|---|---|---|
| Survey timing | one survey at d = start + 29 (2025-02-04), the last latent day | Arm (iii) changes one factor, so the window stays 30 days. The last latent day carries the most cumulative signal and is the latest date at which status is fully simulated. A survey later than the window would be a second factor. |
| Seroconversion lag | 0 days (ever-infected by d) | Any non-zero lag would be an invented biological parameter. Zero is an idealization of the estimand, not a claim about any pathogen. |
| Sensitivity / specificity | 1 / 1 (idealized assay) | Any other values would be invented. Under known, nondifferential misclassification, an imperfect assay carries no more information than a perfect one at the same n. A FAIL is evidence against this anchor at this n, this date, one survey and this weight; it says nothing about larger n, multiple survey dates or other weights. A PASS is an upper bound: assay-quality sensitivity work is required before any reliance (§15). |
| Sample size | n = 400 of N = 3,000 | Criterion tied to the declared grid, not to observed numbers: whenever ≥ 25% of residents are ever-infected by d, two sampling SDs of k/n (finite-population corrected) must be smaller, relative to the proportion, than one symptomatic-detection grid step at truth (0.125/0.75 = 1/6). At F = 0.25: SD = √(0.1875/400 · 2600/2999) = 0.0202, and 2SD/F = 0.161 < 0.167. n = 300 fails (0.190). 400 is the smallest multiple of 100 that meets the criterion. The 25% floor is itself an assumption. |

These describe a synthetic population only. No Jersey serosurvey design value is imported.

**Seeds:**
- Targets: serosurvey seeds `94001–94010`, paired in order, config ID `v13-g35b-sero-target`.
- Candidates (batch A): seeds `95001–95003`, paired in order, config ID `v13-g35b-sero-fit`. One candidate sample is drawn per (candidate process seed, beta, offset) latent run: 75 samples.

## 6. Objective

**Common to all arms.** For target i, cell θ, channel c, date t and R candidate replicates j:

\[
m_{\theta ct}=\frac1R\sum_{j=1}^{R}\sqrt{x_{j\theta ct}+3/8},\qquad
L^{rep}_i(\theta)=\frac{1}{2T}\sum_{c=1}^{2}\sum_{t=1}^{T}\Big(\sqrt{y_{ict}+3/8}-m_{\theta ct}\Big)^2 .
\]

| Arm | R | T |
|---|---:|---:|
| B | 3 | 34 |
| (i) | 12 | 34 |
| (ii) | 3 | H + 4 |
| (iii) | 3 | 34 |

At R = 3 and T = 34 this is the Phase-0b objective verbatim (`phase0_campaign.py:1752–1773`). It is not a likelihood.

**Arm (iii).** Uses the Anscombe binomial transform, the binomial analogue of √(x+3/8), with sampling variance ≈ 1/4:

\[
z(k)=\sqrt{n+\tfrac12}\;\arcsin\sqrt{\frac{k+3/8}{n+3/4}},\qquad
\bar z_\theta=\frac13\sum_{j=1}^{3} z(k_{j\theta}),
\]

\[
L^{iii}_i(\theta)=\frac{1}{2T}\Big[\sum_{c,t}\big(\sqrt{y_{ict}+3/8}-m_{\theta ct}\big)^2+\big(z(k_i)-\bar z_\theta\big)^2\Big].
\]

**Declared weight and why.** The existing 68 date-channel terms keep exactly their Phase-0b per-datum weight 1/(2T), with no silent reweighting. The serosurvey enters as one additional datum at the same weight. Both are variance-stabilized to the same ≈ 1/4 noise scale, so equal per-datum weight is approximately inverse-variance weighting. The anchor's influence then comes from n through z, not from a tuned multiplier. The finite-population correction makes the true serosurvey variance slightly below 1/4, so the anchor is, if anything, slightly under-weighted.

**Unchanged rules (all arms):**
- Tie rule: τᵢ = 10⁻¹² · max(1, L_min).
- Profile by minimizing over the other three dimensions.
- Identified = unique profile minimum within τᵢ, and relative gap ≥ 0.05 with denominator max(P_min, 10⁻¹²).
- A tied global minimum fails.
- Ordinary float inclusive comparisons for computed gaps.
- Exact decimal arithmetic for signed error, tolerance and bias on the declared grid.
- No epsilons, and no reinterpretation of equality at `0.05` or `1e-12`.

**Blind boundary.** The fitter receives only the target's observed tables (and, in arm (iii), k and n), the declared grid and the candidate library. Each blind estimate is hashed and persisted with read-back before any truth join. All generation for all arms completes before any truth join, so no arm can react to another arm's results.

## 7. Predicates and outcome rules

### 7.1 Per-arm recovery gate

The Phase-0b P0-1 predicates and thresholds apply verbatim to each arm X ∈ {B, i, ii, iii}, on ten targets. The fractions keep their meaning and are evaluated with exact integer arithmetic: hits·5 ≥ 4·10; joint·5 ≥ 3·10; boundary·5 ≤ 1·10.

`X RECOVERY GATE: PASS` only if all of:
1. All 10 target runs, all 625 candidate cells and all R replicates per cell complete without replacement.
2. Each truth run realizes all ten inoculation acquisitions, at least one local secondary infection, reports in both channels, and at least three nonzero combined-report dates.
3. Observation chronology and latent-incidence conservation pass.
4. No target has a numerically tied global minimum.
5. Every dimension is identified and within tolerance for ≥ 8/10 targets.
6. ≥ 6/10 targets are identified and within tolerance jointly in all four dimensions.
7. Every dimension's absolute ten-target mean bias is ≤ its limit (exact decimal).
8. No dimension is selected at an outermost grid value for more than 2/10 targets. This is computed by its own code path. As in Phase 0b it is implied by 5 on these grids, and the per-dimension count is reported.
9. Seeds, namespaces, grid, objective, dates, fixed parameters, H (arm ii), serosurvey design (arm iii), read-back and blind provenance match this declaration.
10. Measured work equals the §9 caps.

**Status and failure rules:**
- `software_status` and `scientific_status` are kept separate, as in Phase 0b.
- An extinct or uninformative truth fails predicate 2 and is never resampled.
- A poor or extinct candidate is scored.

### 7.2 Pre-declared comparisons (no forking paths)

**Exactly three primary comparisons:** (i) vs B, (ii) vs B and (iii) vs B. Each is the pair of gate verdicts.

**Explicitly excluded:**
- arm-vs-arm comparisons;
- pooled or combined arms;
- target subsetting (e.g. excluding fallback populations);
- alternative thresholds, re-weightings, alternative H, alternative n, or alternative R.

**Secondary descriptives.** These cannot change any verdict or reading. Replicate spreads are stochastic replicate variation, never confidence intervals.
- (a) Per arm: offset identified-and-within-tolerance count, offset boundary count, and all per-target profiles.
- (b) Arm (i):
  - re-profiled offset per target under each of batches A, B′, C′, D′ (3 replicates each), A∪B′ (6) and all (12);
  - per fixed tuple, the range and median of the four batch objectives;
  - the count of targets whose four batch offsets agree.
- (c) Arm (ii): the prefix-identity result, per-target latent peak day, and the manipulation check.
- (d) Arm (iii): k/n per target and candidate; z values; the serosurvey term's share of L at each selected cell; and, per target, the realized ever-infected fraction at d from the truth run, with a descriptive flag `n_criterion_premise_met` = (fraction ≥ 0.25). The flag never changes a verdict.

### 7.3 Number of targets: 10 per arm, shared

**Argument (grid-independent, not from Phase-0b results).** Treat per-target joint recovery as Bernoulli(p). Under predicate 5's threshold:

| | p = 0.5 | p = 0.7 | p = 0.9 |
|---|---:|---:|---:|
| 5 targets, P(≥ 4/5) | 0.188 | 0.528 | 0.919 |
| 10 targets, P(≥ 8/10) | 0.055 | 0.383 | 0.930 |

Ten targets cut the chance of passing a coin-flip recovery from 19% to 6% without losing power at p = 0.9. The cost is five more target latent calls, five more transforms and five more builds per campaign.

**What 10 can resolve:** gross differences, roughly p ≈ 0.9 against p ≈ 0.5, per arm.

**What 10 cannot resolve:**
- p near the 0.8 threshold;
- small differences between arms;
- a rate estimate with useful precision;
- process versus observation noise.

Targets are shared across B, (i) and (iii), and the seed streams are shared with (ii), so the arms are correlated, not independent replications.

### 7.4 Readings per arm (descriptive statements, separate from the gate vocabulary)

| B gate | X gate | Reading |
|---|---|---|
| FAIL | PASS | "Factor X, at the declared level, coincided with four-dimensional recovery in this one synthetic campaign." Screening result only. |
| FAIL | FAIL | "Factor X alone, at the declared level, did not produce recovery." Arm (i): evidence against Monte-Carlo noise as the sole cause. Arms (ii)/(iii): that factor did not break the ridge at this level. |
| PASS | PASS | "The fresh-seed baseline at ten targets passed the recovery gate. Factor X is not shown to be necessary." This is not a replication of the Phase-0b design (five targets, retired seeds) and alters no Phase-0b verdict. |
| PASS | FAIL | "Factor X coincided with loss of recovery." Reported as an anomaly; no causal reading. |
| any | software FAIL | Arm VOID, with no reading. §8 VOID rules apply. |

**Overall reading:**
- **No factor arm PASS and B FAIL:** "None of the three factors, one at a time at the declared levels, made the recovery gate pass. The ridge hypothesis (H2) is not contradicted."
- **One or more factor arms PASS:** each is reported individually with the multiplicity caveat below. No "best factor" is declared.

**Multiplicity.** Three arms raise the chance that at least one passes when no factor matters. Thresholds are not adjusted, because that would require numbers not justified independently of Phase 0b. Instead, a PASS reading is screening evidence only. Any later decision relying on it requires Steven's decision and a new owner-ruled, fresh-seed confirmatory predeclaration.

**What no outcome authorizes:** real-data fitting (G34 stays in force); any change to the Phase-0 or Phase-0b verdict; any claim of calibration, validation or coverage. State files use the exact phrase "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: not run" before the campaign, and afterwards "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B <PASS|FAIL|VOID>, i <PASS|FAIL|VOID>, ii <PASS|FAIL|VOID>, iii <PASS|FAIL|VOID>". PASS/FAIL are recovery-gate verdicts; VOID is a campaign status under §12; the §7.4 readings are descriptive text and never appear in the status phrase.

## 8. Seeds and replacement rule

All seeds are fresh and mutually disjoint, and disjoint from every earlier set: Phase 0 `42001–42005`, `52001–52005`, `43001–43003`, `53001–53003`; Phase 0b `62001–62005`, `72001–72005`, `63001–63003`, `73001–73003`. The harness holds all earlier sets as an independent module constant, never derived from the supplied config. Seeds are reproducibility identifiers, not parameters.

**How seeds map to work.** The process seed is the population/network build seed. `run_p01_campaign` calls `build_parent(..., process_seed, ...)` (`phase0_campaign.py:2612–2624`), and outbreak and network seeds match. Observation and serosurvey seeds build nothing.

| Role | Primary seeds | Pair / namespace | Reserve (process only) |
|---|---|---|---|
| Probe process (pre-freeze only) | `81001–81003` | obs `91001–91003`, `v13-g35b-probe` | `81004–81006` |
| Target process | `82001–82010` | obs `92001–92010`, `v13-g35b-target`; sero `94001–94010`, `v13-g35b-sero-target` | `82011–82015` |
| Candidate process, batch A (= B, iii, ii) | `83001–83003` | obs `93001–93003`, `v13-g35b-fit`; sero `95001–95003`, `v13-g35b-sero-fit` | `83013–83017` (shared candidate pool) |
| Candidate process, batches B′/C′/D′ (arm i) | `83004–83006` / `83007–83009` / `83010–83012` | obs `93004–93012`, `v13-g35b-fit` | as above |

**Pre-freeze replacement rule** (deterministic and outcome-blind; applied once, by the director's build pre-check on `cf45153`, before any epidemic simulation of study seeds):
- Every process seed above, primaries and reserves, is built with `build_parent` at mode `ci`.
- A primary seed whose build raises any exception is excluded. It is replaced by the lowest-numbered reserve of the same role pool that built. The replacement takes the failed seed's position, paired observation and serosurvey seeds, and batch membership.
- Known failure classes include the adult-supply and household-capacity residual classes, which have no owner rule (G36).
- A build that succeeds through a reviewed fallback (M2 `private_assignment_residual_fallback` or M3 `destination_reassignment_fallback`) is **not** a failure. It is kept, and its fallback diagnostics are recorded as lineage. A different rule is owner decision 7.
- If a pool is exhausted, the draft returns NEEDS OWNER INPUT.
- The frozen text lists final seeds, excluded seeds with their error class, and each final seed's M2/M3/M4 logical hashes.
- The campaign verifies that its builds reproduce those hashes exactly, as an independent source of truth.
- After freezing, there is no replacement of any kind. A build failure at execution fails predicate 1.

**Frozen pre-check outcome (filled mechanically from the build pre-check record, 2026-10-22):**
- All 38 process seeds were built on `2cfb9f6d249c64fe78e0716a6a6ff6208ac681b5` (code tree identical to `cf45153`): 37 BUILT, 1 FAILED.
- **Every primary seed built, so the replacement rule was not triggered.** Final seeds are exactly the primaries in the table above.
- Excluded: reserve `82011` (`DataBuildError`, adult-supply residual class). It was never a primary and is not used.
- Fallback-built final seeds, kept per owner decision 7 and disclosed under A10: M2 `private_assignment_residual_fallback` on `82003`; M3 `destination_reassignment_fallback` on `82007`. Probe seed `81001` and reserves `81005` (M2) and `83015` (M3) also used fallbacks; they are not study seeds.
- Record: `docs/runs/2026-10-22-g35b-seed-precheck.json` (sha256 `9d15beb0abc7e3e190008dbb1d89aecc8bc3488e926c55f632bbe83b5d2614f5`), with its log and script. The campaign must reproduce the M2/M3/M4 logical content hashes below exactly (§8).

| Process seed | Role | Build | Fallback disclosure | M2 logical hash | M3 logical hash | M4 logical hash |
|---|---|---|---|---|---|---|
| `81001` | probe (retired) | BUILT | private_assignment_residual_fallback | `835b08b2de3109e6a3aeeff423b8b67f8c931a5352f885d76f6cccee099547ec` | `8eadaa8f621385e0201240cf412ad8995e81f1ae7406ef7d769e744f95505d88` | `915d0d2556c476e7e7fec7b9ae65763b462962c327c34063229433c056268e1b` |
| `81002` | probe (retired) | BUILT | none | `05bffe224c9f7cc304a2acb2f92c38afc759855b084ba5f990b3fad03a003807` | `32d7f5ab829ff7375bca3b74f1ba232dbf348524ab5174395a42fe9ed6ccbcf5` | `c42c13e91d505b7d2e0df3c1f2660b701aa231f73425432d0defcc9925e6f1fc` |
| `81003` | probe (retired) | BUILT | none | `4cdf6e3b81281765b4e7eab099260bacda36beba30faddce8965131422eca884` | `925a86884cf0121f84731339349ad78bae693914fa2f22b19dee96b7f9ad4c11` | `fdef7c1c899e351b4a68c3156ceb126edc98f5c6719dd49f0ca1dcfe41620f1e` |
| `81004` | probe (retired) | BUILT | none | `badb2068dccc34e1ebd0cfe22ee2847c3d5a11bb18a3acf0c45fc58d2ca48f54` | `98b9c883daf8880de4f88acc77ab7c13870eca90e44899db5b103053592b1522` | `13eea0970989b8db4ac6b4c9d482f82568257030ec738ff39fdc2c154489164f` |
| `81005` | probe (retired) | BUILT | private_assignment_residual_fallback | `6d46b3279c069d83682bebfced031c3732a70249301fff6a94856f5bc7464d59` | `7e562541fbcbabe758eb795404b3352f25b2b2fbd360c7819ef942e094906d90` | `ec1d94571565c4dcc267750af3d6f55e6888e57c10e7eb73b3775cf626299123` |
| `81006` | probe (retired) | BUILT | none | `f45b9c82130ca518327ec846940012ae48836ff63a3ecadf3c41d5ef884fbb5a` | `717861d92efa421c3f5af18ba13a203a4785f32e7cd39e00c337b55f6b71f8c1` | `c5cd5d7574b0ab77e9188a209e7975c67577e457a454f5ef865e41bd3c27139d` |
| `82001` | final (primary) | BUILT | none | `29be3731586fcb88f93edd646c9db8aae1057dc11f7f18a947f67b9ad01f3e19` | `473a4901f68338392a74c0b3f2df23518f9df1a1c09f01d7508d827e3ebb3f75` | `0315d935b99761abdfb79eddfd66077d300e056379f47c2af69c033d12779bab` |
| `82002` | final (primary) | BUILT | none | `0fcfa17427521af536c7fc7eddb247b1665acba2ca802be0cb7c9951d7e0b7ea` | `709c123cffb0a8dc8c8fdf79f83347fd038bc1fe2390f85087ebba2a92b1a213` | `1fa4eb9b9f80c013d6c8ca97e72d87d6aaa101e8f1812ec6026af0c26dfc2bc5` |
| `82003` | final (primary) | BUILT | private_assignment_residual_fallback | `2e2abec14b86855210b5db41a0f32f1ef26401dcf4a9df87c26460ec78f51c3d` | `c8c73f50e6f9db8abcc165bf292390b1067d824a255fb94a0777f92290514233` | `9f8211d43f9352e6b1c716988695839a7ba10c1781173a6071d7914edd73acfc` |
| `82004` | final (primary) | BUILT | none | `4c91addee491fc2ce5efe84b21a3f18ad2822d852f97134f5cec9382835aa2d7` | `de4114c92f4ed53e33b85f52086ad21797acebbdb1acc6ba25fe6240bb9270aa` | `121b6ff4756ed002cc12865f53e47cdf0048e95391ec91b548011f3f9abcc1ca` |
| `82005` | final (primary) | BUILT | none | `366d6486a4790093e9845b31efc0c79a530fdb22d607db24ac905160b6ddebf2` | `18d02e1413e81f9bdb295a2dc9a86ca8d005d4ad16a55e98351c3edcb2365bcd` | `7b7719d020070878215ddce776005878f281146be7f9c69bf78d2c2fd30694e0` |
| `82006` | final (primary) | BUILT | none | `9a55c6f251af65bf70694b04a1d4030530ff481828eb1435243fc2c6701cfa0d` | `18ecca09b73e9711ca71b52d36b42bc7bf906b22a382fcd53902a16e25d5116b` | `0919bc563350669a31672a685324205c19b8c875274e778b27ea572b85b1399d` |
| `82007` | final (primary) | BUILT | destination_reassignment_fallback | `f857b9bee85696f7d1ddb999e5e92bf9e8d8ef078a050ee853fffac37580b01c` | `202589ef822273969468ef1b5336a758f7e9738692455ef8f4bf11d21065f258` | `ba70c35a4afc547c4ce9960dff3a39907dcc128e1a87214c72d298a3c82ad6bb` |
| `82008` | final (primary) | BUILT | none | `2e28de397db5a765e0c6484ef4dbe98aaec638eb58f62488656b2b113a36e60e` | `3d0ec001d43734484b31d8a796541fa2958b08ce8e2a2bba13fbb3f6fffe0542` | `beb428c9d6a1420444bd60dcc5cb9fdf4e6cad6785672834bc4fc9c262a8c405` |
| `82009` | final (primary) | BUILT | none | `a7a472c8e974e065ab8b80d3a638d7b45802dfd03a4c9e238cf671d1cacec24c` | `583502f9615196e331b297f062cc534dd78132720260f3159847f0dbbf7eb252` | `be0013d9a4a1899316693c1d76a55254ed9b2cd7e4fd0c9fc680158fa8e71e50` |
| `82010` | final (primary) | BUILT | none | `beba6277bc836401f506e813d38915ada5932896122bd331882b63f0952aebf1` | `3df598689ee901d22aac5a0b325e5667ae9e6bfa570a38d7aad79a97176abd9b` | `a277760a2224db3bab4986de9a15ed302c9f3a15b334128209ca3e3cda4c3f52` |
| `82011` | reserve (unused) | FAILED: DataBuildError (adult-supply class) | — | — | — | — |
| `82012` | reserve (unused) | BUILT | none | `432ac679849a60a30eb7fb76066d8a20c8e001b1a88b4269577f16e62bbe10bb` | `02b0ed56c6aa11b0341ab86397501808ca69d881d53a62e2428e583e4ca52815` | `7555dfcee0c64c38137aa04874359631b3d4a5303904def616b6e0d19ef64ddb` |
| `82013` | reserve (unused) | BUILT | none | `ecaac8f6cd9ce7d5bd22fb04beeebb9cc73a73570b07b70ca43f2a2a0f0bc357` | `5bc73bfee3d4d1d37a885b6c44f133f08d2d6cc03c65fbc4ffea6f426f09aacc` | `0eaddae5550cd9b48bd3c6a652216411e97fe61d7c671bf00930952d32ce59c6` |
| `82014` | reserve (unused) | BUILT | none | `caefa1b1ce3005225e6ce39d4d5a1d51ca4088af4f3062dde62ef76a928fadb2` | `ca945fff0150272a498bd4ba68c359f2a69890bb68c313738f9cc40e99bb92d8` | `6259368a1a1be79196bb9567c1b4589d93e5557d3530e68c1efea80f1667bce8` |
| `82015` | reserve (unused) | BUILT | none | `f47c69426912006502635f484a757c51b71ee7b3016de321795c9fe8979638fb` | `bc7a671a07c43562b33a837cf8015d598a653880718c6831cd91828ed1f89c8e` | `78a2c8c02da114b349aa025eb67358a33e1a2486c2ce64ee61e7b1d06749b5f1` |
| `83001` | final (primary) | BUILT | none | `cd9b3810b7f82c7acc98afb308f292a7a31e9f8439e9e48c4fc9719e8ebf27db` | `e50724db82ac5475249d7adfa0f779f5e408df78de3f024fc722564269cfb66d` | `448920b78f1effdca6236389a14b241d8352a806e4f5f352ec03e0ecba510bd5` |
| `83002` | final (primary) | BUILT | none | `18576334ad6bbe771a7cbf2efdf44344afd71b104ecdc8125ad2884d22ef53ea` | `109bb47e8eafdc912ed7963c316384db5277b36abb088c3570d5d258d0db0df8` | `be6d085971128ec37d95bc92e7b75f3edebe8e7daae78a6359023d2189a4e977` |
| `83003` | final (primary) | BUILT | none | `1942929d096e8999dd335d39893f16926bd40aab4b9971b610d3848bc2286617` | `287fd4b9f23b5bf939658d8793b3067f49468992d49426e81b2205711112209f` | `6b614984120615ccd78d44aec9c4302bfe691fadc93b6ec93bf1337b79bab0fc` |
| `83004` | final (primary) | BUILT | none | `d791b1cccb554c02cffd88d0887142694e2e64d440fa2bf4aa7bec6bf28e4525` | `a388e9ace447324fad942d6b716d882e9e8a2a69abf1cf5dd1a44e03eb363e0e` | `79fcdd9aa3ac2d9171d3a81ce70e2862c8dc0f420bc1bd2b49200ae04728cacc` |
| `83005` | final (primary) | BUILT | none | `cdf5d4ef0c1fc113a9c379da9db8dcf5080b8ff2dda0f8f785b8dfa1671a706e` | `601866c328f023292ac4d488ce5496161f7afd9b018fd9e1fa85724401aed3c3` | `cd94b37f3a67a48b3cb3d99bd6f3547aed9632e16abac7bb4d309087c673af81` |
| `83006` | final (primary) | BUILT | none | `b590f15749a0b9536be85cd646fc6e7cf867baa74f310580fd4c4673b001f5ef` | `d2608c75efe50704ab46c3d072b56b287726d77494b8fe2db6f3a17188030f1c` | `0af0c44893a755363caeec5474be033c92ebc55d511b735cc7ab98450a7a9acb` |
| `83007` | final (primary) | BUILT | none | `0d51d1f8b9ae6a2ebb4a44935c4d02d99eb309f4a70e50a563ad7aae0d39808e` | `bd40941d56e8f76fb2175e2a430227f283698cda137bcb4e9a7b03e002d163ff` | `8ed53ac6aa78a9fca98004b425e91d2a4c21f0f60e0f5a2ece717a76621cd95b` |
| `83008` | final (primary) | BUILT | none | `7453dbf5d3eea512497c995c92f64527534a1c80a0e1d9b7df165affd9587ebe` | `446e5f5722808f335a9c88d7ee3eec4b8242bcb7616d525c9f7865f70472c500` | `65d1bff09584abb3528d0356a5b5ae7507c2d38f54b2288a8aca97a529d32426` |
| `83009` | final (primary) | BUILT | none | `4c91becbd1d218f4f9c6b76a7e203714f0aefcba5cdf6346f1cc7d9a2591b7ff` | `6538342b86913f0143b9c39c914fbc18f9cd0a2ba69b4f63b95c793cef91d49d` | `5e3562d890207aab01cb3072baa8bdd13654001db93c45b304192c5dab1b9fee` |
| `83010` | final (primary) | BUILT | none | `c2d6c43a84cbabc7704482e646535bad0613e378a8ab628114117717093b9752` | `d0bb98138cb48c04ecfabe8e32d06a0230fec6fd041de391bbed23044446b036` | `f21ba813a10683ab8ac7ee60901f4905da951052053a581dd7764d4c362fb224` |
| `83011` | final (primary) | BUILT | none | `b9195f7493f6d647d59e92274030c5723d4c0595ee95c2e144fdc8c8b69fbfe7` | `8e2f646d05eb1de06f532bc0980e2d75b88c61b12ad095386bf5f9b7b3986107` | `42ee89e0306f1d0c699bf4dce1dc7a70aca4df9fd6b9dc285ef301c51750e617` |
| `83012` | final (primary) | BUILT | none | `969a04909ef4d6385258ab3256e83554aa95d426898547f6df1b0e2486ab6d44` | `a6f42c1dbdc8eccd715e041d6c80771534bf22b73cf76a995fe6793e78e04f25` | `3b43297015067c60e3a8e32e6e5181700d3070360c2a98a00cf370db04e8f3b4` |
| `83013` | reserve (unused) | BUILT | none | `c5a61d4c927869d9b737ec05fe4fe0e57f091c943ca3b8bd4b8beb5372f5007a` | `6f90d20e98d438c7f1ccd86cccb5c36235ff290eb68d38fdb797d29b774cfe81` | `5a85c85482d1cf379f8a249f7915e56774343f71bc9f317b5d41df19e54f5b7b` |
| `83014` | reserve (unused) | BUILT | none | `eb57b2e73b3184d345bbc937f09fc8b7955831564574a7ad0c8ee5a420f06fc8` | `126a1259047cba92a1862d52e38cf2886bf8be892d765f266555bf7e64f53b0a` | `d76515301d2e104099a4609f308c36d26100aef2a565daec5fb25a8ba73b907a` |
| `83015` | reserve (unused) | BUILT | destination_reassignment_fallback | `345d0394ea67753eff9d50bf505cc4a1a531c62ed7a7d064c6679e28b4823dcf` | `dda73202a44839291d0b4b03c5c7eacd9ed136f5fb1d4ef5efff2c421f1a6e57` | `45a95fe6b9ba5374dc2cb7e1e105fc444de473a9d43f98de512e81f9955c3169` |
| `83016` | reserve (unused) | BUILT | none | `eb598e65f7689b93ee4f17d28439759a90eb8e47b4c92bc0fcb72b00bc7ec957` | `cc3edfcdf410f0975a9934c15dd3b00169e987790945f8bb8df5ef72b3ce8046` | `43120fcb6a418f40cfd4448b074b0e7dae127638a41fee91fbf3408ddbfab3e4` |
| `83017` | reserve (unused) | BUILT | none | `c253958d8da53e41e3c1b5acce6089249e0f60ffbd3dbea9c66724338405c399` | `c93e15e0a9783f579302509f34ec872c65e2f03a353e5e08837ae32ce5b7304b` | `4e23e29d1e001a4459171ef8f73b68eff8b690c3e05ace4ce31a3361540f1dbf` |

## 9. Workload and fail-closed caps (ci mode)

Counts assume parents built once per process seed and shared across arms, and candidate latent runs reused across detection probabilities.

| Arm | Gate cells | New latent calls | New report transforms | Serosurvey samples | New builds |
|---|---:|---:|---:|---:|---:|
| B | 625 | 10 + 75 = **85** (30 d) | 10 + 625×3 = **1,885** | 0 | **13** |
| (i) | 625 (R = 12) | 9 × 25 = **225** (30 d) | 625 × 9 = **5,625** | 0 | **9** |
| (ii) | 625 | 10 + 75 = **85** (H d) | **1,885** (H + 4 dates) | 0 | 0 |
| (iii) | 625 | 0 | 0 | 10 + 75 = **85** | 0 |
| **Total** | **2,500** | **395** | **9,395** | **85** | **22** |

- **Scoring, no simulation:** 4 arms × 10 targets × 625 = 25,000 gate loss evaluations. Descriptive arm-(i) re-scorings add 4 batches (A equals B) plus the nested 6, × 10 × 625 = 31,250.
- **Outside the campaign:** the build pre-check covers 38 process seeds. The horizon probe uses 3 builds, 6 latent calls (3 × 30 d, 3 × 91 d) and 6 report transforms.

**Dry-run must enforce exact equality** to:
- per-arm cells `625/625/625/625`;
- latent calls `85/225/85/0`, total `395`;
- transforms `1,885/5,625/1,885/0`, total `9,395`;
- serosurvey samples `85`;
- builds `22`;
- latent duration exactly 30 (B, i) and exactly the frozen H (ii);
- mode `ci`.

Dry-run also rejects: seed overlap within the study or with either earlier campaign; retries; replacement; adaptive work; any predicted or measured breach.

**Wall time (unmeasured; disclosure, never a cap).** Phase-0b's P0-1 arm took 307.5 s for 80 latent calls, 1,880 transforms and 8 builds (`campaign_summary.json` disclosures). Scaling linearly, which the G34-B memo warns is unreliable, gives a rough order of magnitude of 30–60 min in total; arm (ii) depends on H. The probe's measured per-call runtimes are filed before freezing.

**Retained-artifact size estimate.** Phase-0b P0-1 observed tables took ≈ 7.4 MB on disk for 1,885 tables of 34 dates, ≈ 3.9 KB each. The Phase-0b bundle totalled 16.6 MB logical (28 MB on disk) across 4,043 files. For G35-B:

| Component | Estimate |
|---|---|
| 30-day tables (7,510) | ≈ 30 MB |
| Arm-(ii) tables (1,885 × (H + 4)/34; H ≤ 91) | ≤ 21 MB |
| Loss surfaces | ≈ 15–20 MB |
| Blind records (40 gate + 50 descriptive) | ≈ 15–35 MB |
| Provenance and lineage | ≈ 10 MB |
| **Total** | **≈ 70–120 MB, ≈ 10,000 files** |

The director checks host free space (≥ 5 GB margin) before execution.

## 10. Outputs and retained artifacts

One fresh, immutable bundle in a new empty destination, containing:
- **Frozen inputs:** campaign config and SHA-256; this predeclaration and SHA-256; the owner ruling and SHA-256; source and config hashes.
- **Pre-freeze records:** build pre-check record (seeds, exclusions, M2/M3/M4 hashes, fallback diagnostics) and probe record (H derivation, prefix-identity result, runtimes).
- **Seed ledger** for every role.
- **Per arm:** complete loss surfaces, blind-estimate records with read-back hashes, `g35b_<arm>_recovery.csv` with every per-target predicate value and boundary flag computed by its own code path, plus per-target columns `population_fallback_m2` and `population_fallback_m3` (TRUE/FALSE from the build diagnostics) and a per-arm descriptive count of fallback-built targets and candidates. These are disclosures and never gate or subset, and measured counters.
- **Per candidate replicate:** the two-channel table for every cell, plus its process seed, observation seed, batch, and population lineage (M2/M3/M4 logical hashes and both fallback diagnostics).
- **Per serosurvey sample:** sampled agent IDs, everInfected flags, k and n.
- **Descriptives:** the arm-(i) batch and nested descriptives (§7.2b).
- **Summary:** `campaign_summary.json` with the §1 lineage block, per-arm gate verdicts, readings and wall-time disclosures.
- **`SHA256SUMS`.**

The exit-audit verdict lines read `G35-B ARM <B|i|ii|iii> RECOVERY GATE: PASS|FAIL`, followed by the §7.4 readings.

## 11. Protected contracts

**No change to any of:**
- `outbreak_runner.py`, `respiratory.py`, `observation.py`, `observation_scheduler.py`, `observation_schemas.py`, `population_*`, `parent_build.py`, `starsim_adapter.py`, `calibration*.py`, `hashing.py`, `scientific_hashes.py`;
- any artifact schema or identity/persistence contract;
- the handoff §10.4 list (resident identity, seed determinism, observation/latent-truth separation, lifecycle ordering, scientific artifact hashes, no missing→zero coercion, no fabricated uncertainty, among others).

**`phase0_campaign.py` stays byte-unchanged.** The Phase-0 and Phase-0b profiles must still dry-run to 198/59/599/8 and 1,334/107/4,007/8. The new harness imports its pure functions and does not extend it, because it hard-codes:
- 3 replicates (`:51`, `:1756`, `:2744`);
- the 30-day / 34-date calendar (`:1396–1405`, `:2025`, `:2470–2478`);
- an absolute boundary count ≤ 1 (`:2224`);
- a two-profile "other profile" disjointness check that cannot cover a third campaign (`:1480–1488`, `:1638–1646`).

**Stop condition:** any need to modify a protected module, `phase0_campaign.py`, or a contract stops the unit. It requires a separate owner-rulable brief.

## 12. Unit order

0. **Owner ruling** on this draft (§16).
1. **Director pre-freeze actions** (no study simulations):
   - commit this ruling via `fm.sh sync` `[skip ci]`, record its SHA-256 in the trail, and attest that the code tree at that commit is identical to `cf45153` (`git diff --stat cf45153 HEAD -- src configs tests scripts` empty);
   - build pre-check of the §17 process-seed list on that tree, then the replacement rule;
   - horizon probe and prefix-identity check, filed as `docs/runs/*.py.txt` with logs and per-call runtimes;
   - fill final seeds, hashes, H and the prefix result mechanically into the text; commit the frozen predeclaration via `fm.sh sync` `[skip ci]`; record its SHA-256 in the trail.

   The probe may not start before the ruling commit exists on `main`.

   A probe stop rule or exhausted reserve pool returns the draft to the owner.
2. **U1** (`Class: numerical`): standalone harness, declaration, dry-run and caps, generalized R/T objective, integer-count predicates, baseline arm with mocked execution.
3. **U2** (`Class: numerical`): arm (i), batches, nesting and descriptives.
4. **U3** (`Class: numerical`): arm (ii), H-day latent runs, calendar, prefix-identity and manipulation checks.
5. **U4** (`Class: numerical`): arm (iii) serosurvey model and augmented objective.
6. **U5** (`Class: numerical`): integration, bundle, summary and readings; frozen-profile regressions.
7. **Independent Sol review** of the complete implementation against the frozen text.
8. **Steven authorizes one all-arms campaign.**
9. **Fresh independent exit audit** recomputes from the bundle.

**VOID and FAIL rules (Phase-0b §12.2–12.3 pattern):**
- A defect named by an independent reviewer makes the campaign VOID. A corrected rerun uses the same seeds, with Steven's authorization.
- A scientific FAIL is never reclassified.
- No second campaign without Steven's explicit chat decision.

## 13. Implementation brief outline

**U1.** Add the following:
- `src/jersey_outbreak/g35b_design_study.py`
- `configs/calibration/v13_g35b_design_study.yaml`, with decimal strings and every seed listed
- `tests/test_g35b_design_study.py`

The module must provide:
- an independent constants module holding all earlier seed sets and this document's digest;
- strict frozen-payload validation and dry-run reporting the §9 counts exactly.

Acceptance:
- **Generalized loss:** equals `phase0_campaign.minimum_distance_loss` bit-for-bit at R = 3, T = 34 on fixtures, plus an R = 12 hand-computed fixture.
- **Generalized blind fit:** equals `phase0_campaign.fit_blind` on a Phase-0b-shaped fixture.
- **Predicates:** integer-count predicates with endpoint regressions at 8/10, 6/10 and 2/10, plus decimal endpoint and cancellation regressions.
- **Generation path:** the baseline generation and orchestration path is implemented and mock-tested with real config constructors and faithful result metadata (DIRECTOR lessons 2026-09-22).
- No campaign execution.

**U2.** Arm (i) acceptance:
- four batches scored at identical tuples;
- nested 3/6/12 library;
- batch A byte-shared with B;
- descriptive re-profiling;
- retention of every replicate table with seed and lineage.

**U3.** Arm (ii) acceptance:
- H read from the frozen declaration, never computed at runtime;
- (H + 4)-date calendar;
- the prefix-identity check reproduces the probe's declared result on a fixture;
- a cap test rejects any other duration.

**U4.** Arm (iii) acceptance:
- **Independent cross-check:** a census (n = N, perfect assay) equals `daily_epidemic[d]["ever_infected_fraction"]` × N exactly.
- **Unique identities, not episodes:** a waning-enabled fixture with a repeat episode counts that resident once.
- **Seed-only sampling:** the sample depends only on (process seed, serosurvey seed, config ID, agent IDs), with common random numbers across cells.
- **Transform:** the Anscombe transform matches a hand-computed value.
- **Objective:** the augmented loss equals L^rep + S/(2T) exactly.
- **Blinding:** the fitter cannot receive the latent run.

**U5.** Acceptance:
- one bundle, the lineage block, readings logic as a pure function with a table-driven test over all §7.4 cells;
- measured-equals-planned checks;
- Phase-0 and Phase-0b dry-runs unchanged.

Every brief requires changed-file and diff-stat reporting, focused regressions before the full suite, and a stop on any protected-contract conflict. No implementation brief authorizes a campaign.

## 14. Acceptance commands (proposed gates; not run in this consult)

```bash
git rev-parse HEAD; git status --porcelain
UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.g35b_design_study dry-run \
  --config configs/calibration/v13_g35b_design_study.yaml \
  --predeclaration docs/research/v1_3/<frozen-g35b-predeclaration>.md
UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.phase0_campaign dry-run \
  --config configs/calibration/v13_phase0_synthetic.yaml \
  --predeclaration docs/research/v1_3/2026-09-21-phase0-predeclaration.md      # 198/59/599/8
UV_CACHE_DIR=/tmp/uv-cache uv run python -m jersey_outbreak.phase0_campaign dry-run \
  --config configs/calibration/v13_phase0b_synthetic.yaml \
  --predeclaration docs/research/v1_3/2026-09-25-phase0b-predeclaration.md     # 1,334/107/4,007/8
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/jersey_outbreak/g35b_design_study.py tests/test_g35b_design_study.py
UV_CACHE_DIR=/tmp/uv-cache uv run ruff format --check src/jersey_outbreak/g35b_design_study.py tests/test_g35b_design_study.py
UV_CACHE_DIR=/tmp/uv-cache uv run mypy --ignore-missing-imports src/jersey_outbreak/g35b_design_study.py
UV_CACHE_DIR=/tmp/uv-cache uv run python -m compileall -q src
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_g35b_design_study.py tests/test_phase0_campaign.py tests/test_phase0b_campaign.py
UV_CACHE_DIR=/tmp/uv-cache uv run pytest            # once, on final bytes; full CI verify-job mirror
git diff --check; git status --porcelain
```

Only after review and Steven's authorization:

```bash
UV_CACHE_DIR=/tmp/uv-cache STARSIM_INSTALL_FONTS=0 MPLCONFIGDIR=/tmp/mpl-cache \
uv run python -m jersey_outbreak.g35b_design_study execute \
  --config configs/calibration/v13_g35b_design_study.yaml \
  --predeclaration docs/research/v1_3/<frozen>.md \
  --owner-ruling docs/research/v1_3/<ruling>.md --output-dir /tmp/jos-g35b-campaign-<run-token>
```

## 15. Limitations

- **Ten targets** give a descriptive screen, not a rate estimate. The arms share targets and streams, so they are correlated. Three arms create multiplicity (§7.4).
- **One level per factor** (R = 12, one H, one n at one date). A FAIL says nothing about larger levels, and no factor interactions are tested.
- **Arm (i)** cannot separate process from observation noise. Each replicate varies both streams. Four batches give a crude spread.
- **Arm (ii)'s H** comes from three probe seeds. Some targets may peak later; the manipulation check reports this. If the prefix-identity check fails, the realizations are not matched.
- **Arm (iii)** uses an idealized assay with a zero lag, one survey, and n = 400 from a 3,000-resident synthetic population. Its weight is one datum. A PASS is an upper bound on what a real, imperfect serosurvey could give. A misspecified-anchor control (wrong sensitivity or specificity) is not included, and would be required before any reliance.
- **Populations** that built through reviewed fallbacks are kept and disclosed (G36 caveat: point mass in repaired destination shares).
- **Scale and objective.** CI scale, a two-channel square-root distance (not a likelihood), and not the later cases/tests/positivity/serology objective. Replicate spreads are stochastic replicate variation, never confidence intervals.

## 16. Attestation

- **Checkout.** Read-only Windows checkout at HEAD `4d0e1275d329da37a367000ce217b300d6091200`. `git diff --stat cf4515381e0ccc1f7eb8762894b237518f159c78 HEAD -- src configs tests scripts` was empty, and `git status --porcelain` was empty.
- **Code read:** `phase0_campaign.py`, `outbreak_runner.py`, `respiratory.py`, `observation.py`, `observation_scheduler.py`, `observation_schemas.py`, `outbreak_schemas.py`, `parent_build.py` (signature), and the fallback sites in `population_generator.py` and `population_structure_generator.py`.
- **Docs read in full:** the Phase-0b predeclaration, owner ruling, failure mode, ridge diagnostic, G34-B memo, V1.3 plan, Phase-0b exit audit, G29 ruling, GATES/RUN/DIRECTOR, and handoff §10.4.
- **Phase-0b bundle** (WSL path) inspected for listing, sizes, `campaign_summary.json` and `seed_ledger.json` only.
- **Nothing changed or run.** No file was created, edited or deleted. No state-changing git command was run. No simulation, fit or test was run.

## Changes vs Phase 0b and why

| Item | Phase 0b | G35-B | Reason |
|---|---|---|---|
| Purpose / authority | V1.3 gate (redesign cycle 1) | Design study under G35-B; not a gate | §12.1 cap spent; informs a later owner decision only |
| Arms | P0-1, P0-2A, P0-2B, P0-3 | B, (i), (ii), (iii): recovery only | The question is recoverability. P0-2/P0-3 passed twice. |
| Targets | 5 | 10, shared across arms | Binomial operating characteristic (§7.3); thresholds kept as fractions |
| Thresholds | 4/5, 3/5, ≤ 1/5, float/absolute in code | 8/10, 6/10, ≤ 2/10, integer arithmetic | Same fractions; exact endpoints |
| Candidate replicates | 3 | 3 (B, ii, iii); 12 in four batches (i) | 1/√R precision argument; independent batches at fixed tuples |
| Latent window | 30 d | 30 d; H d in (ii) by a pre-freeze probe rule | Cross the peak (diagnostic Q5) |
| Objective | √-distance, 2 channels | Same; arm (iii) adds one serosurvey datum at equal per-datum weight | Anchor on infection scale without reweighting existing channels |
| Seeds | 62/72/63/73 series | 81–83, 91–95 series; pre-freeze build check and reserve rule | Fresh, disjoint, buildable |
| Harness | `phase0_campaign.py` profiles | New standalone module; `phase0_campaign.py` untouched | Hard-coded 3/30/34/≤1 and two-profile disjointness |
| Workload | 1,334 cells / 107 latent / 4,007 transforms / 8 builds | 2,500 / 395 / 9,395 / 22 (+ 85 serosurvey samples) | Exact cost of the declared arms |

## Decisions the model owner must explicitly accept

1. G35-B is a design study whose outcomes authorize nothing beyond input to a later Steven decision. Any PASS needs a fresh-seed confirmatory predeclaration before reliance (§1, §7.4).
2. P0-2, P0-3 and G29 are excluded from this study (§2).
3. Ten targets per arm, with the Phase-0b thresholds kept as fractions and evaluated in integer arithmetic. The alternative is to keep 5 targets (§7.3).
4. Arm (i): R = 12 as four independent batches of 3, with batch A = B's candidates; nested 3/6/12; and the listed descriptives (§4.1, §7.2).
5. Arm (ii):
   - (a) the probe design and rule fixing H (10% decline mark, +8-day margin, multiple of 7, 35 ≤ H ≤ 91);
   - (b) the stop rule;
   - (c) the prefix-identity labelling consequence;
   - (d) H is filled mechanically before freezing (§4.2).
6. Arm (iii) synthetic campaign assumptions: survey on day 29, zero lag, sensitivity 1 and specificity 1, n = 400 by the stated criterion (including the 25% floor), SRS without replacement with seed-only sampling, and the Anscombe transform at weight 1/(2T) (§5.2, §6).
7. The seed table and the pre-freeze replacement rule. Fallback-built populations count as builds, not failures (§8).
8. The exact workload caps; wall time and bundle size as disclosures only (§9).
9. A standalone harness module; `phase0_campaign.py` and the protected modules stay unchanged; any need to change them is a stop (§11).
10. The three pre-declared primary comparisons, the readings table and the multiplicity handling (§7.2, §7.4).
11. One campaign. Phase-0b-style VOID and FAIL rules. No second campaign without Steven (§12).

## Full flat seed list for the pre-check

**Process (build) seeds. Build-check all 38 on `cf45153`, mode `ci`:**
81001, 81002, 81003, 81004, 81005, 81006, 82001, 82002, 82003, 82004, 82005, 82006, 82007, 82008, 82009, 82010, 82011, 82012, 82013, 82014, 82015, 83001, 83002, 83003, 83004, 83005, 83006, 83007, 83008, 83009, 83010, 83011, 83012, 83013, 83014, 83015, 83016, 83017

**Non-building seeds (disjointness check only; 38):**
91001, 91002, 91003, 92001, 92002, 92003, 92004, 92005, 92006, 92007, 92008, 92009, 92010, 93001, 93002, 93003, 93004, 93005, 93006, 93007, 93008, 93009, 93010, 93011, 93012, 94001, 94002, 94003, 94004, 94005, 94006, 94007, 94008, 94009, 94010, 95001, 95002, 95003

## Model-owner acceptance (2026-10-22)

MODEL-OWNER RULING (G35-B): ACCEPT WITH AMENDMENTS. Fable 5.1 model-owner subagent, under Steven's 2026-10-22 delegation. Ruling: `docs/research/v1_3/2026-10-22-g35b-owner-ruling-ACCEPTED.md` (sha256 `f84738a9594312f3371f4bb469c5cfaafed265dc5d233ee34f1f0be564d99643`, committed at `2cfb9f6d249c64fe78e0716a6a6ff6208ac681b5`). Amendments A1–A11 appear verbatim at their named locations above. The ruling's conditions on the pre-freeze actions bind, quoted verbatim:

1. **Order.** Ruling commit (A11) → build pre-check → horizon probe → frozen text. Every step is a trail row through `fm.sh log`; the probe row cites the ruling commit SHA and SHA-256.
2. **Build pre-check** records, per process seed: build outcome, exception class if any, `private_assignment_residual_fallback` and `destination_reassignment_fallback` presence, and M2/M3/M4 logical hashes. Replacement follows §8 verbatim; the record lists every exclusion and its replacement. Reserve exhaustion returns the draft to the owner, not a widened pool.
3. **Probe** runs only the truth cell on seeds `81001–81003` with observation seeds `91001–91003`, at 30 and 91 days, and records only p_s, e_s, H, the prefix-identity result (identity/not identity, with the two hash pairs compared), and `runtime_seconds` per call. No loss, profile, candidate cell or alternative H is computed or written. If the stop rule fires, the record says so and the draft returns NEEDS OWNER INPUT; H is never chosen by hand.
4. **Host disk** free space ≥ 5 GB checked and logged before the probe (2026-09-02 lesson).
5. **Frozen text** contains the final seeds, exclusions, hashes, H, the prefix-identity result and the A1–A11 text verbatim; its SHA-256 is fixed in the config and in an independent module constant (Phase-0b §12.5 pattern). Any later inconsistency is a stop resolved only by a filed clarification ruling that changes no grid, threshold, seed, objective, level or predicate.
6. **Vocabulary** from this point: "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: not run" in every state file until a campaign completes (A9). G34 stays STOPPED throughout.

## Freeze record (director, mechanical)

- **Source draft:** `docs/research/v1_3/2026-10-22-g35b-design-opus-DRAFT.md` (sha256 `29492b3d161fa7f0e9dbc5ec32f146f530792b3fafdb655d98c03b945176a3b2`).
- **Director edits, none of them substantive:**
  - the title and status line now say FROZEN;
  - the draft's report line and filing comment are removed;
  - A1–A11 are applied verbatim;
  - the §4.2 and §8 frozen-value blocks are filled from the filed probe and pre-check records;
  - this acceptance and freeze record is appended.
- **Unchanged:** every grid, truth, tolerance, threshold, objective, seed, level and predicate in the draft.
- **Section cross-references are left as the draft wrote them.** Pointers to "§17" mean the flat seed list at the end. Pointers to "§16" for the owner ruling mean the acceptance section above.
- **The §16 attestation** is the consultant's, as of the draft.
- **Order followed** (ruling condition 1): ruling commit `2cfb9f6`, then build pre-check, then horizon probe, then this frozen text.
- **Disclosed deviation:** one builds-only pre-check ran before the ruling commit. It is superseded and unused, and its hashes were identical to the in-order run's (trail row `g35b-owner-ruling`).
- **Implementation obligation (ruling condition 5):** this file's SHA-256, as recorded in the trail at the freeze commit, is fixed in the G35-B config and in an independent module constant by unit U1.
- **Status phrase:** "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: not run". G34 stays STOPPED.
