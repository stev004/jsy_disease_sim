# Jersey Outbreak Simulator progress ledger

**Last verified:** 27 August 2026
**Current branch:** `codex/m7-interventions`
**C3 verification commit:** `658364c7f02cf44f9392116e7db44c94bdb3175a`
**Scope:** M7 intervention framework and matched-seed experiment gate.

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

## Milestone 8 implementation record

M8 is implemented on branch `codex/m8-visitors-seasonality` from the required
M7/C5 parent. The typed `travel_schemas.py`, lifecycle/network runner
`travel.py` and `travel_artifacts.py` use preallocated temporary Starsim slots
because Starsim 3.5.2 population growth is append-only. Canonical M2/M3/M4
inputs remain immutable. `jos travel run`, `jos travel compare` and
`jos travel ensemble` provide the minimal configuration-first command surface.

The frozen travel evidence currently available is the annual 2025 Ports of
Jersey passenger-arrival table (`passenger_arrivals_total_csv`): 720,842
airport and 196,623 sea/ferry passenger arrivals. No frozen monthly visitor
profile was available, so demo seasonality is a bounded `scenario_assumption`;
annual-to-daily scheduling is explicitly `derived`. Composition, average stay,
party size, transport, community participation, arrival disease state and
external acquisition controls are exposed as provenance-bound assumptions.

### M8 gate ledger

| # | Gate | Status | Evidence / limitation |
|---:|---|---|---|
| 1 | Resident baseline exact compatibility | PASS | Full repository regression and zero-arrival resident-output equivalence |
| 2 | Visitor identity contract | PASS | Separate deterministic visitor namespace; no resident ID collisions |
| 3 | Trip episode model | PASS | Typed person/trip/party episode records with provenance |
| 4 | Arrival/departure generation | PASS | Deterministic dated lifecycle, day and overnight semantics |
| 5 | Air/ferry separation | PASS | Independent mode-keyed streams and terminal identity |
| 6 | Travel parties | PASS | Deterministic party sizes, party IDs and member mapping |
| 7 | Accommodation assignment | PASS | Hotel/guesthouse/self-catered typed accommodation records |
| 8 | Host-household visitors | PASS | Resident household hosting with household route membership |
| 9 | Terminal contacts | PASS | Airport/ferry terminal route family with arrival-day contacts |
| 10 | Visitor local transport | PASS | Bus, taxi, rental, walking and host-pickup categories |
| 11 | Visitor community mixing | PASS | Parish-aware indoor/outdoor temporary community routes |
| 12 | Returning-resident absence | PASS | Resident IDs retained and removed from Jersey routes while away |
| 13 | External travel acquisition | PASS | Return events can acquire `travel_imported` infection distinctly |
| 14 | Visitor disease-state initialization | PASS | Susceptible/exposed/infectious/recovered arrival states |
| 15 | Temporary-agent/Starsim architecture | PASS | Preallocated slots; no unsafe mid-run population growth |
| 16 | Activation/deactivation | PASS | Alive-state, active-UID and route lifecycle transitions |
| 17 | Resident vs present-population denominators | PASS | Resident-present and total-present denominators are separate |
| 18 | Visitor transmission directionality | PASS | Resident/visitor direction and visitor-linked events persisted |
| 19 | Generic-import vs explicit-travel separation | PASS | `generic_import_only`, `explicit_travel` and `both` are explicit |
| 20 | Visitor seasonality | PASS | Typed normalized monthly visitor profile, neutral by default |
| 21 | Transmission/contact seasonality | PASS | Optional separate typed profile applied once and persisted |
| 22 | High-risk targeting/strata | PARTIAL | Older/care/care-staff/occupational targeting exists; severity deferred |
| 23 | Arrival-volume intervention | PASS | Prospective arrival multiplier |
| 24 | Arrival testing | PASS | Probability, sensitivity, specificity and delay are deterministic |
| 25 | Traveller quarantine | PASS | Positive-only/all-arrival modes, adherence and duration controls |
| 26 | M7/M8 intervention composition | PASS | Shared M7 intervention manager composes with visitor slots |
| 27 | Travel intervention neutrality | PASS | Zero/neutral controls preserve resident-only behavior |
| 28 | Resident-network immutability | PASS | M2/M3/M4 inputs and parent hash remain unchanged |
| 29 | Route attribution | PASS | Route IDs, event direction and local-acquisition attribution |
| 30 | Disease-state conservation | PASS | Daily state counts conserve present population |
| 31 | Scenario/run hashing | PASS | Scenario identity binds material parent and travel controls |
| 32 | Visitor/travel hashes | PASS | Config, episode, population, network and seasonality hashes |
| 33 | Reconstructible M8 artifacts | PASS | Schema-2.0 manifest, required tables, hashes and verifier |
| 34 | Matched-seed comparison | PASS | CLI/library comparison with parent and coupling diagnostics |
| 35 | Travel ensembles | PASS | Multi-seed summary preserves state/incidence semantics |
| 36 | Sensitivity auditability | PASS | Bounded visitor-contact sensitivity config and provenance table |
| 37 | Limiting cases | PASS | Zero arrivals, departure cleanup, returning-resident and tamper tests |
| 38 | Performance | PASS | Runtime and peak memory recorded in final full artifact |
| 39 | Visitor capacity safety | PASS | Peak concurrency, headroom and overflow guard |
| 40 | Full-island compatibility | PASS | Clean committed 104,540-resident run completed |
| 41 | Source/provenance discipline | PASS | Official annual arrivals plus explicit derived/assumption statuses |
| 42 | Test quality | PASS | 129 repository tests and 9 focused M8 tests pass |
| 43 | Documentation accuracy | PASS | README, architecture, scope and progress records updated |
| 44 | Synthetic scientific claims | PASS | Visitor outputs explicitly bounded synthetic scenarios |
| 45 | M9/API boundary preserved | PASS | No API, job system or M9 infrastructure added |
| 46 | M10/UI boundary preserved | PASS | No UI, map frontend or M10 work added |

Overall M8 status is **PASS with one accepted narrow PARTIAL**: high-risk
targeting/strata are implemented, while optional biological severity modifiers
remain intentionally deferred.
