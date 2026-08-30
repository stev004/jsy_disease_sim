# Jersey Outbreak Simulator v1.0 — Independent Scientific Model Audit

| | |
|---|---|
| **Project** | Jersey Outbreak Simulator (JOS) |
| **Release reviewed** | `jos-v1.0.0` (frozen) |
| **Release commit expected** | `9e9ce3abc4201cd8303c723015462d21ca237800` |
| **Release commit inspected** | `9e9ce3abc4201cd8303c723015462d21ca237800` — `HEAD` at review time, clean worktree |
| **Engine** | Starsim 3.5.2 (version-pinned at the disease boundary) |
| **Review type** | Independent scientific model audit (methods, assumptions, interpretation, claims) |
| **Review date** | 30 August 2026 |
| **Findings** | 26 validated / coherent · 57 minor limitations · 45 major limitations · **0 scientific blockers** |
| **Verdict** | SCIENTIFIC REVIEW: SUITABLE WITH MAJOR DISCLOSURES |

---

## 1. Executive summary

The Jersey Outbreak Simulator v1.0 is a provenance-anchored, agent-based, multi-route contact-network
epidemic simulation and scenario-experimentation platform for Jersey. It constructs a synthetic
population of 104,540 agents — one per estimated resident — from 22 registered official aggregate
sources, layers eleven separable contact routes over it, runs a deliberately pathogen-neutral SEIRS
module through Starsim 3.5.2, and adds observation, intervention, travel, ensemble and calibration
layers, each emitting hash-chained, independently re-verifiable artifacts.

This review examined the scientific model rather than the software. Its central conclusion is that
**JOS v1 is scientifically coherent within its declared scope, and that its declared scope is
unusually honest.** The system repeatedly declines to claim more than it can support: demonstration
disease parameters are labelled `scenario_assumption` and not presented as pathogen estimates;
calibration diagnostics record `real_jersey_data_used: False`; Ports of Jersey annual figures are
labelled "Passenger movements, not unique tourists" in the schema itself; unimplemented mechanisms
(severity, mortality, age-dependent susceptibility) are recorded as deferred rather than filled with
plausible-looking numbers. That discipline is the principal reason this audit records **no scientific
blocker**: a blocker requires a defect that materially invalidates a claim JOS actually makes, and
JOS's claims are bounded tightly enough that its real limitations fall short of that bar.

Three components are strong enough to be described as exemplary. The **provenance and reproducibility
system** (Section 14) is a genuine scientific reproducibility apparatus rather than software
infrastructure: SHA-256-verified source snapshots, per-row evidence classification, refusal to impute
suppressed cells, surfaced source conflicts, and hash-chained artifacts with separate scenario,
latent-outcome and bundle hashes. The **observation layer** (Section 8) structurally prevents the
conflation of infections with reported cases, with chronology checks, latent-incidence conservation and
an enforced online/offline schedule agreement. The **travel identity model** (Section 10) solves a
genuinely hard problem correctly: visitor slots are reused at runtime, yet historical attribution is
bound at event time so no later occupant can inherit an earlier visitor's infection, detection or test
result.

Against that, 45 findings are classified as major limitations that must be disclosed whenever the
corresponding results are interpreted. The most consequential fall into four groups.

1. **Homogeneity of transmission-relevant heterogeneity.** Contact degree is fixed rather than
   distributed (`N-02`), stage durations are deterministic constants (`D-01`), and no individual-level
   contact-rate variation exists anywhere in the model. JOS therefore cannot generate overdispersion
   or superspreading, and its epidemics are sharper, faster and less variable than a model with the
   same means and realistic dispersion.
2. **Structural leakage and degeneracy in a small number of specific places.** Care-home residents
   participate in the general community route at free-living rates (`N-10`); every school resolves to
   `school_parish = 'St Helier'` (`STR-02`); the youngest-first pupil allocation collapses four of five
   school types to two single years of age or fewer (`STR-01`); the parish no-car allocation inverts
   the gradient its own documentation describes (`POP-07`). Each invalidates a specific named output
   rather than the framework.
3. **One-sided intervention semantics.** Every intervention multiplier is bounded in [0, 1] with no
   behavioural substitution (`I-02`), adherence is drawn independently per route rather than per person
   (`I-01`), and in the shipped observation configuration detection precedes infectiousness (`O-02`).
   Modelled intervention benefit is therefore systematically optimistic, in a direction that is
   unambiguous even though its magnitude is unquantified.
4. **Uncertainty and validation.** Ensemble bands quantify stochastic replicate variation over a fixed
   population and a fixed parameter vector only (`E-01`); the transmission parameters are structurally
   non-identifiable from the system's own outputs (`C-02`); no external validation exists and no Jersey
   epidemiological series is registered (`V-02`); and no full-population, full-horizon epidemic has ever
   been executed (`V-03`).

None of these invalidates JOS as a synthetic experimentation framework, and the project's own
documentation anticipates most of them. The audit's operative recommendation is therefore not
remediation before release — the release is frozen and appropriately scoped — but **disclosure
discipline in presentation**, plus a short list of high-leverage scientific corrections identified in
Section 21 and developed in the accompanying roadmap.

---

## 2. Scope and methodology

### 2.1 What was reviewed

This is a review of the scientific model: its purpose, structure, assumptions, parameterisation,
interpretation and claim boundary. Software engineering, packaging, API design, front-end quality and
release process were out of scope except where they carry scientific consequence (for example, the fact
that all integration tests run at a population scale where the institutions that matter do not exist,
`X-02`).

### 2.2 Method

The repository was reconstructed from source rather than from documentation. Every scientific module
was read in full:

- **Data and population:** `data_pipeline.py` (1,222 lines), `population_generator.py` (1,460),
  `population_controls.py`, `population_structure_generator.py` (1,160),
  `population_structure_controls.py`, `staffing_generator.py`, `staffing_evidence.py`.
- **Networks and engine coupling:** `network_generator.py` (1,740), `starsim_adapter.py`,
  `network_schemas.py`, `network_artifacts.py`.
- **Disease, observation, interventions:** `respiratory.py`, `outbreak_runner.py`,
  `observation_scheduler.py`, `observation.py`, `interventions.py`, `intervention_schemas.py`,
  `intervention_analysis.py`.
- **Travel:** `travel.py` (3,147), `travel_schemas.py`, `travel_artifacts.py`.
- **Ensembles, calibration, verification:** `ensemble.py`, `ensemble_schemas.py`, `calibration.py`,
  `scientific_verification.py`, `scientific_hashes.py`, `verification_archive.py`.

Alongside these: all 13 scenario configurations, all 8 travel configurations, both sensitivity
configurations, the disease and observation parameter files, `data/sources.yaml`, the canonical
processed control tables, and the test suite — with particular attention to tests, because a test is
what converts a behaviour from incidental to guaranteed.

Where documentation and implementation disagreed, **the implementation was treated as authoritative and
the discrepancy recorded as a finding.** Thirty such comparisons were recorded across the three
subsystem reviews, of which twenty-nine are genuine divergences and one is a headline documented figure
that was checked end to end and confirmed; they are reported in the relevant sections.

Several quantitative claims in `docs/progress.md` were independently recomputed from the canonical
controls rather than accepted: the full-mode worker and job inventory (58,045 unique workers, 4,063
secondary jobs, 62,108 filled jobs, 270 synthetic non-private workplaces) reproduced exactly; the
travel apportionment reproduced 720,842 air and 196,623 sea movements exactly at `stream_scale = 1`;
the age-sex raking, the communal inventory, the per-school-type age composition, the realised
employment rates by age band and the parish no-car allocation were each reproduced and, in three cases,
found to differ materially from how the corresponding documentation reads.

### 2.3 Constraints observed

No implementation code, configuration, parameter value or existing document was modified. No branch was
merged, no tag altered, no history rewritten. The simulation was not executed; this is a code-reading
and evidence-tracing review, and every quantitative statement below is either copied from a repository
file or recomputed from repository controls, with the derivation named. Discovered issues are documented,
not fixed.

### 2.4 Classification scheme

Findings are classified per the review brief. `SCIENTIFIC BLOCKER` was reserved for a defect materially
invalidating a claim JOS actually makes; a missing feature, an uncertain parameter, a simplifying
assumption, or the absence of external validation was not treated as a blocker where the project's
claims are correspondingly bounded. Findings carrying the prefixes `DP-`, `POP-`, `STR-`, `STA-` and
`TEST-` concern the data and population lane, `N-` the network lane, `T-` the travel lane, and `D-`,
`O-`, `I-`, `E-`, `C-`, `V-`, `P-`, `X-` the disease, observation, intervention, ensemble, calibration,
validation, provenance and cross-cutting reviews respectively.

---

## 3. Model classification

JOS v1 is best described as a **synthetic-population, multi-route contact-network, agent-based
stochastic epidemic simulator with an explicit observation model, used as a scenario-experimentation
environment.** It is not a forecasting model and not a calibrated epidemiological model, and it does not
claim to be either.

| Model class | Supported? | Evidence |
|---|---|---|
| Synthetic-population model | **Yes, strongly** | 104,540 agents, one per resident, reconciled to official marginals with tolerance exactly 0 (`population_generator.TOLERANCES`) |
| Agent-based epidemic simulator | **Yes** | Individual agents with per-agent compartment membership and per-agent timers in `respiratory.RespiratorySEIRS` |
| Contact-network epidemic simulator | **Yes** | Eleven separable routes with explicit edge tables and six daily-rebuilt dynamic routes (`network_generator._build_route_specs`) |
| Scenario-analysis framework | **Yes** | Typed, hashed, composable `ScenarioConfig` with matched-seed comparison (`intervention_schemas.py`, `intervention_analysis.py`) |
| Intervention experimentation environment | **Yes** | Eleven intervention types with calendar and detection-triggered activation (`interventions.InterventionManager`) |
| Observation / surveillance model | **Yes, strongly** | Separate latent and observed layers with enforced chronology (`observation_scheduler.py`) |
| Importation / travel model | **Yes** | Episode-based temporary population anchored to port statistics (`travel.py`) |
| Stochastic ensemble framework | **Partially** | Replicate machinery exists; it samples network, transmission and observation streams only (`E-01`) |
| Calibrated epidemiological model | **No** | No Jersey epidemiological target is registered; calibration is synthetic recovery (`C-01`, `C-02`) |
| Forecasting model | **No** | No forecast facility, no validation, no predictive claim anywhere in the repository |
| Named-pathogen model | **No** | Deliberately pathogen-neutral; `configs/diseases/respiratory_seirs_demo.yaml` labels every value `scenario_assumption` |
| Burden / healthcare-demand model | **No** | Severity and mortality structurally absent (`D-07`) |

Two classification subtleties are worth stating precisely.

First, **JOS is a mechanism-exploration platform rather than an estimation platform.** Its outputs are
functions of assumptions, and the assumptions are declared. This is a legitimate and well-established
mode of epidemic modelling — the tradition running through Eubank et al. (2004), Ferguson et al. (2006)
and Halloran et al. (2008) — in which a structurally detailed model is used to compare interventions
under controlled assumptions rather than to produce numerical predictions.

Second, **the synthetic population is a latent modelling substrate, not a register of Jersey
residents.** The repository states this explicitly and the review confirms it: agents have no
sub-parish location (`POP-12`), household coordinates are absent entirely, and every within-margin
distribution is either bounded or assumed. The word "synthetic" is doing real work here and should be
preserved in every external description.

---

## 4. Scientific architecture

The architecture proposed in the review brief was verified against the repository and is broadly
accurate, with four corrections.

```
22 REGISTERED OFFICIAL SOURCES (data/sources.yaml, SHA-256 verified)
        |  data_pipeline.build_canonical  ->  14 canonical CSVs, per-row provenance
        v
M1  SOURCE / PROVENANCE LAYER
        |  population_controls (IPF raking) + population_generator
        v
M2  SYNTHETIC RESIDENT POPULATION      104,540 agents / 45,133 households / 164 communal settings
        |  population_structure_generator + staffing_generator
        v
M3  DAYTIME STRUCTURE                  48 schools / ~700 classes / 8,770 workplaces / 62,108 jobs
M4.1                                   1,972 school staff / 448 care staff
        |  network_generator.generate_networks
        v
M4  ELEVEN CONTACT ROUTES              5 persistent edge tables + 6 daily dynamic builders
        |  starsim_adapter.build_starsim_disease_sim   (the ONLY Starsim coupling)
        v
M5  GENERIC RESPIRATORY SEIRS          Starsim 3.5.2, order-invariant route attribution
        |
        +--> M7  INTERVENTIONS      (prospective route views; never mutate M4)
        +--> M8  TRAVEL             (temporary population; 7 additional routes)
        +--> M5' EXOGENOUS IMPORTS  (mutually exclusive with explicit travel except mode 'both')
        |
        v
M6  OBSERVATION MODEL                  latent truth -> onset -> detection -> report
        |
        v
M6  ENSEMBLES / MATCHED-SEED COMPARISON
        |
        v
SCIENTIFIC ARTIFACTS                   Parquet + manifest + diagnostics, hash-chained,
        |                              independently re-verifiable (scientific_verification.py)
        v
M9 / M10  API AND INTERACTIVE APPLICATION   (execution and retrieval boundary; adds no science)
```

**Correction 1 — the observation model is not strictly downstream.** It runs both offline (after a
latent run) and online (inside the running simulation), because detection-triggered interventions need
notifications during execution. `observation_scheduler.ObservationScheduler` is shared by both paths and
the run fails if the two schedules disagree (`observation.observe_latent_run`,
`offline_online_agreement`). This is the correct design and it is stronger than the linear diagram
implies.

**Correction 2 — travel is not a downstream consumer but a parallel population layer.** `travel.py`
supplies its own run orchestration (`run_travel_outbreak`), its own seven contact routes, its own
comparison and ensemble entry points, and its own artifact writer and verifier. It wraps rather than
follows the disease layer.

**Correction 3 — interventions act on a copy.** The M4 route artifact is never mutated; effects are
applied to a prospective Starsim view and the runner asserts the M4 logical hash is unchanged across the
run, raising `"M5 mutated the M4 route artifact"` otherwise (`outbreak_runner.run_outbreak`). This is
what makes the baseline counterfactual clean and matched-seed comparison meaningful (`I-03`).

**Correction 4 — the exogenous import process is a distinct fifth injection channel**, not a facet of
travel. In `explicit_travel` mode it is hard-zeroed before the disease is constructed; only in mode
`both` do both operate, additively and without any linkage between their magnitudes (`T-16`).

One architectural property deserves emphasis because it is the platform's principal scientific asset:
**the layers are separable and the separations are enforced by executable checks.** Removing a route
family leaves all other route snapshots byte-identical
(`tests/test_networks.py::test_route_family_removal_is_independent`); a neutral intervention manager
reproduces the baseline latent hash exactly; and a zero-arrival travel configuration reproduces the
non-travel run's `daily_epidemic`, `transmission_events` and `latent_outcome_hash` verbatim
(`tests/test_m8_travel.py::test_zero_arrivals_are_a_real_noop_for_resident_outputs`, `T-31`). These are
falsifiable claims about modularity, and they pass.

---

## 5. Synthetic population

### 5.1 Construction and what is anchored

The population is built in four hash-chained, seed-deterministic stages, and nothing in this lane is
simulated. The evidence discipline in the ingestion stage is the strongest part of the codebase:
canonical rows carry `source_id`, `source_sha256`, `reference_period`, `observation_status`,
`source_locator` and `transformation_id`; suppressed cells are written with a blank count plus an
explicit `upper_bound` and `censoring = 'positive_less_than'` rather than being imputed (Agriculture
50+ workplaces `upper_bound = 5`; suppressed parish "other" commute cells `upper_bound = 10`);
published rounding is left as published; and source conflicts are surfaced as diagnostics rather than
silently resolved (`mean_bedrooms_conflict`: report 2.47 against CSV 2.57) (`DP-01`).

Three control non-reconciliations exist in the published sources and none is concealed: sector-by-size
workplace rows sum to 8,540 undertakings against a published total of 8,500 (+40, +0.47%); sector job
rows sum to 55,360 against a published private-sector total of 55,370 (−10); the commute table sums to
57,340 workers against 57,338 in the industry table (+2). All three are consistent with publication to
the nearest 10 and none exceeds 0.5% (`DP-02`).

