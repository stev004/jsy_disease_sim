# R5 — Jersey epidemiological data landscape

**Status:** forward-looking, nonblocking research dossier for V1.1 synthesis  
**Research date:** 30 August 2026  
**Scope:** aggregate public evidence only; no restricted, patient-level, or personally identifiable data were accessed or acquired

## Scope and decision boundary

This dossier inventories official Jersey sources that could support future calibration or validation of an outbreak simulator. It covers COVID-19 cases and testing, border testing, hospital indicators, seroprevalence, vaccination, influenza, RSV, care-home outbreaks, school absence, and intervention timelines.

It does **not** download or ingest data, alter the source registry, calibrate a disease, endorse a single observation model, or block V1.1. Publicly reported cases, tests, GP consultations, hospital positives, vaccination, and absences are observation-process outputs or contextual covariates; none is equivalent to infection incidence. A source is “registrable” below only if an immutable aggregate snapshot can legally and reproducibly be stored with its URL, retrieval date, checksum, definitions, and transformation. A live dashboard alone is not reproducible evidence.

## Audit findings addressed

The scientific review roadmap made Jersey epidemiological registration a later evidence milestone, dependent on natural-history, network, runtime, and uncertainty hardening. R5 is therefore intentionally nonblocking.

| Finding ID | Evidence class | Finding | R5 disposition |
|---|---|---|---|
| **R5-F01** | **Repository evidence** | The current source registry is strict, checksum-bound, and oriented to population/network controls, not epidemiological time series. | Reuse its immutable-snapshot contract; extend fields only where observation definitions and revision history require it. |
| **R5-F02** | **Official-source evidence** | Jersey's archived COVID open-data resources are the strongest machine-readable local epidemic series, but testing policy and case definitions changed sharply. | Highest-priority acquisition; register cases and tests together with policy-regime metadata. |
| **R5-F03** | **Official-source evidence** | Current respiratory reporting combines COVID PCR, lab-confirmed influenza/RSV, and GP influenza-like illness, mainly in human-readable charts/tables. | Valuable validation targets and seasonal timing evidence, not direct infection incidence. Preserve dated report snapshots because the “latest” PDF URL can be overwritten. |
| **R5-F04** | **Official-source evidence** | Monthly positive-inpatient counts exist for COVID, influenza, and RSV for 2022–2024, with `<5` suppression and no causal attribution to admission. | Registrable as censored hospital-surveillance counts; never label as hospitalisations caused by the pathogen. |
| **R5-F05** | **Official survey evidence** | Three 2020 community serosurveys estimate adult private-household antibody prevalence, with test-device changes, weighting, nonresponse, and communal-establishment exclusions. | Among the strongest public local cumulative-infection constraints identified in this bounded search; usable only through an explicit serology likelihood including sensitivity/specificity and sampling design. |
| **R5-F06** | **Official-source evidence** | Vaccination data are available as archived weekly open data and later programme-specific PDF reports. Eligibility and denominators change by campaign. | Register doses/coverage by campaign and group; do not concatenate percentages across changing eligible populations. |
| **R5-F07** | **Official-source evidence** | Influenza and RSV surveillance is multi-indicator and testing protocols changed during/after COVID. | Use a joint observation design or validate timing/rank/season shape; do not treat positive counts as stable ascertainment. |
| **R5-F08** | **Search finding / absence of suitable evidence** | No complete, stable, public aggregate care-home outbreak time series was identified. Public inspection material risks facility identification and does not form a consistent denominator. | Do not fabricate or scrape an outbreak target. Seek an official disclosure of weekly aggregate outbreak counts and definitions. |
| **R5-F09** | **Official-source evidence** | School absence and school-case FOI releases are fragmented, definition-specific, and incompletely cover school types and respiratory causes. | Use only as weak timing/contact-regime proxies, with explicit universe and mechanism; not as infection counts. |
| **R5-F10** | **Official-source evidence** | A defensible intervention timeline can be reconstructed from dated official announcements, policy documents, and the independent review, but planned and actual dates can differ. | Build an event-level table with one source per effective date and retain superseded/planned dates as separate records. |
| **R5-F11** | **Modelling inference** | Multiple observation streams can constrain different combinations of transmission, ascertainment, severity, and intervention timing; they cannot identify all parameters without assumptions. | Predeclare calibration roles, holdout targets, observation likelihoods, and non-identifiability checks before fitting. |

## Current implementation

`data/sources.yaml` and `SourceRecord` already define source ID, title, publisher, URL, retrieval date, reference period, licence, evidence status, acquisition method, local snapshot, checksum, and notes. The current registry is snapshot/hash complete, but the schema permits absent snapshots and checksums; `load_source_registry()` rejects unknown fields and verifies hashes when declared. A V1.1 epidemiological acquisition gate should make immutable snapshot/hash fields mandatory for the acquired subset rather than claiming the current base schema already does so. Canonical rows carry source ID/hash, evidence source, reference period, observation status, locator, and transformation ID. These are protected provenance contracts.

