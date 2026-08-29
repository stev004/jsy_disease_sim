# Jersey Outbreak Simulator progress ledger

**Last verified:** 29 August 2026
**Current verified milestone:** M9.2 provenance closure
**M9.2 implementation commit:** `5be3bbf494f5ae85d7f9c3181fc9bcc73212294a`
**C3 verification commit:** `658364c7f02cf44f9392116e7db44c94bdb3175a`
**M9 status:** functional PASS; final evidence/documentation closure in progress
**M10:** CLOSED pending the final independent M9 gate

This ledger records the current implementation and verification state. The
project charter remains the authoritative specification; this file records
which gates have actually passed and the evidence supporting them.

## Gate status

| Gate | Status | Verification boundary |
|---:|---|---|---|
| M0 | PASS | Starsim 3.5.2 compatibility and deterministic demo |
| M1 | PASS | Registered Jersey sources, canonical tables and quality report |
| M2 | PASS | 104,540 synthetic residents; logical hash `bc1e30281edc211dd860cd515450029e2e549cf2b33297d679b9c4b6b975296a` |
| M3 | PASS | 104,540 residents, 48 schools, 703 classes, 58,045 primary jobs and 4,063 secondary jobs; logical hash `b445ee6eb8f366bd07157a1ca8d3f5757892609a5067bf33d5df061b86aad9b7` |
| M4.1 / C1 | PASS | Employment-universe, identity, staffing, geography and institutional-commute blockers closed in `1e501db41f9b0fbf5b3b5ebd57f550bc6dc0450f` |
| C2 | PASS | Nested-route, overlap-policy, shared-vehicle, age-mixing, persistence, calendar and attribution blockers closed in `4dade853dda9c9f7e63df3fc80df10297b41db06` |
| M5 | PASS | Generic respiratory SEIRS demonstration remains compatible with the corrected network |
| M6 / C3 | PASS | Observation, ensemble, calibration, process-safety and archive contracts verified at `658364c7f02cf44f9392116e7db44c94bdb3175a` |
| C4 | PASS | Runtime detection delivery, metric-aware ensemble grids, truthful fallback workers and zero-contact boundary verified on a fresh full-island path |
| M7 | PASS | Typed composable interventions, causal detection effects, route composition, vaccination, artifacts, comparisons and bounded ensembles |
| M8 | PASS | M8.2 closes the three blockers remaining after the independent M8.1 FAIL: episode-safe observations, departed-result lifecycle and typed combined-event artifacts |

The C3 implementation was committed in `0f6667791e481fd2ed5d389d2ea0cb05b8a0d7e9`;
its final integrity hardening is the C3 verification commit recorded above.

## C1 evidence summary

The full corrected population contains 104,540 synthetic agents. Household
checks found 15,375 parent/child households, zero child/parent reversals, zero
gaps below the configured 15-year minimum, a minimum gap of 15 years, median
22 years, and P95/P99 gaps of 46/53 years. The 18,612 ordinary adult-partner
couples have a median age gap of 10 years; 8,861 exceed 10 years, 5,249 exceed
15 years, none exceed 25 years, and the maximum is 25 years.

Communal-setting age checks were: nursing care 637 residents (0 under 18,
195 aged 18–64, 442 aged 65+); non-nursing care 332 (0, 114, 218); children's
homes 15 (15, 0, 0); and detention 149 (0, 149, 0). Setting-specific
eligibility violations were zero.

Parish population and broad-age targets reconcile exactly (all reported cell
errors zero), with parish age×sex structure derived by raking 2021 parish
age×sex data to the 2024 global controls. Generated no-car percentages were:

| Parish | % no car | Parish | % no car |
|---|---:|---|---:|
| Grouville | 8.49 | St Helier | 29.64 |
| St Brelade | 5.40 | St John | 12.85 |
| St Clement | 6.22 | St Lawrence | 9.91 |
| St Martin | 10.16 | St Mary | 19.57 |
| St Ouen | 9.72 | St Peter | 9.29 |
| St Saviour | 6.00 | Trinity | 15.34 |

St Helier is the direct Census control; the other parish no-car values are
explicit residual/proxy allocations. Employment is age-conditioned rather
than uniform: 3,547 synthetic workers are aged 65+ (3,547 of 11,094 aged
65–74, or approximately 31.96%; none are assigned at 75+), versus 8,295 in
the pre-C1 audit. The age weights are structural assumptions because no
compatible official age-by-employment headcount was available.

Mapped sector×sex controls reconcile with zero mapping error. For example,
Construction is 6,083 male / 455 female, Transport/storage is 1,513 / 384,
and Education/health/other is 4,758 / 10,902; these remain visibly
sex-skewed rather than converging to 50/50.

