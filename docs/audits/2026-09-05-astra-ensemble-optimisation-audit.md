# Astra ensemble-optimisation scope audit (2026-09-05)

*Filed verbatim from `~/Documents/jos_ensemble_audit_20260905/AUDIT.md` (WSL/Windows Documents; probes and evidence live beside it: `ensemble_audit.py`, `results.jsonl`, `routes.prof`, `hash_micro.py`, `hash-micro.json`, `evidence-sha256.json`). Companion to `2026-09-05-astra-performance-audit.md`. Read-only audit: no production code changed, no full-wave or ensemble simulation run. Claims here are Astra's measurements on DESKTOP-KQTC6VL; each unit still needs its own equivalence gate before merge.*

---

# 44-replicate ensemble optimisation scope

Read-only audit, 5 September 2026. Target: reduce the elapsed time of the complete 44-seed, 180-day baseline ensemble while preserving scientific outputs exactly. No production changes, commits, full-wave simulation or ensemble simulation were made in this audit.

Source inspected: `036310eed0dafe1e8b19bedeac0a0fb68fb161a8`; its differences from `f5c246c6b2c78860000fe6124dc018a151bd1a50` are six state/documentation files. Measurements used the existing clean detached WSL checkout `/home/steven/jos-astra-perf-f5c246c` at the latter SHA. The immutable historical ensemble is `jos-ensemble-m6-p4-validation-r8-1a0e9c7037ad`, at code `43008ffaad2b4fab4f864312131947bb389555d2`: seeds 101–144, six workers, no M7 scenario, 4864.6885 seconds (81.08 minutes). The earlier audit verified its scientific hashes and replayed its output construction.

## What matters for this workload

The 44 measured replicate durations sum to 27,338.73 worker-seconds. Their sum divided by six is 75.94 minutes; this is an ideal work-balance lower bound using the recorded durations, not a standalone-CPU model. Most of the 81-minute run is therefore replicate work. M2/M3 are built once before `run_ensemble`, then sent repeatedly to workers; each worker generates a seed-specific M4 and a fresh simulation. Sharing one generated network across all seeds would change the experiment.

The previous audit's 433.7-second solo reference predates the already-landed D-2 optimisations. It must not be treated as a current solo baseline or used to credit those gains again. The 81-minute ensemble excludes initial parent construction.

Fresh route-only measurements sampled 30 dates across January–June, all 11 routes, at full population size and seed 101. These are calendar samples, not an epidemic run and not a statistically weighted six-month runtime estimate. Route construction took 35.60 seconds: community indoor/outdoor 19.51, workplace transient 8.28, workplace team 4.57, school cross-class 2.17, and the remainder about 1.07. The harness also converts every route on every sampled date; production keeps always-active static routes as arrays, so its household/care conversions must not be counted as recurring production overhead. Dynamic/calendar route conversion in this probe was about 11.04 seconds. The prior actual 30-day simulation timer measured 11.53 seconds in edge conversion.

A separate four-date cProfile identifies repeated hashing/key construction, community loops, sorting, deduplication, merging and dictionary creation. It made 1.81 million SHA256 calls and 1.25 million canonical-edge calls. Profile timings are instrumented and are not added to the unprofiled measurements.

## Changes to scope, in implementation order

### 1. Remove plain metadata from Starsim's recursive initialisation search — first small, proven opportunity

Locations: `starsim_adapter.py:_make_dynamic_network`, `respiratory.py`, `observation_scheduler.py`, and owning setup in `outbreak_runner.py`.

Keep large, run-constant identity/resident dictionaries behind an explicit owner/reference boundary so Starsim discovers its distributions and rates without recursively walking millions of ordinary metadata objects. Retain normal Starsim initialisation; do not globally patch Sciris, suppress discovery or reuse an initialized simulation.

Evidence carried forward: the prior external prototype removed about 48 seconds of initialization traversal; full 30-day runtime changed from 105.5 to 53.9 seconds with identical latent/outcome hashes. Its observation replay and full M7/M8 checks were not completed. Forty-four times a 48-second saving is approximately 35 worker-minutes, roughly six ideally balanced ensemble minutes before contention/tail effects. This is arithmetic, not a new ensemble timing.

Gate: identical ordered distribution/rate discovery paths and object identity, seed assignments, random-stream states and complete scientific outputs. Include online observation, M7 and M8 ownership/lifetime tests. Effort: medium.

### 2. Make the daily edge path use compact arrays throughout — largest structural long-run priority

Locations: `network_generator.py:RouteSnapshot`, dynamic builders, `_canonical_edge`, `_deduplicate_edges`, `_merge_sorted_edges`; `starsim_adapter.py:_edge_arrays` and `_replace_edges`.

Represent endpoints, weights and persistence in typed columns. Build numeric endpoint pairs directly; use stable pair ordering and deduplication preserving the current maximum-weight/first-on-tie behavior, including persistence. Convert stable IDs using an explicit mapping. Resident UIDs currently follow sorted IDs, but travel mappings must be checked separately. Keep canonical exported edge records and scientific hash bytes unchanged at the serialization boundary. Avoid retaining both full Python dictionaries and arrays for every cached snapshot.

