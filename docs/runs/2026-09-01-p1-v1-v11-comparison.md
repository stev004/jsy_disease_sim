# JOS V1.0 ↔ V1.1 full-scale baseline comparison

## Assumption regime

This comparison is primarily an **assumption-regime comparison**, not a contest between outcome magnitudes.

| Assumption | V1.0 | V1.1 |
|---|---|---|
| Synthetic residents | 104,540 | 104,540 |
| Horizon | 180 dated outputs, 2025-01-06–2025-07-04 | Same |
| Seed | 123; 10 initial infections | Same |
| Transmission beta | 0.08 | 0.08 |
| Latent / infectious duration | Constant 2 / 5 days | Constant 2 / 5 days; no non-zero CV claimed |
| Imports | 0 | 0 |
| Route multipliers | All 11 at 1.0 | Same |
| Generic immunity | Full protection for 30 days, then complete return to susceptibility | Persistent recovery; generic complete waning disabled |
| Immunity-duration field | Active | Retained as an inactive V1 comparator field |
| Disease configuration | `respiratory-demo-v0.1` | `respiratory-demo-v1.1` |
| Observation configuration | `observation-demo-v0.1` | `observation-demo-v1.1` |
| Intervention / travel | None | None |

The V1 recurrent waves, reinfections, and absence of extinction are direct consequences of repeatedly returning recovered synthetic residents to full susceptibility after 30 days. V1.1 removes that unsupported generic default, producing one established wave followed by susceptible depletion and extinction.

This is not a one-factor experiment. V1.1 also contains scientific, lifecycle, output, structure, and network hardening, with different M3/M4 artifact identities. Its manifest explicitly states that the same seed gives matched starts but does not guarantee common random numbers after event-path divergence. Accordingly, the broad trajectory change is attributable to disabled waning, while smaller peak and route-share differences cannot be assigned exclusively to that switch. In particular, the common 2025-02-03 incidence peak predates any V1 post-recovery waning return.

These are synthetic-scenario results from one stochastic realization. They are not forecasts, Jersey calibration, retrospective validation, or named-pathogen estimates.

## Evidence identity and verification

| Item | V1.0 | V1.1 |
|---|---|---|
| Commit | `9e9ce3abc4201cd8303c723015462d21ca237800` | `e3609ff288b33444456de960db9e7c6560d0b898` |
| M7 artifact | `jos-intervention-m7-full-seed-123-dd3664f67330` | `jos-intervention-m7-full-seed-123-f0b18d64a083` |
| Worktree provenance | Clean | Clean |
| Scientific verification | **PASS** | **PASS**, independently rechecked |
| Diagnostics | Passed | Passed |
| Interpretation | Frozen V1 evidence accepted by its allow-listed verifier | M7 and contained M5 hashes, identities, tables, conservation, and aggregations accepted |

## Headline metric comparison

| Metric | V1.0 | V1.1 | Delta | Interpretation |
|---|---:|---:|---:|---|
| Establishment | First local transmission 2025-01-08; established | First local transmission 2025-01-08; established | No date change | V1.1 did not undergo early fadeout. |
| Extinction | No extinction by day 180 | Last local infection 2025-03-20; E=I=0 on 2025-03-27 and thereafter | Extinction only in V1.1 | Persistent recovery closes the established wave once transmission chains end. |
| Peak daily local infections | 7,234 on 2025-02-03 | 7,048 on 2025-02-03 | −186 (−2.57%); same date | The similar pre-waning peak indicates broadly similar early-wave scale; its small difference reflects other hardening/path divergence. |
| Peak infectious prevalence | 28,479 (27.24%) on 2025-03-30 | 27,076 (25.90%) on 2025-02-09 | −1,403; −1.34 pp; 49 days earlier | V1’s horizon maximum occurs during later reinfection dynamics; V1.1’s maximum belongs to the first wave. |
| Total infection episodes, including seeds | 294,565 | 81,384 | −213,181 (−72.37%) | Removing repeated returns to susceptibility eliminates the recurrent-episode burden. |
| Episodes per resident | 2.818 | 0.778 | −2.039 | V1 exceeds one because it counts repeated episodes; V1.1 remains below one. |
| Unique ever infected | 99,041 | 81,384 | −17,657 (−17.83%) | V1 eventually reaches more identities through recurrent transmission; V1.1 stops with 23,156 never-infected synthetic residents. |
| Ever-infected fraction | 94.74% | 77.85% | −16.89 pp | V1.1’s wave ends before reaching the remaining susceptible population. |
| Episodes per ever-infected person | 2.974 | 1.000 | −1.974 | V1 reinfection is central; V1.1 has exactly one episode per infected person. |
| Imported episodes | 0 | 0 | 0 | Imports are disabled in both scenarios. |

