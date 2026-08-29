# Jersey Outbreak Simulator

Jersey Outbreak Simulator (JOS) is a local-first research prototype for
exploring infectious-disease transmission through a wholly synthetic Jersey
population. It is designed to keep population structure, contact mechanisms,
disease biology, interventions, observations and provenance separate.

## Current status

This repository contains **Milestones 0–9 plus corrective closures C1–C5**:
repository contracts, a verified
Starsim compatibility/reproducibility spike, a source-registered aggregate
evidence layer, a disease-agnostic synthetic Jersey population generator, and
synthetic daytime structure for schools, employment, workplaces and commuting,
plus a disease-agnostic Jersey route layer adapted to Starsim 3.5.2. M4.1
closes the school-staff and supported care-home staffing overlays using frozen
official evidence and explicit synthetic allocation assumptions; it does not
claim to reconstruct real staff rosters.
Milestone 5 adds a generic, pathogen-neutral daily respiratory SEIRS
demonstration. Its active states are susceptible, exposed, infectious and
recovered, with configurable immunity waning; severity, disease deaths,
symptom substates and named-pathogen parameters are explicitly deferred.
Milestone 6 adds a standalone observation layer, deterministic ensembles,
matched-seed A/B comparisons and a synthetic-only Optuna recovery harness.
Starsim owns network transmission, while JOS records
route-attributed latent infections and writes tidy daily epidemic, parish, age
and route tables. Demonstration values are scenario assumptions, not Jersey
surveillance controls.
The C4 correction samples observation schedules when infections occur, delivers
detections at their simulation timestep through a read-only consumer hook, and
uses metric-aware ensemble grids. Observation randomness remains isolated by
replicate/configuration, process execution records requested/planned/actual
workers, and synthetic held-out beta recovery remains available. Milestone 7,
as corrected by C5, adds the typed composable intervention runtime,
detection-triggered isolation and quarantine, calendar/contact families,
vaccination, matched-seed comparisons, intervention ensembles and
visualization-ready artifacts. M8 adds the separate travel/visitor layer.
Milestone 9 adds a loopback-only FastAPI interface, persistent SQLite job
execution, isolated workers, cancellation, restart reconciliation, verified
application result manifests and bounded dataset retrieval. No frontend or UI
is included. The quantitative gate record is in
[`docs/progress.md`](docs/progress.md), and the API contract is in
[`docs/api.md`](docs/api.md).
The Starsim demo is an official SIR example using Starsim's built-in
`RandomNet`; it is not a Jersey outbreak reconstruction or a validated
forecast. The Milestone 2 population is synthetic and control-driven; it is
not a sample of named people or real addresses.

C5 defines `duration_days` as the number of dated output points, including the
start and final dates. A manager-attached neutral scenario reuses canonical M4
route arrays without copying or float recasting, so its nonzero-beta latent
events, hazard evidence, daily trajectories and latent-outcome hash are exact
baseline equivalents. Scenario identity hashes the complete run config and all
M2/M3/M4, disease, observation, intervention, sensitivity and model-version
parents. M7 artifacts directly contain the five M5 latent tables alongside
intervention state/events and verify every persisted file hash.

Milestone 1 includes immutable official source snapshots, explicitly labelled
manual PDF transcriptions, canonical aggregate CSVs and deterministic data
quality reports. It does not include synthetic residents, household synthesis,
individual schools/workplaces/commutes, custom routes, a respiratory disease
module, observation, calibration, API or UI.

Milestone 2 adds CI (3,000), scaled (15,000) and full (104,540) population
generation modes. It produces versioned Parquet residents, private households
and communal-setting artifacts, plus JSON/Markdown diagnostics and a
reproducibility manifest. It does not create contacts, schools, workplaces,
commutes, mobility, disease transmission, visitors, API or UI functionality.

Milestone 3 consumes one validated Milestone 2 artifact and produces only
synthetic school/class assignments, employment sectors, bounded primary and
secondary jobs, synthetic workplaces/teams, work parishes and commute metadata.
It records the canonical control hashes, M2 input hashes, assumptions and
diagnostics in an immutable Parquet artifact. It does not create Starsim
networks or contact edges, disease states, interventions, visitors, an API or a
UI; it is not a Jersey outbreak model.

