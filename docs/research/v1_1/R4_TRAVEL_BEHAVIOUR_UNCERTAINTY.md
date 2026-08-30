# R4 — Travel, behaviour and uncertainty

**Status:** research complete for the V1.1 scientific-hardening programme  
**Evidence cut-off and access date:** 2026-08-30  
**Scope:** immediate defects `T-11` and `T-12`; evidence/design for `T-03`, `T-08`, `T-13`, `T-14`, `T-15`, `T-19`, `T-20`, `T-21`, `T-23`, `T-24`, `T-28`, `E-01`, `E-02`, and `E-03`.

## 1. Decision summary

The immediate fixes are lifecycle corrections, not calibration:

1. **Resident presence must be derived from all trip intervals on every simulated day.** The plan already has the correct interval predicate; runtime state does not apply absences that begin within the horizon (`T-11`).
2. **Trip identity must own trip-scoped state.** Person-keyed runtime maps and “processed person” sets collapse repeat returns (`T-12`). A resident can own multiple non-overlapping trip episodes.

The strongest empirical travel improvement is now directly available: Visit Jersey publishes a monthly passenger-arrivals archive by air and sea. It should replace the invented seasonality profile. That series counts **movements** and combines visitors with returning residents. Visitor Volume Survey (VVS) estimates can separately constrain the visitor/resident split, trip purpose, mode and length of stay, with survey uncertainty and a 2025 methodology break retained.

The preferred scientific design is therefore:

- preserve observed movement volume and mode/month totals at every population scale;
- model parties first, then let members inherit party accommodation, stay and local transport;
- make visitor–resident opportunity counts proportional to participating visitors with explicit caps;
- carry infection age/time-since-exposure, not only a disease compartment, into arrival testing;
- promote all travel contact weights and arrival prevalence to provenance-bearing sensitivity parameters;
- distinguish stochastic replicate variation, parameter uncertainty and structural alternatives in outputs;
- refuse 2.5/97.5 empirical quantiles when fewer than 40 successful replicates exist, and always label what a band contains.

No passenger manifests, movement records, immigration data, patient data, test records, or other restricted/personal data were requested or used.

## 2. Evidence classification and interpretive boundary

- **Observed Jersey evidence** is an official Jersey administrative series or weighted Jersey survey. Administrative passenger totals count journeys, not unique people; survey estimates have sampling error.
- **Peer-reviewed proxy/mechanism evidence** supports model form (for example, sensitivity varying with time since exposure). Disease-specific literature does not define a generic-respiratory default.
- **Structural assumptions** include contact opportunity, infection time abroad when origin incidence is absent, within-month daily allocation, party composition, and prior distributions. They must be configurable and sensitivity-tested.

These classes must not be merged in a single unlabelled “calibrated” parameter set.

## 3. Current V1 implementation and frozen evidence

### 3.1 Travel generation and lifecycle

`TravelConfig` contains annual air/ferry arrivals, default `stream_scale=0.001`, a fixed 90% visitor/10% returner split, fixed day-visitor/host fractions, a single stay mean/jitter, a synthetic party-size distribution, fixed contact counts, uniform arrival disease-state fractions, and a single scalar arrival-test sensitivity (default 1.0).

`generate_travel_episodes()` correctly partitions person movements into homogeneous visitor/returner parties and prevents overlapping return episodes at generation time. However, visitor party members independently draw accommodation, parish, transport and stay jitter. Hotel supply is 32 synthetic units per parish selected through household geography. Visitor age is generated uniformly from 1–90.

The plan's daily stream computes resident absence correctly from `absence_start_date <= day < return_date`. `TravelManager` computes presence only at construction for the start date, then adds returners on arrival. It never removes a resident whose absence starts later. Consequently planned and runtime away counts disagree and the resident remains in contact routes (`T-11`).

Runtime episode lookup is `{person_id: episode}` and arrivals are deduplicated by a `processed_arrival_people` set. A repeated resident identity therefore overwrites one episode and suppresses or invalidates the next trip; scheduled-test identity checks can raise (`T-12`). Existing tests cover an absence already in progress at run start, so they do not reproduce the historical in-horizon defect.

