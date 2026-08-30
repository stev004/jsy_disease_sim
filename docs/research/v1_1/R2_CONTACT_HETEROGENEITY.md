# R2 — Contact Network Heterogeneity and Mixing

**Programme:** Jersey Outbreak Simulator V1.1 scientific hardening  
**Research lane:** R2  
**Status:** research recommendation; no implementation or calibration  
**Frozen baseline:** `jos-v1.0.0`, commit `9e9ce3abc4201cd8303c723015462d21ca237800`  
**Evidence reviewed:** the V1 scientific audit, technical report and roadmap on `docs/jos-v1-scientific-review`; frozen full-scale pilot `run-20260830T180202Z`; frozen implementation and tests; external sources listed below  
**Literature access date:** 2026-08-30

## 1. Goal, non-goals and decision summary

The goal is to specify the smallest defensible V1.1 correction for H1/N-10 and H3/N-02 while preserving the network contracts already verified in V1. The correction must introduce persistent differences in personal contact opportunity, remove residents of care/medical communal settings from free-living community mixing, make community age mixing reciprocal, and expose diagnostics capable of showing what changed.

This dossier does **not** calibrate Jersey contact behaviour, select a named-pathogen offspring dispersion, redesign transmission weights, add a new route, or repair every adjacent network limitation. In particular, care-staff rotation (N-11), whole-school bridging (N-12), bus topology (N-21), route-intensity identifiability (N-22), cross-parish community movement (N-08), and full contact-matrix validation (C1/C2) remain separately identifiable work.

The preferred H3 design is one persistent, mean-one **gamma activity trait** per agent, drawn once from a dedicated deterministic seed namespace. It changes participation and attainable degree only on existing pooled routes: `community_indoor`, `community_outdoor`, `workplace_transient`, `school_cross_class`, and `bus`. Gamma is preferred because its coefficient of variation maps directly to its shape and Poisson-gamma allocation produces negative-binomial marginal counts. A negative-binomial draw is a realised count, not a persistent trait; an independent daily negative-binomial therefore does not solve H3. Lognormal activity is a scientifically credible sensitivity design, but its more extreme tail is less controlled and there is not enough Jersey evidence to justify making it the sole V1.1 form.

No non-zero numerical activity dispersion is recommended in this research lane. The family is an architectural choice; the numerical dispersion must be fitted or registered as an explicit scenario assumption. `activity_cv = 0` must exist as a compatibility control, but it is not a scientifically hardened H3 default. V1.1 must not claim H3 complete until a non-zero, documented default has been approved in synthesis.

For H1, exclude residents of the care/medical settings already recognised by JOS's care routes from both general community routes. Staff remain eligible and therefore retain a bridge between institutions and the community. Visitors or resident excursions require an explicit, evidence-backed mechanism later; reducing a hidden probability is inferior to an auditable membership exclusion. The roadmap's acceptance phrase “communal-establishment residents” is overbroad if read literally: Jersey's official communal-establishment categories also include hotels/large guest houses, staff accommodation, shelters and detention [15]. Excluding all such residents would be a new scientific assumption unrelated to N-10. Synthesis must correct the acceptance wording to the care/medical predicate or explicitly authorise broader scope.

The contact-activity mechanism below is a scientific architecture recommendation, not yet an implementation-ready H3 specification. It deliberately supplies no pathogen-neutral non-zero dispersion. Synthesis must freeze one application rule, authority layer, caps, deterministic fixtures and tolerances, or classify H3 as partial. Community-matrix reciprocity (`N-07`) and bus topology (`N-21`) are V1.x work and are not implicitly promoted into M11-B.

## 2. Findings addressed and protected contracts

| Finding | Research conclusion |
|---|---|
| H1 / N-10 | Residents of care/medical communal settings currently enter both community routes at free-living rates. Remove them from community membership and all community edge construction. Do not represent isolation merely by assigning a low activity value; do not broaden the exclusion to unrelated communal categories without evidence. |
| H3 / N-02 | Fixed ring degree and clique degree suppress personal contact heterogeneity. Add a persistent activity trait to pooled routes only. |
| N-03 | Add per-agent, per-day aggregate multiplex degree and weighted exposure-opportunity summaries. Keep “edge opportunity” distinct from empirically reported contacts. |
| N-07 | Replace the row-stochastic community assumption with an absolute contact-rate target that is balanced for population reciprocity before edge allocation; report both target and realised matrices. |
| N-08 | UK age matrices cannot determine Jersey parish flows. Preserve same-parish community mixing in V1.1 unless a Jersey mobility source is approved; do not invent a cross-parish fraction. |
| N-11 | Activity does not repair absent care staff-to-staff contact or cohort rotation. These remain separate structural tasks. |
| N-12 | Activity may modulate the existing cross-class pool but does not create across-year or teacher bridge structure. Preserve class-core exclusions. |
| N-21 | A bus clique gives up to degree 23 and prevents activity from controlling degree. H3 on bus therefore requires the N-21 bounded-pairing correction or an explicit temporary deferral. No evidence here supports the audit's illustrative degree 4–6 as a Jersey value. |
| N-22 | Activity changes the number and identity of opportunities, never per-edge `weight`, `beta`, or route multipliers. |
| N-23 | Route attribution remains hazard-weighted bookkeeping among successful simulated candidates. Always publish candidate-count distributions beside route shares. |
| C1 / C2 | V1.1 should create the provenance and diagnostic basis for later empirical network comparison. It must not collapse routes or infer indoor/outdoor risk ratios from contact diaries in R2. |

