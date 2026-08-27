# Architecture

## Current verified implementation status

As of 27 August 2026, M0–M6 and corrective closures C1–C3 are PASS. The
current tip is `658364c7f02cf44f9392116e7db44c94bdb3175a`; the C3 implementation
commit is `0f6667791e481fd2ed5d389d2ea0cb05b8a0d7e9`, followed by verification
manifest-integrity hardening. M7 is CLOSED and no C4 or intervention work has
started. Quantitative evidence is maintained in
[`progress.md`](progress.md).

The full corrected stack produces 104,540 agents, 522,388 structural edges,
856,050 baseline edges and 1,906,144 selected snapshot edges. A full Starsim
3.5.2 network-only execution succeeds. C3 additionally verifies causal
observation timing, independent observation streams, complete ensemble grids,
memory-bounded worker selection, synthetic train/held-out beta recovery and a
hash-checked external verification archive.

## Milestone 0–4 boundaries

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

`src/jersey_outbreak/starsim_compat.py`,
`src/jersey_outbreak/starsim_adapter.py` and the M5
`src/jersey_outbreak/respiratory.py` disease boundary are the only application
modules allowed to import Starsim. They own the exact 3.5.2 API calls used by
the spike, route adapter and generic disease, and the run layer converts
Starsim result arrays into plain Python values. The rest of the application
does not depend on Starsim's internal object graph.

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

## Milestone 3 daytime-structure boundary

Milestone 3 consumes one validated, immutable Milestone 2 artifact and the
registered Milestone 1 aggregate controls:

```text
M2 residents + canonical school/employment/workplace/commute controls
                              |
                              v
              seeded structure generator
                 /       |        \
                v        v         v
       schools/classes  jobs    workplaces/teams
                              |
                              v
              work parishes + commute metadata
                              |
                              v
                diagnostics + provenance manifest
```

`population_structure_*` owns synthetic membership and daytime structure only.
It preserves the M2 resident IDs, validates school age compatibility, links
jobs to synthetic workplaces and teams, records bounded secondary jobs and
checks car/WFH schedule consistency. The published 66/13/21 workplace
destination split is applied at aggregate control level; it is not an
institutional or address-level observation. No Starsim network, contact edge,
disease state, intervention or visitor model is created here. M4 owns those
simulation-facing layers.

The M3 artifact contains separate Parquet tables for resident structure,
schools, classes, school assignments, workplaces, workplace teams and job
assignments. Its manifest records the M2 artifact ID and hashes, all canonical
input hashes, configuration and logical-content hashes, diagnostics status,
runtime metadata and dirty-worktree state. Logical content is hashed from
stable identifier order, independently of Parquet metadata and volatile run
measurements.

## Milestone 4 route boundary

Milestone 4 consumes validated M2/M3 artifacts and builds route tables without
importing Starsim into population or structure generation:

```text
M2 residents/households/settings + M3 memberships/jobs
                              |
                              v
                  plain JOS route generator
       fixed edges + memberships + deterministic daily snapshots
                              |
                              v
                     route diagnostics
                              |
                              v
              Starsim 3.5.2 adapter boundary
              ss.Network / ss.DynamicNetwork
```

The separable route IDs are `household`, `school_class`,
`school_cross_class`, `workplace_team`, `workplace_transient`,
`care_resident`, `care_staff`, `shared_vehicle`, `bus`, `community_indoor`
and `community_outdoor`. Household, class core, team core and care resident
edges preserve repeated membership. Cross-class, broader workplace, transport
and community edges are bounded deterministic samples, with daily or periodic
refreshes declared in each route specification.

M4.1 adds a separate staffing-evidence and allocation layer before route
construction. Frozen Government of Jersey education FOI snapshots provide
observed CYPES FTE controls; the allocator converts those controls into
synthetic staff endpoints and assigns them to existing synthetic schools and
classes. The Care Commission accommodation standard provides regulatory
minimums for supported nursing and non-nursing care homes; a configurable
structural shift-coverage multiplier derives a minimal unique synthetic roster.
Both overlays select existing employed adult M2/M3 agents, preserve their
household/community and M3 job identity, and do not mutate M3 job accounting or
claim an observed individual roster. Other communal categories are not silently
treated as care homes.

For ordinary workplace routes, an institutional staff member's M3 primary job
is reinterpreted as the synthetic school/care institutional role. An explicitly
represented M3 secondary job remains eligible for ordinary workplace contacts.
This prevents a full unrelated primary workplace environment from being added
on top of the school/care role while preserving legitimate multi-job structure.

The school class route contains repeated pupil-pupil, pupil-staff and bounded
staff-staff contacts for assigned classes; the school cross-class route includes
lower-frequency school/year contacts for staff assigned to the relevant school.
The independent care-staff route creates bounded resident-cohort to assigned
staff contacts while `care_resident` remains resident-only. Staffing
assignments, statuses, source hashes and diagnostics are persisted separately
from the route edge table.

The adapter maps sorted synthetic `agent_id` values to Starsim's zero-based
UIDs, passes the canonical undirected pair as `p1`/`p2`, and passes JOS's
relative contact-opportunity weight through Starsim's required `beta` edge
field. That field is explicitly not a disease-specific transmission parameter.
Calendar-aware routes use the supported `DynamicNetwork.step()` lifecycle to
replace the current daily snapshot; fixed always-active routes use a static
Starsim network with a no-op step hook. No custom disease or transmission
engine is present in M4.

