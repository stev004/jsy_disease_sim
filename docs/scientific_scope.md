# Scientific scope and limitations

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

There are no observed teacher rosters, care staff rosters, bus routes/stops,
real carpools, named community venues or GPS paths in the available evidence.
M4 therefore leaves school-staff and care-staff routes explicitly empty and
labels cross-class, workplace-transient, transport and community mechanisms as
scenario assumptions. The route generator is Starsim-independent; only the
adapter constructs Starsim 3.5.2 `ss.Network` and `ss.DynamicNetwork` objects.
M4 is not an outbreak model and does not implement a disease, intervention,
visitor or observation process.

The full M3 benchmark has 104,540 synthetic residents, 13,991 school
assignments, 8,500 workplaces and 62,108 job assignments. These counts show
that the generated artifact reconciles to the selected controls; they do not
validate the underlying behavioural mechanisms or establish a Jersey contact
network.

## Scientific rules

- Use synthetic people only; never imply that an agent represents a real
  resident.
- Keep population, contacts, disease biology, interventions and observation
  mechanisms separate.
- Distinguish latent infections from reported observations.
- Label inputs as `observed`, `derived`, `literature_prior`, `calibrated` or
  `scenario_assumption`.
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
