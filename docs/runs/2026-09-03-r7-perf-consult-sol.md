# R7 architecture-level performance review

## Executive judgement

The target is plausible, but only through a combined optimization:

1. Reduce exact dynamic-route generation/materialisation by roughly 2.5–4×.
2. Reduce exact attribution lookup by roughly 5–15×.
3. Then run six or preferably seven workers, subject to a measured throughput/RSS sweep.

Neither the bounded cache, higher worker count, M4 persistence, nor `Sim.init()` optimization can reach the target independently.

The current 7/30-day measurements imply approximately:

```text
marginal day cost = (504.65 − 146.28) / 23 = 15.58 s/day
linear fixed component ≈ 37 s
projected 180-day run ≈ 47.4 min
```

To get below 20 minutes, marginal cost must fall below about 6.5 s/day. For the ensemble target with cold parent construction and seven workers, a safer target is approximately 5 s/day, corresponding to a 15–16 minute solo replicate.

Using R6’s profiled 66% route / 34% respiratory split only as an Amdahl prioritization model:

```text
2× routes + 5× attribution → 2.51× loop speed-up → about 19 minutes
3× routes + 5× attribution → 3.47× loop speed-up → about 14 minutes
```

These are projections, not performance claims: R6 correctly warns that its 954-million-call `cProfile` run heavily distorts Python-heavy code ([R6 profile:85](/home/steven/jsy_disease_sim/docs/research/v1_1/R6_PERFORMANCE_PROFILE.md:85)).

The R6 cache change solved the memory problem but not the speed problem: cache retention fell from 257 entries/1.77 GB growth to 33 entries/216 MB growth, while the single 7- and 30-day timing samples slightly increased ([before:5](/home/steven/jsy_disease_sim/docs/runs/2026-09-02-r6-bench-before.json:5), [after:5](/home/steven/jsy_disease_sim/docs/runs/2026-09-02-r6-bench-after.json:5)). The hashes remained identical, which is strong evidence that the cache bound preserved scientific behavior.

Protected contracts remain the complete ordered route snapshots, route calendars and persistence, immutable M4 state, Starsim occurrence union, full attribution evidence, observation lifecycle, RNG namespaces, and scientific hashes ([architecture:301](/home/steven/jsy_disease_sim/docs/architecture.md:301), [architecture:312](/home/steven/jsy_disease_sim/docs/architecture.md:312), [R6 gates:237](/home/steven/jsy_disease_sim/docs/research/v1_1/R6_PERFORMANCE_PROFILE.md:237)).

## Ranked optimization candidates

### 1. Eliminate redundant work inside the dynamic route builders

**Code paths**

- [`GeneratedNetworks.route_snapshot()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:122)
- [`_activity_weighted_participants()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:220)
- [`_job_is_physical_on_date()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:416)
- [`build_school_cross()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:1099)
- [`build_workplace_transient()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:1190)
- [`build_workplace_team()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:1232)
- [`build_shared_vehicle()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:1402)
- [`build_bus()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:1446)
- community [`mixed_edges()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:1496) and daily [`build()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:1593)

**Transformation**

Use closure-local precomputed indices and masks, without introducing a second network implementation:

- Compute each job’s selected and remote weekday sets once per seed/job. `_job_is_physical_on_date()` currently performs ten or more keyed hashes and sorting operations every time a route asks about the same worker’s weekday.
- Resolve each commuter’s primary job once. Bus and shared-vehicle builders currently execute a `next(...)` search inside every daily group traversal.
- Add an exact all-participants fast path. `_activity_participation_probabilities()` already returns `1.0` for every eligible agent when the requested count is the population size ([network_generator.py:189](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:189)), but `_activity_weighted_participants()` still computes a SHA-256 draw for every agent. School cross-class and workplace transient invoke precisely this case.
- In `mixed_edges()`, replace the per-contact source-excluding candidate list with exact index arithmetic over the same sorted age-band list. For a same-band target, select from an `n−1` logical array and skip the source index; for a different band, index directly. Preserve the same `_stable_int`, modulus, sorted list and resulting target.
- Pre-index immutable agent parish/age/adult metadata. The daily community builder repeatedly performs dictionary lookups and rebuilds probability and parish group dictionaries.
- Cache only route states with a proven smaller semantic key. Workplace team depends on weekday; shared vehicle depends on weekday plus its four-week token; bus depends on weekday plus ISO week. Community and ring-based school/workplace contacts remain exact-date keyed and must not be collapsed to weekly snapshots.
- If profiling justifies it, replace the final regular-plus-daily re-deduplication with an exact ordered merge that preserves `_deduplicate_edges()`’s sorted pair order and “larger weight wins” rule ([network_generator.py:260](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:260)).

