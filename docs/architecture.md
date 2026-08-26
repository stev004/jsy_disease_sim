# Architecture

## Milestone 0–2 boundary

The repository intentionally keeps the verified simulation spike isolated from
the aggregate evidence and synthetic-population paths:

```text
strict config/provenance models
          |
          v
      demo runner -----> run manifest + JSON summary
          |
          v
  Starsim compatibility boundary
          |
          v
official ss.Sim + ss.SIR + ss.RandomNet
```

Milestone 1 adds a separate aggregate evidence path:

```text
immutable raw snapshots + source registry
              |
              v
 source-specific CSV/PDF extraction
              |
              v
 canonical aggregate tables with row provenance
              |
              v
 validation/reconciliation + deterministic quality report
```

Milestone 2 adds a bounded synthetic-population path that consumes only the
validated aggregate controls:

```text
canonical aggregate tables + source/table hashes
                  |
                  v
        strict population configuration
                  |
                  v
      seeded parish/age/sex allocation
          /                    \\
         v                      v
 private household generator   communal-setting generator
         |                      |
         +----------+-----------+
                    v
     invariant validation + diagnostics
                    |
                    v
       Parquet artifacts + manifest
```

`src/jersey_outbreak/starsim_compat.py` is the only application module allowed
to import Starsim. It owns the exact 3.5.2 API calls used by the spike and
converts Starsim result arrays into plain Python values. The rest of the
application does not depend on Starsim's internal object graph.

`src/jersey_outbreak/data_pipeline.py` is deliberately independent of Starsim.
It validates local snapshot hashes before parsing, keeps observed and derived
rows distinct, and records manual extraction locators and evidence source IDs.
It stops at aggregate controls. `population_controls.py` is the explicit
boundary from those controls into Milestone 2 generation; it fails closed when
the canonical table manifest or quality report is invalid.

`population_generator.py` owns only synthetic residents, private households and
communal settings. It does not create contacts, schools, workplaces, commutes,
mobility, disease state or interventions. `population_artifacts.py` writes
Parquet plus diagnostics and a manifest; logical content is hashed separately
from volatile runtime metadata.

## Stable boundaries for later milestones

- **Contracts:** versioned Pydantic v2 models describe inputs, provenance and
  run metadata. Unknown fields fail validation.
- **Data:** raw snapshots and canonical aggregate tables remain independent of
  simulation runtime state; each row retains source hash, reference period,
  locator and transformation metadata.
- **Population:** synthetic residents and settings remain disease-agnostic.
  Milestone 2 implements only the bounded resident, household and communal-
  setting layer; contact structures are deferred.
- **Simulation adapter:** the only deep Starsim integration point.
- **Disease:** future disease modules own natural history and transmission
  parameters; they do not create Jersey households or geography.
- **Observation:** future observed-case generation remains separate from latent
  infections.
- **Results:** future summaries and ensembles carry their configuration,
  sources, parameters, code state and seeds.

Milestone 0 does not create placeholder packages for those future boundaries.
They are contracts in the documentation only until a milestone requires them.

## Reproducibility

The demo's deterministic declaration covers the JSON summary's fixed
configuration, time series and final counts for a seed under Starsim 3.5.2.
The manifest records volatile execution metadata separately: creation time,
runtime, dirty-worktree state and artifact hashes. A future milestone may add
more declared outputs, but it must state which outputs are expected to be
stable and test them explicitly.