Worker and workplace universes are explicit: 58,045 resident workers,
58,045 primary jobs, 4,063 secondary jobs, 62,108 filled assignments,
55,370 private-sector assignments, 6,738 synthetic non-private assignments,
8,500 private undertakings and 270 synthetic non-private institutional
workplaces. Institutional staff roles are overlay memberships; M3 job counts
are unchanged and no person receives a duplicate job.

The full workplace tail is 8,770 workplaces: 5,020 single-person, 7,590
under 10, 990 with 10–49 and 190 with 50+ jobs. Median/p90/p95/p99/max are
1/12/25/151/173; the 50+ mean is 150.48 with a 132–173 range. The 50+
workplaces contain 28,591 jobs (46.0%); top-1% and top-5% shares are 22.37%
and 56.83%, with Gini 0.762. The previous approximately 179–180-job
plateau is gone. These are structural synthetic tails, not observed employer
sizes.

Semi-urban destination parishes are St Clement and St Saviour; St Brelade is
not semi-urban. Workplace destinations are St Helier 65.78%, semi-urban
13.09% and rural 21.13%. Institutional staff endpoints are 1,972 school and
448 care; all 2,420 have a compatible primary institutional commute, with zero
incompatible primary records and zero WFH conflicts. Starsim/JOS UID, age,
sex and index checks are all zero mismatches.

## C2 network evidence summary

Before C2, school cross/core and workplace transient/team intersections were
18,784 and 19,318 pairs. After class/core exclusions both are zero. The route
overlap matrix now classifies each route pair as `FORBIDDEN`,
`ALLOWED_DISTINCT_SETTING`, `EXPECTED/NESTED_EXCLUDED` or `DIAGNOSTIC_ONLY`.
Distinct-setting overlaps remain diagnosable; they are separate exposure
opportunities, not duplicate storage of one encounter.

The full corrected route edge counts are:

| Route | Edges |
|---|---:|
| household | 98,052 |
| school_class | 190,293 |
| school_cross_class | 29,345 |
| workplace_team | 147,721 |
| workplace_transient | 96,742 |
| care_resident | 3,336 |
| care_staff | 3,164 |
| shared_vehicle | 3,177 |
| bus | 16,901 |
| community_indoor | 192,631 |
| community_outdoor | 74,688 |

The shared-vehicle route now contains 2,944 drivers with passengers, 3,104
passengers and 2,944 synthetic vehicles; 21,930 car-alone commuters remain
unmatched and are not silently treated as shared rides. Occupancies are 2:
2,798 vehicles, 3: 132, and 4: 14. No non-household carpools are inferred.

Community mixing has nonzero child–adult edges (39,467 indoor and 15,365
outdoor) and adult–older edges (30,856 indoor and 11,793 outdoor). The
regular-contact plus refreshed-contact design gives mean cross-day Jaccards
of approximately 0.517 indoor and 0.361 outdoor. Both the age matrix and
persistence values are structural assumptions, not Jersey contact-diary
measurements.

The common school calendar is based on the frozen official reference-year
term/holiday evidence. It suppresses weekends and official breaks and enables
representative term weekdays; institution-specific inset days are not
modelled. Route attribution uses the successful multi-route hazard mixture,
with a stable target/timestep draw independent of route insertion order.

## C3 implementation and C4 correction

C3 keeps M5 latent events immutable and adds:

- separate infection, generic symptom-onset, detection/testing and report
  dates, with a full latent horizon plus explicit/derived delay tail;
- separate observation schedules and a post-processing `DetectionEvent`
  structure, subsequently made runtime-causal by C4 without isolation or
  interventions;
- observation RNG keyed by latent replicate seed, observation seed,
  configuration identity and stable event identity;
- explicit ensemble date grids, subsequently corrected by C4 to use incidence,
  cumulative and state/prevalence semantics with truthful failed-replicate
  records;
- memory-aware process-worker bounds, subsequently corrected by C4 to
  distinguish requested, planned and actual workers after fallback;
- synthetic train/held-out beta recovery, reporting-delay recovery and
  ascertainment/route-weight sensitivity diagnostics;
- content-addressed observation, ensemble and calibration artifacts; and
- a clean-worktree, parent-hash-checked verification archive.

The final retained archive was verified with logical hash
`32627c432c65e89250ee40d68a9382bb9b463f5076015dd6be5e62acab70bba4` and
recorded the current Git commit, parent logical hashes, source-manifest hash,
command results and benchmark metadata.

The C3 sub-gates remain PASS for observation horizon and latent-incidence
conservation; infection/symptom/detection/report chronology;
replicate/configuration RNG separation; matched-seed diagnostics; memory-safe
process planning; synthetic beta recovery and confounding profiles; indexed
observation aggregation; immutable archive integrity; and M5/M6 forward
compatibility. C4 supplies the later runtime-causality and metric-grid
corrections rather than retroactively describing C3's post-processing objects
as runtime-causal.