**Empirically anchored:** the population total (104,540), its 2024 broad age marginals (under 16 =
15,410; 16–64 = 68,530; 65+ = 20,600) and sex totals, the 2021 single-year age × sex shape, all 12
parish totals, the 11 household-type counts, the private/communal split, communal establishment and
resident counts by category, dwelling and car-access percentages, pupils by school type (13,991),
resident workers by sector and sex (57,338), private undertakings by size band (8,500), private filled
jobs (55,370), commute modes by parish, the workplace destination split (66/13/21), two conditional
commute profiles, and the school FTE and Care Commission ratios.

**Derived by documented transformation:** the detailed 2024 age × sex table, the parish age × sex table,
all mode-scaled targets, the parish no-car weights, and the FTE-to-endpoint and roster conversions.

**Structural or scenario:** household relational constants and size caps, housing attribute weights,
all communal age eligibility and the care-home age ramp, school capacities and class sizes, the 50+
workplace upper bound, the 25-employee non-private cap, the 0.07 secondary-job rate, the employment age
propensity, the 0.8 FTE ratio, the 2.0 care coverage multiplier, and the 13.67% work-from-home level.

### 5.2 Identity, raking and reference-year mixing — done correctly

The identity backbone is sound and unusually well guarded. All count reconciliations carry tolerance
exactly 0; the manifest validator refuses to write an artifact whose actual population differs from
target; and the M2 → M3 → Starsim chain asserts that `people.age` and `people.female` are element-wise
equal to the M2 rows, so silent agent duplication, loss or reordering is impossible
(`tests/test_c1_identity.py::test_c1_starsim_identity_is_exact`) (`POP-01`).

The 2024 detailed age structure is produced by 100 alternating proportional-fitting sweeps on a 3×2
band-by-sex table followed by largest-remainder allocation over the 2021 single-year shape; both
marginal sets are hit exactly (`POP-02`). Critically, **reference-year mixing is handled correctly**:
the 2021-referenced worker control is scaled on `census_population_reference = 103,267` while the
2024/2025-referenced school, workplace and job controls are scaled on `full_population_target =
104,540`, so each control is paired with its own denominator. That is the scientifically correct
treatment and it is easy to get wrong (`POP-03`).

The limitation is that the raking cannot absorb compositional change *within* a band: every single year
of age 65–95 is scaled by the same factor 20,600 / 18,736 = 1.09949, whereas the real 2021–2024 growth
of the 65+ group came predominantly from the 60–64 cohort crossing the boundary. The model therefore
carries 85+ = 2,848, 90+ = 1,053 and 95+ = 263, all modestly over-stated (`POP-02`).

A documentation discrepancy is recorded here: `data/processed/quality_report.md` states that "detailed
2024 age-by-sex is not inferred from 2021 data", while `population_controls._build_full_age_sex_counts`
does exactly that inference and is the sole basis for every agent's age and sex. The M2 assumptions
tuple is honest about it, so the two documents of record contradict each other.

### 5.3 Where the population is weakest

**Distributions inside anchored margins are largely unfitted.** Household size is controlled only at
the mean (2.2696 against an observed 2.2697) and the one-person share (14,239 of 45,133 households =
31.55%, pinned by `HOUSEHOLD_MAX_SIZE = 1` for the two single-person types); no persons-per-household
distribution control exists anywhere in the registry, and the residual 14,765 members are spread across
30,894 growable households by a remaining-capacity-weighted rule that thins the right tail, with a
global cap of 8. The 2/3/4/5+ split is thus a structural artefact presented alongside two genuine
anchors, and household size variance is too low — which under-states within-household amplification
(`POP-04`). Household secondary attack rates are also commonly reported to vary with household size
(Madewell et al. 2020), a dependence the model cannot express.

**Within-household age structure is bounded but not calibrated.** `MIN_GENERATION_GAP = 15` and
`MAX_COUPLE_AGE_GAP = 25` are enforced as hard inequalities with no distribution fitted inside them.
The project's own diagnostics show the consequence: across 18,612 couples the median age gap is 10 years
with 28.2% exceeding 15 years; across 15,375 parent/child households the median generation gap is 22
years with P95 46 and P99 53. Real spousal gaps concentrate within a few years and real parent-child
gaps near 28–33. Household transmission volume is unaffected; its age targeting is not (`POP-05`).

**Care-home residents are far too young.** Eligibility is age 50–95 with draw weight
`max(1, age - 45)`, giving 30.45% aged 50–64 and a median age of 71. The binding constraint is the
weight, not the pool: the model contains 2,848 residents aged 85+ against 969 care-home places in total,
so nearly every place could have been filled from the 85+ group with 1,879 to spare. Any severity-
weighted care-home conclusion is invalidated by this, and the 50-year floor is frozen by a test, so the
behaviour is guaranteed rather than incidental (`POP-10`).

**Two allocation orders produce artefacts that were probably not intended.** The pupil selection sorts
candidates by age ascending within each school type processed in fixed order, so each type strips the
youngest remaining eligible ages: at full scale every special-school pupil is aged exactly 18, the six
independent primary schools contain only 10- and 11-year-olds, and the three independent secondaries
contain only 16- and 17-year-olds. School type is now almost perfectly confounded with pupil age, and
the diagnostic `invalid_school_age_placements = 0` cannot detect it because the permitted ranges are
respected (`STR-01`). Separately, the residual parish no-car allocation distributes counts proportional
to bare commute shares with no household-count weighting, producing a generated no-car rate that
correlates −0.69 with the very weight it is documented to follow: St Mary has the lowest weight of all
12 parishes (0.1688) and the highest non-St-Helier rate (19.57%), while St Saviour has the second
highest weight (0.3886) and 6.00% (`POP-07`).

**Two pieces of ingested evidence are discarded.** The published sector-by-size workplace cross-tab is
parsed into `StructureControls.workplace_cell_counts` and never read; sector is instead matched to
workplace size by a descending-size, minimum-remaining-capacity heuristic that is anti-correlated with
the discarded table by construction, so a sector whose 50+ band is suppressed as fewer than five can
receive a 150-employee workplace (`STR-06`). The tenure-specific overcrowding gradient (owner-occupied
1.5% to non-qualified accommodation 14.6%, a nearly ten-fold range) is collapsed by a last-wins
dictionary and never used (`POP-06`).

**Workplace sizes are near-degenerate and the tail is truncated.** Every workplace is seeded at its band
minimum with surplus spread by capacity-weighted increments, so each band sits near its lower bound
while the 50+ band forms a narrow plateau: mean 150.48, range 132–173, against a declared structural
range of (50, 500). The largest workplace anywhere in the model has 173 employees, and the entire
public-sector universe of 6,738 jobs is partitioned into 270 workplaces of at most 25 employees — so
the hospital, the single most consequential workplace in a respiratory outbreak, has no representation
as a large site (`STR-07`).

**Realised employment rates differ substantially from the declared propensity weights.** The documented
propensity (0.45 / 0.90 / 1.00 / 0.80 / 0.18 by age band) consists of selection weights in a
without-replacement draw with sampling fraction 58,045 / 77,312 = 75.1%, at which the realised rates
compress toward the mean: 60.3% / 84.7% / 87.3% / 81.5% / 31.1%. The 65–74 rate is roughly double what
the declared weight implies, and the project's own figure (3,547 of 11,094, or 31.96%) agrees with the
realised value, not the weight. Older adults therefore acquire workplace and commute contacts they
would not have — in the age band with the highest severity for most respiratory pathogens (`STR-05`).

**Reduced-scale modes are not scale models.** At `ci` mode (3,000 agents) only 3 of 8 communal
categories survive: no nursing care home, no children's home, no homeless hostel, no detention setting,
and care staffing produces 4 support workers and zero nurses. At `scaled` mode the 149-resident
detention setting — the largest congregate setting in the model — rounds to zero establishments and its
residents inflate the survivors. Aggregate per-capita ratios are preserved almost exactly; categorical
composition and per-unit size are not (`POP-11`). Since every integration test runs at `ci` scale, the
nursing staffing branch is never exercised end to end (`TEST-01`, `X-02`).

### 5.4 Fitness for purpose

For **route-separable transmission at island scale** the population is fit: the routes exist, the
memberships reconcile, and the totals are anchored. For **school and workplace interventions** it is fit
at the aggregate level but not by school type, by sector-and-size, or in the workplace size tail. For
**care interventions** it is fit structurally but the resident age profile will not support any
severity-weighted conclusion and there is no cross-facility staff bridge (`STA-05`). For **parish-level
outputs** it is fit on residence but not on daytime geography.

One positive finding deserves emphasis because a reviewer would expect the opposite: **St Helier work
centralisation is empirically anchored, not assumed.** The destination split (66% St Helier, 13%
semi-urban, 21% rural) is an observed census control and the generator reconciles to it within one
percentage point (`STR-10`). Occupational double-counting is also correctly prevented: institutional
staff replace rather than add to their generic workplace membership (`STA-01`).

---

## 6. Contact networks

### 6.1 Architecture

Eleven routes are implemented with exactly the documented identifiers: `household`, `school_class`,
`school_cross_class`, `workplace_team`, `workplace_transient`, `care_resident`, `care_staff`,
`shared_vehicle`, `bus`, `community_indoor`, `community_outdoor` (`network_generator._build_route_specs`).
Five are persistent static edge tables; six are daily-rebuilt closures. The full corrected edge counts
are household 98,052, school_class 190,293, school_cross_class 29,345, workplace_team 147,721,
workplace_transient 96,742 and care_resident 3,336, with the remaining routes generated dynamically.

Determinism is achieved without a random number generator: `_stable_int(seed, *parts)` takes a SHA-256
of a pipe-joined string, so every "sample" is a deterministic hash permutation. For a fixed seed there
is exactly one network realisation — which is why ensemble replicates, which reseed network generation,
genuinely vary the network (`E-01`).

Three topological primitives are used: complete groups (cliques) for households, classes, care residents
and small transport units; circulant rings with offsets 1..k for the larger pooled routes, giving degree
exactly 2k after de-duplication; and hash-directed target choice inside bounded pools.

### 6.2 The nested-route exclusion works

The C2 correction is real and verifiable. Before it, school cross-class and workplace transient pools
intersected class-core and team-core at 18,784 and 19,318 pairs respectively; after the exclusions both
are exactly zero. A route-overlap matrix classifies every route pair as `FORBIDDEN`,
`ALLOWED_DISTINCT_SETTING`, `EXPECTED/NESTED_EXCLUDED` or `DIAGNOSTIC_ONLY`, and distinct-setting
overlaps remain diagnosable. This is the correct treatment: a household pair who also share a workplace
team represent two separate exposure opportunities, not one encounter stored twice (`N-05`).

A qualification: the overlap matrix is computed on a single date, so overlaps arising only on other
calendar days are not captured, and the same dyad appearing on two routes is evaluated as two separate
transmission opportunities — the intended semantics, but it means risk compounds across routes for
co-located pairs.

### 6.3 The dominant network limitation: no contact heterogeneity

**This is the single most important structural finding of the review.** Contact degree is fixed by
construction in every route. Ring-based routes give every participant exactly `2k` neighbours
irrespective of pool size; clique-based routes give every member exactly `n − 1`. There is no
individual-level contact-rate parameter, no negative-binomial or Poisson degree draw, and no persistent
per-agent activity multiplier anywhere in `network_generator.py` (`N-02`).

The consequence is that **JOS cannot generate overdispersion in individual reproduction number and
cannot produce superspreading events**, other than through the modest variation induced by household and
workplace size. Since Lloyd-Smith et al. (2005), individual variation in transmission has been
understood as a first-order determinant of epidemic behaviour: high overdispersion makes early
extinction more likely, makes realised epidemics more explosive when they do take off, and materially
changes which interventions are efficient. A model with homogeneous degree produces epidemics that are
more deterministic, more synchronised and less variable than reality at the same mean.

This compounds with the deterministic stage durations (`D-01`) to make individual reproduction number
strongly under-dispersed on both axes — contact count and infectious duration. It is the primary reason
the ensemble bands in Section 11 should not be read as plausible ranges for a real outbreak.

### 6.4 Weights, beta and the contact budget

Route relative weights are structural assumptions: household 1.0, care_resident 0.9, school_class 0.85,
workplace_team 0.7 and shared_vehicle 0.7, care_staff 0.65, school_cross_class 0.5, bus 0.45,
community_indoor 0.35, workplace_transient 0.3, community_outdoor 0.18. In `starsim_adapter._edge_arrays`
the edge weight becomes the Starsim per-edge `beta` array, and `outbreak_runner` sets
`route_betas[r] = beta * route_multipliers[r]` with every shipped multiplier equal to 1.0. So the
effective daily per-edge transmission probability is `0.08 × weight`: 0.08 on a household edge, 0.0144 on
an outdoor community edge (`N-22`, `D-09`).

Two consequences follow. First, **there are two multiplicative parameters over the same product** — the
M4 relative weight and the M5 route multiplier — and no output identifies the split, which is a
redundancy that should be collapsed. Second, **the indoor:outdoor ratio of about 1.9 is scientifically
low.** Bulfone et al. (2021), reviewing outdoor transmission of SARS-CoV-2 and other respiratory
viruses, report that the identified studies found under 10% of infections occurred outdoors, while
noting explicitly that the heterogeneity of the evidence prevented a pooled quantitative estimate. A
1.9-fold attenuation is not consistent with the qualitative direction of that literature and will
over-state the outdoor share of simulated transmission.

On the **contact budget**: because weights are exposure-opportunity multipliers rather than contact
counts, the model does not expose a per-agent contacts-per-day quantity that could be compared against
contact-survey magnitudes such as POLYMOD (Mossong et al. 2008) or CoMix (Jarvis et al. 2020). The edge
count per agent per day is computable from the artifacts, but its interpretation as a contact number is
not licensed by the code, which is explicit that weights are relative daily exposure opportunities and
are not separately identified from transmissibility. **This should be stated plainly rather than
finessed: JOS v1 does not currently demonstrate that its per-agent daily contact structure is
consistent with any empirical contact survey**, and doing so would be a high-value hardening step.

### 6.5 Community mixing and geography

The community routes use a broad-age mixing matrix that is a structural assumption, not Jersey contact-
diary evidence and not a POLYMOD-derived matrix. Community contacts are drawn within the same parish
only, so the sole cross-parish mixing channels are workplace membership (via synthetic work parish) and
the transport routes. Combined with the absence of sub-parish geography (`POP-12`) and the degeneracy of
school parish (`STR-02`), this means **the model's spatial structure is coarser and more synchronised
than Jersey's real geography**, in the direction of faster island-wide spread.

A specific structural leak deserves separate emphasis. **Care-home residents are not excluded from the
general community route** and participate at free-living rates (`N-10`). Institutional residents are
thereby exposed to, and can seed, community transmission in a way that materially understates the
epidemiological isolation of care settings and overstates the exposure of the model's most
severity-relevant subpopulation. Combined with the care-home age profile (`POP-10`), this is the
highest-leverage single correction identified in the review, and it is a route-membership filter rather
than a modelling redesign.

### 6.6 Route attribution: bookkeeping, not causal inference

Attribution is implemented carefully. Infection occurrence is the unchanged union of successful Starsim
edge draws; attribution then selects one successful candidate per target with probability proportional
to that candidate's realised per-edge hazard, keyed on `(rand_seed, 'attribution', timestep, target)` so
route insertion order cannot matter. The full candidate set, per-candidate hazards and candidate count
are retained on every event and the candidate-count distribution is published in diagnostics (`D-05`).

**The correct description is therefore "simulated transmission pathway" or "bookkeeping attribution
over simulated pathways" — not mechanistic attribution and certainly not inferred cause.** Three
reasons. First, where a target has successful candidates on several routes, the attributed route is one
draw from a hazard-weighted distribution over routes that all in fact succeeded; a different attribution
draw would relabel the same infection. Second, the hazards themselves derive from unanchored relative
weights (`N-22`), so the weighting of the attribution draw is assumption-driven. Third, the route
inventory is the model's own construction, so attribution can only ever be to a route JOS represents.

