# Jersey Outbreak Simulator progress ledger

**Last verified:** 27 August 2026
**Current branch:** `codex/c2-network-semantics`
**Current commit:** `658364c7f02cf44f9392116e7db44c94bdb3175a`
**Scope:** C3 only; M7 remains closed and no C4 or M7 implementation has begun.

This ledger records the current implementation and verification state. The
project charter remains the authoritative specification; this file records
which gates have actually passed and the evidence supporting them.

## Gate status

| Gate | Status | Verification boundary |
|---|---|---|
| M0 | PASS | Starsim 3.5.2 compatibility and deterministic demo |
| M1 | PASS | Registered Jersey sources, canonical tables and quality report |
| M2 | PASS | 104,540 synthetic residents; logical hash `bc1e30281edc211dd860cd515450029e2e549cf2b33297d679b9c4b6b975296a` |
| M3 | PASS | 104,540 residents, 48 schools, 703 classes, 58,045 primary jobs and 4,063 secondary jobs; logical hash `b445ee6eb8f366bd07157a1ca8d3f5757892609a5067bf33d5df061b86aad9b7` |
| M4.1 / C1 | PASS | Employment-universe, identity, staffing, geography and institutional-commute blockers closed in `1e501db41f9b0fbf5b3b5ebd57f550bc6dc0450f` |
| C2 | PASS | Nested-route, overlap-policy, shared-vehicle, age-mixing, persistence, calendar and attribution blockers closed in `4dade853dda9c9f7e63df3fc80df10297b41db06` |
| M5 | PASS | Generic respiratory SEIRS demonstration remains compatible with the corrected network |
| M6 / C3 | PASS | Observation, ensemble, calibration, process-safety and archive contracts verified at `658364c7f02cf44f9392116e7db44c94bdb3175a` |
| M7 | CLOSED | Interventions are intentionally not implemented |

The C3 implementation was committed in `0f6667791e481fd2ed5d389d2ea0cb05b8a0d7e9`;
the final integrity hardening is the current commit above. The worktree is
clean.

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

## C3 implementation and verification

C3 keeps M5 latent events immutable and adds:

- separate infection, generic symptom-onset, detection/testing and report
  dates, with a full latent horizon plus explicit/derived delay tail;
- a read-only `DetectionEvent` interface without isolation or interventions;
- observation RNG keyed by latent replicate seed, observation seed,
  configuration identity and stable event identity;
- complete ensemble date grids with explicit zeroes for missing values and
  truthful failed-replicate records;
- memory-aware process-worker bounds and diagnostics distinguishing requested
  from actual workers;
- synthetic train/held-out beta recovery, reporting-delay recovery and
  ascertainment/route-weight sensitivity diagnostics;
- content-addressed observation, ensemble and calibration artifacts; and
- a clean-worktree, parent-hash-checked verification archive.

The final retained archive was verified with logical hash
`32627c432c65e89250ee40d68a9382bb9b463f5076015dd6be5e62acab70bba4` and
recorded the current Git commit, parent logical hashes, source-manifest hash,
command results and benchmark metadata.

The C3 sub-gates are all PASS: observation horizon and latent-incidence
conservation; infection/symptom/detection/report chronology; causal detection
event exposure; replicate/configuration RNG separation; complete ensemble
date grids and failed-replicate semantics; truthful matched-seed diagnostics;
memory-safe process execution; synthetic beta recovery and confounding
profiles; indexed observation aggregation; immutable archive integrity; and
M5/M6 forward compatibility.

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

## Known limitations and boundary

All residents, staff, schools, workplaces, care rosters, carpools and
community contacts remain synthetic. Official school staffing evidence is FTE
capacity, not a whole-island headcount or roster; Care Commission values are
regulatory minima, not observed staffing. Contact weights remain relative
daily exposure-opportunity weights and are not separately identified from
disease transmissibility. Beta recovery is a synthetic demonstration, not
Jersey surveillance calibration. M7 interventions, C4 work, API/UI, visitors,
and real-disease validation remain out of scope.