## C4 corrective verification

C4 samples each infection's observation schedule at event creation using the
stable replicate/configuration/event stream and queues detected events by
detection timestep. Starsim's daily order is disease-state progression,
network refresh, existing intervention step, disease transmission/imports,
detection delivery and then the read-only intervention consumer. M7 state or
contact changes can first affect the next timestep. C4 remains responsible
only for notification scheduling and delivery.

Offline observation artifacts call the same schedule implementation and fail
if an attached online schedule differs. The ensemble grid registry treats
incidence gaps as structural zeroes, carries cumulative values forward and
marks state/prevalence after actual evolution as outside the metric horizon.
Per-cell semantics and requested/successful/failed/contributing replicate
counts are retained; failed replicates never become zero observations.

The controlled cumulative counterexample now has median cumulative infections
`27.5 -> 27.5 -> 27.5`; attack rate also carries forward, incidence may become
zero, and prevalence has zero contributors outside its horizon. A controlled
process-pool failure records requested/planned/actual workers as `2/2/1` with
`execution_mode=sequential_fallback`. Configuring either community contact
component to zero produces zero edges for that component.

Fresh verification results were:

```text
9 targeted C4 tests passed in 6.29s
44 combined C2-C4/M5/M6 tests passed in 114.22s
89 full pytest tests passed in 113.85s
ruff check: passed
ruff format --check: passed (63 files already formatted)
targeted mypy: Success, no issues found in 14 source files
uv lock --check: passed (67 packages resolved)
git diff --check: passed
```

The fresh representative full-island path produced 104,540 agents and executed
all 11 route families through Starsim 3.5.2. Its hashes were M2
`bc1e30281edc211dd860cd515450029e2e549cf2b33297d679b9c4b6b975296a`, M3
`b445ee6eb8f366bd07157a1ca8d3f5757892609a5067bf33d5df061b86aad9b7`,
M4/C2 `6ef553d4c640baf0d441e57bcc70322aa622dd69c2429ab6a9d13843b274cfb6`,
M5 `4130f943eb2a2839caeaa083b9f19d21dcd86997234095d90ddf02bbdc79307c`,
observation `bfea37ddab85bd756ee186554d6f03abdb2b24c8a5d2d4b752b0a12add419af1`
and ensemble aggregation
`cecc9127508cb75292d9914502a6a7bd347842ecc799ea92569a6c46d5c871fb`.
The run recorded 19 latent events and 12 runtime-delivered detections with exact
online/offline agreement. Its cumulative tail was `19 -> 19 -> 19`; later
prevalence cells were `outside_metric_horizon` with zero contributors.

## Full-population verification

The regenerated full C2/C3 network has 104,540 agents, 522,388 structural
edges, 856,050 baseline edges and 1,906,144 selected snapshot edges. Network
construction took 73.38 seconds with measured peak RSS 921,583,616 bytes.
Compared with the prior C2 benchmark (62.11 seconds, 743,030,784 bytes), the
observed difference is +11.27 seconds (+18.15%) and +178,552,832 bytes
(+24.03%); route edge counts and logical content remained unchanged, so this
is recorded as benchmark variance rather than a structural regression.

A full 2-day generic M5 smoke run produced 19 events: 10 seeded and 9 local,
with 0 imports; runtime was 73.28 seconds and peak RSS 911,261,696 bytes.
A full Starsim 3.5.2 network-only run also executed successfully. M6 CI
observation and ensemble commands passed; the beta calibration CLI recovered
synthetic beta 0.08 with held-out objective 0.

Verification commands completed:

```text
23 focused C3/M6 tests passed in 51.81s
80 full pytest tests passed in 101.57s
ruff check: passed
ruff format --check: passed (53 files already formatted)
targeted mypy: Success, no issues found in 6 source files
uv lock --check: passed
git diff --check: passed
compileall: passed
verification archive check: passed
```

## C5 — M7 intervention integrity and provenance correction

C5 closes the independent post-M7 audit blockers without opening M8. The
canonical horizon is a count of dated output points. Empty and neutral managers
reuse exact network-refresh arrays, touched-route modifiers are reduced in
canonical ID/version order, vaccination acceptance is stable per
seed/campaign/agent, import pressure is attempts followed by acquisition, and
care eligibility is an explicit two-class allow-list.

The C5 test suite contains adversarial nonzero-beta comparisons for every core
neutral family and the retained experimental optional paths. Baseline and
neutral runs have identical infections, dates, infectors, routes, successful
candidate hazard evidence, daily epidemic/route/age/parish rows, latent-outcome
hash and latent logical hash. The empty scenario genuinely attaches an
`InterventionManager`; all of its route rows report `canonical_reused`.