**Expected gain**

R6 attributes 43.2 profiled seconds to route providers, including 21.6 seconds under community `mixed_edges`, 16.0 seconds under `_stable_int`, and 12.0 seconds under job attendance; these figures overlap but expose the redundant work ([R6 profile:99](/home/steven/jsy_disease_sim/docs/research/v1_1/R6_PERFORMANCE_PROFILE.md:99)).

Expected:

- Dynamic-route phase: **2.5–4×**.
- Whole 180-day replicate by itself: approximately **1.7–2.0×**, or roughly **24–29 minutes**.
- Required contribution to the final combined result: route phase should be at least **2×** faster; below that, the <20-minute plan becomes fragile.

**Risk**

- Scientific: **medium**
- Reproducibility: **high**
- Gates: network, intervention/lifecycle, randomness/identity, memory; downstream disease and observation equality also required.

**One-variable kill benchmark**

Freeze one full-scale M4 and run the eight dynamic builders for exactly the same 30-day date range, with cache hits excluded. Compare the complete ordered edge tuple after every call and report per-route wall time, `_stable_int` call count and peak retained bytes. Benchmark each optimization substep independently.

Kill the tranche if:

- Any edge field or order differs.
- Aggregate dynamic-route generation is less than 2× faster.
- A semantic cache grows with horizon rather than with its declared period.

### 2. Remove the full-edge Python dictionary used for attribution

**Code path**