The verified full M3 artifact contains 104,540 residents, 48 synthetic schools,
703 classes, 13,991 school assignments, 8,500 private undertakings plus 270
synthetic non-private workplaces (8,770 operational workplaces), 4,387 teams
and 62,108 job assignments. All 50 M3 diagnostics checks pass. These are
synthetic structures and aggregate-control reconciliations, not observations
about named people, real schools, employer identities or workplace ownership.

Milestone 4 converts the validated M2/M3 artifacts into reproducible household,
school, workplace, care, transport and community route tables. It keeps fixed,
periodically refreshed and daily sampled contacts separate, applies weekday,
weekend, school-term and WFH schedule rules, and adapts the plain route tables
to Starsim `ss.Network`/`ss.DynamicNetwork` objects. M4.1 layers synthetic
teacher/TA/leadership and supported care-home staff memberships onto existing
M4 routes, preserving M3 worker/job accounting. School FTE controls remain
observed CYPES controls with a documented FTE-to-endpoint conversion; Care
Commission ratios are regulatory minima, not observed rosters. Institutional
staff primary jobs are reinterpreted for ordinary workplace routes, while
explicit secondary jobs remain; household, community and transport contacts are
preserved. It does not contain a custom disease, transmission calibration or
intervention model.

Milestone 5 consumes an immutable M4.1 route object and runs a generic
respiratory SEIRS module through Starsim 3.5.2. Seeded infections and optional
generic exogenous imports are distinct from locally acquired infections. Local
events retain the Starsim infector UID and route ID; no visitors, arrivals,
airport/ferry process, observation model, calibration, interventions or API are
implemented in M5.

Milestone 6 keeps M5 latent outputs immutable and applies observation
assumptions in a separate layer. `jos observe run` writes detected/reported
case tables and event metadata without changing the latent hash. `jos ensemble
run --seeds 101,102,103` retains explicit replicate seeds and writes tidy
replicate trajectories with linear lower/median/upper quantiles. Matched-seed
comparisons pair A/B outputs by seed. `jos calibrate synthetic` and
`jos calibrate beta` use Optuna to recover a hidden observation or generic beta
parameter from synthetic truth only, retaining all trials and a held-out
synthetic check; neither is Jersey calibration.

## Quick start

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked
uv run jos demo --seed 123
uv run jos data build
uv run jos population generate --mode ci --seed 123
uv run jos structure generate --mode ci --seed 123
uv run jos network generate --mode ci --seed 123
uv run jos outbreak run --mode ci --seed 123
uv run jos observe run --mode ci --seed 123
uv run jos ensemble run --mode ci --seeds 101,102,103
uv run jos calibrate synthetic --mode ci --seed 123
uv run jos calibrate beta --mode ci --seed 123
uv run jos scenario run --mode ci --seed 123 \
  --scenario-config configs/scenarios/m7_combined.yaml
uv run jos intervention compare --mode ci --seed 123 \
  --scenario-config configs/scenarios/m7_school_closure.yaml
uv run jos intervention ensemble --mode ci --seeds 101,102,103 \
  --scenario-config configs/scenarios/m7_case_isolation.yaml
