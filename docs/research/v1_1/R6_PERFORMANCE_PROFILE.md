# R6 — V1.1 performance profile

**Status:** profiling and static analysis complete; no optimisation is approved or implemented by this report.

## Executive finding

The frozen V1 full-scale pilot spent 9,260.278 seconds in the combined M5/M6/M7 disease, observation, and baseline-scenario run: 51.446 seconds per dated output point across 180 points. A seven-day full-population `cProfile` run identifies two different costs that must not be conflated:

1. a very large fixed-cost Starsim/Sciris recursive initialisation traversal; and
2. a simulated-day loop dominated by regeneration and replacement of dynamic route edges, followed by exact order-invariant infection attribution.

In the profile, `Sim.init()` accumulated 213.682 seconds and `Sim.run()` accumulated 69.470 seconds. Within `Sim.run()`, dynamic edge replacement accumulated 45.829 seconds (65.97% of `Sim.run()`), while the respiratory step accumulated 24.020 seconds (34.58%). The two cumulative figures overlap only at their parent `Sim.run()` boundary and account for almost all of it. Within the respiratory step, `_order_invariant_infect()` accumulated 23.976 seconds and used 23.056 seconds of self time.

These are profiler measurements, not production wall-time estimates. The run generated 954,243,918 instrumented calls; `cProfile` disproportionately penalises Python/Sciris recursive traversal and tight Python loops. It is therefore unsafe to extrapolate its 284.170 seconds to the pilot's 51.446 seconds/day, to infer a 180-day runtime, or to claim a numerical optimisation speed-up. The exact production split of the pilot's approximately 51 seconds/day remains unmeasured. This report ranks where to benchmark next.

The leading long-horizon opportunity is exact-semantics optimisation of dynamic route generation and edge materialisation. The leading fixed-cost opportunity is preventing Starsim initialisation from recursively traversing large plain-data graphs that do not require distribution or rate linking. Exact attribution is the next substantial loop opportunity, but has the highest scientific and reproducibility risk.

No candidate should be merged merely because it ranks highly here. It must first show an unprofiled before/after improvement, memory measurements, and exact fixed-seed scientific equivalence under the gates in this report.

## Scope and protected contracts

### Goal

Locate plausible causes of the frozen full-scale pilot runtime, rank semantics-preserving optimisation candidates, and define evidence sufficient to accept or reject each candidate.

### Non-goals

- No implementation, configuration, test, schema, or existing-document change.
- No change to model behaviour, scientific assumptions, timestep ordering, stochastic keys, or result identity.
- No claim that the seven-day profile reproduces or partitions the 180-day pilot wall time.
- No new 180-day run.
- No claim that M4 construction, Arrow/Parquet artifact creation, artifact verification, or peak memory was profiled.

The frozen V1 commit and tag remain immutable. All verified scientific and execution contracts described by `docs/architecture.md`, `docs/progress.md`, `docs/scientific_scope.md`, and the audit, technical report, and roadmap on `docs/jos-v1-scientific-review` are protected. In particular, an optimisation must preserve:

- exact population, network, route-calendar, persistence, edge-weight, and edge-order semantics;
- daily lifecycle ordering and the fixed daily timestep;
- Starsim transmission occurrence as the union of successful directed-edge transmissions;
- stable, order-invariant, hazard-weighted route attribution and all retained candidate evidence;
- keyed random-stream identities and cross-process reproducibility;
- online/offline observation equivalence, delivery order, and provenance;
- intervention conflict, trigger, route-effect, and neutral-manager behaviour;
- M4 immutability and the separation between base networks and runtime views;
- scientific artifact schemas, canonical logical hashes, latent/bundle hashes, and parent identities.

The outputs remain synthetic engineering assumptions, not estimates of Jersey epidemiology.

## Evidence reviewed

This report uses:

- the complete V1.1 programme brief;
- the scientific audit, technical report, and roadmap read from `docs/jos-v1-scientific-review` with read-only `git show`;
- `docs/architecture.md`, `docs/progress.md`, and `docs/scientific_scope.md` at commit `9e9ce3abc4201cd8303c723015462d21ca237800`;
- the performance-sensitive outbreak runner, Starsim adapter, respiratory disease, dynamic-network builders, intervention manager, observation scheduler, scientific hashing, artifact writers, and verifier at that commit;
- the frozen full-scale pilot report and machine-readable metrics under `/Users/stevenmatson/Documents/JOS_v1_full_scale_evidence/run-20260830T180202Z`;
- `/private/tmp/jsy_v11_r6_7day.prof`, inspected with Python `pstats` by cumulative time, self time, call count, callers, and callees.