Protected V1 contracts are: the eleven route identifiers and route-family boundaries; household, class, team, care and transport membership semantics unless explicitly named above; `school_class`/`school_cross_class` and `workplace_team`/`workplace_transient` forbidden-pair exclusions; calendars and work-from-home attendance; deterministic hash-based construction; route-family removal leaving retained route outputs unchanged; immutable M4 artifacts; neutral-intervention exactness; edge weights remaining separate from activity; and route attribution not changing whether an infection occurs.

## 3. Current implementation and frozen-pilot evidence

### 3.1 Network construction

`NetworkGenerationConfig` has schema `1.0` and generator `4.1.1`. Its contact-count defaults are 3 for school cross-class, 3 for workplace transient, 3 for community indoor and 2 for community outdoor. The bus cohort capacity is 24, the regular-community edge fraction is 0.6, and indoor/outdoor edge weights are 0.35/0.15 in the frozen code. The audit text reports outdoor weight 0.18, so the code/report discrepancy should be resolved as provenance work, not silently propagated by R2.

The five broad community age bands are 0–4, 5–17, 18–34, 35–64 and 65+. The configured matrix is row stochastic:

```text
0–4    0.25  0.30  0.25  0.15  0.05
5–17   0.20  0.35  0.25  0.15  0.05
18–34  0.10  0.15  0.45  0.25  0.05
35–64  0.05  0.10  0.20  0.50  0.15
65+    0.05  0.05  0.10  0.30  0.50
```

Rows are validated to sum to one and to permit cross-age contact, but no condition enforces `N_i C_ij = N_j C_ji`. Community target choice is directional and then canonicalised as an undirected edge. Canonicalisation gives reciprocal realised dyads, but it does not turn the input rows into mutually consistent per-capita contact volumes.

Community regular membership is persistent and hash selected (65% indoor, 45% outdoor). With the default 0.6 regular-edge fraction, regular edge persistence is `int(max(7, 0.6 × 30)) = 18` days. Daily participation is hash-Bernoulli by route and date: indoor adult/minor weekday probabilities are 58%/35%, weekend 70%/55%; outdoor adult/minor weekday 28%/20%, weekend 55%/45%. Targets are uniformly chosen from the selected age band within the source's home parish. All agents are currently listed in both community membership pools, including communal residents.

`_ring_edges` gives each source offsets `1..k`; after undirected de-duplication ordinary participants have about `2k` neighbours. School cross-class and workplace transient are rings within their existing pools and explicitly remove class/team pairs. Household, class, team, care-resident cohort, shared-vehicle cohort and bus cohort constructions are clique-like; a bus cohort of 24 gives degree 23. Care staff are assigned to one resident cohort, with no staff-staff ring and no shift rotation. There is no persistent continuous activity multiplier despite a route-spec claim of seeded activity propensity.

Existing diagnostics report per-route degree quantiles, clustering, age mixing and parish shares for selected snapshots. They do not report each agent's total multiplex daily degree or weighted opportunity budget. M4 hashing includes config, route specifications, structural edges, memberships, staffing and selected snapshots. Existing tests already protect determinism, seed sensitivity, valid/unique endpoints, membership boundaries, calendars, WFH, route-family independence, Starsim mapping, M4 provenance, M4 immutability, neutral interventions and candidate-route attribution.

### 3.2 Frozen pilot

The external evidence root is
`/Users/stevenmatson/Documents/JOS_v1_full_scale_evidence/run-20260830T180202Z/`;
these figures are not backed by files on the research branch.

The first full 104,540-person, 180-day run passed the scientific verifier. It used a generic demonstration scenario and is evidence about V1 execution, **not Jersey epidemiology**. Its selected-snapshot unweighted degree diagnostic had mean 12.16, median 9, p90 23, p95 31, p99 42 and maximum 66. Community indoor degree had mean 3.773 and maximum 20; community outdoor mean 1.606 and maximum 15. Workplace-transient participants were concentrated near degree 6. Bus degree reached 23. These compact route-specific distributions are consistent with the designed homogeneity criticised in N-02.

The pilot recorded 294,565 episodes and recurrent waves. Its simulated route shares were led by household (27.36%), community indoor (22.22%), workplace team (19.83%) and school class (15.89%). Only 10,166 infections (3.45%) had multiple successful candidate routes. These figures are baselines for regression comparisons only. They cannot identify an activity distribution, validate contact rates, or establish a real Jersey route share.

## 4. External scientific evidence

### 4.1 Individual heterogeneity, persistence and superspreading

Lloyd-Smith et al. showed that individual infectiousness can be strongly skewed and that incorporating such variation increases early extinction while making established outbreaks rarer but more explosive [1]. That result motivates reporting offspring distributions and extinction, but its negative-binomial dispersion combines contact behaviour, infectiousness, infectious duration and context. A pathogen-specific offspring `k` must not be copied into a pathogen-neutral contact parameter.