Start with boundary arrays and equivalence tests, then convert the largest builders one at a time. The current conversion work alone costs about 11.5 seconds per measured 30-day simulation, but the bigger potential is avoiding dictionary allocation, repeated endpoint lookups, Python sorting and merging. No whole-route or ensemble speedup is demonstrated yet. Do not claim a 2× simulator gain from a 2× subroutine.

Gate: ordered edge rows, persistence, bit-identical p1/p2/beta arrays, tie behavior, all route fingerprints, unchanged transmission draw inputs and M7/M8 immutable-base behavior. Effort: large; split into reviewable units.

### 3. Pre-encode repeated deterministic hash-key suffixes and pre-index community groups

Locations: community `mixed_edges` and participation paths in `network_generator.py`; retain the frozen SHA256 key specification and public hashing behavior.

Pre-encode known agent-ID/contact-index suffixes once in a bounded per-generated-network structure; concatenate with the exact existing seed/route/date prefix. Reuse existing parish/age-band membership indices and cumulative bounds. Date-dependent participants and targets must still be computed for every date; regular edges are already reused and are not a new saving.

New evidence: 209,080 actual population-ID/contact-index combinations, two seed/date prefixes, three repeats each. Existing helper took 0.186–0.195 seconds; pre-encoded suffix processing 0.095–0.098 seconds, with every returned integer equal. Preparation took 0.0395 seconds; encoded payloads total 3.76 MB, excluding Python container/object overhead. This is a microbenchmark, not a substituted full route or a forecast of ensemble minutes.

Gate: byte-identical full key payloads, identical integer outputs, fingerprints across dates/seeds, empty/same-band cases, and all current activity configurations. The helper's scientific contract and counters must remain intact. Do not replace SHA256 or change random draws. Effort: medium; remeasure after the array work because gains overlap.

### 4. Cache recurring workplace state by weekday, using compact storage

Locations: `build_workplace_team`, physical-workday indexing and `build_workplace_transient` in `network_generator.py`. Follow the roadmap's ordering: after columnar edges.

For workplace teams, retain five compact weekday edge states plus empty weekend behavior. For transient workplaces, precompute only weekday membership lists; the date-specific ring ordering and participant selection remain daily. Keep the normal route calendar check and apply interventions prospectively to separate effective arrays.

New evidence: direct workplace-team builder outputs compared exactly on all 180 dates from 2025-01-06, full seed 101. Reference 29.3766 seconds versus weekday-cache prototype 1.0941 seconds. This proves this builder's ordered edge dictionaries on this fixture, not the full scientific pipeline. Cache contains 738,375 edge rows; caching those dictionaries is not the proposed production representation. Four int64/float64 columns would contain approximately 22.5 MiB of raw data, excluding wrappers and other runtime arrays.

Gate: multiple seeds, calendar boundaries, physical/remote schedule changes and isolation/WFH behavior; bounded memory. Do not use weekday-only cache keys for bus, community or transient contacts. Shared vehicles need a separate invariance proof before joining this change. Effort: medium.

### 5. Reduce worker setup allocation peaks with exact framed M4 hashing

Location: final logical hash construction in `network_generator.py`.

Feed the identical canonical JSON stream to one SHA256 incrementally, using the existing encoder for pieces and preserving sorted keys, punctuation and list order. Avoid materializing the entire ~253 MB encoded payload and its transient copies simultaneously. Keep all hash inputs.

Prior evidence: all 252,689,441 canonical bytes compared equal; transient traced allocation fell from 482 MiB to 37 MiB, with about 0.37 seconds saved in the hashing microbenchmark. The main benefit is memory headroom during concurrent worker generation, not direct runtime. This alone does not establish a higher safe worker count. Effort: small–medium; gate exact bytes plus full hashes.

### 6. Send immutable parents once per worker and bound repeated-job retention

Location: process-pool creation and job submission in `ensemble.py`.

Use a spawn initializer for verified M2/M3 and invariant configs; each task carries seed/provenance and generates its own M4/simulation. Ensure temporary generated networks and simulation cycles are released between jobs. Measure worker RSS/PSS after repeated tasks before introducing forced collection or worker recycling; both can cost more than they save. Do not share mutable simulation or intervention state.

Prior evidence: parent payload 61.75 MB; serialization about 0.72–0.78 seconds and deserialization about 0.30 seconds. Reducing 44 parent transfers to six avoids roughly 40 CPU-seconds, much of which can overlap. This is a small direct speed change, with potential repeated-allocation benefits. M2/M3 generation is already shared; no 15% ensemble saving is supported. Gate seed isolation, authenticated resume, failure behavior and immutable parents. Effort: medium.

### 7. Tune process count only after the above, using measured ensemble throughput

