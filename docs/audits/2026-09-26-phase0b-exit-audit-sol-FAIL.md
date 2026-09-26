JOS V1.3 PHASE-0B EXIT GATE: FAIL

**Phase 0: FAIL (2026-09-24); Phase 0b: FAIL.** This is a determinate scientific failure of P0-1, not an indeterminate G29 result. The published arm statuses agree with independent recomputation.

| Arm | Published software / scientific status | Recomputed software / scientific status |
|---|---|---|
| P0-1 synthetic recovery | PASS / FAIL | PASS / **FAIL** |
| P0-2A wrong delay | PASS / PASS | PASS / PASS |
| P0-2B wrong ascertainment | PASS / PASS | PASS / PASS |
| P0-3 structural control | PASS / PASS | PASS / PASS |

### Findings by severity

- **Gate blocking, scientific:** P0-1 selected inoculation offsets **`4, 4, 0, 2, 0`** for seeds `62001–62005`. Four are the declared outermost grid values, exceeding predicate 8’s maximum of **1/5**. Only **1/5** offsets are within the one-day tolerance, and only **1/5** targets meet the joint four-dimension condition; predicates 5 and 6 also fail. Seed `62003` is not identified in any dimension under the unchanged 5% profile-gap rule. There are no tied global minima.
- **Published-status discrepancies:** None.
- **Non-blocking lineage limitation:** The population-generator fallback affected four frozen process seeds. Their synthetic populations therefore depend on the reviewed fix, even though no frozen seed, grid, tolerance, threshold, predicate, objective, or harness line changed.

### Execution-lineage ruling

The 2026-09-25 `execute` invocation at `024caa0` aborted at population generation in three seconds: four of eight builds raised `DataBuildError`; no simulation ran and no result bundle existed. It was an `execute` abort, rather than the dry-run validation case literally named in §12.3. Owner decision **G32-A** explicitly authorized a reviewed fix and a **same-seed** rerun. That applies §12.3’s safeguard against selecting a new realization. I count the 2026-09-26 run as the **one completed scientific campaign**, not a retry after observing a scientific result.

The fix at `ad37d45` changed only `population_generator.py` and one test. The supplied independent fix audit reports unchanged artifacts for 133 seeds that already built. The rerun log discloses fallback rows for `62001` Trinity 11, `62002` St Peter 3, `62003` Trinity 8, and `63002` Trinity 7 deferred `other` roles, with M2 artifact IDs and diagnostic digests; the other four frozen process seeds had none. The rerun exited 0 in 578 seconds. This lineage must accompany the scientific FAIL.

### Recomputation evidence

`sha256sum -c SHA256SUMS` exited **0** for all **4,043 listed files**; the checksum-file digest is `a319c5557ffa77c56baebb8341b5fc2e1432f367bdb9d0b34169aa079659032a`. All **65** [input hashes](/home/steven/jos-phase0b-rerun-20260926T091252Z/bundle/input_hashes.json) match the retained controls or clone at `ad37d45`. The config, predeclaration, G29 ruling, and owner ruling digests match their frozen values and independent harness constants. The [seed ledger](/home/steven/jos-phase0b-rerun-20260926T091252Z/bundle/seed_ledger.json) has exactly the five declared target pairs, three candidate pairs, and nine negative-control cells. The [summary lineage](/home/steven/jos-phase0b-rerun-20260926T091252Z/bundle/campaign_summary.json) matches §6, preserves Phase-0 FAIL, and labels the earlier P0-2/P0-3 passes as historical evidence only.

Retained tables contain **625/625/75/9 cells** and **1,880/1,875/225/27 transforms**, totaling **1,334 cells and 4,007 transforms**. Measured counters report **107 latent calls, eight builds, `ci` mode, and 30 days**. The config, ledger, and log show no replacement seeds or retry. Independent arithmetic reproduced all **6,670** published objective values across the four arms; maximum absolute difference was `8.89×10⁻¹⁵`.

For P0-1, selected tuples below are `(beta, offset, symptomatic detection, asymptomatic detection)`:

