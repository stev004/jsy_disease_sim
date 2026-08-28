# Scientific scope and limitations

## Current verified status

The C3 verification commit is `658364c7f02cf44f9392116e7db44c94bdb3175a`.
M0–M7 and corrective closures C1–C4 are PASS. The full
104,540-agent corrected stack constructs and executes through Starsim 3.5.2,
and the quantitative evidence is recorded in
[`progress.md`](progress.md). M7 adds intervention experiments; API/UI and
visitor/travel work remain outside scope.

## What this repository demonstrates

Milestone 0 demonstrates that the pinned Starsim 3.5.2 API can execute a small
official SIR simulation with its built-in `RandomNet`, and that a JOS command
can emit a reproducible summary and provenance manifest.

This is a software compatibility and reproducibility spike. It is not an
epidemiological model of Jersey and does not use Jersey residents, addresses,
schools, workplaces, parishes, surveillance data or disease-specific Jersey
parameters.

Milestone 1 adds official Jersey aggregate controls from registered 2021,
2024 and 2025 source snapshots. These are evidence inputs for later work, not
synthetic residents and not a validated outbreak reconstruction. Reference
periods, universes, rounding, suppression and source conflicts remain visible
in the canonical tables and quality report.

Milestone 2 uses those controls to generate wholly synthetic residents at CI,
scaled and full population sizes. Parish counts are scaled shares, detailed
age/sex cells use a documented raking transformation, and household and
communal-setting counts are derived from the available aggregate controls.
Housing, crowding and car-access attributes are broad generated controls, not
individual-level observations. Diagnostics preserve input hashes and list the
assumptions and transformations. This layer has no contacts and makes no claim
to reproduce actual household identities, addresses or movements.

Milestone 3 adds a synthetic daytime-structure layer linked to the immutable
Milestone 2 resident IDs. School types, classes, employment sectors, workplace
size bands, synthetic work parishes and commute modes are generated from the
registered aggregate controls. A small bounded secondary-job rate is an
explicit scenario assumption, not an observed individual-level statistic.
School, workplace and team identities are synthetic. The COVID-period
work-from-home measure is retained as a baseline assumption with provenance,
and the right-censored 50+ workplace band receives a structural range rather
than invented exact employer sizes. The 2021 resident-worker universe is kept
separate from 2025 filled-job and private-undertaking controls; the generator
does not claim to link those different statistical universes at individual
level. The published sector-by-size workplace rows do not exactly reconcile to
the total size-band row, so the implementation does not invent that missing
cross-tab. This layer still has no transmission routes, contact edges, disease
states, visitors or inference about named people or institutions.

Milestone 4 adds a disease-agnostic contact-structure layer. It generates
separable household, school class/cross-class, workplace team/transient, care,
shared-vehicle, synthetic transit, indoor-community and outdoor-community
routes from M2/M3 memberships. Household, class, team and bounded care cohorts
are repeated structures; sampled routes refresh on their declared daily or
periodic schedule. Calendar rules distinguish weekdays, weekends, school term
and physical work from WFH-only days. All edges are canonical undirected pairs
with finite relative contact-opportunity weights, not pathogen-specific beta
values.

C2 makes nested route semantics explicit. The school cross-class and workplace
transient candidate pools exclude pairs already represented by their respective
class-core and team-core routes. Other cross-route overlap is retained only
when it represents a distinct physical exposure opportunity, and is reported in
the route-overlap matrix rather than silently treated as duplicate storage.
Community routes use a configurable structural broad-age mixing matrix and a
regular-contact pool plus daily refreshed contacts. The matrix is not Jersey
contact-diary evidence, and persistence parameters are scenario assumptions.
The common school calendar is a frozen official reference-year term/holiday
calendar; institution-specific inset days are not modelled.

The commute source available to the canonical M3 build provides an aggregate
car category rather than a compatible individual driver/passenger roster. The
shared-vehicle route therefore uses only bounded same-household car commuters
with a common synthetic work parish, records unmatched car commuters, and
does not represent car-alone commuters as shared rides by default. These are
synthetic constraints, not inferred Jersey carpools.

There are no observed teacher rosters, care staff rosters, bus routes/stops,
real carpools, named community venues or GPS paths in the available evidence.
M4.1 therefore uses official CYPES FTE controls plus a documented
FTE-to-synthetic-endpoint conversion for school staff, and the 2026 Care
Commission regulatory minimums plus a configurable shift-coverage assumption
for supported care homes. Neither source is treated as a real staff roster:
school placement, class assignment, care roster construction and all staff
contacts are synthetic/structural. Other communal settings remain outside this
care-home closure. Cross-class, workplace-transient, transport and community
mechanisms remain scenario assumptions. The route generator is
Starsim-independent; only the adapter constructs Starsim 3.5.2 `ss.Network` and
`ss.DynamicNetwork` objects. M4.1 is not an outbreak model and does not
implement a disease, intervention, visitor or observation process.

