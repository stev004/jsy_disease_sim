# Jersey Outbreak Simulator: A Synthetic Agent-Based Framework for Epidemic Simulation and Intervention Experiments in Jersey

**Technical Report — Release `jos-v1.0.0`, commit `9e9ce3abc4201cd8303c723015462d21ca237800`**

*Version 1.0 · 30 August 2026 · Companion to
[`JOS_V1_SCIENTIFIC_AUDIT.md`](JOS_V1_SCIENTIFIC_AUDIT.md)*

---

## Abstract

We describe the Jersey Outbreak Simulator (JOS), an agent-based, multi-route contact-network framework
for simulating respiratory epidemic dynamics and intervention scenarios in Jersey, Channel Islands. JOS
constructs a closed synthetic population of 104,540 agents — one per estimated resident at 31 December
2024 — from 22 registered official aggregate sources, using iterative proportional fitting to reconcile
a 2021 census age-by-sex structure onto 2024 population marginals and largest-remainder allocation to
preserve integer counts. Onto this population it layers households (45,133), communal establishments
(164), schools (48), workplaces (8,770), 62,108 job assignments and 2,420 institutional staff
endpoints, and from that structure it constructs eleven separable contact routes spanning residential,
educational, occupational, institutional, transport and community settings. Transmission is simulated
by a deliberately pathogen-neutral SEIRS module executed through Starsim 3.5.2, with an order-invariant
attribution layer that records which simulated contact route carried each infection together with the
full set of competing successful candidates. Three further layers are provided: an observation model
that separates latent infection from symptom onset, detection and reporting; a composable typed
intervention framework with calendar and detection-triggered activation; and an episode-based temporary
population representing visitors and returning residents, anchored to 2025 Ports of Jersey
passenger-movement totals (720,842 air and 196,623 sea arrivals) with runtime identity binding that
preserves event-time attribution under agent-slot reuse. Every stage emits versioned Parquet artifacts
whose scientific content — state conservation, incidence-flow reconciliation, event-to-aggregate
consistency — is independently re-derived by a verification layer, and whose provenance chain records
source checksums, parameter evidence classes, engine commit, dependency lock and random seeds. JOS v1 is
a synthetic research and experimentation platform. It is not calibrated to Jersey epidemiological data,
has not been validated against any observed epidemic, and does not produce forecasts; its outputs are
internally consistent experiments on declared assumptions. We document the model in full, quantify what
is empirically anchored against what is assumed, and state the limitations that bound interpretation.

**Keywords:** agent-based model, synthetic population, contact network, epidemic simulation,
observation model, importation, reproducibility, Jersey

---

## 1. Introduction

### 1.1 Epidemic modelling and the role of individual-based models

Mathematical models of infectious disease transmission range from compartmental systems of differential
equations, which assume homogeneous mixing within strata, to individual-based (agent-based) models in
which each person is represented explicitly and transmission occurs across an explicit contact
structure. The individual-based approach became central to pandemic preparedness analysis through work
such as Eubank et al. (2004), who simulated transmission over a synthetic urban contact network derived
from activity data; Ferguson et al. (2006), who evaluated mitigation strategies for pandemic influenza
in a spatially explicit population; Chao et al. (2010), whose FluTE model made a community-structured
influenza simulator publicly available; and Halloran et al. (2008), who assessed targeted layered
containment. More recent frameworks — FRED (Grefenstette et al. 2013), Covasim (Kerr et al. 2021),
OpenABM-Covid19 (Hinch et al. 2021) — extended the approach to detailed intervention representation
during the COVID-19 pandemic.

The scientific value of individual-based models lies less in point prediction than in their ability to
represent structure that compartmental models cannot: who contacts whom, in which setting, under what
schedule; how an intervention targeting one setting propagates through the rest; and how heterogeneity
in contact and infectiousness shapes the distribution of outbreak outcomes rather than only its mean.
That structural fidelity comes at a cost in parameter identifiability and in the difficulty of
validation, and the literature on calibrating such models is correspondingly cautious (Hazelbag et al.
2020; Chowell 2017).

### 1.2 Why geographically specific models are worth building

A geographically specific model can be anchored to that jurisdiction's own official statistics rather
than to a generic demographic profile, which makes its structural assumptions auditable against
published evidence. It can represent settings that matter locally — a particular care sector, a
particular school system, a particular pattern of commuting — at their true absolute scale. And it can
be used by the people who hold the corresponding policy levers, in a form whose assumptions they can
inspect.

Small jurisdictions offer a further scientific advantage. In a population of order 10⁵, an immunising
infection does not settle into deterministic endemic dynamics; persistence is governed by stochastic
fadeout and reintroduction. This is the critical-community-size regime identified by Bartlett (1957) and
analysed by Keeling and Grenfell (1997), and it is precisely the regime in which importation, contact
heterogeneity and chance dominate. Small populations are also computationally tractable at one-to-one
agent representation, which removes the scaling artefacts that affect models of large populations.

### 1.3 Jersey

Jersey is a self-governing British Crown Dependency of approximately 119 km² in the Channel Islands,
with an estimated resident population of 104,540 at 31 December 2024 (Statistics Jersey). Several
features make it a distinctive modelling subject:

- **A closed and enumerable boundary.** Jersey has two ports of entry — Jersey Airport and Jersey
  Harbour — and Ports of Jersey publishes annual passenger movements through both. Importation, which in
  most models is an assumed boundary condition, is here close to fully observable in aggregate.
- **Strong daytime centralisation.** The 2021 census records 66% of resident workers working in St
  Helier, against a St Helier resident population share of about 34.7%, so the island's daytime
  population geography differs sharply from its residential geography.
- **Twelve parishes** as the administrative and statistical geography, with population ranging by an
  order of magnitude between the largest and smallest.
- **A substantial visitor economy** relative to resident population, with pronounced seasonality.
- **A regulated care sector** with published staffing standards, and an education system with published
  pupil and staffing statistics.
- **Rich, openly licensed official statistics**, which makes a provenance-anchored synthetic population
  feasible in a way it is not for many jurisdictions.

### 1.4 Motivation and design stance of JOS

JOS was built to provide a structurally detailed, fully auditable simulation environment for Jersey in
which epidemic mechanisms and intervention scenarios can be explored under explicitly declared
assumptions.

Three design commitments shape the system and distinguish it from a conventional simulation codebase.

**Provenance before parameters.** No quantity enters the model without a declared evidence class. Values
derived from official statistics carry the source identifier, the source checksum, the reference period
and the identifier of the transformation that produced them. Values that are assumptions are labelled
`scenario_assumption` or `structural_assumption` with empty source lists, so an assumption cannot be
mistaken for a measurement.

**Pathogen neutrality.** The disease module is a generic respiratory SEIRS model whose demonstration
parameters are explicitly not estimates for any named pathogen. This is a deliberate choice: it forces
the structural model to be assessed on its own terms and prevents the platform from carrying implicit
epidemiological claims it has not earned.

**Verification of scientific content, not only of code.** Persisted artifacts are re-read and their
scientific invariants re-derived: compartment conservation, incidence-flow reconciliation,
event-to-aggregate consistency across every stratification, and cumulative-total reconciliation. An
artifact that passes verification has demonstrably internally consistent content, independent of the
code that produced it.

### 1.5 What this report is and is not

This report documents the model as implemented at the frozen v1.0 release. It states which quantities are
empirically anchored, which are derived by documented transformation and which are assumptions; it
describes the mechanisms; and it bounds interpretation. It does **not** present epidemiological results,
because JOS v1 has produced none that would be appropriate to present: the recorded executions are
construction benchmarks and short smoke tests, not epidemic analyses. Section 16 describes the intended
workflows without fabricating outputs for them.

---

## 2. Objectives and scope

### 2.1 Objectives

JOS v1 was developed to:

1. construct a synthetic Jersey resident population reconciled exactly to registered official controls,
   at one agent per resident;
2. represent the daytime structures through which respiratory transmission occurs — households,
   communal establishments, schools, workplaces, institutional staffing, commuting;
3. derive from that structure a set of contact routes that are individually removable, so that a route's
   contribution to simulated transmission can be isolated by ablation;
4. simulate transmission with a generic respiratory model that makes no pathogen-specific claim;
5. distinguish latent epidemiological truth from observed surveillance data structurally;
6. provide a composable intervention framework whose effects are mechanistically traceable to the routes
   they modify;
7. represent importation explicitly, anchored to observed passenger movements, with a temporary
   population that does not corrupt resident accounting;
8. quantify stochastic replicate variation and support controlled scenario comparison;
9. provide calibration infrastructure and demonstrate parameter recovery in a synthetic setting;
10. make every result reproducible and independently verifiable from its artifacts.

### 2.2 In scope

Resident demography and household structure; communal and institutional populations; education and
employment structure; parish-level geography; eleven contact routes with calendar-dependent activity;
generic SEIRS transmission with waning; deterministic seeding and exogenous importation; observation
with delays and partial ascertainment; eleven intervention types; visitor and returning-resident travel
episodes with border measures; replicate ensembles and matched-seed comparison; synthetic calibration
recovery; artifact provenance and verification; a local API and interactive application over the same
artifacts.

### 2.3 Explicitly out of scope in v1

Disease severity, hospitalisation and mortality; healthcare capacity; age-dependent susceptibility;
presymptomatic and asymptomatic infectiousness differentials; multiple pathogens, strains or variants;
sub-parish geography and coordinates; named individuals, addresses or real contact traces; calibration
to Jersey epidemiological data; validation against observed epidemics; forecasting.

### 2.4 The claim boundary

JOS v1 supports statements of the form *"under the specified assumptions, within the synthetic
population, the simulation suggests X"*, and comparative statements of the form *"scenario A produces
Y% less simulated transmission than scenario B under matched seeds and identical parents"*. It does not
support statements about what will happen in Jersey, what an intervention would achieve in Jersey, or how
any real infection was actually transmitted. The accompanying audit enumerates eighteen specific claim
boundaries.

---

## 3. System overview

JOS is organised as a linear chain of numbered stages, each consuming the validated, checksummed
artifact of its predecessor and emitting its own. Stage boundaries are enforced: a downstream stage
re-hashes its parent artifact and refuses to proceed on mismatch.

| Stage | Function | Principal module |
|---|---|---|
| M1 | Source ingestion, canonicalisation, quality reporting | `data_pipeline.py` |
| M2 | Synthetic residents, households, communal settings | `population_generator.py`, `population_controls.py` |
| M3 | Schools, jobs, workplaces, commuting | `population_structure_generator.py` |
| M4.1 | School and care staffing overlay | `staffing_generator.py`, `staffing_evidence.py` |
| M4 | Eleven contact routes | `network_generator.py` |
| — | Starsim coupling | `starsim_adapter.py` |
| M5 | Generic respiratory SEIRS, attribution, run orchestration | `respiratory.py`, `outbreak_runner.py` |
| M6 | Observation model; replicate ensembles; comparison | `observation_scheduler.py`, `observation.py`, `ensemble.py` |
| M7 | Composable interventions | `interventions.py`, `intervention_schemas.py` |
| M8 | Travel, visitors, border measures | `travel.py` |
| C3 | Calibration (synthetic recovery) | `calibration.py` |
| — | Artifact verification | `scientific_verification.py`, `scientific_hashes.py` |
| M9/M10 | Local API, persistent jobs, interactive application | `api.py`, `job_*.py`, `frontend/` |