The correct use of route output is **ablation and contrast**: disabling a route family and observing the
change is a well-founded experiment, because the separability is enforced by test. Absolute route shares
should be reported with the candidate-count distribution beside them.

---

## 7. Disease dynamics

### 7.1 Structure and coherence

`respiratory.RespiratorySEIRS` implements S → E → I → R → S with per-agent boolean compartments and
per-agent transition timers, delegating edge-level transmission probability to Starsim's
`compute_transmission` and `Network.net_beta` primitives. The engine version is asserted at the disease
boundary (`RuntimeError` unless Starsim is exactly 3.5.2).

**The state transitions are internally coherent.** Exactly one compartment is true per agent; transitions
occur when the simulation index reaches the scheduled timer; `step_die` clears all four compartments;
and artifact verification independently re-derives that the compartment sum is constant across the
horizon, that new infections equal local plus imported, and that cumulative totals equal the running sum
of local, imported and seeded (`scientific_verification._verify_m5_tables`, `D-06`, `V-01`). Modifier
composition is handled through a registered-component system (`set_modifier_component`,
`recompose_modifiers`) so vaccination and travel modifiers compose multiplicatively without either
clobbering the other.

### 7.2 The four substantive limitations

**Deterministic stage durations (`D-01`).** Latent, infectious and immunity durations are all
`ss.constant`: 2, 5 and 30 days respectively. The generation-interval distribution is a point mass.
This is the most consequential parameterisation choice in the disease layer, and it is not merely a
matter of realism. Lloyd (2001) showed that replacing exponential infectious periods with realistically
narrow distributions destabilises epidemic models, and Krylova and Earn (2013) showed that the shape of
the stage-duration distribution alters the dynamical structure of seasonally forced models; Wearing,
Rohani and Keeling (2005) make the same point for management-relevant quantities. A point-mass duration
sits at the extreme end of that spectrum. The expected direction is sharper, faster, more synchronised
peaks, narrower stochastic envelopes and reduced probability of early extinction.

**No presymptomatic infectiousness and constant infectiousness (`D-02`).** Only the `infected` state
transmits, and relative infectiousness is 1.0 throughout. The parameter file records
`infectiousness_profile` as "constant while infected" and `symptom_probability` as not implemented. This
matters chiefly through its interaction with the observation and intervention layers: because
transmission cannot begin before the latent period ends, a detection triggered at or before onset can in
principle avert the entire infectious period.

**Full-susceptibility waning (`D-03`).** Recovered agents return to susceptible with `rel_sus`
unchanged, and the default configuration enables waning at 30 days. There is no partial immunity and no
boosting. Over the default 30-day horizon this is inert; over any longer horizon it produces repeated
full-susceptibility reinfection and a strongly oscillatory SEIRS. Note that the school calendar caps a
run at 360 days from the default start (`N-19`), so the regime in which this matters most is largely
unreachable in v1.

**`attack_rate` is not an attack rate (`D-04`).** The column is
`cum_total_infections / len(sim.people)`, where the numerator accumulates every infection event
including seeds and post-waning reinfections. It is a cumulative incidence rate per capita, is not
bounded by one, and in travel runs its denominator includes pre-allocated visitor slots. The underlying
counts are correct and reconciled; the label is the problem, and it is precisely the kind of label a
reader will take at face value.

### 7.3 Identifiability

The disease layer has a well-defined identifiability problem, and the repository states it. A route's
contribution to transmission is the product of four quantities: `beta`, the route multiplier, the edge
weight, and the edge count. Two of those are free multiplicative parameters over the same product, the
third is fixed by unanchored structural capacities, and no output identifies the split. The calibration
harness demonstrates this deliberately by profiling beta under altered ascertainment and altered route
weights (`calibration.run_beta_recovery`). **Consequently a fitted beta is one point on a ridge of
observationally equivalent parameter combinations** (`C-02`). This is a familiar situation in
individual-based epidemic modelling — Chowell (2017) treats identifiability as a first-class concern for
exactly this reason — and the appropriate response is to reduce the parameter set to one identifiable
per-route intensity rather than to fit the redundant set.

Consistent with the review brief, the generic demonstration parameters are **not** criticised for being
generic: `configs/diseases/respiratory_seirs_demo.yaml` labels every value `scenario_assumption` with
`source_ids: []` and explicit notes that they are not named-pathogen estimates. That is the correct
handling, and it is what keeps a pathogen-neutral engine from becoming a misleading one.

---

## 8. Observation model

### 8.1 The core principle is implemented structurally

JOS honours *true infections ≠ observed cases* not by convention but by construction. Every observation
row carries four distinct dates — infection, symptom onset, detection/testing, report — and the latent
truth is conserved whether or not an event is ever detected. The scheduler is shared between the offline
path (post-hoc observation of a completed latent run) and the online path (notifications delivered
during execution for detection-triggered interventions), and `observe_latent_run` recomputes the offline
schedule with the same sampler and **raises if it disagrees with the runtime schedule**. Observation
randomness is namespaced on latent replicate seed, observation seed, configuration identity and a
stable per-event key, so no two replicates can reuse an observation sequence, and insertion order cannot
matter (`O-01`).

Three checks are computed rather than asserted: `chronology_violations` counts any ordering breach,
`latent_incidence_conservation` confirms the latent series is unchanged by observation, and the analysis
horizon is extended by an explicit or derived maximum-delay tail so late reports are not truncated.
This is a materially better observation layer than most published agent-based models provide.

### 8.2 The onset anchor is decoupled from the natural history

**This is the most important finding in the observation layer, and it has direct consequences for the
intervention results.** `schedule_infection` computes symptom onset as `infection_date +
symptom_onset_delay`, with no constraint that onset fall after the latent period. In the shipped
`configs/observation/observation_demo.yaml`, `symptom_onset_delay` and `detection_delay` are both fixed
at 0 days. With `latent_period_days = 2.0`, symptomatic cases are therefore detected on the day they are
infected — **two days before they become infectious.** Detection-triggered isolation takes effect at
`detection_time_index + 1`, still ahead of the case's first infectious day (`O-02`).

The chronology check cannot catch this because it tests only that onset is not before infection. The
lifecycle machinery is correct and non-retrocausal (`I-03`); the defect is in the anchor, and it means
the shipped isolation and quarantine scenarios operate in a regime where essentially the whole
infectious period is available to be averted. **The direction of bias is unambiguous: modelled
symptom-triggered control is optimistic.** Any presentation of `m7_case_isolation`,
`m7_case_isolation_quarantine` or `m7_combined` results must disclose this or, better, re-run with a
positive onset delay.

### 8.3 Further observation limitations

Symptomatic status is drawn in the observation layer and never enters the disease model, so detection is
a random thinning of infections uncorrelated with how much an agent transmits — whereas real
symptom-based surveillance over-samples the more symptomatic and often more infectious (`O-03`). The
per-day `ascertainment_fraction` divides detections on a date by infections on the same date, mixing
cohorts, so it is not a probability and is unbounded; the run-level figure is the correct cohort
quantity (`O-04`). And the day-of-week factor multiplies an already-validated probability without
re-bounding the product, which would saturate silently if configured above one (`O-05`).

---

## 9. Interventions

### 9.1 Lifecycle: correct

`interventions.InterventionManager` is a single typed Starsim intervention module handling eleven
intervention types with calendar or detection-triggered activation. Three properties are verified and
sound (`I-03`):

- **No retrocausality.** Detection notifications arrive after the day's transmission has completed, and
  action is queued for `detection_time_index + 1 + start_delay_days`. A detection on day *t* cannot
  alter transmission already realised on day *t*.
- **Clean counterfactual.** The M4 route artifact is never mutated; effects apply to a prospective view,
  and the runner asserts the M4 logical hash is unchanged. When every composed factor equals one, route
  arrays are reused without copy or cast, so a neutral scenario is byte-identical to a no-manager run.
- **Auditable suppression.** Care roster edges are retained with zero effective beta rather than deleted,
  so roster topology stays inspectable under a care-protection intervention.

Modifier ordering is deterministic: factors are composed in canonical order with `math.prod` and clipped
into [0, 1]. Targeting reads M2/M3 metadata for age, parish, school, job, workplace, household and care
setting, and correctly ignores visitor slots when a travel population is present.

### 9.2 Three semantic limitations that bias effects upward

**Adherence is per-route, not per-person (`I-01`).** `_target_adheres` keys its stable draw on
`(run_seed, 'route-adherence', intervention_id, route_id, agent_id)`. Because `route_id` is in the key,
draws are independent across routes: at adherence 0.8 across eight suppressed routes, essentially nobody
is fully non-adherent, and the intervention behaves as a uniform 80% reduction in exposure opportunities
rather than as 80% of people complying. **The correlated tail of fully non-compliant individuals — which
is what sustains transmission under real partial compliance — is absent.** Detection-triggered
acceptance additionally includes the detection date in its key, so it is re-drawn at each detection
rather than being a stable personal trait. The work-from-home family is the exception: its adherence is
correctly keyed on the agent alone.

**No behavioural substitution (`I-02`).** Every route multiplier is bounded in [0, 1], in both the
intervention and travel layers (`T-27`). Closing a school deletes class edges without adding household
or community contact; sending a worker home deletes workplace and commute edges with no compensating
community exposure. **A measured intervention effect can never be adverse**, so the framework cannot
represent the well-documented possibility that suppressing one setting displaces exposure into another.
In combined scenarios the bias compounds multiplicatively.

**Vaccination reaches only current susceptibles (`I-04`).** `_refresh_vaccination` filters on
`disease.susceptible.raw[uid]`, while the coverage denominator counts all target-matching agents. A
campaign therefore preferentially reaches the never-infected and the waned, which is more efficient than
a real status-blind campaign, and nominal coverage can become unreachable as the epidemic progresses.

A fourth, smaller point: effects scale per-edge probability rather than contact counts, which coincides
with a contact reduction only to first order in beta and cannot represent rewiring; where both endpoints
are isolating the factor is applied twice (`I-05`).

### 9.3 Do the labels match what the model changes?

Largely yes, with three qualifications worth recording. `household_quarantine` correctly operates on
private-household membership and skips communal residents. `workplace_reduction` genuinely removes
workplace and commute edges on remote days, consuming the same `remote_days_per_week` field the
population layer sets — but the v1 population makes that field binary (5 or 0), so partial remote working
is not representable, and the 13.67% baseline is a 2021-census (pandemic-period) measurement allocated
uniformly at random across sectors rather than concentrated in the sectors where remote work actually
occurs (`STR-09`). `traveller_vaccination_*` in the travel layer covers visitors only and silently
exempts returning residents, who are precisely the arrivals a real pre-travel requirement would reach
(`T-28`).

### 9.4 Simulation efficacy versus policy effectiveness

The distinction must be maintained explicitly. What the intervention layer produces is **the change in
simulated transmission when specified contact-opportunity multipliers are applied to specified routes at
specified times, under the model's assumed adherence semantics and with no behavioural compensation.**
That is a mechanistic experiment. It is not an estimate of what the corresponding real policy would
achieve, and three of the findings above (`O-02`, `I-01`, `I-02`) each push in the optimistic direction.
The repository's own documentation already states that these outputs do not estimate policy
effectiveness; this review confirms that position is not conservatism but a correct reading of the
mechanism.

---

## 10. Travel and visitor modelling

### 10.1 The empirical anchor, stated exactly

The only empirically anchored travel quantities are the 2025 Ports of Jersey totals:
**720,842 air and 196,623 sea passenger arrivals, 917,465 in total.** These were verified against the
frozen snapshot `data/raw/passenger_arrivals_total_csv/total-arrivals.csv` (final row
`2025,196623,720842,917465`) and the processed table `data/processed/passenger_arrivals.csv`.

**These are passenger movements — arrivals at the two ports — and not unique tourists.** The distinction
is maintained in the implementation, not merely in prose: `TravelConfig.resolved_parameter_provenance()`
records `units = 'passenger movements/year'` with the note "Passenger movements, not unique tourists.";
the assumptions tuple states "Annual air/sea values are Ports of Jersey passenger arrivals, not unique
visitors."; and the run diagnostics set `streams.annual_values_are_passenger_arrivals = True`. No code
path converts movements to unique visitors; the generated unit is a person-movement, and composition,
party, stay and transport draws are applied to movements. A single tourist making one round trip
contributes one arrival, and so does a resident returning from a trip (`T-01`). **Any external
description of JOS must preserve this distinction.**

The annual-to-daily apportionment is a half-up integer annual target followed by largest-remainder
(Hamilton) apportionment with an ISO-date tiebreak, so the annual integer is preserved for any
seasonality shape. This reproduces 720,842 / 196,623 / 917,465 exactly at `stream_scale = 1` under both
neutral and summer-shaped profiles, and a test pins the identity (`T-02`). One caveat for accurate
reporting: at `stream_scale = 1` a full-year horizon would need 917,465 materialised episodes, exceeding
the 200,000 limit, so **the exact reconciliation is a property of the apportionment and capacity gate,
demonstrated by the non-epidemic benchmark path, not by an executed full-year disease run** (`T-04`).

Everything else in the travel layer — composition, stay duration, party size, transport mode,
accommodation, contact intensities, arrival prevalence, external acquisition pressure, all border
measures and all seasonality shapes — is a scenario or structural assumption, and the code labels them
as such.

### 10.2 Slot reuse and identity: correct, and the hardest thing here

Because Starsim's `People.grow` is append-only, visitors occupy pre-allocated slots that are reused
across the run. This is the central correctness question for visitor-attributed output, and the
implementation holds up (`T-09`, `T-10`).

State cannot leak: departure calls `reset_person_state`, clearing all four compartments, setting all
four transition timers to NaN, resetting every registered modifier component to 1.0, zeroing age and
sex, marking the slot not-alive and dropping it from the active set; activation calls
`initialize_arrival_state`, which itself begins with a reset. Deactivation strictly precedes activation
within the same daily call, so a slot is never doubly occupied. Contacts cannot leak because the
temporary edge lists are rebuilt from scratch each day. An end-of-run audit checks every inactive slot
for cleared state.

History cannot be relabelled: every event resolves its actor through an interval map keyed on
`(slot_uid, timestep)` rather than through the slot's current occupant, and `visitor_id`, `trip_id`,
`travel_party_id` and `episode_identity_hash` are frozen into the event at creation. The observation
layer prefers the event's own agent identifier and includes the episode hash in its duplicate key, so a
later occupant cannot inherit a detection. A test mutates the identifier map between scheduling and
delivery and confirms the delivered detection still names the original visitor.

### 10.3 Scaling: the ratio is not preserved

`stream_scale` samples the traveller stream, and nothing scales the resident population with it. The
real ratio is 917,465 / 104,540 = 8.776 movements per resident-year. Every shipped travel and scenario
configuration uses `stream_scale: 0.001`, giving 918 movements/year, or 0.0088 per resident-year at full
population — roughly a thousandfold lower than source. At `ci` population with `stream_scale = 1` the
bias reverses and becomes large and upward (`T-03`).

**No shipped configuration should be read as representing Jersey's actual traveller-to-resident exposure
ratio, even qualitatively.** A self-consistent configuration exists (full population at
`stream_scale = 1`, for horizons up to about 79 days) but is not what any documented command uses.

This compounds with a second scaling problem: **visitor-to-resident mixing does not scale with arrival
volume** (`T-13`). The resident pools recruited into the visitor-facing routes are absolute counts —
exactly 4 St Helier residents per terminal per day, exactly 3 residents per parish per day per community
route — regardless of how many people arrive or participate. As volume grows the rings become almost
entirely visitor-to-visitor and absolute resident exposure saturates. **Arrival-volume sensitivity
results must therefore not be read as elasticities or dose-responses.** Incidentally the terminal
resident parish is hard-coded to St Helier, whereas Jersey Airport is in St Peter.

### 10.4 Border measures: mechanistically meaningful, structurally optimistic

