POPGEN RESIDUAL DIAGNOSIS: COMPLETE

## Summary

The CI sweep found **28 failures across seeds 1–300**: 22 M3 destination-share failures, five M2 adult-role supply shortages, and one M2 household-capacity failure. These account for the original 14 failures in seeds 1–150.

All **28 CI-failing seeds passed** M2 and M3 generation in the targeted scaled-mode rerun. Full-mode pins 101 and 123 both passed M2 and M3 diagnostics.

## Class 1 — M3 destination shares

The destination gate uses the correct cohort for the frozen target. The measure dictionary says the census destination split excludes workers who worked from home, had no fixed workplace, or worked outside the Island; the published shares are 66% St Helier, 13% semi-urban, and 21% rural ([measure dictionary, row 82](/home/steven/jos-popdiag-readonly/data/processed/measure_dictionary.csv:82), [destination controls](/home/steven/jos-popdiag-readonly/data/processed/workplace_destination.csv:2)).

The generator assigns destination categories across **all filled job slots**, including secondary jobs and workers later marked as WFH ([`_assign_workplace_parishes`](/home/steven/jos-popdiag-readonly/src/jersey_outbreak/population_structure_generator.py:330), called before primary job placement at [line 1084](/home/steven/jos-popdiag-readonly/src/jersey_outbreak/population_structure_generator.py:1084)). The diagnostic then checks destination shares among physical employed residents, excluding WFH ([lines 608–624](/home/steven/jos-popdiag-readonly/src/jersey_outbreak/population_structure_generator.py:608)). WFH selection occurs separately at [lines 1025–1035](/home/steven/jos-popdiag-readonly/src/jersey_outbreak/population_structure_generator.py:1025).

For CI seed 34, the generator allocated **1,783 filled slots**—1,666 primary jobs plus 117 secondary jobs. The gate measured 1,438 physical workers after excluding 228 WFH workers. St Helier had 965/1,438 physical workers (67.107%) against 66%. The share error decomposes into **+0.012 pp** from slot allocation residual, **+0.374 pp** from primary-worker versus all-slot composition, and **+0.721 pp** from WFH exclusion: **+1.107 pp** total. The WFH effect is the largest term, with secondary-job composition also contributing on some seeds.

If the check instead included all primary workers, all 22 failed seeds would pass the 1 pp test. That denominator is inconsistent with the source, which explicitly excludes WFH.

**CI frequency:** 22/300 seeds failed this gate: 16 St Helier checks, 7 rural checks, and 2 semi-urban checks, with two seeds failing two categories. The original 11 failures in seeds 1–150 are included.

For each failed category below, `A/P/W` gives the additive gap decomposition in percentage points: allocation residual / primary-worker versus all-slot mix / WFH exclusion. Each physical-worker denominator is 1,438.