uv run jos api serve
```

The command prints a machine-readable JSON summary and writes:

```text
outputs/demo_seed_123/summary.json
outputs/demo_seed_123/run_manifest.json
```

The summary is the declared deterministic output. The manifest also records
run metadata such as code state, Python and Starsim versions, lock/config
hashes, seed, runtime and output hashes. Runtime timestamps and measured
duration are intentionally not expected to match between runs.

The data build validates every registered snapshot hash and writes canonical
tables plus `data/processed/quality_report.json` and
`data/processed/quality_report.md`. Warnings in that report are retained source
limitations or published rounding conflicts; they are not silently imputed.

The population command validates the Milestone 1 canonical-table manifest before
generation. Its output directory contains `residents.parquet`,
`households.parquet`, `communal_settings.parquet`, diagnostics and a manifest
with the seed, configuration hash, input hashes, logical content hash, runtime
and memory metadata. Runtime and filesystem artifact hashes may vary; the
logical content hash is the declared same-seed comparison.

The structure command validates the supplied Milestone 2 artifact before
generation. If no artifact is supplied it creates the matching M2 artifact in a
sibling output directory. Its output contains resident structure, schools,
classes, school assignments, workplaces, teams, job assignments, diagnostics,
benchmark metadata and a manifest. The logical structure hash is the declared
same-seed comparison; timestamps, runtime and filesystem artifact hashes remain
volatile.

The network command validates both the M2 and M3 artifact boundaries and writes
selected dynamic snapshots rather than a year's worth of daily edge states.
Network edge weights are relative contact-opportunity weights only; they are not
pathogen-specific transmission probabilities. The network artifact includes
route and staffing diagnostics, cross-route diagnostics, assumptions, selected
snapshots and M2/M3/config/Starsim/source provenance.

The outbreak command builds the matching M2/M3/M4.1 artifacts, runs the generic
respiratory module, and writes versioned M5 output artifacts containing
`daily_epidemic.parquet`, `daily_parish.parquet`, `daily_route.parquet`,
`daily_age.parquet`, `transmission_events.parquet`, parameter metadata,
diagnostics and a manifest. These are latent truth outputs; they are not
detected or reported case counts.

M6 outputs are written under `outputs/observations`, `outputs/ensembles` and
`outputs/calibration` by the corresponding commands. Observation parameters
retain explicit provenance statuses; the demo values are scenario assumptions,
not Jersey surveillance controls. `jos calibrate beta` is a synthetic
train/held-out recovery diagnostic, not Jersey calibration. A constrained host may report
`sequential_fallback` for an ensemble requested with multiple workers when its
OS denies the process-pool semaphore check; this is recorded in diagnostics.
The C3 verification archive is written to external retention rather than
committed generated-output directories; see
[`docs/verification_archive.md`](docs/verification_archive.md).

M7 outputs are written under `outputs/interventions`,
`outputs/intervention_comparisons` and `outputs/ensembles` by the scenario,
comparison and intervention-ensemble commands. All demonstration intervention
values and route multipliers are synthetic assumptions. See
[`docs/interventions.md`](docs/interventions.md) for the runtime contract and
artifact schema.

## Verification

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv lock --check
uv run mypy --ignore-missing-imports \
  src/jersey_outbreak/population_structure_schemas.py \
  src/jersey_outbreak/population_structure_controls.py \
  src/jersey_outbreak/population_structure_artifacts.py \
  src/jersey_outbreak/population_structure_generator.py \
  src/jersey_outbreak/network_schemas.py \
  src/jersey_outbreak/network_generator.py \
  src/jersey_outbreak/network_artifacts.py \
  src/jersey_outbreak/staffing_evidence.py \
  src/jersey_outbreak/staffing_generator.py \
  src/jersey_outbreak/starsim_adapter.py \
  src/jersey_outbreak/outbreak_schemas.py \
  src/jersey_outbreak/respiratory.py \
  src/jersey_outbreak/outbreak_runner.py \
  src/jersey_outbreak/outbreak_artifacts.py \
  src/jersey_outbreak/intervention_schemas.py \
  src/jersey_outbreak/interventions.py \
  src/jersey_outbreak/intervention_artifacts.py \
  src/jersey_outbreak/intervention_analysis.py \
  src/jersey_outbreak/scenario.py \
  src/jersey_outbreak/observation_schemas.py \
  src/jersey_outbreak/observation.py \
  src/jersey_outbreak/observation_artifacts.py \
  src/jersey_outbreak/ensemble_schemas.py \
  src/jersey_outbreak/ensemble.py \
  src/jersey_outbreak/ensemble_artifacts.py \
  src/jersey_outbreak/calibration_schemas.py \
  src/jersey_outbreak/calibration.py \
  src/jersey_outbreak/calibration_artifacts.py \
  src/jersey_outbreak/cli.py
uv run jos demo --seed 123
uv run jos structure generate --mode ci --seed 123
uv run jos network generate --mode ci --seed 123
uv run jos observe run --mode ci --seed 123
uv run jos ensemble run --mode ci --seeds 101,102,103
uv run jos calibrate synthetic --mode ci --seed 123
uv run jos calibrate beta --mode ci --seed 123
```

