# Jersey Outbreak Simulator — Scientific Roadmap

*Derived from the independent scientific model audit of the frozen `jos-v1.0.0` release
(commit `9e9ce3abc4201cd8303c723015462d21ca237800`). Every item below is justified by a specific audit
finding, cited by identifier. Items not traceable to a finding have been excluded.*

*Companion documents: [`JOS_V1_SCIENTIFIC_AUDIT.md`](JOS_V1_SCIENTIFIC_AUDIT.md) ·
[`JOS_V1_SCIENTIFIC_TECHNICAL_REPORT.md`](JOS_V1_SCIENTIFIC_TECHNICAL_REPORT.md)*

---

## How this roadmap is organised

Four tiers, ordered by what each changes about the platform's scientific standing rather than by
implementation effort:

| Tier | What it changes | Precondition |
|---|---|---|
| **V1.1 — Scientific hardening** | Removes disclosure requirements that currently attach to specific outputs; makes the verification surface honest | None |
| **V1.x — Empirical calibration** | Anchors currently-assumed quantities to evidence; makes uncertainty reportable | V1.1 complete for the affected components |
| **V2 — Validated disease-specific modelling** | Changes the class of claim available, from experiment to partially validated inference | V1.x, plus registration of Jersey epidemiological data |
| **Research extensions** | Opens questions Jersey is specifically suited to answer | V2 for anything policy-adjacent |

Each item carries the audit findings that justify it and an acceptance criterion — the observable that
would establish the item is done. Effort labels are indicative only.

---

## V1.1 — Scientific hardening

The purpose of this tier is to remove limitations that currently require a disclosure every time a
particular output is presented. None of these items requires new data.

### 1.1 High-priority corrections

**H1. Exclude care-home residents from the general community route.**
*Findings:* `N-10`, and interacting with `POP-10`, `POP-09`, `STA-05`.
Care-home residents currently participate in `community_indoor` and `community_outdoor` at free-living
rates, which understates the epidemiological distinctness of the model's most severity-relevant setting
and overstates its exposure. This is a route-membership filter, not a redesign, and it is the single
highest-leverage correction identified in the audit.
*Acceptance:* zero community-route edges incident on communal-establishment residents; a diagnostic
reporting community participation by residence type; a regression test at full mode.
*Effort:* low.

**H2. Constrain the symptom-onset anchor to the disease timeline.**
*Findings:* `O-02`, interacting with `D-02`, `I-01`, `I-02`.
Symptom onset is currently `infection_date + symptom_onset_delay` with no requirement that it fall after
the latent period; in the shipped observation configuration both onset and detection delays are zero
while the latent period is two days, so detection-triggered isolation acts before the case is infectious.
Sample onset relative to `ti_infected`, extend the chronology check from "onset not before infection" to
"onset not before end of latent period", and ship a demonstration configuration with a positive onset
delay.
*Acceptance:* `chronology_violations` detects a configuration in which onset precedes infectiousness; the
shipped demonstration configuration has a positive onset delay; the isolation scenarios are re-run and the
change in effect size is recorded.
*Effort:* low. **This should precede any further presentation of the isolation or quarantine scenarios.**

**H3. Introduce individual-level contact-rate heterogeneity.**
*Findings:* `N-02`, interacting with `D-01`, `E-01`.
Add a persistent per-agent activity multiplier, drawn once at population generation and applied to
degree or participation probability on the pooled routes (community, workplace transient, school
cross-class, bus). Expose the dispersion as a declared parameter with a documented default.
*Acceptance:* the realised distribution of secondary cases per index case is reported as a diagnostic and
exhibits overdispersion at the configured dispersion; extinction probability from a single index case is
reported and responds to the parameter.
*Effort:* medium. Together with H4 this is what would let JOS speak to superspreading, extinction
probability and outbreak-size variance — the quantities that matter most in a population of Jersey's
size.

