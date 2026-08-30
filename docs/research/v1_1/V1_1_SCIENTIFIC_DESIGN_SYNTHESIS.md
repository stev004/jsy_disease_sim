# JOS V1.1 scientific design synthesis

**Decision date:** 30 August 2026  
**Frozen V1 base:** `9e9ce3abc4201cd8303c723015462d21ca237800` (`jos-v1.0.0`)  
**Inputs:** R1–R6, the V1 audit/technical report/roadmap on
`docs/jos-v1-scientific-review`, the frozen full-scale pilot at
`/Users/stevenmatson/Documents/JOS_v1_full_scale_evidence/run-20260830T180202Z/`,
and direct inspection of the frozen implementation and tests.

## Intent and boundary

V1.1 removes bounded correctness defects and establishes scientifically honest
interfaces for heterogeneous natural history and contact behaviour. It must not
manufacture pathogen-neutral values, claim calibration or validation, change the
eleven route identities, collapse provenance classes, or alter the frozen V1 tag.
The authoritative lifecycle, route separation, deterministic identity, immutable
artefacts, offline/online observation agreement, no-retrocausality rule, and
resident/travel identity contracts remain protected unless a decision below names
the exact change.

“Architecture complete” and “scientific default selected” are separate states.
Where evidence supports a mechanism but not a numeric default, V1.1 may implement
and test the mechanism while keeping the neutral comparator. It must report the
remaining scientific blocker rather than imply that the finding is fully closed.

## Audit errata resolved by this synthesis

- Frozen `community_outdoor` edge weight is `0.15`, not `0.18`. V1.1 preserves
  `0.15` unless a later evidence-backed change is authorised.
- Community-matrix reciprocity is `N-07`. `N-21` concerns bus topology. Neither is
  promoted into M11-B.
- H1's phrase “communal-establishment residents” is narrowed to residents of the
  care/medical settings already represented by JOS care routes. Hotels, staff
  accommodation, shelters and detention are not silently excluded.
- H2's “positive onset delay” means a positive infection-to-onset interval. The
  generic no-presymptomatic design places onset at infectious start after a
  strictly positive latent duration; it does not invent a positive
  infectious-start-to-onset delay.

## Decisions

