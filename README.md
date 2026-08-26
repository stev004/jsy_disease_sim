# Jersey Outbreak Simulator

Jersey Outbreak Simulator (JOS) is a local-first research prototype for
exploring infectious-disease transmission through a wholly synthetic Jersey
population. It is designed to keep population structure, contact mechanisms,
disease biology, interventions, observations and provenance separate.

## Current status

This repository contains **Milestones 0–2**: repository contracts, a verified
Starsim compatibility/reproducibility spike, a source-registered aggregate
evidence layer, and a disease-agnostic synthetic Jersey population generator.
The Starsim demo is an official SIR example using Starsim's built-in
`RandomNet`; it is not a Jersey outbreak reconstruction or a validated
forecast. The Milestone 2 population is synthetic and control-driven; it is
not a sample of named people or real addresses.

Milestone 1 includes immutable official source snapshots, explicitly labelled
manual PDF transcriptions, canonical aggregate CSVs and deterministic data
quality reports. It does not include synthetic residents, household synthesis,
individual schools/workplaces/commutes, custom routes, a respiratory disease
module, observation, calibration, API or UI.

Milestone 2 adds CI (3,000), scaled (15,000) and full (104,540) population
generation modes. It produces versioned Parquet residents, private households
and communal-setting artifacts, plus JSON/Markdown diagnostics and a
reproducibility manifest. It intentionally does not add schools, workplaces,
commutes, mobility, disease transmission, visitors, API or UI functionality.

## Quick start

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked
uv run jos demo --seed 123
uv run jos data build
uv run jos population generate --mode ci --seed 123
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

## Verification

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run jos demo --seed 123
```

Run the demo twice with the same seed and compare `summary.json` to verify the
declared deterministic outputs under the pinned Starsim version.

## Scientific scope

JOS follows the scientific rules in [`docs/scientific_scope.md`](docs/scientific_scope.md):
synthetic people only, no fake precision, explicit measured/derived/assumed
labels, separate latent truth from observation, stochastic ensembles for
scenario comparisons, and reproducible manifests for every run.

The architecture boundary is documented in
[`docs/architecture.md`](docs/architecture.md). Later milestones must be
started one at a time and must pass their gates before the next one begins.
