# JOS independent performance audit

*Filed 2026-09-05 from Steven's chat paste of the GPT-6 Astra report (prompt: `docs/handoff/2026-09-05-astra-performance-audit-prompt.md`). Evidence archive (371 files, profiles, benchmark scripts, SHA-256 inventory): `~/Documents/jos_astra_perf_evidence_20260905/` (Windows Documents; `performance-audit-evidence.zip` + `evidence/`). Companion focused audit: `2026-09-05-astra-ensemble-optimisation-audit.md`. Read-only: no tracked file edited, no commit, no push, no 180-day or 44-replicate run. All figures are Astra's measurements on DESKTOP-KQTC6VL at the audited SHA; every candidate still needs its exact-equivalence gate before merge.*

---

## 1. Identity, scope and conclusion
**Audited SHA:** `f5c246c6b2c78860000fe6124dc018a151bd1a50`
**Date/model:** 2026-09-05 · GPT-6 Astra
**Machine:** DESKTOP-KQTC6VL, Ryzen 7 5800X, 8 cores/16 threads, Ubuntu WSL2, 26 GiB RAM.
**Environment:** Python 3.12.13, NumPy 2.5.2, PyArrow 22.0.0, Starsim 3.5.2, frozen `uv.lock`.

**No additional 10× improvement to an entire workload is demonstrated.** There are substantial, exact-output opportunities:
- A metadata-discovery prototype reduced a full-mode 30-day run from **105.5 to 53.9 seconds**, preserving latent and outcome hashes.
- The M3 secondary-job loop fell from **136.2 to 1.25 seconds**, preserving its output, final RNG state, and subsequently the full M3 logical hash.
- Framing the unchanged M4 canonical byte stream reduced traced transient allocation from **482.0 to 37.2 MiB**.

The first implementation tranche should target those three findings.

All measurements used the detached audited checkout. The shared checkout advanced through documentation changes during the audit. **No tracked files were edited by this audit; no commits or pushes occurred. Audited diff stat: empty.**

### Corrections to the starting assumptions
1. **Workers do not rebuild M2/M3.** They receive serialized parent inputs and regenerate M4 for each replicate. Consequently, eliminating "parent build × six workers" is not an available saving.
2. **The 433.7-second measurement precedes the D-2 commit.** It is a historical reference, not a measured solo baseline at the audited SHA. The 81-minute validation ensemble is post-D-2.
3. **The 81-minute timer excludes initial parent construction.** It starts inside `run_ensemble`, after the generated parent network is supplied.
4. **An empty intervention manager's apparent daily tax is predominantly initialization.** Current measurements do not support treating it as a constant per-day cost.
5. **Duplicate ensemble grids are constructed after the worker pool closes.** Removing that duplication will not provide memory for another concurrent worker.

The landed R6–R8 scientific-equivalence claims survived the checks performed here. I found no reason to undo those optimizations.

### Commands and verification
The measurement invocations below abbreviate the external harness directory as `$A`. Execution was sequential; profiling and memory sizing were separate from ordinary timing.
```bash
cd /home/steven/jos-astra-perf-f5c246c
git rev-parse HEAD
uv sync --frozen
uv run jos demo --seed 123
uv run python scripts/bench_dynamic_routes.py --help
A=/mnt/c/Users/StevBeast/Documents/jos_astra_perf_evidence_20260905
uv run python "$A/campaign.py" --mode full --days 7 30
uv run python "$A/timed_campaign.py" --mode full --days 7 30 --tag=-timed
uv run python "$A/campaign.py" --mode full --days 7 30 --profile
uv run python "$A/m3_micro.py"
uv run python "$A/m3_micro.py" --fast-only
uv run python "$A/discovery_micro.py"
uv run python "$A/discovery_micro.py" --fast-only
uv run python "$A/m4_micro.py"
uv run python "$A/hash_memory.py"
uv run --with pympler python "$A/ensemble_micro.py"
uv run python "$A/routes.py"
for astra_horizon in 1 7 14 30; do
  uv run --with pympler python "$A/memory.py" --horizon "$astra_horizon"
done
uv run python "$A/timed_campaign.py" --mode full --days 7 30 \
  --offline-only --tag=-calibration
uv run python "$A/timed_campaign.py" --mode ci --days 7 30 --tag=-ci-timed
uv run python "$A/timed_campaign.py" --mode ci --days 7 30 \
  --offline-only --tag=-calibration
uv run python "$A/timed_campaign.py" --mode full --days 30 \
  --scenarios m7_baseline m7_community_indoor m7_combined --tag=-m7-timed
uv run python "$A/timed_campaign.py" --mode full --days 30 --tag=-timed2
uv run pytest -q \
  tests/test_golden_hashes.py \
  tests/test_bench_dynamic_routes.py \
  tests/test_respiratory_attribution_lookup.py \
  tests/test_ensemble.py \
  tests/test_m7_interventions.py \
  tests/test_c5_m7_integrity.py \
  tests/test_job_liveness.py
```
Trimmed results:
```text
f5c246c6b2c78860000fe6124dc018a151bd1a50
demo: Starsim 3.5.2; seed 123; cumulative_infections 37
route fingerprints identical: standard and term-boundary windows
full M3 prototype hash equals frozen parent hash
canonical_stream_byte_equality: true; compared_bytes: 252689441
74 passed in 198.03s
git status --porcelain: empty
git diff --stat: empty
```
cProfile worked without a sandbox blocker. No 180-day simulation or 44-replicate simulation ensemble was run. Ensemble measurements below replay existing outputs or use no-op payload-transfer jobs.