The stable latent-outcome hash covers exactly `daily_epidemic`, `daily_route`,
`daily_age`, `daily_parish` and `transmission_events`. Scenario/run hashes bind
the complete `OutbreakRunConfig`, M2/M3/M4 parents, disease and observation
configs, interventions, sensitivity IDs, seed/dates and Starsim/JOS versions.
M7 manifest schema 2.0 directly embeds a complete M5 latent bundle and rejects
missing, stale or hash-mismatched content.

The bounded CI sensitivity demonstration is tracked at
`configs/sensitivity/m7_community_exposure_demo.json`. With beta 0.35, seed 123
and eight dated points, community-indoor multipliers 0.7 and 1.0 produced 638
and 708 cumulative infections. Their scenario hashes are
`f9392b4ffc1f09cae7af324bf8769df0ac96953a9295c8eede0cd932803c2a30` and
`76d3a5e8916490935a4f2f9baa30ca22fef0422e5994771fff00fe74b09c30ed`.

The 104,540-agent four-point profile retained M2/M3/M4 hashes
`bc1e30281edc211dd860cd515450029e2e549cf2b33297d679b9c4b6b975296a`,
`b445ee6eb8f366bd07157a1ca8d3f5757892609a5067bf33d5df061b86aad9b7`
and `6ef553d4c640baf0d441e57bcc70322aa622dd69c2429ab6a9d13843b274cfb6`.
Baseline, neutral attached manager and community-indoor 0.5 runs took 29.41,
45.83 and 51.29 seconds. Neutral events and daily rows were exact and shared
latent-outcome hash
`402df7ada8e512199d38690e1be12bdacf7ddf40b8db870e19aad57adb7fadee`.
The targeted run touched exactly four indoor-route/date rows and had latent hash
`39d45e8cbb9be85eb006282ea51844b7dc46749c4d9f6a8a895b587ec815bc6e`.
Neutral and targeted overheads were 55.82% and 74.41%; this is a measured
remaining performance limitation, not a correctness blocker under C5.

Verification on the pre-commit worktree completed with the full pytest suite,
Ruff, format check, targeted mypy across 18 CI and M5–M7/ensemble source files,
`uv lock --check`, `git diff --check` and compileall. Clean-commit artifact
identity and verification hashes are recorded in the final C5 handoff.
The final suite result was 120 passed with one expected Starsim warning for the
deliberate one-point C1 compatibility fixture.

| C5 sub-gate | Status |
|---|---|
| 1. nonzero-beta empty-manager equivalence | PASS |
| 2. neutral isolation equivalence | PASS |
| 3. neutral quarantine equivalence | PASS |
| 4. neutral school equivalence | PASS |
| 5. neutral WFH equivalence | PASS |
| 6. neutral community equivalence | PASS |
| 7. neutral care equivalence | PASS |
| 8. neutral vaccination equivalence | PASS |
| 9. neutral optional equivalence where retained | PASS / experimental-deferred |
| 10. canonical modifier composition | PASS |
| 11. simulation/calendar end semantics | PASS |
| 12. care target correctness | PASS |
| 13. isolation state/event metrics | PASS |
| 14. quarantine state/event metrics | PASS |
| 15. school state metrics | PASS |
| 16. WFH transition/state metrics | PASS |
| 17. community metric semantics | PASS |
| 18. care state metrics | PASS |
| 19. vaccination administration/protection metrics | PASS |
| 20. stable vaccine uptake semantics | PASS |
| 21. import exposure/acquisition semantics | PASS |
| 22. WFH multi-job semantics | PASS |
| 23. scenario/run hashing completeness | PASS |
| 24. latent outcome hash | PASS |
| 25. complete/reconstructible M7 artifacts | PASS |
| 26. matched-seed comparison | PASS |
| 27. intervention ensemble metrics | PASS |
| 28. sensitivity auditability | PASS |
| 29. performance overhead | PASS with measured limitation |
| 30. C1–C4 regression compatibility | PASS |
| 31. test quality | PASS |
| 32. documentation accuracy | PASS |

**C5 overall: PASS.** M7 is restored to PASS subject to the documented
synthetic-claim boundary. Masking and gathering reduction remain experimental,
and M8 remains closed.

## M7 intervention verification (superseded by C5)

The original M7 PASS record below is retained as historical evidence but was
invalidated by the independent post-M7 audit. C5 is the authoritative current
gate record; the old baseline-equivalence, provenance and metric claims must not
be read as current.

M7 adds a single typed `InterventionManager` with immutable M4 snapshot
refresh, multiplicative route effects and explicit state/event/provenance
records. The supported families are case isolation, household quarantine,
school closure, workplace/commute reduction with WFH scheduling, community
indoor/outdoor reduction, care-home protection, vaccination, masking and
gathering reduction. A C4 detection delivered on timestep `t` can first affect
M5 transmission on `t+1`; overlapping detection-triggered states release by
the maximum active-until time. Care roster edges are retained with effective
beta zero when protected, and the generated M4 logical hash remains unchanged.