No canonical epidemiological-series schema, observation-regime table, suppression/censoring representation, or revision policy exists. Current disease and observation parameters are scenario assumptions; V1 outputs and the frozen pilot are not calibrated to the Jersey series below. The API exposes verified simulation datasets, not an epidemiological data warehouse. Proposed concepts such as `proxy` are roles or transfer tags unless a separately versioned schema change extends the protected status enums.

### Search scope and negative-result provenance

The search covered the Government of Jersey open-data catalogue, gov.je States reports, gov.je Freedom of Information releases, Statistics Jersey publications, Public Health/Health and Care Jersey respiratory reports, and the Jersey Care Commission public site, using the dataset categories named in this dossier. Candidate sources were retained only when an official landing page or publication could be identified and its population, period, and measure could be described. The care-home search found guidance, inspection context, death-place material, and isolated releases, but no stable complete aggregate outbreak series with a consistent outbreak definition and denominator. This is a bounded negative result, not proof that no unpublished or later source exists. URL availability was checked during research, but no archived status/redirect log was created; acquisition must perform and preserve that check reproducibly.

## Dataset inventory

All URLs were checked on 30 August 2026. “Complete” refers to the stated source universe, not all infections in Jersey.

### R5-D01 — Archived COVID cases, PCR tests, deaths, and legacy inbound fields