| Target seed | Minimum loss | Selected tuple | Joint identified and within tolerance |
|---|---:|---|---|
| 62001 | 0.226994 | `(0.08, 4, 0.75, 0.325)` | No |
| 62002 | 0.224612 | `(0.08, 4, 0.75, 0.25)` | No |
| 62003 | 0.334549 | `(0.08, 0, 0.75, 0.25)` | No; all profile gaps below 5% |
| 62004 | 0.282804 | `(0.10, 2, 0.625, 0.25)` | Yes |
| 62005 | 0.372013 | `(0.08, 0, 0.75, 0.25)` | No |

| Dimension | Raw tolerance hits | Identified tolerance hits | Mean signed bias | Boundary selections |
|---|---:|---:|---:|---:|
| Beta | 5/5 | 4/5 | `+0.004` | 0/5 |
| Inoculation offset | **1/5** | **1/5** | `0` | **4/5** |
| Symptomatic detection | 5/5 | 4/5 | `−0.025` | 0/5 |
| Asymptomatic detection | 5/5 | 4/5 | `+0.015` | 0/5 |

All four mean biases meet their declared limits. The inclusive decimal endpoints for beta, symptomatic detection, and asymptomatic detection were counted as tolerance hits. All five truths realized ten inoculation acquisitions, 1,828–2,144 local secondary infections, both report channels, and 27–28 nonzero combined-report dates. Retained chronology and conservation diagnostics pass.

For P0-2, each wrong-arm minimum is unique. In seed order `62001–62005`, P0-2A’s independently evaluated clauses are: **offset `4`** `T,T,F,T,F`; **any dimension outside tolerance** `T,T,F,T,F`; **\(R_i\ge0.25\)** `T,T,T,T,T`. Its \(R_i\) values are `9.688, 10.535, 3.400, 3.671, 3.805`. P0-2B has **\(R_i\ge0.25\)** and **\(E_i\ge0.25\)** true for every target, beta outside tolerance false for every target, and timing outside tolerance `T,T,T,F,T`. Its \(R_i\) values are `3.517, 4.269, 2.452, 2.940, 2.664`; \(E_i\) values are `0.706, 1.246, 0.801, 1.043, 1.049`. Under G29, each arm has **D=5, U=0, attainable interval [5,5]**, so both detection statuses are proven PASS.

For P0-3, all five nine-cell surfaces give beta argmins **`0.16, 0.08, 0.04`** at route factors **`0.5, 1.0, 2.0`**, with shifts **`+0.08, 0, −0.04`**. Ridge objective spread is **0** for every target. The three 204-element ridge vectors agree exactly; their independently rebuilt hash is `316268e43f658e154e7f28d90cf55c14bbc7a2ee583b73f5890c9a8113a92ac1`. All six predicates hold, `factor_estimate` is null without precision fields, and `NON_IDENTIFIED_STRUCTURAL` is supported.

### Limits and consequence

The 15 retained blind records, their file and estimate hashes, complete surfaces, and reviewed persistence/read-back code support the blind-fitting rule. The [manifest](/home/steven/jos-phase0b-rerun-20260926T091252Z/bundle/blind_estimate_manifest.json) explicitly says runtime event order and timestamps were **not recorded**. Latent-call and build totals rely on retained measured counters and provenance; the observed-table count was checked directly. Five-target hit rates and replicate variation are descriptive, not confidence intervals.

Because every arm’s software status is PASS but P0-1 fails, **§12.2 records a scientific FAIL**. **§12.1 now applies:** the director parks a gate for Steven with the declared default **STOP: V1.3 does not proceed to real-data fitting**, and files the Phase-0b failure mode under `docs/research/v1_3/`. No further redesign cycle is authorized by the standing delegation.

Phase 1 may continue written era and holdout synthesis and preparatory specification work. This verdict does **not** license fitting real Jersey data, claiming synthetic recovery passed, Jersey calibration, or named-pathogen validation. A materially different later objective still requires its declared deterministic fixture and synthetic-recovery check before real fitting.

**Attestation:** Audited the immutable bundle at the digest above against clean clone `ad37d45df75f28459b1311476128438114c198a6`. Audit scripts and output were confined to `/tmp`. No bundle or clone edits, simulations, observation calls, commits, or pushes were made.