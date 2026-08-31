# JOS V1.1 scientific hardening — implementation status

**Candidate branch:** `codex/v1.1-integration`
**Frozen V1 base:** `9e9ce3abc4201cd8303c723015462d21ca237800`
(`jos-v1.0.0`)
**Scientific authority:** `V1_1_SCIENTIFIC_DESIGN_SYNTHESIS.md`
**Status date:** 31 August 2026

## Boundary

V1.1 is a scientific-hardening candidate, not a calibrated or validated
named-pathogen model. It preserves the frozen V1 tag, one authoritative
S→E→I→R disease engine, eleven route identities, deterministic identity,
immutable artifact verification, offline/online observation agreement,
next-day detection-trigger effects, and the resident/travel identity
contracts except where the synthesis explicitly approves a correction.

No 180-day V1.1 full-wave run, 30-replicate ensemble, merge to `main`, or
release tag is part of this candidate.

## Recovered programme state and commits

| Work | Commit | Result |
|---|---|---|
| Correctness foundation | `7bcdab19d4d175c9c754e371766e4286738d8ca8` | PASS |
| R1–R5 dossiers | `68770f3` | Complete |
| Scientific synthesis | `bde889565854d99f81eb81fe3f7e539e291a4e2b` | Complete |
| R6 performance profile | `d2e57d8b985755ac2f2e28c40f1211db147251b7` | Complete; documentation only |
| M11-A natural history/observation | `ccf9d4f50f58e403b140c671129cc5a984187eeb` | PASS |
| M11-B contact/adherence | `2143255a5de24b5215dbd669e3255fc74fd0dd94` | PASS |
| M11-C school/institution structure | `dc6870245056e0ccaa5120c8389d26c0aedadf2f` | PASS with S1 deferred |
| M11-D output/ensemble semantics | `0d40c8a0aa89481ea91e4f4b219dffce926d4140` | PASS |

The integration base was
`b844cd064b644376a3a6d1624daa02fb33e14885`. Ordinary merge commits were
created in this order:

1. M11-A: `17dcb5934e506912fb20c0dc53c84d2803705e32`
2. M11-B: `dc80fe31191883038f5e0ff6d30e0753aaa5c2ea`
3. M11-C: `e779271b6a35276ab2f67318a5a0506b168d9cf0`
4. M11-D: `a570f4b55588e3f5721f2a09b55b0cf871d513ab`

The M11-D merge had one conflict: M11-A had already promoted the outbreak run
schema to V1.1 while M11-D independently versioned output semantics from the
V1 base. Resolution retained the V1.1 run/generator contract and allowed
artifact-manifest parsing for both legacy `1.0` and new `1.1` manifests.

## Scientific contract differences from V1.0

- Parish no-car residual allocation now uses the documented
  `weight × household count` definition.
- Resident absences are recomputed at runtime and repeat-trip state is keyed by
  compound trip/person identity.
- Previously asserted staffing, route-persistence, and housing diagnostics are
  measured from realised artifacts; live calendar alignment has a regression.
- Travel edge weights are named, configured, and present in resolved
  provenance without changing their V1 numeric values.
- Natural-history durations have one versioned constant/gamma interface using
  mean and CV. Draws are deterministic by infection episode and continuous
  durations advance at the first daily timestep at or after the draw.
- The generic demonstration remains constant-duration and disables complete
  short-term waning. The V1 30-day full-reset assumption is retained only as an
  explicit comparator.
- Natural history owns symptom status and nullable onset. Generic symptomatic
  onset equals infectious start; observation consumes it without resampling.
- NPI adherence is one stable intervention-version/person trait across routes,
  dates, and repeated detections. Vaccine uptake remains separate.
- Residents of represented care/medical settings are excluded from both
  general community routes. Care staff and non-care communal residents remain
  eligible.
- M4 supports persistent mean-one gamma contact activity on the approved
  participation routes, with an exact `activity_cv=0` bypass. No non-zero
  default is claimed.
- Synthetic schools now emit distinct explicit non-geographic markers instead
  of pupil-derived false parish precision. School age allocation is unchanged
  because no compatible immutable year-group margin was available.