M7 writes content-addressed state, event, route-effect, scenario, diagnostics
and manifest artifacts. Matched comparisons retain cumulative/peak health
outcomes separately from agent-day, household/settings-day and vaccine-dose
burden, and route shares are paired with absolute counts. The bounded M6
ensemble path carries explicit scenario/config hashes and intervention state
metrics. The focused M7 contract suite covers lifecycle validation, neutral
equivalence, next-timestep causality, calendar families, WFH suppression,
vaccination delay, care topology and artifact outputs.

The bounded full-population smoke used 104,540 synthetic agents and two daily
steps on M4 hash
`6ef553d4c640baf0d441e57bcc70322aa622dd69c2429ab6a9d13843b274cfb6`. The
baseline ran in 51.52 seconds with 19 transmission events; the representative
community-indoor intervention ran in 94.36 seconds with 19 events, preserved
the M4 hash and produced 33 effective-route rows. The measured intervention
overhead was 42.84 seconds for this bounded run; this is reported as a
benchmark, not treated as a model-validity result. A bounded CI sensitivity
pair for WFH plus community reduction produced indoor multipliers 0.5 and 0.9,
scenario hashes
`ef16e2eab93aa47bfccaf68e6f6b9ccb558e48e497a8db3ca49ad03866dcb8d1` and
`f48caffaba743f9a94c6056cd7d9ac4ff4a2043f68aa88a21de4b7475511fb36`, and
cumulative totals 20 and 23; both retained M4 immutability.

### M7 gate report

| Gate | Status | Evidence |
|---|---|---|
| Intervention architecture | PASS | One typed manager, strict scenario/intervention hashes and shared lifecycle |
| Lifecycle / no retrocausality | PASS | C4 detection delivery; effect is `t+1` plus declared delay |
| Case isolation | PASS | Detection, adherence, duration, release and route controls |
| Household quarantine | PASS | Corrected private-household membership; communal residents skipped |
| School closure/reduction | PASS | Calendar-aware class/cross-class route modifiers and targeting |
| WFH/workplace reduction | PASS | Worker/sector/workplace targeting, WFH schedules, workplace/commute routes |
| Community reduction | PASS | Independent indoor/outdoor route multipliers |
| Care-home protection | PASS | Resident/staff/setting targeting; care roster edges retained |
| Vaccination | PASS | Rollout, uptake, delay, susceptibility/infectiousness efficacy and waning |
| Optional masking/gathering | PASS | Generic route-multiplier families use the shared framework |
| Composition | PASS | Active multipliers are multiplied and clipped to `[0, 1]` |
| Baseline equivalence | PASS | Neutral route and disease-state contract tests |
| Matched-seed comparison | PASS | Same-seed baseline/scenario pairing with coupling caveat |
| Intervention ensembles | PASS | M6 bounded worker planner and explicit replicate records |
| Metric-aware aggregation | PASS | Intervention state registered as state metrics |
| Route-shift analysis | PASS | Absolute route counts and relative shares are both emitted |
| Sensitivity framework | PASS | Named IDs/axes plus bounded CI community-intensity demonstration |
| Provenance/manifests | PASS | M2/M3/M4/M5/C4/config/git/output hashes are retained |
| Intervention event logging | PASS | State transitions, triggers and provenance hashes are emitted |
| Deterministic regeneration | PASS | Stable seeded draws and content-addressed outputs |
| Full-population compatibility | PASS | 104,540-agent two-day baseline/intervention smoke |
| Performance | PASS | Bounded overhead measured and recorded above |
| C1–C4 regression | PASS | Full repository suite passed after M7 integration |
| Travel controls | PASS / DEFERRED | No travel/import/visitor controls added; boundary is M8 |

Travel, airport, ferry, arrival and visitor controls remain deliberately
deferred to M8; API and UI are also outside this milestone.

## Known limitations and boundary

All residents, staff, schools, workplaces, care rosters, carpools and
community contacts remain synthetic. Official school staffing evidence is FTE
capacity, not a whole-island headcount or roster; Care Commission values are
regulatory minima, not observed staffing. Contact weights remain relative
daily exposure-opportunity weights and are not separately identified from
disease transmissibility. Beta recovery is a synthetic demonstration, not
Jersey surveillance calibration. M7 and M8 intervention/travel values are
synthetic assumptions; real-disease validation and API/UI remain out of scope.
M8 visitor counts and seasonality are scenario controls, not tourism or
border-control estimates.

## Milestone 8 / M8.1 corrective record

M8 was initially implemented at `5768398760d9822ca3e875367dcbd9a42d8c174d`.
An independent audit then marked M8 **FAIL**: reusable Starsim slots could
relabel historical visitor events, annual streams and seasonality did not
reconcile, M7 could reintroduce absent residents, temporary networks/configs
were not reconstructible, and testing/quarantine/contact boundary semantics
were not causal. That failed audit is retained as project history.

