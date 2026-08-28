# Milestone 7: intervention framework and experiments

Milestone 7 adds a single composable, typed intervention runtime on top of the
M4.1 route layer and M5 generic respiratory disease. It is an experiment
framework over the synthetic population; it is not a policy recommendation,
forecast, Jersey surveillance calibration, or named-person model.

## Contract and lifecycle

`InterventionConfig` describes one versioned intervention with an ID, type,
enabled flag, activation/release rules, dates or detection delay, target
population, route multipliers, adherence, provenance metadata, assumptions and
an independent content hash. `ScenarioConfig` is a canonically sorted, ID-unique set of
these configs plus seed, parent identifiers, sensitivity IDs and a run hash.
Unknown fields and unknown M4 route IDs fail validation.

The manager is one Starsim intervention module. Each daily timestep follows:

```text
disease state progression
        -> M4 route refresh
        -> M7 intervention state and effective-route phase
        -> transmission and exogenous imports
        -> C4 detection delivery
        -> next-timestep intervention effect
```

A detection delivered on timestep `t` queues case isolation or household
quarantine for `t + 1` plus its declared start delay. It cannot alter
transmission already completed on `t`. Overlapping isolation/quarantine uses
the maximum active-until time, and release is explicitly logged.

The canonical M4 route object is never modified. For each date, the manager
first determines whether any active config can materially touch a route.
Untouched routes reuse the exact canonical representation, without a copy,
float cast or array replacement. Touched routes multiply effects in canonical
`(intervention_id, version)` order with `math.prod`, clip the product to
`[0, 1]`, and replace only the prospective Starsim route view. Care roster edges remain represented with zero
effective beta when protected so setting/staff topology is not silently lost.

## Supported intervention families

- `case_isolation`: detected target agent, with configurable delay, duration,
  adherence and route-specific effects.
- `household_quarantine`: detected agent's private household, with communal
  residents explicitly skipped and logged.
- `school_closure`: whole or targeted school effects for class and cross-class
  routes, including staff memberships already present in M4.1.
- `workplace_reduction`: workplace and commute multipliers plus deterministic
  WFH fractions or exact weekday schedules. Institutional staff are excluded
  from ordinary workplace targeting unless explicitly enabled. Workplace
  edges are selected by job/workplace. Because M4 commute edges have no
  secondary-job attribution, commute suppression uses the primary job only.
- `community_reduction`: separate indoor and outdoor multipliers.
- `care_home_protection`: nursing/non-nursing/both setting targeting, resident
  and staff care-route effects, and separate external resident/staff effects.
  Eligible classes are exactly `Care home (with nursing)` and `Care home
  (without nursing)`; all other communal types are excluded.
- `vaccination`: deterministic rollout, target/eligibility, stable one-draw
  campaign/person acceptance, delay,
  susceptibility and infectiousness efficacy, and optional waning.
- `masking` and `gathering_reduction`: experimental generic route-multiplier
  families deferred from the core PASS claim. Ventilation is not implemented.

There are no travel, airport, ferry, arrival or visitor controls in M7; those
remain an M8 boundary. Every random choice is keyed by the declared run seed,
intervention ID, stable agent/setting identity and relevant date or schedule
key. Matching a seed therefore gives matching starts and deterministic
intervention draws, while epidemic paths can still diverge after treatment.

## Outputs and experiments

`jos scenario run` and its `jos intervention run` alias write a versioned,
content-addressed directory containing:

- `daily_intervention_state.parquet` — family-specific agents, households,
  settings/routes, care residents/staff, WFH transitions, vaccine doses,
  effective protection and waning;
- `intervention_events.parquet` — detection references, state transitions,
  release reasons, configuration hashes and provenance hashes;
- `route_effects.parquet` — base/effective edge counts and composed
  multiplier diagnostics by route and date;
- `scenario_config.json`, `diagnostics.json` and `manifest.json` — the full
  scenario, parent M2/M3/M4/M5/C4 hashes, dependency versions, sensitivity IDs,
  seed, dirty-worktree flag and output hashes.
- `latent_outputs/jos-outbreak-m5-*/` — directly included daily epidemic,
  route, age and parish tables plus transmission events and a verified M5
  manifest. Missing or changed latent content makes verification fail.

`duration_days` is the number of inclusive dated output points, with
`simulation_end = start_date + duration_days - 1`. Generic imports are exposure
attempts: attempted people are selected before vaccine susceptibility controls
successful acquisition, and blocked attempts are not back-filled.
Pre-C5 M5/M7 artifacts used an inclusive Starsim stop with `start +
duration_days`, producing one extra point; those artifacts retain their
historical meaning and must be regenerated under manifest schema 2.0 rather
than mixed with C5 results.

The stable latent-outcome hash covers exactly the canonical rows in
`daily_epidemic`, `daily_route`, `daily_age`, `daily_parish` and
`transmission_events`; it excludes file paths, timestamps and Parquet metadata.
The latent logical hash additionally binds the full run/disease config and M4
parent. Scenario identity separately binds the complete `OutbreakRunConfig`,
M2/M3/M4, disease and observation configs, intervention/sensitivity config,
seed/dates and Starsim/JOS versions. The artifact-bundle hash also binds M7
state, events and route-effect outputs.

`jos intervention compare` runs a matched-seed baseline and scenario and
writes `scenario_comparison.parquet`, `paired_seed_comparison.parquet` and a
route-shift table. Health outcomes are reported as absolute cumulative cases,
peak prevalence and timing; intervention burdens are reported separately as
agent-days, household-days/settings-days and vaccine doses. Route shares are
always accompanied by absolute counts because a higher share can coexist with
fewer infections.

`jos intervention ensemble` uses the existing bounded M6 process/worker
planner and explicit replicate seeds. Intervention state metrics are registered
as state metrics: they contribute only over the actual simulated horizon;
failed replicates remain failed/non-contributing. Sensitivity runs should use
small, named `sensitivity_config_ids` over the documented dimensions: timing,
duration, adherence, coverage, rollout, protection delay, susceptibility
efficacy, infectiousness efficacy, waning, target population and route/contact
multiplier. Each variant must retain its own config and run hash.

Example commands:

```bash
uv run jos scenario run --mode ci --seed 123 \
  --scenario-config configs/scenarios/m7_combined.yaml
uv run jos intervention compare --mode ci --seed 123 \
  --scenario-config configs/scenarios/m7_school_closure.yaml
uv run jos intervention ensemble --mode ci --seeds 101,102,103 \
  --scenario-config configs/scenarios/m7_case_isolation.yaml
```

The YAML files under `configs/scenarios/` are deliberately synthetic demo
assumptions. They should be used to test composition, lifecycle, hashes and
artifact wiring—not interpreted as calibrated Jersey intervention effects.