| Seed | Failed destination share: actual vs target; gap | A/P/W (pp) |
|---:|---|---:|
| 34 | St Helier: 965/1,438 = 67.107% vs 66%; +1.107 | +0.012 / +0.374 / +0.721 |
| 47 | St Helier: 932/1,438 = 64.812% vs 66%; −1.188 | +0.012 / −0.226 / −0.974 |
| 54 | St Helier: 934/1,438 = 64.951% vs 66%; −1.049 | +0.012 / −0.166 / −0.895 |
| 65 | St Helier: 964/1,438 = 67.038% vs 66%; +1.038 | +0.012 / +0.074 / +0.951 |
| 73 | St Helier: 931/1,438 = 64.743% vs 66%; −1.257 | +0.012 / −0.226 / −1.044 |
| 77 | St Helier: 934/1,438 = 64.951% vs 66%; −1.049 | +0.012 / −0.166 / −0.895 |
| 79 | St Helier: 930/1,438 = 64.673% vs 66%; −1.327; rural: 317/1,438 = 22.045% vs 21%; +1.045 | H: +0.012 / +0.014 / −1.353; R: −0.024 / +0.033 / +1.036 |
| 81 | St Helier: 964/1,438 = 67.038% vs 66%; +1.038 | +0.012 / −0.046 / +1.071 |
| 93 | Rural: 286/1,438 = 19.889% vs 21%; −1.111 | −0.024 / −0.508 / −0.579 |
| 118 | Rural: 320/1,438 = 22.253% vs 21%; +1.253 | −0.024 / +0.033 / +1.245 |
| 119 | St Helier: 933/1,438 = 64.882% vs 66%; −1.118 | +0.012 / −0.226 / −0.905 |
| 156 | Rural: 287/1,438 = 19.958% vs 21%; −1.042 | −0.024 / −0.148 / −0.870 |
| 159 | St Helier: 970/1,438 = 67.455% vs 66%; +1.455; rural: 286/1,438 = 19.889% vs 21%; −1.111 | H: +0.012 / +0.014 / +1.428; R: −0.024 / −0.268 / −0.820 |
| 168 | St Helier: 964/1,438 = 67.038% vs 66%; +1.038; rural: 285/1,438 = 19.819% vs 21%; −1.181 | H: +0.012 / +0.014 / +1.011; R: −0.024 / −0.028 / −1.129 |
| 177 | St Helier: 930/1,438 = 64.673% vs 66%; −1.327 | +0.012 / −0.226 / −1.113 |
| 192 | Rural: 318/1,438 = 22.114% vs 21%; +1.114 | −0.024 / +0.513 / +0.625 |
| 218 | St Helier: 932/1,438 = 64.812% vs 66%; −1.188 | +0.012 / −0.226 / −0.974 |
| 254 | St Helier: 930/1,438 = 64.673% vs 66%; −1.327 | +0.012 / −0.646 / −0.693 |
| 263 | Semi-urban: 169/1,438 = 11.752% vs 13%; −1.248 | +0.012 / +0.013 / −1.273 |
| 273 | St Helier: 934/1,438 = 64.951% vs 66%; −1.049 | +0.012 / −0.106 / −0.955 |
| 277 | St Helier: 934/1,438 = 64.951% vs 66%; −1.049 | +0.012 / −0.466 / −0.595 |
| 299 | Semi-urban: 172/1,438 = 11.961% vs 13%; −1.039 | +0.012 / −0.587 / −0.464 |

Among 272 passing CI seeds, the median absolute gap was 0.353 pp for St Helier, 0.213 pp for semi-urban, and 0.313 pp for rural. The nearest passing seeds to the 1 pp failure boundary were seed 36 for St Helier (0.021 pp of margin), seed 40 for semi-urban (0.031 pp), and seed 186 for rural (0.028 pp).

**Fix designs**

- **Recheck against all primary workers, including WFH:** Existing structure tables and logical structure hashes would be unchanged, but diagnostic values and complete artifact hashes would change on passing seeds too. Counts and published targets stay fixed; the denominator would contradict the source exclusion. Tolerance stays at 0.01, but the check’s meaning changes. An end-to-end test would compare the source definition, rebuild seeds 1–300, and verify unchanged structure tables and downstream M4 outputs. **Not recommended.**
- **Failure-only destination reassignment weighted by physical primary workers:** After primary jobs and WFH membership are known, reassign workplace destination categories only if the physical-worker shares fail; update workplace and job destinations before commute modes are assigned. Existing passing builds can remain byte-identical; failed seeds receive new M3 work-parish assignments and hashes. Population counts, controls, and published targets stay fixed. The 0.01 tolerance stays fixed. Test all CI seeds 1–300, byte-compare all currently successful M3 tables/hashes, verify every destination category on repaired seeds and all other M3 checks, then verify deterministic M4 generation and route consistency. **Recommended**, subject to owner review of the changed M3 geography and hashes for newly buildable seeds.

Simply widening the destination tolerance would change a scientific gate and requires an owner decision; it is not recommended.

## Class 2 — M2 adult-role demand exceeds parish supply

Before assigning ages, household roles require more age-16+ residents than the parish’s fixed private age-sex pool contains. The role bounds are explicit: adult/parent/partner/unrelated-adult roles require age 18+, and adult-child roles require age 16+ ([role bounds](/home/steven/jos-popdiag-readonly/src/jersey_outbreak/population_generator.py:445)). The residual-last fallback defers only `other` roles; it cannot satisfy an aggregate shortage of constrained roles ([fallback](/home/steven/jos-popdiag-readonly/src/jersey_outbreak/population_generator.py:713)).

**CI frequency:** 5/300 seeds failed this way. The age-16+ role demand and private supply were:

| Seed | Parish | Demand | Supply | Shortfall |
|---:|---|---:|---:|---:|
| 122 | St Peter | 98 | 97 | 1 |
| 147 | St Ouen | 75 | 73 | 2 |
| 163 | St Peter | 96 | 95 | 1 |
| 228 | St Ouen | 87 | 86 | 1 |
| 261 | St Ouen | 86 | 85 | 1 |