The arrival-testing lifecycle is genuinely well built (`T-17`). Administration, scheduled result time,
result availability and prospective action are four separately logged stages; a result is a frozen
record bound to the episode identity hash; a result landing after the visitor has left is emitted as
non-actionable and cannot quarantine the replacement occupant; returning-resident delayed results are
matched to the permanent identity and remain actionable; and all-arrival quarantine is independent of
testing probability. Quarantine is multiplicative attenuation of both endpoints with a route-class
distinction, a per-person adherence draw, an activation delay and a release timestep, which correctly
separates the policy's three loss channels of coverage, turnaround and adherence (`T-27`).

But **the test has no incubation-dependent sensitivity** (`T-14`). It is a perfect-information test on
compartment membership: `exposed` and `infectious` are treated identically, a single constant sensitivity
applies, and every shipped configuration sets it to 1.0. Worse, external acquisition for returning
residents runs immediately before the arrival test in the same callback, so a resident infected abroad at
the return timestep is already `exposed` when tested and is detected with full sensitivity. **The
recently infected are exactly the population that real border screening systematically misses, and that
is the dominant reason real arrival testing has modest effect.** The model cannot represent the main
failure mode of the policy it is used to explore, in the optimistic direction. A second, smaller
distortion runs the other way: positive results returned after departure are excluded from reported
positive-test counts, so measured screening *yield* is understated even as measured *effectiveness* is
overstated (`T-18`).

Arrival prevalence itself is a free dial with no anchor, applied identically to air and sea and to all
origins because origin is not modelled at all (`origin_category` is the constant
`'synthetic_temporary_visitor'`). Since arrival prevalence times arrival volume is the entire
visitor-side importation signal, **every visitor-driven result is approximately linear in a number the
user chooses**, and should be reported as a function of it rather than at a single value (`T-19`).

### 10.5 Two defects in the resident-travel path

**In-horizon resident absences are never applied at runtime (`T-11`).** Presence is computed once at
construction from the start date; the daily loop adds residents back on return but never removes anyone
at absence start. A returning resident whose absence begins inside the horizon therefore remains in
every resident route edge for the whole of their nominal absence, while the plan counts them as away.
Two artifact columns then disagree for the same day: `daily_travel_population.resident_away` comes from
the plan, `daily_travel_intervention_state.resident_away` from the runtime. The magnitude is negligible
at the shipped scale (about 276 resident-days out of some 38 million) but reaches roughly 0.7% of
resident person-time at `stream_scale = 1`. **This is the finding closest to a blocker in the whole
review**, because it is an internal inconsistency in a system whose central scientific asset is
reconciliation; it stops short because the mechanism does exist and functions for absences in progress at
run start, and because no published result depends on it. It would become a blocker for any analysis
using resident outbound travel as a material mechanism.

**Repeat resident returns collide in person-keyed runtime maps (`T-12`).** The same resident can
legitimately receive two return episodes in one horizon; when that happens the second is silently
dropped with testing off, and raises a `RuntimeError` with testing on. At `stream_scale = 1` over 30 days
roughly 270 such collisions would be expected.

Finally, returning residents always arrive susceptible and acquire infection abroad via a draw applied
on the return day, so no resident can return already infectious and every resident importation spends its
full latent period on the island (`T-15`).

### 10.6 Denominators

The denominator design is mostly careful and explicitly diagnosed: `resident_attack_rate` divides
resident acquisitions by the fixed resident count, `visitor_attack_rate` divides visitor acquisitions by
cumulative arrivals, inactive slots are excluded from the active set, and seeding is restricted to
present residents so visitors can never be seeded. The residual issue is that the headline
susceptible/exposed/infectious/recovered columns are counted over the active set, which includes active
visitors, so **a reader plotting `infectious` from `daily_epidemic.parquet` is plotting residents plus
visitors** — about 6% of the present population at `stream_scale = 1` and full population. Resident-only
columns exist alongside but carry no note on the mixed ones (`T-25`).

---

## 11. Ensembles and uncertainty

### 11.1 What the bands actually contain

Each replicate re-validates the same M2 and M3 population artifacts and re-generates **only** the M4
network with the replicate seed, then runs the disease and observation layers on that seed
(`ensemble._run_replicate_job`). The quantified uncertainty is therefore:

- network-realisation stochasticity — **included**;
- transmission stochasticity — **included**;
- observation stochasticity — **included**;
- population-generation stochasticity — **excluded** (one fixed population);
- parameter uncertainty — **excluded** (one `base_run_config`, one parameter set per ensemble);
- structural uncertainty — **excluded** (no facility anywhere in the system).

**Stochastic replicate bands alone do not quantify total scientific uncertainty, and in JOS v1 they do
not even quantify total stochastic uncertainty**, because the two largest sources of individual-level
variability are suppressed by construction: contact degree is fixed (`N-02`) and stage durations are
deterministic (`D-01`). Parameter uncertainty in `beta` alone would very likely dominate the reported
intervals. Ensemble bands must be labelled as stochastic replicate variation and never as confidence,
credible or prediction intervals (`E-01`).

### 11.2 Bookkeeping: done well

Several details are handled better than is typical (`E-04`). Failed replicates are retained as failed
and never become zero observations. Summary cells carry an explicit semantic — `observed`,
`structural_zero`, `carried_forward`, `outside_metric_horizon`, `non_contributor` — so a missing
incidence value is distinguished from a real zero and prevalence is not fabricated beyond the simulated
horizon. Requested, planned and actual worker counts are recorded separately with `sequential_fallback`
flagged as an execution diagnostic. Matched comparison refuses to proceed unless seed, horizon and the
M2, M3 and M4 parent hashes all agree.

Two gaps. Default quantiles are 2.5% and 97.5% computed by linear interpolation with **no minimum-
replicate guard**, while the documented demonstration ensembles use two or three seeds — at which point
the reported "95% band" is essentially the observed minimum and maximum (`E-02`). And paired scenario
comparison emits per-seed differences without any distributional summary, so the natural inferential
object for a scenario contrast — a central difference with an interval — is left to the consumer
(`E-03`). To the project's credit, common-random-number decay is diagnosed explicitly rather than
ignored: the comparison records `event_path_divergence_may_break_later_coupling` and claims true
coupling only where stream keys and event paths remain equal.

---

## 12. Calibration and identifiability

### 12.1 What the calibration framework is

`calibration.py` provides two harnesses. `run_synthetic_recovery` hides a reporting-delay parameter,
generates target observations under a fully detecting observation configuration, searches with Optuna,
and re-checks the recovered value on fresh held-out seeds. `run_beta_recovery` profiles a generic
transmission parameter over a declared candidate grid and additionally profiles it under altered
ascertainment and altered route weights.

**This is correctly scoped and correctly labelled** (`C-01`). The docstring states it is not calibration
to Jersey surveillance data; every trial is retained (`all_trials_retained: True`); and the diagnostics
record `real_jersey_data_used: False`. `docs/architecture.md` states plainly that the harness "does not
identify beta separately from contact intensity." The confounding profiles are, in effect, a
deliberate identifiability probe rather than a fitting exercise, which is the right thing to build first.

### 12.2 Calibration is not validation, and v1 has neither for Jersey

The distinction must be stated without softening. **No Jersey calibration exists.** The 22 registered
sources are demographic, educational, labour-market, regulatory and port-traffic aggregates; not one is
a case notification, testing, serology, hospitalisation or excess-mortality series. There is therefore
no Jersey epidemiological observable in the repository against which any transmission parameter could be
fitted (`V-02`).

Layered on that is the structural non-identifiability described in Section 7.3: even with a target
series, the product `beta × route_multiplier × edge_weight × edge_count` contains two free multiplicative
parameters over the same quantity, so a fit would return one point on a ridge (`C-02`). Hazelbag et al.
(2020), reviewing calibration of individual-based models across HIV, tuberculosis and malaria, found
that fewer than half of the studies they examined used reproducible, non-subjective calibration methods
and emphasised that policy-facing individual-based models should report uncertainty in both parameters
and predictions. JOS v1 meets the reproducibility half of that standard comprehensively and does not yet
attempt the uncertainty half.

A methodological point on the objective (`C-03`): the loss is an unweighted sum of squared differences in
daily reported counts, which is an implicit homoskedastic Gaussian likelihood on count data whose
variance grows with the mean, and the search returns a point with no interval and no goodness-of-fit
test. Adequate for demonstrating exact recovery of a hidden integer delay; insufficient for inference.
Because truth and candidate share the same generative model, network and population, the demonstrated
recovery is also over-precise relative to any real fitting problem — a well-posed mis-specification arm
would be the natural next test.

**This is not a release failure.** The intended claims are bounded to synthetic recovery, and the
infrastructure — trial retention, held-out checking, confounding profiles, hashed artifacts — is exactly
what an eventual real calibration would need.

---

## 13. Validation status

The five distinct activities must be separated, because conflating them is the most common way a
simulation study over-claims.

| Activity | Status in JOS v1 | Evidence |
|---|---|---|
| **1. Software verification** | **Present, extensive** | 80-test suite, strict typed schemas, `ruff`, targeted `mypy`, dependency lock check, tamper-detection tests |
| **2. Scientific / model verification** | **Present, strong** | `scientific_verification.py` re-derives conservation, daily-flow, event-to-aggregate and cumulative reconciliation from persisted artifacts (`V-01`) |
| **3. Calibration** | **Infrastructure only** | Synthetic recovery with `real_jersey_data_used: False` (`C-01`); no Jersey target registered (`C-02`) |
| **4. Retrospective validation** | **Absent** | No Jersey epidemiological series in `data/sources.yaml` (`V-02`) |
| **5. Prospective validation** | **Absent** | No forecast facility and no predictive claim anywhere in the repository |

### 13.1 Internal verification does strengthen scientific reliability — with one caveat

Model verification in JOS is not decorative. Artifact verification re-reads the persisted tables and
re-derives the science: the compartment sum must be constant across the horizon; new infections must
equal local plus imported; cumulative totals must equal the running sum of local, imported and seeded;
the parish, age and route tables must each sum to the matching daily flow on every date; the
transmission-event table must reconcile to the daily flows by source kind; and the attribution
diagnostics must match the event table. Files are checked by size and SHA-256 first and paths are
constrained to the artifact directory. Travel verification does the same and additionally defeats
logical tampering that updates the manifest checksum (`T-32`).

This materially raises confidence that **what the artifacts say is what the model did**. It says nothing
about whether what the model did resembles Jersey — that is validation, and it is absent.

The caveat is finding `X-01`: **three diagnostics assert rather than measure.** The occupational
double-counting audit tests institutional staff for primary jobs in the very list from which those rows
were removed, so its reported zero is structurally guaranteed and the outer diagnostics dictionary
additionally hardcodes zero (`N-25`); `repeated_edge_rate` is set to 1.0 without measurement for routes
declared "fixed", including `workplace_team`, whose executed edge set in fact changes daily with
attendance (`N-15`); and a declared housing-proportion tolerance is never applied to anything
(`POP-13`). The underlying behaviour is acceptable in each case, but presenting an assertion as an
observation is precisely the failure mode internal verification exists to exclude, and it should be
corrected because the credibility of the whole apparatus rests on that distinction.

### 13.2 The unexercised regime

**No full-population, full-horizon epidemic has ever been executed** (`V-03`). The recorded full-scale
runs are a two-day generic smoke producing 19 events (10 seeded, 9 local, 0 imported) at 73.28 seconds
and 911 MB peak RSS, and a seven-day scaled-travel smoke at 174.38 seconds and 1.24 GB. The default run
configuration is 30 days; the school calendar raises outside its reference year, capping a run at 360
days from the default start (`N-19`); and literal source-scale travel execution is bounded to about 79
days (`T-04`). Behaviours that appear only at epidemic scale — peak dynamics, susceptible depletion,
waning-driven oscillation, saturation of the sampled travel routes — have not been observed, so neither
their plausibility nor the computational feasibility of observing them is established.

### 13.3 Datasets and events that could support external validation

The following are named as candidate targets, not as available data; each would require registration
through the existing source pipeline with the same provenance discipline.

- **Jersey COVID-19 surveillance (2020–2022):** case notifications with testing volumes, and the
  documented border-testing regime. The single most valuable target, because it exercises the travel
  layer, the observation layer and the intervention layer simultaneously, and because Jersey's
  well-defined border makes importation unusually observable.
- **Seroprevalence surveys**, if any were conducted in Jersey: these constrain cumulative infection
  independently of ascertainment, and so break part of the ascertainment-transmissibility confounding.
- **Influenza and RSV sentinel surveillance:** multi-season data supporting a seasonality test and a
  recurring-epidemic test that the waning mechanism could be assessed against.
- **Care-home outbreak records:** institution-level outbreak sizes would test the closed-setting
  structure directly, and are the natural check on `POP-09`, `POP-10` and `N-10`.
- **School absence data:** an indirect but independent check on school-route intensity and term-time
  gating.
- **Ports of Jersey monthly series:** would replace the invented seasonality shape with an observed one
  (`T-08`), a small and immediately achievable improvement.

The natural first external test is **retrospective reconstruction of a known Jersey outbreak** —
fitting only ascertainment and a single transmission intensity, holding the structure fixed, and
reporting how much of the observed epidemic shape the synthetic structure reproduces without further
tuning.

---

## 14. Provenance and reproducibility

Evaluated **as a scientific reproducibility system** rather than as software infrastructure, this is the
strongest aspect of the project, and it exceeds normal practice in computational epidemiology (`P-01`).

**Evidence classification.** The repository uses `observed`, `derived`, `regulatory_minimum`,
`scenario_assumption`, `structural_assumption` and `synthetic`. This is a better-adapted taxonomy than
the generic alternative because `regulatory_minimum` captures something real — the Care Commission
staffing ratios are floors, not observed rosters, and treating them as observations would be a
category error the classification prevents (`STA-04`). The one gap relative to the classification
proposed in the review brief is that there is no `literature_prior` class, and correspondingly no
parameter in v1 is justified by reference to published estimates; values are either observed, derived
from observations, or declared assumptions. That is internally consistent, and it is also why several
parameters that could be literature-anchored (stage durations, indoor:outdoor ratio, test sensitivity
profile) currently are not.

**Source registry.** 22 sources with publisher, URL, reference period, licence, acquisition method and
SHA-256; every snapshot re-hashed at build time with a mismatch raising `DataBuildError`. PDF-only
sources are paired with narrow manual-transcription fixtures carrying an `evidence_source_id` back to
the primary document — an honest and auditable way to handle evidence that exists only in prose tables.

**Transformation transparency.** Canonical rows carry `transformation_id`, so a derived quantity names
the operation that produced it (`age_sex_raking_to_2024_marginals_v1`). Suppressed cells are preserved as
censored with an explicit upper bound rather than imputed. Published rounding is retained. Source
conflicts are surfaced as warnings rather than resolved silently.

**Run identity.** Separate hashes carry distinct meanings — configuration, scenario, latent outcome and
artifact bundle — so a change of presentation can be distinguished from a change of science. Parent
logical hashes are recorded and re-checked, the engine commit and a dirty-worktree flag are stored, seeds
are explicit and ordered, and the dependency lock is verified. The verification archive re-checks parent
hashes so a stale parent cannot be presented as current.

**Determinism.** The population and network layers use hash-derived permutations rather than a mutable
RNG stream, which makes reproducibility independent of call order — a stronger guarantee than seeding
alone provides.

Against this, three gaps in the provenance surface itself (`P-02`), each small but each undercutting the
completeness claim: the nine travel route edge weights are hard-coded literals absent from both
provenance tables while being direct per-edge beta multipliers (`T-20`); the school-calendar provenance
block is keyed on the configured year rather than verified against the registered snapshot, so a
customised calendar inherits an official `source_id` it never consulted (`N-18`); and two demonstration
seasonality profiles cite a registered `source_id` for an invented monthly shape (`T-08`). Two ingested
evidence items are also silently discarded (`STR-06`, `POP-06`), and the housing weights are literals
rather than reads from the canonical table that holds the same values.

The relevant external benchmark is the reproducibility and transparency framework of Pokutnaya et al.
(2023) for computational infectious-disease models. JOS v1 satisfies the substance of it — versioned
inputs, hashed artifacts, declared parameters, deterministic reruns, machine-checkable verification —
more completely than most published models do.