A large Great Britain encounter survey found a lognormal body and a heavy tail in reported degree, substantial clustering and degree assortativity; when contact duration and local clustering were represented, extremes in expected secondary cases were damped and realised secondary cases were well described by a negative binomial [2]. This establishes that heterogeneity matters and that degree alone is insufficient. It does not establish that JOS community-only activity has the survey's whole-day coefficient of variation, because the survey also includes work, school, travel and grouped encounters which JOS represents separately.

Persistent and time-varying activity are not interchangeable. Tkachenko et al. distinguish longer-term social connectivity from shorter-lived activity fluctuations and show that time-dependent heterogeneity can create transient epidemic suppression that later wanes [3]. H3 specifically requires a trait drawn once. JOS's existing dated attendance, community participation, calendar and pool re-pairing already supply day variation. The minimal V1.1 design is therefore a persistent trait combined with existing daily stochasticity, not a second autocorrelated activity process.

### 4.2 Why gamma, lognormal and negative binomial mean different things

| Candidate | Strength | Limitation for V1.1 |
|---|---|---|
| Gamma latent activity | Mean-one parameterisation is simple: shape `1/CV²`, scale `CV²`; finite moments; Poisson-gamma count mixing yields a negative-binomial marginal; tail is controllable. | Not the best-fitting form in every encounter dataset and cannot reproduce a power-law tail. |
| Lognormal latent activity | Directly compatible with the lognormal body observed in the GB encounter study; strictly positive and naturally persistent. | Tail and maximum degree are very sensitive to `sigma`; finite pools, de-duplication and caps distort it; it increases performance and validation risk. |
| Negative-binomial daily degree | Discrete, familiar, and directly exposes count overdispersion. | It is an outcome distribution, not a stable personal trait. Independent daily draws erase persistence; a persistent random effect is still required. |
| Empirical quantile table | Can reproduce a chosen survey exactly. | Survey and setting transfer are opaque, tail treatment is arbitrary, and it adds data/version complexity before Jersey evidence exists. |

Gamma is the preferred primary form. Lognormal should be evaluated in a sensitivity analysis against the same filtered UK data before it is rejected permanently. There is no case for supporting multiple runtime families in V1.1 unless synthesis explicitly requires that sensitivity; one implementation plus an offline comparison is the minimal solution.

### 4.3 Age mixing and UK proxy evidence

POLYMOD collected 97,904 contacts from 7,290 participants in eight European countries, including 1,012 UK participants, with age, duration, frequency and location information [4,5]. Strong age assortativity, particularly among school-aged people and young adults, is well established. CoMix subsequently collected 101,350 observations from 19,914 participants reporting 466,710 contacts across 53 weeks in England [6]. Working-age mean contacts varied from 2.39 in lockdown periods to 4.93 in summer 2020, versus 11.41 in the comparable POLYMOD ages; this is direct evidence that matrices and absolute contact totals are policy- and calendar-dependent, not universal constants.

Prem et al. provide setting-specific synthetic matrices for 177 locations, including the UK, and reproduce the main qualitative features of out-of-sample empirical matrices [7]. They are useful as a cross-check, not a reason to prefer a synthetic national total over observed UK POLYMOD records. Reconnect provides a post-pandemic UK comparison with a mean 9.1 daily contacts in late 2024/early 2025 [8]; because it was published after the frozen V1 review and is very recent, it should be a sensitivity comparator, not the sole basis of V1.1.

JOS already represents home, school, work, transport, care, indoor community and outdoor community as distinct routes. Importing a POLYMOD or Prem **all-location** matrix into each community route would count household, school, workplace and transport mixing twice. The defensible proxy is therefore the UK POLYMOD pattern after excluding home, school, workplace and transport reports, retaining leisure/other-location contacts only under a documented mutually exclusive location rule. If the records cannot be assigned uniquely, ambiguous multi-location contacts must be excluded or allocated by a prespecified rule and reported. The filtered pattern can inform age allocation; it does not identify JOS edge weights, indoor/outdoor attenuation, regular-edge fraction or total contact budget.

Survey matrices must be population reciprocal: total contacts reported from group `i` to `j` should equal those from `j` to `i`, `N_i C_ij = N_j C_ji`. Imbalanced matrices can bias reproduction numbers, subgroup cumulative incidence and targeted-intervention effects [9]. Reciprocal balancing and residual reporting are therefore acceptance conditions, not optional polish.

### 4.4 Schools, workplaces, care and geography

Proximity data from a primary school show dense within-class structure with measurable school-level mixing [10]. Multi-day high-school data show stable class-level matrices alongside renewal in individuals' neighbours [11]. Those observations support retaining persistent classes and a lighter dynamic cross-class layer; they do not support replacing school routes with an undifferentiated age matrix.

Workplace contact studies find that research-group membership, role, shared projects and physical distance predict contacts, and that organisational structure improves epidemic simulation [12]. JOS's stable workplace team plus transient worksite pool is therefore a reasonable qualitative decomposition. Personal activity belongs on the transient layer; changing the team clique or inventing cross-site encounters is not required for H3.