Three architectural properties are load-bearing for the scientific claims.

**Single engine coupling point.** Starsim is imported only at the disease boundary
(`respiratory._load_starsim`, which raises unless the version is exactly 3.5.2) and in
`starsim_adapter.py`. The population and network layers have no engine dependency, so the synthetic
population and contact structure are reusable independently of the transmission engine.

**Interventions and travel never mutate their parents.** Both operate on prospective views of the M4
route object. `outbreak_runner.run_outbreak` asserts the M4 logical content hash is unchanged across the
run and raises `"M5 mutated the M4 route artifact"` otherwise. Consequently the baseline is a clean
counterfactual, and a mathematically neutral scenario reproduces the no-intervention run exactly.

**Determinism without a mutable random stream.** The population and network layers derive every choice
from `SHA-256(seed | key-parts)` rather than from a sequentially advanced generator, so results are
invariant to call order and to any reordering of internal loops. Combined with the hash chain, this makes
a run reproducible from its recorded configuration alone.

---

## 4. Data sources and provenance

### 4.1 The registry

`data/sources.yaml` registers 22 sources. Each carries `source_id`, title, publisher, URL,
`retrieved_at`, `reference_period`, licence, `status`, `acquisition_method`, the path of a local snapshot
and that snapshot's SHA-256. At build time every snapshot is re-hashed and a mismatch raises
`DataBuildError`, so the pipeline cannot run against altered inputs.

Publishers are Statistics Jersey, the Government of Jersey Open Data portal, the Children, Young People,
Education and Skills department (via freedom-of-information releases), the Jersey Care Commission and
Ports of Jersey. Reference periods span 2021-03-21 (census) to 2026 (care standards), and the mixing of
reference years is handled explicitly rather than absorbed (Section 5.1).

Where a source exists only as a PDF, the pipeline does not attempt automated table extraction. Instead a
narrow manual-transcription fixture records the specific table and page, carrying an `evidence_source_id`
back to the primary document — so a transcribed value names both the document and the location within it.

### 4.2 Canonicalisation

`data_pipeline.build_canonical` emits 14 canonical long-form CSV tables. Every row carries
`schema_version`, `source_id`, `source_sha256`, `evidence_source_id`, `reference_period`,
`observation_status`, `source_locator` and `transformation_id`. The last field is what makes a derived
quantity auditable: a raked age-by-sex cell records `age_sex_raking_to_2024_marginals_v1`, naming the
operation that produced it.

Three ingestion policies are worth stating because they are unusual and they matter scientifically.

**No imputation of suppressed cells.** Published tables suppress small counts. The pipeline writes such
cells with a blank count plus an explicit `upper_bound` and `censoring = 'positive_less_than'` — for
example the Agriculture 50+ workplace cell (`upper_bound = 5`) and suppressed parish "other" commute
cells (`upper_bound = 10`). Downstream code must therefore handle censoring explicitly rather than
consuming a fabricated point value.

**Published rounding is preserved.** Counts published to the nearest ten are stored as published, so
apparent non-reconciliations attributable to rounding remain visible rather than being smoothed away.

**Source conflicts are surfaced, not resolved.** Where two registered sources disagree, the difference is
emitted as a diagnostic with a check status. The recorded example is `mean_bedrooms_conflict`: 2.47 in
the report against 2.57 in the CSV, a 0.10 difference, flagged as a warning.

Three control non-reconciliations follow from publication rounding and are quantified rather than
described: sector-by-size workplace rows sum to 8,540 undertakings against a published total of 8,500
(+40, +0.47%); sector job rows sum to 55,360 against a published private-sector total of 55,370 (−10);
and the commute table sums to 57,340 workers against 57,338 in the industry table (+2). None exceeds
0.5%.

### 4.3 Evidence classification

Every parameter and control carries one of six classes:

| Class | Meaning | Example |
|---|---|---|
| `observed` | Directly from a registered official source | Parish population totals; 720,842 air arrivals |
| `derived` | Documented transformation of observed values | 2024 detailed age × sex; FTE-to-endpoint conversion |
| `regulatory_minimum` | A published legal or regulatory floor, not an observed value | Care Commission staffing ratios |
| `scenario_assumption` | A chosen value for demonstration or scenario exploration | `transmission_beta = 0.08`; arrival prevalence |
| `structural_assumption` | A modelling-structure choice with no direct evidence | Household age-gap bounds; route relative weights |
| `synthetic` | Generated content with no external referent | Visitor identities; synthetic accommodation units |

The `regulatory_minimum` class earns its place: the Care Commission ratios are floors that real homes
staff above, and classifying them as `observed` would be a category error with direct epidemiological
consequence, since care staffing determines the staff-mediated introduction route into care homes.

There is no `literature_prior` class, and correspondingly no v1 parameter is justified by reference to
published epidemiological estimates. This is internally consistent with pathogen neutrality, and it is
also why several quantities that could be literature-anchored — stage durations, the indoor:outdoor
transmission ratio, test-sensitivity profiles — are currently assumptions.

### 4.4 Reproducibility infrastructure

Artifacts are written to content-addressed directories with a manifest recording every output file's
size and SHA-256, the parent artifacts' logical hashes, the configuration hash, the engine version, the
Git commit, a dirty-worktree flag, the dependency lock state and the random seeds. Distinct hashes carry
distinct meanings — configuration, scenario, latent outcome, artifact bundle — so a change in
presentation can be told apart from a change in science. A verification archive re-checks parent hashes
so a stale parent cannot be presented as current.

Evaluated against the transparency and reproducibility framework proposed by Pokutnaya et al. (2023) for
computational infectious-disease models, JOS v1 satisfies the substance: versioned and checksummed
inputs, declared parameters with evidence classes, deterministic reruns, recorded environment, and
machine-checkable verification of persisted content.

---

## 5. Synthetic population

### 5.1 Demography

The target is 104,540 agents at full scale, one per estimated resident. Reduced modes exist for
development and testing (`ci` = 3,000; `scaled` = 15,000).

The 2024 population estimate publishes broad age bands and sex totals but not a detailed age-by-sex
table; the 2021 census publishes single-year age by sex. `population_controls._build_full_age_sex_counts`
therefore rakes the 2021 shape onto the 2024 marginals: 100 alternating proportional-fitting sweeps on a
3 × 2 table of (under 16, 16–64, 65+) × (male, female), followed by largest-remainder allocation of each
raked cell across the 2021 single-year shape. Both marginal sets are hit exactly. This is the classical
synthetic-population approach of Beckman, Baggerly and McKay (1996) — fit a detailed joint structure to
known marginals — applied here across reference years rather than across geographies.

Fitted marginals: under 16 = 15,410 (14.741%); 16–64 = 68,530 (65.554%); 65+ = 20,600 (19.705%),
against 2021 shares of 15.955%, 65.902% and 18.143%. Raked band-by-sex cells: under 16 male 7,889 /
female 7,521; 16–64 male 34,764 / female 33,766; 65+ male 9,497 / female 11,103.

Parish structure is raked analogously: 2021 parish five-year bands are fitted simultaneously to the
generated parish totals and the generated island age × sex totals, with an integer balancing loop
preserving both.

**Reference-year mixing is handled by pairing each control with its own denominator.** The 2021-referenced
worker control is scaled on `census_population_reference = 103,267`; the 2024- and 2025-referenced
school, workplace and job controls are scaled on `full_population_target = 104,540`. At full scale this
uprates the observed 57,338 resident workers by 1.233% to 58,045 while leaving the 2024 pupil control at
exactly 13,991 and the 2025 workplace control at exactly 8,500.

*Limitation.* Raking to broad bands cannot absorb compositional change within a band: every single year
of age 65–95 is multiplied by the same factor 20,600 / 18,736 = 1.09949. Because the real 2021–2024
growth of the 65+ group came predominantly from the 60–64 cohort crossing the boundary, the model's
oldest-old counts (85+ = 2,848; 90+ = 1,053; 95+ = 263) are modestly over-stated.

### 5.2 Households

45,133 households are instantiated from the 11 published census household types, each with a fixed base
role tuple. Two types have maximum size 1 (Single adult 8,709; Single pensioner 5,530), pinning 14,239
households (31.55%) at exactly one member. The residual 14,765 private residents are distributed as
extra roles across the 30,894 growable households by draws weighted on remaining capacity, with a global
cap of 8 members. Mean household size is 2.2696 against an observed 2.2697.

Ages are assigned per household as a relational unit under hard inequalities: a parent must be at least
`MIN_GENERATION_GAP = 15` years older than the oldest child; a couple's age gap must not exceed
`MAX_COUPLE_AGE_GAP = 25`; parents are capped at 64 where the residual pool permits. Housing attributes
(dwelling type, crowding band, car access) are drawn from fixed weights, with observed car-access anchors
of 16% island-wide and 30% in St Helier.

*Limitations.* No persons-per-household distribution control exists in the registry, so only the mean and
the one-person share are anchored; the remaining size distribution is an artefact of the
remaining-capacity rule, which thins the right tail. Within the age bounds, no distribution is fitted:
the realised median couple age gap is 10 years (28.2% exceeding 15 years) and the median parent-child
gap is 22 years with P99 = 53, whereas real spousal gaps concentrate within a few years and parent-child
gaps near 28–33. Household transmission volume is unaffected; its age targeting is. Household secondary
attack rates are also commonly reported to vary with household size (Madewell et al. 2020), a dependence
the compressed size distribution cannot express.

### 5.3 Communal populations

164 establishments holding 2,105 residents are generated across eight census categories, scaled from an
observed control of 162 establishments and 2,079 residents. Full-scale inventory: nursing care 15 homes
(637 residents), non-nursing care 16 (332), children's homes 8 (15), other medical or care 6 (30),
hotel/guest house/hostel 92 (572), homeless hostel 6 (94), staff communal 20 (276), detention 1 (149).
Residents are drawn before private households, from category-specific age bounds.

*Limitations.* Residents are split as evenly as integers allow within each category, so establishments
are equal-sized; since final outbreak size in a closed setting is a strongly non-linear function of
setting size, this eliminates the variance in institutional outbreak size and removes both the very
large and the very small settings. Care-home age eligibility is 50–95 with draw weight
`max(1, age − 45)`, giving 30.45% of residents aged 50–64 and a median age of 71 — far younger than real
care-home populations. The binding constraint is the weight rather than the pool: 2,848 modelled
residents are aged 85+ against 969 care-home places in total. Reduced modes delete whole categories
rather than scaling them: at `ci` scale there is no nursing home and no detention setting.

### 5.4 Education

Pupil controls are the 2024 spring-term census by school type: Government primary 6,220; Non-provided
primary 1,221; Government secondary 5,258; Non-provided secondary 1,114; Special 178; total 13,991.
School counts are `ceil(pupils / nominal capacity)` with nominal capacities of 240 (primary), 500
(secondary) and 90 (special), giving 48 schools at full scale; pupils are split evenly and classes formed
at 25 (primary and secondary) or 10 (special), yielding approximately 700 classes.