**H4. Replace deterministic stage durations with distributions.**
*Findings:* `D-01`.
Latent, infectious and immunity durations are all `ss.constant`. Replace with gamma or lognormal
distributions of the same mean, exposed as parameters, and report the realised generation-interval
distribution as a run diagnostic.
*Acceptance:* the realised generation-interval distribution appears in diagnostics with a non-zero
coefficient of variation; peak timing and height are compared against the constant-duration baseline and
the difference recorded.
*Effort:* low. The literature basis is direct (Lloyd 2001; Wearing et al. 2005; Krylova and Earn 2013).

**H5. Make adherence a per-person trait.**
*Findings:* `I-01`.
Remove `route_id` from the adherence key so one draw per (intervention, agent) governs all routes, and
remove the detection date from the acceptance key so acceptance is a stable personal characteristic.
Expose route-level variation as a separate explicit parameter if wanted.
*Acceptance:* at adherence *a*, the realised fraction of fully non-adherent targeted agents equals
1 − *a* within Monte Carlo error; intervention effect sizes are re-run and the change recorded.
*Effort:* low.

### 1.2 Structural defects that currently invalidate named outputs

**S1. Fix the school-type age collapse.** *Finding:* `STR-01`.
Replace the age-ascending pupil selection with an age-stratified allocation: for each school type derive a
target age profile and allocate pupils to types within each single year of age by largest remainder, so
all five types span their proper year ranges. Add a diagnostic on the age distribution **within** each
type, not only on range validity.
*Acceptance:* every school type spans at least its documented year range; the within-type age
distribution appears in diagnostics; school-type-resolved outputs become quotable.

**S2. Give schools a geography, or stop emitting one.** *Finding:* `STR-02`.
Either implement parish-weighted catchments (allocate school places to parishes by resident school-age
population, with distance or adjacency weighting), or set `school_parish` to an explicitly synthetic
label and disclose that schools have no geography. The current field invites exactly the misreading it
cannot support, and it propagates to all 1,972 school staff.
*Acceptance:* `school_parish` is either non-degenerate or explicitly labelled non-geographic; the
household-to-school parish correlation is reported.

**S3. Correct the parish no-car allocation.** *Finding:* `POP-07`.
Weight the residual allocation by `share × household count` rather than by bare share, so the
implementation matches its own documented definition.
*Acceptance:* the correlation between generated parish no-car rate and the intended weight is positive;
the two observed anchors (16% island-wide, 30% St Helier) continue to reconcile exactly.

**S4. Apply resident absences at runtime.** *Finding:* `T-11`.
Recompute presence each day from the absence intervals — the correct helper already exists and is used
only at construction — and assert that the runtime away-set size equals the planned figure for every day.
Add a test with an absence starting strictly after the run start date.
*Acceptance:* `daily_travel_population.resident_away` and
`daily_travel_intervention_state.resident_away` agree for every day of every run; a regression test covers
the in-horizon case.

**S5. Key travel runtime maps on trip identity.** *Finding:* `T-12`.
Replace person-keyed runtime maps with trip-keyed maps (the trip identifier is already unique) and allow
multiple episodes per resident per horizon, or enforce at generation time that each resident receives at
most one return episode and report the resulting censoring.
*Acceptance:* a regression test with two returns for one resident inside the horizon passes with and
without arrival testing enabled.

### 1.3 Verification and diagnostics fidelity

**V1. Compute the three asserted diagnostics from realised artifacts.** *Findings:* `X-01`, `N-25`,
`N-15`, `POP-13`.
The occupational double-counting audit currently tests staff against the collection from which their rows
were removed, so its zero is structurally guaranteed; `repeated_edge_rate` is set to 1.0 without
measurement for routes declared "fixed", including a workplace route whose executed edge set varies daily
with attendance; and a declared housing-proportion tolerance is never applied to anything. Adopt a
convention that any diagnostic whose value is structurally fixed is labelled an invariant rather than a
measurement.
*Acceptance:* each of the three is computed from the realised artifact; deliberately introducing the
corresponding defect makes the diagnostic non-zero.