Run the demo twice with the same seed and compare `summary.json` to verify the
declared deterministic outputs under the pinned Starsim version. For M3, the
declared logical structure hash is stable across independent processes; runtime,
timestamps, memory measurements and filesystem artifact hashes are not.
The verified CI seed-123 logical structure hash is
`18087772e7286f1b88e3e30ca325e53d97d4fcce3582cf2e8f2fe3ac6e198d2a`.

The repository-wide legacy codebase still has pre-existing mypy errors, so CI
currently type-checks the M3, M4/M4.1 and M5 modules explicitly. This is an
engineering cleanup item, not evidence that the milestone contracts are
untyped.

## Scientific scope

JOS follows the scientific rules in [`docs/scientific_scope.md`](docs/scientific_scope.md):
synthetic people only, no fake precision, explicit measured/derived/assumed
labels, separate latent truth from observation, stochastic ensembles for
scenario comparisons, and reproducible manifests for every run.

The architecture boundary is documented in
[`docs/architecture.md`](docs/architecture.md). Later milestones must be
started one at a time and must pass their gates before the next one begins.

## Milestone 8 explicit travel and visitors

M8 adds a typed travel layer without inflating the 104,540 permanent resident
population. Residents retain stable IDs; temporary visitors use a
`visitor-<seed>-<counter>` namespace and preallocated Starsim slots. Episodes
record airport/ferry entry, travel parties, accommodation or host households,
transport, arrival disease state and departure. Inactive slots have no
contacts and are excluded from present-population denominators. Returning
residents retain their identity but leave Jersey routes while away and may
acquire infection through a separate synthetic external-travel pressure.
M8.1 resolves every transmission event through the active `(slot UID, timestep)`
episode interval; M8.2 carries that immutable visitor/trip/party/episode identity
through observation rows, detection delivery and persisted travel artifacts.
A final slot map is never used for historical attribution.
Activation assigns episode age/sex/state/protection and departure resets all
temporary state before reuse.

Generic M5 import attempts and explicit arrivals are separate streams. Use
`mode: generic_import_only`, `explicit_travel` or `both` deliberately; the M8
manifest records the choice. Visitor terminal, accommodation, host-household,
party, bounded transport-unit and community routes are temporary and
route-attributed, while M7
interventions can compose with M8 episodes. Visitor-volume seasonality and
optional travel-contact seasonality are typed, bounded and persisted in
`seasonality_schedule.parquet`; monthly profiles are normalized by modeled
days so annual passenger-movement totals are preserved. Exact executed
temporary edges are persisted in `temporary_edges.parquet` and logically
rehash-verified with the episode, visitor, scenario and latent tables. High-risk strata are targeting metadata only;
M5 has no validated severity pathway.

Arrival-test results are episode-bound. Results available after visitor
departure remain historical and non-actionable, so slot reuse cannot transfer a
positive result or quarantine to the replacement visitor. Combined M7/M8 event
artifacts use typed columns and canonical JSON for heterogeneous transition
state, preserving exact JSON types during logical verification.

```bash
uv run jos travel run --mode ci --seed 123 \
  --travel-config configs/travel/m8_explicit_travel.yaml
uv run jos travel compare --mode ci --seed 123
uv run jos travel ensemble --mode ci --seeds 101,102,103
uv run jos scenario run --mode ci --seed 123 \
  --scenario-config configs/scenarios/m8_combined.yaml
```

M8 outputs describe only the declared synthetic travel scenario. They are not
real visitor prevalence, airport/ferry transmission rates, policy-effectiveness
estimates, tourism forecasts or traveller surveillance. At `stream_scale < 1`,
simulated movements are a computational sample, not source-equivalent unique
tourists, and epidemic results are not automatically inflated to source scale.
Only the annual 2025 air/ferry passenger-movement totals are observed travel
controls; monthly seasonality and all composition/contact/intervention values
are assumptions unless a frozen source explicitly says otherwise.