The UK CONTACT feasibility study instrumented residents and staff inside four care homes, concentrating location markers in communal lounges, dining rooms, bedrooms and staff/service areas [13]. Although it does not estimate general-community participation, it supports treating the home as an explicit contact setting. Staff and visitors are distinct bridge populations. It does not justify free-living community edges for residents or a numeric excursion probability. Jersey's 2021 Census counted 2,079 residents in all communal establishments but only 957 in care homes with or without nursing; the remainder span categories with very different community access [15]. That primary Jersey evidence rules out using “communal” as a scientific synonym for “care-home resident.”

Routine commuter movement and random movement can produce materially different spatial epidemic dynamics [14]. JOS already contains explicit work-parish and transport bridges. In the absence of Jersey community origin-destination evidence, replacing same-parish community mixing with random cross-parish targets would be less defensible than retaining the known limitation.

## 5. Candidate designs

### Candidate A — activity changes participation only

Map activity through a bounded participation probability while retaining fixed ring degrees for participants. This is cheap and protects pairing code, but high-activity agents cannot have higher degree once participating, so saturation is severe and the mechanism chiefly changes days present. It does not adequately address ring homogeneity.

### Candidate B — activity changes degree only

Keep existing eligibility draws and allocate a route-specific target degree proportional to activity. This gives clearer degree variance but leaves low-activity agents present as often as high-activity agents and can waste target stubs through duplicates or finite-pool caps.

### Candidate C — persistent activity controls both participation and degree (preferred)

Use one activity trait across pooled routes. Translate it through route-specific, mean-preserving opportunity allocation: a higher trait increases the probability of non-zero participation and the number of desired partner stubs, subject to existing route eligibility, attendance, calendar, pool and degree caps. Pair stubs as unordered edges, respecting reciprocal age-pair totals and nested-route exclusions. This best represents stable sociability while existing daily hashes provide day variation.

### Candidate D — route-specific activity traits

Draw separate community, work, school and transport traits, optionally correlated. This may be more realistic but introduces several dispersions and correlations with no Jersey evidence. It is not necessary to close H3 and should be rejected for V1.1.

## 6. Preferred design in detail

### 6.1 Trait definition and deterministic identity

For each agent `i`, draw once:

```text
A_i ~ Gamma(shape = 1 / c², scale = c²),  E[A_i] = 1,  CV[A_i] = c
```

where `c = activity_cv`. At `c = 0`, set every `A_i = 1` without entering a random sampler. Key the deterministic draw only on `(network_seed, "persistent-contact-activity", agent_id, distribution_version)`. Do not include route, date, scenario, intervention or process order. Store or reproducibly materialise the trait at M4 construction; it is not a disease characteristic.

Normalise draws once over all applicable agents to exact island mean one, and report both pre- and post-normalisation moments. Route/day allocation should additionally normalise the eligible agents' propensities when preserving a route budget; this avoids age, attendance or residence composition causing an unintended change in the route's mean opportunity count.

`activity_cv` requires a finite upper guard for operational safety, but clipping individual draws would change the declared distribution. Prefer a validated parameter bound plus route/pool degree caps and report the fraction of requested stubs lost to caps, duplicates, exclusions and small pools. If clipping is unavoidable, it becomes part of the declared model and its clipped mass must be reported.

### 6.2 Route inheritance

| Route | Inherit personal activity? | Reason |
|---|---:|---|
| `household` | No | Household membership is authoritative; sociability should not remove co-residence opportunity. |
| `school_class` | No | Stable class core is protected. |
| `school_cross_class` | Yes | It is a discretionary pooled bridge; retain class-pair exclusion and existing school/year scope. |
| `workplace_team` | No | Stable organisational core is protected. |
| `workplace_transient` | Yes | It is the pooled worksite layer; retain team-pair exclusion, WFH and attendance. |
| `care_resident` | No | Bounded institutional cohort is protected; H1 changes community membership, not care degree. |
| `care_staff` | No | Activity would not repair missing staff-staff/rotation structure. |
| `shared_vehicle` | No | A realised small co-travel group is not a discretionary contact budget. |
| `bus` | Yes, only with N-21 pairing correction | Clique degree overrides activity. Preserve exact commute/time cohort but use bounded activity-weighted pairing. |
| `community_indoor` | Yes | Core H3 setting. |
| `community_outdoor` | Yes | Core H3 setting. |

Sharing one trait across these routes is a declared structural assumption: stable sociability is positively correlated across discretionary settings. Eligibility remains route-specific, so a child cannot acquire workplace contacts and a non-commuter cannot acquire bus contacts merely by having high activity.

### 6.3 Mean-preserving pooled edge allocation

The generator should operate on desired **undirected opportunity stubs**, not multiply hazards:

1. Form the exact V1 eligible pool after residence exclusion, calendar, attendance, commute, school and route membership rules.
2. Derive each eligible person's propensity from `A_i` and the route's existing participation/contact budget. Preserve the route/day expected total by normalising propensities over that eligible pool.
3. Allocate integer stubs with a deterministic, mean-preserving method (for example, floor plus hash-ranked largest remainder, or a keyed count draw followed by exact budget reconciliation).
4. For community, allocate reciprocal age-band pair totals first. Within each band pair, choose endpoints proportional to remaining stubs. For school/work/bus, pair only inside the existing pool.
5. Canonicalise unordered pairs and enforce self-edge, duplicate, nested-pair and degree-cap rules during matching, rather than silently relying on final de-duplication.
6. Report requested and realised stubs, rejected attempts, saturation and achieved degree by activity quantile.