School staffing derives from a 2025 CYPES payroll FTE release: teachers and lecturers 983.30 FTE,
teaching assistants 507.15, heads and deputies 86.00. Endpoints are
`ceil(FTE × population_scale / 0.8)`, giving 1,230 teachers, 634 assistants and 108 heads — 1,972
endpoints, or one staff member per 7.10 pupils.

*Limitations.* Within each school type, pupils are selected in ascending age order from an island-wide
pool, and types are processed in a fixed order, so each type strips the youngest remaining eligible ages.
At full scale this produces: Special school 178 pupils all aged exactly 18; Non-provided primary
consisting only of 10- and 11-year-olds; Non-provided secondary only 16- and 17-year-olds; Government
primary spanning 4–10 with no 11-year-olds; Government secondary 11–16. School type is therefore nearly
perfectly confounded with pupil age. Separately, pupils are drawn island-wide with no catchment, and
`school_parish` is set to the modal home parish of that sample — which, given St Helier's 34.7%
population share, resolves to St Helier for all 48 schools and for all 1,972 school staff. There is no
further-education setting for the 16–18 band, although Highlands College appears in a registered source
universe. The staffing control's universe excludes independent schools, whose 2,335 pupils are
nonetheless staffed from it; restricting the numerator to the 11,656 pupils the control covers would
imply one staff member per 5.91 pupils, about 17% denser.

### 5.5 Employment

58,045 unique resident workers are selected from the 77,312 eligible residents aged 18–74 who are not
pupils, by a without-replacement draw weighted on a declared age propensity (0.45 under 25; 0.90 for
25–34; 1.00 for 35–54; 0.80 for 55–64; 0.18 for 65+). Sector is then assigned by shuffling within sex
against published sector-by-sex targets. A further 4,063 secondary jobs (7% of workers) are created,
giving 62,108 filled jobs.

Workplaces are seeded at their published size-band minima — 1 employee: 5,020 sites; 2–5: 2,020; 6–9:
550; 10–19: 440; 20–49: 280; 50+: 190; total 8,500 — with surplus jobs spread by capacity-weighted
increments. The residual 6,738 non-private (public-sector) jobs form 270 synthetic workplaces capped at
25 employees each. Workplace teams are formed at `ceil(employees / 12)` for sites of 10 or more.

Work parishes are assigned so that destination shares match the observed census split — St Helier 66%,
semi-urban 13%, rural 21% — within one percentage point. Commute modes are drawn from two published
conditional profiles where they exist (St Helier resident and worker: 69% walk, 24% car; rural resident
working in town: 75% car, 9% cycle, 8% bus), subject to a household car-access constraint. 13.67% of
workers (7,840 / 57,340) are assigned full-time remote working.

*Limitations.* Because the sampling fraction is 75.1%, the realised employment rates compress toward the
mean and differ substantially from the declared propensity: 60.3% (18–24), 84.7% (25–34), 87.3% (35–54),
81.5% (55–64), 31.1% (65–74). The 65–74 rate is roughly double what the weight implies, so older adults
acquire workplace and commute contacts they would not have. The published sector-by-size cross-tab is
ingested but never read; sector is instead matched to workplace size by a descending-size,
minimum-remaining-capacity heuristic that is anti-correlated with the discarded table. Within-band
workplace sizes are near-degenerate (the 50+ band has mean 150.48, range 132–173) so the largest
workplace in the model has 173 employees, and the hospital has no representation as a large site. Sector
carries no age profile. The 13.67% remote share is a 2021-census (pandemic-period) measurement allocated
uniformly at random across sectors rather than concentrated where remote work occurs, and
`remote_days_per_week` is binary (5 or 0).

### 5.6 Geography

Parish is the sole spatial unit: twelve parishes, with agents exchangeable within a parish. St Helier
holds 34.7% of the population as one undifferentiated unit. No vingtaine, postcode, output area, ward or
coordinate exists anywhere in the codebase, and household locations are not represented even
synthetically.

*Limitations.* Residential parish structure is anchored and correct. Daytime geography is not: every
school resolves to St Helier, and the residual parish no-car allocation distributes counts in proportion
to bare commute shares without weighting by household count, producing a generated no-car rate that
correlates −0.69 with the share it is documented to follow (St Mary: lowest weight 0.1688, highest
non-St-Helier rate 19.57%; St Saviour: second-highest weight 0.3886, rate 6.00%). Household type
composition is identical in every parish, because the census publishes household types for the island
only.

### 5.7 Institutional staffing

Care staffing converts Care Commission Appendix 4 regulatory minima into unique rosters as
`ceil(max(day_required, night_required) × coverage_multiplier)` with the multiplier defaulting to 2.0.
Full-scale output is 448 care staff across 31 staffed settings: 18 support workers and 6 nurses per
43-resident nursing home; 6 support workers per 20–21-resident non-nursing home.

Occupational double-counting is correctly prevented. Staff are drawn only from existing workers in the
education-and-health sector living in private households; school staff are taken first and care staff
from the strict remainder, so no agent holds two institutional roles; and in the network layer an
institutional staff member's generic primary job is removed from the ordinary workplace routes, so the
institutional membership replaces rather than adds to it.

*Limitations.* Only settings typed "with nursing" or "without nursing" are staffed — 31 of 164
establishments. The other 133 receive no staff at all, including the single 149-resident detention
setting, 8 children's homes and 6 homeless hostels. Each staff agent holds exactly one care assignment,
so cross-facility staff are structurally zero and the between-care-home staff bridge — among the
best-documented transmission pathways between care homes during COVID-19 — is absent as a direct
mechanism. Because the ratios are regulatory floors, the resulting staff count is a lower bound rather
than a central estimate. Teachers are bound to a single class by hash-modulo, leaving an estimated 7% of
classes without a class-linked staff member and giving secondary teachers none of the between-class
bridging role they have in reality.

---

## 6. Contact-network architecture

### 6.1 Routes

`network_generator.generate_networks` emits eleven routes, each with a typed specification recording
route family, persistence, active calendar, an indoor flag, a relative weight and free-text assumptions.

| Route | Topology | Refresh | Full-scale edges | Relative weight |
|---|---|---|---|---|
| `household` | Clique within household | Static | 98,052 | 1.00 |
| `school_class` | Clique within class | Static (term-time active) | 190,293 | 0.85 |
| `school_cross_class` | Ring over year group, class-core excluded | Static (term-time active) | 29,345 | 0.50 |
| `workplace_team` | Clique within team | Static (attendance-gated) | 147,721 | 0.70 |
| `workplace_transient` | Ring over workplace, team-core excluded | Static (attendance-gated) | 96,742 | 0.30 |
| `care_resident` | Clique within setting | Static | 3,336 | 0.90 |
| `care_staff` | Staff-to-resident roster | Dynamic | — | 0.65 |
| `shared_vehicle` | Clique within sharing group | Dynamic | — | 0.70 |
| `bus` | Ring over synthetic pool | Dynamic | — | 0.45 |
| `community_indoor` | Ring over parish pool | Dynamic (partly persistent pool) | — | 0.35 |
| `community_outdoor` | Ring over parish pool | Dynamic | — | 0.18 |

Three topological primitives are used: complete groups (cliques); circulant rings with offsets 1..k,
giving degree exactly 2k after de-duplication; and hash-directed target selection within bounded pools.
All construction is deterministic given the seed, via SHA-256-derived permutations rather than a random
number generator.

### 6.2 Nested-route exclusion and overlap policy

Routes representing sub-structures of the same setting are made disjoint. Before this correction, school
cross-class and workplace transient pools intersected the corresponding class-core and team-core edge
sets at 18,784 and 19,318 pairs respectively; after the exclusions both intersections are exactly zero.
A route-overlap matrix classifies every route pair as `FORBIDDEN`, `ALLOWED_DISTINCT_SETTING`,
`EXPECTED/NESTED_EXCLUDED` or `DIAGNOSTIC_ONLY`.

The treatment of distinct-setting overlap is deliberate and correct: a pair who share both a household
and a workplace team represent two separate daily exposure opportunities, not one encounter recorded
twice, and each is evaluated as a separate transmission opportunity. The overlap matrix is computed on a
single date, so overlaps arising only on other calendar days are not enumerated.

### 6.3 Calendar semantics

Routes are gated by a frozen official school-term calendar and by weekday/weekend rules. School routes
are inactive outside term time; workplace routes are gated by attendance including remote-working days;
community routes operate daily with route-specific participation. The calendar is keyed to a fixed
reference year and raises for dates outside it, which caps a simulated run at 360 days from the default
start date.

### 6.4 Coupling to the transmission engine

`starsim_adapter.build_starsim_disease_sim` converts each route into a Starsim network — static routes to
`ss.Network`, dynamic routes to `ss.DynamicNetwork` subclasses whose edges are replaced each timestep
from the corresponding date-keyed builder. Critically, the per-edge weight is written into the Starsim
per-edge `beta` array. Combined with `route_betas[r] = beta × route_multipliers[r]` in the run layer, the
effective daily per-edge transmission probability is `beta × weight`: at the demonstration `beta = 0.08`,
0.08 on a household edge and 0.0144 on an outdoor community edge.

### 6.5 What the network can and cannot represent

*Strengths.* Eleven genuinely separable routes; enforced non-duplication of nested structures;
calendar-dependent activity anchored to an official term calendar; institutional memberships that
replace rather than duplicate generic ones; and a tested separability guarantee — removing a route family
leaves every retained route's snapshot byte-identical.

*The dominant limitation.* **There is no individual-level contact-rate heterogeneity.** Ring routes give
every participant exactly 2k neighbours regardless of pool size; cliques give every member exactly
n − 1. No per-agent activity multiplier, no negative-binomial or Poisson degree draw, and no persistent
individual contact-rate parameter exists anywhere in the network layer. JOS therefore cannot generate
overdispersion in individual reproduction number and cannot produce superspreading events, beyond the
modest variation induced by household and workplace size. Since Lloyd-Smith et al. (2005), individual
variation in transmission has been recognised as a first-order determinant of epidemic behaviour,
affecting extinction probability, the explosiveness of established epidemics, and which interventions are
efficient. Simulated epidemics will be more deterministic, more synchronised and less variable than
reality at the same mean.

*Further limitations.* The community broad-age mixing matrix is a structural assumption, not Jersey
contact-diary evidence and not a published contact matrix; community contacts are drawn within-parish
only, so the sole cross-parish mixing channels are workplace membership and transport; care-home
residents are **not** excluded from the general community route and participate at free-living rates,
which materially understates the epidemiological isolation of care settings; and the two multiplicative
scaling parameters over the same product (M4 relative weight and M5 route multiplier) are redundant and
not separately identifiable.

On magnitudes: because weights are exposure-opportunity multipliers rather than contact counts, the model
does not expose a per-agent contacts-per-day quantity comparable to contact-survey measurements such as
POLYMOD (Mossong et al. 2008) or CoMix (Jarvis et al. 2020). **JOS v1 does not demonstrate that its
per-agent daily contact structure is consistent with any empirical contact survey**, and establishing
that comparison would be a valuable addition. Relatedly, the indoor:outdoor weight ratio of about 1.9 is
low relative to the direction of the outdoor-transmission literature: Bulfone et al. (2021) report that
the studies they identified found under 10% of infections occurred outdoors, while noting that
heterogeneity prevented a pooled estimate.