## Exact seven-day profile setup

| Item | Value |
|---|---|
| Repository root / working directory | `/private/tmp/jsy_v11_performance` |
| Commit | `9e9ce3abc4201cd8303c723015462d21ca237800` |
| Python | frozen repository `.venv`, Python 3.12.13 |
| Import path | `PYTHONPATH=src` |
| Population | verified M2 artifact `jos-population-m2-full-seed-123-ca3aed04498e` |
| Structure | verified M3 artifact `jos-structure-m3-full-seed-123-0a72b6f82d4c` |
| Parent-artifact source | frozen pilot directory listed above |
| M4 preparation | `generate_networks(NetworkGenerationConfig(mode="full", seed=123), m2, m3, root)` before `profiler.enable()` |
| Disease | `configs/diseases/respiratory_seirs_demo.yaml` |
| Observation | `configs/observation/observation_demo.yaml` |
| Scenario | `configs/scenarios/m7_baseline.yaml` |
| Run config | `default_run_config("full", 123, params, duration_days=7)` |
| Scenario overrides | seed 123; start 2025-01-06; duration 7 days; matching disease and observation IDs |
| Profile boundary | only `run_outbreak(network, config, params, observation_config=obs, scenario=scenario)` |
| Profile artifact | `/private/tmp/jsy_v11_r6_7day.prof` (280,372 bytes) |

Network generation was deliberately outside the profiler. The profiled call still regenerated date-sensitive route snapshots through the runtime network providers. No artifact writer or verifier was invoked inside the profile.

`dump_stats()` completed successfully. A subsequent convenience JSON print failed with `AttributeError` because the neutral scenario returned an `OutbreakRunResult`, not an object with `base_result`. That post-profile error does not invalidate the profile, but it means the network-generation elapsed time and exact result hash intended for the final print were not captured. Neither value may be reconstructed or claimed from this run.

## Profile results

The profile contains 954,243,918 calls, of which 936,949,636 were primitive, in 284.170459 seconds of deterministic-profiler time.

### Top cumulative paths

| Path | Calls | Cumulative seconds | Share of profile | Interpretation |
|---|---:|---:|---:|---|
| `run_outbreak()` | 1 | 284.172 | ~100% | Profile boundary; small rounding difference from total |
| `build_starsim_disease_sim()` | 1 | 213.958 | 75.29% | Almost entirely `Sim.init()` |
| Starsim `Sim.init()` | 1 | 213.682 | 75.20% | Fixed setup cost in this run |
| Sciris `search()` | 27 | 212.338 | 74.72% | Nested recursive object-graph work during initialisation |
| Sciris `iterobj()` / `iterate()` | 27 / 27 | 177.798 / 177.795 | 62.57% | Nested beneath initialisation; do not add to parent |
| Starsim `init_dists()` | 1 | 115.363 | 40.60% | Distribution linking over the object graph |
| Starsim `init_modules_pre()` | 1 | 97.543 | 34.33% | Module initialisation; overlaps other child paths |
| Starsim `Sim.run()` | 1 | 69.470 | 24.45% | Seven simulated steps |
| Dynamic `_replace_edges()` | 64 | 45.829 | 16.13% | 8 initial replacements plus 8 routes × 7 steps |
| Dynamic route provider | 64 | 43.239 | 15.22% | Calls `route_snapshot()` and materialises a list |
| `GeneratedNetworks.route_snapshot()` | 67 | 43.175 | 15.19% | Runtime route generation/cache access |
| Community route `build()` | 10 | 26.188 | 9.22% | Multiple community snapshots; nested under route work |
| Respiratory `step()` | 7 | 24.020 | 8.45% | Disease work in the daily loop |
| `_order_invariant_infect()` | 7 | 23.976 | 8.44% | 23.056 seconds self time |
| Community `mixed_edges()` | 10 | 21.604 | 7.60% | 17.667 seconds self time |
| `_stable_int()` | 6,989,778 | 16.014 | 5.64% | String assembly and SHA-256 keyed draws |
| `_job_is_physical_on_date()` | 462,512 | 12.007 | 4.23% | Recomputes deterministic weekly/day choices |
| Edge-array conversion `_edge_arrays()` | 67 | 2.685 | 0.94% | 2.328 seconds self time |
| Edge deduplication | 13,218 | 2.755 | 0.97% | Canonical edge processing |