---

## 15. Jersey-specific realism

### 15.1 What v1 represents well

- **Population scale and structure.** 104,540 agents, one per resident, with age, sex and parish
  reconciled exactly to Statistics Jersey controls. For an island of this size, a one-to-one agent
  population is both feasible and the right choice: no scaling artefacts, and institution-level
  outbreaks are representable at their true absolute size.
- **St Helier work centralisation.** Anchored to the observed 66/13/21 destination split and reconciled
  to within one percentage point (`STR-10`) — the correct treatment of the island's most distinctive
  daytime feature.
- **Commuting mode structure.** Conditional commute profiles are used where published (St Helier
  resident and worker: 69% walk, 24% car; rural resident working in town: 75% car, 9% cycle, 8% bus),
  with a car-access constraint linking household car ownership to mode.
- **The care sector as a distinct structure.** Separate resident and staff routes, regulatory ratios
  from the Care Commission standards, and a correctly prevented double-count between institutional and
  ordinary employment (`STA-01`).
- **Border connectivity as a first-class mechanism.** Air and sea streams are separate, anchored to
  observed movements, and the border-measure lifecycle models turnaround delay as a real loss channel.
  For an island, importation is not a boundary condition but a central mechanism, and JOS treats it that
  way.
- **A genuinely closed system.** Jersey has exactly two ports of entry, so the arrival stream is close to
  a complete accounting of importation — a property few geographies offer and one that makes the island
  an unusually good validation setting.

### 15.2 What is missing or degenerate

- **Daytime school geography does not exist.** Every school resolves to `school_parish = 'St Helier'`,
  and all 1,972 school staff inherit that parish (`STR-02`). There is no catchment, so household
  clusters and school clusters do not overlap — removing exactly the local reinforcement that drives
  parish-level heterogeneity in a small island.
- **The parish transport gradient is inverted** relative to its own documented definition (`POP-07`),
  so parish-level car-access and mode geography outside St Helier should not be quoted.
- **No sub-parish geography.** St Helier holds 34.7% of the population as one undifferentiated unit
  (`POP-12`). No neighbourhood structure, no coordinates, no adjacency.
- **The hospital is absent as a setting.** The public-sector universe is partitioned into units of at
  most 25 employees (`STR-07`), so the island's most consequential workplace in a respiratory outbreak
  has no representation, and there is no healthcare-worker route.
- **Care-home realism is compromised on three axes simultaneously**: residents too young (`POP-10`),
  homes equal-sized so institutional outbreak-size variance is eliminated (`POP-09`), and residents
  exposed to the general community route at free-living rates (`N-10`). Staff serve exactly one home,
  so the between-care-home staff bridge — one of the best-documented transmission pathways between care
  homes during COVID-19 — is structurally absent (`STA-05`).
- **Tourism realism is thin beyond the arrival count.** Visitor age is uniform 1–90 (`T-24`),
  accommodation stock is a hard-coded 32 synthetic units per parish allocated in proportion to household
  counts rather than to accommodation supply (`T-23`), party members draw accommodation and stay length
  independently so parties are not co-located (`T-21`), and the monthly seasonality shape is invented
  (`T-08`).
- **No further-education setting** for the 16–18 age band, although Highlands College appears in a
  registered source universe and its lecturers are inside the FTE control that staffs the model's
  schools (`STR-04`).

### 15.3 A Jersey-specific dynamic worth naming: critical community size

At about 104,540 residents, Jersey sits in the population range where stochastic fadeout and
reintroduction, rather than deterministic endemic dynamics, govern the persistence of an
immunising infection. This is the classic critical-community-size regime identified by Bartlett (1957)
and analysed by Keeling and Grenfell (1997), and it is precisely the regime in which importation and
stochasticity matter most — which is what makes Jersey scientifically interesting as a modelling
subject and JOS's explicit, port-anchored importation layer well matched to it.

Two v1 properties currently limit how much can be said in that regime. Suppressed heterogeneity
(`N-02`, `D-01`) biases extinction probability, which is the central quantity; and the unexercised
long-horizon regime (`V-03`, `N-19`) means the persistence dynamics have never been observed. Both are
tractable, and together they define what would make JOS a genuinely distinctive scientific instrument
rather than a well-built general-purpose simulator applied to Jersey.

---

## 16. Scientific strengths

Stated plainly, and separately from the limitations, because a review that lists only faults
misrepresents the object.

1. **Provenance as a scientific instrument** (`P-01`, `DP-01`). Refusing to impute suppressed cells,
   preserving published rounding, surfacing source conflicts, and carrying `transformation_id` on every
   derived row is a standard of evidence handling higher than most published epidemic models meet.
2. **Enforced separation of latent truth from observation** (`O-01`). The layer cannot conflate
   infections with cases, and the enforcement is executable rather than conventional.
3. **Verification that re-derives rather than re-asserts** (`V-01`). Conservation, flow reconciliation
   and event-to-aggregate reconciliation are recomputed from the persisted artifacts, so an artifact
   that passes verification has demonstrably internally consistent science.
4. **Genuine route separability** (`N-01`, `N-05`). Eleven routes, nested-route double counting reduced
   to exactly zero pairs, and a test asserting byte-identical snapshots for retained routes when a
   family is removed. This makes route-ablation experiments well founded.
5. **Order-invariant attribution with retained evidence** (`D-05`). The competing-candidate set and its
   hazards are preserved, so attribution is auditable rather than opaque.
6. **A correct solution to a hard identity problem** (`T-09`, `T-10`). Runtime slot reuse with
   event-time identity binding, tested against deliberate map mutation.
7. **Non-retrocausal intervention lifecycle with an exactly neutral baseline** (`I-03`). The clean
   counterfactual is what makes matched-seed comparison meaningful.
8. **Honest claim discipline throughout** (`X-03`). Demonstration parameters labelled as assumptions,
   `real_jersey_data_used: False` recorded in artifacts, passenger movements never presented as unique
   tourists, unimplemented mechanisms recorded as deferred rather than filled with plausible numbers.
9. **Explicit missing-value semantics in ensembles** (`E-04`). Distinguishing a structural zero from an
   unobserved value from a non-contributing replicate is a detail most implementations get wrong.
10. **Reproducibility independent of call order.** Hash-derived permutations rather than mutable RNG
    streams give a stronger determinism guarantee than seeding alone.

---

## 17. Limitations

Organised as the review brief requires. Every item is tied to implementation evidence; the finding
identifiers point to the full entry in Section 18.

### 17.1 Data limitations

- No household size distribution exists in the registry; only the mean and the one-person share
  constrain household sizes (`POP-04`).
- No communal establishment size distribution, so homes are equal-sized within category (`POP-09`).
- No care-home resident age profile, so the age ramp is invented (`POP-10`).
- No employment-by-age headcount control, so employment propensity is a structural weight whose realised
  rates differ substantially from the declared values (`STR-05`).
- No sector-by-age control, so no sector carries an age profile (`STR-08`).
- No multiple-job-holding rate; 0.07 is an unanchored constant with a clear bridging mechanism
  (`STR-12`).
- No monthly visitor profile, so travel seasonality is an invented shape (`T-08`).
- No visitor demographic profile; age is uniform 1–90 (`T-24`).
- No accommodation-stock source; 32 synthetic units per parish, allocated by household counts (`T-23`).
- No Jersey epidemiological series of any kind (`V-02`).
- Two ingested evidence items are never consumed (`STR-06`, `POP-06`).
- The work-from-home level is a 2021-census pandemic-period measurement (`STR-09`).
- The two school-staffing FOI releases are mutually inconsistent and only one is used (`STA-02`); the
  control's universe excludes independent schools whose staff are nonetheless drawn from it (`STA-03`).

### 17.2 Parameter limitations

- All disease parameters are demonstration assumptions, correctly labelled (`configs/diseases/`).
- Route relative weights are unanchored structural assumptions and are redundant with the M5 route
  multipliers over the same product (`N-22`, `D-09`).
- The indoor:outdoor ratio of about 1.9 is low relative to the direction of the outdoor-transmission
  literature (`D-09`).
- Nine travel route edge weights are hard-coded literals outside the provenance surface (`T-20`).
- Arrival prevalence is a free dial and every visitor-driven result is approximately linear in it
  (`T-19`).
- The FTE-to-endpoint ratio (0.8) and care shift-coverage multiplier (2.0) are unanchored, with
  validated ranges spanning a factor of two or more (`STA-02`, `STA-04`).
- Transmission parameters are structurally non-identifiable from the system's own outputs (`C-02`).

### 17.3 Structural model limitations

- No individual-level contact heterogeneity, therefore no overdispersion or superspreading (`N-02`).
- Deterministic stage durations; the generation interval is a point mass (`D-01`).
- No presymptomatic infectiousness; constant infectiousness while infectious (`D-02`).
- Waning returns agents to full susceptibility with no partial immunity (`D-03`).
- No severity, hospitalisation or mortality pathway (`D-07`).
- Care residents are not excluded from the general community route (`N-10`).
- Workplace size tail truncated at 173 employees; no hospital as a setting (`STR-07`).
- School type is nearly perfectly confounded with pupil age (`STR-01`).
- Care staff serve exactly one home; 133 of 164 communal establishments receive no staff at all
  (`STA-05`).
- Teachers are bound to a single class, so the secondary-school between-class bridge is weak (`STA-06`).
- No further-education setting (`STR-04`).
- Reduced-scale modes delete whole institution categories rather than scaling them (`POP-11`).

### 17.4 Behavioural assumptions

- Adherence is drawn per route rather than per person, removing the fully non-adherent tail (`I-01`).
- No behavioural substitution or displacement; all multipliers bounded in [0, 1] (`I-02`, `T-27`).
- No adherence fatigue or time-varying compliance.
- Work-from-home is binary (5 days or 0) and allocated uniformly at random across sectors (`STR-09`).
- Vaccination reaches only current susceptibles (`I-04`).
- Travel parties are not co-located: members draw accommodation and stay length independently (`T-21`).
- Visitor contact intensities are unanchored to any empirical measurement (`T-20`).

### 17.5 Geographic limitations

- Parish is the finest spatial unit; no sub-parish geography exists anywhere (`POP-12`).
- Every school resolves to St Helier; there is no catchment (`STR-02`).
- The parish no-car gradient is inverted relative to its documented definition (`POP-07`).
- Household type composition is identical in every parish (`POP-08`).
- Community contacts are same-parish only, so cross-parish mixing runs solely through workplaces and
  transport.
- The terminal resident pool is hard-coded to St Helier although the airport is in St Peter (`T-13`).
- Visitor accommodation is allocated by household counts rather than accommodation supply (`T-23`).

### 17.6 Validation limitations

- No retrospective validation (`V-02`).
- No prospective validation.
- No Jersey calibration (`C-02`).
- No full-population, full-horizon epidemic has ever been executed (`V-03`).
- No demonstration that per-agent contact structure is consistent with any contact survey (Section 6.4).
- All integration tests run at a scale where the institutions that matter do not exist (`X-02`).
- Three diagnostics assert rather than measure (`X-01`).

### 17.7 Observation limitations

- The onset anchor is decoupled from the natural history; in the shipped configuration detection precedes
  infectiousness (`O-02`).
- Symptomatic status is uncorrelated with infectiousness (`O-03`).
- The per-day ascertainment fraction mixes cohorts (`O-04`).
- No test-negative or testing-capacity structure; detection is a simple thinning.
- Travel runs emit empty resident parish, route and age stratifications (`T-26`).
- Positive arrival tests returned after departure are excluded from reported yield (`T-18`).

### 17.8 Uncertainty limitations

- Ensemble bands cover network, transmission and observation stochasticity only (`E-01`).
- No parameter uncertainty propagation anywhere in the system.
- No structural uncertainty representation; no multi-model comparison.
- Extreme quantiles are computed from very small ensembles with no minimum-replicate guard (`E-02`).
- No distributional summary of paired scenario differences (`E-03`).
- Common-random-number coupling decays after trajectories diverge — correctly diagnosed, but it means a
  single seed-pair difference is not a clean contrast (`E-03`, `T-33`).
- Suppressed heterogeneity (`N-02`, `D-01`) narrows even the stochastic component.

### 17.9 Computational limitations

- Full-scale network construction takes about 73 seconds at roughly 0.9 GB peak RSS; the seven-day
  travel epidemic took about 174 seconds at 1.24 GB (`docs/progress.md`).
- The materialised-episode limit of 200,000 caps literal source-scale travel execution at about 79 days
  (`T-04`).
- The school calendar raises outside its reference year, capping runs at 360 days from the default start
  (`N-19`).
- Ensembles regenerate the full network per replicate with no parent-artifact caching, so replicate cost
  is dominated by network construction rather than by disease dynamics.
- Fixed daily timestep; no sub-daily resolution (`D-08`).

---

## 18. Findings table

128 findings. Ordered by severity, then by identifier. `Consequence` states whether the finding
invalidates results or limits interpretation, followed by the primary outputs affected.