Returning acquisition is drawn on the return callback and immediately calls `set_prognoses()`. It has no exposure date abroad. The returner is therefore susceptible until arrival and, if infected, begins a full latent period on Jersey (`T-15`). The arrival test then treats exposed and infectious identically with the configured constant sensitivity, allowing a just-acquired infection to be detected at sensitivity 1.0 (`T-14`).

### 3.2 Contact and provenance behaviour

Resident mixing pools are absolute per route-day: four terminal residents and three residents per parish/community route under defaults, independent of visitor volume. Airport and ferry terminal pools both use St Helier. Current hard-coded pre-intervention edge weights are 0.30 terminal, 0.60 party, 0.55 accommodation, 0.80 host household, 0.35 bus transit, 0.25 taxi/car/host-pickup transit, 0.35 community indoor and 0.18 community outdoor. These literals directly multiply transmission but do not all appear as named provenance parameters (`T-13`, `T-20`).

Arrival infectious/exposed/recovered fractions are common to all modes, origins and months. Since volume times infection prevalence is the imported visitor signal, this free dial dominates conclusions (`T-19`). Traveller vaccination is generated for visitor slots only; returning residents are not covered by that M8 mechanism (`T-28`).

### 3.3 Ensemble behaviour

`EnsembleConfig` allows one seed and defaults to linear empirical 2.5/97.5 quantiles. The only validation is `lower <= upper`; a two-replicate unit test deliberately returns interpolated values. The ensemble changes network, transmission and observation random streams but retains one M2 population and one parameter vector (`E-01`, `E-02`).

`compare_ensembles()` retains per-seed differences but emits no aggregate median or quantiles of paired differences (`E-03`). Matching seed integers is useful pairing, but event-stream consumption diverges after scenarios change events. It is not a guarantee that all later random draws are common random numbers.

### 3.4 Frozen pilot implications

The frozen V1.0 full-population pilot was a single 180-day no-travel run with fixed generic parameters. It verified artifact integrity and exposed operational cost (9,953 seconds wall time and 2.16 GiB peak RSS). A projected 30-replicate full-scale ensemble was 82.94 hours sequential or an optimistic 22.12 hours with four workers. It supplies **no travel calibration and no uncertainty distribution**. Its recommendation to move full-scale ensembles to a desktop is directly relevant to the feasibility of nested parameter/stochastic designs.

## 4. Observed Jersey travel and visitor evidence

### 4.1 Annual and monthly movement volume (`T-03`, `T-08`)

