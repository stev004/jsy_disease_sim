# Jersey Outbreak Simulator

Jersey Outbreak Simulator (JOS) is a local-first research prototype for
exploring infectious-disease transmission through a wholly synthetic Jersey
population. It is designed to keep population structure, contact mechanisms,
disease biology, interventions, observations and provenance separate.

## Current status

V1.0 (tag `jos-v1.0.0`) and V1.1 (tag `jos-v1.1.0`, scientific-hardening
release, 2026-09-01) are released and frozen. The V1.2 cycle is open; `main`
additionally carries the V1.2 carry-ins, frozen Jersey COVID-era source
snapshots, and the 2026-09-02/04 audit-driven optimization cycles (R6/R7/R8:
~10x faster runs with byte-identical scientific outputs — see
[`docs/performance-history.md`](docs/performance-history.md)). The living
backlog is [`docs/roadmap.md`](docs/roadmap.md); the current-state authority
is [`.claude/FRONTIER.md`](.claude/FRONTIER.md); agents start at `CLAUDE.md`.

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