M4.1 also prevents occupational double-counting: for institutional staff, the
existing M3 primary job is reinterpreted as the synthetic school/care role for
ordinary workplace routes, while declared M3 secondary jobs remain eligible.
M3 job rows and counts are unchanged, and household, community and transport
participation is retained.

## Milestone 5 generic respiratory disease

M5 adds a pathogen-neutral daily SEIRS demonstration behind the Starsim 3.5.2
disease/adapter boundary. It uses the existing M4.1 route objects and weights;
Starsim performs the network transmission draw. The active states are
susceptible, exposed, infectious and recovered, with optional configurable
immunity waning. The default parameter file contains demonstration values
labelled `scenario_assumption`; it does not name or parameterize influenza,
COVID-19, RSV or another real pathogen.

Initial seeds, generic exogenous imports and locally acquired infections are
reported separately. Each local infection is attributed to one of the 11
configured M4 route IDs and retains an infector UID when Starsim supplies one.
Same-timestep multiple-route opportunities preserve Starsim's union infection
occurrence while attribution selects among successful route hazards with a
stable target/timestep draw that does not depend on route insertion order.
Daily tidy outputs are latent truth: no ascertainment,
reporting delay, detected-case, calibration, ensemble or observation model is
included.

Severity, disease deaths, symptom substates, age susceptibility, seasonality,
visitors, arrivals, ports, interventions and API/UI functionality are outside
the M5 boundary. Consequently the `severe` and `dead` output columns remain
zero by design, and M5 is a demonstration validation level rather than a
forecast or clinical model.

## Milestone 6 observation, ensembles and synthetic recovery

M6 consumes an immutable M5 `OutbreakRunResult`. Its observation layer adds
synthetic symptomatic classification, weekday effects, detection/ascertainment
and non-negative reporting delays; it does not mutate M5 transmission events or
latent hashes. The demonstration observation configuration is explicitly
`scenario_assumption`. No Jersey surveillance series is treated as an observed
calibration target.

M6 ensembles require an explicit ordered list of unique replicate seeds. They
retain each successful or failed replicate, summarize only successful outputs
with declared linear quantiles, and preserve latent route/parish/age metrics
alongside detected and reported metrics. Matched comparisons pair the same seed
identities across A/B configurations. A process-pool request may be recorded as
`sequential_fallback` when the host disallows its semaphore capability; this is
an execution-environment diagnostic, not a claim of parallel execution.

The calibration harness is a synthetic recovery test, not parameter estimation
for Jersey. It can hide a reporting delay or generic transmission beta,
generates fully detected truth from the generic M5 model, retains every grid
trial, and checks recovery on fresh synthetic seeds. Beta recovery also emits
profiles under altered ascertainment and route-weight assumptions to expose
confounding. Its truth, candidate and held-out results are separate from
official Jersey evidence and cannot establish model validity.

### Milestone 6 / C3 observation semantics

C4 keeps the latent M5 event table intact while making the observation timeline
runtime-causal: infection, optional generic symptom-onset anchor, testing/
detection, and report dates are separate fields. Infection schedules are
sampled when events occur and due notifications are delivered after that day's
transmission. The M7 consumer can first affect the next timestep. The analysis horizon is the
complete latent horizon plus either an explicitly configured delay tail or the
maximum configured symptom, detection and reporting delays. Latent incidence is
therefore conserved even when an event is never detected or reported. Detection
notifications are exposed through a read-only interface for the M7
intervention consumer; C4 itself does not implement intervention logic.

Observation draws use a stream derived from latent replicate seed, observation
seed and configuration identity, with stable event keys. Different latent
replicate seeds therefore do not silently reuse the same observation random
sequence. Ensemble summaries use explicit date grids: missing incidence is a
structural zero, cumulative values carry forward, and state/prevalence is not
fabricated beyond the latent horizon. Failed replicates are non-contributors.
Requested, planned and actual process workers are recorded separately.

## Milestone 7 intervention experiments

