# V1.3 Phase 0b — failure mode (filed under §12.1)

**Status:** Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26). Filed by the director from the independent exit audit `docs/audits/2026-09-26-phase0b-exit-audit-sol-FAIL.md`. Phase-0b numbers are quoted from that audit; Phase-0 numbers from `docs/audits/2026-09-24-phase0-exit-audit-sol-FAIL.md` and the Phase-0b lineage block. Nothing here is new analysis.

## What failed
P0-1 (synthetic recovery) failed scientifically; the software status is PASS. All other arms passed: P0-2A, P0-2B (G29: D=5, U=0) and P0-3 (NON_IDENTIFIED_STRUCTURAL, all six predicates).

The failing dimension is the **inoculation offset**, the same one that failed Phase 0.

| | Phase 0 (2026-09-24) | Phase 0b (2026-09-26) |
|---|---|---|
| Offset grid | coarse | five points at half spacing |
| Selected offsets (truth 2) | 0, 2, 2, 2, 4 | 4, 4, 0, 2, 0 |
| Outermost-grid selections (predicate 8, limit 1/5) | 2/5 | **4/5** |
| Offset within tolerance | not restated here | 1/5 |
| Joint four-dimension recovery | — | 1/5 |

Beta and both detection probabilities were recovered within tolerance for 5/5 targets (4/5 identified), and every mean bias was within its limit. Target 62003 has profile gaps below 5% in every dimension, so it is not identified at all.

## What the pattern shows (observation only)
In Phase 0b the selected offsets fell on both grid edges, not near the truth. The two campaigns are **not a controlled comparison**: the seeds, absolute tolerances and grid all differ, and four Phase-0b populations used the fallback. So neither the grid change nor any other factor can be isolated as the cause of the difference between them.

**Hypotheses, not findings:**
- (H1) The 30-day report series from ci-scale populations carries little information about inoculation timing.
- (H2) Timing trades off against the other fitted dimensions.

Neither Phase 0 nor Phase 0b tests these.

## Lineage disclosure
- The completed campaign ran at `ad37d45` after a pre-simulation abort at `024caa0`. The fix was the audited population-generator fallback (G32-A); the rerun used the same frozen seeds.
- Four frozen process seeds used the fallback: 62001 Trinity 11, 62002 St Peter 3, 62003 Trinity 8, 63002 Trinity 7 deferred `other` roles.
- The exit audit counts this run as the one completed scientific campaign.
- Bundle digest: `a319c5557ffa77c56baebb8341b5fc2e1432f367bdb9d0b34169aa079659032a`.

## Consequence (§12.1, §12.2)
- The one authorized redesign cycle is used. The standing delegation authorizes no Phase 0c.
- Gate **G34** is parked for Steven with the declared default **STOP: V1.3 does not proceed to real-data fitting.**
- Still permitted: written era/holdout synthesis and preparatory specification work.
- Not licensed: real Jersey fitting, any claim that synthetic recovery passed, Jersey calibration, or named-pathogen validation.