**V2. Execute and archive a full-population, full-wave baseline ensemble.** *Finding:* `V-03`.
No full-population, full-horizon epidemic has ever been run. Archive a baseline with face-validity
diagnostics: peak timing and height, final size, route shares reported with the candidate-count
distribution, realised generation interval, per-agent daily contact-opportunity counts by age band, and
runtime and memory profile.
*Acceptance:* an archived, verified artifact covering a complete epidemic wave at full population, with
the diagnostics above recorded and the runtime and memory cost documented.
*Effort:* medium (compute-bound). **This is the most important missing piece of evidence in the platform**
and a precondition for every claim about behaviour at scale.

**V3. Add full-mode regression tests for institutional structure.** *Findings:* `X-02`, `TEST-01`,
`POP-11`.
Every integration test runs at 3,000 agents, where no nursing home, detention setting, children's home or
homeless hostel exists and there is exactly one school per type — so the nursing staffing branch and
multi-school allocation are never exercised end to end. Add a full-mode (or a scaled mode chosen so every
communal category survives) test asserting the institutional inventory, the nurse-role count and the
per-school-type age composition.
*Acceptance:* the full-scale figures currently recorded narratively in `docs/progress.md` become enforced
contracts.

**V4. Test calendar-to-timestep alignment inside a running simulation.** *Finding:* `N-26`.
The entire calendar apparatus acts through a single date resolution inside the dynamic-network refresh,
and no test asserts that the date a network reads corresponds to the timestep whose transmission is about
to be evaluated.
*Acceptance:* a test comparing live network edges against the route snapshot for the expected date, across
a term boundary and a weekend boundary.

### 1.4 Output-semantics and provenance corrections

**O1. Rename `attack_rate`.** *Finding:* `D-04`. The column is cumulative infection episodes per capita,
can exceed one under waning, and in travel runs its denominator includes visitor slots. Rename to
`cumulative_incidence_per_capita`, add a distinct `ever_infected_fraction` computed from unique agent
identities, and document the denominator in the column metadata.

**O2. Disambiguate mixed compartment columns in travel runs.** *Finding:* `T-25`. Rename the headline
compartment columns to `present_*` or add resident-only equivalents, and document that present prevalence
is a whole-present-population quantity.

**O3. Promote the travel route edge weights into the provenance surface.** *Findings:* `T-20`, `P-02`.
Nine hard-coded float literals act as direct per-edge beta multipliers while appearing in neither
provenance table. Promote them to named configuration fields with provenance entries, and pass the real
weight into the exported route metadata (currently a constant 0.35 for all seven travel routes).

**O4. Close the remaining provenance gaps.** *Findings:* `P-02`, `N-18`, `T-08`, `POP-06`, `STR-06`.
Verify calendar dates against the named snapshot rather than keying provenance on the configured year;
empty the source list for invented seasonality shapes or add a distinct "inspired by" field; read the
housing attribute weights from the canonical table that already holds the same values; and either consume
or explicitly retire the two ingested-but-unused evidence items.

**O5. Add a distributional summary of paired scenario differences.** *Finding:* `E-03`.
Emit the median and quantiles of the per-seed difference alongside the per-seed rows, and quote the
coupling caveat verbatim wherever a paired difference is presented.

**O6. Guard small-ensemble quantiles.** *Finding:* `E-02`.
Warn or refuse when the replicate count is too small for the requested quantiles, and default to an
interquartile summary for small ensembles.

**O7. Report the realised rather than the intended employment propensity.** *Finding:* `STR-05`.
The diagnostics currently publish selection weights that differ substantially from the realised rates
(65–74: 31.1% realised against 0.18 relative weight). Report realised rates alongside the weights, since
only the realised rates are the model's behaviour.