[`RespiratorySEIRS._order_invariant_infect()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/respiratory.py:287), especially the per-direction `probability_by_pair` construction and `pop(0)` lookup at [lines 343–360](/home/steven/jsy_disease_sim/src/jersey_outbreak/respiratory.py:343).

**Transformation**

Retain all authoritative behavior:

- Keep the existing `trans_rng.rvs()` call.
- Keep the existing Starsim `compute_transmission()` call.
- Keep its successful target/source arrays authoritative.
- Keep `candidates_by_target`, candidate sorting, stable attribution draw and evidence production unchanged.

Replace only the Python scan of every directed edge with a small compiled two-pointer subsequence matcher:

1. Starsim’s successful `(source,target)` sequence is an order-preserving subsequence of the input edge sequence.
2. Walk the input and successful sequences and return the earliest matching input index for each success.
3. This reproduces the current `probability_by_pair[pair].pop(0)` behavior, including duplicate-pair occurrences.
4. Calculate the current scalar hazard expression only at those matched indices.

This is safer than recomputing the transmission mask with NumPy. A NumPy mask could differ in floating evaluation and, with duplicate pairs, can identify the actual successful occurrence rather than the current earliest-occurrence evidence semantics.

**Expected gain**

- Attribution lookup: **5–15×**, depending on success density.
- Whole replicate alone: approximately **1.4–1.5×**, or **33–35 minutes**.
- Combined with candidate 1: plausible **14–19 minutes**.

The Starsim transmission kernel itself was negligible in the early profile; the Python evidence construction dominated ([R6 profile:103](/home/steven/jsy_disease_sim/docs/research/v1_1/R6_PERFORMANCE_PROFILE.md:103), [R6 profile:117](/home/steven/jsy_disease_sim/docs/research/v1_1/R6_PERFORMANCE_PROFILE.md:117)).

**Risk**

- Scientific: **high**
- Reproducibility: **high**
- Gates: disease/attribution and randomness are primary; downstream observation, intervention and identity gates are mandatory.

**One-variable kill benchmark**

Capture real `src`, `trg`, `beta_per_dt`, susceptibility/transmissibility arrays and Starsim outputs from a high-prevalence day. Time only the current lines 343–360 versus the matcher. Compare:

- matched occurrence indices;
- every hazard bit-for-bit;
- ordered candidate route/hazard arrays;
- duplicate-pair fixtures where an earlier duplicate fails and a later one succeeds.

Kill it on any mismatch or if lookup speed-up is below 5×.

### 3. Raise ensemble concurrency only after kernel optimization

**Code path**

[`safe_worker_bound()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/ensemble.py:550) and pool creation at [`run_ensemble()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/ensemble.py:643).

**Transformation**

Calibrate the bound from measured aggregate memory and throughput instead of immediately changing the default fraction:

- Sweep 4, 5, 6 and 7 workers.
- Record per-process USS/PSS, aggregate peak, parent process memory, WSL memory pressure/PSI, CPU time, frequency/thermal drift, and completed replicates per hour.
- Reserve parent and OS headroom explicitly. The current formula applies `0.6` to total physical memory and divides by 3.5 GB, without accounting separately for the roughly 2 GB parent/base footprint ([ensemble.py:553](/home/steven/jsy_disease_sim/src/jersey_outbreak/ensemble.py:553)).
- Select the count maximizing completed replicates/hour, not the count that merely avoids OOM.
- Prefer seven physical-core workers only if it remains faster than six over several waves.

The measured workers were approximately 3.3 GB and four ran with negligible PSI, so the current bound is clearly conservative ([P4 report:25](/home/steven/jsy_disease_sim/docs/runs/2026-09-03-p4-full-scale-ensemble-report.md:25)). That does not yet prove that seven is thermally or memory-bandwidth optimal.

**Expected gain**

With unchanged kernels, four to seven workers lowers 44 equal-duration jobs from 11 waves to 7: only **1.57×**, taking 10.6 hours to roughly **6.7 hours**, not 2.5 hours.

After a threefold loop improvement, seven workers plausibly reduce the ensemble to approximately **2.1–2.3 hours**, leaving limited allowance for parent construction and artifact work.

**Risk**

- Scientific: **low**
- Reproducibility: **low–medium**
- Main risks: cross-process identity, worker failure handling, memory pressure and thermal slowdown.

**One-variable kill benchmark**

Run identical full-scale 14- or 30-day replicates with only `workers` varied: 4/5/6/7. Use at least two complete waves per setting and rotate setting order. Kill seven workers if its throughput is no better than six, aggregate headroom falls below a declared limit, PSI appears, or any scientific hash changes.

### 4. Reuse verified parents and reduce repeated process serialization

**Code paths**

- [`_run_replicate_job()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/ensemble.py:295)
- ensemble job construction at [lines 624–641](/home/steven/jsy_disease_sim/src/jersey_outbreak/ensemble.py:624)
- CLI parent construction at [`_build_m4_for_m6()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/cli.py:155)
- artifact writer [`write_network_artifact()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_artifacts.py:197)

**Transformation**

- Put immutable M2/M3/config objects into each spawned worker once via a process-pool initializer; submit seed and scenario data only. Currently every submitted job serializes M2 and M3 again. Their measured pickled sizes are approximately 18 MB and 35.5 MB ([attr sizes:6](/home/steven/jsy_disease_sim/docs/runs/2026-09-02-r6-attr-sizes.json:6)).
- Load and verify existing M2/M3 parents instead of regenerating and rewriting them when the identity matches.
- For repeated ensemble runs, optionally persist a compact per-seed M4 reconstruction state keyed by generator version, config, seed, M2/M3 hashes and source hashes.

Do not persist all 180 days of snapshots. The former 257-entry cache already serialized to 366.7 MB after 30 days ([attr sizes:3](/home/steven/jsy_disease_sim/docs/runs/2026-09-02-r6-attr-sizes.json:3)); naïve full-horizon storage could reach roughly 2 GB per seed or around 88 GB for 44 seeds.

The existing M4 artifact contains structural edges and only configured selected snapshots ([network_artifacts.py:288](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_artifacts.py:288)); it is not presently a loader-complete representation of all dynamic builder semantics.

**Expected gain**

- Verified M2/M3 reuse: up to roughly **14 minutes per ensemble invocation**, less artifact-loading time.
- Per-seed M4 cache hit: approximately **59 seconds per replicate**, or only about **6–7 minutes of seven-worker ensemble wall time**.
- Pool initializer: unmeasured but probably modest; it should reduce IPC and memory churn.
- Little or no benefit to a fresh ensemble containing 44 unique seeds.