- **Publisher/source:** Public Health, Government of Jersey; [Open Data dataset landing page](https://opendata.gov.je/dataset/coronavirus-covid-19-number-of-cases-in-jersey); consolidated [CSV resource metadata](https://opendata.gov.je/dataset/coronavirus-covid-19-number-of-cases-in-jersey/resource/19454b59-b6da-4cb4-a9c7-93e5a52ad5a5); direct CSV endpoint `https://www.gov.je/Datasets/ListOpenData?ListName=Coronavirus(COVID-19)DataforJersey&type=CSV`.
- **Period:** dataset created 10 March 2020; routine graph/data updates ended 31 January 2023. The consolidated resource was last marked updated 11 October 2023. Exact first/last record dates and revisions must be confirmed from the acquired file.
- **Granularity:** dated aggregate records. Consolidated fields are date, total PCR tests, cumulative confirmed positives, rolling seven-day cases per 100,000, and cumulative deaths. Legacy resources include negative/pending tests, inbound-travel reasons, and death breakdowns.
- **Completeness:** official reported PCR/test system, not all infections. Legacy resource definitions changed on 11 May 2021 when mortality and inbound fields were combined/renamed; weekday then weekly publication schedules also changed.
- **Machine-readability:** high (CSV/JSON/XML), although the direct endpoint is mutable and must be snapshotted. CKAN resource metadata and the file both need hashes.
- **Calibration/validation target:** daily/weekly reported cases jointly with testing volume; broad epidemic timing/growth; cumulative reported burden. Legacy inbound fields can constrain import observation, not import incidence.
- **Ascertainment caveats:** eligibility, availability, repeat testing, screening, border testing, confirmatory practice, reporting lag, and LFT use changed. The current dashboard defines cases by PCR swab date; excluded/rejected/inconclusive tests are not in current test totals. Death definitions require their own metadata.
- **Registry decision:** **yes**, under [Open Government Licence – Jersey v1.0](https://www.gov.je/ServiceManual/opendata/Pages/open-government-licence-jersey-ogl-j-v1-0.aspx), with required attribution. Acquire each selected resource as an immutable snapshot; preserve raw column names and definition/version notes. Do not use a Power BI export as the authoritative snapshot where an official file exists.
- **Evidence role:** **observed surveillance data**, measured through a changing observation process.

### R5-D02 — Current respiratory epidemiological reports (COVID, influenza, RSV, ILI)

- **Publisher/source:** Public Health Intelligence, Health and Care Jersey; [report landing page](https://www.gov.je/Government/Pages/StatesReports.aspx?ReportID=5645); [current PDF URL](https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/Epidemiological%20Report.pdf).
- **Period:** each report covers a recent reporting month/season and historical comparator seasons. The 9 April 2026 final 2025/26 report contains influenza-like illness profiles from 2018/19 onward, season-to-date influenza/RSV comparisons, and the preceding 12 months of COVID PCR indicators.
- **Granularity:** weekly GP influenza-like illness charts; season-to-date laboratory-positive influenza A/B and RSV tables; monthly COVID PCR tests and positives, with counts rounded to tens and values below five suppressed where stated.
- **Completeness:** recurring official summary, not a stable downloadable time-series archive. The generic PDF filename may be replaced by a later issue. Reporting steps down outside winter.
- **Machine-readability:** low to medium; PDF tables may extract, charts require controlled transcription/digitisation and second-person verification.
- **Calibration/validation target:** seasonal peak week, relative season shape, cross-pathogen timing, recent COVID PCR observation rate. Prefer holdout validation over primary calibration unless tabular source data are obtained.
- **Ascertainment caveats:** general-population/pre-admission/asymptomatic COVID PCR screening ceased in 2023; PCR is now clinically indicated. Four-in-one LFT results were excluded pending quality assurance in the April 2026 report. Flu testing and behaviour changed during COVID; GP ILI is syndromic and attendance-dependent.
- **Registry decision:** **conditional yes**. Dated official report pages/PDFs may be preserved for research/internal use under [gov.je terms](https://www.gov.je/Pages/Terms.aspx), with copyright attribution, retrieval date, checksum, page/table locator, and manual-transcription evidence. Do not register a mutable “latest.pdf” without the acquired snapshot and report date.
- **Evidence role:** **observed proxies** for respiratory activity, not infection truth.

### R5-D03 — JGH admitted patients testing positive, 2022–2024

- **Publisher/source:** Health and Care Jersey via the Freedom of Information office; [official FOI response 8247](https://www.gov.je/Government/FreedomOfInformation/pages/foi.aspx?ReportID=8247) and its attached COVID/infection tables.
- **Period:** admissions from 1 January 2022 through 31 December 2024.
- **Granularity:** month × pathogen counts for COVID, influenza, RSV, norovirus and others; first positive per patient admission. Annual totals are supplied where disclosure permits.
- **Completeness:** laboratory-confirmed infections among admitted patients; “treated as” diagnoses without laboratory confirmation are excluded. It does not distinguish admission because of infection from incidental positive status.
- **Machine-readability:** low; small PDF tables. Values `<5` are interval-censored, not zero and not missing.
- **Calibration/validation target:** monthly severe-care/healthcare-burden proxy after a severity and admission observation model exists; cross-check seasonal timing.
- **Ascertainment caveats:** testing practice, admission threshold, length of stay, hospital outbreaks, vaccination, age mix, and incidental positives can change. Attribution is to the month of first laboratory report, not admission or symptom onset. Influenza A/B are combined monthly; 199 influenza positives over three years comprised 191 A and 8 B.
- **Registry decision:** **conditional yes** as a public aggregate FOI release. Preserve the FOI page and attachments with checksums and gov.je copyright/terms; encode `<5` as interval `[0,4]` (or `[1,4]` only if the publisher confirms nonzero), never impute a point value in the canonical raw layer.
- **Evidence role:** **observed hospital-surveillance proxy**, explicitly not pathogen-caused hospitalisation.

### R5-D04 — Community SARS-CoV-2 antibody surveys, 2020

- **Publisher/source:** Statistics Jersey. [Round 1 report](https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/R%20Prevalence%20of%20antibodies%202020508%20SJ.pdf); [round 2 official release](https://www.gov.je/News/2020/Pages/Community-antibody-survey-report-published.aspx); [round 3 report](https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/R%20Prevalence%20of%20antibodies%2020200707%20SJ.pdf). An [essential-worker survey](https://www.gov.je/News/2020/Pages/EssentialWorkerSurveyReport.aspx) is a separate nonrepresentative population.
- **Period:** round 1 fieldwork 29 April–5 May 2020; round 2 around late May/early June; round 3 published 7 July 2020. Confirm exact field dates from each frozen report before registry entry.
- **Granularity:** survey-round population prevalence with uncertainty; some broad age, sex, and geography tables; longitudinal repeat-participant transitions in round 3.
- **Completeness:** adults aged 16+ in sampled private households. Under-16s and communal establishments such as care homes were excluded. Round 3 sampled 745 households/1,386 people; household response 60% and estimated individual response 59%.
- **Machine-readability:** low; PDF tables/manual extraction.
- **Calibration/validation target:** cumulative infection prevalence by survey window, through a seroconversion/waning and diagnostic-error likelihood. It is the best public local constraint on early under-ascertainment.
- **Ascertainment caveats:** cluster sampling, weighting to 2011 Census age/sex/household size, residual nonresponse bias, infection-to-antibody lag, antibody loss, and uncertain test sensitivity/specificity. Device changed after round 1. Round 3 used DNA World/CTK kits and reported adjusted prevalence 4.0% ±1.2 percentage points; round 2 reported 4.2% ±1.3 points. These are not directly interchangeable with PCR cumulative cases.
- **Registry decision:** **conditional yes**, preserving each public aggregate report with page/table locator and gov.je copyright terms. Record test device, assumed sensitivity/specificity, target population, weighting, and field dates as data, not prose-only notes.
- **Evidence role:** **observed survey estimate**; essential-worker results are a **selection-biased proxy**, not population prevalence.

### R5-D05 — COVID-19 and influenza vaccination

- **Publisher/source:** Public Health, Government of Jersey. [Archived COVID vaccination open data](https://opendata.gov.je/dataset/coronavirus-covid-19-vaccination-statistics), direct CSV endpoint `https://www.gov.je/Datasets/ListOpenData?ListName=COVID19Weekly&clean=true`; later programme reports in the [Public Health report directory](https://www.gov.je/Health/PublicHealth/Pages/StatesReports.aspx), including [Autumn 2025 COVID/influenza](https://www.gov.je/Government/Pages/StatesReports.aspx?ReportID=6002) and [Spring 2026 COVID booster](https://www.gov.je/Government/Pages/StatesReports.aspx?ReportID=6045).
- **Period:** open dataset created 4 May 2021 and metadata last updated 11 May 2021, though the endpoint was described as weekly; the actual snapshot range must be inspected. Programme PDFs provide campaign-specific later coverage, including Autumn 2025 and Spring 2026.
- **Granularity:** archived weekly cumulative total doses and age-group doses/coverage; later reports provide campaign totals, age/eligible-group coverage, vaccine types, and selected care-home coverage.
- **Completeness:** administered doses recorded by the programme. Denominators and eligible cohorts vary by campaign; some clinical-risk denominator quality is explicitly uncertain.
- **Machine-readability:** high for archived CSV/JSON/XML; low for later PDFs.
- **Calibration/validation target:** dated vaccine coverage/administration covariate for future named-pathogen immunity models; validate simulated uptake by age/eligible group. It cannot calibrate biological efficacy without external evidence.
- **Ascertainment caveats:** cumulative doses are not unique people; dose number, product, campaign, eligibility, prior infection, and denominator vintage matter. Autumn 2025 eligibility narrowed to age 75+, older-care-home residents, and immunosuppressed people, so coverage is not comparable with earlier broad campaigns.
- **Registry decision:** **yes** for open data under OGL-J; **conditional yes** for dated public PDFs under gov.je terms. Register each campaign separately and never merge percentages without exact numerator/denominator definitions.
- **Evidence role:** **observed intervention delivery/coverage**, not infection or transmission effect.

### R5-D06 — Influenza-like illness and influenza vaccination/deaths

- **Publisher/source:** Public Health Intelligence; [Influenza and Winter Illness Report 2024 landing page](https://www.gov.je/Government/Pages/StatesReports.aspx?ReportID=5969) and [PDF](https://www.gov.je/SiteCollectionDocuments/Health%20and%20wellbeing/Influenza%20and%20Winter%20Illness%20Report%202024.pdf).
- **Period:** 2024/25 winter with weekly ILI comparators from 2017/18–2024/25; vaccination for 2024/25; influenza/pneumonia deaths 2015–2024.
- **Granularity:** weekly GP ILI chart; vaccination uptake by eligible age group and timing; annual death counts. The 2025 publication withheld newly identified hospital-positive influenza datasets pending validation.
- **Completeness:** GP Central Server/EMIS presentations by resident patients; not all symptomatic people and not lab-confirmed influenza. Vaccination integrates GP, pharmacy, and child immunisation systems. Deaths combine influenza and pneumonia and are a mortality proxy.
- **Machine-readability:** low to medium; tables are extractable but the time series is plotted.
- **Calibration/validation target:** influenza seasonal timing and relative shape; age-specific vaccine delivery; annual order-of-magnitude checks. Avoid fitting absolute infection incidence directly to ILI.
- **Ascertainment caveats:** care-seeking and coding change; other respiratory viruses cause ILI; COVID-era behaviour/testing affects comparisons. The report itself says historical comparisons should be used as a guide.
- **Registry decision:** **conditional yes** with dated snapshot, page/table locator, transcription audit, and gov.je attribution. Prefer unpublished official tabular extracts if later released under OGL-J.
- **Evidence role:** ILI and influenza/pneumonia deaths are **proxies**; vaccine counts are **observed programme data**.

### R5-D07 — RSV laboratory positives

- **Publisher/source:** Public Health Intelligence respiratory reports ([landing page](https://www.gov.je/Government/Pages/StatesReports.aspx?ReportID=5645)) and JGH FOI 8247 ([response](https://www.gov.je/Government/FreedomOfInformation/pages/foi.aspx?ReportID=8247)).
- **Period:** seasonal comparator tables in recent respiratory reports (at least 2021/22–2025/26 in the April 2026 issue); monthly admitted-patient positives for 2022–2024.
- **Granularity:** season-to-date cumulative community/diagnostic positives by season and monthly inpatient positives with suppression.
- **Completeness:** tested, laboratory-confirmed patients only; general-population denominator and stable test protocol are absent.
- **Machine-readability:** low; PDF tables.
- **Calibration/validation target:** RSV season timing and relative burden; hospital proxy only after a severity/testing model. Age-specific infant burden is not publicly resolved in these sources.
- **Ascertainment caveats:** test eligibility, multiplex assay introduction, four-in-one LFT exclusion, healthcare seeking, age mix, and `<5` suppression. Cross-season totals are not stable ascertainment fractions.
- **Registry decision:** **conditional yes**, using the same snapshot/censoring rules as R5-D02/D03.
- **Evidence role:** **observed laboratory-surveillance proxy**.

### R5-D08 — Care-home outbreaks

- **Publisher/source:** no suitable complete public aggregate time series identified. The [Jersey Care Commission COVID-19 page](https://carecommission.je/covid-19/) provides guidance/inspection context, not an outbreak dataset. COVID death-place resources on the open-data page are outcomes, not outbreaks.
- **Period/granularity/completeness:** unavailable. Named inspection reports and isolated FOI references do not establish consistent weekly outbreak counts, case definitions, resident denominators, or complete facility coverage.
- **Machine-readability:** unavailable for a defensible outbreak series.
- **Calibration/validation target:** none currently. A future aggregate series could validate institutional outbreak frequency, size, duration, and resident/staff split.
- **Ascertainment caveats:** definition of outbreak, testing intensity, repeat outbreaks, facility occupancy, residents versus staff, disclosure suppression, and reporting completeness would all need documentation.
- **Registry decision:** **no current source to register as an outbreak target**. Do not scrape named-facility inspection reports or seek restricted resident/staff data. Request an official aggregate release with disclosure control.
- **Evidence role:** current absence is a **documented evidence gap**, not zero outbreaks.

### R5-D09 — School absence and reported school cases

- **Publisher/source:** Government of Jersey FOI releases: [Year 1 weekly absence, September 2020–January 2023](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=6195) with attached `Attendance data.xlsx`; [weekly school absence, September–December 2020](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=4214); [COVID cases by school year group, 2021/22](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=5938); and [weekly pupil/staff cases, September–October 2022](https://www.gov.je/government/freedomofinformation/pages/foi.aspx?ReportID=5918).
- **Period:** fragmented windows from September 2020 through January 2023, differing by release.
- **Granularity:** weekly counts/percentages; one release is Year 1 in government schools, others split primary/secondary or pupil/staff/year group. Definitions mix authorised, unauthorised, and COVID-related absence; some case totals count positive tests rather than unique children.
- **Completeness:** incomplete school universe and time coverage. Highlands, private nurseries/schools, or individual establishments may be excluded depending on release.
- **Machine-readability:** medium for the attached XLSX; low for PDF/HTML tables.
- **Calibration/validation target:** school calendar/contact-regime timing, broad age-pattern checks, or a syndromic absence observation model. Not suitable as direct infections or a stable attack rate.
- **Ascertainment caveats:** absence combines illness, isolation, shielding, class closure, authorised/non-authorised reasons, school policy, testing availability, and repeat tests. Denominators and term weeks must be joined explicitly.
- **Registry decision:** **conditional yes** for a bounded proxy study, preserving each FOI release/attachment and exact universe. Do not merge releases into a continuous series without a documented harmonisation decision.
- **Evidence role:** **weak proxy/contextual covariate**.

### R5-D10 — Border testing and intervention timeline

- **Publisher/source:** dated official announcements and policies, supplemented by the [Jersey Independent COVID-19 Review](https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/Report%20of%20the%20Jersey%20Independent%20Covid19%20Review.pdf). Anchor sources include [Stay Home from 30 March 2020](https://www.gov.je/News/2020/Pages/StayAtHome.aspx), [border testing trial from 1 June 2020](https://www.gov.je/News/2020/pages/bordertesting.aspx), [Safer Travel introduced 3 July 2020](https://www.gov.je/Health/Coronavirus/CoronavirusDocuments/P%20COVID-19%20Winter%20Strategy%20Update%202021%20to%202022.pdf), [2 November 2021 testing exemptions](https://www.gov.je/Health/Coronavirus/CoronavirusDocuments/P%20COVID-19%20Winter%20Strategy%20Update%202021%20to%202022.pdf), and [Safer Travel suspension on 7 February 2022](https://www.gov.je/News/2022/Pages/policysuspended.aspx).
- **Period:** principally March 2020–April 2023, with exact effective times supplied by individual notices. The independent review covers the response through early 2022.
- **Granularity:** event-level effective dates/policy regimes; selected aggregate testing-composition facts. The review reports that, from 1 July 2020 to its cutoff, testing comprised approximately 50% inbound, 43% surveillance, and 7% healthcare-seeking tests.
- **Completeness:** no single machine-readable legal/policy timeline was found. The review is retrospective; announcements can describe planned dates later superseded. For example, a 31 March 2022 isolation-law removal plan was extended to end-April because of BA.2 ([18 March 2022 notice](https://www.gov.je/News/2022/pages/isolationrequirementextended.aspx)).
- **Machine-readability:** low; HTML/PDF manual extraction. A canonical event table is straightforward once sources are frozen.
- **Calibration/validation target:** exogenous scenario timing and observation-regime breakpoints; border-testing periods for import detection/ascertainment. These dates do not identify intervention effect sizes by themselves.
- **Ascertainment caveats:** policy announcement, legal commencement, guidance, operational delivery, and adherence are different dates/quantities. From 2 November 2021, fully vaccinated/recently recovered/pre-departure-PCR arrivals could avoid arrival testing, reducing visibility of imported infections. Border-test counts are not imported cases.
- **Registry decision:** **conditional yes**. Register each official source snapshot, then one canonical event per sourced effective date with `announced_at`, `effective_from`, `effective_to`, legal/guidance/operational status, population/routes affected, and transformation ID. Retain superseded plans; do not overwrite them.
- **Evidence role:** **observed policy/context evidence**; intervention-effect multipliers remain assumptions or calibrated parameters.

## External scientific evidence for use in calibration

The Jersey inventory is primary-source work; three general principles are needed to prevent misuse.

**R5-E01 — Evidence.** Surveillance data are generated by infections plus care-seeking, test eligibility, test performance, reporting, and delay processes. The WHO's COVID surveillance guidance explicitly treats case definitions, testing strategy, and reporting as part of interpretation ([WHO COVID-19 surveillance guidance](https://www.who.int/publications/i/item/WHO-2019-nCoV-SurveillanceGuidance-2022.2), accessed 30 August 2026).

**R5-E02 — Evidence.** Seroprevalence must account for study design and assay sensitivity/specificity; the Statistics Jersey reports themselves perform such adjustment and describe residual uncertainty. In JOS this requires a survey observation likelihood, not a direct equality to recovered proportion.

**R5-E03 — Evidence.** Intervention timing and epidemic outcomes are confounded by contemporaneous behaviour, testing, susceptibility, and other policies. This dossier therefore treats the timeline as an input/covariate and does not infer causal multipliers from before/after plots.

**R5-A01 — Assumption.** Jersey's small population and changing test regimes make a multi-stream, regime-aware likelihood preferable to fitting one case curve. This is a modelling recommendation, not a finding that the available streams are jointly sufficient for identifiability.

## Candidate data-use designs

| Candidate | Description | Merits | Failure mode | Disposition |
|---|---|---|---|---|
| Single reported-case curve | Fit incidence scale/timing directly to COVID positives | Simple | Confounds transmission with testing and policy; fails after regime changes | Reject. |
| Dashboard transcription | Copy values from live Power BI/chart | Quick | Mutable, unversioned, difficult to reproduce | Reject when an official file/report exists. |
| **Immutable multi-stream registry** | Freeze official aggregate files/reports; canonicalise cases, tests, serology, vaccination, hospital proxies and policy regimes separately | Auditable; preserves definitions; supports explicit observation models | More metadata/manual QA | **Preferred.** |
| Unified “respiratory incidence” series | Harmonise COVID, influenza, RSV, and ILI into one curve | Convenient | Erases pathogen/test/denominator differences | Reject. |
| Restricted record linkage | Patient-level tests/admissions/vaccination | Potentially powerful | Outside scope, governance-heavy, unnecessary for V1.1 | Do not pursue in this programme. |

## Preferred design and priority order

1. **First acquisition tranche:** R5-D01 archived COVID cases/tests; R5-D04 serology; R5-D05 archived vaccination; R5-D10 intervention/testing-regime events. Together these constrain early cumulative burden, reported incidence conditional on testing, intervention dates, and vaccine exposure.
2. **Second tranche:** R5-D02/D06/D07 respiratory and influenza/RSV reports plus R5-D03 hospital-positive FOI. Use primarily for validation and seasonal timing until stable observation models and tabular data exist.
3. **Exploratory proxies:** R5-D09 school releases. Register only for a predefined analysis; do not make them core calibration targets.
4. **Evidence request:** R5-D08 care-home outbreaks. Seek aggregate weekly outbreak counts, residents/staff split if disclosure-safe, facility denominator, definition, and reporting completeness. No patient/facility-identifiable data are required.

Use at least two time axes where sources demand it: specimen/swab/report dates for observations and effective dates for policy. Do not convert one to the other without an explicit delay model. Split COVID calibration into predeclared testing regimes, at minimum: early limited testing; expanded community/surveillance and border testing; vaccination-era/arrival-rule changes; February 2022 de-escalation; January/August 2023 surveillance step-downs. Final boundaries must be sourced from the canonical timeline rather than inferred from curve changes.

## Parameter and provenance strategy

Preserve the existing source-registry contract and add epidemiological metadata in a dedicated, versioned canonical schema rather than free-text notes alone. Each series needs:

- `source_id`, immutable snapshot path and SHA-256, publisher, URL, retrieval date, licence/terms, reference period, and source locator;
- pathogen, measure, unit, numerator, denominator, geography, age/group, event date type, frequency, and revision/publication date;
- case/test/admission/survey definition; coverage universe; reporting cadence; observation regime ID; lower/upper bounds for suppressed cells; missingness reason;
- raw value and canonical value, with transformation ID; no destructive replacement of `<5`, rounded values, or cumulative fields;
- evidence role: `calibration_target`, `validation_target`, `context_covariate`, or `not_usable`; observation status: `observed`, `derived`, or `proxy`;
- extraction method (`direct`, `table_extract`, `manual_transcription`, `digitised_chart`) and independent-verification evidence for manual/digitised values;
- known revisions and superseded records, without overwriting the earlier snapshot.

The OGL-J applies to datasets expressly made available on opendata.gov.je and requires attribution. Ordinary gov.je reports/FOIs are subject to the website's copyright terms: reproduction for research/private study/internal circulation is permitted if accurate, non-misleading, and attributed; third-party material is excluded. Registry entries must record the actual applicable terms, not the placeholder phrase “where applicable.” Legal uncertainty should block republication of a snapshot, not internal source metadata or linking.

Calibration configuration must reference source hashes and a predeclared likelihood/transformation version. Any inferred ascertainment fraction, delay distribution, severity probability, or intervention effect is `calibrated`/`derived`, not `observed`. External natural-history priors remain `literature_prior`; scenario-only values remain `scenario_assumption`.

## Risks

- **Mutable sources:** direct gov.je list endpoints and the respiratory `Epidemiological Report.pdf` can change in place. Snapshot at acquisition and hash immediately.
- **Regime confounding:** observed case decline can be a testing-policy decline. Model tests and cases jointly and introduce sourced breakpoints.
- **Cumulative/daily confusion:** differentiate cumulative counts, incident counts, and rolling rates; never difference a revised cumulative series without preserving negative corrections and documenting the transform.
- **Suppression:** `<5` is interval censoring. Zero substitution biases small-island series; midpoint imputation creates false precision.
- **Small denominators:** parish, age, hospital, care-home, and school strata are noisy and disclosure-controlled. Prefer aggregated likelihoods and exact denominators.
- **PDF extraction:** chart digitisation can create transcription precision that the publication never claimed. Preserve original rounding and page/image evidence.
- **Serology comparability:** round 1 used a different device; communal settings and children were excluded. Do not force a single smooth prevalence series.
- **Hospital semantics:** “admitted patient testing positive” is not “admitted because of disease.” Labels, reports, and likelihood names must preserve that distinction.
- **Policy causality:** correlated interventions and voluntary behaviour make isolated effect estimates weak. Timeline dates are scenario inputs, not causal evidence.
- **Cross-pathogen changes:** multiplex/LFT adoption and COVID-era behaviour alter influenza/RSV observations. Do not interpret cross-season counts under constant ascertainment.
- **Coverage gaps:** absence of a public care-home series is not evidence of no outbreaks. School FOIs are fragmented and should not silently define all schools.
- **Governance creep:** record-level linkage could create privacy/legal obligations and is unnecessary for the stated roadmap. Keep acquisition aggregate-only.

## Testable acceptance criteria

These are criteria for a later data-registration/calibration milestone; R5 itself remains nonblocking.

| ID | Acceptance criterion |
|---|---|
| **R5-AC01** | Every acquired source has a strict registry record with nonempty publisher, direct official URL, retrieval date, exact reference period, licence/terms, acquisition method, local snapshot, and lowercase SHA-256 that matches the file. Unknown fields and hash mismatches fail validation. |
| **R5-AC02** | A second build with network disabled produces byte-identical canonical tables solely from registered snapshots; no build reads a live dashboard or mutable endpoint after acquisition. |
| **R5-AC03** | Canonical epidemiological rows include pathogen, measure, unit, event-date type, frequency, coverage universe, observation-regime ID, evidence role, source hash/locator, and transformation ID. Missing any required semantic field fails validation. |
| **R5-AC04** | The COVID open-data ingestion preserves raw tests, cumulative positives, rolling rate, and deaths as distinct measures. Any derived incident series reconciles back to the published cumulative series except explicitly recorded revisions/corrections. |
| **R5-AC05** | At least one fixture spanning a sourced testing-policy breakpoint proves that records on either side carry different observation-regime IDs; a calibration run cannot assume one ascertainment parameter across them unless its config explicitly overrides the guard and records the assumption. |
| **R5-AC06** | Every `<5` hospital/respiratory value is stored with raw token and bounds, never as zero or a point estimate in the raw/canonical layer. The likelihood consumes censoring bounds. |
| **R5-AC07** | Serology rows store field dates, target population, sample size, sampling design, weighting, assay, sensitivity, specificity, estimate, and interval. A model-data comparison applies the registered assay/survey transformation and does not compare prevalence directly to `R` or cumulative reported cases. |
| **R5-AC08** | Vaccination records include campaign, dose/product where available, numerator, exact eligible denominator/source, age/group, and date. Two campaigns with different eligibility cannot be concatenated into one coverage series by the canonicaliser. |
| **R5-AC09** | A hospital output exposed to users is labelled “admitted patients testing positive” and its metadata states first positive per admission and non-causal admission status. A forbidden alias such as `covid_hospitalisations` fails a semantic-label test unless a different source explicitly measures causal admissions. |
| **R5-AC10** | Every manually transcribed or chart-digitised series has two independent extraction/verification records and exactly reconciles published totals/labels within the publication's rounding. Failure remains visible; it is not silently corrected. |
| **R5-AC11** | Policy events store announcement and effective dates separately. The March 2022 planned isolation removal and its later extension remain two sourced records; canonicalisation does not overwrite the superseded plan. |
| **R5-AC12** | No source snapshot or canonical row contains names, addresses, exact dates tied to identifiable individuals, facility-identifying outbreak line lists, or other personal data. Acquisition rejects a resource marked restricted/personal pending governance approval. |
| **R5-AC13** | Calibration output lists source snapshot hashes, transformations, likelihood versions, fitted versus fixed parameters, and calibration versus holdout targets. It never labels posterior/prediction intervals as supported by sources omitted from the likelihood. |
| **R5-AC14** | A synthetic recovery test generated from known surveillance/serology parameters recovers them within a predeclared tolerance or reports non-identifiability; this test precedes fitting Jersey data. |
| **R5-AC15** | Core calibration can run with care-home and school proxy sources absent. Their absence is reported as an evidence gap and never interpreted as zero counts. |
| **R5-AC16** | All published derived tables include the required OGL-J attribution for open-data sources and source/copyright attribution for gov.je report/FOI material. |

## Implementation implications

No implementation change is required for V1.1. A later approved milestone would minimally add:

- epidemiological `SourceRecord` metadata or a linked strict series-metadata schema, without weakening current registry/hash validation;
- immutable snapshots beneath one source ID per publication/resource revision;
- canonical long-form epidemiological, observation-regime, policy-event, vaccination, and survey tables with row provenance;
- explicit suppressed-value bounds and cumulative-series revision handling;
- deterministic extraction scripts for machine-readable sources and small reviewed transcription tables for PDFs;
- calibration adapters that model observations rather than passing reported cases directly to the disease engine;
- provenance-bound train/holdout definitions and synthetic recovery tests before Jersey fitting.

Do not add a general data platform, web scraper, patient database, or live dashboard dependency. The smallest useful extension is the existing immutable-registry pattern plus strict epidemiological semantics.

## Unresolved questions

1. Can Public Health provide stable CSV extracts behind the respiratory PDF charts, with historic revision/definition metadata? This would remove the largest manual-extraction risk.
2. What is the exact record range and full data dictionary of the current COVID and vaccination direct endpoints when snapshotted? Metadata dates are inconsistent with stated update schedules.
3. Are legacy inbound-test fields still available in a stable OGL-J resource, and do they distinguish test reason, arrival mode, result, and unique traveller without disclosure risk?
4. Can Health and Care Jersey publish causal admission categories or age bands for COVID/influenza/RSV, distinct from incidental positives and subject to safe aggregation?
5. What official care-home outbreak definition and aggregate series can be released without identifying facilities or residents?
6. Can CYPES provide a consistent all-school weekly denominator and absence-reason series, or should school proxies be dropped entirely?
7. Which COVID policy timeline should be considered authoritative where the independent review, announcement, law, and operational start differ? The event schema can preserve all, but scenario construction needs a declared precedence rule.
8. Which sources will be calibration targets versus held-out validation before any parameter fitting? This choice must be frozen before inspecting fit quality.
9. What minimal observation model is identifiable from cases/tests plus three serosurveys in Jersey's small population? Synthetic recovery should answer before real fitting.
10. May gov.je report/FOI snapshots be redistributed with a future public repository, or should only transforms/metadata be committed while acquisition remains reproducible under the website terms?

## Source register

All sources were accessed 30 August 2026. Dataset-specific links are given above; this table records the authoritative catalogue/terms pages and major reports.

| ID | Source | Publisher | Evidence class |
|---|---|---|---|
| R5-S01 | [COVID cases/tests/inbound Open Data](https://opendata.gov.je/dataset/coronavirus-covid-19-number-of-cases-in-jersey) | Public Health, Government of Jersey | Official aggregate surveillance; OGL-J. |
| R5-S02 | [Consolidated COVID CSV metadata](https://opendata.gov.je/dataset/coronavirus-covid-19-number-of-cases-in-jersey/resource/19454b59-b6da-4cb4-a9c7-93e5a52ad5a5) | Public Health | Official machine-readable resource metadata. |
| R5-S03 | [Coronavirus data for Jersey](https://www.gov.je/health/coronavirus/pages/coronaviruscases.aspx) | Government of Jersey | Current definitions/context; live dashboard not registry snapshot. |
| R5-S04 | [Respiratory epidemiological report](https://www.gov.je/Government/Pages/StatesReports.aspx?ReportID=5645) | Public Health Intelligence | Official surveillance report/proxies. |
| R5-S05 | [JGH admitted-patient positives FOI 8247](https://www.gov.je/Government/FreedomOfInformation/pages/foi.aspx?ReportID=8247) | Health and Care Jersey | Official censored hospital proxy. |
| R5-S06 | [Community antibodies round 1](https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/R%20Prevalence%20of%20antibodies%202020508%20SJ.pdf) | Statistics Jersey | Official probability survey. |
| R5-S07 | [Community antibodies round 2 release](https://www.gov.je/News/2020/Pages/Community-antibody-survey-report-published.aspx) | Statistics Jersey / Government of Jersey | Official probability-survey result. |
| R5-S08 | [Community antibodies round 3](https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/R%20Prevalence%20of%20antibodies%2020200707%20SJ.pdf) | Statistics Jersey | Official probability survey with longitudinal subset. |
| R5-S09 | [COVID vaccination Open Data](https://opendata.gov.je/dataset/coronavirus-covid-19-vaccination-statistics) | Public Health | Official intervention-delivery data; OGL-J. |
| R5-S10 | [Public Health report directory](https://www.gov.je/Health/PublicHealth/Pages/StatesReports.aspx) | Public Health Intelligence | Official catalogue of current/historic reports. |
| R5-S11 | [Influenza and Winter Illness Report 2024](https://www.gov.je/Government/Pages/StatesReports.aspx?ReportID=5969) | Public Health Intelligence | Official influenza/ILI/vaccination/death proxies. |
| R5-S12 | [Independent COVID-19 Review](https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/Report%20of%20the%20Jersey%20Independent%20Covid19%20Review.pdf) | Government of Jersey independent review | Retrospective policy/testing context. |
| R5-S13 | [OGL-J v1.0](https://www.gov.je/ServiceManual/opendata/Pages/open-government-licence-jersey-ogl-j-v1-0.aspx) | Government of Jersey | Legal reuse terms for opendata.gov.je datasets. |
| R5-S14 | [gov.je terms and conditions](https://www.gov.je/Pages/Terms.aspx) | Government of Jersey | Copyright/research/internal-use terms for reports/FOIs. |
| R5-S15 | [WHO COVID-19 surveillance guidance](https://www.who.int/publications/i/item/WHO-2019-nCoV-SurveillanceGuidance-2022.2) | World Health Organization | Authoritative observation/surveillance interpretation. |