---

## 7. Disease model

### 7.1 States and transitions

`respiratory.RespiratorySEIRS` implements a four-compartment SEIRS structure with per-agent boolean state
arrays and per-agent transition timers:

```
S  --(edge-level transmission)-->  E  --(latent period)-->  I  --(infectious period)-->  R
^                                                                                        |
+----------------------------------(immunity duration, if waning enabled)-----------------+
```

Exactly one compartment is true per agent. On infection, `set_prognoses` schedules
`ti_infected = ti + latent_period`, `ti_recovered = ti_infected + infectious_period` and, when waning is
enabled, `ti_susceptible = ti_recovered + immunity_duration`. Transitions fire when the simulation index
reaches the scheduled timer. Only the `infected` state transmits.

### 7.2 Parameters

All values in `configs/diseases/respiratory_seirs_demo.yaml` are labelled `scenario_assumption` with
empty source lists and explicit notes that they are not named-pathogen estimates.

| Parameter | Value | Distribution | Class |
|---|---|---|---|
| `transmission_beta` | 0.08 | Fixed daily per-edge probability before route weight | `scenario_assumption` |
| `latent_period_days` | 2.0 | `ss.constant` | `scenario_assumption` |
| `infectious_period_days` | 5.0 | `ss.constant` | `scenario_assumption` |
| `immunity_duration_days` | 30.0 | `ss.constant` | `scenario_assumption` |
| `immunity_waning_enabled` | 1.0 (on) | — | `scenario_assumption` |
| `initial_seed_count` | 10 agents | Deterministic selection | `scenario_assumption` |
| `route_multipliers` | 1.0 for all 11 routes | — | `scenario_assumption` |
| `seasonal_amplitude` | 0.0 (disabled) | — | `scenario_assumption` |
| Severity, mortality, age susceptibility | Not implemented | — | Deferred |

### 7.3 Coherence and internal verification

State transitions are internally coherent, and the coherence is machine-checked rather than asserted.
Artifact verification re-derives from the persisted tables that the compartment sum is constant across
the horizon, that daily new infections equal local plus imported, and that cumulative totals equal the
running sum of local, imported and seeded contributions. Modifier composition uses a registered-component
system, so vaccination and travel modifiers compose multiplicatively without either overwriting the
other.

### 7.4 Limitations

**Deterministic stage durations.** All three durations are `ss.constant`, so the generation-interval
distribution is a point mass and there is no individual variation in infectious duration. This is not
only a realism issue: Lloyd (2001) showed that narrowing the infectious-period distribution destabilises
epidemic models, and Krylova and Earn (2013) showed that stage-duration shape alters the dynamical
structure of seasonally forced models; Wearing, Rohani and Keeling (2005) make the corresponding point
for management-relevant quantities. A point mass sits at the extreme of that spectrum. Expected
consequences: sharper and faster peaks, narrower stochastic envelopes, and reduced probability of early
stochastic extinction.

**No presymptomatic infectiousness; constant infectiousness.** Only `infected` agents transmit and
relative infectiousness is 1.0 throughout, so the entire infectious period follows the latent period.
This interacts strongly with the observation and intervention layers, because it means an intervention
triggered at or before symptom onset can in principle avert the whole infectious period.

**Waning to full susceptibility.** Recovered agents return to susceptible with relative susceptibility
unchanged; there is no partial immunity and no boosting. Inert over the 30-day default horizon; over
longer horizons it produces repeated full-susceptibility reinfection and strongly oscillatory dynamics.

**`attack_rate` is a cumulative incidence rate, not an attack rate.** The column is
`cum_total_infections / len(sim.people)`, where the numerator counts every infection event including
seeds and post-waning reinfections. It is not bounded by one, and in travel runs the denominator includes
pre-allocated visitor slots. The counts are correct and reconciled; the label invites misreading.

**No severity, hospitalisation, mortality or age-dependent susceptibility.** Structurally absent by
design, with the corresponding columns held at zero and the parameters recorded as not implemented.

**Fixed daily timestep.** The runner rejects any timestep other than 1.0 days, so within-day contact
sequencing is outside the model.

---

## 8. Transmission model

### 8.1 Hazard and infection

Edge-level transmission probability is computed by Starsim's `compute_transmission` and
`Network.net_beta` primitives from the per-edge beta array (Section 6.4), the source's relative
infectiousness and the target's relative susceptibility. Infection occurrence is the unmodified union of
successful directed edges: a target infected on more than one route is infected once.

### 8.2 Five distinguished infection streams

JOS separates the ways an agent can become infected, and reports them separately:

| Stream | Meaning | Event label |
|---|---|---|
| Seeded | Deterministically selected initial infections | `seeded` |
| Local | Acquired across a simulated contact edge | `local`, with attributed route |
| Exogenous import | Generic external-force-of-infection process | `imported`, route `exogenous_import` |
| Travel importation | Returning resident infected abroad | `travel_imported`, `travel_acquisition = True` |
| Visitor arrival state | Visitor arriving already exposed or infectious | Recorded on the episode, not as an acquisition |

`cum_infections` excludes seeds; `cum_total_infections` includes them; both are reconciled against the
event table. Generic imports and explicit travel importation are mutually exclusive except in an
explicit `both` mode, in which they operate additively with no linkage between their magnitudes.

A detail worth noting as good practice: the generic import process draws the attempted people first and
then applies each attempt's relative susceptibility, so vaccine protection reduces successful
acquisitions rather than merely relabelling which agent is imported. Attempts and acquisitions are both
reported.

### 8.3 Route attribution

Where a target has successful candidate edges on several routes, `_order_invariant_infect` selects one
route with probability proportional to that candidate's realised per-edge hazard, using a draw keyed on
`(rand_seed, 'attribution', timestep, target)`. Route insertion order therefore cannot influence the
outcome. The full candidate set, each candidate's route and hazard, and the candidate count are written
onto every event, and the run diagnostics publish the distribution of candidate counts.

### 8.4 How route attribution should be described

The defensible description is **"simulated transmission pathway"**, or **"bookkeeping attribution over
simulated pathways"**. It is not mechanistic attribution and it is not inferred cause. Three reasons:

1. Where multiple candidates succeed, the attributed route is one draw from a hazard-weighted
   distribution over routes that all in fact succeeded; a different draw relabels the same infection.
2. The hazards derive from unanchored relative weights, so the weighting of that draw is
   assumption-driven.
3. The route inventory is the model's own construction, so attribution can only ever be to a route JOS
   represents.

The scientifically sound use of route output is **ablation and contrast** — disabling a route family and
observing the change — because route separability is enforced by test. Absolute route shares should be
reported alongside the candidate-count distribution.

### 8.5 Interpretability of aggregate outputs

`new_infections`, `new_local`, `new_imported`, `new_seeded`, `cum_infections` and
`cum_total_infections` are interpretable as simulated counts and are reconciled to the event table by
verification. Parish, age and route stratifications each sum to the matching daily flow on every date.
`attack_rate` requires the qualification in Section 7.4. In travel runs, the headline
susceptible/exposed/infectious/recovered columns are counted over the active set and therefore include
active visitors; resident-only columns are provided separately.

---

## 9. Observation model

### 9.1 Design

The observation layer implements the principle that true infections are not observed cases. Each latent
infection is passed to `ObservationScheduler.schedule_infection`, which assigns:

1. **Infection date** — from the latent event;
2. **Symptomatic status** — Bernoulli draw on `symptomatic_probability` (0.6 in the demonstration
   configuration);
3. **Symptom onset date** — infection date plus `symptom_onset_delay`;
4. **Detection** — Bernoulli draw on `symptomatic_detection_probability` (0.75) or
   `asymptomatic_detection_probability` (0.05), anchored at onset for symptomatic cases and at infection
   for asymptomatic;
5. **Detection date** — anchor plus `detection_delay`;
6. **Report date** — detection date plus `reporting_delay`.

A per-weekday reporting factor is available. Randomness is namespaced on the latent replicate seed, the
observation seed, the observation configuration identity and a stable per-event key, so replicates cannot
share an observation sequence and insertion order cannot matter.

The scheduler serves two paths: **offline**, observing a completed latent run, and **online**, delivering
detection notifications during execution for detection-triggered interventions. `observe_latent_run`
recomputes the offline schedule with the same sampler and **raises if it disagrees with the runtime
schedule**, so the two paths cannot silently diverge.

### 9.2 Self-checks

Three properties are computed rather than assumed: `chronology_violations` counts any breach of date
ordering; `latent_incidence_conservation` confirms the latent series is unchanged by observation; and the
analysis horizon is extended by an explicit or derived maximum-delay tail so late reports are not
truncated. Detection events consumed by the intervention layer are delivered strictly after the day's
transmission has been evaluated.

### 9.3 Limitations

**The onset anchor is not constrained by the disease timeline.** Symptom onset is computed as infection
date plus a configured delay, with no requirement that it fall after the latent period. In the shipped
demonstration configuration both `symptom_onset_delay` and `detection_delay` are 0 days, while the latent
period is 2 days — so symptomatic cases are detected on the day they are infected, two days before they
become infectious, and detection-triggered isolation takes effect the following day, still before the
case can transmit. The chronology check cannot detect this because it tests only that onset is not before
infection. **The direction of bias is unambiguous: modelled symptom-triggered control is optimistic**,
and any presentation of the isolation or quarantine scenarios must disclose this or re-run with a
positive onset delay.

**Symptomatic status is uncorrelated with infectiousness.** The flag is drawn in the observation layer
and never enters the disease model, so detection is a random thinning of infections independent of how
much an agent transmits — whereas real symptom-based surveillance over-samples the more symptomatic and
often more infectious.

**The per-day ascertainment fraction mixes cohorts.** `daily_observed_cases.ascertainment_fraction`
divides detections on a date by infections on the same date; because detection follows infection, the
numerator and denominator refer to different cohorts and the ratio is not a probability. The run-level
figure is the correct cohort quantity.

**No testing-capacity or test-negative structure.** Detection is a simple probabilistic thinning with no
representation of testing supply, test-seeking behaviour or test performance.

Two further points: the weekday factor multiplies an already-validated probability without re-bounding the
product; and travel runs emit empty resident parish, route and age stratifications, so enabling travel
silently removes breakdowns the baseline runner provides.

---

## 10. Intervention framework

### 10.1 Structure

`interventions.InterventionManager` is a single typed Starsim intervention module. A `ScenarioConfig` is
a canonically sorted, identifier-unique set of `InterventionConfig` records plus seed, parent identifiers
and a run hash; unknown fields and unknown route identifiers fail validation. Each intervention declares
its type, activation rule (`calendar` or detection-triggered), dates or detection delay, target
population, per-route multipliers, adherence, provenance metadata, assumptions and an independent content
hash.

Implemented types: school closure and reduction, workplace reduction (work-from-home), community
reduction (independent indoor and outdoor), care-home protection, vaccination, case isolation, household
quarantine, masking, gathering reduction, and travel-layer border measures (arrival testing, border
quarantine, arrival-volume reduction, traveller vaccination).

Each daily timestep the manager releases expired states, applies due detection actions, updates calendar
transitions, refreshes work-from-home and vaccination states, synchronises vaccine modifiers, applies
effective route multipliers to prospective route views, and records state, events and route-effect
diagnostics.