**O8. Report travel scaling context.** *Findings:* `T-03`, `T-13`.
Add movements per resident-year to travel diagnostics, and report the realised visitor-to-resident
endpoint ratio per route per day, so the two scaling distortions are visible in every travel artifact.

---

## V1.x — Empirical calibration

This tier anchors currently-assumed quantities and makes uncertainty reportable. It requires data
acquisition but not epidemiological data.

### 2.1 Contact structure

**C1. Demonstrate contact-structure plausibility against an empirical contact survey.**
*Findings:* audit Section 6.4; `N-02`, `N-22`.
Compute the per-agent daily contact-opportunity distribution by age band from the artifacts and compare
its magnitude and age pattern against POLYMOD (Mossong et al. 2008) or CoMix (Jarvis et al. 2020). This is
not a calibration; it is a check that the structure sits in the right region. JOS v1 currently makes no
such demonstration, and either outcome is informative.
*Acceptance:* a published comparison figure and table; if the comparison is unfavourable, a documented
revision of the route parameters.

**C2. Collapse the redundant transmission parameterisation and set the indoor:outdoor ratio from
evidence.** *Findings:* `N-22`, `D-09`.
The M4 relative weight and the M5 route multiplier are two free multiplicative parameters over the same
product and are not separately identifiable. Reduce to a single per-route intensity. Separately, the
indoor:outdoor ratio of about 1.9 is low relative to the direction of the outdoor-transmission literature
(Bulfone et al. 2021); set it explicitly with a cited basis and a sensitivity range.
*Acceptance:* one identifiable intensity parameter per route; the indoor:outdoor ratio carries a
documented basis and a declared sensitivity range.

**C3. Replace the structural community mixing matrix with a documented basis.** *Finding:* `N-21`.
The broad-age community mixing matrix is currently a structural assumption with no external referent.
Either derive it from a published contact matrix, adjusting for the settings JOS represents separately,
or retain it as an assumption with an explicit sensitivity axis.

### 2.2 Population distributions

**P1. Fit household size and within-household age structure.** *Findings:* `POP-04`, `POP-05`.
Ingest the census persons-per-household distribution and fit the extra-member allocation to it by largest
remainder, as household types already are. Fit parametric age-gap distributions (for example truncated
normals on the couple gap and the parent-child gap) and use rejection sampling against those rather than
only against the bounds. The existing diagnostics already measure the right quantities, so target
distributions can be added as reconciliation checks.

**P2. Give care homes a resident age profile and a size distribution.** *Findings:* `POP-10`, `POP-09`.
Replace the linear age ramp with a profile from a registered source, or an explicitly labelled scenario
profile concentrated at 80+ exposed as a configurable parameter with a sensitivity range. Impose a
plausible establishment size distribution — for example fitted to the public Care Commission register of
registered bed numbers — subject to the observed establishment and resident totals.
*Acceptance:* age-stratified care-home outcomes and institutional outbreak-size tails become quotable.

**P3. Give workplaces a realistic size distribution and represent the hospital.** *Finding:* `STR-07`.
Draw within-band sizes from a right-skewed distribution subject to the exact band job totals, give the
50+ band a realistic tail using publicly known large-employer headcounts, and represent the hospital as a
named large non-private workplace with a distinct healthcare-worker route rather than folding it into
25-employee units.
*Acceptance:* workplace outbreak-size tails and healthcare-worker transmission become quotable.

**P4. Use the already-ingested sector-by-size cross-tab.** *Finding:* `STR-06`.
Allocate workplaces to (sector, band) cells by largest remainder against the published cross-tab, letting
the +40-undertaking rounding discrepancy be absorbed as an explicit residual. The data is already
ingested; only the allocator needs changing.

**P5. Rake worker selection to age and sex marginals.** *Finding:* `STR-05`.
Ingest the labour-market economic-activity-by-age table from the release already registered, and rake
worker selection to age × sex marginals rather than using unnormalised propensities.