The exact matching algorithm is an implementation choice, but it must have one authoritative construction path. Adding an alternative heterogeneous network beside the old builder would violate route-family independence and invite divergent bug fixes.

### 6.4 Community matrix transformation

The preferred V1.1 community age target is derived by a versioned offline transformation:

1. Pin the POLYMOD dataset version and checksums [5]. The cited record currently publishes MD5 `25f259c5a7548d5adb89b8808b7b3c66` for `2008_Mossong_POLYMOD_contact_common.csv`; the derivation must also record a locally computed SHA-256. Select UK participants and apply documented survey weights/day-type handling.
2. Select only contacts assigned uniquely to leisure or other non-home, non-school, non-work, non-transport locations. Publish included/excluded record counts and treatment of group and multi-location reports.
3. Estimate fine-age per-capita contact rates, then aggregate to JOS's five bands using the V1.1 Jersey population counts. Do not average already normalised rows.
4. Balance totals with `T_ij = (N_i C_ij + N_j C_ji) / 2`, then recover `C*_ij = T_ij / N_i`. This guarantees `N_i C*_ij = N_j C*_ji` subject to floating-point tolerance.
5. Scale the whole balanced matrix by one scalar so its population-weighted mean matches the separately approved JOS **community opportunity budget**. Preserve the age pattern; do not infer absolute edge count or beta from the survey in the same step.
6. Use the balanced totals to allocate unordered band-pair edge quotas. Publish raw, filtered, aggregated, balanced, scaled and realised matrices plus reciprocity residuals.
7. Compare the resulting pattern with Prem UK “other locations,” CoMix unrestricted/school-open periods where suitable, and Reconnect. These are sensitivity checks, not pooled pseudo-replications.

Both community routes may share the age pattern initially, but this is a declared simplification. The evidence does not identify separate indoor/outdoor matrices or their transmission-weight ratio. Their absolute budgets, persistence fraction and weights remain outside R2 unless synthesis commissions explicit work.

### 6.5 Care, parish, school, workplace and bus consequences

- **Care/medical residents:** map each resident's `care_setting_id` to the M2 setting type and reuse the authoritative `_is_care_setting` classification already used to construct care routes. Exclude only residents for whom that predicate is true. Assert zero indoor and outdoor community incidence for them at membership and edge levels. Staff stay eligible. Other communal categories retain current eligibility unless separately researched. A later visitor/excursion model should use explicit identities and dates, not restore generic community participation.
- **Parish:** retain same-home-parish community targeting for the preferred V1.1 design. If synthesis demands configuration capacity, a cross-parish matrix may be added only with a zero default and `scenario_assumption` provenance; it must be symmetric in total flows. There is no R2 evidence for a non-zero Jersey value.
- **School:** activity changes `school_cross_class` opportunity only. N-12 across-year and teacher bridging requires its own evidence and should, if later approved, remain within the existing cross-class route with subcategory diagnostics rather than introduce an indistinguishable second school bridge.
- **Workplace:** activity changes only `workplace_transient`; team edges and physical-attendance rules remain unchanged. Do not generate cross-worksite contacts except from explicit multiple-job membership.
- **Bus:** replace the cohort clique with a bounded activity-weighted pair generator before claiming bus inheritance. Keep commute origin, destination, time band, cohort membership and calendar fixed. The contact cap/budget needs an evidence or scenario classification; this dossier supplies no Jersey number.

## 7. Parameter and provenance strategy

| Item | Evidence class and required record |
|---|---|
| Gamma family and mean-one parameterisation | `structural_assumption`, supported by [2,3] and the count-mixture rationale; record formula and version. |
| `activity_cv` | `literature_prior` only if estimated by the registered filtered-data pipeline; otherwise `scenario_assumption`. Never derive it from pathogen offspring `k`. Record estimate, uncertainty, fitting population/settings and transfer caveat. |
| Shared trait across pooled routes | `structural_assumption`; record inherited-route list explicitly. |
| POLYMOD filtered community matrix | `literature_prior` / `geographic_proxy`; record article DOI, dataset DOI, file checksum, retrieval date, filters, survey weights, age aggregation, Jersey population artifact hash, balancing and scaling code hash. |
| CoMix, Prem and Reconnect comparisons | `external_validation_reference`; record exact wave/setting selection and dataset version. |
| Same-parish default | Existing `structural_assumption`, retained because no Jersey origin-destination evidence was found. |
| Communal-resident exclusion | Model-logic correction mandated by H1; record residence predicate and counts excluded by setting type. |
| Route opportunity budgets and caps | Preserve existing values initially as `structural_assumption`; do not relabel as observed contacts. Any changed number needs its own evidence decision. |

M4 configuration and logical provenance must include the activity family/version, CV, seed namespace, inherited routes, matrix identifier/hash, community residence exclusion predicate, matching algorithm version and any cap. Outputs must record realised trait moments/quantiles and the loss from requested to realised opportunity stubs.

The term **contact** must be qualified. JOS edge weights are relative daily exposure opportunities and are not separately identified from transmissibility. Diagnostics should report both unweighted incident edge opportunities and weighted opportunity budget, not claim either is a directly observed contact count. Matrix comparisons must state their mapping from diary contact to JOS edge.