### 10.2 Mechanism

An intervention multiplies the **edge weight** — that is, the per-edge daily transmission probability —
on a prospective view of the route. Factors from all active interventions compose in canonical order via
`math.prod`, clipped to [0, 1]. An edge is dropped only when the composed factor reaches zero, and care
roster edges are retained with zero effective beta so roster topology remains inspectable.

Three lifecycle properties are verified:

- **No retrocausality.** Detection notifications arrive after that day's transmission; action is queued
  for `detection_time_index + 1 + start_delay_days`.
- **Clean counterfactual.** The M4 artifact is never mutated, and when every factor equals one the route
  arrays are reused without copy, so a neutral scenario is byte-identical to a no-manager run.
- **Deterministic composition.** Canonical ordering with explicit clipping.

### 10.3 Limitations

**Adherence is drawn per route, not per person.** The stable draw is keyed on
`(run_seed, 'route-adherence', intervention_id, route_id, agent_id)`. Because the route identifier is in
the key, draws are independent across routes: at adherence 0.8 across eight suppressed routes,
essentially nobody is fully non-adherent, and the intervention acts as a uniform 80% reduction of
exposure opportunities rather than as 80% of people complying fully. The correlated tail of fully
non-compliant individuals — which is what sustains transmission under real partial compliance — is
absent. The work-from-home family is the exception, keying adherence on the agent alone.

**No behavioural substitution or displacement.** All multipliers are bounded in [0, 1] in both the
intervention and travel layers, so the framework is attenuation-only: closing a school deletes class
edges without adding household or community contact, and sending a worker home deletes workplace and
commute edges with no compensating community exposure. A measured intervention effect can never be
adverse. There is also no adherence fatigue or time-varying compliance.

**Vaccination reaches only current susceptibles**, while the coverage denominator counts all
target-matching agents — so a campaign preferentially reaches the never-infected and the waned, and
nominal coverage can become unreachable as the epidemic progresses. Efficacy is leaky (relative
susceptibility is multiplied by one minus efficacy), which is the conventional choice.

**Effects scale per-contact risk, not contact counts**, which coincides with a contact reduction only to
first order in beta and cannot represent network rewiring.

### 10.4 Simulated efficacy is not policy effectiveness

What the framework produces is the change in simulated transmission when specified contact-opportunity
multipliers are applied to specified routes at specified times, under the model's adherence semantics and
with no behavioural compensation. Three separate mechanisms — the onset anchor (Section 9.3), per-route
adherence, and the absence of substitution — each bias measured benefit upward, and none is quantified.
Results should be reported as simulated reductions under declared assumptions, never as what a
corresponding real policy would achieve.

---

## 11. Travel and temporary population

### 11.1 The empirical anchor

The travel layer's only empirically anchored quantities are the 2025 Ports of Jersey annual totals:
**720,842 air arrivals and 196,623 sea arrivals, 917,465 in total.**

**These are passenger movements — arrivals at the two ports — not unique tourists.** The distinction is
enforced in the implementation: the configuration schema records units as "passenger movements/year" with
the note "Passenger movements, not unique tourists."; the assumptions tuple states that the values are
"Ports of Jersey passenger arrivals, not unique visitors"; and the run diagnostics set
`annual_values_are_passenger_arrivals = True`. No code path converts movements to unique visitors: the
generated unit is a person-movement, and composition, party, stay and transport attributes are drawn per
movement. A single tourist making one round trip contributes one arrival, and so does a resident
returning from a trip.

The annual total is converted to a daily stream by a half-up integer annual target followed by
largest-remainder (Hamilton) apportionment with an ISO-date tiebreak, so the annual integer is preserved
exactly for any seasonality shape. At unit stream scale this reproduces 720,842 / 196,623 / 917,465
exactly under both neutral and summer-weighted profiles, and a test pins the identity. One caveat for
accurate reporting: a full-year run at unit scale would require 917,465 materialised episodes, exceeding
the 200,000 limit, so the exact reconciliation is a property of the apportionment and capacity sizing,
demonstrated by a non-epidemic benchmark path rather than by an executed full-year disease run.

### 11.2 Episodes and visitor representation

Each day's movements are split into returning residents and visitors by an exact cumulative rule, then
grouped into parties. A visitor receives a synthetic identity, an age drawn uniformly on 1–90, a sex,
an accommodation type (day visitor, host household, or synthetic hotel guest), a local transport mode, a
stay length with jitter, and an arrival disease state. Returning residents are bound to a real resident
agent, forced to arrive susceptible, and carry an absence interval.

Because Starsim's population growth is append-only, visitors occupy pre-allocated slots sized from peak
concurrency plus 10% headroom, and slots are reused across the run.

### 11.3 Identity binding under slot reuse

Slot reuse is the layer's central correctness problem, and it is solved on both axes.

**State cannot leak.** Departure calls `reset_person_state`, clearing all four compartments, setting all
transition timers to NaN, resetting every registered modifier component to 1.0, zeroing age and sex,
marking the slot not-alive and removing it from the active set. Activation calls
`initialize_arrival_state`, which itself begins with a reset. Deactivation strictly precedes activation
within the same daily call, so a slot is never doubly occupied, and temporary edges are rebuilt from
scratch each day so contacts cannot persist. An end-of-run audit checks every inactive slot.

**History cannot be relabelled.** Every event resolves its actor through an interval map keyed on
`(slot_uid, timestep)` rather than through the slot's current occupant, and the visitor identity, trip,
party and episode identity hash are frozen into the event at creation. The observation layer prefers the
event's own agent identifier and includes the episode hash in its duplicate key, so a later occupant
cannot inherit an earlier visitor's detection. A test mutates the identifier map between scheduling and
delivery and confirms the delivered detection still names the original visitor.

### 11.4 Contact pathways

Seven temporary routes are rebuilt daily: `arrival_terminal` (weight 0.30), `visitor_party` (0.60),
`visitor_accommodation` (0.55, chunked at 8), `visitor_host_household` (0.80), `visitor_transit`
(0.35 bus, 0.25 vehicle), `visitor_community_indoor` (0.35) and `visitor_community_outdoor` (0.18).
Quarantine attenuation and a visitor-to-resident multiplier are applied per endpoint at transmission
time.

### 11.5 Border measures

The arrival-testing lifecycle separates four stages — administration, scheduled result time, result
availability, prospective action — each logged independently, with a frozen test record bound to the
episode identity hash. A result landing after the visitor has departed is emitted as non-actionable and
cannot quarantine the replacement occupant; returning-resident delayed results are matched to the
permanent identity and remain actionable; all-arrival quarantine is independent of testing probability.
Quarantine is multiplicative attenuation of both endpoints with a route-class distinction, a per-person
adherence draw, an activation delay and a release timestep — a formulation that correctly separates the
three real loss channels of coverage, turnaround delay and adherence.

### 11.6 Limitations

**Only the two annual totals are anchored.** Composition, stay duration, party size, transport mode,
accommodation, contact intensities, arrival prevalence, external acquisition pressure, all border
measures and all seasonality shapes are scenario or structural assumptions, and are labelled as such.

**Stream scaling does not preserve the traveller-to-resident ratio.** The real ratio is 8.776 movements
per resident-year. Every shipped configuration uses stream scale 0.001, giving 0.0088 per resident-year
at full population — roughly a thousandfold lower. No shipped configuration should be read as
representing Jersey's actual traveller exposure ratio, even qualitatively.

**Visitor-to-resident mixing does not scale with arrival volume.** The resident pools recruited into the
visitor-facing routes are absolute counts — four terminal residents per day, three residents per parish
per day per community route — regardless of arrival volume, so resident exposure saturates as volume
grows and arrival-volume sensitivity results cannot be read as elasticities. The terminal resident pool
is also hard-coded to St Helier, whereas Jersey Airport is in St Peter.

**Arrival testing has no incubation-dependent sensitivity.** The test reads compartment membership,
treating exposed and infectious identically with a single constant sensitivity set to 1.0 in every
shipped configuration. Because external acquisition for returning residents is applied immediately before
the test in the same callback, a resident infected abroad at the return timestep is detected with full
sensitivity. The recently infected are exactly the population real border screening misses, so the model
cannot represent the dominant failure mode of the policy, in the optimistic direction. Conversely,
positive results returned after departure are excluded from reported positive-test counts, so measured
screening yield is understated.

**Arrival prevalence is a free dial** with no anchor, applied identically across entry mode and origin
(origin is not modelled). Since prevalence times volume is the entire visitor-side importation signal,
every visitor-driven result is approximately linear in a user-chosen number.

**Two defects in the resident-travel path.** Resident absences beginning inside the run horizon are never
applied at runtime — presence is computed once at construction — so a returning resident remains in every
resident route edge throughout their nominal absence while the plan counts them as away, and two artifact
columns disagree for the same day. And repeat resident returns collide in person-keyed runtime maps,
silently dropping the second episode with testing off and raising an error with testing on.

**Further structural simplifications.** Travel parties are not co-located, since members draw
accommodation, transport and stay length independently; the configured party-size distribution is not
realised at demonstration scale because parties are truncated to the daily residual; visitor
accommodation stock is a hard-coded 32 synthetic units per parish allocated in proportion to household
counts rather than accommodation supply; visitor age is uniform 1–90; traveller vaccination covers
visitors only; and the monthly seasonality shape is invented, with two demonstration profiles citing a
registered source identifier for a shape not derived from it.

**Denominators.** Resident and visitor attack rates are correctly separated, and inactive slots are
excluded from all denominators, but the headline compartment columns include active visitors.

### 11.7 Zero-travel equivalence

A travel configuration producing no episodes is a mathematical no-op: the runner delegates to the
non-travel path and reproduces its `daily_epidemic`, `transmission_events`, stratifications and latent
outcome hash verbatim, with empty travel tables retained as separate artifacts. This is a genuine
falsifiable check that the travel layer is separable and does not perturb the resident baseline, and it
passes.

---

## 12. Ensemble simulation and scenario comparison

### 12.1 Replicates

`ensemble.run_ensemble` executes a list of explicitly ordered, unique seeds. Each replicate re-validates
the same M2 and M3 population artifacts and re-generates **only** the M4 contact network with the
replicate seed, then runs the disease and observation layers on that seed. Summaries report the median
and configurable lower and upper quantiles (default 2.5% and 97.5%) per metric per date.

### 12.2 What the bands quantify

| Source of uncertainty | Represented? |
|---|---|
| Network realisation | Yes |
| Transmission stochasticity | Yes |
| Observation stochasticity | Yes |
| Population generation | No — one fixed population |
| Parameter uncertainty | No — one parameter vector per ensemble |
| Structural uncertainty | No — no facility exists |

**Stochastic replicate bands alone do not quantify total scientific uncertainty**, and in JOS v1 they do
not quantify total stochastic uncertainty either, because the two largest sources of individual-level
variability are suppressed by construction: contact degree is fixed (Section 6.5) and stage durations are
deterministic (Section 7.4). Parameter uncertainty in beta alone would very likely dominate the reported
intervals. Bands must be labelled as stochastic replicate variation and never as confidence, credible or
prediction intervals.

### 12.3 Bookkeeping