The thrown errors confirm the constrained assignment was left with only children in the pool, including `18–95` role failures. **All five passed in scaled mode.**

**Fix designs**

- **Relax age bounds or convert constrained roles to `other`:** A failure-only fallback could preserve current successful outputs, but it changes household-role semantics; a global rule could also change existing outputs. Population counts and published controls could remain fixed, and there is no diagnostic tolerance involved. An end-to-end test would need an owner-authored role rule and explicit checks for age/role validity. **Not recommended without that written rule.**
- **Failure-only, role-feasibility-aware parish household placement:** Reallocate household placement across parishes so constrained-role demand fits each already-fixed parish age-sex pool, using existing household types and age rules. Preserve parish resident totals and age-sex counts plus island household totals/type counts. Successful current seeds can stay byte-identical; affected seeds get new household/resident assignments and M2 hashes. Published controls do not change, but the derived household-to-parish allocation and protected identities/hashes do. No tolerance changes. Test seeds 122, 147, 163, 228, and 261, then the full CI 1–300 sweep; assert all exact population and parish age-sex controls, household-type totals, role-age invariants, deterministic repeats, and downstream M3/M4 builds. **Recommended**, with the parish allocation rule specified and reviewed before implementation.

## Class 3 — M2 household capacity exhausted

Seed 96 fails before resident-age assignment. In St Mary, the probe found four households with seven baseline roles and 15 additional private residents to place. Under the current household-size caps, those four households have room for only nine additional roles, leaving six unplaceable. The probe found zero capacity remaining in the eligible categories when the generator raises at [lines 1539–1556](/home/steven/jos-popdiag-readonly/src/jersey_outbreak/population_generator.py:1539). This is a structural cap/cell-allocation mismatch, not a draw-order issue. The source does not publish hard maximum household sizes; the current limits are documented as structural assumptions ([limits](/home/steven/jos-popdiag-readonly/src/jersey_outbreak/population_generator.py:62)).

**CI frequency:** 1/300 seed, 96. It passed at scaled mode.

**Fix designs**

- **Increase household-size caps:** A failure-only version could leave currently successful seeds byte-identical; seed 96 would get a new household structure and hash. Counts and controls could stay fixed, but this introduces a new structural assumption without a sourced value. There is no tolerance change. An end-to-end test would need a written cap specification plus checks for household-size and population controls. **Not recommended without a written spec.**
- **Failure-only household placement reallocation under existing caps:** Reassign household placements to St Mary so existing capacity suffices. For example, a two-person couple household with six available slots under the existing cap could replace two one-person households while preserving St Mary’s resident total. This preserves island household-type totals, population controls, and the current size limits. Existing successful seeds can stay byte-identical; seed 96’s household placement and M2 hash change. No tolerance changes. Test seed 96 and all CI seeds 1–300; require exact parish resident and age-sex counts, exact island household totals/type counts, current caps respected, deterministic output, and downstream M3/M4 builds. **Recommended**, with the parish allocation rule reviewed as a synthetic structural choice.

## Scaled and full-mode checks

The targeted scaled run covered the **28 CI-failing seeds**: all 28 passed M2 and M3. The largest destination-share gap among them in scaled mode was 0.620 pp, within the unchanged 1 pp tolerance. This was a targeted check of those seeds, not a full scaled 1–300 sweep.

Full-mode seeds 101 and 123 both passed all 2,532 M2 checks and 75 M3 checks. Destination-share gaps were at most 0.218 pp. Across nonzero-tolerance checks, the closest M3 gate was `commute_car`, using 57.66% and 58.58% of its allowed difference respectively; the pins are not near a threshold.

## Probe evidence and tree state

The probes called the population and structure generator APIs directly; they ran no outbreak simulation and no test suite.

- Probe script: [`/tmp/popdiag_probe.py`](/tmp/popdiag_probe.py)
- CI seeds 1–300: [`ci-1-300.jsonl`](/tmp/jos-popdiag-residual/ci-1-300.jsonl)
- Scaled rerun of the 28 CI-failing seeds: [`scaled-ci-failures.jsonl`](/tmp/jos-popdiag-residual/scaled-ci-failures.jsonl)
- Full-mode pins 101 and 123: [`full-pins-101-123.jsonl`](/tmp/jos-popdiag-residual/full-pins-101-123.jsonl)

Clone SHA: `9b504f3a8c51a574607fadab5e79c49b9231a136`. Final `git status --porcelain=v1 --untracked-files=all` and `git diff --stat` were empty. No repository files were changed.