## 8. Risks and mitigations

| Risk | Consequence | Mitigation |
|---|---|---|
| Confusing offspring `k` with activity dispersion | Named-pathogen biology leaks into a generic contact model. | Fit activity only to contact/network evidence; analyse offspring after H4 jointly. |
| Mean inflation | Heterogeneity changes both mean and variance, obscuring interpretation. | Exact stub-budget reconciliation and homogeneous comparator. |
| Finite-pool saturation and duplicate collapse | High `A_i` fails to produce high realised degree, especially in schools/buses. | Match without replacement, cap explicitly, and report requested/realised ratio by activity quantile. |
| Double counting external settings | Household/school/work/transport mixing is imported again through community. | Setting-filter raw records before aggregation; never import an all-location matrix wholesale. |
| Non-reciprocal target matrix | Age-specific incidence and interventions are biased. | Balance total contacts before pairing and report residuals. |
| Care isolation becomes absolute realism claim | Resident visits/excursions disappear. | State that H1 is the bounded V1.1 correction; future explicit visitor/excursion mechanism remains unresolved. |
| One trait creates excessive cross-route correlation | Same agents dominate all pooled routes. | Report cross-route degree correlations; retain route-specific eligibility; assess lognormal/gamma sensitivity offline. |
| Bus clique masks H3 | Activity parameter appears ineffective on bus. | Couple bus inheritance to N-21 bounded pairing or explicitly defer it. |
| Heterogeneity changes performance | Heavy tails increase matching retries and memory. | Deterministic caps, attempt limits with failure diagnostics, CI/scaled tests and short full-mode snapshots. |
| Route-share changes are overinterpreted | Attribution remains model bookkeeping and weights remain uncalibrated. | Publish successful-candidate counts and call shares “simulated pathway attribution.” |
| Compatibility path becomes a second implementation | V1 and V1.1 builders diverge. | One builder; `CV=0` is a parameter branch in allocation, not a legacy pipeline. |

## 9. Exact, testable acceptance criteria

These criteria are deliberately separable so a green epidemic run cannot conceal a broken network contract.

### 9.1 Protected-contract regression

1. For a fixed seed/configuration, two complete M4 builds have byte-identical route edge tables, memberships, trait table/derivation and logical hashes.
2. A checked `activity_cv = 0` comparison against frozen V1 lists every changed route, edge count and degree summary. Every difference must be attributable to one approved change: H1 membership exclusion, N-07 reciprocal community allocation, replacement of a pooled ring by the one authoritative opportunity matcher, or a separately approved N-21 bus correction. Zero changes are allowed in non-inheriting routes. This is a classified scientific baseline, not a claim that intentional topology corrections are byte compatible.
3. Changing `activity_cv` changes no edge in the six non-inheriting routes. The test compares canonical tables exactly.
4. Removing any route family leaves all retained route edge tables byte-identical for the same configuration.
5. `school_class`/`school_cross_class` and `workplace_team`/`workplace_transient` forbidden overlaps are zero on every configured snapshot, not only the baseline date.
6. Existing M4 immutability, neutral-intervention equality, Starsim mapping and route-attribution invariance tests continue to pass.

### 9.2 Trait and pooled-network behaviour

7. For `activity_cv = 0`, every stored or recomputed `A_i` equals exactly 1. For a non-zero fixed test configuration, every agent's trait is identical across routes, dates and repeated materialisations, changes when the network seed changes, and matches an independently recomputed keyed draw.
8. The post-normalisation full-population activity mean equals 1 within `1e-12`. At 104,540 agents and the approved non-zero default, `|realised CV - configured CV| <= max(0.01, 0.02 × configured CV)`; the exact realised value is stored and must match an independent deterministic recomputation.
9. On each inheriting route with at least 100 eligible agents and non-zero budget, mean realised degree in the highest activity quartile exceeds that in the lowest quartile on every tested active day. The diagnostic also reports Spearman correlation, requested stubs and realised stubs.
10. For each inherited route/day, the total realised stub budget differs by no more than 1% from its `activity_cv = 0` comparator unless a finite-pool/cap diagnostic accounts for the complete difference. At full population the aggregate difference across inherited routes is no more than 0.5%.
11. With a non-zero activity CV, the variance of aggregate inherited-route daily degree exceeds the `CV=0` comparator while its mean satisfies criterion 10. Multiplex degree and weighted-budget summaries report mean, median, p90, p95, p99 and maximum by age band, day type, residence type and activity quintile.
12. Requested-to-realised stub loss is reported separately for self-pair avoidance, duplicate avoidance, nested exclusions, caps and pool exhaustion; no silent loss category is permitted.

### 9.3 Care and mixing correctness