**P6. Allocate remote working by sector and make it partial.** *Findings:* `STR-09`, `I-05`.
Allocate work-from-home using sector-specific remote-working shares rather than uniformly at random,
expose the overall level as a scenario parameter with a sensitivity range around a post-pandemic value
rather than fixing it at the 2021 census figure, and allow non-binary `remote_days_per_week`.

**P7. Extend institutional staffing.** *Findings:* `STA-05`, `STA-06`, `STA-02`, `STA-03`.
Add staffing rules for detention, children's homes and other medical settings; add an explicitly
parameterised share of care staff holding assignments at two homes so the cross-facility bridge exists
and can be intervened on (the diagnostic already reports it as zero); make the teacher-to-class binding a
covering assignment and give secondary teachers membership of several classes; justify or replace the
FTE-to-endpoint ratio; and either restrict the CYPES-derived endpoints to the schools that control
covers, or state the resulting ratio distortion numerically.

**P8. Add a further-education setting.** *Finding:* `STR-04`.
Register a further-education enrolment control and add a tertiary setting for the 16–18 band, or state
explicitly that this population is out of scope.

### 2.3 Travel and visitor evidence

**T1. Replace the invented seasonality shape with the observed monthly series.** *Findings:* `T-08`,
`T-05`, `T-06`.
Register the Ports of Jersey monthly passenger series. Separately, normalise the seasonality profile in
the explicit-schedule path as well (or refuse the combination of a non-neutral profile with an explicit
schedule), validate normalised rather than raw multipliers against the declared bounds, and collapse the
inert normalisation choice to the single implemented option.
*Effort:* low, and immediately available.

**T2. Tie stream scale to population scale.** *Finding:* `T-03`.
Default `stream_scale` to `actual_population / 104_540` so movements per resident-year is preserved, or
refuse to run until the user acknowledges the ratio. Raise the materialised-episode limit or generate
episodes lazily by date so the self-consistent full-scale configuration is usable beyond ~79 days
(`T-04`).

**T3. Make visitor-to-resident mixing scale with volume.** *Finding:* `T-13`.
Size the resident pool as a rate — per participating visitor, with a documented cap — rather than as an
absolute count per parish-day, and draw terminal residents from the terminal's own parish.
*Acceptance:* the resident-facing endpoint count responds to arrival volume; arrival-volume results become
interpretable as a dose-response.

**T4. Make arrival-test sensitivity incubation-dependent.** *Findings:* `T-14`, `T-15`.
Make sensitivity a function of time since exposure using the existing transition timers — near zero in the
first days post-exposure, peaking near symptom onset — and draw the returning-resident acquisition time
uniformly over the absence interval rather than at the return timestep, setting the arrival state
accordingly. Report both results returned and results actionable (`T-18`).
*Acceptance:* modelled border screening exhibits the incubation-window failure mode; border-measure
results are no longer an upper bound by construction.

**T5. Anchor or bound visitor behaviour.** *Findings:* `T-19`, `T-20`, `T-21`, `T-23`, `T-24`.
Draw accommodation, stay duration and optionally arrival state at party level so parties are co-located;
register a visitor age-sex profile or mark visitor age-stratified output as non-meaningful; register an
accommodation-stock source by parish and make the unit count scale with occupancy; and always report
visitor results as a function of arrival prevalence rather than at a single value.

**T6. Separate importation channels cleanly.** *Finding:* `T-16`.
Restrict generic exogenous imports to residents when explicit travel is active — currently they can select
active visitor slots — and add a diagnostic reporting importation per channel with an explicit warning
when both channels are enabled.

**T7. Extend traveller vaccination to returning residents.** *Finding:* `T-28`.
Or rename the control to make its visitor-only scope unambiguous.

### 2.4 Uncertainty quantification

