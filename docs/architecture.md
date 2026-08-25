# Architecture

## Milestone 0 boundary

The repository intentionally contains only the contracts and a small verified
simulation spike:

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

`src/jersey_outbreak/starsim_compat.py` is the only application module allowed
to import Starsim. It owns the exact 3.5.2 API calls used by the spike and
converts Starsim result arrays into plain Python values. The rest of the
application does not depend on Starsim's internal object graph.

## Stable boundaries for later milestones

- **Contracts:** versioned Pydantic v2 models describe inputs, provenance and
  run metadata. Unknown fields fail validation.
- **Data:** future raw snapshots and canonical aggregate tables remain
  independent of simulation runtime state.
- **Population:** future synthetic residents and settings remain
  disease-agnostic.
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