Add a bounded, opt-in benchmark harness recording phase wall/CPU time, worker PSS/RSS, allocation peaks, major faults, swap and completion throughput. Compare equivalent seed batches at four and six workers; consider eight only after memory measurements support it. Inspect any native thread pools and test caps if oversubscription actually exists. Do not assume 16 logical CPUs means 16 efficient workers. Keep runs on WSL ext4 as already done.

At six workers, reaching 40 minutes requires at least about 47% less recorded worker work even with perfect balancing and no other overhead. With eight workers, the same idealized work bound is 57 minutes before optimisations; 40 minutes would still require about 30% less work. These are necessary arithmetic bounds, not forecasts: recorded six-worker durations do not stay fixed when concurrency changes.

A new fixed-duration schedule replay reproduced seed-order completion in 4842.88 seconds, close to the actual 4864.69. Longest-first ordering was worse at 4889.20 seconds. The replay is not an exact historical timeline, and longest-first is not an optimal scheduling proof, but it gives no reason to prioritize queue reordering. Even perfect balance could recover only about 5.1 minutes under fixed durations. Effort: medium measurement work; no higher worker count approved by this audit.

### 8. Skip optional descriptive M4 diagnostics on internal replicate construction

Location: `generate_networks` diagnostics block and `_run_replicate_job`.

Add an explicit internal construction mode that omits only unused descriptive route analysis; keep staffing/provenance, required validation and every hash input. Audit consumers before implementation; absent fields must not silently change a public artifact schema.

Prior ABAB prototype saved 4.86–5.16 seconds per M4 build with identical M4 hash. Across 44 tasks this is roughly 36–38 ideally balanced wall-seconds at six workers. Useful later, not a major ensemble reduction. Effort: medium.

### 9. Vectorize intervention edge modifiers for scenario ensembles

Locations: `interventions.py:_apply_effective_routes` and its per-edge modifier calculations.

Apply UID-indexed adherence/isolation/WFH/closure masks and beta multipliers to compact arrays. Preserve sorted intervention application order, floating multiplication/clamping order, zero-beta care edges and all notifications/logs. Reuse unchanged base endpoints without mutating M4 snapshots.

Prior combined-scenario 30-day measurement spent 60.4 seconds applying effective routes, including 8.43 seconds in conversion. This is an important scenario opportunity but contributes zero to the historical baseline ensemble, which has no scenario. Do not multiply a temporary intervention's 30-day cost by six. Effort: large, after array infrastructure; scenario-specific gates.

## Lower priority or excluded

- M3 secondary-job optimisation remains worthwhile for fresh startup (prior prototype saved ~135 seconds), but is outside the reported 81-minute ensemble and is not multiplied by 44.
- Build the completed grid once instead of twice: prior replay saves approximately 1.5 seconds and 124 MiB transiently after workers have shut down. It cannot unlock another concurrent worker.
- Checkpoint writes were ~0.06 seconds each; artifact writes and summary construction took seconds. Preserve persistence and online/offline observation agreement.
- Avoid increasing the daily snapshot LRU, retaining every date, or evicting M8 identity/evidence stores. Compact bounded representation is the path to lower memory.
- No fewer replicates, coarser timesteps, shortened horizon, sampled contacts, lower precision, changed RNG/hash algorithms, skipped draws or early exit after epidemic extinction. No reuse of an initialized simulation or one seed's network across seeds.
- GPU/distributed migration and a new compiled hashing dependency are not justified first changes by this evidence. Re-profile after the scoped improvements before introducing another runtime.

## Acceptance and evidence

Each implementation unit needs a baseline-versus-candidate benchmark and exact scientific-equivalence evidence before merge. Keep all 44 seed identities and ordered trajectories, M4/latent/observation hashes, ensemble summary/quantile semantics, provenance and authenticated resume. Operational runtimes may differ. Start with focused oracle tests and CI-sized cases, then selected full 7/30-day runs and calendar-only replay, including term boundaries and M7/M8 where affected. Only after those pass should the separately gated full 44-replicate run measure the actual reduction.

This audit did not rerun the test suite because it changed no production code. The new probes passed their explicit equality assertions; they are not a production acceptance verdict. The prior audit's 74-test run remains prior evidence, not a fresh result here.

New reproducible harnesses and results: `ensemble_audit.py`, `results.jsonl`, `routes.prof`, `run.log`, `hash_micro.py`, `hash-micro.json`, `hash-run.log` beside this report. Earlier measurements: `../jos_astra_perf_evidence_20260905/evidence/`, especially `astra-ensemble-micro.log`, `astra-fast-init.log`, `astra-hash-byte-proof.log`, `astra-m4micro.log`, and `astra-timed2.log`. New microbenchmarks are limited fixtures on one machine; no combined speedup has been measured, and the savings must not be blindly added.

Recommendation: ship the initialization improvement as the first measurable unit, then put the main engineering effort into compact daily edges, repeated key preparation and bounded weekday reuse. Measure concurrency again after their memory profile is known. Forty minutes remains a target to test, not a promised outcome.