**U1. Add parameter-uncertainty propagation.** *Finding:* `E-01`.
Introduce a parameter-ensemble layer drawing from declared prior ranges over transmission intensity,
stage durations, route intensities and ascertainment, and report a variance decomposition separating
stochastic from parametric contributions.
*Acceptance:* an interval that can honestly be described as an uncertainty range; a variance decomposition
reported alongside it. **Until this exists, no JOS interval should be presented as an uncertainty range.**

**U2. Global sensitivity analysis.** *Findings:* `E-01`, `C-02`, and the many unanchored structural
parameters.
A variance-based global sensitivity analysis over the declared parameter space, identifying which
assumptions actually drive which outputs. This would also tell the project where the remaining
calibration effort is best spent.

**U3. Move to count-appropriate likelihoods with intervals.** *Finding:* `C-03`.
Replace the unweighted sum of squares with a Poisson or negative-binomial likelihood, report intervals
rather than points, and add a mis-specification arm in which truth is generated under a different
structure than the fitted model.

---

## V2 — Validated disease-specific modelling

This tier changes the class of claim available. It requires Jersey epidemiological data and should not be
attempted before V1.1 and the relevant parts of V1.x are complete, because fitting an unhardened
structure would absorb structural error into the parameters.

### 3.1 Register Jersey epidemiological evidence

**E1. Register a Jersey surveillance series.** *Finding:* `V-02`.
None of the 22 registered sources is epidemiological. Candidate targets, in descending value:

- **Jersey COVID-19 surveillance (2020–2022)** — case notifications with testing volumes, plus the
  documented border-testing regime. The highest-value target because it exercises the travel, observation
  and intervention layers simultaneously, and because Jersey's two-port boundary makes importation
  unusually observable.
- **Seroprevalence surveys**, if any were conducted — these constrain cumulative infection independently
  of ascertainment and so break part of the ascertainment-transmissibility confounding.
- **Influenza and RSV sentinel surveillance** — multi-season data supporting seasonality and recurrence
  tests, and the natural check on the waning mechanism.
- **Care-home outbreak records** — institution-level outbreak sizes, the direct test of the closed-setting
  structure and the natural check on `POP-09`, `POP-10` and `N-10`.
- **School absence data** — an indirect but independent check on school-route intensity and term-time
  gating.

All should be registered through the existing pipeline with the same provenance discipline, including
checksummed snapshots and evidence classification.

### 3.2 Calibration and retrospective validation

**E2. Retrospective reconstruction of a known Jersey outbreak.** *Findings:* `V-02`, `C-02`.
Fit only ascertainment and a single transmission intensity, holding the hardened structure fixed, and
report how much of the observed epidemic shape the synthetic structure reproduces **without** further
tuning. The scientific interest is in the residual: what the structure gets right unaided.
*Acceptance:* a documented reconstruction with a pre-specified fitting protocol, a held-out period, and an
explicit statement of what was and was not fitted.

**E3. Likelihood-free or Bayesian calibration.** *Findings:* `C-02`, `C-03`.
Adopt a scheme returning a posterior over the reduced identifiable parameter set — approximate Bayesian
computation, sequential Monte Carlo, or history matching — rather than a point. Hazelbag et al. (2020)
found that a minority of individual-based modelling studies used reproducible, non-subjective calibration
methods; JOS already has the reproducibility infrastructure such a scheme needs.
*Acceptance:* a posterior sample, with prior-to-posterior contraction reported per parameter, and
predictive intervals that include parameter uncertainty.

**E4. Out-of-sample structural validation.** *Finding:* `V-02`.
Hold out a period or a setting entirely and test whether structural conclusions — the ordering of route
contributions, the relative ranking of interventions — are reproduced without refitting. For a mechanistic
model this is the more meaningful test than curve fit.

### 3.3 Disease-specific parameterisation

**E5. Named-pathogen parameter sets.** *Findings:* `D-01`, `D-02`, `D-07`.
Add registered, literature-referenced parameter sets for specific pathogens — introducing a
`literature_prior` evidence class, which the taxonomy currently lacks — with stage-duration
distributions, presymptomatic and asymptomatic infectiousness, and age-dependent susceptibility. Keep the
generic set as the default so pathogen neutrality remains available.