M7 provides a typed, composable intervention framework over the synthetic M2–M4
population and M5 generic respiratory module. It supports detection-triggered
case isolation and household quarantine; school closure/reduction; workplace
and commute reduction with deterministic WFH schedules; separate community
indoor/outdoor reduction; care-home resident/staff protection; generic
vaccination with delay, efficacy and waning; and generic masking/gathering
route multipliers. Targets can use stable agent IDs, age bands, parishes,
sectors, schools, workplaces, care settings and care roles.

The runtime lifecycle is disease progression, M4 network refresh, intervention
state/effective-route updates, transmission/imports, C4 detection delivery and
next-timestep effect. A detection on day `t` cannot change transmission already
completed that day. Route effects compose multiplicatively and operate on
prospective Starsim views derived from immutable M4 snapshots. Care edges are
retained with zero effective beta when suppressed so roster topology remains
auditable. Vaccination affects susceptibility and infectiousness only; M5 does
not implement severity or mortality.

M7 experiments are matched-seed scenario comparisons and bounded ensembles.
They retain explicit config/run/provenance hashes, daily intervention state,
event logs, route-effect diagnostics, absolute route counts and relative route
shares, and separate social/intervention burden metrics. Every included YAML
value is a synthetic scenario assumption. These outputs do not estimate policy
effectiveness, identify causal effects from Jersey data, or validate the
contact mechanisms. Travel, arrivals, airports, ferries and visitor processes
remain deferred to M8.

C5 establishes exact-neutral and provenance semantics for those experiments.
Empty and mathematically neutral managers reuse untouched route arrays exactly;
nonzero-beta latent events, infectors, routes, hazard evidence, daily outputs
and latent hashes therefore match the no-manager run. `duration_days` means the
number of dated output points. Care protection can target only the explicit
nursing/non-nursing care-home classes. Global community route controls do not
invent an all-island `active_agents` denominator.

Vaccination `uptake_probability` is stable willingness for one agent/campaign,
not a repeated daily offer. Rollout controls timing and coverage bounds total
administration. Administration, protection becoming effective, current
protection and waning are separate event/state measures. Import schedules and
rates are exposure-attempt pressure; susceptibility modifies whether each
attempt becomes an imported acquisition, without replacing blocked attempts.
These are synthetic experiment semantics, not real vaccine-effectiveness or
travel-incidence claims.

M7 artifacts directly include the material latent epidemic tables and verify
their file hashes. Scenario/run, latent-outcome and artifact-bundle hashes have
separate roles. Optional masking/gathering controls remain experimental and
outside the core M7 PASS claim; ventilation is neither implemented nor claimed.

The verification archive is a separate retained index for ignored/generated
outputs. It records the clean Git commit, parent logical hashes, source-manifest
hashes, command results, benchmark metadata and hashes of retained summary
files. It does not turn local generated outputs into Git-tracked source, so the
archive and its external output bundle must be retained together for
reproducibility. The final C3 archive was independently hash-checked against
the current commit and parent logical hashes; its archive logical hash is
`32627c432c65e89250ee40d68a9382bb9b463f5076015dd6be5e62acab70bba4`.

The full M3 benchmark has 104,540 synthetic residents, 13,991 school
assignments, 8,500 private undertakings, 270 synthetic non-private workplaces
(8,770 operational workplaces) and 62,108 job assignments. Employer identity
and ownership remain synthetic and unobserved. These counts show that the
generated artifact reconciles to the selected controls; they do not validate
the underlying behavioural mechanisms or establish a Jersey contact network.

## Scientific rules

- Use synthetic people only; never imply that an agent represents a real
  resident.
- Keep population, contacts, disease biology, interventions and observation
  mechanisms separate.
- Distinguish latent infections from reported observations.
- Label inputs and transformations with their actual status, including
  `observed`, `regulatory_minimum`, `derived`, `synthetic`,
  `structural_assumption` or `unknown` where applicable.
- Do not expose synthetic household coordinates as real addresses or imply
  household/GPS precision that the evidence cannot support.
- Use ensembles and uncertainty intervals for stochastic scenario comparisons.
- Calibration is not validation; a fitted curve does not establish mechanism
  validity.
- Preserve code version, dependency lock, configuration, data snapshots and
  random seeds for reproducibility.
- Bound claims visibly: a working demo is not a forecast or policy authority.
- Treat a synthetic population as a latent modelling substrate, not as a list
  of real Jersey residents.

## Parameters in the spike

The SIR values are explicitly demo assumptions required to exercise the
official Starsim example. They are not named-pathogen parameters, Jersey
measurements or calibrated estimates. They must not be reused as a real
respiratory disease model without a later evidence and validation milestone.