Several details are handled better than is typical. Failed replicates are retained as failed and never
become zero observations. Summary cells carry an explicit semantic — `observed`, `structural_zero`,
`carried_forward`, `outside_metric_horizon`, `non_contributor` — so a missing incidence value is
distinguished from a genuine zero and prevalence is not fabricated beyond the simulated horizon.
Requested, planned and actual worker counts are recorded separately with sequential fallback flagged as
an execution diagnostic.

*Limitation.* Extreme quantiles are computed by linear interpolation with no minimum-replicate guard,
while documented demonstration ensembles use two or three seeds — at which point a reported "95% band" is
essentially the observed minimum and maximum.

### 12.4 Matched-seed comparison

Scenario comparison holds the population, network parents and seed fixed and varies only the scenario
configuration, refusing to proceed unless seed, horizon and the M2, M3 and M4 parent hashes all agree.
This is a common-random-numbers design, and it makes a paired difference a genuinely controlled contrast
at the point of divergence.

The framework is honest about the limits of that coupling: comparison diagnostics record whether episode
generation and the temporary network are actually coupled, and flag
`event_path_divergence_may_break_later_coupling` — coupling is exact only while stream keys and event
paths remain equal, and decays once the trajectories diverge.

*Limitation.* The comparison emits per-seed differences without any distributional summary, so the
natural inferential object for a scenario contrast — a central difference with an interval — must be
computed by the consumer.

---

## 13. Calibration framework

### 13.1 What is provided

Two harnesses. `run_synthetic_recovery` hides a reporting-delay parameter, generates target observations
under a fully detecting observation configuration, searches with Optuna against a squared-error objective
on daily reported cases, and re-checks the recovered value on fresh held-out seeds.
`run_beta_recovery` profiles a generic transmission parameter over a declared candidate grid and
additionally profiles it under altered ascertainment and altered route weights.

Diagnostics record `all_trials_retained: True` and, critically, `real_jersey_data_used: False`.

### 13.2 Calibration is not validation

**JOS v1 provides calibration infrastructure and demonstrates parameter recovery in a synthetic setting.
It contains no calibration to Jersey epidemiological data.** Of the 22 registered sources, none is a case
notification, testing, serology, hospitalisation or excess-mortality series, so no Jersey epidemiological
observable exists in the repository to fit.

The project states this in its own documentation, including the observation that the harness "does not
identify beta separately from contact intensity."

### 13.3 Identifiability

