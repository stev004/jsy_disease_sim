# R1 — Natural history, observation timing, and adherence

**Status:** research dossier for V1.1 synthesis; not an implementation specification  
**Research date:** 30 August 2026  
**Primary audit findings:** `D-01`, `O-02`, `I-01`  
**Interacting findings:** `D-02`, `D-03`, `I-02`, `I-04`, `E-01`

## Scope and decision boundary

This dossier asks what the smallest scientifically defensible V1.1 design is for variable natural-history durations, symptom-onset timing, and persistent individual adherence. It also records the implications for isolation, generation-interval diagnostics, and the frozen pilot's 30-day full-susceptibility waning assumption.

It does **not** choose or calibrate a named pathogen, claim Jersey-specific natural-history values, add parameter-uncertainty propagation, add behavioural substitution, redesign vaccination, or implement partial immunity. A distribution family can be selected generically; a scientifically consequential numeric mean or shape cannot be made pathogen-neutral by calling it a default.

Definitions used here follow WHO's distinction: latent period is infection to becoming infectious; incubation period is infection to first symptoms; infectious duration is independent of symptom status; generation interval is infection of a primary case to infection of a secondary case ([WHO influenza investigation protocol](https://cdn.who.int/media/docs/default-source/unity-studies/230811-who_whe_unity_studies_g1_closed-setting-protocol_100823_lc_web.pdf?sfvrsn=f87e38a1_3), accessed 30 August 2026). “Acceptance” means agreeing or being selected to undertake an intervention; “adherence” means carrying out the accepted intervention; “route effect” is the resulting conditional reduction on a named contact route. These are separate model quantities.

## Audit findings addressed

| Finding ID | Evidence class | Finding and consequence | R1 disposition |
|---|---|---|---|
| **R1-F01** (`D-01`) | **Repository evidence** | Latent, infectious, and immune durations are deterministic. This suppresses individual variation and changes epidemic persistence, peak shape, extinction, and intervention timing. | Replace the scalar-only duration contract with explicit distributions parameterised by mean and coefficient of variation (CV); retain `constant` only as an explicit comparison family. |
| **R1-F02** (`O-02`) | **Repository evidence** | Observation onset is anchored to infection date. In the shipped demo its zero onset and detection delays permit detection before the fixed two-day latent period ends; isolation starts the following day and can precede infectiousness. | Make symptom onset a natural-history time and let observation consume it. Require positive onset after infection in the no-presymptomatic demo and validate chronology against infectious start. |
| **R1-F03** (`I-01`) | **Repository evidence** | The adherence draw is keyed by route, so a person can adhere on one route and not another. Detection-triggered acceptance is keyed by detection date, so reinfection can redraw it. The fully non-adherent tail is consequently removed or reduced. | Draw one Bernoulli adherence value per intervention/person and reuse it across routes and dates. Keep route effects deterministic conditional on that value. |
| **R1-F04** (`D-02`, `O-02`) | **Repository evidence + scientific evidence** | Only the `I` state transmits, with constant relative infectiousness. Symptoms are currently an observation label, so the model cannot represent a consistent presymptomatic phase or symptom-linked isolation. | Establish an optional, explicitly parameterised presymptomatic interval and infectivity profile, but do not enable either with invented generic values. Symptom status/onset must be shared natural-history state. |
| **R1-F05** (`D-03`) | **Repository and frozen-pilot evidence** | Recovery followed by 30 days of complete protection returns an agent to full susceptibility. In the 180-day pilot, repeat infection was central to the trajectory. | Disable short full-susceptibility waning in the generic V1.1 demonstration unless it is explicitly selected as a sensitivity scenario; do not silently “improve” it by distributing the same 30-day mean. |
| **R1-F06** (`I-02`, `I-04`) | **Repository evidence** | Route multipliers are attenuation-only and vaccine uptake already has separate acceptance logic. | Preserve attenuation-only route semantics and vaccine-uptake semantics. Persistent NPI adherence must not be overloaded to represent substitution, dose acceptance, or biological vaccine effect. |
| **R1-F07** (`E-01`) | **Repository evidence** | Current replicate bands sample process randomness, not uncertainty in duration means, shapes, adherence, or ascertainment. | Record parameter status and source. Report stochastic variation as such; do not call it parameter or total uncertainty. |
| **R1-F08** | **Peer-reviewed evidence** | Non-exponential and non-deterministic dwell-time shapes materially change epidemic dynamics and inferred control effects. | Distribution shape is a first-class parameter, independent of the mean, rather than an implementation detail. |
| **R1-F09** | **Peer-reviewed evidence + modelling inference** | Generation intervals arise from latent duration, time-varying infectiousness, contact opportunity, depletion, and network context. They are not identical to a configured stage duration. | Persist source episode identity and report the realised event-derived distribution separately from configured natural-history quantities. |
| **R1-F10** | **Behavioural evidence + modelling assumption** | Longitudinal studies show both stable between-person heterogeneity and within-person/contextual change in protective behaviour. | A stable Bernoulli trait is a justified minimal correction to independent route draws, not a claim that real adherence is immutable or binary. Dynamic adherence is deferred. |