## 2. Measurements
### Parent construction
Full mode, seed 101:
| Phase | Seconds |
|---|---:|
| M2 generation | 79.03 |
| M2 write / verified reload | 1.80 |
| M3 generation | 147.12 |
| M3 write / verified reload | 2.58 |
| M4 generation | 18.27 |
| **Total** | **248.81** |

M2, M3 and M4 hashes matched the frozen validation ensemble's seed-101 inputs.

### Replicate phases
Ordinary, unprofiled runs measured **61.19 seconds at 7 days** and **105.46 seconds at 30 days**, excluding parent construction and subsequent offline observation.

The following additive breakdown comes from the final lightweight-timer 30-day pass. Initialization excludes work assigned separately to routes, arrays and observation.
| Phase | Seconds | Share |
|---|---:|---:|
| Initialization | 48.41 | 47.83% |
| Route snapshots | 34.39 | 33.97% |
| Edge-to-array conversion | 11.53 | 11.39% |
| Online observation scheduling | 2.43 | 2.40% |
| Transmission processing excluding attribution lookup | 1.07 | 1.06% |
| Attribution lookup | 0.40 | 0.39% |
| Scientific hashes | 0.95 | 0.94% |
| Remaining loop/post-processing | 2.05 | 2.02% |
| **Total** | **101.22** | **100%** |

The earlier lightweight pass took 102.98 seconds. These are individual measurements, not a statistically fitted interval.

At 30 days, the ordinary pass additionally measured:
- Offline observation: **2.90 s**
- Latent artifact writing: **0.17 s**
- Observation artifact writing: **0.28 s**

cProfile inflated the 7/30-day runs to 157.6/238.5 seconds. Its useful finding was **27 recursive searches visiting approximately 10.25 million objects**, rather than those instrumented wall times.

### Route harness
All **561 route/date pairs** across the two windows matched committed edge and `p1/p2/beta/dur` fingerprints.
| Route | Standard, 30 dates: s | Term boundary, 21 dates: s |
|---|---:|---:|
| bus | 0.653 | 0.339 |
| care_resident | 0.001 | 0.001 |
| care_staff | 0.001 | 0.001 |
| community_indoor | 12.152 | 8.725 |
| community_outdoor | 8.066 | 5.772 |
| household | 0.043 | 0.033 |
| school_class | 0.059 | 0.028 |
| school_cross_class | 2.556 | 1.160 |
| shared_vehicle | 0.409 | 0.310 |
| workplace_team | 4.232 | 2.955 |
| workplace_transient | 7.815 | 5.643 |
| **Total** | **35.987** | **24.966** |

The standard-window improvement over the committed pre-D-2 fixture was **1.289×**, consistent with the landed D-2 claim.

### Interventions
Full mode, seed 101, 30 days:
| Scenario | Run: s | `Sim.init`: s | Route-effect application: s |
|---|---:|---:|---:|
| No manager | 101.22 | 48.82 | — |
| Empty manager | 141.29 | 88.56 | 0.002 |
| Community indoor | 154.68 | 90.88 | 10.63 |
| Combined | 225.62 | 92.24 | 60.41 |

Route-effect application includes effective-array conversion: **1.99 s** for community indoor and **8.43 s** for combined.