13. Every resident whose M2 setting satisfies the authoritative care/medical predicate is absent from both community membership tables. Across every selected snapshot there are exactly zero `community_indoor` or `community_outdoor` edges incident on such a resident. Diagnostics give eligible, excluded, participating and incident-edge counts for **every** communal setting type and for free-living residents, so accidental exclusion of non-care communal categories is visible. Staff are not excluded merely because they work in care.
14. For the transformed target matrix, `max_ij |N_i C_ij - N_j C_ji| / max(1, N_i C_ij + N_j C_ji) <= 1e-12`. Raw and balanced residuals are both archived.
15. Every realised community edge is undirected and counted once. Its realised band-pair total differs from the deterministic integer target by at most the fully enumerated matching shortfall; an unexplained residual is a build failure.
16. The matrix build artifact records the POLYMOD file checksum shown by the pinned dataset, UK sample/filter counts, setting inclusion/exclusion, treatment of multi-location and group contacts, survey/day weighting, five-band aggregation, Jersey population hash, balancing, scaling and transformation code hash. Re-running it produces the same matrix and hash.
17. In the preferred V1.1 configuration, every community edge has equal home parishes. If future cross-parish mixing is enabled, total parish flows obey the same reciprocity rule and the non-zero source is registered; a scalar “plausible” fraction is not acceptable evidence.

### 9.4 Epidemiological response and reporting

18. A deterministic ensemble of at least 1,000 small single-index simulations, with disease parameters and mean network opportunity budget held fixed, reports per-index secondary cases, zero-secondary fraction, mean, variance, variance-to-mean ratio and fitted negative-binomial dispersion with uncertainty for `CV=0` and the approved non-zero activity CV. In a purpose-built susceptible toy fixture where only pooled contacts transmit, the non-zero configuration must have greater secondary-case variance and a different extinction fraction than `CV=0`; this is a mechanism test, not validation of Jersey.
19. The same report states that full-model offspring dispersion also depends on natural-history heterogeneity (H4), susceptibility, edge weights, repeated/clustering structure and interventions. No contact-only run may be labelled calibrated superspreading.
20. Every route-share table includes the successful-candidate-route-count distribution and uses “simulated pathway attribution” or equivalent language.
21. A short full-population contact-only build over the configured snapshots completes within a synthesis-approved resource envelope and reports runtime/peak memory against frozen V1. No 180-day full epidemic is required for R2 acceptance.

Criteria 8, 10 and 18 require synthesis to fix the tested non-zero CV and resource/ensemble fixture before implementation starts. Their thresholds are verification tolerances, not scientific uncertainty intervals.

## 10. Implementation implications

The minimal likely file ownership is:

- `network_schemas.py`: activity CV (and only if approved, family/version and bounded bus contact budget); reciprocal matrix representation or external matrix identifier; strict validation.
- `network_generator.py`: persistent keyed trait; care/medical-resident membership predicate using the existing setting classification; a single activity-aware pooled matcher; reciprocal community band-pair allocation; inherited-route integration; no edits to hazard weights.
- `network_artifacts.py` / schema-facing artifact code: trait or derivation provenance, target/realised matrices, stub-loss and multiplex diagnostics, content hashes.
- Network tests: exact H1 historical regression, persistence/mean/variance response, inherited-route boundaries, reciprocity, family independence and `CV=0` compatibility.
- Targeted epidemic diagnostics/tests: secondary-case and extinction response without a full-wave run.
- Evidence registry/data derivation: a pinned, reproducible POLYMOD transformation artifact. Do not make runtime network generation download or parse the external survey.

The new matcher is justified only because the existing ring is the authoritative source of N-02. It should replace pooled ring construction for the five named routes, not coexist as a second model. Fixed routes and their current builders should remain untouched. Implementation should land the care membership filter and activity/mixing work in reviewable commits, but integration must verify their combined effect because removing communal residents changes eligible-pool normalisation.

Before code changes, run the relevant frozen network tests. Add only the regressions required by Section 9. Use CI/scaled populations for most checks, one deterministic full-mode M4 build for distribution/residence criteria, and short single-index ensembles for mechanism response. Passing tests must be followed by inspection of matching, hashing and provenance logic.

## 11. Unresolved questions for synthesis

1. What non-zero `activity_cv` and uncertainty are approved as the shipped generic default? A fit to filtered UK data is required if it is to be `literature_prior`; otherwise it must be labelled `scenario_assumption`.
2. Should the offline fit compare gamma and lognormal by out-of-sample predictive performance before gamma is finalised, or is gamma's simpler operational contract sufficient for V1.1?
3. Will synthesis correct “communal-establishment residents” in the roadmap acceptance to “residents of care/medical communal settings”? This dossier recommends that correction because H1/N-10 concerns care homes, while Jersey's official communal category also includes hotels, staff accommodation, shelters and detention [15]. Broader exclusion requires separate evidence and authorisation.
4. What is the authoritative JOS community opportunity budget after the setting-filtered matrix is derived? The current 3/2 per-source constructions are structural assumptions, not survey-matched contacts.
5. How are POLYMOD contacts with multiple reported locations and group contacts to be mapped without double counting? The rule must be frozen before deriving a matrix.
6. Should weekday and weekend community matrices differ in V1.1, or should the existing participation probabilities remain the only day-type modulation?
7. Is bus N-21 in the same implementation milestone as H3? If not, bus must be explicitly excluded from the initial inheritance list and H3 scope disclosed as partial.
8. What bounded bus contact budget is approved? Neither UK diary data nor this lane provides a Jersey-specific within-vehicle degree.
9. Is same-parish community mixing acceptable for V1.1 with a visible N-08 limitation, or will a Jersey mobility research source be commissioned? R2 recommends no non-zero guessed fraction.
10. Does storing one trait per agent in M4 outweigh recomputing it from a versioned deterministic key? Storage improves auditability; derivation reduces artifact size. Either way the logical hash must cover it.
11. Should activity affect regular-community membership, daily contacts, or both through a unified opportunity allocator? Candidate C recommends both, but exact mean-preserving semantics must be agreed before code.
12. What degree or stub cap provides an operational guard without materially truncating the approved activity distribution? This must be evaluated from the fitted distribution and full-mode pool sizes.
13. Will whole-school teacher/across-year bridges (N-12) and care staff rotation (N-11) be implemented concurrently? They must not be claimed as consequences of H3.
14. Which downstream V1 baseline changes are expected from H1 alone, so the `CV=0` compatibility diff can classify every changed edge without normalising unintended drift?