Shares are descriptive only. Cumulative paths are nested and must not be summed. `Sim.run()` was 69.470 seconds; `_replace_edges()` was 65.97% of that parent and the respiratory step was 34.58%. The 64 edge replacements comprise eight initial route loads plus 56 daily updates. The 67 `route_snapshot()` calls include those replacements and three other accesses.

The dominant self-time entries reinforce the same diagnosis: Sciris object processing/traversal, `_order_invariant_infect()`, community `mixed_edges()`, and `_stable_int()` are Python-heavy paths with very high call counts. The profile's instrumentation cost is correspondingly severe.

### What was small in this early-epidemic profile

- Starsim's transmission kernel itself (`compute_transmission`) accumulated approximately 0.048 seconds across 130 calls. This does not make transmission cheap at later prevalence; it only separates kernel occurrence from JOS attribution work in these seven days.
- The empty baseline intervention manager's daily `step()` accumulated approximately 0.003 seconds. Its initial metadata preparation was approximately 0.688 seconds. Optimising empty-manager dispatch cannot materially address the target runtime.
- Only 63 observation events were scheduled. Event scheduling, scientific hashes, result aggregation, and diagnostics were consequently too small to characterise pilot-scale costs.

### What the profile did not measure

| Area requested by R6 | Status |
|---|---|
| Dynamic-network regeneration | Measured inside the seven-day runtime providers |
| Starsim edge handling | Measured, including replacement and edge-array conversion |
| Route copying/conversion | Measured in providers and `_edge_arrays()` |
| Intervention manager | Measured for the empty baseline only |
| Observation scheduler | Exercised for only 63 events; not representative |
| Attribution | Measured in the early seven-day state |
| Daily diagnostics / event accumulation | Exercised but not representative of the 294,565-event pilot |
| DataFrame/Arrow/Parquet construction | Not invoked; unavailable |
| Artifact hashing and creation | Not invoked; unavailable |
| Artifact verification | Not invoked; unavailable |
| Peak RSS / allocation profile | No memory profiler; unavailable for this run |
| Exact result hash | Lost after `dump_stats()` in the reporting error; unavailable |
| M4 construction elapsed time | Outside the profile and lost in the reporting error |

## Frozen pilot context

The frozen evidence is the production wall-time anchor, not the seven-day profiler duration.

| Pilot item | Measurement |
|---|---:|
| Host | MacBook Air, Apple M4, 10 cores, 16 GB; macOS 26.5.2 |
| Runtime | Python 3.12.13; Starsim 3.5.2 |
| Population / seed | 104,540 residents / 123 |
| Horizon | 180 dated points, 2025-01-06 through 2025-07-04 |
| M2 | 239.377 s |
| M3 | 319.019 s |
| M4 | 32.809 s |
| M5/M6/M7 `result.runtime_seconds` | 9,260.278 s |
| Primary wall time | 9,953.313 s |
| Verification | 5.510 s, PASS |
| Peak RSS | 2,324,103,168 bytes (2.16 GiB); no swaps |

The disease/observation/baseline result was 93.04% of primary wall time. M2+M3+M4 totalled 591.205 seconds, 5.94%. The remaining approximately 101.83 seconds, 1.02%, combines parent loading, artifact writing, CLI/reporting, and other residual work. Artifact writing was not separately instrumented, so 101.83 seconds is only an upper bound for it.

The pilot used the empty `m7-baseline` scenario, no travel, ten seeded infections, the respiratory demonstration disease, and demonstration observation parameters. It produced 294,565 infection episodes (294,555 local plus ten seeded), affecting 99,041 unique residents. Incidence and infectious prevalence changed dramatically over the horizon, including recurrent waves. A seven-day early-epidemic profile with 63 scheduled observations cannot represent the later event, observation, hashing, diagnostics, or memory load.

The pilot's M4 timing came from a separate supported-persistence rerun with the same logical network hash. It must not be attributed to the seven-day profile. Similarly, the verifier's 5.510 seconds was a separate command.

Eliminating all 591.205 seconds of parent construction from this one pilot would have a mathematical wall-time ceiling of only 1.063× (`9953.313 / (9953.313 - 591.205)`). Parent reuse still matters operationally for ensembles, but the pilot evidence rejects parent construction as the principal single-run target for a long horizon.

