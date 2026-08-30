# R3 — Jersey structure evidence

**Status:** research complete for the V1.1 scientific-hardening programme  
**Evidence cut-off and access date:** 2026-08-30  
**Scope:** `STR-01`, `STR-02`, `POP-07`, and the evidence needed to plan `POP-04`, `POP-05`, `POP-09`, `POP-10`, `STR-05`, `STR-06`, `STR-07`, `STR-09`, `STA-05`, and `STA-06`.

## 1. Decision summary

Three V1.1 corrections can be made without inventing new Jersey facts:

1. **School age structure (`STR-01`):** allocate pupils by documented school-year eligibility and an observed Jersey year-group margin. Do not allocate an island-wide pool youngest-first. The current CYPES publication supplies the school inventory, age ranges, and a pupil-by-year-group series, but its published characteristics universe must not be silently extended from government-provided compulsory-age schools to private and post-16 provision.
2. **School geography (`STR-02`):** use the public school-site inventory and the published government catchment/feeder relationships. Selective and private schools require an explicitly non-catchment assignment rule. A pupil's home-parish mode must not be used to manufacture school location.
3. **Car access (`POP-07`):** use the 2021 Census cars/vans-by-parish counts directly. If the existing residual algorithm is retained temporarily, its weights must be multiplied by the number of eligible households in each parish; bare parish weights are mathematically wrong.

The strongest additional Jersey evidence is already public but unused: economic status by age, industry by age, a current sector-by-workplace-size table, experimental employment by age/sex/sector and second-job rates, a public care-home register, further-education counts, and monthly public-sector staffing. Several requested details are **not** publicly evidenced at the required resolution: a current household-size distribution, household age relationships, staff by hospital site, care-resident ages, cross-home staffing, and current Jersey remote-work days by sector. Those quantities must remain labelled proxy or assumption inputs rather than being presented as Jersey observations.

## 2. Evidence classification

This document uses three non-interchangeable labels:

- **Observed Jersey evidence:** a Jersey administrative, census, regulatory, or survey publication. Rounding, coverage and reference dates remain attached.
- **UK proxy evidence:** an official UK statistic or peer-reviewed UK study used only to set a plausible distribution or sensitivity range. It is not a Jersey estimate.
- **Structural assumption:** a modelling choice not estimated from either source class. It must be configurable and included in structural sensitivity where material.

No restricted, person-level, manifest, health-record, school-record, employee-record, or commercially confidential data were requested or used.

## 3. Current V1 behaviour and protected contracts

The review reports, current implementation, tests, and frozen pilot were inspected. The following are protected unless a named finding explicitly authorises a change: exact resident identity, exact raked demographic margins, immutable artifact identity and hashes, route/lifecycle ordering, the replacement of generic workplace membership by institutional staff membership, and existing provenance semantics.

| Finding | Current implementation and realised behaviour | Consequence |
|---|---|---|
| `STR-01` | `_build_schools()` takes an island-wide eligible pool in ascending age order for each school type. At full scale, special pupils are all 18; independent-primary pupils are only 10–11; independent-secondary pupils are only 16–17. | School type is confounded with age; range-validity tests do not detect the collapse. |
| `STR-02` | Each synthetic school's parish is the modal home parish of its selected pupils. All 48 schools and all 1,972 school staff resolve to St Helier. | Parish-resolved school and school-staff results are invalid. |
| `POP-07` | St Helier and island no-car totals are pinned, then the residual is allocated using bare parish commute weights rather than weight times household count. | The intended parish gradient is inverted (reported review correlation `-0.69`). |
| `POP-04` | The mean private-household size (2.2696) and one-person household share are pinned; remaining members are capacity-weighted into households with a cap of 8. | The size tail is under-dispersed and not fitted to an observed size distribution. |
| `POP-05` | Couple and parent-child ages satisfy hard gaps only. Full-scale realised couple gap median is 10 years and 28.2% exceed 15; parent-child median is 22, p95 46, p99 53. | Age-specific household transmission targeting is weakly evidenced. |
| `POP-09`, `POP-10` | Communal residents are divided nearly equally within category. Care ages use a synthetic 50–95 ramp; 30.45% are 50–64 and median age is 71. | Institutional outbreak-size variance is suppressed and care severity composition is implausibly young. |
| `STR-05` | Fixed age weights are sampled without replacement. Realised employment rates are 60.3%, 84.7%, 87.3%, 81.5%, and 31.1% across the five configured age bands. | Intended weights are not realised employment controls. |
| `STR-06`, `STR-07` | The sector-by-size control is loaded but unused; sectors are assigned greedily. The 50+ workplace band is nearly uniform (132–173, mean 150.48); public jobs are split into sites capped at 25. | Sector-by-size and large-site outbreak results are invalid; no hospital site exists. |
| `STR-09` | Workers are selected for remote work without sector conditioning and receive either 5 or 0 remote days. | Hybrid work and sector differences are absent. |
| `STA-05`, `STA-06` | Only nursing/non-nursing homes receive care staff; every care worker has one setting. Each teacher has one class. | No cross-home bridge, no staff for other communal categories, and weak secondary-school class bridging. |