M8.1 on `codex/m8.1-travel-integrity` is the bounded corrective milestone. It
uses interval-aware `(slot UID, timestep)` episode identity; complete temporary
slot demographic/disease/modifier reset; exact largest-remainder annual
apportionment; person-movement traveller categories; day-weighted seasonality;
presence-valid resident route views consumed by M7; edge-local/directional
travel effects; explicit test/result/quarantine phases; exact sparse temporary
edge persistence; and logical artifact verification. No M9 API/job or M10 UI
work is included.

The frozen travel evidence currently available is the annual 2025 Ports of
Jersey passenger-arrival table (`passenger_arrivals_total_csv`): 720,842
airport and 196,623 sea/ferry passenger arrivals. No frozen monthly visitor
profile was available, so demo seasonality is a bounded `scenario_assumption`;
annual-to-daily scheduling is explicitly `derived`. At `stream_scale < 1`,
simulated movements are a computational sample and epidemic outcomes are not
inflated back to source scale. Composition, average stay,
party size, transport, community participation, arrival disease state and
external acquisition controls are exposed as provenance-bound assumptions.

The source-scale gate is generation/capacity only. Literal full-year
source-scale disease execution remains unbenchmarked; the materialized episode
runner rejects unnecessarily large horizons and directs callers to the
constant-memory generation benchmark. Monthly tourism seasonality, detailed
taxi/rental behaviour and traveller biological values remain structural
assumptions, not verified Jersey behaviour.

### M8.1 corrective verification — 28 August 2026

The corrective suite completed with 139 tests passing (one pre-existing
single-date Starsim warning), including 19 focused M8/M8.1 tests. Ruff check,
Ruff format check, targeted mypy across six changed runtime/schema/artifact
files, `uv lock --check`, `compileall` and `git diff --check` passed.

The literal 2025 source-scale generation/capacity gate reconciled exactly:
720,842 air plus 196,623 ferry equals 917,465 passenger movements, tolerance
zero. It generated an annual mean 2,513.60 and peak 2,514 movements/day,
91,747 returning-resident movements (realized fraction 0.100000545 within the
declared 0.5/N tolerance), peak concurrent visitors 6,336 and 6,970 slots with
headroom. The constant-memory calculation took 0.0039 seconds in the measured
process; its process peak RSS was 277,430,272 bytes with zero incremental
high-water increase. The first seven-day source-scale window contained 17,598
movements and the same 6,336 concurrency peak under the declared synthetic
stay contract.

The full-island seven-day scaled-travel smoke passed with 104,540 residents,
19 visitor episodes, two returning-resident episodes, visitor capacity 9,
peak active visitors 8 and 11 slot reuses. It recorded 21 arrivals and 11
visitor departures. Exact temporary edges were: terminal 160, party 11,
accommodation 2, host household 4, transit 6, indoor community 147 and outdoor
community 106. The representative run had no visitor-linked disease event;
the separate controlled fixture produced and validated all four transmission
directions with candidate-hazard and immutable event-time identities across
slot reuse. Epidemic runtime was 174.38 seconds and peak RSS 1,240,104,960
bytes. Its temporary-network hash was
`776708a76860f840b9056d533e3471cb9739e759693607dba51e30a48db11f02`.

A full two-day resident C5 baseline ran in 14.47 seconds; the explicit
zero-travel manager path ran in 67.13 seconds and produced the exact same C5
latent hash,
`7e9d0188f6d364a6b23dec2dd13938e31c118554b7609b656a55b934fdab585b`.
The zero-travel artifact passed logical verification. A bounded paired
comparison emitted 44 metric rows; a two-seed ensemble emitted 52 semantic
summary rows with zero failed replicates. The executable valid sensitivity
axis (`visitor_community_contacts` 1/3/6) produced 268/513/1,138 temporary
edges and distinct latent hashes.

The independent M8.1 audit subsequently passed 57 of 60 gates but marked
**M8.1 FAIL — M8 REMAINS CLOSED**. It found three blockers: temporary-traveller
observation rows and `DetectionEvent` objects dropped trip/party/episode
identity; an arrival-test result due after visitor departure could be processed
against a reused runtime slot; and combined M7/M8 intervention events could not
be written when `new_state` mixed scalar and structured values. The earlier
M8.1 PASS claim is therefore preserved above only as superseded implementation
history, not as a valid audit conclusion.

### M8.2 final travel closure — 28 August 2026

M8.2 is a minimal correction for those three findings. The observation
scheduler now copies visitor, actor, runtime slot, trip, travel party and
episode hash directly from the latent infection event into the observation row
and immutable `DetectionEvent`; equivalent infector context is retained when
present. Travel artifacts persist both observation and detection tables with
the same episode identity. Permanent-resident scheduling remains compatible.