**E6. Severity, hospitalisation and healthcare capacity.** *Finding:* `D-07`.
Add an age- and risk-stratified severity pathway and a healthcare-capacity layer. This is the natural
prerequisite for any burden question, and it is what would make the care-sector structure scientifically
consequential rather than merely structurally present. It depends on `POP-10` being corrected first: a
severity pathway applied to the current care-home age profile would systematically understate care-home
consequence.

**E7. Partial immunity and vaccination history.** *Findings:* `D-03`, `I-04`.
Add partial protection on waning rather than return to full susceptibility, boosting, and an initial
immunity profile representing prior infection and vaccination history. Offer vaccination irrespective of
infection state, reporting doses administered separately from doses conferring protection.

### 3.4 Behavioural realism

**E8. Behavioural substitution and adherence dynamics.** *Findings:* `I-02`, `T-27`.
Add an explicit compensatory-contact parameter — a fraction of suppressed contact reappearing on named
routes — allow selected multipliers above one behind a transmission-probability guard, and add adherence
fatigue as a time-varying process. Until this exists, measured intervention benefit can never be adverse,
which is a structural constraint rather than a finding about interventions.

---

## Research extensions

Questions that a hardened, partially validated JOS would be well placed to address, several of which are
distinctively suited to Jersey. Each is justified by an audit finding about what the platform is or could
be, not by speculation about what would be interesting.

**R1. Persistence and stochastic extinction in the critical-community-size regime.**
*Basis:* audit Section 15.3; `N-02`, `D-01`, `V-03`.
At about 104,540 residents Jersey sits where stochastic fadeout and reintroduction, rather than
deterministic endemic dynamics, govern persistence (Bartlett 1957; Keeling and Grenfell 1997). With
contact and duration heterogeneity introduced (H3, H4) and long-horizon runs feasible (V2, and lifting the
calendar cap `N-19`), JOS could address the interaction of importation pressure, contact heterogeneity and
population size in determining persistence. **This is the platform's most distinctive potential
contribution**, because it requires exactly what JOS has — an explicit, port-anchored, provenance-tracked
importation mechanism — in a setting where importation is close to fully observable.

**R2. Optimal allocation of finite border-testing capacity.**
*Basis:* `T-14`, `T-17`, `T-19`.
Once test sensitivity is incubation-dependent (T4) and arrival prevalence is treated as an explicit
uncertain input, the question of how to allocate a fixed testing budget across entry modes, turnaround
times and quarantine durations becomes well posed. The lifecycle machinery for it already exists and is
correctly implemented.

**R3. Care-sector protection under a corrected care structure.**
*Basis:* `N-10`, `POP-10`, `POP-09`, `STA-05`.
Four corrections (H1, P2, P7) would make the care sector epidemiologically realistic: residents isolated
from free-living community mixing, an appropriate age profile, a size distribution, and a cross-facility
staff bridge. The value of staff testing, visitor restriction, staff-movement restriction and vaccination
prioritisation could then be assessed meaningfully — and with a severity pathway (E6), in terms of
consequence rather than infections alone.

**R4. Repeated importation and reintroduction dynamics.**
*Basis:* `T-03`, `T-13`, `T-16`.
With scaling self-consistency (T2) and volume-responsive mixing (T3), the relationship between arrival
volume, arrival prevalence and the frequency and size of resulting resident outbreak clusters becomes
interpretable as a dose-response rather than as a saturating artefact.

**R5. Structural uncertainty through independent model comparison.**
*Basis:* `E-01`.
Structural uncertainty cannot be quantified from within a single model. Comparison against an
independently constructed model of the same population — even a well-specified age-structured
compartmental model — would bound how much of JOS's output is driven by its structural choices.