## 12. References

All links were accessed 2026-08-30.

1. Lloyd-Smith JO, Schreiber SJ, Kopp PE, Getz WM. “Superspreading and the effect of individual variation on disease emergence.” *Nature* 438, 355–359 (2005). [https://doi.org/10.1038/nature04153](https://doi.org/10.1038/nature04153).
2. Danon L, House TA, Read JM, Keeling MJ. “Social encounter networks: collective properties and disease transmission.” *Journal of the Royal Society Interface* 9, 2826–2833 (2012). [https://doi.org/10.1098/rsif.2012.0357](https://doi.org/10.1098/rsif.2012.0357).
3. Tkachenko AV et al. “Time-dependent heterogeneity leads to transient suppression of the COVID-19 epidemic, not herd immunity.” *PNAS* 118 (2021). [https://doi.org/10.1073/pnas.2015972118](https://doi.org/10.1073/pnas.2015972118).
4. Mossong J et al. “Social contacts and mixing patterns relevant to the spread of infectious diseases.” *PLOS Medicine* 5:e74 (2008). [https://doi.org/10.1371/journal.pmed.0050074](https://doi.org/10.1371/journal.pmed.0050074).
5. Mossong J et al. “POLYMOD social contact data.” Zenodo dataset, versioned record and file checksums. [https://doi.org/10.5281/zenodo.1215899](https://doi.org/10.5281/zenodo.1215899).
6. Gimma A et al. “Changes in social contacts in England during the COVID-19 pandemic between March 2020 and March 2021 as measured by the CoMix survey.” *PLOS Medicine* 19:e1003907 (2022). [https://doi.org/10.1371/journal.pmed.1003907](https://doi.org/10.1371/journal.pmed.1003907).
7. Prem K et al. “Projecting contact matrices in 177 geographical regions: an update and comparison with empirical data for the COVID-19 era.” *PLOS Computational Biology* 17:e1009098 (2021). [https://doi.org/10.1371/journal.pcbi.1009098](https://doi.org/10.1371/journal.pcbi.1009098); code/data [https://doi.org/10.5281/zenodo.4889500](https://doi.org/10.5281/zenodo.4889500).
8. Goodfellow C et al. “Social contact patterns in the United Kingdom following the COVID-19 pandemic: The Reconnect cross-sectional survey.” *PLOS Medicine* 23:e1005038 (2026). [https://doi.org/10.1371/journal.pmed.1005038](https://doi.org/10.1371/journal.pmed.1005038).
9. Hamilton MA, Knight J, Mishra S. “Examining the influence of imbalanced social contact matrices in epidemic models.” *American Journal of Epidemiology* 193, 339–347 (2024). [https://doi.org/10.1093/aje/kwad185](https://doi.org/10.1093/aje/kwad185).
10. Stehlé J et al. “High-resolution measurements of face-to-face contact patterns in a primary school.” *PLOS ONE* 6:e23176 (2011). [https://doi.org/10.1371/journal.pone.0023176](https://doi.org/10.1371/journal.pone.0023176).
11. Fournet J, Barrat A. “Contact patterns among high school students.” *PLOS ONE* 9:e107878 (2014). [https://doi.org/10.1371/journal.pone.0107878](https://doi.org/10.1371/journal.pone.0107878).
12. Potter GE, Smieszek T, Sailer K. “Modeling workplace contact networks: the effects of organizational structure, architecture, and reporting errors on epidemic predictions.” *Network Science* 3, 298–325 (2015). [https://doi.org/10.1017/nws.2015.22](https://doi.org/10.1017/nws.2015.22).
13. Thompson CA et al. “CONTACT: a non-randomised feasibility study of bluetooth-enabled wearables for contact tracing in UK care homes during the COVID-19 pandemic.” *Pilot and Feasibility Studies* 10:125 (2024). [https://doi.org/10.1186/s40814-024-01549-6](https://doi.org/10.1186/s40814-024-01549-6).
14. Danon L, House T, Keeling MJ. “The role of routine versus random movements on the spread of disease in Great Britain.” *Epidemics* 1, 250–258 (2009). [https://doi.org/10.1016/j.epidem.2009.11.002](https://doi.org/10.1016/j.epidem.2009.11.002).
15. Statistics Jersey. “Report on the 2021 Jersey Census — Chapter 4: Households and housing,” communal establishments table 4.12 (2022). Primary official statistics. [https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/R%20CensusFinalReport%2020221213%20SJ.pdf](https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/R%20CensusFinalReport%2020221213%20SJ.pdf).
