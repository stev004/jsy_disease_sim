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
