# Architecture

## Current verified implementation status

As of 28 August 2026, M0–M7 and corrective closures C1–C5 are PASS. The C3
verification commit is `658364c7f02cf44f9392116e7db44c94bdb3175a`; the C3
implementation commit is `0f6667791e481fd2ed5d389d2ea0cb05b8a0d7e9`, followed
by verification manifest-integrity hardening and documentation-only commits.
M7 adds a prospective intervention layer while keeping the canonical M4
routes and latent M5 outputs immutable. The original M8 implementation failed
independent audit, and the independent M8.1 audit left three blockers. M8.2 is
the minimal final correction for episode-safe observations, departed test
results and combined-event artifact serialization. API and UI remain later
M9 now adds the local API/job boundary described below; M10 UI remains a later
boundary. M8 now passes with explicit non-blocking warnings for source-backed
seasonality, structural transport detail and unbenchmarked literal annual
source-scale disease execution.
Quantitative evidence is maintained in
[`progress.md`](progress.md).

## Milestone 8 travel boundary

M8 is an explicit temporary-person layer above the immutable resident M2/M3/M4
parent. `travel_schemas.py` owns strict episode, stream, seasonality,
intervention and targeting contracts. `travel.py` generates deterministic
airport/ferry episodes, maps temporary visitor identities to bounded
preallocated Starsim slots, activates/deactivates those slots on episode
dates, and constructs sparse temporary routes for terminals,
accommodation/host households, local visitor transit and visitor community
activity. Starsim 3.5.2 population growth is append-only, so M8 does not append
or delete agents during a run. Capacity is derived from peak concurrency plus
declared headroom, not annual passenger volume.

Canonical resident IDs and M4 routes are not rewritten. A route view adds seven
M8 route families and filters resident routes to people present in Jersey when
returning-resident episodes exist. Event attribution maps temporary slot UIDs
through the immutable active episode at the event timestep, never through a
final slot occupant. It retains runtime UID, visitor/trip/party identity and
resident→resident, resident→visitor, visitor→resident and visitor→visitor
directions. The travel lifecycle runs
before disease transmission; post-transmission state snapshots drive the
date-specific present-population outputs.

Generic M5 exposure attempts and explicit visitor arrivals/returning-resident
external acquisition are separate processes. The `both` mode is intentional
and persisted to prevent silent double counting. Arrival testing, quarantine,
traveller protection and travel-acquisition reduction are prospective controls.
Each scheduled arrival-test result is bound to the immutable actor, runtime UID,
trip/episode and administration/result timesteps. A visitor result available
after departure is historical and non-actionable; it cannot follow the slot to
its next occupant. Returning-resident results retain the permanent resident
contract.
M7 consumes the presence-valid route view rather than rebuilding canonical M4,
so route intervention refreshes cannot reintroduce absent residents. Its
vaccination modifier composes multiplicatively with traveller protection, and
community interventions declare whether temporary visitor routes are in scope.
Temporary slots remain ignored by resident-only target selectors. Visitor intensity and optional
travel-route transmission seasonality are separate typed profiles, and the
actual daily schedule is persisted. High-risk categories are targeting and
stratification tags, not medical diagnoses or severity probabilities.

M8 artifacts use schema version 2.0 and include exact sparse executed temporary
edges plus travel/epidemic Parquet tables, complete configurations, parent
references, file hashes, scenario/run/episode/network/seasonality hashes and
performance diagnostics. Observation and detection tables retain immutable
event-time visitor/trip/party/episode identity. Combined M7/M8 intervention
state is stored in explicit typed columns with canonical JSON state values,
then reconstructed before logical hashing. Verification recomputes logical
identities from contents, so replacing a table and updating only its raw
checksum still fails. Comparisons
retain matched seed and parent information while documenting coupling decay.
The M8 CLI stops at travel runs, comparisons and small ensembles. M9 wraps
those verified paths without changing their scientific artifacts.

The full corrected stack produces 104,540 agents, 522,388 structural edges,
856,050 baseline edges and 1,906,144 selected snapshot edges. A full Starsim
3.5.2 network-only execution succeeds. C4 verifies runtime-causal observation
delivery, independent observation streams, metric-aware ensemble grids,
truthful fallback worker reporting and a zero-community-contact boundary. The
synthetic train/held-out beta recovery and hash-checked external archive
contracts remain intact.

## Milestone 9 local API and persistent jobs

M9 is an application layer above the verified scientific runners:

```text
loopback HTTP /api/v1
          |
          v
typed request validation -> SQLite FIFO registry
                                |
                                v
                  isolated worker subprocess
                                |
                                v
                 one execution adapter -> M5/M6/M7/M8
                                |
                                v
       content-verified artifacts + M9.2 provenance-bound finalizer
```

`api.py` contains the compact FastAPI contract and no scientific calls.
`job_registry.py` owns SQLite schema version 2, WAL mode, canonical submission
identity, immutable submitted engine anchors, atomic write-once worker-observed
anchors, append-only application events and legal state transitions. Schema v1
rows migrate without fabricated anchors: existing values and terminal states
are preserved, while the new fields remain null.
`job_manager.py` claims queued rows atomically in FIFO order and launches only
the fixed `jersey_outbreak.job_worker` entrypoint with `sys.executable`.
Workers run in dedicated process groups on POSIX so cancellation can terminate
only that job and its children. The default API concurrency is one, while the
existing ensemble worker bound remains authoritative inside an ensemble job.