Arrival-test work items now bind administration/result timesteps, actor,
runtime UID, trip, party and episode hash. At result availability, actionability
is computed from that episode and its active interval. An old positive result
after visitor departure is retained as
`test_result_available_after_departure` with `actionable=false`; it cannot
detect, quarantine, isolate or alter a replacement visitor. Returning-resident
results remain actionable against the permanent resident identity. Deferred
quarantine activation is also rejected after the originating visitor departs.

`travel_intervention_events.parquet` now has an explicit Arrow schema.
Heterogeneous `previous_state` and `new_state` values are stored as canonical
JSON strings in `previous_state_json` and `new_state_json`, preserving JSON
bool/dict/string/number/null types on reconstruction. Verification deserializes
those values before recomputing the existing latent logical hash, so scientific
state tampering still fails even after raw checksum and size metadata are
updated. Direct non-M7 runs continue to persist a legitimate null
`scenario_config.json`; applicable combined M7/M8 runs persist non-null
scenario, M7 and observation identities.

Fresh M8.2 verification completed as follows:

```text
6 focused M8.2 tests passed in 11.23s
25 combined M8/M8.1/M8.2 tests passed in 39.07s
72 exposed C4/M7/M8 regression tests passed in 118.53s
145 full pytest tests passed in 225.16s (one pre-existing single-date warning)
ruff check: passed
ruff format --check: passed (77 files already formatted)
targeted mypy --ignore-missing-imports: Success, no issues found in 4 source files
uv lock --check: passed (67 packages resolved)
compileall: passed
git diff --check: passed
```

**M8.2 corrective status: PASS. M8 status: PASS with the previously recorded
non-blocking performance/realism warnings.** Monthly tourism seasonality is not
source-backed; detailed taxi/rental behaviour and travel biology remain
structural assumptions; literal annual source-scale disease execution was not
attempted; and the explicit zero-travel manager retains measured overhead.
M9 implementation is complete at the application boundary and M10 remains
closed. M9 adds a loopback-only FastAPI `/api/v1` contract, persistent SQLite
schema version 1, FIFO scheduling with default API concurrency one, isolated
worker subprocesses, cancellation, restart reconciliation, append-only job
events, verified M5–M8 artifact discovery, bounded manifest-driven Parquet
queries, and an application result manifest. Scientific engine modules and
scientific artifact semantics are unchanged. See [`api.md`](api.md) for the
runtime contract and limitations; final gate evidence is recorded with the
M9 verification result.

## M9 verification evidence

The implementation-time evidence in this section is historical. A subsequent
independent adversarial audit reproduced three blockers and returned
**M9 FAIL — M10 REMAINS CLOSED**: in-memory artifact references could be
trusted at normal completion, restart used a weaker success path, and M5/M6
verification did not rederive scientific identities from persisted content.
M9.1 below is the bounded correction of that audit result.

The focused M9 suite passed 7 tests in 11.62s, covering the registry state
machine, concurrent claiming, request/idempotency persistence, API contract and
CORS, bounded dataset reads and traversal rejection, direct/API equivalence,
running cancellation, and isolated worker failure. The complete repository
suite passed 152 tests in 234.87s with only the existing Starlette/httpx
deprecation and single-date Starsim timestep warnings. Ruff check, formatting,
targeted mypy, `uv lock --check`, compileall, and `git diff --check` passed.

### M9.1 corrective integrity architecture

M9.1 closes the independent M9 audit's successful-finalization and scientific
verification blockers without changing M5--M8 scientific behavior. A worker
now persists only `result_candidate.json` role/path locators. One fail-closed
finalizer reloads `request.json`, recomputes its hash, enforces exact artifact
roles and types for each job kind, checks worker and artifact Git provenance,
rederives scientific identities from persisted content, reconstructs and
rereads `result_manifest.json`, and calls the registry's sole successful
terminal operation. Artifact publication, `artifact_written`,
`artifact_verified`, `job_completed`, PID clearing, and `SUCCEEDED` commit in
one SQLite transaction. Restart reconciliation invokes the same finalizer;
unverifiable active jobs become `INTERRUPTED`.

M5 and M6 writers and verifiers share canonical identity functions. The M5
verifier rebuilds parameter/run identities and table-derived latent, logical,
and bundle hashes. The M6 verifier rebuilds ensemble/comparison logical hashes,
replicate identities and counts, metric-aware persisted values, configuration
links, and request-bound disease parameters. Existing M7/M8 verifiers remain
in the same fixed dispatch, with M7 additionally verifying its contained M5
bundle. The API now exposes typed response models, a catalogue-derived dataset
list, explicit loopback-only CORS origins, and Arrow predicate/projection
pushdown with bounded page materialization.