All three scenarios retained the earlier campaign's latent and outcome hashes. The combined scenario's school/WFH windows are January 13–24; multiplying its measured tax by six would not establish a 180-day cost.

### Memory
Each horizon used a fresh process. RSS was sampled at the final disease update, **before sizing and final output extraction**.

Pympler sized named data roots jointly, including parents, generated networks, snapshots, simulation state, events and direct builder-closure contents. These are scoped data-graph sizes, not complete process memory.
| Horizon | RSS: GiB | Joint data roots: GiB | Cache entries |
|---|---:|---:|---:|
| 1 | 1.258 | 0.760 | 33 |
| 7 | 1.395 | 0.800 | 33 |
| 14 | 1.414 | 0.802 | 33 |
| 30 | 1.501 | 0.944 | 33 |

The 30-day snapshot root alone measured approximately **286 MiB**, including shared referents. Individual root sizes must not be added together.

These measurements do not replace a concurrent 180-day worker-footprint measurement or authorize seven workers.

### Ensemble overhead
The historical records establish:
| Quantity | Result |
|---|---:|
| `run_ensemble` wall | 4,864.69 s |
| Replicate runtime minimum / median / maximum | 498.14 / 627.48 / 652.96 s |
| Sum of replicate runtimes | 27,338.73 s |
| Sum divided by six | 4,556.45 s |
| Difference from ensemble wall | 308.23 s |

The last difference includes occupancy/tail effects and execution overhead. **It cannot be assigned entirely to serialization or I/O.** Exact historical critical-path attribution is unavailable from the retained records.

Current replay measurements on the actual frozen trajectories:
| Operation | Seconds |
|---|---:|
| Completed grid | 1.54 |
| Summary, including its second grid | 2.50 |
| Ensemble logical hash | 1.21 |
| Three Parquet writes combined | 0.45 |
| File hashing for those writes | <0.001 |
| Checkpoint write, three measured seeds | 0.059–0.063 each |

Replay reproduced ensemble hash `1a0e9c7037ad9736f8eead680e582f1409a9e26b8f13c6f1f410d899e10bb376` and **all three raw Parquet hashes**.

One completed grid measured **124.3 MiB**, rather than the earlier approximately 304 MB estimate.

Parent transfer:
- Pickled payload: **61,745,705 bytes**
- Pickle: **0.72–0.78 s**
- Unpickle: **0.30–0.32 s**
- Twelve no-op jobs carrying real parents: **12.27 s at one worker; 13.68 s at six**, including spawn/import/transfer overhead

An initializer can eliminate repeated transfers. These measurements do not support a 15% ensemble-wall claim.

### Calibration shape
The existing beta-recovery implementation already reuses networks across candidate beta values and uses offline observation.
| Workload | Initialization: s | Simulation: s | Offline observation: s |
|---|---:|---:|---:|
| Full, 7 days, calibration path | 8.44 | 18.33 | 0.03 |
| Full, 30 days, calibration path | 10.17 | 61.86 | 2.81 |
| `ci`, 30 days, calibration path | 0.32 | 1.47 | 0.12 |
| `ci`, 30 days, online path | 1.38 | 2.65 | 0.12 |

`ci` contained 3,000 agents; full mode contained 104,540.

For this fixture, 1,000 full-mode calibration trials cost approximately **18 serial hours**, excluding one-time parents. The ideal six-way floor is approximately three hours; actual parallel calibration throughput was not measured.

Fresh imports took approximately **1.8–3.1 seconds** across processes. Persistent execution matters particularly for `ci`, but the current inner recovery loop already avoids per-trial imports.

## 3. Ranked candidates
Ranking prioritizes recurring replicate/trial work, then fresh-parent latency. Effort estimates: **S** roughly half a day; **M** one to three days; **L** more than three days. All implementation candidates still **need proof** before merging.

### PERF-1 — Keep plain metadata outside Starsim discovery
**Location:** `starsim_adapter.py:131`, `respiratory.py:212`, `observation_scheduler.py:143`.
**Mechanism:** avoid recursively traversing UID and resident metadata when finding Starsim distributions and rates. Preserve normal discovery and every discovered path. The audit's `skip`-ID monkeypatch is a measurement prototype, not a proposed production library patch.
**Measured gain:** discovery **48.56 → 0.045 s**; ordered paths and object identities matched. A 30-day prototype actually using the pruned result ran in **53.90 s**, retaining exact latent/outcome hashes. Expected recurring saving: approximately **48 s with online observation**, substantially less on the existing offline calibration path.
**Gate:** exact ordered distribution/rate traces, distribution seeds and RNG states; bit-identical initialized state arrays; 7/30-day latent, outcome and observation hashes; M7/C5 lifecycle tests and M8 golden fixtures. Preserve metadata lifetime and consumer connections.
**Risk:** needs proof. **Effort:** M. **Dependencies:** none.