The frozen full-scale pilot is baseline execution evidence, not empirical Jersey evidence. It contained 104,540 residents, 48 synthetic schools, 8,770 workplaces, 164 communal settings, 1,972 school staff and 448 care staff. Its PASS verifies artifact and accounting contracts. Its route attributions and contact distributions are generated outputs and must not be used as targets for this lane.

## 4. Observed Jersey evidence

### 4.1 Schools, pupils, sites and catchments

The current CYPES publication reports **30 primary, 9 secondary and 2 special schools**, serving ages 3–18, plus Highlands College Level 3 provision for ages 16–18. It publishes a school list, sector/type descriptions, school-size summaries, and a pupil-by-year-group visual. It also warns that pupil-characteristic statistics cover Reception–Year 11 in government-provided schools only ([CYPES schools and pupils](https://www.gov.je/Education/Schools/Education/pages/schoolspupilscharacteristics.aspx), accessed 2026-08-30).

The catchment publication supplies an interactive primary/secondary map and explicit government secondary feeder relationships: Grainville (Grands Vaux, Janvrin, Springfield, St John, St Martin, St Saviour, Trinity); Haute Vallée (D'Auvergne, First Tower, Rouge Bouillon, St Lawrence); Le Rocquier (Grouville, Plat Douet, Samarès, St Clement, St Luke); Les Quennevais (Bel Royal, La Moye, Les Landes, Mont Nicolle, St Mary, St Peter). It cautions that a catchment school need not be the closest school ([CYPES catchments](https://www.gov.je/Education/Schools/FindingSchool/Pages/FindSecondaryCatchmentSchool.aspx), accessed 2026-08-30). Admissions also allow siblings, special need, feeder school, parental work location and out-of-catchment decisions; catchment is not deterministic attendance ([secondary admissions](https://www.gov.je/education/schools/findingschool/pages/admissions.aspx), accessed 2026-08-30).

**Evidence implication.** School location can be observed; pupil home-to-school linkage cannot be reconstructed exactly from public aggregates. Government catchment relationships support weighted allocation, not a claim of observed individual attendance. Selective, fee-paying, Catholic, independent, special and post-16 pathways require separate declared rules.

### 4.2 Households and relational ages

The 2021 Census publishes 11 household types by tenure, parish dwelling and tenure tables, and mean persons per private dwelling. It does **not** expose a current persons-per-household frequency table in the searchable open-data catalogue: the resource named “Number of persons per private dwelling 1971–2021” is a time series of the mean, not a size distribution ([2021 Census catalogue](https://opendata.gov.je/dataset/2021-census), [mean-persons resource](https://opendata.gov.je/dataset/2021-census/resource/a050dce7-db03-4c6d-a09b-0d074208d5e3), accessed 2026-08-30). Household type by tenure is observed and rounded, but does not identify partner-age or parent-child-age distributions ([household type by tenure](https://opendata.gov.je/dataset/2021-census/resource/5eb10530-8847-4fc9-bb12-66114f05e562), accessed 2026-08-30).

A historical Jersey housing survey reported a 2007 household-size distribution of 29% one person, 36% two, 16% three, 13% four, 4% five, and 2% six or more (mean 2.33). This is observed Jersey survey evidence but is too old to be a current exact control ([Jersey Housing Assessment 2008–2012](https://www.gov.je/sitecollectiondocuments/government%20and%20administration/irp1%20bt8%20jersey%E2%80%99s%20housing%20assessment%202008-2012%2020140115%20mm.pdf), accessed 2026-08-30).

**Evidence implication.** Preserve the exact 2021 household-type and population margins. Use the 2007 size distribution only as a historical sensitivity comparator until Statistics Jersey supplies a current table. There is no basis for labelling any fitted relational-age law as Jersey-observed.

### 4.3 Employment, workplace size and large workplaces

Statistics Jersey reports 64,680 jobs in December 2025 and 8,710 private undertakings. Its current cross-tab contains 190 private undertakings in the 50+ band and detailed sector-by-size cells, with counts rounded to the nearest 10 ([Labour market and employment](https://stats.je/statistic/labour-market-and-employment/), [downloadable sector-by-size resource](https://opendata.gov.je/dataset/companies-by-size-and-sector/resource/11f447a5-a2e7-4afb-a708-d0988ab2be78), accessed 2026-08-30). “Jobs” are not unique workers; people with multiple jobs can be counted more than once.

The 2021 Census catalogue exposes **Economic Status by Age** and **Industry by Age**, both currently unused by V1 ([Economic Status by Age](https://opendata.gov.je/dataset/2021-census/resource/0de34c6c-f586-4eeb-a40a-426b78e24528), [Industry by Age](https://opendata.gov.je/dataset/2021-census/resource/ab4912f0-f8cb-4bdb-b8c9-d4060b5c3cf1), accessed 2026-08-30). A newer experimental administrative release exposes employed people by sector/age/sex and the proportion with a second job by main-job sector; it explicitly warns that experimental values may be revised ([Employment and jobs (experimental)](https://opendata.gov.je/dataset/c88c7fee-5aac-4837-bf32-8d43ac3066f2), accessed 2026-08-30).

The 50+ band does not reveal its upper tail or identify large employers. Publicly named employers and department totals must not be combined with the private-undertaking cross-tab as if they share a universe. For Health and Care Jersey (HCJ), public-sector staffing is available at department/pay-group level, but central records do not group staff by working location and cannot supply a Jersey General Hospital-only total ([Public Sector Staffing Statistics](https://www.gov.je/government/pages/statesreports.aspx?reportid=5953), [hospital-location FOI](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=8276), accessed 2026-08-30).

**Evidence implication.** `STR-05` and `STR-06` can use Jersey controls now. A right-skewed within-band tail remains a structural assumption. A named Jersey General Hospital site is geographically defensible, but assigning all HCJ staff to it is not.

### 4.4 Care homes and communal settings

The 2021 Census reported 162 communal establishments and 2,079 communal residents, including 15 care homes with nursing (629 residents) and 16 without nursing (328 residents) on Census Day ([Report on the 2021 Jersey Census](https://statesassembly.gov.je/assemblyreports/2023/r.45-2023.pdf), accessed 2026-08-30). These are occupied usual-resident counts at one date, not current registered capacity.

The Jersey Care Commission provides a current searchable service register and inspection reports. At the evidence cut-off, the care-home filter returned 49 registered care-home services; the live count and classifications are mutable and must be snapshotted before use ([Care Commission service search](https://carecommission.je/care-service-search/), [inspection reports](https://carecommission.je/inspection-reports/), accessed 2026-08-30). Government FOI responses direct users to the Commission for registered beds and state that HCJ does not hold island-wide resident counts because most homes are private ([care-home resident FOI](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=8121), accessed 2026-08-30).

No public Jersey aggregate was located for care-resident age, staff working across multiple homes, or establishment-level occupancy at a common reference date. Public inspection material may state each service's registration conditions and maximum capacity; only aggregate service attributes should be extracted. Names of residents or staff, rota data and other personal information are out of scope.

### 4.5 Remote work

The V1 control is a 2021 Census travel-to-work measure collected during pandemic conditions. A March 2021 Jersey business survey found strong sector contrast (for example, finance businesses were much more likely than non-finance businesses to report all staff working remotely), but it measures businesses during restrictions, not employee-days in a stable hybrid regime ([Business Tendency Survey, March 2021](https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/R%20BTS%20Mar%202021%2020210415%20SJ.pdf), accessed 2026-08-30). A 2025 FOI says formal flexible-working data cannot provide a complete picture and informal home working is not recorded ([flexible-working FOI](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=8686), accessed 2026-08-30).

**Evidence implication.** Jersey evidence supports sector heterogeneity, but not exact current days per week. Sector-specific remote-day distributions must be a sensitivity input.

### 4.6 Further education

Highlands College is a missing contact setting. The Summer Census 2024 recorded **606 students aged 16–18 in full-time education at Highlands** ([Highlands FOI](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=7495), accessed 2026-08-30). A separate higher-education FOI reports 2024/25 Highlands higher-education enrolment of 36 aged 16–18, 81 aged 19–24 and 55 aged 25+, and 171 undergraduates; these counts describe HE courses and must not be added to the 606 without checking overlap and universe ([on-island higher education FOI](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=9168), accessed 2026-08-30).

**Evidence implication.** Further education is well-supported as a future setting but not part of the bounded S1/S2 correction. A later implementation needs timetable/contact assumptions and reconciliation against pupils already counted in school Years 12–13.

### 4.7 Parish car access and transport

The 2021 Census publishes **Cars/Vans by Parish** and usual travel-to-work mode by parish. The direct cars/vans table should supersede derived bare weights ([Cars/Vans by Parish](https://opendata.gov.je/dataset/2021-census/resource/d4047f98-6383-4031-ba70-aa95fc3fa703), accessed 2026-08-30). Counts are rounded and their household universe must be matched to synthetic private households. Island and St Helier checks used by V1 (approximately 16% and 30% no-car households) remain useful reconciliation diagnostics, not substitutes for all-parish targets.

## 5. UK proxy evidence — never Jersey observations

| Gap | Proxy and defensible use | Prohibited interpretation |
|---|---|---|
| Household age composition | ONS Census 2021 household composition and living-arrangement releases can supply partner and parent/child age-gap shapes ([ONS household composition dataset RM057](https://www.ons.gov.uk/datasets/RM057/editions/2021/versions/2), accessed 2026-08-30). | Do not call fitted gaps Jersey estimates or overwrite exact Jersey age/household-type margins. |
| Care-resident age | In England and Wales, 82.1% of care-home residents were 65+, 74.0% of those older residents were 80+, and 56.4% were 85+; median age among residents aged 65+ was 86 years 5 months ([ONS care-home residents](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/ageing/articles/olderpeoplelivingincarehomesin2021andchangessince2011/2023-10-09), accessed 2026-08-30). Use as a sensitivity distribution constrained to Jersey care-place totals. | Do not infer Jersey occupancy or exact age shares. The ONS census was also pandemic-affected. |
| Cross-home staffing | An England survey estimated 11.5% of care homes had staff working at more than one location in spring 2020 ([ONS Vivaldi](https://www.ons.gov.uk/peoplepopulationandcommunity/healthandsocialcare/conditionsanddiseases/articles/impactofcoronavirusincarehomesinenglandvivaldi/26mayto19june2020), accessed 2026-08-30). In six London outbreak homes, cross-home workers had roughly threefold higher test positivity; the study is mechanism evidence, not a prevalence estimate for Jersey ([Ladhani et al., 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7387283/), accessed 2026-08-30). | Do not set Jersey's bridge fraction to 11.5% without sensitivity analysis; home-level and worker-level denominators differ. |
| Current remote work | ONS estimated 28% of working adults in Great Britain hybrid-worked in Jan–Mar 2025, with large occupation/industry differences ([ONS hybrid work](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/articles/whohasaccesstohybridworkingreatbritain/2025-06-11), accessed 2026-08-30). | Do not copy the GB overall rate into finance-heavy Jersey or treat hybrid status as five days at home. |

## 6. Candidate designs and preferred design

### 6.1 Immediate V1.1 corrections

#### S1 / `STR-01`: school age structure

Candidates:

- random selection within each allowed age range;
- school-type by age/year target matrix from published CYPES margins;
- an individual-level school census (rejected: unnecessary and restricted).

**Preferred:** freeze a versioned CYPES year-group table and school inventory. Construct a school-type × year-group matrix whose row totals preserve the existing pupil-type controls and whose column totals match the compatible observed Jersey year-group margins. Where the public release lacks a type/year cell, use a documented eligibility mask plus maximum-entropy/proportional allocation. Select pupils randomly and deterministically by seed within each year stratum. Map academic year to age using the run's reference date; the bridge is an assumption and must be recorded.

This is the smallest root-cause fix that prevents type-age collapse while preserving exact totals and agent uniqueness.

#### S2 / `STR-02`: school geography

Candidates:

- remove `school_parish` and declare schools non-geographic;
- distribute synthetic schools by parish counts only;
- use observed sites and catchment-weighted pupil allocation.

**Preferred:** use the public school inventory as the authoritative school-site/parish table. For government non-fee schools, allocate pupils with a high weight for their published primary catchment/secondary feeder group and a non-zero out-of-catchment probability. For selective, fee-paying, private, Catholic and special schools, use island-wide assignment subject to eligibility and capacity. Never infer a site's parish from assigned pupils. If reconciling the current 48 synthetic institutions to the 41-school public inventory is judged outside V1.1's permitted contract change, retain synthetic identities but allocate their parishes in proportion to observed sites by type and mark them synthetic; this is the fallback, not the scientific preference.

#### S3 / `POP-07`: no-car allocation

Candidates:

- correct the current residual weight to `parish_weight × eligible_households`;
- target direct census no-car counts by parish.

**Preferred:** ingest the direct Cars/Vans by Parish table and allocate no-car households by largest remainder within parish, reconciling the rounded cells to the exact island target. Preserve household eligibility rules. The multiplication fix is an acceptable minimal fallback only if the direct resource cannot be frozen reproducibly.

### 6.2 Later V1.x structure work

| Findings | Preferred design | Evidence status |
|---|---|---|
| `POP-04` | Preserve 2021 mean/type totals; expose household-size shape as a structural scenario. Compare current allocation with the historical Jersey 2007 distribution and a UK-2021 proxy. Do not claim a current Jersey fit until a current size table is obtained. | Jersey margin + historical Jersey / UK proxy shape. |
| `POP-05` | Fit truncated partner and parent-child gap distributions from ONS proxy micro-aggregates, then condition on exact Jersey ages and household types. Report realised gap quantiles. | UK proxy + structural conditioning. |
| `POP-09` | Freeze public Care Commission service capacities and draw/allocate occupied residents subject to Census category totals. Preserve the distinction between registered capacity and occupied usual residents. | Jersey register + Jersey census. |
| `POP-10` | Use a configurable care-age distribution. Preferred base is the ONS care-home shape reweighted to Jersey's age margins; include a broad younger-adult-care component rather than excluding under-65 residents. | UK proxy; Jersey-specific profile unresolved. |
| `STR-05` | Rake primary-worker selection to observed Jersey economic-status age × sex totals; use experimental employment by age/sex/sector as a validation target or, after a stability review, a control. | Jersey observed/experimental. |
| `STR-06` | Consume the already-loaded sector-by-size cells as the authoritative private-workplace allocation target; retain rounding intervals rather than inventing exact suppressed cells. | Jersey observed, rounded. |
| `STR-07` | Within each size band, use a declared right-skew distribution and exact band job totals. Treat the 50+ upper tail as structural sensitivity. Add separately sourced named public sites; do not assign all departmental HCJ staff to Jersey General Hospital. | Jersey band totals + assumption tail. |
| `STR-09` | Assign remote days by sector/occupation with 0–5-day distributions. Centre scenarios on Jersey overall constraints, use GB 2025 patterns only for relative gradients, and include low/base/high hybrid scenarios. | Jersey historical + UK proxy + assumption. |
| `STA-05` | Parameterise a small cross-home staff bridge and staff other communal categories only when a regulatory/staffing source exists. Run zero/low/high bridge scenarios; zero remains an explicit comparator. | UK mechanism proxy; Jersey fraction unknown. |
| `STA-06` | Give secondary teachers subject/year-group rosters spanning multiple classes; retain primary class-teacher concentration. The number of bridged classes is a documented timetable assumption. | Structural assumption; school-type evidence observed. |
| `STR-04` | Add Highlands as a separate further-education setting only after de-duplicating Year 12/13 and HE universes. | Jersey observed counts; contact structure assumed. |

## 7. Provenance strategy

Every normalized evidence table should be immutable and registered with:

- publisher, publication title, direct source URL, access date, reference date/period, licence, original filename, and SHA-256;
- extraction method (CSV direct, manually transcribed public table, or public dashboard export), original units, rounding/suppression rules, population universe, and any reconciliation transformation;
- `evidence_class` in `{jersey_observed, jersey_experimental, uk_proxy, structural_assumption}`;
- source-to-model mapping, including category crosswalks and whether the quantity is an exact target, bounded target, validation diagnostic, or sensitivity input;
- a frozen normalized table and a human-reviewable derivation note. Live dashboard or register values must never be read silently at simulation time.

Assumptions require an identifier and version even when they have no external source. Proxy-derived parameters must retain both the proxy geography and the Jersey margins to which they were conditioned. Rounded Jersey cells should be represented as intervals or reconciled with a documented deterministic rule; fabricated exactness is prohibited.

## 8. Exact testable acceptance criteria

### 8.1 V1.1 implementation gates

1. **School age spans:** every compatible documented year group is non-empty for every realised school type whose pupil count is at least the number of compatible year groups; every pupil lies in the type's documented year/age eligibility; all pupil IDs are unique across schools; exact type totals are unchanged. A full-scale regression must fail on the historical youngest-first allocation.
2. **School distribution diagnostic:** for each type, emit target and realised counts by year group plus total-variation distance. For cells defined by observed targets, integer counts must match the deterministic rounded target exactly; cells based on assumptions must be labelled as such.
3. **School geography:** the full-scale inventory has at least two school parishes and `school_parish` always comes from a registered site/parish mapping, never from pupil home-parish mode. School staff inherit the site's parish. Emit household-school same-parish rate and a parish association statistic. The historical all-St-Helier fixture must fail.
4. **Catchment semantics:** government catchment allocations show a higher in-catchment rate than an island-wide random allocation under the same capacities. Selective/private/special allocations are not falsely labelled catchment-based. All capacity and pupil-count totals reconcile.
5. **Car access:** exact full-scale no-car household totals match the declared island and parish integer targets after documented rounding reconciliation; St Helier is 30% and island-wide is 16% when those frozen controls are retained. Across parishes, generated no-car rates have positive Pearson and Spearman association with the source rates/weights. The historical bare-weight fixture must fail.
6. **Protected contracts:** resident identity/count, demographic margins, household membership integrity, institutional-staff job replacement, lifecycle order, artifact schema and provenance hashes change only where the new registered inputs require new logical identities. No duplicate pupil, worker, staff or household membership is introduced.

### 8.2 Gates for later findings

1. Household-size and relational-age outputs report realised size frequencies and partner/parent-child gap quantiles against their labelled target or proxy; exact Jersey population and household-type totals remain unchanged.
2. Communal-setting sizes are non-degenerate within any category having at least three establishments and reconcile exactly to category establishment/resident totals. Capacity is never described as occupancy.
3. The realised care population reports shares `<65`, `65–79`, `80–84`, and `85+`; its source class is present in the artifact. No default may be labelled Jersey-observed without a Jersey source.
4. Realised employment rates by age × sex and workplace counts by sector × size are emitted and reconcile to their source universes. The sector-by-size table is consumed, not merely registered.
5. At least one workplace exceeds the former 173-worker maximum in a structural-tail scenario, but no exact large-employer size is asserted without evidence. Hospital-site staff never exceed the sourced site-specific count; absent such a count, the field is explicitly assumed.
6. Remote-work outputs contain 0–5 remote days, differ by sector in the configured proxy/scenario direction, and report realised employee-days remote. A binary-only 0/5 implementation fails.
7. Cross-home staffing reports the number and proportion of workers with multiple assignments and the resulting inter-home connected components. Zero, low and high scenarios are reproducible from their own provenance IDs.

## 9. Risks and implementation implications

- Replacing 48 synthetic schools with 41 public sites changes M3/M4 logical identities and may require an explicitly approved schema/data-contract migration. The fallback parish-allocation design avoids that change but is less realistic.
- CYPES dashboards can be revised without versioned files. Implementation must freeze an export, not scrape at runtime.
- Census, labour, care-register and staffing sources have different dates and universes. “Current Jersey” is not a single coherent reference date; each target must retain its own date.
- Workplace rounding and the open-ended 50+ band make a unique tail unidentifiable. One fitted tail cannot be treated as observed.
- A hospital site can dominate a contact network. Using department-wide HCJ FTE as a site count would create false precision and likely a large structural bias.
- Care Commission registered capacity, Census occupied residents and modelled daily presence are different quantities.
- UK care and remote-work evidence comes from a different labour market and, for several sources, pandemic conditions. These are sensitivity bounds only.
- Further-education counts overlap multiple reporting universes; adding them without de-duplication would double-count residents.

## 10. Unresolved questions and recommended data requests

1. Can CYPES provide a versioned aggregate school-type × year-group table and aggregate home-parish × school-site/catchment table, with no pupil records?
2. Can Statistics Jersey provide a rounded 2021 persons-per-private-household frequency table and aggregated partner/parent-child age cross-tabs?
3. Can the Care Commission provide a versioned aggregate export of service type, parish and registered maximum capacity? Public service metadata is sufficient; no resident or staff data are needed.
4. Is there an aggregate Jersey count of workers employed at more than one registered care service, or a provider-level “has cross-site staff” count?
5. Can HCJ provide aggregate FTE by major work site, especially Jersey General Hospital, without role- or person-level disclosure?
6. Is there a post-pandemic Jersey survey of usual work location or remote employee-days by sector/occupation?
7. Does the CYPES pupil total already include every 16–18 Highlands learner used by the Summer Census, and how should HE/apprenticeship learners be de-duplicated?
8. Which existing exact school-count and communal-setting-count contracts, if any, are authorised to change in V1.1 rather than V1.x?

## 11. Source register

All links were accessed 2026-08-30.

- Government of Jersey / CYPES: [Schools, pupils and their characteristics](https://www.gov.je/Education/Schools/Education/pages/schoolspupilscharacteristics.aspx); [catchment schools](https://www.gov.je/Education/Schools/FindingSchool/Pages/FindSecondaryCatchmentSchool.aspx); [admissions](https://www.gov.je/education/schools/findingschool/pages/admissions.aspx).
- Statistics Jersey: [2021 Census dataset catalogue](https://opendata.gov.je/dataset/2021-census); [2021 Census report](https://statesassembly.gov.je/assemblyreports/2023/r.45-2023.pdf); [labour market and employment](https://stats.je/statistic/labour-market-and-employment/); [experimental employment and jobs](https://opendata.gov.je/dataset/c88c7fee-5aac-4837-bf32-8d43ac3066f2); [undertakings by size/sector](https://opendata.gov.je/dataset/companies-by-size-and-sector/resource/11f447a5-a2e7-4afb-a708-d0988ab2be78).
- Government of Jersey FOI: [Highlands 16–18 full-time learners](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=7495); [on-island HE](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=9168); [hospital-location staffing limitation](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=8276); [care-home resident data limitation](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=8121); [flexible-working limitation](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=8686).
- Jersey Care Commission: [service search](https://carecommission.je/care-service-search/); [inspection reports](https://carecommission.je/inspection-reports/).
- ONS: [household composition RM057](https://www.ons.gov.uk/datasets/RM057/editions/2021/versions/2); [care-home resident population](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/ageing/articles/olderpeoplelivingincarehomesin2021andchangessince2011/2023-10-09); [Vivaldi care-home survey](https://www.ons.gov.uk/peoplepopulationandcommunity/healthandsocialcare/conditionsanddiseases/articles/impactofcoronavirusincarehomesinenglandvivaldi/26mayto19june2020); [hybrid work, Jan–Mar 2025](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/articles/whohasaccesstohybridworkingreatbritain/2025-06-11).
- Ladhani et al. (2020): [cross-home staff and SARS-CoV-2 infection](https://pmc.ncbi.nlm.nih.gov/articles/PMC7387283/).