The corrective suite adds 24 direct M9.1 tests. It covers the closed success
transition, transaction rollback, normal/restart idempotence, incomplete and
wrong-role candidates, wrong artifact type, request mismatch, candidate and
scientific provenance mismatch, result-manifest write failure, M5/M6 logical
tampering with attacker-updated raw checksums, bounded 50,000-row projection
and filtering, wildcard/non-loopback CORS rejection, and controlled POSIX child
process cleanup. Real worker smokes pass for M5, M7, M8, M6 ensemble, and M6
matched comparison. Direct/worker M5 equivalence covers scenario, latent and
bundle identities plus exact epidemic, parish, route, age, and canonical event
tables. The strengthened verifier independently reproduces the previously
recorded full-island M5 latent/bundle hashes and clean M7
scenario/latent/bundle hashes. The complete repository suite passes 176 tests
in 134.41s. An archived required-base checkout and the corrected branch
produced identical M5 latent/logical/bundle, two M6 ensemble, and M6 comparison
identities for the same deterministic inputs. Ruff, formatting, targeted mypy (nine application files),
`uv lock --check`, compileall, CLI help smokes, and `git diff --check` pass.

The independent full-island timing decomposition remains the performance
baseline: queue about 0.06s; worker startup/validation 4.39s; M2 construction
217.75s; M3 construction 276.20s; M4 construction 67.05s; parent load/other
about 18s; M5 simulation 17.29s; artifact writing 0.19s; verification 0.01s;
and M9 finalization under 0.01s. M9 orchestration is not the ten-minute
bottleneck. Reuse of verified M2--M4 parents is an explicit post-M9/pre-M10
performance item and is not implemented in M9.1.

**Historical M9.1 implementation status: PASS.** The three independently
reproduced M9 blockers were closed by the implementation, before the later
independent audit recorded below; M10 remains closed.

The required API full-island smoke submitted one `scenario_run` at `full`
scale (104,540 residents), seed 123, one dated output point. Job
`b5832a52-fa04-4fd0-a4ca-9f91fb4bd855` reached `SUCCEEDED` after 601.4s; its
M5 runner reported 17.29s, 11 routes, latent hash
`23ddd5d0ea47943ebb4d2b50facfaf74bc03d056083cd5f9d298ead1480e2e54`, bundle
hash `9316b3727ebb9b89e800203c16d30cc8812a3f5feef49e77c5f9b7dd8c2797f5`, and
M9 result-manifest hash
`d0569cccbc96f7d98e3f9d5c5f6800f55cba4e960094acfcd7397585407bf1d4`.
Artifact verification passed and `daily_epidemic` was discoverable/readable;
the pre-commit run necessarily recorded `dirty_worktree_flag: true`.

Additional runtime smokes showed one-running/two-queued FIFO behavior at API
concurrency 1, real process-group cancellation with no verified artifact, and
a persisted `FAILED` worker integrity error while the API remained healthy.

### Independent M9.1 audit and M9.2 provenance correction

The M9.1 implementation evidence above is retained as history. A later
independent adversarial audit confirmed the missing/incomplete-artifact and
M5/M6 content-verification blockers closed, but reproduced one remaining
restart defect: coordinated false commit/dirty values in mutable request
metadata, the candidate, and scientific manifests could agree with one another,
reach `SUCCEEDED`, and overwrite SQLite provenance. The independent result was
therefore **M9.1 FAIL — M10 REMAINS CLOSED**.

M9.2 is the minimal correction for that single defect. SQLite schema version 2
persists submission-time commit/dirty values atomically with the job and worker
commit/dirty observations through a conditional write-once operation. The
canonical application request hash now includes submission identity; scientific
scenario-hash semantics are unchanged. The strict live/restart finalizer treats
the two registry identities as authority, requires them to agree with each
other and with candidate, scientific artifact, and result-manifest evidence,
and no longer accepts provenance fields during success publication. Historical
v1 rows retain their state and old evidence while the new fields remain null;
stale active jobs with incomplete anchors cannot succeed.

The focused M9.2 suite passes 15 tests covering atomic submission persistence,
hash binding, immutable generic updates, concurrent write-once observations,
commit and dirty mismatches before scientific execution, coordinated false
commit/dirty restart substitution, independent candidate/artifact binding,
result-manifest binding after coordinated hash replacement, valid and
incomplete restart paths, immutable success publication, and v1-to-v2/fresh/
future-schema behavior. The combined M9/M9.1/M9.2 suite passes 46 tests, and
the complete repository suite passes 191 tests in 147.09s with only the
pre-existing Starlette/httpx and single-date Starsim warnings. Final toolchain
and clean-commit smoke evidence is recorded with the M9.2 completion report.

**M9.2 corrective implementation status: PASS.** The immutable restart
provenance blocker is closed and functional M9 verification passes. Final
independent evidence/documentation closure remains in progress; M10 remains
closed.