Thirty sequential replicas at the measured pilot wall time would require about 82.94 hours. Idealised two- and four-worker lower bounds are about 41.47 and 22.12 hours, with pilot-RSS multiples of about 4.33 and 8.66 GiB. These are arithmetic lower bounds, not capacity promises: the host is fanless, tasks contend for memory bandwidth, and concurrent RSS and thermal behaviour were not measured.

## Static explanation of the hot paths

### Starsim initialisation traversal

Starsim initialisation asks Sciris to search and link distributions, modules, and rates recursively. The JOS runtime object graph includes large network structures and plain metadata such as UID/agent mappings and observation-scheduler state. The profile records 17,281,989 `process_obj()` calls and hundreds of millions of type/attribute checks. This proves excessive traversal, but it does not prove which single attached object is responsible. The static candidates must be isolated with one-variable microbenchmarks before changing lifecycle attachment.

### Dynamic networks and edge replacement

Eight route networks are date-sensitive because they have a dynamic builder or a non-`always` calendar. Each daily Starsim network step requests a complete tuple of edge dictionaries, converts it to a list, then converts three fields through Python comprehensions into `p1`, `p2`, and `beta` arrays and creates a duration array. `GeneratedNetworks.route_snapshot()` retains complete snapshots keyed by `(route_id, date)`.

Within route builders, deterministic choices repeatedly construct string keys and SHA-256 digests. Workplace routes repeatedly derive weekly physical/remote weekdays for each job/date. Community routes repeatedly group participants and, inside the contact loop, construct a source-excluding target candidate list. These operations explain the observed `_stable_int()`, `_job_is_physical_on_date()`, and `mixed_edges()` costs.

The snapshot cache may also grow with horizon because complete date-specific edge dictionaries remain reachable. The pilot's 2.16 GiB peak proves the run was feasible, not that this cache dominates memory. Allocation/RSS sampling and cache-size instrumentation are required before adopting or rejecting bounded caching.

### Exact attribution

Starsim determines successful directed-edge transmissions. JOS then scans directed route edges, builds a Python mapping from `(source, target)` to ordered hazard lists, retrieves the hazards for successful pairs, and performs a stable keyed hazard-weighted attribution for each target. The full-edge Python scan and tuple/list/dictionary allocation explain 23.056 seconds of self time even when Starsim's early transmission kernel is small.

This evidence lookup is scientifically protected: duplicate pair occurrences, their order, route candidates, edge counts, hazard values, successful candidates, and the final attributed route all contribute to auditability and/or deterministic output. A fast lookup that merely returns the same final infector is insufficient.

### Observation, post-processing, hashing, and artifacts

The scheduler derives keyed detection/delivery results per infection event and stores pending and delivered state. Static inspection finds repeated immutable observation-config provenance hashing and per-event RNG construction. The outbreak runner later materialises events and repeatedly filters them into daily parish, route, and age diagnostics. Scientific hashing canonicalises complete payloads, and artifact writers convert row dictionaries through Arrow/Parquet.

These are credible high-incidence costs, but the seven-day profile and pilot timers do not quantify them. In particular, the normal baseline scenario does not run the offline observation reconstruction in addition to the online scheduler. This report therefore does not claim duplicate online/offline work. Separate timers are required.

## Ranked optimisation opportunities

Ratings describe the current evidence, not approval. “Speed-up” is expected impact on its applicable workload; it is not a promised factor. Scientific risk is risk of changing modeled meaning. Reproducibility risk is risk of changing fixed-seed identity, order, hashes, or cross-process results.