### Milestone 5 disease boundary

M5 consumes the M4.1 `GeneratedNetworks` object without modifying its route
tables. `starsim_adapter.py` converts the existing 11 route families into
Starsim networks and initializes the generic `RespiratorySEIRS` infection. The
disease subclass uses Starsim's edge-level `compute_transmission()` and
`Network.net_beta()` machinery; JOS adds only deterministic generic import
selection, SEIRS state progression and order-invariant event attribution. For a
target with successful candidates on multiple routes, infection occurrence is
the unchanged union of Starsim edge successes and attribution selects a route
with probability proportional to its successful edge hazard, using a stable
target/timestep draw independent of route insertion order. The run layer maps stable Starsim UIDs back
to synthetic JOS agent IDs and writes daily latent-truth summaries by epidemic
state, parish, age band and route.

M5 parameter metadata is stored separately from runtime controls. Demonstration
values are `scenario_assumption`; unsupported symptom, severity, death and
seasonality families are recorded as deferred rather than assigned fake
observed values. The run manifest references the M2, M3 and M4.1 logical hashes,
the parameter hash, Starsim version, seed, outputs, attribution totals and
network immutability check. Interventions, visitors, API and UI remain
later-milestone concerns.

### Milestone 6 observation and ensemble boundary

M6 adds a pure post-processing boundary over the immutable M5 result:

```text
immutable M5 latent run + observation config
                    |
                    v
       detected/report-date observation tables
                    |
                    +--> explicit-seed replicate trajectories
                    |        |
                    |        +--> linear quantile summaries
                    |        +--> matched-seed A/B differences
                    |
       +--> synthetic-only Optuna recovery artifact
```

C3 closes the remaining observation and verification contracts without adding
disease biology or interventions. Observation events retain separate infection,
generic symptom-onset, detection and report dates, and a causal detection-event
interface is exposed without mutating M5 state. The observation horizon includes
the full latent horizon and a documented maximum-delay tail. Observation RNG is
keyed by latent replicate seed, observation seed, configuration ID and stable
event identity, so matched seeds are reported as matched starts rather than
unqualified common random numbers.

Ensemble summaries are complete over the declared date grid; missing values in a
successful replicate are explicit zeroes and failed replicates remain failed
records. Process-pool worker counts are bounded by a configurable memory
estimate, physical-memory safety fraction and CPU count. Beta recovery is a
synthetic train/held-out profile over generic M5 beta values, with explicit
ascertainment and route-weight sensitivity checks. It is not Jersey surveillance
calibration and does not identify beta separately from contact intensity.

`verification_archive.py` writes an immutable, hash-checked index tying C3
results to the Git commit, parent M2/M3/M4 logical hashes, source manifests,
commands, benchmarks and externally retained output summaries. A stale parent
artifact cannot be presented as a current verification archive without failing
the parent-hash check.

`observation.py` never writes back to M5 events or network state. Observation
parameters carry their own statuses and source references; the included demo
values are scenario assumptions. `ensemble.py` reruns the existing M4.1/M5
stack for an explicit unique seed list, preserves failed replicates as failed,
and summarizes successful results only. `compare_ensembles()` pairs seed
identities before calculating differences. The recovery harness uses a hidden
synthetic reporting delay or generic beta and a fresh synthetic held-out seed;
it is not a Jersey-data calibration or a model-validation claim. Ensemble,
observation and calibration tables have immutable content-addressed directories
and manifests.

## Stable boundaries for later milestones

- **Contracts:** versioned Pydantic v2 models describe inputs, provenance and
  run metadata. Unknown fields fail validation.
- **Data:** raw snapshots and canonical aggregate tables remain independent of
  simulation runtime state; each row retains source hash, reference period,
  locator and transformation metadata.
- **Population:** synthetic residents and settings remain disease-agnostic.
  Milestone 2 implements the bounded resident, household and communal-setting
  layer. Milestone 3 adds synthetic school and daytime-structure metadata;
  Milestone 4 adds route structure without disease biology.
- **Simulation adapter:** `starsim_adapter.py` is the deep Starsim integration
  point; all M4 route generation and diagnostics remain plain Python.
- **Disease:** future disease modules own natural history and transmission
  parameters; they do not create Jersey households or geography.
- **Observation:** M6 observed-case generation remains separate from latent
  infections and writes its own configuration, event table and manifest.
- **Results:** M6 summaries and ensembles carry their configuration, sources,
  parameters, code state and explicit seed list; matched comparisons preserve
  seed pairing.

Milestone 0 does not create placeholder packages for those future boundaries.
They are contracts in the documentation only until a milestone requires them.

## Reproducibility

The demo's deterministic declaration covers the JSON summary's fixed
configuration, time series and final counts for a seed under Starsim 3.5.2.
The M2, M3 and M4 manifests make the same distinction for their logical
population, structure and route content hashes. Each manifest records volatile
execution metadata separately: creation time, runtime, dirty-worktree state and
artifact hashes. M4 also stores per-route hashes and selected daily snapshots,
so fixed membership and refreshed route states can be compared independently.
The current M3 CI run with seed 123 reproduced the same logical structure hash
across independent processes, and M4 tests reproduce the same route hash while
showing a changed seed changes sampled community edges. A future milestone may
add more declared outputs, but it must state which outputs are expected to be
stable and test them explicitly.