## Current implementation and frozen evidence

### Authoritative implementation

- `src/jersey_outbreak/outbreak_schemas.py` represents each natural-history quantity as one scalar `ParameterEntry`; current allowed provenance statuses include `observed`, `derived`, `literature_prior`, `calibrated`, and `scenario_assumption`.
- `src/jersey_outbreak/respiratory.py` converts all three duration scalars to Starsim constant distributions. For each infection it schedules `ti_infected = ti + latent`, `ti_recovered = ti_infected + infectious`, and, when waning is enabled, `ti_susceptible = ti_recovered + immunity`. Only the infectious state transmits and relative infectiousness is flat.
- `src/jersey_outbreak/observation_scheduler.py` samples symptom onset from infection date, then detection from onset or infection, and reporting from detection. Offline and online observation share the scheduler, a protected contract.
- `src/jersey_outbreak/observation.py` validates only `infection <= onset <= detection <= report`; it does not compare onset or detection with the disease transition to infectiousness.
- `src/jersey_outbreak/interventions.py` keys route adherence by `(run seed, intervention, route, agent)` and detection acceptance additionally by detection date. Case isolation and quarantine become effective no earlier than the day after detection, a protected no-retrocausality rule.
- Existing tests prove constant transition timing, deterministic replay, observation reconciliation, offline/online agreement, neutral-scenario equality, and intervention start ordering. They do not prove nonzero duration variation, onset relative to infectiousness, exact source-episode generation intervals, or persistent cross-route adherence.

The following existing contracts are protected unless synthesis explicitly changes them: one authoritative transmission engine; exact route separation; observation offline/online agreement; no retrocausal intervention effect; neutral-scenario exact latent equivalence; state/event reconciliation; travel-slot event identity; deterministic hashes; evidence-class semantics; and pathogen-neutral claims.

### Frozen full-population pilot

The frozen external evidence used here is
`/Users/stevenmatson/Documents/JOS_v1_full_scale_evidence/run-20260830T180202Z/`.
It is V1 execution evidence, not repository content or epidemiological evidence.

The frozen run at commit `9e9ce3abc4201cd8303c723015462d21ca237800` used 104,540 residents, 180 days, fixed 2-day latency, fixed 5-day infectiousness, and 30-day full-protection immunity followed by complete susceptibility. It produced 294,565 infection episodes in 99,041 people (94.74% ever infected), or 2.818 episodes per resident. It ended with 20,380 infectious residents during a further upswing. These are simulated outputs from declared demonstration assumptions, not Jersey epidemiology.

The event graph yielded 294,555 resolved local generation intervals: 2–6 days, mean 3.652, SD 1.384, with counts `{2: 80,818; 3: 68,630; 4: 57,503; 5: 47,490; 6: 40,114}`. This corrects the audit report's literal “point mass” wording. Fixed stages did **not** create a point-mass realised generation interval because transmission could occur on different infectious days. They did create a mechanically bounded interval whose shape is driven by fixed transition times, flat infectiousness, and realised contact opportunity. The post-hoc derivation also inferred each infector's latest earlier episode; it did not persist exact source-episode identity.

## External scientific evidence

### Duration distributions