**R6. Multi-strain and variant dynamics.**
*Basis:* `D-03`, and the modular disease boundary.
Cross-immunity, strain replacement and immune escape in a small, importation-driven population. Depends
on partial immunity (E7). Jersey's boundary observability makes strain introduction unusually traceable.

**R7. Contact-structure inference from surveillance data.**
*Basis:* `C-02`, `N-22`.
Given a reduced identifiable parameterisation (C2) and a Jersey surveillance series (E1), the relative
route intensities themselves become estimable rather than assumed — inverting the current situation, in
which they are the model's least anchored and most consequential parameters.

**R8. An ODD-conformant model description for publication.**
*Basis:* technical report Section 22.
The elements required by the ODD protocol (Grimm et al. 2020) are all present in the technical report but
not under its headings. A dedicated ODD appendix would make the model description conformant for journal
submission, and the provenance apparatus already supplies most of what such an appendix requires.

---

## Dependency summary

```
V1.1 hardening
  H1 care/community exclusion ────────────┐
  H2 onset anchor ────────────────────────┤
  H3 contact heterogeneity ───┐           │
  H4 duration distributions ──┤           │
  H5 per-person adherence ────┤           │
  S1..S5 structural defects ──┤           │
  V1..V4 verification ────────┤           │
  O1..O8 semantics/provenance ┘           │
         │                                │
         v                                v
V1.x calibration                    R3 care-sector protection
  C1 contact-survey check                 (also needs P2, P7, E6)
  C2 identifiable intensity ──┐
  P1..P8 population fits ─────┤
  T1..T7 travel evidence ─────┤
  U1..U3 uncertainty ─────────┤
         │                    │
         v                    v
V2 validation           R1 persistence / CCS      R2 border testing
  E1 register Jersey data     (needs H3, H4, V2,        (needs T4, U1)
  E2 retrospective fit         calendar cap lifted)
  E3 Bayesian calibration
  E4 out-of-sample test
  E5..E8 disease specificity
         │
         v
R4..R7 research extensions
```

**The three items that unblock the most downstream work:** `H2` (onset anchor — every
detection-triggered result depends on it), `V2` (full-wave baseline — every claim about behaviour at scale
depends on it), and `E1` (register Jersey epidemiological data — every validation claim depends on it).

---

## What this roadmap deliberately excludes

Items that might appear in a generic roadmap but are **not** justified by the audit, and are therefore
omitted:

- **Sub-parish or coordinate-level geography.** JOS does not claim it, and adding synthetic locations
  without evidence would create a precision the data cannot support — the audit's `POP-12` treats the
  parish resolution as a declared scope boundary, not a defect.
- **Real contact traces or mobility data.** Incompatible with the platform's synthetic-population stance
  and with the privacy posture the repository maintains explicitly.
- **Named-individual or address-level representation.** Explicitly excluded by the project's own
  scientific rules, and correctly so.
- **Forecasting capability as a near-term goal.** Nothing in v1 supports it, and Stages 1–5 of the
  validation roadmap must precede any prospective claim.
- **Performance optimisation as a scientific priority.** Runtime is currently adequate for the analyses
  the platform supports (full-scale network construction about 73 seconds at roughly 0.9 GB), and the one
  place where computation genuinely limits science — the materialised-episode cap and the reference-year
  calendar cap — is addressed directly by T2 and R1 rather than by general optimisation. Parent-artifact
  caching in ensembles is the one exception worth doing, since replicate cost is currently dominated by
  network reconstruction rather than by disease dynamics.

---

*Derived from the independent scientific model audit of `jos-v1.0.0` at commit
`9e9ce3abc4201cd8303c723015462d21ca237800`. This roadmap proposes future work; it does not modify the
frozen release. Finding identifiers refer to
[`JOS_V1_SCIENTIFIC_AUDIT.md`](JOS_V1_SCIENTIFIC_AUDIT.md) Section 18.*