| Finding | Classification | Component | Consequence | Recommendation |
|---|---|---|---|---|
| `C-02` | MAJOR LIMITATION | Calibration / identifiability | Limits interpretation absolutely for parameter estimates, and correctly so given the declared scope. Affects: Every parameter value; | Reduce the parameter set to one identifiable per-route intensity, register a Jersey surveillance series as a calibration target, and adopt a likelihood-free or Bayesian scheme that returns a... |
| `D-01` | MAJOR LIMITATION | Disease model / stage durations | Limits interpretation. Affects: Peak timing and height, doubling time, all ensemble quantiles, extinction probability, and any implied R or generation time. | Replace with gamma or lognormal stage durations (Starsim provides the distributions) and expose the shape as a scenario parameter; |
| `D-02` | MAJOR LIMITATION | Disease model / natural history | Limits interpretation. Affects: Case isolation and household quarantine effect sizes; | Add a presymptomatic infectious sub-state and a relative-infectiousness profile, and couple asymptomatic status to both infectiousness and detection probability. |
| `D-03` | MAJOR LIMITATION | Disease model / immunity | Limits interpretation. Affects: Long-horizon incidence, endemic and oscillatory behaviour, cumulative infection totals, attack_rate (see D-04), and the interpretation of any... | Add a partial-immunity parameter applied to rel_sus on waning, and either lengthen the default immunity duration or disable waning by default so the demonstration configuration is not implicitly an... |
| `D-04` | MAJOR LIMITATION | Disease model / output semantics | Limits interpretation, and specifically invalidates reading the column as a proportion of the population infected. Affects: daily_epidemic.attack_rate; | Rename to cumulative_incidence_per_capita and add a distinct ever_infected_fraction computed from unique agent identities; |
| `D-09` | MAJOR LIMITATION | Transmission semantics / setting differentiation | Limits interpretation. Affects: All route shares; | Set an explicit, literature-referenced default indoor:outdoor ratio and collapse the duplicate route-scaling parameters into one calibrated per-route intensity (see N-22). |
| `E-01` | MAJOR LIMITATION | Ensembles / uncertainty quantification | Limits interpretation. Affects: Every quantile band, every interval, every uncertainty statement derived from ensemble_summary; | Add a parameter-ensemble layer that draws from declared prior ranges over beta, stage durations, route weights and ascertainment, and report a variance decomposition separating stochastic from... |
| `I-01` | MAJOR LIMITATION | Intervention framework / adherence semantics | Limits interpretation. Affects: All scenario comparisons for case_isolation, household_quarantine, school_closure, community_reduction, care_home_protection, masking and... | Draw one adherence value per (intervention, agent) and reuse it across routes and dates, exposing route-level variation as a separate explicit parameter if it is wanted. |
| `I-02` | MAJOR LIMITATION | Intervention framework / behavioural response | Limits interpretation. Affects: Every intervention comparison and route-shift table; | Add an explicit compensatory-contact parameter (a fraction of suppressed contact reappearing on named routes), allow selected multipliers above one behind a beta guard, and state the attenuation-only... |
| `N-02` | MAJOR LIMITATION | Degree distribution | Limits interpretation. Affects: All ensemble quantiles and prediction intervals (ensemble.py outputs), probability-of-extinction and time-to-detection statistics, and any statement... | Add a per-agent lognormal or gamma activity multiplier applied to community (and optionally transient/bus) contact counts, and a non-degenerate infectious-period distribution; |
| `N-03` | MAJOR LIMITATION | Contact budget / calibration plausibility | Limits interpretation, and specifically invalidates reading the default parameter set (parameter_set_id 'respiratory-demo-v0.1') as a... Affects: Peak timing and height, doubling time, final size, R0/Rt implied by a parameter set, all route-share outputs, and the interpretation of any... | Add an aggregate multiplex diagnostic to the M4 artifact: per-agent total daily degree and weighted budget (mean, median, p90, p99, max) by age band and day type, plus the realised whole-population... |
| `N-04` | MAJOR LIMITATION | shared_vehicle route | Limits interpretation. Affects: Household attack rates, the household share of route-attributed transmission, any 'transport' route share (which is carried entirely by `bus`), and... | Either (a) rename/reclassify the route as a weekday within-household exposure amplifier and drop it from any 'transport' aggregation, or (b) add a bounded non-household carpool mechanism (e.g. |
| `N-07` | MAJOR LIMITATION | Community mixing structure | Limits interpretation. Affects: Age-band incidence and attack-rate outputs, age-targeted intervention effects (school closure, shielding), and any statement about who infects whom. | Reformulate as a symmetric contact-rate matrix with reciprocity enforced (build the target distribution as M_ij * N_j normalised, or symmetrise the realised matrix), and report the realised... |
| `N-08` | MAJOR LIMITATION | Community mixing geography | Limits interpretation. Affects: Parish-level incidence time series (a headline latent output), spatial spread timing, parish-targeted interventions, and the parish breakdown in... | Add a configurable cross-parish community mixing fraction (e.g. |
| `N-10` | MAJOR LIMITATION | Care route / community pool interaction | Limits interpretation, but severely for any care-home-focused analysis. Affects: Care-home attack rates and deaths-proxy outputs, care-setting-targeted intervention effects (interventions.py care-setting targeting), the care... | Exclude communal residents from the community participant pool, or give them a separate, much lower participation probability plus an explicit visitor route. |
| `N-11` | MAJOR LIMITATION | care_staff route | Limits interpretation. Affects: Care-home outbreak size and duration, cross-cohort spread within a facility, staff attack rates, care-setting intervention effects. | Add (a) a staff-staff clique or bounded ring per care setting, and (b) a periodic re-draw of the staff-cohort assignment representing shift rotation (e.g. |
| `N-12` | MAJOR LIMITATION | School routes | Limits interpretation. Affects: School route transmission share, 5-17 age-band incidence, school-closure intervention effect size, and the timing of the... | Add a bounded whole-school route (a ring or hashed pool across year groups within school_id, at a low weight), and allow at least the head_deputy role and a configurable fraction of teachers to hold... |
| `N-21` | MAJOR LIMITATION | bus route | Limits interpretation. Affects: Transport route transmission share, cross-parish spread (the bus route is one of the few cross-parish bridges - see N-08), incidence among bus... | Replace the cohort clique with a bounded ring or nearest-neighbour sampling within the cohort (degree ~4-6 rather than 23), which preserves the bridging role without the implausible intensity; |
| `N-22` | MAJOR LIMITATION | Weight -> beta composition | Limits interpretation. Affects: All route-share outputs, route-specific intervention effect sizes, calibration parameter estimates and their intervals, and any statement of the form... | Collapse the two multiplicative route parameters into one calibrated per-route intensity, or fix relative_weight as structural and calibrate only route_multipliers, and say which. |
| `N-23` | MAJOR LIMITATION | Route attribution | Limits interpretation. Affects: Route-specific transmission counts and shares (a headline latent output), route-effect diagnostics in intervention artifacts, and the calibration... | Report `successful_candidate_route_count` distribution alongside every route-share table so readers can see what fraction of infections were multi-candidate, and state in the results template that... |
| `O-02` | MAJOR LIMITATION | Observation model / intervention coupling | Limits interpretation, and specifically invalidates reading the shipped isolation scenarios as indicative of achievable isolation benefit. Affects: Every case_isolation and household_quarantine comparison (configs/scenarios/m7_case_isolation.yaml, m7_case_isolation_quarantine.yaml,... | Constrain the onset anchor to the disease timeline (sample onset relative to ti_infected rather than the infection date, or reject onset delays shorter than the latent period), extend the chronology... |
| `POP-04` | MAJOR LIMITATION | population_generator._new_household / _allocate_extra_roles / HOUSEHOLD_MAX_SIZE | Limits interpretation. Affects: Household-route incidence and secondary attack rates; | Ingest the census persons-per-household distribution (Statistics Jersey publishes it) and fit the extra-member allocation to it by largest remainder, exactly as household types already are. |
| `POP-05` | MAJOR LIMITATION | population_generator._assign_household_ages / _choose_adult_pair / MIN_GENERATION_GAP / MAX_COUPLE_AGE_GAP | Limits interpretation. Affects: Age-specific household attack rates; | Fit a parametric age-gap distribution (for example a truncated normal on the couple gap and on the mother-child gap) and use rejection sampling against it rather than only against the bound. |
| `POP-07` | MAJOR LIMITATION | population_generator._assign_housing_attributes (residual allocation) | Limits interpretation, and specifically invalidates parish-level car-access and transport-mode geography outside St Helier. Affects: Parish-level commute-mode composition; | Change the residual weight to parish_no_car_weights[parish] * households_in_parish[parish]. |
| `POP-09` | MAJOR LIMITATION | population_generator._build_communal_settings | Limits interpretation. Affects: Care-home and communal-route outbreak size distributions; | Impose a plausible size distribution (for example a log-normal fitted to the Care Commission register of registered bed numbers, which is public) subject to the observed establishment and resident... |
| `POP-10` | MAJOR LIMITATION | population_generator._communal_age_bounds / care-home age weight | Limits interpretation, and specifically invalidates any age-stratified care-home outcome. Affects: Care-home route attack rates by age; | Replace the linear ramp with an age profile from a registered source. |
| `POP-11` | MAJOR LIMITATION | population_generator._build_communal_settings; population_structure_generator._build_schools | Limits interpretation. Affects: Any comparison of results across modes; | State plainly that ci and scaled modes are computational smoke tests for institutional structure, not scaled representations, and that all institutional and school claims must come from full mode. |
| `STA-05` | MAJOR LIMITATION | staffing_generator._care_staff (setting filter and one-assignment rule) | Limits interpretation, and specifically invalidates any conclusion about between-care-home spread via staff or about staffed non-care... Affects: Care-staff route structure; | Add a staffing rule for detention, children's homes and other medical settings (regulatory ratios exist for several of these), and add an explicitly parameterised share of care staff holding... |
| `STR-01` | MAJOR LIMITATION | population_structure_generator._build_schools (pupil selection order) | Limits interpretation, and specifically invalidates any school-type-resolved or within-school age-resolved result. Affects: Age-specific school attack rates; | Replace the age-ascending sort with an age-stratified allocation: for each school type, derive a target age profile (Statistics Jersey and the CYPES school census publish pupils by year group) and... |
| `STR-02` | MAJOR LIMITATION | population_structure_generator._build_schools (pupil allocation and school_parish derivation) | Limits interpretation, and specifically invalidates every parish-resolved school or school-staff output and any parish-targeted school... Affects: school_parish and institution_parish (degenerate); | Either implement parish-weighted catchments (allocate school places to parishes by resident school-age population with a distance or adjacency weighting) or, if catchment data is unavailable, stop... |
| `STR-05` | MAJOR LIMITATION | population_structure_generator.employment_age_weight and the worker draw | Limits interpretation. Affects: Age-specific workplace and commute contact; | Ingest the Jersey labour-market economic-activity-by-age table (it is published in the same release already registered as labour_market_june_2025_pdf) and rake worker selection to age x sex marginals... |
| `STR-06` | MAJOR LIMITATION | population_structure_controls.workplace_cell_counts; population_structure_generator._assign_workplace_sectors | Limits interpretation, and specifically invalidates sector-by-size workplace results. Affects: Sector-resolved workplace outbreak sizes; | Use workplace_cell_counts as the primary allocation target: allocate workplaces to (sector, band) cells by largest remainder against the published cross-tab, then let the +40-undertaking discrepancy... |
| `STR-07` | MAJOR LIMITATION | population_structure_generator._allocate_sizes / BAND_LIMITS / _allocate_nonprivate_sizes | Limits interpretation. Affects: Workplace outbreak size distribution and its tail; | Draw within-band sizes from a right-skewed distribution (a truncated Pareto or log-normal fitted to the band boundaries) subject to the exact band job totals, and give the 50+ band a realistic tail... |
| `STR-09` | MAJOR LIMITATION | population_structure_generator (WFH assignment) | Limits interpretation. Affects: Workplace and workplace-team route contact volume; | Allocate WFH by sector using sector-specific remote-working shares (the labour-market release or a UK/Jersey occupational proxy), and expose the overall level as an explicit scenario parameter with a... |
| `T-03` | MAJOR LIMITATION | Scaling contract | Limits interpretation; Affects: daily_epidemic.parquet (visitor_infections, visitor_linked_local_acquisitions, resident_attack_rate, present_prevalence), daily_travel_route.parquet... | Report movements per resident-year alongside every travel result and add it to diagnostics. |
| `T-05` | MAJOR LIMITATION | Seasonality | Limits interpretation. Affects: daily_travel_population.parquet arrivals/airport_arrivals/ferry_arrivals, every downstream visitor and transmission table,... | Either normalise the profile in the explicit path as well, or refuse the combination of a non-neutral visitor_seasonality profile with a non-empty daily_arrivals schedule. |
| `T-11` | MAJOR LIMITATION | Resident outbound travel | Limits interpretation at the shipped scales, and it makes one reported column wrong rather than merely approximate. Affects: daily_travel_population.parquet (resident_away, resident_present, present_population), daily_epidemic.parquet (resident_away, resident_present,... | In apply(), recompute presence each day from the absence intervals (the helper _resident_present_on already exists and is correct) rather than only at construction; |
| `T-12` | MAJOR LIMITATION | Resident outbound travel | Limits interpretation and constrains the usable configuration space. Affects: travel_episodes.parquet (which still contains both episodes) versus visitor_events.parquet, daily_epidemic returning_resident_travel_acquisitions,... | Key the runtime maps on trip_id (which is already unique) rather than person_id, allow a list of episodes per resident, and add a regression test with two returns for one resident inside the horizon. |
| `T-13` | MAJOR LIMITATION | Visitor contact pathways | Limits interpretation. Affects: daily_travel_route.parquet (visitor_to_resident, resident_to_visitor, active_contacts, share_of_local_transmission), daily_epidemic.parquet... | Make the resident pool a rate: size it as visitor_community_contacts x (number of participating visitors) with a documented cap, or express it per visitor rather than per parish-day. |
| `T-14` | MAJOR LIMITATION | Border measures | Limits interpretation. Affects: visitor_events.parquet / travel_intervention_events.parquet (arrival_test_result, detected), quarantine_activated counts, compare_travel_runs... | Make sensitivity a function of time since exposure (e.g. |
| `T-19` | MAJOR LIMITATION | Arrival disease state | Limits interpretation. Affects: Every visitor-attributed and importation-attributed output: visitor_infections, visitor_to_resident transmission, arrival-test detections, resident... | Always report results as a function of arrival_infectious_fraction rather than at a single value; |
| `T-20` | MAJOR LIMITATION | Visitor contact pathways / provenance completeness | Limits interpretation. Affects: temporary_edges.parquet edge_weight, all travel-route transmission events, daily_travel_route share_of_local_transmission, every visitor-attributable... | Promote the nine weights to named TravelConfig fields with provenance entries and sensitivity_required=True, pass the real weight into _travel_spec, and add them to provenance_table(). |
| `V-02` | MAJOR LIMITATION | Validation status | Limits interpretation. Affects: Every epidemiological output. | Register a Jersey surveillance series (COVID-19 case and testing data, influenza sentinel surveillance, or a serological survey) and attempt retrospective reconstruction of a known Jersey outbreak as... |
| `V-03` | MAJOR LIMITATION | Validation status / computational exercise | Limits confidence rather than any specific published result, because no full-wave result has been published. Affects: Confidence in any full-wave result; | Run and archive a full-population, full-wave baseline ensemble with face-validity diagnostics (peak timing, final size, route shares, realised generation interval, per-agent contact budget) as the... |
| `X-01` | MAJOR LIMITATION | Diagnostics fidelity | Limits interpretation of the diagnostics artifacts. Affects: diagnostics.json and diagnostics.md staffing, route-persistence and housing blocks; | Compute each of the three from the realised artifact rather than from the construction rule, and adopt a convention that any diagnostic whose value is structurally fixed is labelled as an invariant... |
| `C-03` | MINOR LIMITATION | Calibration / statistical method | Limits interpretation; Affects: calibration trial tables and best_parameters. | Move to a count-appropriate likelihood (Poisson or negative binomial) and report intervals; |
| `D-07` | MINOR LIMITATION | Disease model / clinical outcomes | Limits scope, correctly declared. Affects: Any burden, healthcare-demand or mortality output (none exist). | Keep the columns explicitly typed as not-implemented rather than zero, so a consumer cannot read zero deaths as a modelled result. |
| `D-08` | MINOR LIMITATION | Disease model / temporal resolution | Limits scope. Affects: Within-day dynamics (absent); | Retain the daily step. |
| `E-02` | MINOR LIMITATION | Ensembles / summary statistics | Limits interpretation. Affects: ensemble_summary lower_value and upper_value; | Warn or refuse when the replicate count is below a documented minimum for the requested quantiles, and default to an interquartile summary for small ensembles. |
| `E-03` | MINOR LIMITATION | Scenario comparison / inference | Limits interpretation. Affects: matched_seed_comparison.parquet; | Add a paired-difference summary (median and quantiles of the per-seed difference) to the comparison artifact, and quote the coupling caveat verbatim wherever a paired difference is presented. |
| `I-04` | MINOR LIMITATION | Intervention framework / vaccination | Limits interpretation of vaccination scenarios. Affects: configs/scenarios/m7_vaccination.yaml and m7_combined.yaml results; | Offer vaccination irrespective of infection state (administering to non-susceptibles with no effect), and report both doses administered and doses that conferred protection. |
| `I-05` | MINOR LIMITATION | Intervention framework / mechanism | Limits interpretation only. Affects: Route-effect diagnostics (mean/min/max multiplier, effective edge counts); | State in the results template that route multipliers are per-contact risk multipliers, and report the effective edge count alongside the mean multiplier as the route-effects table already does. |
| `N-06` | MINOR LIMITATION | Route-overlap diagnostics | Limits interpretation of the diagnostic only. Affects: diagnostics.json / diagnostics.md route_overlap_matrix, manifest.diagnostics_status. | Evaluate the overlap matrix on all `snapshot_dates` (which already include a weekend and a school-holiday date) and add a containment metric plus a threshold (e.g. |
| `N-09` | MINOR LIMITATION | Community persistence semantics | Limits interpretation only. Affects: Community route transmission share, repeated_edge_rate / cross_day_jaccard diagnostics, the shape of the epidemic tail. | Either introduce a genuine refresh period for the regular component (rekey `mixed_edges` on a period index such as ISO-week // 4) or change the declared persistence to a value that describes a static... |
| `N-13` | MINOR LIMITATION | School routes / staffing | Limits interpretation only. Affects: School route transmission share, staff (adult) incidence attributed to the school family, school-closure counterfactual. | Add a per-school staff pool route (bounded ring across all staff of a school_id) at a modest weight, excluding pairs already in the class core. |
| `N-14` | MINOR LIMITATION | Communal setting coverage | Limits interpretation. Affects: Communal-resident incidence, any setting-level outbreak analysis, the care route's transmission share, and setting-targeted interventions. | Either widen the staffing layer to the two unstaffed 'care' types (or exclude them from care_resident so no unstaffed clique exists), and add a generic bounded 'other communal setting' route for... |
| `N-15` | MINOR LIMITATION | Persistence taxonomy / diagnostics fidelity | Limits interpretation of the diagnostics artifact only. Affects: diagnostics.json routes.workplace_team.repeated_edge_rate and cross_day_jaccard; | Compute repeated_edge_rate / cross_day_jaccard for every route from the actual snapshots rather than branching on the declared persistence label, and change workplace_team's declared persistence to... |
| `N-16` | MINOR LIMITATION | Adapter fidelity | Limits interpretation of the artifact schema only. Affects: structural_edges.parquet, snapshot_edges.parquet, route documentation. | Either pass persistence_days through to Starsim's edge `dur` where the engine supports it, or document the field in the artifact schema as descriptive metadata and record the actual refresh key per... |
| `N-17` | MINOR LIMITATION | Calendar semantics | Limits interpretation only. Affects: Daily incidence around Easter and early May; | Add a `public_holiday_dates` tuple to NetworkGenerationConfig, sourced from a registered Government of Jersey bank-holiday snapshot, and treat those dates as non-weekday for school, work and... |
| `N-18` | MINOR LIMITATION | Calendar provenance | Limits interpretation. Affects: diagnostics.json calendars.school_calendar_provenance; | Load the term/holiday periods from the registered snapshot via data_pipeline.load_source_registry (as staffing_evidence already does), verify the SHA-256, and fail if configured dates disagree with... |
| `N-19` | MINOR LIMITATION | Calendar horizon | Limits scope. Affects: Maximum simulable horizon; | Validate `start_date + duration_days - 1` against the configured calendar year at config construction so the failure is a clear setup error, and add multi-year calendar support (a mapping from year... |
| `N-20` | MINOR LIMITATION | Work calendar | Limits interpretation only. Affects: Workplace route transmission share, weekday-vs-weekend incidence contrast, workplace-targeted intervention effects. | Give M3 a distribution of remote days per week (0-5) by sector and expose it as a scenario parameter; |
| `N-24` | MINOR LIMITATION | Ring topology | Limits interpretation only. Affects: Workplace and school route transmission shares; | Optionally scale the contact parameter with log(venue size) or expose a size-elasticity parameter, and report the realised degree distribution by venue size in diagnostics so the flat profile is... |
| `N-25` | MINOR LIMITATION | Staffing diagnostics fidelity | Limits interpretation of the diagnostics artifact only. Affects: diagnostics.json staffing.occupational_staff_mapping; | Compute the audit against the RAW `jobs_by_agent` and the realised route participation (e.g. |
| `N-26` | MINOR LIMITATION | Adapter verification | Limits confidence rather than results; Affects: Everything that depends on the calendar: weekday/weekend incidence contrast, school-term effects, and the school-closure intervention baseline. | Add a test that runs a sim across a weekend and a term boundary and asserts, for each dynamic route and each simulated day, that the live `network.edges` p1/p2 set equals... |
| `N-27` | MINOR LIMITATION | household route | Limits interpretation only. Affects: Household attack rate by household size, household route transmission share, household_quarantine intervention effect. | Optionally attenuate the household edge weight with household size (e.g. |
| `O-03` | MINOR LIMITATION | Observation model | Limits interpretation only. Affects: Ascertainment fraction; | Once a symptom state exists in the disease model (D-02), derive the observation classification from it rather than drawing it independently. |
| `O-04` | MINOR LIMITATION | Observation model / output semantics | Limits interpretation of one column. Affects: daily_observed_cases.ascertainment_fraction and anything plotted from it. | Rename the column to detected_to_infected_same_day_ratio, or compute a cohort ascertainment by infection date. |
| `O-05` | MINOR LIMITATION | Observation model / numerical safety | Limits nothing in v1. Affects: Detected and reported case series. | Clamp or validate the product and raise when a weekday factor would carry a probability above one. |
| `P-02` | MINOR LIMITATION | Provenance completeness | Limits the strength of the provenance-completeness claim, not the results. Affects: provenance_table and resolved_parameter_provenance outputs; | Promote the travel weights and housing weights to provenanced configuration fields, verify calendar dates against the named snapshot, empty source_ids for invented shapes, and either consume or... |
| `POP-02` | MINOR LIMITATION | population_controls._build_full_age_sex_counts | Limits interpretation only. Affects: Age-specific incidence and any age-stratified severity or mortality reporting; | If Statistics Jersey publishes a 2024 five-year age structure, extend the raking to a five-year-by-sex table so the within-65+ composition is fitted rather than assumed. |
| `POP-06` | MINOR LIMITATION | population_generator._assign_housing_attributes | Limits nothing in v1 because the fields are unused; Affects: None currently. | Read the weights from controls.housing_controls; |
| `POP-08` | MINOR LIMITATION | population_generator (household parish allocation) | Limits interpretation of parish-level detail only. Affects: Parish-level household-route intensity; | If a parish-by-household-type table is available, rake the type allocation to it. |
| `POP-12` | MINOR LIMITATION | whole lane | Limits interpretation. Affects: Spatial spread pattern; | State the spatial resolution explicitly wherever parish-level maps or outputs are shown, and do not present within-St-Helier variation. |
| `POP-13` | MINOR LIMITATION | population_generator.TOLERANCES | Limits nothing; Affects: None currently. | Either wire the tolerance into _validate_generated as a real check on the dwelling, crowding and car-access proportions, or delete the constant so the tolerance table does not overstate what is... |
| `STA-02` | MINOR LIMITATION | staffing_generator._fte_endpoints; staffing_evidence.SchoolStaffingEvidence | Limits interpretation. Affects: School staff endpoint count; | Justify the 0.8 in the scope document or replace it with a registered headcount, and state explicitly why the 2025 universe is preferred over 2024 rather than leaving the 2024 values as unused... |
| `STA-03` | MINOR LIMITATION | staffing_generator._school_staff (allocation across school types) | Limits interpretation of school-type-resolved staffing. Affects: Staff-pupil contact intensity by school type; | Either restrict the CYPES-derived endpoints to government and special schools and add a separate (even scenario-based) independent-school staffing assumption, or state the ratio distortion... |
| `STA-04` | MINOR LIMITATION | staffing_evidence.care_minimums / nursing_nurse_minimum; staffing_generator._care_staff | Limits interpretation. Affects: Care-staff route contact volume; | Keep the regulatory floor as the default but report care-staff results across the permitted coverage_multiplier range, and state in the scope document that care staffing is a regulatory lower bound... |
| `STA-06` | MINOR LIMITATION | staffing_generator._school_staff (class binding) | Limits interpretation of within-school structure only. Affects: Within-school between-class spread; | Make the class binding a covering assignment (allocate at least one teacher per class before distributing the remainder), and give secondary teachers membership of several classes within their year... |
| `STR-03` | MINOR LIMITATION | population_structure_generator._build_schools; data/processed/school_students.csv | Limits interpretation marginally. Affects: Age-specific school-route exposure at the range boundaries; | Ingest a pupils-by-single-year-of-age control if available and treat enrolment as a rate rather than a residual, so the build degrades gracefully instead of failing. |
| `STR-04` | MINOR LIMITATION | population_structure_generator (economic status assignment) | Limits interpretation. Affects: Contact and incidence in the 16-19 age band; | Register a further-education enrolment control and add a tertiary setting, or state explicitly that the 16-18 further-education population is out of scope. |
| `STR-08` | MINOR LIMITATION | population_structure_generator (sector allocation loop) | Limits interpretation of sector-by-age detail only. Affects: Sector-resolved age-specific attack rates; | State that sector carries no age information. |
| `STR-11` | MINOR LIMITATION | population_structure_generator.TOLERANCES['commute_share'] | Limits interpretation of mode-resolved commute results. Affects: Commute-mode composition; | Report the actual realised commute-mode deviations rather than only the pass/fail against a 6-point tolerance, and tighten the tolerance after fixing POP-07. |
| `STR-12` | MINOR LIMITATION | population_structure_controls.additional_job_rate | Limits interpretation. Affects: Workplace network connectivity between sites; | Register a multiple-job-holding rate from the labour-market release if published, and in the meantime treat 0.07 as a sensitivity parameter and report workplace-bridging results across a range (for... |
| `T-04` | MINOR LIMITATION | Apportionment / capacity gate | Limits interpretation only. Affects: diagnostics['movement_reconciliation'], benchmark outputs. | State in the report that 'reconciles exactly at stream_scale=1' is a property of the apportionment and the capacity gate, verified without epidemic execution. |
| `T-06` | MINOR LIMITATION | Seasonality | Limits interpretation of the config schema only. Affects: seasonality_schedule.parquet, seasonality_hash, config identity. | Collapse the Literal to the single implemented option, or read the field and implement both. |
| `T-07` | MINOR LIMITATION | Seasonality / numerical safety | Limits interpretation; Affects: temporary_edges.parquet edge weights, all travel-route transmission events, seasonality_schedule.parquet multipliers. | Validate the normalised multipliers against [minimum, maximum] and compute the guard from max over the horizon of route_beta * base_weight * normalised_multiplier. |
| `T-08` | MINOR LIMITATION | Provenance labelling | Limits interpretation. Affects: seasonality_schedule.parquet source_status column, provenance_table output, diagnostics['seasonality']. | Empty source_ids for invented shapes, or add a distinct 'shape_source_ids' / 'inspired_by' field so 'derived from' and 'loosely motivated by' cannot be confused. |
| `T-15` | MINOR LIMITATION | Resident outbound travel / importation timing | Limits interpretation. Affects: daily_epidemic.parquet returning_resident_travel_acquisitions and its timing, transmission_events with source_kind travel_imported, daily_high_risk... | Draw the acquisition time uniformly over the absence interval and set the arrival state accordingly (exposed with a partially elapsed latent period, or infectious), which the existing... |
| `T-16` | MINOR LIMITATION | Importation streams | Limits interpretation; Affects: daily_epidemic.parquet (new_infections, visitor_infections, resident_infections, returning_resident_travel_acquisitions), transmission_events... | Restrict generic imports to residents when explicit travel is active, and add a diagnostic reporting importation events per channel with an explicit warning when mode='both'. |
| `T-18` | MINOR LIMITATION | Border measures / surveillance reporting | Limits interpretation of surveillance-yield outputs only. Affects: compare_travel_runs positive_tests rows, daily_high_risk.parquet detections, travel_intervention_burden in run_travel_ensemble. | Report two series: results returned (all) and results actionable (episode_active). |
| `T-21` | MINOR LIMITATION | Visitor composition | Limits interpretation. Affects: temporary_edges.parquet on visitor_accommodation / visitor_host_household / visitor_transit, visitor_to_visitor transmission counts, cluster... | Draw accommodation, stay duration and (optionally) arrival state at party level and inherit them to members, keeping only the day-visitor/transport variation individual. |
| `T-22` | MINOR LIMITATION | Visitor composition | Limits interpretation of demo-scale runs only. Affects: travel_episodes.parquet travel_party_id group sizes, temporary_edges.parquet visitor_party and PRIVATE_RENTAL_CAR groups, visitor_to_visitor... | Report the realised party-size distribution in diagnostics alongside the configured one, so the gap is visible. |
| `T-23` | MINOR LIMITATION | Accommodation representation | Limits interpretation. Affects: visitor_population.parquet accommodation_id and home_parish, temporary_edges.parquet visitor_accommodation, any parish-level reading of visitor... | Register an accommodation-stock source (bed spaces by parish) if a geographic claim is ever wanted, and at minimum make the unit count configurable and scale it with expected occupancy. |
| `T-24` | MINOR LIMITATION | Visitor composition | Limits interpretation of age-stratified visitor output. Affects: visitor_population.parquet age/sex, observation_events.parquet age_band for visitors, high_risk_strata.parquet, daily_high_risk.parquet. | Either register a visitor age-sex profile, or drop age from visitor rows and mark visitor age-stratified output as not meaningful. |
| `T-25` | MINOR LIMITATION | Denominators | Limits interpretation. Affects: daily_epidemic.parquet (susceptible, exposed, infectious, recovered, present_prevalence, new_infections), run_travel_ensemble summaries of those... | Rename the mixed columns (present_susceptible, present_infectious, ...) or add resident-only equivalents, and document that present_prevalence is a whole-present-population quantity. |
| `T-26` | MINOR LIMITATION | Output completeness | Limits interpretation only; Affects: daily_parish.parquet, daily_route.parquet, daily_age.parquet in every non-trivial travel artifact. | Compute the resident parish/route/age stratifications inside the travel runner as well, or state in the manifest that these tables are structurally empty for travel runs so a consumer does not read... |
| `T-28` | MINOR LIMITATION | Border measures | Limits interpretation. Affects: travel_intervention_events.parquet traveller_vaccine_administered counts, visitor and resident susceptibility, resident incidence under a vaccination... | Extend coverage sampling and modifier synchronisation to returning residents, or rename the control visitor_vaccination_* so its scope is unambiguous. |
| `T-29` | MINOR LIMITATION | Documentation / dead code | Limits interpretation of the provenance table. Affects: provenance_table output and any report generated from it. | Correct the provenance_table string to the largest-remainder contract and delete _profile_counts. |
| `T-30` | MINOR LIMITATION | Output semantics | Limits interpretation of one exported column. Affects: temporary_edges.parquet edge_weight, temporary_network_hash (unaffected in kind, but the hashed value is the pre-intervention weight), any external... | Add an effective_weight column (or a per-endpoint quarantine factor) so the executed hazard is reconstructible from the table alone. |
| `TEST-01` | MINOR LIMITATION | tests/conftest.py; tests/test_population.py; tests/test_population_structure.py; tests/test_staffing.py; tests/test_c1_identity.py | Limits verification coverage, not results. Affects: Confidence in full-scale institutional and school behaviour rather than any specific output. | Add a full-mode (or a scaled mode chosen so every communal category survives) regression test that asserts the institutional inventory, the nurse-role count and the per-school-type age composition,... |
| `X-02` | MINOR LIMITATION | Test coverage | Limits verification coverage. Affects: Confidence in full-scale institutional behaviour and in calendar gating. | Add a full-mode institutional-inventory regression test and an in-simulation calendar-alignment test comparing live network edges against route_snapshot for the expected date. |
| `C-01` | VALIDATED / COHERENT | Calibration framework | Positive finding. Underpins: Calibration artifacts and their diagnostics. | Retain. |
| `D-05` | VALIDATED / COHERENT | Transmission semantics / attribution | Positive finding. Underpins: daily_route tables, route shares, route-effect diagnostics. | Retain, and always publish the candidate-count distribution alongside route shares so readers can see what fraction of events were multi-candidate. |
| `D-06` | VALIDATED / COHERENT | Transmission semantics / importation | Positive finding. Underpins: All incidence decompositions; | Retain. |
| `DP-01` | VALIDATED / COHERENT | data_pipeline.py | Positive finding. Underpins: All controls; | No change. |
| `DP-02` | VALIDATED / COHERENT | data_pipeline.py / population_structure_controls.py | Limits nothing material; Affects: Workplace counts, sector job totals, commute-mode shares. | Quote the three magnitudes (+40 undertakings, -10 jobs, +2 workers) rather than describing the non-reconciliation qualitatively. |
| `E-04` | VALIDATED / COHERENT | Ensembles / bookkeeping | Positive finding. Underpins: All ensemble and comparison artifacts. | Retain. |
| `I-03` | VALIDATED / COHERENT | Intervention framework / lifecycle | Positive finding. Underpins: All intervention runs and their comparison against baseline. | Retain. |
| `N-01` | VALIDATED / COHERENT | Route inventory | Positive finding. Underpins: Route inventory, per-route diagnostics, route-specific transmission counts, intervention route targeting. | No action. |
| `N-05` | VALIDATED / COHERENT | C2 nested exclusion | Positive finding. Underpins: Route-specific transmission shares for school and workplace families; | State in the technical report that the guarantee is structural (superset exclusion sets), not merely empirical on one date. |
| `O-01` | VALIDATED / COHERENT | Observation model | Positive finding. Underpins: All detected and reported case series; | Retain, and present it as the reference pattern: an ABM that structurally cannot conflate infections with cases. |
| `P-01` | VALIDATED / COHERENT | Provenance and reproducibility | Positive finding. Underpins: Every artifact and every claim traceable through it. | Retain, and close the three provenance-surface gaps in P-02 so the completeness claim is exact. |
| `POP-01` | VALIDATED / COHERENT | population_generator.py / population_schemas.py / starsim_adapter.py | Positive finding. Underpins: Every output. | No change. |
| `POP-03` | VALIDATED / COHERENT | population_structure_controls._scale / scaled_structure_targets | Positive finding. Underpins: Worker, pupil, workplace and job counts at every mode. | Make the choice of denominator explicit in the scope document; |
| `STA-01` | VALIDATED / COHERENT | staffing_generator._eligible_worker_ids; network_generator institutional_staff_ids filter and _occupational_staffing_audit | Positive finding. Underpins: Institutional route memberships; | No change. |
| `STR-10` | VALIDATED / COHERENT | population_structure_generator._assign_workplace_parishes / _destination_category | Positive finding. Underpins: Work-parish distribution; | No change. |
| `T-01` | VALIDATED / COHERENT | Empirical anchor | Positive finding. Underpins: All arrival-volume, episode-count, capacity and reconciliation outputs. | Retain. |
| `T-02` | VALIDATED / COHERENT | Apportionment | Positive finding. Underpins: daily_travel_population.parquet arrival counts, diagnostics['movement_reconciliation'], benchmark_travel_generation output. | Retain. |
| `T-09` | VALIDATED / COHERENT | Visitor representation / slot reuse | Positive finding. Underpins: All visitor-attributed transmission, incidence, detection and edge tables. | Retain. |
| `T-10` | VALIDATED / COHERENT | Identity binding | Positive finding. Underpins: transmission_events.parquet, travel_transmission_events.parquet, observation_events.parquet, detection_events.parquet, temporary_edges.parquet,... | Retain; |
| `T-17` | VALIDATED / COHERENT | Border measures | Positive finding. Underpins: visitor_events.parquet, travel_intervention_events.parquet, quarantine and testing counts in compare_travel_runs and run_travel_ensemble. | Retain. |
| `T-27` | VALIDATED / COHERENT | Border measures | Positive finding. Underpins: quarantine_activated counts, temporary_edges and resident edge weights under quarantine, all intervention comparisons. | Retain, and state the attenuation-only constraint whenever quarantine results are presented. |
| `T-31` | VALIDATED / COHERENT | Stream integrity | Positive finding. Underpins: daily_travel_population departures, diagnostics['departure_reconciliation'], the whole zero-travel equivalence fixture. | Retain. |
| `T-32` | VALIDATED / COHERENT | Reproducibility | Positive finding. Underpins: All travel artifacts. | Retain. |
| `T-33` | VALIDATED / COHERENT | Sensitivity and ensembles | Positive finding. Underpins: compare_travel_runs rows, ensemble summaries, sensitivity variants. | Retain. |
| `V-01` | VALIDATED / COHERENT | Verification | Positive finding. Underpins: Confidence in every persisted artifact. | Retain, and extend the same measure-rather-than-assert discipline to the three diagnostics identified in X-01. |
| `X-03` | VALIDATED / COHERENT | Model classification / claim discipline | Positive finding. Underpins: How the whole system should be described. | Retain. |

---

## 19. Claims JOS v1 can make

Each claim below is supported by repository evidence identified in this review. Suggested wording is
given because precision of wording is what keeps these claims defensible.

**1. Internally consistent synthetic epidemic experiments.**
> "JOS simulates epidemic dynamics in a synthetic population of 104,540 agents whose age, sex, parish,
> household-type, communal-resident, pupil, worker and workplace totals reconcile exactly to registered
> Statistics Jersey controls, and whose outputs are re-verified against conservation and reconciliation
> invariants at the artifact level."

**2. Controlled scenario comparison.**
> "Under the specified assumptions, and holding the population, network parents and random seed fixed,
> JOS quantifies the difference in simulated transmission between a baseline and an intervention
> scenario."
The matched-seed machinery, the exactly neutral baseline and the enforced parent-hash agreement make
this a genuinely controlled contrast (`I-03`, `E-04`).

**3. Mechanistic exploration of route structure.**
> "Disabling a contact-route family and re-running under an otherwise identical configuration isolates
> that route's contribution to simulated transmission within the model."
Supported by enforced separability (`N-01`).

**4. Route-specific simulated transmission pathways.**
> "Of simulated infections in this run, X% were attributed to the household route" — with the
> candidate-count distribution reported alongside, and the word *simulated* retained (`D-05`, `N-23`).

**5. Stochastic replicate behaviour.**
> "Across N replicates differing only in random seed, with the synthetic population and all parameters
> held fixed, simulated peak incidence ranged from A to B."
Never "the 95% confidence interval" (`E-01`).

**6. Structural provenance and reproducibility.**
> "Every input is registered with a checksummed snapshot and an evidence classification; every artifact
> carries the hashes of its parents, the engine commit, the dependency lock and the random seed; and any
> artifact can be independently re-verified, including against logical tampering that updates the
> manifest checksum."
This is the strongest defensible claim in the project (`P-01`, `T-32`).

**7. Correct handling of the infection/case distinction.**
> "JOS distinguishes latent infections from observed cases structurally, with separate infection, onset,
> detection and report dates, and conserves latent incidence independently of ascertainment" (`O-01`).

**8. Importation as an explicit, port-anchored mechanism.**
> "Arrival volumes are apportioned from 2025 Ports of Jersey passenger-movement totals — 720,842 air and
> 196,623 sea arrivals — reconciling exactly to the annual integer at unit stream scale."
Always with the movements-not-tourists qualification (`T-01`).

**9. Demonstrated parameter recovery in a synthetic setting.**
> "Where the data-generating process is the model itself, the calibration harness recovers a hidden
> reporting delay and a hidden transmission parameter, with all trials retained and held-out
> verification" (`C-01`).

**10. A reusable, auditable methods contribution.**
The combination of exhaustive provenance, enforced route separability, event-time identity binding under
slot reuse, and artifact-level scientific verification is a defensible methods contribution
independent of any epidemiological result.

---

## 20. Claims JOS v1 should avoid

**1. Any forecast or prediction of Jersey cases.** No validation, no calibration to Jersey data, no
forecast facility (`V-02`). Avoid "projects", "predicts", "expects", and any dated numerical
expectation.

**2. Validated estimates of intervention effectiveness.** Three mechanisms bias intervention benefit
upward — detection preceding infectiousness in the shipped configuration (`O-02`), per-route rather than
per-person adherence (`I-01`), and no behavioural substitution (`I-02`) — and none is quantified. Say
"simulated reduction under the specified assumptions", never "would reduce".

**3. Real-world *R* or *R*<sub>t</sub> values.** Beta is not identifiable separately from contact
intensity (`C-02`), contact structure has not been validated against any contact survey (Section 6.4),
and no *R* estimator exists in the codebase. Any implied *R* is a property of the assumption set.

**4. Causal attribution of actual historical transmission.** Route attribution is a hazard-weighted draw
among simultaneously successful simulated edges, over a route inventory of the model's own construction
(`N-23`, `D-05`). It cannot speak to how any real infection occurred.

**5. Complete uncertainty bounds.** Bands omit parameter and structural uncertainty entirely, and the
two dominant sources of individual-level stochastic variability are suppressed by construction
(`E-01`, `N-02`, `D-01`).

**6. Anything about real border-policy effectiveness.** Test sensitivity is state-based rather than
incubation-dependent, and is 1.0 in every shipped configuration (`T-14`); arrival prevalence is a free
dial (`T-19`); visitor-to-resident mixing does not scale with volume (`T-13`).

**7. Named-pathogen conclusions.** The disease module is deliberately pathogen-neutral and its
parameters are labelled demonstration assumptions. Do not describe results as applying to COVID-19,
influenza or any specific pathogen.

**8. Parish-resolved school or school-staff results, or parish transport geography.** Every school is in
St Helier (`STR-02`) and the parish no-car gradient is inverted (`POP-07`).

**9. School-type-resolved or within-school age-resolved results.** School type is nearly perfectly
confounded with pupil age (`STR-01`).

**10. Age-stratified care-home outcomes, or institutional outbreak-size tails.** Care residents are too
young (`POP-10`), homes are equal-sized (`POP-09`), and residents mix in the general community at
free-living rates (`N-10`).

**11. Sector-by-size workplace results, workplace outbreak-size tails, or hospital transmission.** The
published cross-tab is discarded (`STR-06`), the size tail is truncated at 173 (`STR-07`), and the
hospital is not represented.

**12. Elasticities or dose-responses with respect to arrival volume.** Resident-facing visitor pools are
absolute constants (`T-13`) and no shipped configuration preserves the real
traveller-to-resident ratio (`T-03`).

**13. "Attack rate" without qualification.** The column is cumulative infection episodes per capita and
can exceed one (`D-04`).

**14. Anything about between-care-home spread via staff, or about staffed non-care congregate
settings.** Cross-facility staff are structurally zero and 133 of 164 establishments are unstaffed
(`STA-05`).

**15. Superspreading, overdispersion, or the value of measures targeting high-contact individuals.**
The mechanism does not exist in the model (`N-02`).

**16. Any claim resting on results from `ci` or `scaled` mode for institutional or school questions.**
Those modes delete whole institution categories (`POP-11`).

**17. That the synthetic population represents identifiable Jersey residents or households.** It is a
latent modelling substrate with no sub-parish location and no coordinates (`POP-12`).

**18. That reported passenger figures represent unique visitors or tourists.** They are passenger
movements at the two ports (`T-01`).

---

## 21. Priority scientific next steps

Ordered by scientific value per unit of effort. Items 1–5 are corrections whose absence currently
constrains what can be said; items 6–10 are additions that would change what class of model JOS is.
The accompanying roadmap develops these into a programme.

**1. Exclude care-home residents from the general community route** (`N-10`). A route-membership filter.
It is the single highest-leverage correction in the review: it restores the epidemiological distinctness
of the model's most severity-relevant setting, and it is a small change.

**2. Constrain the symptom-onset anchor to the disease timeline** (`O-02`). Sample onset relative to
`ti_infected` rather than the infection date, extend the chronology check to require onset after the
latent period, and ship a demonstration observation configuration with a positive onset delay. Without
this, every shipped isolation scenario operates in an optimistic regime.

**3. Introduce contact-rate heterogeneity** (`N-02`). A persistent per-agent activity multiplier applied
to pooled-route degree, exposed as a parameter with a documented dispersion. Together with distributed
stage durations (item 4) this is what would let JOS speak to extinction probability, superspreading and
the variance of outbreak size — the quantities that matter most in a population of Jersey's size.

**4. Replace deterministic stage durations with distributions** (`D-01`) and report the realised
generation-interval distribution as a diagnostic.

**5. Fix the four specific structural defects that currently invalidate named outputs**: the school-type
age collapse (`STR-01`), the degenerate school parish (`STR-02`), the inverted parish no-car allocation
(`POP-07`), and the runtime resident-absence gap (`T-11`). Each is a localised change and each currently
requires a disclosure that would otherwise be unnecessary.

**6. Execute and archive a full-population, full-wave baseline ensemble** (`V-03`) with face-validity
diagnostics: peak timing and height, final size, route shares with candidate-count distribution,
realised generation interval, and per-agent daily edge counts by age band. This is the missing evidence
that the model behaves sensibly in its own intended regime.

**7. Demonstrate contact-structure plausibility against an empirical contact survey** (Section 6.4).
Compute per-agent daily contact-opportunity counts by age band from the artifacts and compare their
magnitude and age pattern against POLYMOD or CoMix. Either the comparison is reassuring and should be
published, or it is not and the route parameters need revisiting.

**8. Collapse the redundant transmission parameterisation** (`N-22`, `D-09`) to a single identifiable
per-route intensity, and set the indoor:outdoor ratio from the literature rather than by assumption.

**9. Add parameter-uncertainty propagation and a variance decomposition** (`E-01`). Until ensembles
sample parameters, no JOS interval can be presented as an uncertainty range.

**10. Register a Jersey epidemiological series and attempt retrospective reconstruction** (`V-02`). This
is the step that would move JOS from a verified synthetic framework to a partially validated one, and
it is the precondition for every stronger claim.

Three corrections that cost almost nothing and remove avoidable misreading risk: rename `attack_rate`
to reflect what it computes (`D-04`); promote the nine travel edge weights into the provenance surface
(`T-20`); and compute the three asserted diagnostics from realised artifacts (`X-01`).

---

## 22. Overall assessment

JOS v1.0 is a carefully constructed, scientifically coherent synthetic epidemic simulation platform
whose principal achievement is not any epidemiological result — it has produced none, and correctly
claims none — but the construction of an auditable chain from official published aggregates through a
reconciled synthetic population and a separable contact architecture to hash-verified, independently
re-derivable simulation artifacts. Assessed as a methods contribution and as a research instrument,
that chain is the substance of the work, and it is stronger than most comparable published systems.

The review found no scientific blocker. That conclusion follows directly from the project's claim
discipline: JOS's real limitations are numerous and several are consequential, but the system does not
assert the things those limitations would invalidate. Demonstration parameters are labelled as
assumptions; calibration artifacts record that no Jersey data was used; passenger movements are never
presented as tourists; unimplemented mechanisms are recorded as deferred rather than filled in. Where
documentation and implementation diverge — and they diverge in twenty-nine identified places — the
divergences are mostly documentation lagging a corrected implementation, not implementation
over-claiming. The one finding that comes closest to the blocker threshold, the runtime resident-absence
gap (`T-11`), stops short because the mechanism functions for its tested case and no published result
depends on it; it would cross that threshold for any analysis that used resident outbound travel as a
material mechanism.

The forty-five major limitations are real and must travel with the results. They cluster in an
informative way: JOS is strong wherever the question is *structural* (which routes exist, how settings
interlock, what reconciles to what, what is traceable to which source) and weak wherever the question
is *distributional* (how much individuals vary, how wide the tails are, how uncertain the answer is).
The system's homogeneity assumptions — fixed degree, deterministic stage durations, per-route adherence,
attenuation-only interventions — all push in the same direction: epidemics that are sharper, more
synchronised, less variable and more controllable than reality. That is a coherent bias with a knowable
sign, which makes it disclosable rather than disqualifying, and items 1–4 of Section 21 would
substantially address it.

Two properties give the platform genuine scientific potential beyond its present state. First, Jersey is
an unusually good subject: a population of about 104,540 sits squarely in the critical-community-size
regime where stochasticity and importation govern persistence, and with exactly two ports of entry the
importation stream is close to completely observable. Second, JOS already has the layer that most models
lack for exploiting that — an explicit, port-anchored, provenance-tracked importation mechanism with a
correctly implemented temporary population. The combination of contact and duration heterogeneity
(items 3–4), a full-wave baseline (item 6), and a registered Jersey surveillance series (item 10) would
turn a well-built general-purpose simulator applied to Jersey into a distinctive instrument for
questions that Jersey is specifically suited to answer.

For now the correct posture is the one the repository already adopts, held consistently in external
presentation: a verified, reproducible, honestly bounded synthetic research platform, with an explicit
statement that its epidemiological outputs are experiments on declared assumptions rather than
statements about Jersey.

---

**SCIENTIFIC REVIEW: SUITABLE WITH MAJOR DISCLOSURES**

Suitable as a synthetic research and experimentation platform. Not suitable, and not offered, as a
forecasting or policy-effectiveness instrument. The forty-five major limitations recorded in Section 18
must be disclosed whenever the corresponding results are interpreted, and the eighteen claim boundaries
in Section 20 should be treated as binding on any external presentation of JOS v1.

---

*This audit reviewed the frozen `jos-v1.0.0` release at commit
`9e9ce3abc4201cd8303c723015462d21ca237800`. No implementation code, configuration, parameter or existing
document was modified. Companion documents:
[`JOS_V1_SCIENTIFIC_TECHNICAL_REPORT.md`](JOS_V1_SCIENTIFIC_TECHNICAL_REPORT.md) and
[`JOS_V1_SCIENTIFIC_ROADMAP.md`](JOS_V1_SCIENTIFIC_ROADMAP.md).*