| Rank | Candidate | Expected speed-up | Effort | Scientific risk | Reproducibility risk | Memory impact |
|---:|---|---|---|---|---|---|
| 1 | Preserve exact route semantics while reducing dynamic route recomputation and edge copying/conversion | High, horizon-scaled; 65.97% of profiled `Sim.run()` sits under edge replacement | Medium–high | Medium | High | Can decrease with streaming/bounded caches; naive precompute can increase sharply |
| 2 | Reduce full-edge Python allocation in exact attribution while retaining every candidate/hazard/order | High within daily loop; 23.056 s self time in seven days | Medium | High | High | Likely decrease |
| 3 | Keep non-linkable bulk plain data out of Starsim/Sciris recursive initialisation traversal | High fixed-cost potential, especially short runs and replicas; long-horizon fraction unknown | Medium | Low if lifecycle truly unchanged | Medium | Neutral to lower |
| 4 | Reuse already-verified M2/M3 parents across ensembles; reuse M4 only for an identical permitted seed/scenario identity | Medium operational ensemble benefit; low single long-run ceiling | Low–medium | Low | Medium | Lower CPU; storage/cache trade-off |
| 5 | Hoist observation constants; then profile high-incidence scheduling | Low–medium, prevalence-scaled but unquantified | Low for immutable hashes; medium for RNG changes | Low for constants | Low for constants; high for RNG redesign | Neutral |
| 6 | Aggregate events/diagnostics in one exact-order pass and separately benchmark canonical hashing/Arrow writing | Low–medium, unquantified; pilot combined residual is at most 1.02% | Medium | Low | Medium | Likely lower transient memory |
| 7 | Special-case the empty baseline manager | Negligible; daily manager work was ~0.003 s | Low | Low | Low | Neutral |

### 1. Dynamic routes and edge materialisation

Prototype the smallest exact transformations separately:

- cache each job's deterministic selected physical/remote weekdays at the same ISO-week key granularity, then perform membership tests without recomputing hashes;
- precompute immutable participant/age-band indices and replace per-contact source-excluding list construction with an index mapping that selects the identical member from the identical canonical order;
- remove redundant tuple-to-list-to-array copies or cache adapter arrays alongside a snapshot only where bounded memory and immutability can be demonstrated;
- preserve route-specific date keys: community contacts are keyed by exact ISO date and cannot be replaced with a repeated weekly snapshot;
- do not parallelise route generation as a first move: process transfer, ordering, memory, and determinism risks are not justified before removing redundant serial work.

A cache of all full-horizon NumPy arrays may be faster but could multiply the already material cache. Prefer a measured streaming or bounded design unless downstream artifact/intervention access requires retention.

### 2. Exact attribution lookup

Candidate approaches include storing hazards only for successful pair keys while scanning edges, or deriving a vectorised/indexed join from successful pairs to directed-edge occurrences. Either approach must preserve duplicate-occurrence ordering and all recorded candidate arrays exactly. Do not replace hazard-weighted attribution with route counts, first-success order, aggregate route probabilities, or a new random draw.

### 3. Starsim initialisation graph

Use isolation benchmarks to determine whether the main traversal comes from network edge payloads, disease-attached observation metadata, UID/agent mappings, or another object. Only then keep proven non-linkable plain data outside the recursively searched graph or attach it after the relevant Starsim linking phase. Existing lifecycle overrides in the neutral manager show that targeted avoidance is possible, but they do not prove that the same technique is safe for disease, networks, or observation state.

### 4. Parent reuse

Verified M2 and M3 artifacts can be loaded rather than regenerated when the ensemble design holds those parents fixed. M4 contains seed-dependent contact randomness and runtime-provider semantics: different replicate seeds must not silently share it. Reuse M4 only when the intended parent identity, seed, scenario/calendar assumptions, artifact verification, and logical hash all match.

### 5–6. Later-horizon materialisation work

Compute immutable observation configuration/provenance hashes once per scheduler. Treat replacement of per-event NumPy generators as a separate, higher-risk proposal because a statistically equivalent generator is not reproducibly equivalent.

For diagnostics, replace repeated day-by-dimension filtering only with an order-preserving single-pass index and prove exact row order and contents. Instrument event materialisation, each diagnostic family, logical hashing, Arrow table construction, Parquet compression, bundle writing, and verification independently before prioritising further work.

## Exact semantics-equivalence gates

Every optimisation must pass all applicable gates with the same frozen inputs and seed. Approximate equality, matching aggregate curves, or a passing high-level suite alone is insufficient.

### Network gate

- For every route and every date exercised, compare the complete canonical ordered edge sequence: route, `p1`, `p2`, weight, persistence, and any supported edge fields.
- Compare per-route snapshot hashes and the M4 logical hash.
- Compare Starsim `p1`, `p2`, `beta`, and `dur` arrays for exact dtype, shape, order, and values; use byte equality where representation is part of the contract.
- Exercise weekdays/weekends, ISO-week transitions, school-term/calendar transitions, workplace remote/physical schedules, dynamic community contacts, supported persistence, and intervention-modified route views.
- Prove the base M4 remains immutable and runtime views do not mutate cached parent state.

### Disease and attribution gate