### PERF-2 — DATA-1: finish the M3 secondary-job transformations
**Location:** `population_structure_generator.py:1082`.
**Mechanism:** primary-job index; remaining-workplace counter; order-preserving candidate removal; equivalent scalar index draw.
**Measured gain:** real 4,063-iteration loop over 50,109 candidates: **136.15 → 1.25 s**. Jobs, remaining slots and final PCG64 state matched. Running the production tail reproduced full M3 hash:
`b7d2fb34a7e08b6089c21f80b02c44f3f0eb6010c19ef72818f9c24b2ad54ccd`
The draw oracle passed **1,200 cases**, covering 200 seeds and six list lengths.
Expected saving: approximately **135 s per fresh full parent build**. This is not a per-ensemble-replicate saving.
**Gate:** golden M2/M3 hashes and table hashes; full-mode multi-seed original/prototype comparisons including final RNG state; downstream M4 fingerprints.
**Risk:** needs proof beyond seed 101. **Effort:** M. **Dependencies:** existing DATA-6 gate. **Backlog verdict:** **confirm; raise priority**.

### PERF-3 — ROUTE-11 hash portion: frame identical canonical bytes
**Location:** `network_generator.py:2069`.
**Mechanism:** feed the existing encoder's unchanged sub-payload bytes, with exact container framing, into one SHA-256 state.
**Measured gain:** **482.0 → 37.2 MiB** traced transient allocation; approximately **2.46 → 2.09 s** hashing. All **252,689,441 bytes** matched the monolithic stream.
Expected benefit is approximately **445 MiB less transient Python allocation per M4 build**; wall savings are minor.
**Gate:** byte-stream equality, not merely equal digests; M4 golden hashes, full-mode payloads in separate processes, both fingerprint windows, unchanged encoder behavior and artifact schema.
**Risk:** needs proof across supported configurations. **Effort:** S–M. **Dependencies:** none. **Backlog verdict:** **confirm as memory work**.

### PERF-4 — ROUTE-11 diagnostics switch
**Location:** `network_generator.py:1789`.
**Mechanism:** omit expensive route diagnostics on eligible run paths while retaining required staffing diagnostics, unconditional scientific hashing and full writer/verification behavior.
**Measured gain:** **4.86 and 5.16 s per M4 build**; hashes remained identical. This straddles the binding five-second cutoff.
**Gate:** demonstrate a repeatable median saving of at least five seconds; audit all consumers; preserve staffing diagnostics; match M4 hashes and both complete fingerprint windows; test M7/M8 callers.
**Risk:** needs proof. **Effort:** M. **Dependencies:** consumer audit. **Backlog verdict:** **borderline; re-rank below PERF-1–3**.

### PERF-5 — Parallelize predeclared calibration batches
**Location:** `calibration.py:354–384`.
**Mechanism:** execute independent cells of the existing fixed beta grid in bounded processes, amortizing parent/network setup. Restore the original seed, trial and floating-point aggregation order.
**Measured basis:** the serial trial costs **64.67 s** in the measured full-mode fixture. Six workers provide a theoretical 6× ceiling; historical ensemble contention suggests approximately **4× throughput** as a planning estimate. This is **arithmetic, not a measured calibration speedup**.
**Gate:** byte-identical complete calibration logical hash, trial rows, selected parameter, objective components, train/held-out outputs and diagnostics versus sequential execution; test worker completion permutations and failures. Use the same trials and seeds.
**Risk:** needs proof. **Effort:** L. **Dependencies:** PROV-8 and verified worker initialization. **Scope:** fixed predeclared grids only; adaptive Optuna scheduling is excluded.