| # | Decision | Findings and evidence | Implementation consequence | Compatibility consequence | Test consequence |
|---:|---|---|---|---|---|
| 1 | **Duration architecture:** versioned `constant` and `gamma` stage specifications use `mean_days` and, for gamma, strictly positive `cv`. Lognormal and empirical PMFs are deferred. Continuous draws advance at the first daily timestep at or after the sampled transition. Draw identity is infection-episode scoped. | `H4/D-01`; R1 duration review and discrete-time risk. | M11-A adds one schema/runtime path whose family selects constant or gamma; no parallel disease engine. Latent and infectious stages are required. Immunity may use the same schema only when waning is explicitly enabled. | The constant family is the V1 comparator. Schema and manifests are versioned. | Validation, deterministic episode draws, nonzero synthetic variation, discrete transition rule, and explicit V1-projection equivalence. |
| 2 | **Generic default:** the shipped pathogen-neutral demonstration remains constant-duration. No non-zero gamma CV is selected as a scientific default. A synthetic test fixture may use `mean_days=4`, `cv=0.5`, seed `20260830`; it is fixture evidence only. Generic complete waning is disabled in the V1.1 demonstration. A 30-day full-reset configuration remains an explicitly labelled V1 sensitivity comparator. | `D-01`, `D-03`, `E-01`; R1 finds no pathogen-neutral CV and identifies recurrent-wave sensitivity to full reset. | M11-A changes the demo's waning switch, retains a V1 comparator fixture, and emits configured/realised duration and waning semantics. | Expected demo epidemic and hashes change because waning changes; the V1 comparator remains reproducible. H4 is **architecture-complete but scientifically partial** until a declared non-zero scenario or named-pathogen evidence is approved. | No 180-day run now. Short tests prove disabled waning, comparator timing, and gamma fixture moments (10,000 draws; sample mean within 2%, sample CV within 3%). |
| 3 | **Onset and detection:** natural history owns symptom status and nullable onset. In the generic no-presymptomatic mode, symptomatic onset equals infectious start; asymptomatic episodes have no onset. Observation consumes, never resamples, those fields. Detection remains onset- or infection-anchored as configured and cannot precede its anchor. Presymptomatic phase weights/durations are deferred. | `H2/O-02`, interacting `D-02/I-01/I-02`; R1 and QA conflict resolution. | M11-A changes lifecycle order so prognosis/onset exists before observation scheduling, without duplicating disease logic. | Observation artefact/hash schemas must be versioned. Detection-triggered effects still start no earlier than the next day. | Every symptomatic episode has `infection < infectious_start = onset <= recovery`; offline/online schedules match; a deliberately pre-infectious onset is rejected. |
| 4 | **NPI adherence:** one stable Bernoulli trait is keyed by `(run_seed, intervention_id, intervention_version, agent_id)`. It represents acceptance/adherence to that intervention. All configured route reductions are deterministic conditional on the trait; route/date/episode are absent from the key. Separate intervention identities may yield separate traits. Existing WFH day scheduling is not a second adherence draw. Vaccine campaign uptake remains separate. | `H5/I-01`, interactions `I-02/I-04`; R1 and repository inspection. | M11-B removes route and detection-date redraws and documents the existing field's clarified semantics; no schema rename is required. | Intervention effect sizes may change; neutral scenarios, next-day activation, attenuation-only route semantics and vaccine uptake remain protected. | Repeated detections and route-order permutations reuse one value; fully non-adherent fraction passes a fixed binomial 99.9% interval for `N=100000`, `a=0.60`; vaccine and neutral fixtures are unchanged. |
| 5 | **Contact activity:** authority is M4, not M2, preserving population identity. A persistent mean-one gamma trait is keyed by `(network_seed, "persistent-contact-activity", agent_id, distribution_version)`. `activity_cv=0` bypasses the new logic exactly. For non-zero CV, activity modifies **participation once**, not participation and degree: for each eligible route/day, `p_i=min(1, lambda*A_i)` and deterministic bisection selects `lambda` so `sum(p_i)` equals the V1 expected participant count. Existing per-route hash uniforms decide inclusion. Ring degree among participants remains unchanged. Initial routes are community indoor/outdoor, workplace transient, and pupil-to-pupil school cross-class. Staff bridge construction is preserved and bus is deferred. No non-zero shipped CV is approved. | `H3/N-02`; R2 evidence, QA finding that the prior dual mapping was ambiguous; `N-07/N-21` deferred. | M11-B may implement the neutral-preserving interface and diagnostics, but a non-zero default is blocked. Edge weights remain separate. | `activity_cv=0` must reproduce V1 route snapshots/hashes exactly. Non-zero configs are explicit structural sensitivity scenarios. | Synthetic gamma moments use the same 10,000-draw/2%/3% fixture rule; tests prove identity persistence, route scope, preserved staff bridges, no bus/matrix change, and exact zero-CV V1 projection. H3 remains **scientifically partial**. |
| 6 | **Care participation:** residents whose represented setting type is care or medical are excluded from both general community routes. Care staff remain eligible. Other communal categories are unchanged. | `H1/N-10`, interacting `POP-09/POP-10/STA-05`; R2 and official category definitions. | M11-B applies one auditable membership predicate before community construction and adds residence-type participation diagnostics. | Community route outputs change only for the named residents; care-route membership and staffing remain protected. | Full-mode institutional fixture proves zero community endpoints for care/medical residents, nonzero eligible staff participation, and unchanged non-care communal eligibility. |
| 7 | **School ages:** preferred V1.1 design uses a frozen, registered CYPES school-year margin and inventory, reconciled to protected island pupil/type totals. Allocation is deterministic within single-year age strata and preserves documented eligibility. If the source cannot be frozen and hashed, S1 does not proceed; no synthetic age profile is invented merely to close the finding. | `S1/STR-01`; R3 official Jersey evidence. | M11-C owns acquisition/registration plus the smallest age-stratified allocator. | School assignments and derived hashes are expected to change; island pupil totals and school-type identities stay protected. | Source/hash gate; every type spans its eligible years; type-by-single-year diagnostics reconcile exactly; fixed-seed determinism and full-mode institutions pass. |
| 8 | **School geography:** preferred design uses a frozen official school-site/parish inventory and published catchment/feeder information where applicable. Selective, fee-paying, private, Catholic and special schools remain island-wide subject to eligibility/capacity. If those sources cannot be frozen, the accepted fallback is to emit an explicit non-geographic/synthetic value and remove any false St Helier implication. | `S2/STR-02`; R3. | M11-C implements one of the two ordered outcomes, never inferred geography from assigned pupils. | School/staff parish outputs change. Downstream fields must distinguish observed site geography from synthetic/non-geographic allocation. | Source/hash and capacity reconciliation for preferred design; otherwise a semantic test proves no ordinary parish is emitted. Household-school parish association is reported only for the geographic design. |
| 9 | **Provenance:** retain existing protected status enums. New concepts such as `structural_assumption`, `proxy`, `geographic_proxy`, and `external_validation_reference` are separate role/transfer tags, not ad hoc status values. Every resolved parameter reports meaning, units, status, role, source/derivation, value, and sensitivity requirement. | `P-02`, R1–R5, QA enum inspection. | Lanes extend versioned metadata only where required and reuse current `scenario_assumption`, `literature_prior`, `derived`, and source evidence statuses. | Readers of older artefacts need explicit schema-version handling; no silent enum widening. | Unknown statuses fail; role/status mappings round-trip; every new scientific control appears in resolved provenance. |
| 10 | **V1.1 data boundary:** S1/S2 school evidence is the only new external structural acquisition promoted into V1.1. The POP-07 formula correction is sufficient now; direct cars-by-parish ingestion, monthly travel replacement, visitor composition/accommodation, household/care/workplace/remote-work improvements, and epidemiological series registration remain V1.x. | `S1/S2/S3`, R3–R5 and programme scope. | M11-C is bounded to schools and V3 institutional coverage. R5 remains a forward plan, not an ingestion lane. | Avoids changing unrelated population, travel-volume or epidemiological contracts. | Tests target only promoted data and named structural outputs. |
| 11 | **Performance:** no optimisation is approved from R6. The profile is instrumentation-distorted and lacks repeated unprofiled before/after timing, memory and recovered result hashes. Dynamic edge refresh and exact attribution are candidates only after science integration. | R6; pilot wall anchor `9260.278 s / 180 = 51.446 s` per output point and peak RSS about 2.16 GiB. | Performance branch remains documentation-only. Post-integration work must benchmark one isolated change at a time. | No scientific or reproducibility contract changes for a speculative speedup. | Require at least three unprofiled paired timings after one warm-up, median runtime, peak RSS, identical fixed-seed logical/latent outputs, route snapshots, events, observation/intervention tables and diagnostics. |
| 12 | **Outputs and ensembles:** M11-D implements O1/O2/O5/O6/O7/O8 with explicit denominators and interval classes. Interior empirical quantiles require `n*min(q,1-q) >= 1`; 2.5/97.5 therefore requires 40 successful replicates. Below the floor, no requested tail band is emitted; median/IQR is allowed only when its own floor passes. Paired summaries aggregate within-seed differences and retain the coupling caveat. | `D-04/T-25/E-02/E-03/STR-05/T-03/T-13`; R4. | Add truthful names and metadata; deprecated misleading fields may remain only if marked and unused by UI. | Output schemas change version; old names are compatibility aliases, not headline scientific fields. | Deterministic 39/40 replicate boundary fixtures; exact paired summary fixture; resident/present denominators; realised employment and travel-scaling reconciliation. |