**R1-E01 — Evidence.** Lloyd showed that replacing exponentially distributed infectious periods with more realistic, less dispersed distributions changes oscillatory behaviour and increases the critical community size for persistence ([Theoretical Population Biology, 2001, DOI 10.1006/tpbi.2001.1525](https://pubmed.ncbi.nlm.nih.gov/11589638/), accessed 30 August 2026).

**R1-E02 — Evidence.** Wearing, Rohani, and Keeling showed that inappropriate exponentially distributed latent and infectious periods can bias estimates of reproductive number and the projected effect of controls; their staged/gamma formulation separates the mean from distribution shape ([PLOS Medicine, 2005, DOI 10.1371/journal.pmed.0020174](https://journals.plos.org/plosmedicine/article?id=10.1371%2Fjournal.pmed.0020174), accessed 30 August 2026).

**R1-E03 — Evidence.** Krylova and Earn found that realistic latent- and infectious-period shapes alter transient and long-term epidemic dynamics, supporting explicit distribution shape rather than a fixed-duration shortcut ([Journal of the Royal Society Interface, 2013, DOI 10.1098/rsif.2013.0098](https://pubmed.ncbi.nlm.nih.gov/23676892/), accessed 30 August 2026).

Gamma, lognormal, and empirical discrete distributions can all be scientifically legitimate. Gamma is the best generic core representation because mean and CV are direct, positive-support parameters; the exponential is the special case CV=1 and the deterministic limit is approached as CV tends to zero. Lognormal is useful when evidence supports a heavier right tail, but it is not generically superior. An empirical discrete distribution is preferable when a named-pathogen study supplies a validated probability mass function. A phase-type/Erlang construction is computationally natural, but integer stage counts are an unnecessarily restrictive public parameterisation for this task.

**R1-A01 — Assumption.** Selecting gamma as the initial non-constant family is an engineering/scientific-interface choice, not evidence that all respiratory natural histories are gamma-distributed. No source reviewed supports one pathogen-neutral numeric CV. Therefore V1.1 must require an explicit CV with provenance; it must not hide a value such as 0.5 in code.

### Onset, presymptomatic transmission, and generation intervals

**R1-E04 — Evidence.** WHO defines latency and incubation as different clocks; infectiousness can begin before symptoms, so symptom onset cannot safely be treated as “infection plus observation delay” ([WHO contact-tracing glossary](https://www.ncbi.nlm.nih.gov/books/NBK611568/?report=reader), accessed 30 August 2026; [WHO influenza protocol](https://cdn.who.int/media/docs/default-source/unity-studies/230811-who_whe_unity_studies_g1_closed-setting-protocol_100823_lc_web.pdf?sfvrsn=f87e38a1_3), accessed 30 August 2026).

**R1-E05 — Evidence.** Svensson derived how generation-time distributions depend on latent and infectious periods and the infectiousness function, and distinguished generation time from serial interval ([Mathematical Biosciences, 2007, DOI 10.1016/j.mbs.2006.10.010](https://www.sciencedirect.com/science/article/pii/S0025556406002094), accessed 30 August 2026).

**R1-E06 — Evidence.** Champredon, Dushoff, and Earn distinguished intrinsic from realised generation intervals: competition for susceptible contacts and epidemic context change the realised interval even with a fixed intrinsic profile ([Proceedings of the Royal Society B, 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4707754/), accessed 30 August 2026).

**R1-A02 — Assumption.** The smallest generic architecture needed for `D-02` is a nonnegative presymptomatic duration between infectious start and symptom onset plus an explicit relative-infectiousness profile. It does not justify enabling presymptomatic transmission or assigning its length or relative weight in a generic demo. Named-pathogen evidence must supply those values.

### Adherence

**R1-E07 — Evidence.** A longitudinal study of 51,600 UK adults found large between-person correlations in self-reported compliance and some within-person change associated with context and confidence; it also warns that self-report, nonrepresentative recruitment, and a generic compliance item limit interpretation ([Scientific Reports, 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7907734/), accessed 30 August 2026).

**R1-E08 — Evidence.** A longitudinal study of 800 participants across six context-specific protective behaviours found both between-person variation and behaviour/context-specific habit formation; prior intention and habitual repetition predicted later adherence ([British Journal of Health Psychology, 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9392502/), accessed 30 August 2026).

**R1-A03 — Assumption/proxy.** A single stable Bernoulli draw per intervention/person is a deliberately coarse proxy for persistent behavioural heterogeneity. It repairs the current route-wise redraw and restores a fully non-adherent tail. It does not represent graded adherence, fatigue, capability, enforcement, household correlation, or time-varying motivation.

## Candidate designs

### Natural-history duration representation

| Candidate | Merits | Scientific/implementation cost | Disposition |
|---|---|---|---|
| Constant only | Exact V1 behaviour; simple | Fails `D-01`; suppresses variation | Retain only as an explicit comparator and legacy evidence reproducer. |
| **Gamma, parameterised by mean and CV** | Positive support; mean/shape separated; exponential and near-fixed regimes expressible; common in epidemic models | Requires explicit discretisation and CV provenance | **Preferred initial V1.1 family.** |
| Lognormal, mean and CV | Positive, heavier right tail; useful for some pathogen evidence | Tail can dominate finite simulations; no generic basis to prefer it | Permit only if low-cost in the schema/runtime; otherwise defer to named-pathogen extension. |
| Empirical discrete PMF | Closest to a published named-pathogen estimate; matches daily time step | Requires curated, pathogen-specific data and versioned bins | Future named-pathogen option, not generic demo. |
| Erlang stages | Efficient Markov approximation; shape controlled by stage count | Integer-only shape; exposes engine mechanism as science interface | Do not make the public V1.1 contract. |

The configuration should express `family`, `mean_days`, and `cv` for gamma/lognormal, and `family: constant` plus `mean_days` for the comparator. Validation must reject missing or nonpositive means and reject missing, zero, or nonpositive CV for non-constant families. Continuous draws on a one-day time step need one documented conversion rule; the existing comparison with daily time indices effectively advances on the first time index at or after the sampled transition. That rule must be tested, not changed incidentally.

### Symptom-onset architecture

1. **Current observation-relative onset:** keep onset as an observation draw from infection. Rejected because it can precede disease progression and cannot consistently drive symptom-linked transmission.
2. **Clamp onset to infectious start:** minimal surface patch. Rejected because clamping distorts the configured distribution and hides invalid parameters.
3. **Natural-history onset with optional presymptomatic phase:** disease progression samples symptom status and, for symptomatic episodes, a nonnegative duration from infectious start to symptom onset. Observation consumes the resulting time. This is preferred because it makes the chronology authoritative and creates one future-compatible hook for `D-02` without supplying pathogen-specific values.

In the V1.1 generic no-presymptomatic mode, the presymptomatic duration is explicitly zero; because latent duration is strictly positive, symptom onset is strictly after infection and coincides with first infectiousness. An explicitly configured presymptomatic mode may give a positive duration and a separate pre-/post-onset infectivity profile. Asymptomatic episodes have no symptom-onset time. Detection can still be symptom-anchored or infection-anchored, but a symptom anchor is invalid for an asymptomatic episode.

### Adherence architecture

1. **Independent route draws:** current design; rejected.
2. **One continuous propensity plus route thresholds:** richer but introduces an unvalidated latent scale and unnecessary mechanics; defer.
3. **One Bernoulli draw per `(run seed, intervention identity/version, agent)` reused for all active dates and routes:** preferred minimal correction. The configured probability `a` implies an expected adherent fraction `a` and fully non-adherent fraction `1-a`. Route multipliers then describe the effect *given adherence*, not additional chances to adhere.

Detection is an observation outcome; accepting an isolation instruction is an intervention behaviour. For detection-triggered isolation, the acceptance/adherence draw must not include detection date or infection episode. The same person's trait persists across repeated detections for that intervention version. A policy change that should legitimately redraw behaviour must use a new intervention version/identity. Vaccine `uptake_probability` remains its own stable campaign-person draw and is not routed through this NPI trait.

## Preferred design

1. Add an explicit versioned duration specification with `constant` and `gamma` as the required families. Use mean and CV; do not use a shape-only API that entangles mean and shape. Lognormal may be included only if it adds no second execution path; it is not needed to satisfy V1.1.
2. Require every non-constant stage CV to be explicit and provenance-labelled. Do not choose a hidden generic numeric CV. The synthesis decision must either select a clearly labelled scenario CV and require sensitivity runs, or leave the shipped demo constant while exercising nonzero-CV fixtures and a separate illustrative scenario.
3. Sample duration per infection episode using a deterministic episode-specific stream/key. A reinfection of the same resident must be allowed a different draw; adding unrelated agents or observation events must not perturb an existing episode's draw.
4. Make symptom status and onset part of the natural-history episode. Record infection, infectious-start, symptom-onset (nullable), recovery, and waning times on the event. Observation consumes these values and never resamples symptom status/onset.
5. In the no-presymptomatic generic mode, use zero presymptomatic duration so onset is at infectious start and positive after infection. Support a positive presymptomatic duration and explicit phase profile only as an opt-in parameterised architecture; assign no pathogen-neutral values.
6. Persist infection episode ID and exact source episode ID at transmission time. Derive realised generation intervals directly from those IDs and infection times, not by guessing the infector's latest earlier episode.
7. Draw NPI adherence once per intervention/person and reuse it across all dates and routes. Apply route-specific effects only conditional on that draw. Preserve next-day activation and attenuation-only semantics.
8. Make generic demonstration waning disabled by default. Keep complete return to susceptibility only as an explicitly labelled sensitivity scenario until a separately approved partial-immunity design exists.

This is the minimum root-cause design. A clamp, a route-level correlation patch, or randomising the existing 30-day immunity value would preserve the authoritative defects rather than fix them.

## Parameter and provenance strategy

Every parameter record should contain: canonical name; semantic definition and anchor; units; distribution family; mean; CV where applicable; allowed range; status (`observed`, `derived`, `literature_prior`, `calibrated`, `scenario_assumption`); source ID/version; access date; transformation/rounding rule; and whether parameter-uncertainty sensitivity is required.

Required semantic names are `latent_duration` (infection to infectious start), `infectious_duration` (infectious start to recovery), `presymptomatic_duration` (infectious start to symptom onset for symptomatic episodes), `symptomatic_probability`, and, only when enabled, phase-specific relative infectiousness. “Incubation” must not be used for latency. Immune protection must say whether it is sterilising and what susceptibility becomes after waning.

Evidence classes must remain honest:

- The literature establishes the need for variable shapes and the distinction among clocks: **evidence**.
- Gamma as the generic interface and Bernoulli stable adherence are **model-design assumptions**.
- The pilot generation interval is **simulated evidence about current model mechanics**, not epidemiological evidence.
- Generic means, CVs, symptom probability, presymptomatic duration, phase weights, adherence probabilities, and 30-day waning remain **scenario assumptions** until named evidence or calibration supports them.
- Replicate quantiles conditional on one parameter vector are **stochastic intervals**, not confidence, credible, parameter, or total uncertainty intervals (`E-01`).

## Risks and interactions

- **Discrete-time bias:** positive continuous draws are rounded by daily transitions. A documented rule can shift means; report configured continuous and realised discrete summaries separately.
- **Episode identity:** UID-only random keys can repeat a person's duration on reinfection. Key by stable episode identity and verify travel-slot reuse.
- **Ordering:** the current local-event callback records observation before prognosis is set. Moving onset into natural history requires a deliberate lifecycle order while preserving event reconciliation and no same-day intervention effect.
- **Calibration confounding:** changing duration shape changes growth and peak behaviour even at unchanged mean and beta. Beta must not be silently retuned to conceal this; compare before/after and record any later calibration.
- **Isolation optimism:** onset at infectious start removes the current pre-infectious detection artefact, but flat post-onset infectiousness and no behavioural substitution can still overstate isolation effects (`D-02`, `I-02`).
- **Adherence overconfidence:** stable binary adherence is more coherent than route draws but still omits time/context change. Scenario language must call it a trait proxy.
- **Vaccination:** stable NPI adherence must not alter current vaccine uptake or the `I-04` susceptible-only protection limitation.
- **Waning:** a distribution around 30 days would retain the biologically consequential full-reset assumption. Disabling generic waning is safer than cosmetic randomisation; partial protection is a separate `D-03` milestone.
- **Performance:** non-constant sampling and added event fields must be benchmarked at full population, but scientific semantics take priority over premature vectorisation.

## Testable acceptance criteria

These criteria are exact enough to become implementation tests. They do not select unresolved numeric scientific parameters.

| ID | Acceptance criterion |
|---|---|
| **R1-AC01** | A V1.1 non-constant duration config without `family`, `mean_days`, or a strictly positive `cv` fails schema validation with the offending field named; `family: constant` rejects any nonzero shape field. |
| **R1-AC02** | For at least 10,000 independently keyed episode draws from a fixed gamma fixture with declared mean `m` and CV `c>0`, realised unrounded draws have sample CV greater than zero and mean and CV within a predeclared deterministic Monte Carlo tolerance computed for that fixture. The test tolerance and seed are fixed before execution. |
| **R1-AC03** | Under one fixed run seed, repeating the same episode set reproduces every duration bit-for-bit; adding an unrelated observation event or an unrelated higher-ID agent does not change any pre-existing episode's duration; a reinfection episode has its own key. |
| **R1-AC04** | With the constant comparator and otherwise neutral V1 inputs, disease transition dates and the V1 projection of V1.1 event rows remain exactly equal to the frozen comparator fixture. A versioned V1.1 event/hash schema may add fields; its full hash is expected to differ, while an explicit projection comparator proves preservation of V1 scientific fields. |
| **R1-AC05** | Every symptomatic event satisfies `infection_time < infectious_start <= symptom_onset <= recovery` in no-presymptomatic mode; every asymptomatic event has `symptom_onset = null`. A fixture that attempts zero-delay onset from infection while latency is positive is rejected or normalised through the natural-history anchor, never recorded before infectious start. |
| **R1-AC06** | In an explicitly enabled presymptomatic fixture, at least one episode satisfies `infectious_start < symptom_onset`; transmission is possible in that interval only when the configured pre-onset relative-infectiousness value is positive. With that value zero, a paired seeded run records no presymptomatic transmissions. |
| **R1-AC07** | Offline reconstruction and online observation produce identical symptom status, onset, detection, reporting dates, event IDs, and observation bundle hash for the same outbreak artefact/config. Observation code does not independently draw symptom status or onset. |
| **R1-AC08** | Every local infection event stores a source episode ID that resolves to exactly one prior infection event for the infector; reported generation interval equals `infectee infection time - source episode infection time`. Seeds/imports have no source episode ID and are excluded from the local distribution denominator. |
| **R1-AC09** | A nontrivial transmission fixture reports realised generation-interval `n`, mean, SD, CV, median, IQR, minimum, maximum, and discrete counts. With a nonzero-CV stage fixture, the realised generation-interval CV is nonzero. Output labels it “realised simulated generation interval.” |
| **R1-AC10** | For `N=100,000` agents and adherence `a=0.60`, exactly one stored Bernoulli result is used per intervention/person across all dates and routes; the observed fully non-adherent fraction lies within the predeclared binomial 99.9% interval around `0.40`. No route-specific redraw occurs. |
| **R1-AC11** | Repeating detection of the same person under the same intervention identity returns the same isolation-adherence result; changing only detection date, route iteration order, or episode ID does not change it; changing intervention version/identity may do so. |
| **R1-AC12** | For a fully non-adherent target, every route multiplier remains neutral (`1.0`). For an adherent target, each configured route effect is applied according to existing endpoint and route semantics. Intervention effects still begin no earlier than the day after detection. |
| **R1-AC13** | Vaccine uptake results and neutral-scenario hashes are unchanged by the NPI adherence change, proving `I-04`/campaign acceptance was not accidentally coupled to the new trait. |
| **R1-AC14** | The generic V1.1 demonstration has waning disabled, or its run manifest explicitly labels complete waning as a scenario assumption and emits a high-visibility warning when the horizon reaches the first possible full-susceptibility return. |
| **R1-AC15** | A 180-day sensitivity reproducing fixed 30-day full waning reports both infection episodes per resident and unique-ever-infected fraction; it cannot label episodes/resident as attack rate. |
| **R1-AC16** | Provenance output exposes family, mean, CV, anchor semantics, status, source, and discretisation for every duration; it contains no named-pathogen claim for a generic scenario. Ensemble output states that bands condition on the supplied parameter vector. |

Before adding any regression test, the implementation plan should map it to one or more criteria above. Existing tests should be extended where they already own the contract; no second test framework or parallel scheduler is warranted.

## Implementation implications

Likely affected areas, subject to synthesis approval:

- `src/jersey_outbreak/outbreak_schemas.py` and disease YAML: versioned duration schema and provenance validation.
- `src/jersey_outbreak/respiratory.py`: episode-specific draws, symptom state/onset, optional pre-onset phase/profile, and generic waning default.
- Event schema/artifact writer: natural-history transition times and, only if synthesis proves it necessary, exact source episode identity. Any added fields require explicit artefact/hash versioning and a V1 projection comparator rather than an impossible unchanged full-row hash.
- `src/jersey_outbreak/observation_scheduler.py` and `src/jersey_outbreak/observation.py`: consume natural-history symptom fields and validate chronology relative to infectious start while retaining the one shared scheduling path.
- `src/jersey_outbreak/interventions.py` and intervention schema: one NPI intervention/person draw; keep route effects, vaccine acceptance, and next-day activation separate.
- Diagnostics: configured-versus-realised stage durations and exact realised generation intervals.
- Focused tests: outbreak timing/distributions, observation online/offline reconciliation, intervention trait persistence, source-episode identity, neutral equivalence, and one full-population performance comparison.

The lifecycle issue is material: current local infection recording precedes prognosis scheduling. Implementation must make the natural-history episode authoritative before observation consumes it, without duplicating disease logic in the observation layer.

## Unresolved questions for synthesis

1. Will V1.1 ship a non-constant illustrative scenario with an explicitly labelled numeric CV, or retain the generic demo constant while the architecture/tests demonstrate gamma? Research supplies no pathogen-neutral numeric CV.
2. Is optional presymptomatic transmission in V1.1 scope, or should V1.1 only establish natural-history onset and defer the profile implementation? No numeric generic phase duration or weight should be invented either way.
3. Should lognormal be supported now for schema completeness, or deferred until a named-pathogen source requires it? Gamma plus constant is sufficient for the current acceptance criteria.
4. Does changing generic demonstration waning to disabled receive explicit approval? If not, the existing 30-day full reset must be retained only with an unavoidable scenario warning and sensitivity reporting.
5. Should `adherence` be renamed to `acceptance_probability` for detection-triggered interventions in a schema-version change, or retained with clarified semantics? The underlying stable key is not optional.
6. Is symptom status allowed to move into the disease artefact now? This is the clean root-cause fix for `O-02`/`O-03`, but it changes an existing schema and may alter observation hashes by design.
7. What deterministic Monte Carlo tolerances will be frozen for distribution and adherence tests before implementation? They must not be tuned after seeing results.
8. Will source episode identity be added to the event schema in V1.1, or will the current post-hoc “latest earlier episode” diagnostic remain explicitly approximate until a later schema milestone?

## Source register

All web sources were accessed 30 August 2026.

| ID | Source | Role |
|---|---|---|
| R1-S01 | [Lloyd, *Realistic distributions of infectious periods in epidemic models*, 2001](https://pubmed.ncbi.nlm.nih.gov/11589638/) | Peer-reviewed duration-shape evidence. |
| R1-S02 | [Wearing, Rohani & Keeling, *Appropriate Models for the Management of Infectious Diseases*, 2005](https://journals.plos.org/plosmedicine/article?id=10.1371%2Fjournal.pmed.0020174) | Peer-reviewed gamma/stage-shape and inference evidence. |
| R1-S03 | [Krylova & Earn, *Effects of the infectious period distribution on predicted transitions in childhood disease dynamics*, 2013](https://pubmed.ncbi.nlm.nih.gov/23676892/) | Peer-reviewed transient/long-run shape evidence. |
| R1-S04 | [Svensson, *A note on generation times in epidemic models*, 2007](https://www.sciencedirect.com/science/article/pii/S0025556406002094) | Peer-reviewed generation-time theory. |
| R1-S05 | [Champredon, Dushoff & Earn, *Intrinsic and realized generation intervals in infectious-disease transmission*, 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4707754/) | Peer-reviewed intrinsic/realised distinction. |
| R1-S06 | [WHO guideline on contact tracing, glossary](https://www.ncbi.nlm.nih.gov/books/NBK611568/?report=reader) | Authoritative timing terminology. |
| R1-S07 | [WHO influenza investigation protocol](https://cdn.who.int/media/docs/default-source/unity-studies/230811-who_whe_unity_studies_g1_closed-setting-protocol_100823_lc_web.pdf?sfvrsn=f87e38a1_3) | Authoritative definitions and relationship of epidemiological intervals. |
| R1-S08 | [Wright, Steptoe & Fancourt, longitudinal UK compliance study, 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7907734/) | Peer-reviewed evidence for heterogeneity/change and measurement caveats. |
| R1-S09 | [Zhang et al., longitudinal habit/adherence study, 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9392502/) | Peer-reviewed behaviour/context persistence evidence. |
| R1-S10 | Frozen local evidence: `JOS_V1_FULL_SCALE_PILOT.md` and `RUN_PLAN.md`, run `run-20260830T180202Z` | Verified evidence about current model behaviour only. |