### PERF-6 — DISEASE-1 step 3: effective-route vectorization
**Location:** `interventions.py:819`, `:952`.
**Measured hotspot:** **60.41 s** in combined-scenario route application, including **8.43 s** array conversion.
**Expected gain:** a 2–5× improvement to that block would save approximately **30–48 s per measured 30-day combined run**. This is a profile-based target, not a demonstrated vectorized implementation or a 180-day projection.
**Gate:** scalar oracle for every intervention type and interaction; exact multiplication/clamping order; retained zero-beta care edges; bit-identical arrays, hazards, event/state logs, scenario hashes and observation outputs; C5 lifecycle ordering.
**Risk:** needs proof. **Effort:** L. **Dependencies:** existing D-1 predicates. **Backlog verdict:** **confirm, but separate fixed initialization from the kernel prize**.

### PERF-7 — ROUTE-5: exact columnar edges/array boundary
**Location:** `network_generator.py:79`, `starsim_adapter.py:79`.
**Measured hotspot:** **11.53 s/30 days** converting edge dictionaries into arrays.
**Expected gain:** a 5× boundary improvement would save approximately **9 s/30 days**. Rough 180-day arithmetic gives approximately **50 s**, subject to calendar coverage. Additional route-generation savings are unmeasured and are not credited.
**Gate:** the three-phase route gate: canonical row equivalence, all 11 route/date fingerprints, and exact `p1/p2/beta/dur` dtype/order/bytes; full M4 hashes and attribution oracle. Preserve endpoint identity and persistence metadata.
**Risk:** needs proof. **Effort:** L. **Dependencies:** staged representation proof. **Backlog verdict:** **confirm**, particularly for calibration, where routes and conversion dominate.
A 16-byte-per-edge estimate is incomplete if weights and persistence must also be retained.

### PERF-8 — ROUTE-4: smaller semantic cache keys
**Location:** `network_generator.py:1326`, `:1489`.
**Mechanism:** memoize workplace-team states by weekday and shared-vehicle states by their proven period.
**Measured basis:** these routes cost **4.23 and 0.41 s** over the standard window. Most repeated workplace-team generation is avoidable; approximately **4 s/30 days**, or roughly **20–25 s/180 days**, is a reasonable arithmetic target.
**Gate:** original/cached fingerprints and array bytes across both windows and period boundaries, multiple seeds and non-default configurations; bounded retention.
**Risk:** needs proof. **Effort:** M. **Dependencies:** ROUTE-5, per the binding ordering. **Backlog verdict:** **confirm**. Bus is excluded.

### PERF-9 — Verified parent reuse and pool initializer
**Location:** `cli.py:155`, `ensemble.py:889`, `:953`.
**Measured basis:** verified reloads cost approximately **3.5 s**, versus the 248.8-second fresh stack; repeated parent serialization costs approximately **one CPU-second per transfer**.
**Expected gain:** substantial across repeated compatible top-level invocations; **no M2/M3 rebuild saving inside the existing ensemble**. An initializer removes approximately 38 repeated transfers in a 44-job/six-worker run—roughly 40 CPU-seconds, much of which may overlap simulation. Expect seconds or tens of wall seconds, not 15%.
**Gate:** verified cold/reused parent hashes, tamper rejection, complete configuration/provenance keys, sequential/parallel replicate and ensemble hash equality, unchanged resume authentication.
**Risk:** needs proof. **Effort:** M. **Dependencies:** PROV-8. **Backlog verdict:** **confirm mechanism; sharply lower ensemble-wall estimate**.

### PERF-10 — DISEASE-3: reuse the completed grid
**Location:** `ensemble.py:548`, `:632`.
**Measured basis:** the duplicated grid takes **1.54 s** and one grid occupies **124.3 MiB**.
**Expected gain:** approximately **1–1.5 s** and removal of one transient grid. Do not claim another worker from this saving.
**Gate:** exact grid, summary, trajectories and ensemble hash; failed-replicate handling; metric horizons, cell semantics and quantile rules unchanged. The known incidence-horizon correction remains separate.
**Risk:** needs proof. **Effort:** S. **Dependencies:** none. **Backlog verdict:** **confirm, low priority**.

### Remaining named backlog
- **PROV-8:** confirm as a prerequisite, not a standalone speedup. Consolidation alone saves **zero measured runtime**. Preserve all existing entry-point identities.
- **PROV-10:** drop from this performance tranche. An empty registry claim measured **0.269 ms**, approximately **0.54% of one core** at 20 polls/second. Heartbeat authorship remains a separate operational correctness issue.

## 4. Hash-migration track
Numba/Cython or columnar storage do **not inherently require** a hash migration. If they preserve every protected byte, they belong behind equivalence gates.

