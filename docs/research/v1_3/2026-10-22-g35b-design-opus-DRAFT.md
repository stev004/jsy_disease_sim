G35-B DESIGN: READY FOR OWNER RULING

<!-- Filed verbatim by the director (Claude Opus 5.5) on 2026-10-22 from the consultant's returned report (HTML entities decoded). Author: Opus 5.5 consultant subagent, read-only, brief sha256 8f02f80dbd8597835fa3d57b103505b9ace7a9eb897ea447df813ef6decf1bcd. Re-routed from gpt-6.1-sol after an OpenAI bio-risk classifier stop (trail row g35b-design-filtered). DRAFT for owner ruling; not frozen. -->

# G35-B synthetic design-study predeclaration (DRAFT for owner ruling, not frozen)

## 1. Status and lineage

**Status:** DRAFT for owner ruling. Nothing in it is frozen. This draft is not a Phase 0c and not a V1.3 gate. Phase 0: FAIL (2026-09-24). Phase 0b: FAIL (2026-09-26). G35-B: not run. Real-data fitting stays STOPPED (G34 A+B). This study was designed **after** both Phase-0 and Phase-0b results were seen, and after the exploratory ridge diagnostic. No outcome of this study changes either FAIL verdict.

**Authority:** G35 was resolved B on 2026-10-22 (`.claude/GATES.md`, Resolved). That resolution authorized a synthetic design study with no real data. The Phase-0b §12.1 cycle cap is spent. This study opens no recovery cycle, and no outcome of it can satisfy the V1.3 plan's Phase-0 gate.

**What any outcome authorizes:** nothing beyond input to a separate, later owner decision by Steven. In particular:
- **No outcome licenses:** real Jersey fitting; a claim that Phase 0 or Phase 0b passed; nominal coverage; Jersey calibration; or named-pathogen validation.
- **A PASS in any arm** is a screening result. A decision may rely on it only after a separately owner-ruled, fresh-seed confirmatory campaign (§7.4).

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
- **Precision.** The candidate mean m = (1/R)Σⱼ√(xⱼ+3/8) has Monte-Carlo standard deviation ∝ 1/√R. Going from 3 to 12 halves the replicate-noise component of every per-date candidate mean, and so of every between-cell loss difference. A two-fold reduction is the smallest step that would plausibly turn a step "comparable to its scatter" into one twice its scatter.
- **Cost.** A four-fold reduction needs R = 48: 1,200 candidate latent calls, about 16× B. That is not modest.
- **Sampling distribution.** Four independent three-replicate batches give four independent draws, per target, of the baseline objective at every fixed tuple and of the re-profiled offset. This is the measurement the diagnostic says the Phase-0b bundle could not make. Four draws are the minimum that yield a range and a median. They are stochastic replicate variation, never an interval.
- **What R = 12 does not do.** It cannot remove a structural trade-off (diagnostic Q5). A FAIL at R = 12 is evidence against H3 as the sole cause. It is not proof of H2.

### 4.2 Arm (ii): longer latent window crossing the peak