**Risk**

- Scientific: **low**
- Reproducibility/provenance: **medium**
- Never share one M4 across different seeds. For the same seed, instantiate fresh mutable Starsim network objects for each scenario/run.

**One-variable kill benchmark**

For one seed, compare fresh M4 generation with a verified warm reconstruction while holding everything else fixed. Require identical manifest parent identities, M4 hash, every exercised snapshot and adapter array. Kill persistence if warm reconstruction does not save at least 45 seconds or requires horizon-proportional storage.

### 5. Reduce unnecessary Starsim initialization traversal

**Code paths**

- Dynamic networks retain `_uid_by_agent_id` directly at [`starsim_adapter.py:121`](/home/steven/jsy_disease_sim/src/jersey_outbreak/starsim_adapter.py:121).
- The disease retains the entire observation scheduler at [`respiratory.py:162`](/home/steven/jsy_disease_sim/src/jersey_outbreak/respiratory.py:162).
- `sim.init()` occurs at [`starsim_adapter.py:246`](/home/steven/jsy_disease_sim/src/jersey_outbreak/starsim_adapter.py:246).

**Transformation**

Keep proven non-linkable bulk maps outside the Sciris-searchable object graph:

- Let network callbacks close over UID mappings instead of storing the mapping as a direct network attribute.
- Let the disease retain a narrow scheduling callback rather than the scheduler and its 104,540-agent maps.
- Keep strong ownership in `run_outbreak()` so object lifetimes do not change.

Do not detach arbitrary objects around `sim.init()` or override broad Starsim lifecycle methods without identifying the exact traversal owner.

**Expected gain**

The unprofiled 7/30-day timings imply a linear fixed component of only about 37 seconds. Even if every second were `Sim.init()`, eliminating it entirely would improve a 48-minute replicate by only **1.3%**. A realistic gain is probably **10–35 seconds per replicate**.

**Risk**

- Scientific: **low**, if only plain non-linkable data moves.
- Reproducibility/lifecycle: **medium**.

**One-variable kill benchmark**

Construct identical full-scale simulations and time only `sim.init()` while hiding one graph owner at a time: UID mappings, then scheduler maps. Record recursive object visits if possible. Kill each change if it saves less than five seconds or changes any initialized distribution, array, lifecycle hook or output.

### 6. Eliminate duplicate observation scheduling and hoist constants

**Code paths**