## Event identity and hash decision

Exact source-episode identity is deferred. The frozen single-active-episode lifecycle
makes the current latest-earlier source resolution exact for the demonstrated V1
state machine, and no ambiguous historical case was reproduced. M11-A may add
authoritative natural-history timing fields only where required for onset ownership.
Any event-row addition requires a versioned V1.1 hash plus a V1 projection
comparator; it must not claim the full V1 hash is unchanged.

## Lane acceptance and ownership

### M11-A — natural history and observation

- Own only duration schema/runtime, generic waning default, natural-history onset,
  observation consumption, diagnostics, artefact versioning and direct tests.
- Do not implement presymptomatic profiles, named-pathogen values, exact source
  episode IDs, partial immunity, calibration, or a second scheduler.
- PASS requires the fixed synthetic gamma tolerances above, exact constant
  comparator transition projection, chronology rejection, offline/online equality,
  no same-day intervention effect, and all affected protected suites.

### M11-B — contact behaviour and interventions

- Own H1, H5, and only the activity interface precisely specified in decision 5.
- Do not change community matrices, bus topology, school staff bridges, edge
  weights, M2 identity, route names, or route attribution semantics.
- PASS requires exact zero-CV V1 route projection, stable adherence, full-mode care
  exclusion, route separation, activity diagnostics, and all affected protected
  suites. Report H3 as partial while the shipped CV is zero.

### M11-C — structure

- Acquire/freeze/register only the R3 school sources needed for S1/S2, or take the
  explicit non-geographic S2 fallback. If S1 evidence cannot be frozen, stop S1.
- Preserve island pupil totals and all unrelated population/institution contracts.
- PASS requires source hashes, deterministic reconstruction, type/year
  reconciliation, no age collapse, truthful geography, and a short full-mode
  institutional test.

### M11-D — semantics

- Own O1/O2/O5/O6/O7/O8 and their API/UI consumers where present.
- Do not add parameter-uncertainty propagation, travel-volume redesign, or
  calibration.
- PASS requires the exact quantile boundary, paired-difference fixture, denominator
  metadata, realised employment/travel diagnostics, and backend/frontend checks for
  affected surfaces.

## Integration gates

Each lane must state its exact base commit, changed files, changed scientific
contract, evidence basis, provenance additions, expected output differences,
compatibility effects, tests and PASS/FAIL. Merge passing lanes one at a time with
ordinary merge commits. After each merge run affected tests; after all merges run
the full backend suite, scientific verification, frontend tests, TypeScript, build,
lint/format/type checks and diff check. No 180-day or 30-replicate full-population
execution is authorised before an independent V1.1 audit candidate passes.

## Explicit remaining scientific blockers

- A non-zero pathogen-neutral duration CV is unsupported.
- A non-zero contact-activity CV is unsupported.
- Presymptomatic duration/relative infectiousness and incubation-sensitive test
  curves require named-pathogen evidence.
- School implementation requires immutable acquisition of the cited official
  aggregate sources; absence of that acquisition blocks S1 and forces the S2
  non-geographic fallback.
- Performance implementation awaits unprofiled, equivalence-gated measurement on
  the integrated science candidate.

These blockers limit claims; they do not justify invented values or compatibility
layers.