Variants that alter floating-point results, endpoint ordering, duplicate-edge semantics, persistence meaning or canonical scientific rows are **not through an equivalence gate**. They require separately specified scientific/schema changes and explicit historical hash migrations.

No migration-dependent option has a measured gain here sufficient to recommend it over the exact candidates. Replacing draw identities or changing RNG consumption remains forbidden.

## 5. Would not do
- Replace SHA-256, combine draws, alter delimiters or switch canonical encoders.
- Enlarge the R6 LRU or retain full-horizon snapshots.
- Evict M8 evidence stores; deduplication must preserve their complete logical evidence.
- Change replicate counts, quantiles or population scale and call that an exact speedup.
- Reuse initialized Sims or RNG generators without a complete state/lifecycle proof.
- Remove online/offline observation verification to obtain the calibration-path timing.
- Parallelize adaptive optimization in a way that changes trial selection or aggregation order.
- Raise workers above six using these short-horizon memory samples.
- Optimize attribution, ordinary Parquet writing or checkpoint frequency ahead of the measured initialization/kernel work.
- Attribute the historical 308-second occupancy residual entirely to I/O.
- Route scientific corrections, including DISEASE-4, through this performance campaign.

## 6. Proposed `$foreman` run
**First-tranche predicate**
> PERF-1–3 landed with byte-identical protected outputs; full-mode cold parent stack ≤120 s; M4 hashing transient allocation ≤64 MiB; authorized validation subsequently demonstrates solo 180-day `run_outbreak` ≤390 s and the same 44-replicate ensemble ≤75 min at six workers.

The long runs require the existing gate order and Steven's authorization. They are not first-brief acceptance commands.

**Budget:** three implementation iterations, at most three Codex implementation runs per iteration: **nine implementation runs**, plus two independent review/audit runs. PERF-4 is a subsequent measurement decision because it barely meets its cutoff.

**First brief:** PERF-1 only. Keep production discovery intact, move only proven plain metadata outside its traversal, and preserve strong ownership/lifetime. No global monkeypatch to Starsim/sciris in production.

The executor must add the named boundary test and benchmark harness below. The harness must emit the explicitly asserted fields; these files are proposed deliverables, not existing repository tools.
```bash
set -euo pipefail
uv sync --frozen
uv run pytest -q \
  tests/test_init_metadata_boundary.py \
  tests/test_golden_hashes.py \
  tests/test_bench_dynamic_routes.py \
  tests/test_respiratory_attribution_lookup.py \
  tests/test_ensemble.py \
  tests/test_m7_interventions.py \
  tests/test_c5_m7_integrity.py \
  tests/test_m8_travel.py \
  tests/test_m8_1_travel_integrity.py \
  tests/test_m8_2_travel_closure.py
uv run python scripts/bench_init_metadata_boundary.py \
  --base f5c246c6b2c78860000fe6124dc018a151bd1a50 \
  --modes ci full --seeds 101 123 124 --days 7 30 \
  --out /tmp/jos-perf1-proof.json
uv run python - <<'PY'
import json
p = json.load(open("/tmp/jos-perf1-proof.json"))
assert p["ordered_distribution_and_rate_paths_equal"]
assert p["distribution_seeds_and_rng_states_equal"]
assert p["initialized_arrays_bit_equal"]
assert p["all_scientific_hashes_equal"]
assert p["all_route_and_array_fingerprints_equal"]
assert p["lifecycle_and_consumer_order_equal"]
assert p["full_online_init_median_s"] <= 5
assert p["full_online_7d_median_s"] <= 20
assert p["full_online_30d_median_s"] <= 65
PY
git diff --check
```
Before any proposed push, mirror the complete current `.github/workflows/ci.yml` verification steps, as DIRECTOR requires.

### Projection discipline
The headline projection credits **only PERF-1–3**, using approximately 48 seconds of recurring initialization saving plus the small M4 hash saving. It does not credit unimplemented vectorization, calibration parallelism, borderline diagnostics savings, or unmeasured benefits already landed in D-2.

The 433.7-second reference's older code identity and uncertain contention scaling make the long-horizon projection **low confidence**. The directly measured 30-day prototype result is considerably stronger evidence than that extrapolation.

**PERF AUDIT: 10 candidates; projected replicate 385 s (from 433.7); projected ensemble 74 min (from 81); confidence low.**