`execution_adapter.py` is the only application-to-engine translation point.
It builds the existing M2/M3/M4 parent, calls the existing M5–M8 orchestration,
writes existing scientific artifacts, and emits only persisted artifact
locators. `scientific_verification.py` uses a fixed allow-listed dispatch and
shared writer/verifier scientific hash functions. `job_finalizer.py` is the
only path to `SUCCEEDED`; both live workers and restart reconciliation use it,
and its registry publication is one transaction. It treats submitted and
worker-observed SQLite identities as authority and candidate, scientific
artifact, and result-manifest identities as evidence that must match. Neither
candidate nor finalizer may replace the anchors. Dataset endpoints resolve
only catalogue- and manifest-listed Parquet files under a job directory and
use Arrow projection/filter pushdown with bounded response materialization.
The API never exposes arbitrary paths, SQL, Python, shell commands or a new
scientific taxonomy. Full endpoint and restart/cancellation semantics are
documented in [`api.md`](api.md).

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
`src/jersey_outbreak/starsim_adapter.py`, the M5
`src/jersey_outbreak/respiratory.py` disease boundary and the M7
`src/jersey_outbreak/interventions.py` runtime are the application modules
allowed to import Starsim. They own the exact 3.5.2 API calls used by the
spike, route adapter, generic disease and intervention lifecycle; the run
layer converts Starsim result arrays into plain Python values. The rest of the
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

M6/C4 keeps the immutable M5 result boundary while sampling observation
schedules during the Starsim run:

```text
infection recorded during M5 + observation config
                    |
                    v
       stable event-specific schedule sampler
                    |
                    +--> detection-time priority queue
                    |        |
                    |        +--> delivery after disease transmission
                    |        +--> read-only future-consumer hook
                    |
                    v
       offline detected/report-date tables
                    |
                    +--> explicit-seed replicate trajectories
                    |        |
                    |        +--> linear quantile summaries
                    |        +--> matched-seed A/B differences
                    |
       +--> synthetic-only Optuna recovery artifact
```

C4 integrates the observation scheduler without adding disease biology or
interventions. Observation events retain separate infection, generic
symptom-onset, detection and report dates. The daily lifecycle is disease-state
progression, network refresh, existing intervention step, disease transmission
and imports, detection delivery, then the intervention consumer. The M7
consumer can first change contact or intervention state for the next timestep;
it cannot retroactively affect completed transmission. The observation horizon
includes the full latent horizon and a documented maximum-delay tail.
Observation RNG is keyed by latent replicate seed, observation seed,
configuration ID and stable event identity. Offline artifacts use the same
sampler as the online queue.

Ensemble summaries are complete over the declared date grid using an explicit
metric registry. Missing incidence is a structural zero, cumulative values
carry forward, and state/prevalence cells beyond actual evolution are marked
outside the metric horizon and excluded from quantiles. Failed replicates remain
non-contributors rather than zeroes. Process-pool worker counts distinguish
requested, planned and actual execution and are bounded by a configurable
memory estimate, physical-memory safety fraction and CPU count. Beta recovery is a
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

### Milestone 7 intervention boundary

M7 adds `intervention_schemas.py`, `interventions.py`,
`intervention_analysis.py`, `intervention_artifacts.py` and `scenario.py`.
`InterventionManager` is the single Starsim intervention module. It refreshes
state after the M4 network refresh and before M5 transmission, applies a
product of active route multipliers to prospective route views, and records
state/events/effective-route diagnostics. Detection notifications arrive from
the C4 scheduler after same-day transmission, so case isolation and household
quarantine begin no earlier than the next timestep.

The manager reads M2/M3 metadata for age, parish, school, job, workplace,
household and care-setting targeting. It never mutates the generated M4 route
snapshots. Care roster edges are retained with beta zero when a care
protection multiplier suppresses them. Vaccination is represented by
prospective susceptibility/infectiousness modifiers in the generic M5 disease
module; severity and mortality pathways remain outside M5. Intervention
artifacts carry parent logical hashes, config/provenance hashes, seed and
matched-seed coupling diagnostics. The supported M7 CLI and demo YAMLs are
documented in [`interventions.md`](interventions.md).

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
- **Interventions:** M7 scenarios and experiments carry typed targets,
lifecycle controls, route composition, parameter provenance, sensitivity IDs
and parent hashes; no travel/visitor controls are included.

C5 tightens that boundary. `duration_days` is a count of inclusive dated output
points, so every layer uses `start + duration_days - 1` as the final date. The
manager performs a route-level materiality check before edge work: an unchanged
route retains the exact network-refresh arrays, while a touched route is rebuilt
from the immutable snapshot using modifiers sorted by intervention ID/version.
This preserves float precision and hazard evidence for empty and neutral
manager-attached runs.

Scenario/run identity contains the canonical full `OutbreakRunConfig`, M2, M3
and M4 hashes, disease/observation configs, interventions, sensitivity IDs,
seed/date horizon and Starsim/JOS versions. A separate latent-outcome hash
covers only the five material M5 output datasets. The M7 artifact-bundle hash
adds intervention state, events and route effects. M7 artifacts directly embed
a hash-verified M5 bundle; they cannot verify as complete after any latent table
or its manifest is removed or changed.

WFH workplace targeting resolves selected jobs and shared workplaces; commute
suppression is deliberately primary-job-only because M4 commute edges cannot
identify a secondary job. Vaccination acceptance is stable by seed, campaign
and agent; capacity affects administration timing, not willingness. Exogenous
import controls represent exposure attempts followed by susceptibility-modified
acquisition. Care targets use an explicit two-class allow-list for nursing and
non-nursing care homes. Route-global community controls expose route/settings
state rather than claiming an island-wide person-level active count.
- **Results:** M6/M7 summaries and ensembles carry their configuration,
  sources, parameters, code state and explicit seed list; matched comparisons
  preserve seed pairing and separate health outcomes from intervention burden.

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