- Compare the complete ordered transmission-event sequence, not only totals: infection time/date, infected and infector UIDs/agent IDs, source/route, successful-candidate route and edge counts, ordered candidate routes, ordered candidate hazards, and selected attributed route.
- Compare all state arrays and daily epidemic, parish, route, and age outputs exactly.
- Compare `latent_outcome_hash`, M5 logical hash, and the M5 bundle identity required by the existing scientific contract.
- Include no-success, single-route, multiple-route, duplicate-pair, equal-hazard, unequal-hazard, simultaneous-success, and reinfection fixtures.

### Observation gate

- Compare every scheduled and delivered observation event, detection decision, delivery time/date, stable event key, provenance/configuration hash, ordering, pending count, stream fingerprint, and observation logical/bundle hashes.
- Preserve exact online/offline agreement.
- Exercise zero and non-zero onset/detection/report delays and events crossing day boundaries.

### Intervention and lifecycle gate

- Prove exact equivalence for no manager, the empty baseline, an explicit neutral scenario, and representative non-neutral date-, calendar-, and detection-triggered scenarios across all affected route families.
- Compare lifecycle ordering, conflict resolution, route-effect rows, scenario hashes, M7 logical/bundle identity, and all disease/observation outputs.
- Do not move random draws or intervention effects across timestep boundaries.

### Randomness and identity gate

- Preserve every existing seed namespace, key input, canonical order, draw count where sequence-based generators require it, and stable-hash interpretation.
- Repeat in separate processes to confirm cross-process identity.
- Load and verify produced artifacts through public readers; run the scientific verifier and relevant tamper/adversarial tests.
- Require canonical table-level equality and existing scientific logical hashes. Raw Parquet-file byte equality is required only where it is already a contract; writer metadata or compression must not be mistaken for scientific identity.

### Memory and growth gate

- Measure peak RSS and, for cache proposals, retained snapshot/array counts and bytes at 7, 14, and 30 days.
- Reject an unbounded horizon-proportional cache unless the retained data is an explicit existing requirement and the measured memory budget is acceptable.
- Check that a speed improvement does not obtain its result by materialising several full copies of all edges or events.

## Benchmark protocol for approval

1. Benchmark the frozen implementation and one optimisation at a time on the same host, commit ancestry, Python/Starsim environment, verified M2/M3 parents, full 104,540-person population, seed, disease, observation configuration, and scenario.
2. Use unprofiled 7-, 14-, and 30-day runs. Seven days exposes fixed setup; 14 and 30 days expose scaling, later calendars, growing prevalence, observation/event load, and immunity transitions. Do not infer long-horizon behaviour from a single duration.
3. Separate timers for parent loading, M4 construction, Starsim initialisation, per-route snapshot generation, edge conversion/replacement, transmission occurrence, attribution, observation scheduling/delivery, intervention processing, event materialisation, each diagnostic family, scientific hashing, Arrow/Parquet writing, bundle writing, and verification.
4. Record wall time, process CPU time, peak RSS, artifact sizes, event counts, and cache sizes. Run repeated unprofiled trials in interleaved before/after order and report median plus range; do not select the best run.
5. Use the same `cProfile` boundary before and after only to confirm that the intended hot path moved. Calculate the accepted speed-up from unprofiled wall/CPU measurements, not profiler cumulative time.
6. Run focused contract tests first, then the complete relevant suite. Inspect exact output comparisons and implementation logic; a green suite is supporting evidence, not the equivalence proof.
7. Reject the optimisation if any protected fixed-input scientific output changes unintentionally, if performance does not improve reproducibly, or if memory growth is unacceptable.
8. Delay a new 180-day validation until the V1.1 scientific integration is stable and the short representative gates pass.

## Decision for V1.1 synthesis

R6 recommends three prototypes, in order: dynamic-route/edge materialisation, exact attribution lookup, and isolated Starsim initialisation-graph reduction. It does **not** approve any of them for implementation yet. The V1.1 scientific design synthesis should admit only a narrowly specified transformation that has passed the benchmark and exact-equivalence protocol above.

The current evidence is sufficient to stop treating parent construction, the empty intervention manager, or the raw Starsim transmission kernel as the primary explanation for the long-horizon run. It is not sufficient to promise a speed-up or to assign the frozen pilot's 51.446 seconds/day precisely among daily subcomponents. That requires the short, unprofiled, phase-timed before/after runs specified here.