**Single change:** the latent run lasts **H** days instead of 30. The observation tail stays 4 days, so the fitter sees T = H + 4 dates.
- Unchanged: population builds, truth, grids, reporting model, the target and candidate process/observation seed streams (B's own), the objective form and R = 3.
- Target trajectories cannot be byte-shared, because the latent runs are longer.

**Choosing H: declared pre-freeze probe.** The model's dynamics bound the outcome only qualitatively. It is a closed 3,000-resident SEIR population with no waning and no imports after the pulse, so the epidemic must end. Its generation interval is fixed by the 2-day latent and 5-day infectious durations. The network's reproduction number is not available analytically. H is therefore fixed by a probe that runs before freezing and is outside every study set:

1. **Probe seeds:** process seeds `81001–81003` (reserves `81004–81006`), observation seeds `91001–91003`, config ID `v13-g35b-probe`. Each probe runs the truth cell (beta 0.08, offset 2, B's scenario) at 30 days and at 91 days.
2. **Peak and decline marks.** On each 91-day run, compute the 7-day trailing sum of latent `new_infections` from `daily_epidemic`. Let p_s be the earliest day index of its maximum. Let e_s be the first day index ≥ p_s at which it is ≤ 10% of that maximum.
3. **Rule:** H = the smallest multiple of 7 that is ≥ max_s(e_s) + 8, and ≥ 35. The 10% mark and the one-week margin are **synthetic campaign assumptions**. They define "crossed the peak and captured the decline" (diagnostic Q5: "growth, peak and decline"). They are not epidemiological claims.
4. **Stop rule.** If any probe has no e_s within 91 days, or ends with fewer than 10 local infections, the draft returns as NEEDS OWNER INPUT. H is never chosen ad hoc.
5. **Prefix-identity check, same probe.** For each probe seed, test whether `transmission_events` with `infection_date ≤ start+29`, and report counts on dates ≤ start+29 under one fixed observation config, are identical between the 30-day and 91-day runs.
   - The code makes this plausible: observation draws are keyed per event (`observation_scheduler.py:61–90`).
   - It is unverified for the Starsim latent RNG.
   - The result is written into the frozen text. If identity holds, arm (ii) shares B's realizations on days 0–29 and differs only by extension. If it fails, the comparison is labelled "seed-stream matched, realization not matched" and proceeds unchanged.
6. **Bounds.** `OutbreakRunConfig.duration_days` allows ≤ 366 (`outbreak_schemas.py:136`). The probe's 91-day cap is a cost bound: about 3× B per latent call. It is a synthetic campaign assumption.

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
- Order residents by SHA-256 of (`process_seed`, `serosurvey_seed`, `serosurvey_config_id`, `"serosurvey"`, `agent_id`) and take the first n.
- The sample depends only on the seed, the config and the population, never on the latent run. Candidate samples are therefore common random numbers across all cells of one process seed.
- k = the number of sampled residents with everInfected = 1.

**Synthetic campaign assumptions, labelled and argued:**

| Assumption | Value | Argument |
|---|---|---|
| Survey timing | one survey at d = start + 29 (2025-02-04), the last latent day | Arm (iii) changes one factor, so the window stays 30 days. The last latent day carries the most cumulative signal and is the latest date at which status is fully simulated. A survey later than the window would be a second factor. |
| Seroconversion lag | 0 days (ever-infected by d) | Any non-zero lag would be an invented biological parameter. Zero is an idealization of the estimand, not a claim about any pathogen. |
| Sensitivity / specificity | 1 / 1 (idealized assay) | Any other values would be invented. Under known, nondifferential misclassification, an imperfect assay carries no more information than a perfect one at the same n. A FAIL here is therefore decisive against this anchor at this n and timing. A PASS is an upper bound: assay-quality sensitivity work is required before any reliance (§14). |
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
- (d) Arm (iii): k/n per target and candidate, z values, and the serosurvey term's share of L at each selected cell.

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
| PASS | PASS | "The fresh-seed baseline recovered at 10 targets: the Phase-0b failure did not replicate. Factor X is not shown to be necessary." |
| PASS | FAIL | "Factor X coincided with loss of recovery." Reported as an anomaly; no causal reading. |
| any | software FAIL | Arm VOID, with no reading. §8 VOID rules apply. |

**Overall reading:**
- **No factor arm PASS and B FAIL:** "None of the three factors, one at a time at the declared levels, made the recovery gate pass. The ridge hypothesis (H2) is not contradicted."
- **One or more factor arms PASS:** each is reported individually with the multiplicity caveat below. No "best factor" is declared.

**Multiplicity.** Three arms raise the chance that at least one passes when no factor matters. Thresholds are not adjusted, because that would require numbers not justified independently of Phase 0b. Instead, a PASS reading is screening evidence only. Any later decision relying on it requires Steven's decision and a new owner-ruled, fresh-seed confirmatory predeclaration.

**What no outcome authorizes:** real-data fitting (G34 stays in force); any change to the Phase-0 or Phase-0b verdict; any claim of calibration, validation or coverage. State files use the exact phrase "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: <PASS|FAIL readings per arm | not run>".

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
- **Per arm:** complete loss surfaces, blind-estimate records with read-back hashes, `g35b_<arm>_recovery.csv` with every per-target predicate value and boundary flag computed by its own code path, and measured counters.
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
   - build pre-check of the §17 process-seed list on `cf45153`, then the replacement rule;
   - horizon probe and prefix-identity check, filed as `docs/runs/*.py.txt` with logs;
   - fill final seeds, hashes, H and the prefix result mechanically into the text;
   - commit ruling and frozen predeclaration via `fm.sh sync` `[skip ci]`; record both SHA-256 digests in the trail.

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