- Online scheduling occurs through [`_record_events()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/respiratory.py:235).
- `run_outbreak()` stores the online snapshot at [`outbreak_runner.py:338`](/home/steven/jsy_disease_sim/src/jersey_outbreak/outbreak_runner.py:338).
- The ensemble then invokes [`observe_latent_run()`](/home/steven/jsy_disease_sim/src/jersey_outbreak/ensemble.py:323), which unconditionally rebuilds the schedule offline at [`observation.py:90`](/home/steven/jsy_disease_sim/src/jersey_outbreak/observation.py:90).
- Observation configuration is hashed for every detected event at [`observation_scheduler.py:301`](/home/steven/jsy_disease_sim/src/jersey_outbreak/observation_scheduler.py:301).

This is a post-R6 finding: the current production ensemble path does perform both online and offline scheduling, contrary to the profile document’s statement at [R6 profile:191](/home/steven/jsy_disease_sim/docs/research/v1_1/R6_PERFORMANCE_PROFILE.md:191).

**Transformation**

- Hoist the immutable observation config hash and sorted parameter-status map into `ObservationScheduler.__init__()`.
- After measuring the full 180-day event load, consider consuming the already-produced online snapshot for output materialization. Preserve the independent offline path as an equivalence-gate/debug operation.

Care is required with the current `offline_online_agreement` diagnostic: it must not claim an on-run comparison that was not executed.

**Expected gain**

The entire 30-day observation-plus-trajectory phase measured only 5.06 seconds ([memory profile:71](/home/steven/jsy_disease_sim/docs/runs/2026-09-02-r6-mem-profile-desktop.json:71)). Full-horizon high-incidence cost is unmeasured, but this is probably **seconds to under one minute**, not a primary target contributor.

**Risk**

- Constant hoisting: scientific **low**, reproducibility **low**.
- Removing production offline reconstruction: scientific **low**, reproducibility/observation provenance **medium**.

**One-variable kill benchmark**

Replay one actual 180-day transmission-event list through scheduling and observation aggregation, first with current online-plus-offline work and then with online reuse. Require exact event order, payloads, delays, provenance, fingerprints and logical hash. Kill if the phase is below 30 seconds or the diagnostic cannot remain truthful.

### 7. Optimize adapter conversion and post-processing only if new timers justify it

`_edge_arrays()` performs three Python comprehensions ([starsim_adapter.py:79](/home/steven/jsy_disease_sim/src/jersey_outbreak/starsim_adapter.py:79)), but it accounted for only 2.7 profiled seconds versus 43.2 seconds in route snapshots. Likewise, `run_outbreak()` repeatedly filters events for parish, route and age tables ([outbreak_runner.py:388](/home/steven/jsy_disease_sim/src/jersey_outbreak/outbreak_runner.py:388)) and hashes the full output/projection twice ([outbreak_runner.py:650](/home/steven/jsy_disease_sim/src/jersey_outbreak/outbreak_runner.py:650)), but current wall contributions are unknown.

These are measure-gated follow-ups, not part of the primary plan. Cache adapter arrays only for repeated semantic route states and within a hard bound. Do not create a second authoritative integer-edge model alongside M4.

## Specific judgement on the R6 finalists

### Edge materialisation: retain as the first finalist, but narrow its target

R6 was correct. The present code confirms that route generation, not `_edge_arrays()` alone, is the opportunity. The largest avoidable costs are source-excluding community lists, repeated job hashes, all-one participation hashes and repeated metadata grouping.

The post-R6 cache bound should remain. It reduced cache growth by approximately 88% and retained identical hashes; enlarging it would trade memory back for little reuse because community/ring contacts are exact-date keyed.

### Attribution lookup: retain as the second finalist

This is the cleanest large speed opportunity after route generation. The authoritative Starsim occurrence kernel need not change. A compiled subsequence lookup can remove full-edge Python allocation while preserving the current duplicate-pair evidence semantics exactly.

It has the highest equivalence burden and should follow, not precede, route work.

### Starsim initialization graph: downgrade for the 180-day target

The code still exposes large plain mappings to recursive traversal, so the diagnosis remains valid. But the current unprofiled duration data makes it a small fixed-cost opportunity, probably under one minute per replicate. It is worthwhile for short tests and repeated calibration runs, not as one of the first two changes needed for the 20-minute target.

Do not attempt to amortize `Sim.init()` by resetting or cloning an initialized `Sim`. Initialization links distributions, RNGs, people, modules, networks and loop state; `copy_inputs=False` is not a reusable-template contract. Per-seed networks and RNG state also differ. Narrow graph pruning is defensible; initialized-simulation reuse is not.

## Can `_stable_int` be batched byte-identically?

Yes in principle, but not by ordinary NumPy vectorization.

Each output is the first eight bytes of SHA-256 over an exact string-joined UTF-8 message ([network_generator.py:150](/home/steven/jsy_disease_sim/src/jersey_outbreak/network_generator.py:150)). Independent messages can be processed in bulk while producing identical digests, but:

- `hashlib` exposes scalar message objects, not a multi-buffer SHA API.
- Combining several logical draws into one digest changes every result.
- Switching to a PRNG, Python `hash()`, a different encoding or a different delimiter violates reproducibility.
- Prefix-state copying can be exact if the byte prefix, separator and suffix representation reproduce the current message exactly.
- A native SIMD/multi-buffer SHA implementation could be exact, but adds dependency and portability cost.

The right order is to eliminate unnecessary calls first: precomputed workday masks, all-one participation bypasses and O(1) community candidate selection. Only then benchmark the remaining hashes. A batch implementation should be rejected unless one million representative real keys are all byte-identical across processes and route-generation wall time improves materially, not merely the isolated hash loop.

## Staged plan to reach the target

### Stage 1 — Exact route-builder tranche

Implement the route changes as small independently benchmarked commits: community candidate indexing, workday/primary-job precomputation, all-one participation fast paths, then proven-period route reuse.

Acceptance target:

- Dynamic-route phase at least **2.5× faster**.
- No horizon-proportional retained payloads.
- Complete network equality.

Gate set:

- All 11 routes for every one of the 180 exercised dates.
- Exact ordered `p1`, `p2`, weight, persistence and other fields.
- Exact route snapshot hashes and M4 logical hash.
- Exact Starsim `p1`, `p2`, `beta`, `dur` dtype, shape, order and bytes.
- Weekends, ISO transitions, school-term transitions, physical/remote workdays, community dates, persistence and neutral/non-neutral route views.
- M4 immutability.
- Downstream disease events, state tables, observation schedules and scientific hashes on frozen 7/14/30-day runs.
- Stable-hash key tests and cross-process identity.
- RSS/cache tests at 7/14/30 days.

### Stage 2 — Exact attribution subsequence lookup

Implement only the evidence lookup replacement. Do not change Starsim calls, transmission random draws, candidate sorting or attribution selection.

Acceptance target:

- Attribution lookup at least **5× faster**.
- Combined 30-day marginal slope at or below **5 s/day** for sufficient ensemble margin.
- Projected solo 180-day time below **16 minutes**, followed by one actual 180-day confirmation.

Gate set:

- Network hashes and arrays as unchanged sentinels.
- Complete ordered transmission events and all state/daily tables.
- No-success, single-route, multi-route, duplicate-pair, equal/unequal-hazard, simultaneous-success and reinfection fixtures.
- Exact candidate counts, ordered route arrays, hazard values and selected route.
- Exact `trans_rng` call count/order and attribution key inputs.
- Exact latent, M5 and bundle hashes.
- Exact downstream observation events, deliveries, fingerprints and hashes.
- No-manager, empty, neutral and representative non-neutral scenarios.

If Stage 1 plus Stage 2 does not get below 6.4 s/day, the single-replicate target has not been met and concurrency work should not be presented as compensation.

### Stage 3 — Ensemble execution and verified reuse

After kernel changes, sweep 4–7 workers and choose by throughput. Add the pool initializer and verified M2/M3 reuse; add per-seed M4 persistence only if warm reruns are operationally important.

Acceptance target:

- Seven-worker contended replicate median preferably **≤17.5–18 minutes**.
- Aggregate memory has explicit OS/parent headroom and no PSI/OOM behavior.
- Actual 44-replicate wall time **<9,000 seconds**, including whatever phases the target is intended to include.

Gate set:

- Each seed’s fresh and reused M4 hashes and snapshots match.
- Sequential, four-worker, six-worker and seven-worker scientific tables and hashes match.
- Exact observation and intervention outputs across process modes.
- Seed ordering, failed-replicate behavior and ensemble quantiles remain identical.
- Cross-process repeat on a second invocation.
- Artifact public-reader verification and tamper tests.
- Runtime seconds and worker diagnostics may naturally differ; scientific tables and logical identities must not.

## What I would not do

- Do not change SHA-256, key construction, delimiters or keyed-draw namespaces.
- Do not replace attribution with first-success, route counts, aggregate hazards or a new random draw.
- Do not recompute transmission occurrence independently and treat a statistically equivalent mask as authoritative.
- Do not cache all 180-day snapshots or adapter arrays.
- Do not restore an unbounded snapshot cache.
- Do not persist a multi-gigabyte full-horizon M4 per seed.
- Do not share seed-dependent M4 state across different seeds.
- Do not clone/reset initialized Starsim simulations across replicates.
- Do not increase to seven workers solely because aggregate RSS appears to fit; throughput and thermal contention decide.
- Do not use 16 logical workers on this eight-core host.
- Do not parallelize individual route builders before eliminating their redundant scalar work.
- Do not pool observation RNGs or otherwise change per-event seeded generator construction.
- Do not optimize the empty intervention manager: its measured daily cost was approximately 0.003 seconds ([R6 profile:115](/home/steven/jsy_disease_sim/docs/research/v1_1/R6_PERFORMANCE_PROFILE.md:115)).
- Do not introduce a second authoritative edge representation or broad native rewrite before the narrow route and attribution prototypes prove insufficient.

No files were changed; the worktree remained clean.

CONSULTANT: gpt-5.6-sol