- Episode incidence, unique-person ever-infected fraction, present-population
  travel compartments, realised employment rates, travel scaling context,
  empirical-quantile resolvability, and matched-seed paired-difference
  summaries are explicit. Deprecated attack-rate fields are exact aliases and
  are not used by the UI.

The V1 projection comparator removes both V1.1 natural-history event fields
and V1.1 daily output columns before hashing. Its scope is frozen V1 columns
under the candidate inputs; intentional upstream scientific corrections are
not misrepresented as schema incompatibility.

## Finding disposition

| Finding | Classification | Evidence in V1.1 |
|---|---|---|
| H1 | CLOSED | Care/medical residents have zero general-community membership/endpoints; staff and other communal categories remain eligible. |
| H2 | CLOSED | Natural-history-owned onset, chronology validation, observation consumption, and next-day effects. |
| H3 | PARTIALLY CLOSED BY DESIGN | Mechanism and diagnostics exist; shipped CV is zero and school/work participation can saturate under the preserved V1 expected-count rule. |
| H4 | PARTIALLY CLOSED BY DESIGN | Constant/gamma episode-scoped architecture exists; no supported non-zero generic CV or named-pathogen default is supplied. |
| H5 | CLOSED | Stable intervention-version/person adherence; route/date/episode redraws removed. |
| S1 | DEFERRED TO V1.x | A compatible frozen CYPES year-group margin was unavailable; the collapse is exposed in diagnostics, not hidden. |
| S2 | CLOSED | School and staff geography is explicitly synthetic/non-geographic. |
| S3 | CLOSED | Correct parish residual weighting and regression. |
| S4 | CLOSED | In-horizon absence lifecycle and daily reconciliation. |
| S5 | CLOSED | Repeat trips use compound episode identity. |
| V1 | CLOSED | Three named diagnostics are realised measurements or explicit invariants. |
| V3 | CLOSED | Full-target controls enforce 48 schools, 13,991 pupils, type totals, age eligibility, multi-school behaviour, and the nursing-role boundary. |
| V4 | CLOSED | Live simulation regression crosses weekend and school-term boundaries. |
| O1 | CLOSED | Truthful incidence and unique-person fields; deprecated alias only. |
| O2 | CLOSED | Present compartments and mixed-population denominators are explicit. |
| O3 | CLOSED | Travel route weights are configured and provenanced. |
| O4 | PARTIALLY CLOSED BY DESIGN | Low-risk provenance gaps in the promoted V1.1 scope are corrected; broader calendar/source-role and unused-control cleanup was not promoted by the synthesis. |
| O5 | CLOSED | Persisted matched-seed distributional summary and coupling caveat. |
| O6 | CLOSED | Quantile floors use successful replicates only; unresolved values remain null. |
| O7 | CLOSED | Realised employment numerators, denominators, and rates are reported. |
| O8 | CLOSED | Movements per resident-year and route/day endpoint context are reported. |

No listed finding is classified `FAILED`. Partial/deferred findings constrain
claims and are not nominally closed by the existence of an interface.

## Explicit deferrals

- Immutable, compatible CYPES year-group evidence and an S1 allocator.
- A scientifically supported non-zero generic duration CV.
- A scientifically supported non-zero contact-activity CV and sensitivity
  execution; bus activity remains deferred with N-21.
- Presymptomatic duration/relative infectiousness, partial immunity, and exact
  source-episode identity.
- Parameter-uncertainty propagation and variance decomposition.
- Remaining O4 provenance cleanup outside the promoted bounded work.
- Broader household, care, workplace, remote-work, visitor-volume/composition,
  accommodation, infection-age, and epidemiological-data work described by
  R3–R5.
- Performance optimisation. R6 approved no code change; candidates require a
  separate repeated unprofiled before/after equivalence gate.

## Verification

Independent lanes and post-merge focused suites passed. Integrated frontend
tests, TypeScript, production build, Ruff, formatting, targeted mypy, lock
check, compileall, and `git diff --check` passed. The final integrated backend
suite passed **214 tests** with four known third-party/runtime warnings in
**714.17 seconds**.

The bounded full-target institutional regression is verification of exact
controls and previously unexercised branches; it is not a new 104,540-person
epidemic run or empirical validation.