A route's contribution to transmission is the product `beta × route_multiplier × edge_weight ×
edge_count`. Two of these are free multiplicative parameters over the same quantity, the edge count is
fixed by unanchored structural capacities, and no output identifies the split. The confounding profiles
in `run_beta_recovery` are, in effect, a deliberate identifiability probe rather than a fitting exercise
— which is the right thing to build first. Consequently **a fitted beta is one point on a ridge of
observationally equivalent parameter combinations**, and the appropriate remedy is to reduce the
parameterisation to a single identifiable per-route intensity rather than to fit the redundant set.
Chowell (2017) treats parameter identifiability as a first-class concern in exactly this setting.

### 13.4 Methodological limitations

The objective is an unweighted sum of squared differences in daily reported counts, which is an implicit
homoskedastic Gaussian likelihood on count data whose variance grows with the mean; the search returns a
point estimate with no interval and no goodness-of-fit test. Because truth and candidate share the same
generative model, network and population, the demonstrated recovery is also over-precise relative to any
real fitting problem — a mis-specification arm, in which truth is generated under a different structure
than the fitted model, would be the natural next test.

Hazelbag et al. (2020), reviewing calibration of individual-based models across HIV, tuberculosis and
malaria, found that a minority of studies used reproducible, non-subjective calibration methods and
emphasised that policy-facing models should report uncertainty in both parameters and predictions. JOS v1
meets the reproducibility half of that standard comprehensively and does not yet attempt the uncertainty
half.

---

## 14. Software and scientific reproducibility

### 14.1 Environment

Python 3.12, with Starsim pinned at 3.5.2 and the version asserted at the disease boundary. Dependencies
are locked and the lock is verified in continuous integration alongside linting, formatting, targeted
static type checking, and a demonstration and continuous-integration-scale population build.

### 14.2 Determinism

The population and network layers derive every choice from `SHA-256(seed | key-parts)` rather than from a
sequentially advanced generator. Results are therefore invariant to call order and to internal loop
reordering — a stronger guarantee than seeding alone. Observation and intervention randomness is
namespaced hierarchically (latent seed, then observation or intervention identity, then a stable
per-event or per-agent key), so streams cannot collide across replicates or configurations.

### 14.3 Artifact identity

Each artifact carries a manifest with per-file sizes and SHA-256 checksums, the parent artifacts' logical
hashes, the configuration hash, the engine version, the Git commit, a dirty-worktree flag and the seeds.
Distinct hashes carry distinct meanings — configuration, scenario, latent outcome, artifact bundle — so a
presentational change can be distinguished from a scientific one. Because the dirty-worktree flag is
recorded, a result produced from an uncommitted tree is self-identifying.

### 14.4 Assessment as a scientific reproducibility system

Judged as a scientific rather than a software artefact, this is the strongest component of the project.
The chain from a checksummed published source, through a named transformation, to a hash-identified
artifact whose scientific content can be independently re-derived, is complete and machine-checkable.
Suppressed data is preserved as censored rather than imputed; source conflicts are surfaced; derived
quantities name their transformation; assumptions are labelled as assumptions.

Three gaps remain in the provenance surface itself, each small but each undercutting the completeness
claim: the nine travel route edge weights are hard-coded literals absent from both provenance tables
despite being direct per-edge beta multipliers; the school-calendar provenance block is keyed on the
configured year rather than verified against the registered snapshot; and two demonstration seasonality
profiles cite a registered source identifier for an invented shape. Two ingested evidence items — the
sector-by-size workplace cross-tab and the tenure-specific overcrowding gradient — are also loaded and
never consumed, and the housing attribute weights are literals rather than reads from the canonical table
holding the same values.

---

## 15. Verification

### 15.1 The five distinct activities

| Activity | Status |
|---|---|
| Software verification | Present, extensive |
| Scientific / model verification | Present, strong |
| Calibration | Infrastructure only; synthetic recovery |
| Retrospective validation | Absent |
| Prospective validation | Absent |

### 15.2 Scientific verification

`scientific_verification.py` re-reads persisted artifacts and re-derives their scientific content rather
than trusting recorded diagnostics. For a transmission run it checks that: the compartment sum is
constant across the horizon; daily new infections equal local plus imported; cumulative totals equal the
running sum of local, imported and seeded; the parish, age and route tables each sum to the matching
daily flow on every date; the transmission-event table reconciles to the daily flows by source kind; and
the attribution diagnostics match the event table. Every output file is checked by size and checksum
first, and paths are constrained to the artifact directory. Ensemble, comparison, intervention and travel
artifacts have their own verifiers; travel verification additionally defeats logical tampering that
updates the manifest checksum, by re-deriving the episode, visitor, temporary-network, latent-outcome,
scenario and bundle hashes from the tables themselves.

This materially raises confidence that **what the artifacts report is what the model did.** It says
nothing about whether what the model did resembles Jersey.

### 15.3 Where verification is weaker

Three diagnostics assert rather than measure: the occupational double-counting audit tests institutional
staff for primary jobs in the very collection from which those rows were removed, so its zero is
structurally guaranteed; the repeated-edge rate is set to 1.0 without measurement for routes declared
"fixed", including a workplace route whose executed edge set in fact varies daily with attendance; and a
declared housing-proportion tolerance is never applied to anything. The underlying behaviours are
acceptable, but presenting an assertion as an observation is the failure mode verification exists to
exclude.

Coverage is also scale-limited: every integration test runs at the 3,000-agent continuous-integration
scale, where there is no nursing care home, no detention setting, no children's home and exactly one
school per type — so the nursing staffing branch and multi-school allocation are never exercised end to
end, and the full-scale figures that support the scientific claims exist as narrative documentation
rather than as enforced regression contracts.

### 15.4 Computational exercise

Recorded full-scale executions are a two-day generic run producing 19 events (10 seeded, 9 local, 0
imported) at 73.28 seconds and 911 MB peak resident set size, and a seven-day scaled-travel run at 174.38
seconds and 1.24 GB. The default run configuration is 30 days; the school calendar caps a run at 360 days
from the default start; and literal source-scale travel execution is bounded to roughly 79 days by the
materialised-episode limit.

**No full-population, full-horizon epidemic has been executed.** Behaviours that appear only at epidemic
scale — peak dynamics, susceptible depletion, waning-driven oscillation, saturation of the sampled travel
routes — have not been observed, so neither their plausibility nor the computational feasibility of
observing them is established. This is the most important single gap in the platform's evidence base.

---

## 16. Example scientific workflows

The workflows below are supported by the implemented command-line interface and API. **No numerical
results are presented, because JOS v1 has produced none that would be appropriate to report**: the
recorded executions are construction benchmarks and short smoke tests. Each workflow is described with
the outputs it produces and the disclosures that must accompany them.

### 16.1 Baseline simulation

Generate the population, structure, staffing and networks at the chosen mode; run the generic respiratory
model for the configured horizon; observe the latent run.

*Outputs:* daily epidemic series with the five infection streams separated; parish, age and route
stratifications; the full transmission-event table with attributed route and competing-candidate
evidence; observed and reported case series with delay distributions; diagnostics and a verifiable
manifest.

*Required disclosures:* parameters are demonstration assumptions, not pathogen estimates; `attack_rate` is
cumulative incidence per capita rather than the proportion ever infected; the epidemic is sharper and
less variable than a model with dispersed stage durations and heterogeneous contact would produce; in the
shipped observation configuration detection precedes infectiousness.

*Recommended additions before any baseline is presented:* peak timing and height, final size, route
shares reported with the candidate-count distribution, the realised generation-interval distribution, and
per-agent daily edge counts by age band as a contact-plausibility check.

### 16.2 Intervention comparison

Run a baseline and an intervention scenario at matched seed with identical population, structure and
network parents; compare.

*Outputs:* scenario comparison rows on health outcomes; route-shift rows showing where transmission moved
between routes; paired per-seed differences; intervention state, event log and route-effect diagnostics
recording effective edge counts and mean, minimum and maximum multipliers per route per day.

*Required disclosures:* the comparison is a simulated contrast under declared assumptions, not an estimate
of policy effectiveness; adherence is per route rather than per person, which removes the fully
non-adherent tail and biases benefit upward; there is no behavioural substitution, so measured benefit
can never be adverse; detection-triggered scenarios additionally inherit the onset-anchor bias;
common-random-number coupling decays after divergence, so a single seed pair is not a clean contrast.

### 16.3 Ensemble analysis

Run N replicate seeds under one configuration; summarise as median with quantile bands; optionally
compare two ensembles at matched seeds.

*Outputs:* per-replicate trajectories; quantile summaries with explicit metric semantics and replicate
accounting; failed-replicate records; matched-seed paired differences.

*Required disclosures:* bands are stochastic replicate variation over a fixed population and a fixed
parameter vector — not confidence, credible or prediction intervals; parameter and structural uncertainty
are absent entirely; extreme quantiles from small ensembles approximate the observed range; the two
dominant sources of individual-level stochastic variability are suppressed by construction.

*Recommended practice:* report the replicate count beside every band, and prefer an interquartile summary
for small ensembles.

### 16.4 Travel and importation experiment

Configure arrival volumes, seasonality, visitor behaviour and border measures; run with the travel
manager; compare against a zero-travel or reduced-arrival configuration; optionally sweep the supported
sensitivity axes (visitor community contacts, terminal mixing contacts, arrival prevalence).

*Outputs:* daily travel population with arrivals, departures and present population; travel episode and
visitor population tables; daily temporary edge lists with route and weight; visitor-attributed
transmission with event-time identity; arrival-test and quarantine event logs; separated resident and
visitor incidence and attack rates.

*Required disclosures:* the annual anchors are passenger movements, not unique tourists; no shipped
configuration preserves the real traveller-to-resident ratio; visitor-to-resident mixing does not scale
with arrival volume, so arrival-volume results are not elasticities; arrival prevalence is a free dial and
results are approximately linear in it; arrival testing has no incubation-dependent sensitivity and is
therefore an upper bound on detection; resident absences beginning inside the horizon are not applied at
runtime; the headline compartment columns include active visitors.

*Recommended practice:* report movements per resident-year alongside every travel result, and present
visitor-driven outputs as a function of arrival prevalence rather than at a single value.

### 16.5 Synthetic calibration recovery

Hide a parameter, generate target observations from the model itself, search, and verify on held-out
seeds.

*Outputs:* the full retained trial table with objective components; recovered value and recovery error;
held-out verification; diagnostics recording that no real Jersey data was used.

*Required disclosures:* this demonstrates that the estimation machinery works, not that any parameter is
estimated for Jersey; recovery is over-precise because truth and candidate share the same generative
model, network and population; the objective is an unweighted sum of squares on counts and returns a
point without an interval; transmission parameters remain non-identifiable in the full model.

---

## 17. Scientific interpretation

### 17.1 What a JOS result is

A JOS result is the behaviour of a specified stochastic mechanism operating on a specified synthetic
structure under specified parameters. Its epistemic status is that of a controlled computational
experiment: it establishes what follows from the assumptions, given the structure. It does not establish
what will happen in Jersey, and it does not establish what would happen under a real intervention.

This is a legitimate and productive mode of epidemic modelling — the mode in which structurally detailed
individual-based models have been most useful — provided the boundary is stated rather than implied.

### 17.2 Where the structure is strong and where it is weak

The pattern is informative. **JOS is strong wherever the question is structural** — which routes exist,
how settings interlock, what reconciles to what, what is traceable to which source, whether an artifact's
content is internally consistent. **It is weak wherever the question is distributional** — how much
individuals vary, how heavy the tails are, how uncertain the answer is.

The homogeneity assumptions all push in the same direction. Fixed contact degree, deterministic stage
durations, per-route adherence and attenuation-only interventions each make simulated epidemics sharper,
more synchronised, less variable and more controllable than reality. That is a coherent bias with a
knowable sign, which makes it disclosable rather than disqualifying, and it is largely addressable.

### 17.3 Conservative language

The following wording is used throughout this report and is recommended for any presentation of JOS
results:

| Prefer | Avoid |
|---|---|
| "under the specified assumptions" | (unqualified assertion) |
| "within the synthetic population" | "in Jersey" |
| "the model represents" | "the model shows" |
| "the simulation suggests" | "the simulation predicts" |
| "simulated transmission pathway" | "transmission route" (as fact) |
| "scenario comparison" | "intervention effectiveness" |
| "stochastic replicate variation" | "confidence interval" |
| "cumulative simulated incidence" | "attack rate" |
| "passenger movements" | "visitors" or "tourists" |
| "regulatory minimum staffing" | "staffing levels" |

### 17.4 Jersey-specific interpretation

Two Jersey features are represented well and should be foregrounded: the empirically anchored
concentration of daytime working population in St Helier, and importation as an explicit, port-anchored,
provenance-tracked mechanism rather than an assumed boundary condition. For an island with two ports of
entry, the second is a genuine methodological advantage.

Three Jersey features are represented poorly enough to bound interpretation: daytime school geography
does not exist, since every school resolves to St Helier with no catchment; the parish transport gradient
is inverted relative to its own documented definition; and the care sector — which in a respiratory
outbreak is the setting where consequence concentrates — is compromised on three axes simultaneously
(residents too young, homes equal-sized, and residents mixing in the general community at free-living
rates).

Finally, a population of about 104,540 sits in the critical-community-size regime where stochastic
fadeout and reintroduction govern persistence (Bartlett 1957; Keeling and Grenfell 1997). This is where
Jersey is scientifically most interesting, and where JOS's importation layer is best matched to the
question — but it is also where the suppressed heterogeneity bites hardest, because extinction
probability is precisely the quantity that overdispersion controls. Addressing heterogeneity and
executing a long-horizon baseline would together open the question the platform is best placed to
answer.

---

## 18. Limitations

Summarised here by category; the companion audit records 128 classified findings with file-level
evidence, of which 45 are major limitations.

**Data.** No household size distribution, communal establishment size distribution, care-home age
profile, employment-by-age headcount, sector-by-age table, multiple-job-holding rate, monthly visitor
profile, visitor demographic profile or accommodation-stock source exists in the registry. No Jersey
epidemiological series of any kind is registered. Two ingested evidence items are never consumed. The
work-from-home level is a pandemic-period measurement. The two school-staffing releases are mutually
inconsistent and only one is used, and its universe excludes independent schools whose staff are drawn
from it.

**Parameters.** All disease parameters are demonstration assumptions. Route relative weights are
unanchored and redundant with the route multipliers over the same product. The indoor:outdoor ratio is
low relative to the literature's direction. Nine travel edge weights sit outside the provenance surface.
Arrival prevalence is a free dial on which visitor results depend approximately linearly. Transmission
parameters are structurally non-identifiable.

**Structure.** No individual-level contact heterogeneity, hence no overdispersion or superspreading.
Deterministic stage durations. No presymptomatic infectiousness. Waning to full susceptibility. No
severity, hospitalisation or mortality. Care residents not excluded from the general community route.
Workplace size tail truncated at 173 employees with no hospital as a setting. School type nearly
perfectly confounded with pupil age. Care staff serve one home each, with 133 of 164 communal
establishments unstaffed. No further-education setting. Reduced-scale modes delete institution categories
rather than scaling them.

**Behaviour.** Per-route rather than per-person adherence. No substitution, displacement or adherence
fatigue. Binary work-from-home allocated uniformly at random across sectors. Vaccination reaching only
current susceptibles. Travel parties not co-located. Unanchored visitor contact intensities.

**Geography.** Parish is the finest spatial unit. Every school in St Helier. Inverted parish no-car
gradient. Identical household composition in every parish. Same-parish-only community mixing. Terminal
resident pool hard-coded to St Helier. Accommodation allocated by household counts.

**Validation.** No retrospective validation, no prospective validation, no Jersey calibration. No
full-population, full-horizon epidemic executed. No demonstrated consistency with any contact survey.
All integration tests at a scale where the relevant institutions do not exist. Three diagnostics assert
rather than measure.

**Observation.** Onset anchor decoupled from natural history, with detection preceding infectiousness in
the shipped configuration. Symptomatic status uncorrelated with infectiousness. Cohort-mixing per-day
ascertainment fraction. No testing-capacity structure. Empty resident stratifications in travel runs.

**Uncertainty.** Bands cover network, transmission and observation stochasticity only. No parameter or
structural uncertainty. Extreme quantiles from small ensembles. No distributional summary of paired
differences. Suppressed heterogeneity narrows even the stochastic component.

**Computation.** Full-scale network construction about 73 seconds at roughly 0.9 GB; seven-day travel
epidemic about 174 seconds at 1.24 GB. Literal source-scale travel execution capped near 79 days. Runs
capped at 360 days by the reference-year calendar. No parent-artifact caching, so replicate cost is
dominated by network construction. Fixed daily timestep.

---

## 19. Validation roadmap

Validation should proceed in the order below, because each stage's interpretation depends on the
preceding one.

**Stage 1 — Internal face validity at full scale.** Execute and archive a full-population, full-wave
baseline ensemble with diagnostics on peak timing and height, final size, route shares with
candidate-count distribution, realised generation interval, and per-agent daily contact-opportunity
counts by age band. This is currently missing and everything else depends on it.

**Stage 2 — Contact-structure plausibility.** Compare the age-stratified per-agent daily
contact-opportunity distribution against an empirical contact survey (POLYMOD or CoMix) for magnitude and
age pattern. This is not a calibration; it is a check that the structure is in the right region. If it
is, the result should be published as evidence; if not, the route parameters need revisiting.

**Stage 3 — Structural sensitivity and uncertainty decomposition.** Global sensitivity analysis over the
declared parameter space, with variance decomposition separating stochastic from parametric
contributions, so that intervals can be reported honestly.

**Stage 4 — Retrospective reconstruction.** Register a Jersey epidemiological series and attempt to
reconstruct a known outbreak, fitting only ascertainment and a single transmission intensity while
holding the structure fixed, and reporting how much of the observed epidemic shape the synthetic
structure reproduces without further tuning. Candidate targets: Jersey COVID-19 case notifications with
testing volumes and the documented border-testing regime (the highest-value target, because it exercises
the travel, observation and intervention layers simultaneously, and because Jersey's two-port boundary
makes importation unusually observable); seroprevalence surveys if any exist, which would constrain
cumulative infection independently of ascertainment; influenza or RSV sentinel surveillance for a
multi-season seasonality and recurrence test; care-home outbreak records as a direct test of the
closed-setting structure; and school absence data as an indirect check on school-route intensity.

**Stage 5 — Out-of-sample structural validation.** Hold out a period or a setting entirely and assess
whether structural conclusions — the ordering of route contributions, the relative ranking of
interventions — are reproduced without refitting. This tests the structure rather than the fit and is the
more meaningful test for a mechanistic model.

**Stage 6 — Prospective evaluation, if ever appropriate.** Only after Stages 1–5, and only with
pre-registered predictions and explicit uncertainty. Nothing in v1 supports this and it should not be
attempted from the current base.

An immediate, small improvement available at any point: replace the invented monthly seasonality shape
with the observed Ports of Jersey monthly series.

---

## 20. Future development

Grouped by what each group would change about the model's standing. The companion roadmap develops these
with dependencies and acceptance criteria.

**Scientific hardening (would remove current disclosure requirements).** Exclude care-home residents from
the general community route; constrain the symptom-onset anchor to the disease timeline and extend the
chronology check; introduce a persistent per-agent contact-rate multiplier; replace deterministic stage
durations with distributions; correct the school-type age collapse, the degenerate school parish, the
inverted parish no-car allocation and the runtime resident-absence gap; make adherence a per-person
trait; compute the three asserted diagnostics from realised artifacts; rename `attack_rate`; promote the
travel edge weights into the provenance surface; add a full-mode institutional regression test.

**Structural enrichment (would extend the question set).** Household size and age-gap distributions
fitted to census data; a right-skewed workplace size distribution with a realistic tail and the hospital
represented as a named large workplace with a healthcare-worker route; institutional size distributions;
school catchments with parish weighting; a further-education setting; cross-facility care staffing and
staffing for detention and children's homes; sector-specific and partial remote working; behavioural
substitution and adherence fatigue; presymptomatic and asymptomatic infectiousness with a symptom state
in the disease model; partial immunity on waning; severity, hospitalisation and mortality with a
healthcare-capacity layer.

**Inferential capability (would change the class of claim available).** A single identifiable per-route
intensity replacing the redundant parameterisation; parameter ensembles with declared priors; global
sensitivity analysis; likelihood-free or Bayesian calibration returning posteriors rather than points;
count-appropriate likelihoods; paired-difference distributional summaries; a mis-specification arm in the
calibration tests.

**Empirical extension (would change what the model is anchored to).** Registration of Jersey
epidemiological series; observed visitor seasonality and demographics; accommodation stock by parish; an
empirical contact-survey comparison; sector-by-size workplace allocation using the already-ingested
cross-tab; a care-home resident age profile from a registered source.

**Research extensions.** Multi-strain and variant dynamics; vaccination history and waning cohorts;
repeated importation and reintroduction dynamics in the critical-community-size regime; optimal
allocation of finite border-testing capacity; the value of care-sector-targeted measures under a
corrected care structure; and structural-uncertainty assessment through comparison against an independent
model of the same population.

---

## 21. Conclusion

The Jersey Outbreak Simulator v1.0 is a structurally detailed, provenance-anchored, agent-based epidemic
simulation framework for Jersey, built to an unusually high standard of evidence traceability and
internal verifiability. Its principal contribution is not an epidemiological result — it presents none,
and correctly claims none — but a complete and auditable chain from official published aggregates,
through a synthetic population reconciled exactly to registered controls, through eleven separable
contact routes, to simulation artifacts whose scientific content can be independently re-derived and
whose provenance is machine-checkable.

Assessed as a research instrument, the platform's strengths are the exhaustive provenance and evidence
classification, the structurally enforced separation of latent infection from observed cases, verification
that re-derives rather than re-asserts, genuine route separability with nested-route double counting
eliminated, an order-invariant attribution layer that retains its competing-candidate evidence, a
correct solution to identity binding under agent-slot reuse in the travel layer, and a consistent refusal
to claim more than the evidence supports.

Its limitations are equally clear and cluster informatively. The model suppresses individual-level
heterogeneity in both contact rate and infectious duration, so it cannot represent overdispersion or
superspreading and its epidemics are sharper and less variable than reality. Its intervention semantics
are one-sided, biasing measured benefit upward. Its uncertainty quantification covers stochastic
replicate variation only. Its transmission parameters are structurally non-identifiable. It has no
calibration to Jersey data, no external validation, and no executed full-population epidemic. A small
number of specific structural defects — care-home residents mixing freely in the community, school type
confounded with pupil age, all schools resolving to a single parish, an inverted parish transport
gradient — currently invalidate specific named outputs and each is locally correctable.

None of this invalidates JOS v1 as a synthetic experimentation framework, because the framework does not
claim what those limitations would undermine. The appropriate description is a verified, reproducible,
honestly bounded synthetic research platform whose epidemiological outputs are experiments on declared
assumptions rather than statements about Jersey. With contact and duration heterogeneity introduced, a
full-wave baseline executed and archived, and a Jersey epidemiological series registered for retrospective
reconstruction, the platform would move from verified to partially validated — and Jersey's small
population and two-port boundary would make it a genuinely distinctive instrument for questions about
importation, persistence and stochastic extinction that larger, less well-bounded settings cannot
address as cleanly.

---

## 22. References

### External scientific literature

1. Bartlett MS. Measles periodicity and community size. *Journal of the Royal Statistical Society, Series
   A* 1957;120(1):48–70.
2. Beckman RJ, Baggerly KA, McKay MD. Creating synthetic baseline populations. *Transportation Research
   Part A: Policy and Practice* 1996;30(6):415–429.
3. Bulfone TC, Malekinejad M, Rutherford GW, Razani N. Outdoor transmission of SARS-CoV-2 and other
   respiratory viruses: a systematic review. *The Journal of Infectious Diseases*
   2021;223(4):550–561. doi:10.1093/infdis/jiaa742
4. Chao DL, Halloran ME, Obenchain VJ, Longini IM Jr. FluTE, a publicly available stochastic influenza
   epidemic simulation model. *PLOS Computational Biology* 2010;6(1):e1000656.
5. Chowell G. Fitting dynamic models to epidemic outbreaks with quantified uncertainty: a primer for
   parameter uncertainty, identifiability, and forecasts. *Infectious Disease Modelling*
   2017;2(3):379–398.
6. Eubank S, Guclu H, Anil Kumar VS, Marathe MV, Srinivasan A, Toroczkai Z, Wang N. Modelling disease
   outbreaks in realistic urban social networks. *Nature* 2004;429:180–184.
7. Ferguson NM, Cummings DAT, Fraser C, Cajka JC, Cooley PC, Burke DS. Strategies for mitigating an
   influenza pandemic. *Nature* 2006;442:448–452.
8. Grefenstette JJ, Brown ST, Rosenfeld R, DePasse J, Stone NTB, Cooley PC, et al. FRED (A Framework for
   Reconstructing Epidemic Dynamics): an open-source software system for modeling infectious diseases and
   control strategies using census-based populations. *BMC Public Health* 2013;13:940.
9. Grimm V, Railsback SF, Vincenot CE, Berger U, Gallagher C, DeAngelis DL, et al. The ODD protocol for
   describing agent-based and other simulation models: a second update to improve clarity, replication,
   and structural realism. *Journal of Artificial Societies and Social Simulation* 2020;23(2):7.
   doi:10.18564/jasss.4259
10. Halloran ME, Ferguson NM, Eubank S, Longini IM Jr, Cummings DAT, Lewis B, et al. Modeling targeted
    layered containment of an influenza pandemic in the United States. *Proceedings of the National
    Academy of Sciences* 2008;105(12):4639–4644.
11. Hazelbag CM, Dushoff J, Dominic EM, Mthombothi ZE, Delva W. Calibration of individual-based models to
    epidemiological data: a systematic review. *PLOS Computational Biology* 2020;16(5):e1007893.
12. Hinch R, Probert WJM, Nurtay A, Kendall M, Wymant C, Hall M, et al. OpenABM-Covid19 — an agent-based
    model for non-pharmaceutical interventions against COVID-19 including contact tracing. *PLOS
    Computational Biology* 2021;17(7):e1009146.
13. Jarvis CI, Van Zandvoort K, Gimma A, Prem K, CMMID COVID-19 working group, Klepac P, et al.
    Quantifying the impact of physical distance measures on the transmission of COVID-19 in the UK. *BMC
    Medicine* 2020;18:124.
14. Keeling MJ, Grenfell BT. Disease extinction and community size: modeling the persistence of measles.
    *Science* 1997;275(5296):65–67.
15. Kerr CC, Stuart RM, Mistry D, Abeysuriya RG, Rosenfeld K, Hart GR, et al. Covasim: an agent-based
    model of COVID-19 dynamics and interventions. *PLOS Computational Biology* 2021;17(7):e1009149.
16. Kerr CC, Stuart RM, Abeysuriya RG, Sanz-Leon P, Cohen JA, Klein DJ, et al. Starsim: a flexible
    framework for agent-based modeling of health and disease. *Proceedings of the 23rd Python in Science
    Conference (SciPy 2024)*. doi:10.25080/ukpu4584
17. Krylova O, Earn DJD. Effects of the infectious period distribution on predicted transitions in
    childhood disease dynamics. *Journal of the Royal Society Interface* 2013;10(84):20130098.
    doi:10.1098/rsif.2013.0098
18. Lloyd AL. Destabilization of epidemic models with the inclusion of realistic distributions of
    infectious periods. *Proceedings of the Royal Society B* 2001;268(1470):985–993.
19. Lloyd-Smith JO, Schreiber SJ, Kopp PE, Getz WM. Superspreading and the effect of individual variation
    on disease emergence. *Nature* 2005;438(7066):355–359.
20. Madewell ZJ, Yang Y, Longini IM Jr, Halloran ME, Dean NE. Household transmission of SARS-CoV-2: a
    systematic review and meta-analysis. *JAMA Network Open* 2020;3(12):e2031756.
21. Mossong J, Hens N, Jit M, Beutels P, Auranen K, Mikolajczyk R, et al. Social contacts and mixing
    patterns relevant to the spread of infectious diseases. *PLOS Medicine* 2008;5(3):e74.
22. Pokutnaya D, Childers B, Arcury-Quandt AE, Hochheiser H, Van Panhuis WG. An implementation framework
    to improve the transparency and reproducibility of computational models of infectious diseases. *PLOS
    Computational Biology* 2023;19(3):e1010856.
23. Wearing HJ, Rohani P, Keeling MJ. Appropriate models for the management of infectious diseases. *PLOS
    Medicine* 2005;2(7):e174.

### Repository evidence

Repository evidence is cited inline by file path, class, function and configuration key rather than
enumerated here. The primary scientific modules are `data_pipeline.py`, `population_controls.py`,
`population_generator.py`, `population_structure_controls.py`, `population_structure_generator.py`,
`staffing_evidence.py`, `staffing_generator.py`, `network_generator.py`, `starsim_adapter.py`,
`respiratory.py`, `outbreak_runner.py`, `observation_scheduler.py`, `observation.py`, `interventions.py`,
`intervention_analysis.py`, `travel.py`, `ensemble.py`, `calibration.py`, `scientific_verification.py`,
`scientific_hashes.py` and `verification_archive.py`, all under `src/jersey_outbreak/`. Documents of
record are `README.md`, `docs/scientific_scope.md`, `docs/architecture.md`, `docs/interventions.md`,
`docs/progress.md` and `data/sources.yaml`. The 22 primary data sources are registered in
`data/sources.yaml` with publisher, URL, reference period, licence and SHA-256 checksum; readers should
consult that registry rather than a secondary list, since it is the authoritative and checksum-verified
record.

### Note on the model description standard

This report follows the substance of the ODD protocol for describing agent-based models (Grimm et al.
2020) — overview, design concepts, details — without adopting its section headings, since the required
report structure differs. Readers seeking a strict ODD-conformant description should note that the
elements it requires are present here: purpose and patterns (Sections 2, 17), entities and state
variables (Sections 5, 7), process overview and scheduling (Sections 3, 6.3, 8, 10.1), design concepts
including stochasticity, heterogeneity and observation (Sections 6.5, 7.4, 9, 12), initialisation
(Sections 5, 7.2), input data (Section 4) and submodels (Sections 5–11). A dedicated ODD-conformant
appendix would be a worthwhile addition for journal submission.

---

*Prepared as an independent scientific technical report on the frozen `jos-v1.0.0` release at commit
`9e9ce3abc4201cd8303c723015462d21ca237800`. No implementation code, configuration, parameter or existing
document was modified in its preparation. Companion documents:
[`JOS_V1_SCIENTIFIC_AUDIT.md`](JOS_V1_SCIENTIFIC_AUDIT.md) (128 classified findings with file-level
evidence) and [`JOS_V1_SCIENTIFIC_ROADMAP.md`](JOS_V1_SCIENTIFIC_ROADMAP.md).*