V1.1 contains 81,374 local episodes and 10 seeded episodes. All 81,384 infected identities are unique, every natural-history episode index is zero, and no susceptibility-return date is populated.

## Route attribution

Shares use local infections as the denominator: 294,555 in V1 and 81,374 in V1.1. These are bookkeeping attributions over simulated pathways, not causal evidence about Jersey.

| Simulated pathway | V1 count | V1 share | V1.1 count | V1.1 share | Delta | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| household | 80,586 | 27.359% | 22,634 | 27.815% | +0.456 pp | Remains the largest pathway; modestly larger share in the single wave. |
| community_indoor | 65,464 | 22.225% | 18,792 | 23.093% | +0.869 pp | Modest share increase; still the second-largest pathway. |
| workplace_team | 58,410 | 19.830% | 16,236 | 19.952% | +0.122 pp | Essentially stable share across regimes. |
| school_class | 46,808 | 15.891% | 11,709 | 14.389% | −1.502 pp | Largest share shift, lower when attribution is confined to the terminating first wave. |
| workplace_transient | 17,254 | 5.858% | 4,836 | 5.943% | +0.085 pp | Essentially stable. |
| community_outdoor | 12,027 | 4.083% | 3,466 | 4.259% | +0.176 pp | Slightly larger share. |
| school_cross_class | 5,794 | 1.967% | 1,438 | 1.767% | −0.200 pp | Slightly smaller share. |
| bus | 3,679 | 1.249% | 982 | 1.207% | −0.042 pp | Essentially stable. |
| care_resident | 1,869 | 0.635% | 572 | 0.703% | +0.068 pp | Slightly larger share, still below 1%. |
| care_staff | 1,576 | 0.535% | 446 | 0.548% | +0.013 pp | Essentially stable. |
| shared_vehicle | 1,088 | 0.369% | 263 | 0.323% | −0.046 pp | Essentially stable and remains the smallest pathway. |

All 11 pathways remain nonzero and sum exactly to the respective local-event totals. Although absolute counts fall with total episodes, the attribution profile remains broadly coherent; the largest movement is school class at −1.50 percentage points.

## Realized generation interval

The V1 method was applied unchanged: each local event was linked to the recorded infector’s latest earlier persisted infection episode. All V1.1 local events resolved. With no V1.1 reinfection, each source identity has one unambiguous earlier episode.

| Statistic | V1.0 | V1.1 | Delta | Interpretation |
|---|---:|---:|---:|---|
| Local events, N | 294,555 | 81,374 | −213,181 | Fewer events reflect elimination of recurrent waves. |
| Mean | 3.652 d | 3.667 d | +0.015 d | Practically unchanged under the common 2-day/5-day constant-duration assumptions. |
| Median | 3 d | 3 d | 0 | Unchanged. |
| Sample SD | 1.384 d | 1.388 d | +0.004 d | Distributional spread is essentially unchanged. |
| IQR | 2–5 d | 2–5 d | 0 at both bounds | Unchanged. |
| Minimum | 2 d | 2 d | 0 | Consistent with the fixed latent duration. |
| Maximum | 6 d | 6 d | 0 | Unchanged upper bound. |

V1.1 counts by interval are 22,088 at 2 days, 18,798 at 3, 16,039 at 4, 13,033 at 5, and 11,416 at 6.

## Final compartment state at day 180