The current Government open-data resource publishes annual arrivals by air and sea and describes them as passenger movements, not unique visitors. V1 uses the 2025 values 720,842 air plus 196,623 sea, total 917,465, equivalent to 8.776 arrivals per 104,540 residents per year ([Government of Jersey passenger statistics](https://opendata.gov.je/dataset/2da64802-1281-429e-8506-1d568e488d22), [total-arrivals resource](https://opendata.gov.je/dataset/passenger-statistics/resource/dcc8a6c2-152a-48c0-b24b-de1774354d3c), accessed 2026-08-30). The resource metadata says figures are rounded to the nearest thousand even though V1 stores unit-level constants; implementation must reconcile that provenance discrepancy rather than imply unwarranted precision.

Visit Jersey maintains a complete **monthly passenger arrivals** archive for 2025 and later, split across air and sea routes and including scheduled, charter, private plane, cruise and yacht arrivals as documented. It includes visitors and returning residents and excludes transit passengers ([Monthly Passenger Arrivals](https://business.jersey.com/research-trends/tourism-statistics/monthly-passenger-arrivals/), accessed 2026-08-30).

**Evidence implication.** `T-08` no longer needs an invented monthly curve. Freeze the 12 latest-revised 2025 reports/export, retain mode and coverage, and reconcile their annual sum to the selected annual source. If only monthly totals are available, spreading a month uniformly across its days is a structural assumption, not observed daily seasonality.

### 4.2 Visitor versus resident movements and length of stay

The VVS surveys departing passengers and is weighted to total passenger volumes. It identifies passenger type, group size, travel mode, purpose, origin and nights stayed; the detailed Visitor Experience Survey adds demographics and accommodation. Visit Jersey reports more than 40,000 VVS interviews annually and estimated monthly sampling error below 1.5%, but all estimates remain revisable ([Visitor Statistics Methodology](https://business.jersey.com/research-trends/tourism-statistics/methodology/), accessed 2026-08-30).

The VVS definition excludes Jersey residents, transit passengers, seasonal workers and stays over 60 days from “visitors.” Published monthly releases distinguish visits from passengers and explicitly state that repeated trips count repeatedly. For example, January 2025 estimated 14,200 visits, 40,600 departing passengers, 35% visitors among passengers, and 4.9 nights average stay ([January 2025 VVS](https://business.jersey.com/research-trends/tourism-statistics/visitor-figures/visitor-volume-statistics-jan-25/), accessed 2026-08-30). These are illustrative monthly estimates, not constants.

The Exit Survey weighting changed in January 2025, and 2025 values are not directly comparable with earlier years; Jan–May 2025 totals were revised by about 1% in June 2026 ([About the data](https://business.jersey.com/research-trends/tourism-statistics/visitor-figures/about-the-data/), accessed 2026-08-30).

**Evidence implication.** Use one coherent methodology vintage, preferably the latest revised 2025 tables, for monthly visitor fraction, purpose, mode, day/overnight share and stay. Do not use the current constant 0.90 visitor fraction as if observed. Passenger arrivals and visitor estimates remain different evidence streams.

### 4.3 Visitor demographics and party behaviour (`T-21`, `T-24`)

The 2023 Travel Survey reports adult visitor ages by purpose. For leisure visitors the published shares are 4%, 7%, 13%, 22%, 28%, 20% and 7% across ages 16–24, 25–34, 35–44, 45–54, 55–64, 65–74 and 75+; it also reports that 13% of adult visitors travelled with a child under 16. Profiles differ materially for business, visiting friends/relatives and other trips ([Annual Travel Survey 2023](https://cdn.jersey.com/images/v1715334523/Trade/Annual-Passenger-Exit-Survey-2023-V9-for-website/Annual-Passenger-Exit-Survey-2023-V9-for-website.pdf), accessed 2026-08-30).

The current survey programme collects group size, and the detailed survey collects demographics and accommodation. Public aggregate releases do not fully identify within-party age relationships or prove that every interviewed “group” shares one accommodation booking. Co-location is nevertheless a much more defensible structural assumption than independent member accommodation draws.

**Evidence implication.** Use purpose-specific adult age bands and an observed child-accompaniment margin. Draw uniformly within a published band only as a recorded interpolation assumption. Construct household-like party templates (solo adult, adult pair/group, adults with children) and sensitivity-test the unobserved within-party relationships.

### 4.4 Accommodation (`T-23`)

In 2023 Jersey had 118 registered visitor-accommodation premises and 9,313 bed spaces: 47 hotels/6,548 spaces, 27 guest houses/628, 37 self-catering/1,212, two hostels/186 and five campsites/739 ([Government of Jersey tourism statistics](https://www.gov.je/industry/retailhospitality/visitoreconomy/pages/tourism.aspx), accessed 2026-08-30). The annual tourism dataset is downloadable ([annual tourism data](https://opendata.gov.je/dataset/tourism-statistics/resource/59c9f0d6-1620-4424-a724-3d61aed32f7f), accessed 2026-08-30). Airbnb is not required to register, so Government does not hold a complete stock ([visitor-bed FOI](https://www.gov.je/Government/FreedomOfInformation/pages/foi.aspx?ReportID=7057), accessed 2026-08-30).

The 2023 survey estimated accommodation used by overnight visitors as 69% hotel, 16% friends/relatives, 5% self-catering, 5% guest house, 3% Airbnb, 1% camping and 1% other (rounding applies) ([Annual Travel Survey 2023](https://cdn.jersey.com/images/v1715334523/Trade/Annual-Passenger-Exit-Survey-2023-V9-for-website/Annual-Passenger-Exit-Survey-2023-V9-for-website.pdf), accessed 2026-08-30).

No authoritative island-wide **bedspaces by parish** aggregate was located. Census “Accommodation Type by Parish” concerns resident dwellings and must not be repurposed as tourist stock.

**Evidence implication.** Constrain accommodation type and capacity island-wide now. A parish distribution requires either an aggregate export from the public registered-premises directory or an explicit assumed distribution. Household counts are not an acceptable proxy.

### 4.5 Arrival infection prevalence and external acquisition (`T-15`, `T-19`)

No pathogen-neutral Jersey observation can determine the proportion of arrivals exposed or infectious. It depends on pathogen, origin, date, vaccination/immunity, trip duration, traveller selection and testing policy. The public VVS collects origin category and purpose, which can define strata, but it contains no infection status.

**Evidence implication.** Arrival prevalence is necessarily a disease-specific scenario or calibrated input. It must vary by at least month, traveller class and mode/origin where evidence supports that resolution, and results must be presented over a declared low/base/high range or probability distribution. Visitor infection state and returning-resident acquisition need an infection-age distribution, not independent compartment fractions with no exposure time.

## 5. Peer-reviewed mechanism evidence — not generic defaults

Kucirka et al. estimated strongly time-varying RT-PCR false-negative probability after SARS-CoV-2 exposure, with very poor detection early after infection ([Annals of Internal Medicine, 2020, DOI 10.7326/M20-1495](https://doi.org/10.7326/M20-1495), accessed 2026-08-30). Johansson et al. modelled travel testing and found optimal timing changes with when exposure occurred and whether quarantine is used ([BMC Medicine, 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8043777/), accessed 2026-08-30). A separate within-host modelling study explicitly combined temporal test sensitivity, incubation and infectious periods for incoming travellers ([Quilty et al./RKI study, 2021, PubMed 33899034](https://pubmed.ncbi.nlm.nih.gov/33899034/), accessed 2026-08-30).

These studies establish the **model form** required by `T-14`: sensitivity is conditional on assay and time since infection/exposure. Their SARS-CoV-2 estimates must not become the default for the generic `respiratory-demo` pathogen.

For paired simulation, common random numbers can reduce variance when paired outcomes are positively correlated, but effectiveness depends on how random processes are coupled ([Yang & Nelson, 1991](https://doi.org/10.1287/opre.39.4.583), accessed 2026-08-30). JOS's seed matching is therefore a useful design, not proof of persistent coupling after scenario-dependent event divergence.

## 6. Candidate designs and preferred design

### 6.1 Immediate corrections

#### S4 / `T-11`: resident absence lifecycle

Candidates:

- add a one-off “absence started” callback;
- recompute present/away sets daily from the existing interval predicate.

**Preferred:** before networks/transmission on every date, derive the complete present/away partition from all resident trip intervals. Apply set differences atomically, emit one departure/return event per trip transition, and build active route endpoints/denominators from that authoritative partition. Keep biological alive/dead state conceptually distinct from on-island presence. If the engine uses `people.alive` as an active mask, verify explicitly whether disease clocks should progress during absence; do not reset a resident's disease state merely because they leave the island.

#### S5 / `T-12`: repeated trips

**Preferred:** key episode-scoped lookup, test, quarantine, processed-arrival and identity state by unique `trip_id`/episode identity. Maintain a secondary `resident_id -> ordered trip_ids` index for presence queries. Person-scoped biological state remains keyed by resident ID. Reject overlapping intervals for one resident unless explicit overlap semantics are later designed; allow any number of non-overlapping returns.

### 6.2 Volume, seasonality and mixing

#### `T-03`, `T-08`: scale and monthly stream

**Preferred:** normalize the latest-revised 2025 monthly passenger-arrivals table by `{month, mode}`. For a synthetic resident fraction `s = simulated_residents / 104540`, set the annual movement target to deterministic rounded source movements × `s`, then allocate integers across month/mode/day by largest remainder. Default `stream_scale` must be derived from the population scale, not independently set to 0.001. Explicit scenario multipliers apply after the representative scale and are reported separately.

Emit:

- movements per resident-year, annualized for partial horizons;
- visitor arrivals per resident-year and returning-resident returns per resident-year;
- visitor person-days / resident present person-days;
- temporary-edge visitor endpoints / resident endpoints;
- source-scale, population-scale and intervention multipliers.

#### `T-13`: volume-responsive mixing

Candidates include a mass-action pool, fixed degree per visitor, or an empirically fitted contact kernel. No Jersey contact survey currently identifies the last.

**Preferred:** for each route-day, select resident partners at `ceil(participating_visitors × resident_partners_per_visitor)`, bounded by a named cap and available residents; construct edges so mean resident endpoints per participating visitor remains stable as volume changes until the declared cap binds. Use St Peter residents for Jersey Airport and St Helier for the ferry terminal, with optional wider catchment weights. Report cap-binding days. “Contacts” remain synthetic opportunities unless an empirical contact source is added.

### 6.3 Infection timing and border testing

#### `T-14`, `T-15`

**Preferred generic interface:** every infected arrival carries `exposure_date` or `infection_age_days`. Returning acquisitions sample exposure during `[absence_start, return)` from a declared daily hazard; visitor imported states sample infection age conditional on their arrival state. A named-pathogen parameter set supplies `P(test positive | assay, specimen, infection_age)` and natural-history stage timing. The generic respiratory demonstration either uses an explicitly synthetic curve with prominent labelling or disables policy-effect claims.

Arrival testing queries that curve at sample time. Specificity remains separate. Delayed results retain episode identity even after visitor departure, with “detected” and “actionable” reported separately. Infection acquired just before return must have low early sensitivity under a curve that says so, and can become infectious according to its already elapsed disease time rather than starting a new full latent period on Jersey.

### 6.4 Visitor composition, accommodation and contact weights

| Findings | Preferred design | Status |
|---|---|---|
| `T-19` | Stratum-specific arrival prevalence/infection-age scenarios by month, traveller type and mode/origin; sweep or sample distributions and show results as a function of them. | Disease-specific assumption until surveillance/calibration. |
| `T-20` | Promote every literal route weight and participation probability to named `TravelConfig` parameters with units, source class, bounds, sensitivity-required flag and resolved provenance. | Structural assumption. |
| `T-21` | Draw party type/size once; all members inherit trip, accommodation ID/type/parish, departure/stay and party-compatible transport. Draw ages/sex from purpose-specific party templates. | Jersey margins + structural within-party relationships. |
| `T-23` | Match observed island accommodation-type mix and public capacity. Use a frozen public premises/parish aggregate when available; otherwise publish assumed parish weights. Never allocate by resident household counts. | Jersey island total; parish unresolved. |
| `T-24` | Use Jersey purpose-specific adult age bands and child-accompaniment rate; sample within-band ages with documented interpolation and sensitivity. | Jersey observed survey, 2023. |
| `T-28` | Returning residents inherit resident vaccination/immunity state from the base model; temporary visitors receive M8 visitor vaccination. If one policy applies to all arrivals, compose once without double dosing. Rename current fields to `visitor_*` unless that unified behaviour is implemented. | Semantics correction. |

### 6.5 Honest uncertainty (`E-01`, `E-02`, `E-03`)

Three layers must stay separate:

1. **Aleatory/stochastic:** repeat one frozen structure/parameter set with independent replicate seeds.
2. **Parameter uncertainty:** draw a provenance-bearing vector (at minimum beta, stage durations, major route weights, ascertainment, arrival prevalence/infection age, visitor contact intensity, and test curve where active), then run stochastic replicates within draws as budget permits.
3. **Structural uncertainty:** compare named alternative models (for example zero/low/high care bridges, alternative accommodation parish rules, different external-acquisition hazards). Do not pool them into one anonymous quantile band.

**Preferred minimal implementation:** add a versioned parameter-draw table with distribution family, support, units, evidence class, dependencies/correlation rule, draw seed and resolved value/hash. Use a space-filling design such as Latin hypercube for an initial sensitivity screen, followed by a smaller nested design for variance decomposition. Preserve the frozen-parameter stochastic ensemble as a distinct mode.

For interior empirical quantiles, require `n × min(q, 1-q) >= 1`; endpoint quantiles 0 and 1 remain allowed and are explicitly the sample minimum/maximum. Thus the default 2.5/97.5 interval requires at least **40 successful replicates**. This is a mathematical resolvability floor, not a claim of precision. Always emit successful `n`, quantile method (`linear` if retained), tail rank, and a “stochastic replicate quantile” or “parameter-draw outcome quantile” label. Below the floor, fail configuration/summary creation or default to median/IQR when the IQR itself passes the rule (otherwise descriptive extrema only), with an explicit insufficient-tail diagnostic; never display an interpolated “95% uncertainty interval.”

For comparisons, aggregate the within-seed differences by scope/key/metric/date and emit paired count, median, lower and upper quantiles, mean, and fraction positive/negative/zero. The artifact must state that same seeds create matched starts but not guaranteed common random numbers after paths diverge.

## 7. Provenance strategy

Every travel evidence snapshot should record publisher, title, direct URL, access date, reference period, revision/methodology vintage, coverage (air/sea/private/cruise/yacht), whether arrival or departure, inclusion of residents/transit, units, rounding, survey sample/weighting notes, source filename and SHA-256. Store raw-public and normalized files; simulations read only the frozen normalized table.

Each parameter must carry:

- `evidence_class` in `{jersey_observed, jersey_survey_estimate, peer_reviewed_proxy, structural_assumption, scenario}`;
- model meaning and units, source universe, central value/distribution/support, and whether sensitivity is mandatory;
- deterministic derivation and source hashes;
- correlation/dependency rules (for example exposed and infectious arrival fractions cannot be drawn independently of prevalence and natural history);
- resolved value/draw hash in every run artifact.

Source updates create new evidence versions and hashes; they never mutate an old artifact. A live dashboard must not be queried during a scientific run.

## 8. Exact testable acceptance criteria

### 8.1 Immediate V1.1 gates

1. **In-horizon absence regression:** create one return episode whose absence begins on simulation day 2 and return is day 4. For days 2–3, planned and runtime `resident_away`/`resident_present` are identical; the resident is absent from every resident and visitor-facing edge and from on-island denominators. On day 4 the resident returns exactly once before network/transmission construction.
2. **Initial and boundary intervals:** absences already active at day 0, beginning day 0, ending on day 0, and ending after the horizon obey the half-open interval `[absence_start, return)`. Daily present + away equals the fixed resident count.
3. **State preservation:** leaving/returning does not reset resident disease episode, immunity, vaccination, or identity. The chosen disease-progression-during-absence policy is tested and documented; `alive` is never interpreted as death for travel absence outputs.
4. **Repeat-trip regression without tests:** one resident with two non-overlapping returns produces two `resident_returned` events with distinct trip/episode hashes; neither is dropped and daily presence reconciles.
5. **Repeat-trip regression with tests:** the same fixture with arrival testing produces two administrations and two correctly bound results (including delayed results), no identity mismatch and no exception. Quarantine state binds to the intended trip.
6. **Protected lifecycle:** arrivals/returns, delay-zero testing/quarantine, route construction and transmission retain their verified ordering. Visitor slot-reuse and event-time identity tests remain green.

### 8.2 Travel evidence and behaviour gates

1. A 365-day full-population neutral-volume run reconciles exactly to the frozen annual `{air, sea, total}` targets after declared source rounding; each month/mode equals the frozen monthly table. A partial horizon equals the sum of included daily targets.
2. At any population scale, movements per resident-year differ from the full-population target only by documented integer-rounding tolerance; changing an intervention volume multiplier does not alter the reported representative population scale.
3. The artifact reports realised visitor fraction by month/mode and distinguishes passenger movements, visits, unique synthetic IDs and resident returns. No “tourists” label is applied to all arrivals.
4. Doubling participating visitors while below the contact cap approximately doubles visitor–resident endpoint opportunities; contacts per participating visitor remain invariant within integer tolerance. Cap-binding days and pool shortages are emitted.
5. Airport terminal resident partners come from St Peter under the default geographic mapping; ferry partners come from St Helier. Alternative catchments require provenance.
6. Every travel edge weight in output resolves to a named config field and provenance row. A test scanning route construction finds no unregistered numeric base weight.
7. Every multi-person visitor party shares accommodation ID/type/parish and stay/departure dates. Party size is never split by accommodation; day-visitor parties are consistently day visitors. Realised party-size, visitor-age, child-party and accommodation-type margins are emitted.
8. Accommodation units never exceed declared capacity on a day. Island type totals/mix reconcile to their source or labelled scenario; parish weights cannot be derived from resident household counts.
9. Two infected arrivals in different infection-age bins can have different detection probabilities under the same assay. A just-exposed returner is not deterministically detected unless the configured curve explicitly says so.
10. Sampled returning-resident exposure dates lie within their absence interval. Stage on return and remaining latent/infectious duration reconcile to exposure time. Imported visitor/returner totals reconcile with transmission-event provenance.
11. Arrival-prevalence outputs are stratified by configured month/type/mode/origin and every headline visitor-linked result records or links to the resolved prevalence scenario/draw.
12. Returning residents do not receive a second M8 vaccination modifier when resident vaccination already applies; visitor-only fields are named visitor-only unless unified traveller semantics are implemented.

### 8.3 Ensemble and comparison gates

1. `lower=0.025`, `upper=0.975` with 39 successful replicates is rejected or marked insufficient with no 95% band; 40 succeeds. Failed replicates do not count toward the floor. Boundary tests cover arbitrary interior quantiles using `n × min(q,1-q) >= 1` and permit 0/1 only as explicitly labelled sample extrema.
2. Every summary row reports successful replicate count, interval class, quantile definition/method and tail rank. Stochastic-only bands cannot contain “confidence,” “credible,” “prediction,” or unqualified “uncertainty” in machine-readable labels.
3. Paired comparison emits one aggregate row for every complete scope/key/metric/date set with exact paired count and median/lower/upper difference. A deterministic fixture validates the values; missing/failed pairs reduce `n` and are reported.
4. Comparison metadata contains the coupling caveat and seed-pair correlation diagnostic. Equal seeds are described as matched-seed pairing, not guaranteed persistent common-random-number coupling.
5. Parameter draws are deterministic from draw seed and spec hash; every run retains draw vector/hash and all distribution provenance. Repeating the same draw/stochastic seeds reproduces outputs.
6. A nested synthetic fixture with known parameter and stochastic effects produces non-negative variance components that reconcile to total variance within numerical tolerance. Structural alternatives remain separate scenario rows, not pooled samples.

## 9. Risks and implementation implications

- Representative movement scaling raises small-mode travel volume by orders of magnitude relative to V1's shipped `0.001` stream. Visitor-slot capacity, materialized-episode limits, runtime and memory must be profiled before making it a default epidemic run.
- Annual and monthly sources can differ by revision, rounding or coverage (private aircraft, cruise, yachts). One versioned reconciliation rule is required.
- Arrival and departure survey measures are near-equivalent only under a steady accounting period; boundaries, long stays and resident trips can differ. Do not silently substitute one for the other.
- A fixed contact degree per visitor is still a structural contact model. It corrects the saturation defect but does not calibrate mixing intensity.
- Backdating infection interacts with disease transition scheduling, event provenance and observation timing. It requires direct inspection of the authoritative disease state machine, not a wrapper that edits labels only.
- Using `people.alive` for temporary absence risks freezing disease progression or conflating absence with death. Presence should be an explicit mask if engine semantics permit.
- Party co-location increases clustered exposure and peak accommodation occupancy; capacity checks and slot reuse must operate on party episodes.
- The 2023 visitor profile predates the 2025 survey-method change and can age. It is better than uniform ages but must retain date and uncertainty.
- A minimum of 40 only makes 2.5/97.5 empirical tails resolvable. Quantile Monte Carlo error may still be large; convergence diagnostics or more runs are needed for policy claims.
- A full nested uncertainty design is computationally expensive. Screening at reduced scale may identify influential inputs, but scale-sensitive travel structure must be rechecked at representative/full scale.

## 10. Unresolved questions and recommended aggregate requests

1. Can Visit Jersey provide one versioned CSV of revised 2025 monthly arrivals by mode/coverage, avoiding transcription from 12 reports?
2. Can the VVS publish aggregate 2025 passenger-type × month × mode, party-size, purpose, stay-length, age-band and accommodation tables with uncertainty/weights?
3. Can the registered visitor-accommodation list be exported as premises count and bedspaces by type and parish? No guest names or booking records are required.
4. Which origin categories are stable enough for disease-specific arrival prevalence, and are monthly cells sufficiently sampled?
5. For residents infected while away, should their disease progress during absence, and should off-island recovery/death be represented? This lifecycle choice must precede implementation of backdated acquisition.
6. Which assay/pathogen is intended for the first incubation-sensitive arrival-test configuration? Generic respiratory demonstration parameters cannot answer it.
7. Which route-contact parameters should be jointly distributed, and what dependencies are scientifically defensible?
8. Is the 40-replicate tail floor acceptable as an execution guard, or should the default output change to median/IQR until a larger, precision-based run budget is adopted?
9. What reduced-scale/full-scale validation plan is required before parameter-uncertainty results are called transferable across travel scales?

## 11. Source register

All links were accessed 2026-08-30.

- Government of Jersey / Ports of Jersey: [Passenger and freight statistics](https://opendata.gov.je/dataset/2da64802-1281-429e-8506-1d568e488d22); [annual total arrivals](https://opendata.gov.je/dataset/passenger-statistics/resource/dcc8a6c2-152a-48c0-b24b-de1774354d3c).
- Visit Jersey: [Monthly Passenger Arrivals](https://business.jersey.com/research-trends/tourism-statistics/monthly-passenger-arrivals/); [Visitor Statistics Methodology](https://business.jersey.com/research-trends/tourism-statistics/methodology/); [Visitor Statistics](https://business.jersey.com/research-trends/tourism-statistics/visitor-figures/); [About the data](https://business.jersey.com/research-trends/tourism-statistics/visitor-figures/about-the-data/); [2023 Annual Travel Survey](https://cdn.jersey.com/images/v1715334523/Trade/Annual-Passenger-Exit-Survey-2023-V9-for-website/Annual-Passenger-Exit-Survey-2023-V9-for-website.pdf).
- Government of Jersey tourism: [Tourism statistics and registered accommodation](https://www.gov.je/industry/retailhospitality/visitoreconomy/pages/tourism.aspx); [annual tourism dataset](https://opendata.gov.je/dataset/tourism-statistics/resource/59c9f0d6-1620-4424-a724-3d61aed32f7f); [visitor-bed FOI](https://www.gov.je/Government/FreedomOfInformation/pages/foi.aspx?ReportID=7057).
- Kucirka et al. (2020): [Variation in false-negative rate by time since exposure](https://doi.org/10.7326/M20-1495).
- Johansson et al. (2021): [Layered mitigation for travel-related SARS-CoV-2 transmission](https://pmc.ncbi.nlm.nih.gov/articles/PMC8043777/).
- RKI within-host traveller testing study (2021): [PubMed 33899034](https://pubmed.ncbi.nlm.nih.gov/33899034/).
- Yang and Nelson (1991): [Common random numbers in multiple comparisons](https://doi.org/10.1287/opre.39.4.583).