| Compartment | V1.0 | V1.1 | Delta | Interpretation |
|---|---:|---:|---:|---|
| Susceptible | 51,025 | 23,156 | −27,869 | V1 susceptible includes previously infected residents returned by waning; V1.1 susceptible corresponds to never-infected residents. |
| Exposed | 9,675 | 0 | −9,675 | V1 ends during active recurrence; V1.1 is extinct. |
| Infectious | 20,380 | 0 | −20,380 | V1 ends with 19.49% infectious; V1.1 has no active infection. |
| Recovered | 23,460 | 81,384 | +57,924 | Without waning, every V1.1 infected resident remains recovered at the horizon. |
| Total | 104,540 | 104,540 | 0 | Exact population conservation in both runs. |

## Runtime and memory

| Phase/resource | V1.0 | V1.1 | Delta | Interpretation |
|---|---:|---:|---:|---|
| M2 construction | 239.38 s | 215.17 s | −24.20 s (−10.1%) | Faster in the V1.1 execution. |
| M3 construction | 319.02 s | 275.09 s | −43.94 s (−13.8%) | Faster in the V1.1 execution. |
| Disease/observation/baseline runtime | 9,260.28 s | 11,899.19 s | +2,638.91 s (+28.5%) | V1.1’s hardened execution/output path took longer despite fewer episodes. |
| M4 plus writing/CLI residual | 134.64 s | 249.96 s | +115.32 s | V1.1 M4 was not separately instrumented; its value is the compatible residual bucket. |
| Primary command wall time | 9,953.31 s | 12,639.40 s | +2,686.09 s (+27.0%) | Operationally slower in this execution; the V1.1 console also records a one-time font-cache rebuild. |
| Maximum RSS | 2,324,103,168 B (2.164 GiB) | 2,178,990,080 B (2.029 GiB) | −145,113,088 B (−0.135 GiB; −6.24%) | Peak memory did not increase. |
| Scientific verification | PASS, 5.51 s | PASS; original duration not recorded | Status unchanged | Artifact integrity and scientific reconciliation pass in both versions. |

The supplied shorthand “2.179 GiB” for V1.1 is a unit-label mismatch: 2,178,990,080 bytes are 2.179 decimal GB or 2.029 GiB. The artifact itself records exact bytes, so this is not an artifact-integrity defect.

## Semantic and anomaly review

- All 180 V1.1 state rows are non-negative and conserve exactly 104,540 synthetic residents; maximum conservation residual is zero.
- Daily, route, age, parish, and event totals reconcile exactly. Every local event has an infector and attributed route, and all realized generation intervals resolve.
- Latent and infectious draws are exactly 2 and 5 days. Immunity draws and susceptibility-return dates are correctly null because waning is inactive.
- Severe and dead remain zero by design; no impossible compartment or chronology values were found.
- V1.1 distinguishes `cumulative_incidence_per_capita`—episodes divided by residents—from `ever_infected_fraction`—unique identities divided by residents. The legacy `attack_rate` field is explicitly deprecated and exactly aliases episode incidence. The two V1.1 fractions happen to be equal only because this run has no reinfections.
- `daily_epidemic.new_infections` excludes the 10 initial seeds, while `cumulative_total_infections` and the headline episode-per-resident measure include them. The report therefore uses 81,384 total episodes, not the legacy 81,374 cumulative field.
- O5–O8 are output-contract hardening rather than new epidemic assumptions: O5 records the matched-seed coupling caveat; O6 governs ensemble quantile floors; O7 adds realized employment numerators and denominators; O8 adds movement-per-resident-year and route/day endpoint context. O6–O8 do not alter this no-travel, single-run M7 trajectory.
- Exact source-episode identity remains deferred generally, but it creates no ambiguity here because V1.1 has one episode per infected identity.
- No observed conservation, aggregation, chronology, attribution, or provenance behavior questions the V1.1 release.

## Release-relevant observations

V1.1 demonstrates coherent full-scale behavior under its stated synthetic assumptions: transmission establishes, generates a large single wave, exhausts reachable transmission chains without reinfection or imports, and reaches persistent extinction with internally consistent artifacts. The large outcome changes are scientifically expected consequences of removing 30-day complete waning, not evidence that V1.1 must reproduce or improve V1’s numbers. The longer runtime is an operational observation, while the exact-byte peak RSS is lower and scientific verification passes.

P1 OBSERVATION: NO RELEASE CONCERN