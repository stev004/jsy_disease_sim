# Jersey (Channel Islands) public data source inventory — V1.2 evidence foundation

**DRAFT — URLs verified 2026-09-03 by research agent; not yet snapshot-frozen.**

Scope: Bailiwick of Jersey (Channel Islands, pop ~103–105k). **Not New Jersey, USA** — most
generic search engines return New Jersey; every source below was confirmed to be the Channel
Island by fetching it.

Verification method: each "verified live" row was fetched this session with `curl` (browser
User-Agent) or WebFetch and the HTTP status, content-type, byte count and first/last data rows
were inspected. Where a summary-model reading of a PDF disagreed with the PDF itself, the PDF
text was extracted locally and the local extraction is what is recorded here (this happened
twice — the WebFetch summariser mis-attributed two Jersey PDFs to UK gov.uk publications).

**Caution — `www.gov.je` blocks default `curl`.** Requests without a browser User-Agent get
HTTP 500 with an "Attack ID" WAF page. Any fetcher/snapshot script must set a normal UA.

---

## Summary table

| # | Source | What | Format | Coverage | Granularity | Verified |
|---|--------|------|--------|----------|-------------|----------|
| 1.1 | gov.je `ListName=COVID19` (legacy list) | 112-column COVID surveillance extract: daily new cases, cumulative cases/tests, symptomatic/asymptomatic split, route of ascertainment, 7-day rate by age band, care-home/community/hospital cases, deaths by age/sex/place | CSV / XML / JSON | 2020-07-30 → 2023-02-01 | daily, island-wide; some age-band cuts | **Yes** — 200, `text/csv`, 375,979 B, 917 dated rows |
| 1.2 | gov.je `ListName=Coronavirus(COVID-19)DataforJersey` (current) | Cumulative tests, cumulative cases, 7-day rate/100k, cumulative deaths | CSV / XML / JSON | 2020-07-30 → 2026-07-29 | daily rows, sparse after Jan 2023 | **Yes** — 200, `text/csv`, 35,141 B, 1,295 rows |
| 1.3 | JHU CSSE `time_series_covid19_confirmed_global.csv` | Cumulative confirmed cases, Jersey as a UK province row | CSV (GitHub) | 2020-01-22 → 2023-03-09 | daily, island-wide | **Yes** — 200, Jersey row present, first non-zero 2020-03-22 (12), final 66,391 |
| 1.4 | OWID COVID compact dataset | cases, deaths, vaccinations for `country == "Jersey"` | CSV | 2020-01-04 → 2026-07-19 (cases to 2023-01-31) | daily, island-wide | **Yes** — 200, 179 MB, 2,389 Jersey rows |
| 1.5 | opendata.gov.je CKAN API | dataset/resource metadata, licences, direct file URLs | JSON API | live | n/a | **Yes** — `package_show` / `package_search` 200 |
| 2.1 | gov.je `ListName=COVID19` test columns | cumulative tests, tests by reason (symptomatic / inbound travel / on-island screening), pending, negatives, 7-day turnaround | CSV | 2020-08-03 → 2023-02-01 | daily | **Yes** (same file as 1.1) |
| 2.2 | Epidemiological Report for Respiratory Illnesses | COVID PCR testing rate + positives, ILI, flu A/B, RSV | PDF (rolling URL) | current season; 2025/26 edition dated 2026-04-09 | monthly report, weekly charts | **Yes** — 200, `application/pdf`, 475.6 KB, 3 pp |
| 3.1 | Statistics Jersey, *SARS-CoV-2: Prevalence of antibodies in Jersey* | **the** Jersey community serosurvey: 3.1% ± 1.3% adult prevalence | PDF, 20 pp | fieldwork 2020-04-29 → 2020-05-05 | one-off, island-wide, adults 16+ | **Yes** — 200, `application/pdf`, 1,561,733 B |
| 3.2 | gov.je news: Essential Worker Antibody Survey results | 7,850 essential workers tested, 300 antibody-positive (~3.8%) | HTML only | 21–29 May and 1–7 June 2020 | one-off, occupational cohort | **Yes** — 200; **no report PDF published** |
| 3.3 | gov.je news: community antibody testing rounds 1 & 2 | context/design for 3.1; round 2 announced | HTML | May 2020 | n/a | **Yes** — 200; round-2 page links only the round-1 PDF |
| 4.1 | gov.je `ListName=COVID19Weekly` (vaccination statistics) | doses 1–4 + autumn-2022 booster, counts **and** % coverage, by 14 age bands | CSV / XML / JSON | 2021-03-14 → 2023-01-29 | weekly, island-wide, age-banded | **Yes** — 200, `text/csv`, 78,034 B, 132 weekly rows × 155 cols |
| 4.2 | Statistics Jersey, *Insights from Jersey data on COVID-19 vaccinations and positive PCR tests* | linked administrative data: % double-vaccinated and % ever-PCR-positive by age, ethnicity, household type, occupation, census characteristics; time-to-first-dose | PDF, 28 pp | Feb 2020 → end 2022 | cumulative, by subgroup | **Yes** — 200, `application/pdf`, 2,120,900 B |
| 4.3 | OWID vaccination columns for Jersey | total_vaccinations, people_vaccinated, fully vaccinated, boosters (+per-hundred) | CSV | 2021-03-14 → 2023-01-29 (132 obs) | weekly | **Yes** (same file as 1.4) |
| 5.1 | 2021 Census — Population by Parish, Age and Sex | 12 parishes × sex × 17 five-year age bands | CSV | census day 2021-03-21 | parish × age × sex | **Yes** — 200, 3,585 B, 39 rows |
| 5.2 | 2021 Census — Population by age and gender | single year of age 0–95+, by sex | CSV | 2021 | island, single-year age | **Yes** — 200, 1,599 B, 96 rows |
| 5.3 | 2021 Census — Population and density by Parish | parish population + density | CSV | 2021 | parish | **Yes** — resource URL 200 (metadata verified) |
| 5.4 | 2021 Census — Population by Vingtaines | sub-parish (vingtaine) populations | CSV | 2021 | vingtaine (57) | **Yes** — 200, 2,540 B, 57 rows |
| 5.5 | 2021 Census — Households by household type and tenure | 12 household types × 7 tenures | CSV | 2021 | island | **Yes** — 200, 850 B, 12 rows |
| 5.6 | Annual population estimates by age and sex | resident population, single year of age × sex × year | CSV | 2011 → present | annual, island | **Yes** — 200, 23,605 B, 1,414 rows |
| 5.7 | Population and migration by sex, age group, nationality, CHWL status | 5-year age groups × nationality × residential status | CSV | 2017 → present | annual, island | **Yes** — resource URL from CKAN, 200 |
| 5.8 | Population projections 2025–2080 | 6 net-migration scenarios + projected births/deaths | CSV ×10 | 2025 → 2080 | annual, island | **Yes** — CKAN metadata 200 |
| 5.9 | 2021 Census Report (full) | methodology + annex tables | PDF | 2021 census, published 2022-12-13 | — | **Yes** — landing page 200 |
| 5.10 | stats.je population & migration 2024 reports | latest estimate 104,540 (end-2024) | PDF ×4 | 2024 | annual | **Yes** — index page 200 |
| 6.1 | Epidemiological Report for Respiratory Illnesses | ILI GP consultations, flu A/B positives, RSV positives, COVID PCR | PDF (rolling) | monthly in season | weekly series, island | **Yes** (same as 2.2) |
| 6.2 | Influenza and Winter Illness Report | GP ILI presentations, flu vaccine uptake, flu/pneumonia deaths 2015–2024 | PDF, 11 pp | winter 2024-25 (published 2025-09-04) | seasonal/annual | **Yes** — 200, `application/pdf`, 495.5 KB |
| 6.3 | opendata.gov.je Immunisation datasets | routine immunisation coverage at 12/24/60 months, teens, adults, flu | CSV ×6 | flu file 2014/15 → 2024/25 | annual/seasonal, island | **Yes** — flu CSV 200, 594 B, 11 rows |
| 6.4 | Public Health Data Explorer (PHOF) | 142 indicators incl. all routine vaccination coverage, COVID mortality rates, winter mortality index | XLSX | 1993 → 2025 | annual, mostly island; some age/sex | **Yes** — 200, 160,546 B, 2,370 rows |
| 6.5 | gov.je notifiable diseases page | the statutory notifiable list (~35 diseases) | HTML | current | n/a | **Yes** — 200; **no counts published** |
| 6.6 | Jersey Mortality Report 2024 | all-cause and cause-specific mortality | PDF | to 2024 | annual | Link present on gov.je COVID page; **PDF not fetched this session** |

**Verified live this session: 27 of 28 rows** (only 6.6 was not fetched). Licence for every
opendata.gov.je / gov.je `ListOpenData` item: **Open Government Licence – Jersey v1.0**
(`OGL-J-1.0`), text at
`https://www.gov.je/ServiceManual/opendata/Pages/open-government-licence-jersey-ogl-j-v1-0.aspx`
(HTTP 200).

---

## 1. COVID-era case counts

### 1.1 gov.je legacy COVID list — the richest single case file (HIGHEST VALUE)

- **URL (CSV):** `https://www.gov.je/Datasets/ListOpenData?ListName=COVID19`
  (also `&type=xml`, `&type=json`)
- **Publisher:** Public Health, Government of Jersey (surfaced via opendata.gov.je dataset
  `coronavirus-covid-19-number-of-cases-in-jersey`)
- **Format:** CSV / XML / JSON, served directly (no scraping needed)
- **Coverage:** 2020-07-30 → 2023-02-01, 917 dated rows, 112 columns
- **Granularity:** daily, island-wide. Some age structure: `7DayRateUnder18`, `7DayRate18to39`,
  `7DayRate40to59`, `7DayRateOver60`. **No parish breakdown.**
- **Verified:** HTTP 200, `text/csv; charset=utf-8`, 375,979 bytes (browser UA required)
- **Columns of highest modelling value** (verbatim header names, with observation counts):
  - `CasesDailyNewConfirmedCases` — 917 obs, full span. *This is the incidence series.*
  - `CasesTotalConfirmedPositiveCases` — 501 obs, 2020-08-03 → 2023-02-01 (final 66,391)
  - `CasesSymptomatic` / `CasesAsymptomatic` — 499 obs each
  - `CasesAverageAgeTestedPositive` — 499 obs
  - `CasesCurrentKnownActiveCases`, `CasesNumberOfKnownDirectContactsOfCurrentActiveCases`
  - `CasesKnownCasesInCareHomes` / `InCommunity` / `InHospital` — 499 obs each
  - Route of ascertainment: `CasesPositiveCasesIdentifiedSymptomaticIndividualsSeekingHealthcare`,
    `...InboundTravelArrivalsScreening`, `...AdmissionsScreening`, `...WorkforceScreening`,
    `...CohortScreening`, `...ContactTracing`, `CasesOldCasesConfirmedBySerology`
  - Mortality by age band (40-49 … 90+), sex, and place (hospital / St Saviours / care home /
    domestic)
  - Inbound-travel block: arrivals by traffic-light colour, air/sea, reason for travel
    (business, critical worker, holiday, resident returning, seasonal worker, student, VFR,
    crew) — counts and percentages
- **Snapshot method:** direct file URL, single GET with browser UA. Freeze all three formats.
- **Caveat:** this endpoint is a live SharePoint list rendering — it is *not* a versioned file.
  A `float;#0` string appears as a stray value in at least one cell; `-1` is used as a
  not-reported sentinel alongside empty strings. Parse defensively.

### 1.2 gov.je current COVID list

- **URL (CSV):** `https://www.gov.je/Datasets/ListOpenData?ListName=Coronavirus(COVID-19)DataforJersey&clean=true`
  (`&type=CSV` and `&type=json` variants are the ones registered in CKAN)
- **Coverage:** 2020-07-30 → 2026-07-29, 1,295 rows. Columns: `Date`, `TestsTotalTests`,
  `CasesTotalConfirmedPositiveCases`, `CasesSeven7DayNumberper100000`, `MortalityTotalDeaths`
- **Density by year (rows with a real case value):** 2020: 110/155 · 2021: 269/365 ·
  2022: 117/365 · 2023: 51/278 · 2024: 49 · 2025: 52 · 2026: 30
- **Verified:** HTTP 200, `text/csv`, 35,141 bytes
- **Reading:** cumulative-only. Post-2023 rows are a slow-moving cumulative total from residual
  PCR reporting, not epidemic signal. Useful mainly as a cross-check on 1.1 and for the
  7-day-rate series.

### 1.3 JHU CSSE — the only machine-readable source covering Jersey's **first wave**

- **URL:** `https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv`
  (row: `Province/State = "Jersey"`, `Country/Region = "United Kingdom"`, lat 49.2138, lon -2.1358)
- **Coverage:** 2020-01-22 → 2023-03-09 (daily columns). First non-zero 2020-03-22 (12 cases);
  final cumulative 66,391.
- **Verified:** HTTP 200, 1,819,904 bytes, Jersey row inspected
- **Why it matters:** gov.je's open-data feeds start 2020-07-30. **JHU is the only verified
  machine-readable series covering March–July 2020**, i.e. Jersey's first wave and the exact
  window the 2020 serosurvey (3.1) measures.
- **Licence:** JHU CSSE terms — free for educational/academic/research use with attribution;
  the repository is archived (no longer updated after March 2023), which makes it a stable
  snapshot target. Sister files: `..._deaths_global.csv`, `..._recovered_global.csv`.

### 1.4 Our World in Data

- **URL:** `https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv`
  (filter `country == "Jersey"`)
- **Coverage:** 2,389 Jersey rows, 2020-01-04 → 2026-07-19. `new_cases` non-zero
  2020-03-12 → 2023-01-31 (870 obs). `population` field = 103,493.
- **Verified:** HTTP 200, 179,419,823 bytes (large — filter on download)
- **Licence:** OWID data CC-BY 4.0.
- **Populated Jersey columns:** cases, deaths, vaccinations (+ per-capita variants), code,
  continent, population, median_age, life_expectancy. See §Gaps for what is empty.

### 1.5 opendata.gov.je CKAN API (discovery layer)

- `https://opendata.gov.je/api/3/action/package_show?id=<slug>` and
  `.../package_search?q=<term>&rows=N` — both HTTP 200, JSON.
- Coronavirus group holds exactly three datasets:
  `coronavirus-covid-19-number-of-cases-in-jersey` (17 resources),
  `coronavirus-covid-19-vaccination-statistics` (3 resources),
  `coronavirus-covid-19-operational-status-dashboard` (3 resources, "no longer maintained").
- Dataset note, verbatim: *"Weekly updates to graphs and data ended on 31 January 2023."*

---

## 2. COVID testing volumes

### 2.1 Testing columns inside the legacy list (1.1) — the only detailed testing data

- Same URL as 1.1. Verified in the same fetch.
- `TestsTotaltests` — 499 obs, 2020-08-03 → 2023-02-01 (final 1,140,136 cumulative swabs)
- `TestsTotalsamplestestedpriorto1July2020` / `...since1July2020` — the pre/post-July-2020 split
- **Tests by reason** (cumulative): `TestsReasonfortestseekinghealthcaresymptomatic` (496 obs,
  final 103,522), `TestsReasonforTestInboundTravel`, `TestsReasonforTestOnIslandSurveillanceScreening`
- Weekly reason cuts: `TestReasonbyWeekInboundTravel`, `...OnIslandSurveillanceScreening`,
  `...SeekingHealthcareSymptomatic`
- `TestsPendingResults`, `TestsTotalNegativeTests`, `TestsAverageTurnaroundTimeAllSwabsLast7days`
- **Granularity:** daily, cumulative counts (differencing gives daily volume), island-wide.
- **This is PCR only.** See §Gaps — LFT volumes are not published.

### 2.2 Epidemiological Report for Respiratory Illnesses (current-era testing rates)

- **URL:** `https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/Epidemiological%20Report.pdf`
- **Publisher:** Public Health Intelligence, Strategic Policy Planning and Performance, Government of Jersey
- **Verified:** HTTP 200, `application/pdf`, 475.6 KB, 3 pages. Local text extraction confirms
  it is Jersey: *"This report provides a summary of the available epidemiological data on the
  spread of influenza, COVID-19 (coronavirus) and RSV ... in Jersey."* Edition fetched is dated
  **09 April 2026** — the final report of the 2025/26 winter season.
- Contains COVID-19 PCR testing rates and positives over the last 12 months, as charts.
- The report states explicitly that positive-case data **currently includes PCR results only**,
  and that 4-in-1 LFT data "will be incorporated into future releases once quality assured" —
  so a step-down in reported positives after the LFT transition is a known artefact.
- **This is a rolling URL: each new edition overwrites the previous one.** Historic editions are
  not separately archived on gov.je. Wayback has snapshots (nearest checked: 2026-01-02).

---

## 3. Seroprevalence

### 3.1 Statistics Jersey — *SARS-CoV-2: Prevalence of antibodies in Jersey* (preliminary analysis)

**This is the Jersey community serosurvey. It exists, it is public, and it is a PDF.**

- **URL:** `https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/R%20Prevalence%20of%20antibodies%202020508%20SJ.pdf`
- **Publisher:** Statistics Jersey (analysis); survey conducted by Government of Jersey
- **Verified:** HTTP 200, `application/pdf`, 1,561,733 bytes, 20 pages, text extracted locally
- **Headline result, verbatim:** *"the estimated population prevalence rate of SARS-CoV-2
  antibodies is: **3.1% ± 1.3% (95% confidence interval)**"*
- **Design (from the report):** single-stage cluster sample; 700 private addresses randomly drawn
  from the **Jersey Land and Property Register (JLPR)**; all household members aged 16+ invited;
  fieldwork **29 April – 5 May 2020** (7 days); **438 households / 855 individuals** tested;
  response rate 63% households, ~65% individuals. Testing at three centres plus a mobile team
  (~70 households tested at home). Ethics approval 1 May 2020.
- **Test:** Healgen Scientific lateral-flow IgG/IgM rapid cassette, finger-prick whole blood.
- **Explicit exclusions:** under-16s; residents of communal establishments including **care homes**.
- **Known bias flagged in the report:** significant non-response among Islanders living in
  non-qualified accommodation.
- **Status:** labelled *preliminary*, "potentially subject to revision" — no revised version was
  found this session.
- **Reuse terms:** none stated on the PDF; Statistics Jersey outputs generally fall under
  OGL-J. **Treat licence as unconfirmed** and attribute.
- **Snapshot:** direct PDF URL (browser UA). Wayback copy available (2025-07-11).
- **Landing pages:** `https://www.gov.je/News/2020/pages/antibodytesting.aspx` (200) and
  `https://www.gov.je/News/2020/Pages/Antibody-survey-report-published.aspx` (200) — both link
  this same PDF.

### 3.2 Essential Worker Antibody Survey (occupational cohort)

- **URL:** `https://www.gov.je/news/2020/pages/EssentialWorkerSurveyReport.aspx` (HTTP 200)
- **Results, as published on the page:** 7,850 individuals tested; **300 antibody-positive
  (~3.8%)**; just over half of positives reported no symptoms. Fieldwork 21–29 May and
  1–7 June 2020; results published 14 July 2020.
- **Format: HTML news page only.** The page scraped this session contains **no PDF, XLSX or CSV
  link** — the full report referenced in the text is not published at a discoverable URL.
- Companion page: `https://www.gov.je/News/2020/Pages/EssentialWorkersAntibody.aspx` (200) —
  eligibility was working away from home 5+ times between 30 March and 11 May 2020.
- **Snapshot method: scrape the HTML.** For the underlying report → **FOI**.

### 3.3 Community antibody testing round 2

- `https://www.gov.je/News/2020/Pages/CommunityAntibodyTesting.aspx` and
  `https://www.gov.je/News/2020/Pages/communitytest.aspx` (200) announce a second round
  (contemporary press reporting puts it at ~30 May 2020).
- **The round-2 page links only the round-1 PDF.** No round-2 results report was found on
  gov.je, stats.je, statesassembly.gov.je, or Europe PMC. See §Gaps.

### 3.4 Peer-reviewed literature — one Jersey COVID paper, and it is not a serosurvey

- Gama S, Bellamy J, Couvert N, Liakopoulou E. **"Laboratory Features of Hospitalised Patients
  with COVID-19 in Jersey, UK."** *EJIFCC* 2022 Aug 8;33(2):105–120. PMID 36313915,
  PMC9562481. Verified via `https://pmc.ncbi.nlm.nih.gov/articles/PMC9562481/` (200).
- Retrospective observational: 81 lab-confirmed hospitalised cases, March–December 2020, vs 100
  controls. Median age 75 (28–94), 59.3% male, 33.3% mortality. No date-stratified counts.
- Platinum open access, CC BY-NC.
- Europe PMC searches run this session (`"Jersey" AND seroprevalence AND "Channel Islands"`
  16 hits; `seroprevalence AND "Jersey, Channel Islands"` 2 hits; `"Jersey" AND "Channel
  Islands" AND COVID-19` 42 hits) returned **no Jersey Channel Islands seroprevalence paper**.

---

## 4. Vaccination uptake

### 4.1 gov.je weekly vaccination statistics (HIGHEST VALUE for age-structured coverage)

- **URL (CSV):** `https://www.gov.je/Datasets/ListOpenData?ListName=COVID19Weekly&clean=true`
  (`&type=xml&clean=true`, `&type=json&clean=true`)
- **CKAN dataset:** `coronavirus-covid-19-vaccination-statistics` · **Licence: OGL-J-1.0**
- **Verified:** HTTP 200, `text/csv`, 78,034 bytes, **132 weekly rows × 155 columns**,
  **2021-03-14 → 2023-01-29**
- **Structure:** for each of doses 1, 2, 3, 4 and the Autumn 2022 booster, both a **dose count**
  and a **% of population vaccinated**, across 14 age bands:
  `5to11`, `12to15`, `16to17`, `17yearsandunder`, `18to29`, `30to39`, `40to49`, `50to54`,
  `55to59`, `60to64`, `65to69`, `70to74`, `75to79`, `80yearsandover`.
- Also carries `EligiblePopulation`, `VaccinationsDosesPer100PeopleInPopulation`,
  `7DayRatePercentageChange`, and the three test-reason columns.
- Sanity check on the last row (2023-01-29): 266,953 total doses; 84,365 first; 81,882 second;
  64,894 third. First row (2021-03-14): 45,758 doses; 40,137 first; 5,621 second.
- **Snapshot:** direct file URL, browser UA. This is the single best-structured Jersey COVID file.

### 4.2 Statistics Jersey — *Insights from Jersey data on COVID-19 vaccinations and positive PCR tests*

- **URL:** `https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/Insights%20from%20Jersey%20data%20on%20COVID19%20vaccinations%20and%20positive%20PCR%20tests.pdf`
- **Landing page:** `https://www.gov.je/Government/Pages/StatesReports.aspx?ReportID=5765`
- **Publisher:** Statistics Jersey (Covid Recovery Insights Project, funded by the Covid Health
  Recovery Fund) · **Published 8 December 2023**
- **Verified:** HTTP 200, `application/pdf`, 2,120,900 bytes, 28 pages, text extracted locally
- **Coverage:** tests from February 2020, vaccinations from December 2020, both to end-2022, for
  individuals resident in Jersey throughout 2020 and 2021.
- **Why it matters for calibration:** it is a **record-linked administrative-data** study giving
  the **cumulative proportion ever PCR-positive** — not just case counts — broken down by
  subgroup. Contains 8 tables and 21 figures, including:
  - Table 1 / Figure 2: % double-vaccinated and % ever-PCR-positive **by age group**
  - Table 2 / Figure 3: days until half the age group took up dose 1 (vaccination speed)
  - Figure 5, Table 3: age-standardised coverage **by ethnicity**
  - Table 4, Figures 12–13: **by household type**
  - Figures 9–10: **by occupation / working adults**
  - Tables 7–8: by census characteristics
  - Table 5: % double-vaccinated and % tested positive by age group
- **Caveat quoted in the report:** variation in positive-test proportions between groups
  "is not only a reflection of variations in infection rates" — differential testing regimes by
  workplace confound it. Use for structure, not as ground-truth attack rates.
- **Format is PDF with no accompanying CSV** — tables must be transcribed by hand or by OCR.

### 4.3 OWID vaccination columns

- Same file as 1.4. `people_vaccinated` 2021-03-14 → 2023-01-29, 132 observations — i.e. OWID is
  a re-serialisation of 4.1, not an independent source. Prefer 4.1.

### 4.4 Current-era vaccination coverage reports

- Public Health reports index: `https://www.gov.je/Health/PublicHealth/pages/statesreports.aspx`
  (200). Recent relevant entries seen: *COVID-19 Spring Booster 2026: Vaccination Coverage
  Report* (ReportID 6045, 23 Jul 2026) and *Seasonal Vaccination Update Report – COVID-19 &
  Influenza* (ReportID 6002, 15 Jan 2026).
- **Note:** the URL the CKAN dataset description points at for these
  (`/Government/Departments/StrategicPolicy/PublicHealth/Pages/StatesReports.aspx`)
  returns **HTTP 404** — the working path is the one above.

---

## 5. Population denominators

All items below are opendata.gov.je CKAN resources under **OGL-J-1.0**, served as static CSV
from `opendata.gov.je/dataset/<pkg-uuid>/resource/<res-uuid>/download/<filename>` — stable,
directly fetchable, no browser-UA trick needed.

| Resource | URL | Verified |
|---|---|---|
| **Population by Parish, Age and Sex (2021 Census)** | `https://opendata.gov.je/dataset/5840dfa1-8f67-4455-af42-241586ac8999/resource/24384097-b5f4-40b6-a0f3-2fcf7f7d683d/download/2021-census-parish-by-age-and-sex.csv` | 200, 3,585 B, 39 rows. Header: `Parish,Sex,< 5,5 - 9,…,80+,All`; 12 parishes × {Female, Male} |
| **Population by age and gender (2021 Census)** | `https://opendata.gov.je/dataset/5840dfa1-8f67-4455-af42-241586ac8999/resource/96bc726b-d820-4be1-933a-7080b139fd24/download/2021-census-age-gender.csv` | 200, 1,599 B, 96 rows. `Age,Male,Female,All`, single year of age |
| **Population and density by Parish** | `.../resource/8b9b106e-6bf6-400f-8a0b-a413204051e3/download/2021-census-parish-population-density.csv` | CKAN 200 (metadata) |
| **Population by Vingtaines** | `https://opendata.gov.je/dataset/5840dfa1-8f67-4455-af42-241586ac8999/resource/8a69b1b1-2675-44a1-93e4-a5b346959032/download/vingtaines-populations-2021-census.csv` | 200, 2,540 B, 57 rows. `Parish,Vingtaine,Persons` — **the finest published geography** |
| **Households by household type and tenure** | `.../resource/5eb10530-8847-4fc9-bb12-66114f05e562/download/2021-census-householdtype-tenure.csv` | 200, 850 B, 12 rows (Single adult, Couple (adult), … × 7 tenures) |
| **Household type by property type** | `.../resource/384078ae-1f1d-4136-aafa-0e0ac1fe4645/download/2021-census-householdtype-propertytype.csv` | CKAN 200 |
| **Annual population estimates by age and sex, 2011→present** | `https://opendata.gov.je/dataset/199794de-4927-457a-9fc4-569c0d2f7b47/resource/4f0988d8-c5d2-4bff-af72-0a314b95024a/download/annual-population-estimates-by-age-and-sex.csv` | 200, 23,605 B, 1,414 rows. `Year,Age,Male,Female` |
| **Population & migration by sex, age group, nationality, CHWL status (2017→)** | `https://opendata.gov.je/dataset/6e29738b-644a-45c2-87d3-786da4c76eff/resource/cd55f05d-fa0e-495e-bfda-69d27b9dbe9b/download/population-and-migration-by-age-group-nationality-and-chwl-status.csv` | CKAN 200 |
| **Population projections 2025–2080** | package `population-projections`, 10 CSV resources (net nil / +200 / +400 / +600 / +800 / legacy / summary, plus projected births and deaths) | CKAN 200 |
| **Long run census data 1821–2021** | `.../resource/ddc152a4-1da2-4180-96bb-a1e1767507c9/download/long-run-census-data.csv` | CKAN 200 |

The `2021-census` package holds **77 resources** in total — also of interest for a contact-network
model: *Usual mode of travel to work by parish*, *Economic Status by Age*, *Industry by Age*,
*Occupation by age*, *Accommodation Type by Parish*, *Cars/Vans by Parish*, *Self-assessed general
health by sex/tenure/place of birth*, *Longstanding health conditions by sex*, *Day-to-day
activities limited by health conditions*.

Supporting documents (not machine-readable):
- **2021 Census Report**, Statistics Jersey, published 13 Dec 2022 —
  `https://www.gov.je/Government/Census/Pages/Census2021Results.aspx` (200); report PDF at
  `https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/R%20CensusFinalReport%2020221213%20SJ.pdf`
  (**URL from search results, not fetched this session — verify before use**). Census day
  2021-03-21. Annex contains detailed age × sex × parish tables.
- **stats.je population index** — `https://stats.je/statistic/population/` (200). Latest estimate
  **104,540 at end-2024** (2023 revised to 104,030). Four 2024 reports published 2025-09-24 with
  `stats.je/wp-content/uploads/2025/09/R-Population-and-migration-2024-*.pdf` URLs (listed on
  the page; individual PDFs not fetched this session).
- OWID's Jersey `population` field is 103,493 — differs from the Statistics Jersey estimate.
  Use the Statistics Jersey figure for the denominator and note the discrepancy.

---

## 6. General infectious-disease surveillance

### 6.1 Epidemiological Report for Respiratory Illnesses (flu, COVID, RSV)

- **URL:** `https://www.gov.je/SiteCollectionDocuments/Government%20and%20administration/Epidemiological%20Report.pdf`
  · landing page `https://www.gov.je/Government/Pages/StatesReports.aspx?ReportID=5645`
- **Publisher:** Public Health Intelligence, Government of Jersey · monthly during the winter
  season, stepped down outside it. Edition fetched: **09 April 2026**, final report of 2025/26.
- **Verified:** HTTP 200, `application/pdf`, 475.6 KB, 3 pages; Jersey provenance confirmed by
  local text extraction.
- **Content:** influenza-like-illness case numbers, confirmed influenza A & B positives, RSV
  positives, with comparison to historic seasons; COVID-19 PCR testing rates and positives over
  the trailing 12 months. Season-to-date confirmed flu A+B in the fetched edition: 38.
- **Format is PDF charts** — no underlying CSV published.
- **Rolling URL, single ReportID.** Prior monthly editions are overwritten. Wayback has copies.

### 6.2 Influenza and Winter Illness Report

- **URL:** `https://www.gov.je/SiteCollectionDocuments/Health%20and%20wellbeing/Influenza%20and%20Winter%20Illness%20Report%202024.pdf`
- **Publisher:** Health and Care Jersey, Public Health Intelligence · **dated 04 September 2025**,
  covering **winter 2024-2025**
- **Verified:** HTTP 200, `application/pdf`, 495.5 KB, 11 pages, text extracted locally
- **Content:** resident patients presenting to GP with flu-like illness; annual seasonal flu
  vaccine uptake; **deaths from influenza and pneumonia 2015–2024**. ILI peaked mid-January,
  above pre-pandemic average; ~31,000 flu vaccinations delivered; 65% uptake in 65+.
- **Documented data gap inside the report:** all positive-influenza-test results were
  **excluded from this edition** pending quality assurance of two newly identified hospital
  admission datasets. So flu *positives* are missing from the 2024-25 edition.
- Filename carries the year, so prior editions likely exist at parallel URLs — **not verified**.

### 6.3 Immunisation datasets (opendata.gov.je)

- Package `immunisation`, 6 CSV resources, **OGL-J-1.0**: coverage at 12 months, 24 months,
  60 months, teenagers, adults, and flu.
- **Flu resource verified:** `https://opendata.gov.je/dataset/79afb43a-4f8c-4883-a0ec-5f5ea9fd57be/resource/0e2525be-4b3a-4224-a889-0e5d0afb058d/download/immunisation-flu.csv`
  — 200, 594 bytes, 11 rows, seasons **2014/15 → 2024/25**, columns: `Flu season`,
  `At risk working age (16-64 years)`, `Adults aged 65 and over`, `Pregnant women`,
  `Children aged 2-4 years`, `All immunisations in school`. Values are proportions.
- Note the dataset description points at
  `https://www.gov.je/Government/JerseyInFigures/Health/Pages/Immunisation.aspx`, which returns
  **HTTP 404**.

### 6.4 Public Health Data Explorer (PHOF indicators)

- **URL (XLSX):** `https://opendata.gov.je/dataset/267b016f-dffc-48a9-81a2-d537ab456d45/resource/edbbfd8e-5f26-4f45-82eb-13a424f7b169/download/phof-opendata.xlsx`
  · **Licence OGL-J-1.0** · interactive Power BI front-end also linked from the CKAN record
- **Verified:** HTTP 200, XLSX, 160,546 bytes; **2,370 rows, 142 distinct indicators, years
  1993–2025**. Columns: `Indicator Code, PHE Indicator Name, Unit, Year, Value, CI Lower,
  CI Upper, ValueType, PeriodType, Age, Gender, Category, Definition`.
- Relevant indicators include the **full routine vaccination coverage set** (MMR 1 and 2 dose,
  DTaP/IPV/Hib/HepB, MenB, MenACWY, PCV, HPV, rotavirus, shingles, flu 2–3y and 65+),
  *Mortality rate for deaths due to / involving COVID-19*, *Winter mortality index*
  (incl. 85+), and *Under 75 mortality rate from respiratory disease considered preventable*.
- Confidence-interval columns are present but mostly empty in the rows sampled.

### 6.5 Notifiable diseases

- **URL:** `https://www.gov.je/Health/IllnessVaccine/pages/notifiablediseases.aspx` (HTTP 200)
- Lists the ~35 statutory notifiable diseases for Jersey (acute encephalitis, acute infectious
  hepatitis A/B/C/E, acute meningitis, acute poliomyelitis, anthrax, botulism, brucellosis,
  cholera, COVID-19, diphtheria, enteric fever, food poisoning, glandular fever, HUS, infectious
  bloody diarrhoea, invasive group A strep, legionnaires, leprosy, malaria, measles,
  meningococcal septicaemia, MERS, MPOX, mumps, plague, rabies, rubella, scarlet fever, SARS,
  smallpox, tetanus, TB, typhus, VHF, whooping cough, yellow fever). COVID-19 was added by
  ministerial order in 2020 (`https://www.gov.je/news/2020/pages/CoronavirusNotifiableDisease.aspx`).
- **It publishes the list and the reporting form only — no notification counts.** See §Gaps.

### 6.6 Mortality

- *Jersey Mortality Report 2024* — `https://www.gov.je/SiteCollectionDocuments/Health%20and%20wellbeing/Mortality%20Report%202024.pdf`
  (link found in the HTML of the gov.je coronavirus page; **PDF itself not fetched this
  session — unverified**).
- COVID-specific mortality is also in 1.1 (by age band, sex, place of death) and in the four
  archived deaths breakdown lists (§Gaps note: these end 10 May 2021):
  `COVID19DeathsAge` (200, 21,428 B — 10-year age bands, 2020→2021-05-10),
  `COVID19DeathsPlace` (200, 17,938 B — St Saviours / General Hospital / Community / Care Home /
  Overdale, from 2020-04-26), `COVID19DeathsGender` (200, 16,551 B),
  `COVID19DeathsClassification` (200, 16,180 B — probable vs laboratory-proven).
  All at `https://www.gov.je/datasets/listopendata?listname=<name>` (+`&type=xml|json`).
  **Data-quality warning:** the deaths files contain rows with a null date rendered as
  `"12:00 AM, Saturday 30 December 1899"` (Excel epoch) — drop these.

---

## Gaps and non-existence findings

These are findings, not failures to search. Each was actively checked this session.

1. **No parish-level or vingtaine-level COVID case counts are published, at any point in the
   pandemic.** Neither the 112-column legacy list (1.1), the current list (1.2), the CKAN
   coronavirus group (3 datasets, 23 resources total), nor the Statistics Jersey linked-data
   report (4.2 — which has zero occurrences of the word "parish") contains sub-island geography.
   Population denominators go down to vingtaine (5.4); cases do not go below island. **Any
   spatial calibration of JOS below island level has no Jersey COVID data behind it.** FOI is
   the only route, and small-number disclosure control makes success unlikely for a 103k island.

2. **No machine-readable case data before 2020-07-30 from gov.je.** Both gov.je feeds start on
   that date. The first wave (March–June 2020) — the exact window the serosurvey measures — is
   available in machine-readable form **only via JHU CSSE (1.3)** and OWID (1.4, from
   2020-03-12). This is the single most important workaround in this inventory.

3. **LFT (lateral flow) testing volumes are not published anywhere.** The testing series (2.1)
   is PCR-only and ends 2023-02-01. The April 2026 epidemiological report states LFT data "will
   be incorporated into future releases once quality assured" — i.e. as of the latest published
   report, LFT volumes and LFT-diagnosed positives are **still not public**.

4. **No published notifiable-disease notification counts.** Jersey has a statutory notification
   system (6.5) but publishes only the disease list and the practitioner form. No annual
   communicable-disease report, no counts dataset, nothing on opendata.gov.je (CKAN
   `package_search?q=notifiable` returns 1 irrelevant hit). Regulations mandating reporting for
   infectious disease surveillance are indicated for 2026, so this may change.

5. **No norovirus surveillance data at all.** `package_search?q=norovirus` → 0 results. Not in
   the epidemiological report (flu/COVID/RSV only), not in the winter illness report.

6. **No peer-reviewed Jersey (Channel Islands) seroprevalence publication exists.** Three
   Europe PMC searches returned no such paper. The only Jersey COVID paper in the literature is
   a hospital laboratory-features study (3.4). The serosurvey lives **only** as a Statistics
   Jersey PDF (3.1), and is explicitly labelled *preliminary*.

7. **Only one round of community serosurvey results was ever published.** A second round was
   announced (3.3) but no round-2 report was found on gov.je, stats.je, statesassembly.gov.je or
   Europe PMC, and the round-2 announcement page links only the round-1 PDF. **Record as
   "announced, results not published" — do not assume it exists.**

8. **The Essential Worker Antibody Survey full report is not published.** Only headline numbers
   on an HTML news page (3.2). FOI candidate.

9. **OWID carries no Jersey testing, hospital, ICU, stringency or reproduction-rate data.**
   Verified by column-population check across all 2,389 Jersey rows: `total_tests`, `new_tests`,
   `positive_rate`, `tests_per_case`, `hosp_patients`, `icu_patients`, `weekly_hosp_admissions`,
   `stringency_index`, `reproduction_rate`, `hospital_beds_per_thousand` are **all empty**.
   Jersey is absent from the OxCGRT stringency index. Do not expect an off-the-shelf Jersey
   NPI-timing series — NPI dates must be reconstructed from gov.je news pages by hand.

10. **No COVID hospitalisation time series is published.** `CasesKnownCasesInHospital` in 1.1 is
    *cases known to be in hospital*, not admissions, and there is no ICU series. Hospital
    admission data for influenza is explicitly described in 6.2 as newly identified and still
    under quality assurance.

11. **The COVID deaths breakdowns freeze at 10 May 2021** (age band, place, sex, probable vs
    lab-proven). After that date only a single cumulative `MortalityTotalDeaths` continues.

12. **The two current-era PDF report series use rolling URLs with no historic archive.** The
    Epidemiological Report (6.1) and the vaccine coverage reports (4.4) overwrite in place under
    a single ReportID. **Historic monthly editions are recoverable only from the Wayback
    Machine** (confirmed available: 2026-01-02 snapshot of the epidemiological report).

13. **The gov.je `ListOpenData` endpoints are live SharePoint list renderings, not versioned
    files.** They can change without notice and carry sentinel values (`-1`, empty string, one
    stray `float;#0`) and Excel-epoch null dates. There is no checksum, no `Last-Modified`
    contract, and no archive of prior states. Freezing them is genuinely urgent.

14. **Three URLs referenced by official metadata are dead (404):**
    `gov.je/Government/Departments/StrategicPolicy/PublicHealth/Pages/StatesReports.aspx`
    (cited in the CKAN coronavirus dataset description),
    `gov.je/Government/JerseyInFigures/Health/Pages/Immunisation.aspx` (cited in the CKAN
    immunisation dataset description), and
    `gov.je/Government/Pages/OpenGovernmentLicence.aspx`. Working equivalents are recorded above.

15. **Unverified this session (do not cite as confirmed):** the 2021 Census Report PDF direct
    URL, the four stats.je 2024 population/migration PDFs, the Jersey Mortality Report 2024 PDF,
    and any pre-2024 edition of the Influenza and Winter Illness Report.

16. **No contact/social-mixing survey for Jersey was sought or found.** JOS contact-network
    parameters have no Jersey-specific empirical source in this inventory. Out of scope here,
    but it is the structural gap that this inventory cannot close.

---

## Recommended snapshot order

Ordered by calibration value per unit of effort, and by **risk of disappearing**. Items 1–4 are
live SharePoint endpoints with no versioning and should be frozen in a single session.

| Order | Source | Why first | Effort |
|---|---|---|---|
| **1** | **1.1 legacy `ListName=COVID19`** (CSV + XML + JSON) | The only daily incidence series with symptomatic/asymptomatic split, ascertainment route, age-banded 7-day rates and setting (care home/community/hospital). Nothing else in this inventory substitutes for it. Live endpoint, unversioned, could vanish. | 1 GET ×3 formats |
| **2** | **4.1 `ListName=COVID19Weekly`** (CSV + XML + JSON) | 132 weeks × 155 columns of dose counts *and* % coverage across 14 age bands — directly parameterises an age-structured vaccination model. Same disappearance risk. | 1 GET ×3 |
| **3** | **1.2 current `Coronavirus(COVID-19)DataforJersey`** + the 4 deaths lists (`COVID19DeathsAge/Place/Gender/Classification`) | Completes the gov.je live-endpoint set; deaths-by-age gives an IFR anchor. Cheap. | 5 GETs ×3 |
| **4** | **3.1 serosurvey PDF** | The one true prevalence anchor: 3.1% ± 1.3% at 5 May 2020 with full documented design. Calibrates the ascertainment ratio for the first wave. Small, static, but a gov.je PDF path could be reorganised. | 1 GET |
| **5** | **1.3 JHU CSSE confirmed/deaths global** | Fills the March–July 2020 hole that no gov.je feed covers — the window the serosurvey measures. Archived repo, so low risk, but pair it with item 4 or the serosurvey has no case series to sit against. | 2 GETs |
| **6** | **5.1, 5.2, 5.4, 5.5, 5.6 population/household CSVs** | Denominators and the synthetic-population age/parish/household structure. Static CKAN files, low risk — but everything above is meaningless without them. | 5 GETs |
| **7** | **4.2 *Insights* PDF** | Cumulative ever-positive proportion by age, household type, ethnicity, occupation — the closest thing to a Jersey attack-rate-by-stratum dataset. PDF-only, so budget transcription time for Tables 1–8. | 1 GET + transcription |
| **8** | **6.4 PHOF XLSX** + **6.3 immunisation CSVs** | Routine vaccination coverage baselines (MMR, flu) for non-COVID scenarios; winter mortality index. | 7 GETs |
| **9** | **6.1 epidemiological report + 6.2 winter illness report** (and Wayback back-fill) | Flu/RSV baselines. Rolling URLs, so also enumerate Wayback snapshots to recover prior editions — this is the only historic series recovery in the list and should be scripted, not done by hand. | 2 GETs + Wayback crawl |
| **10** | **1.4 OWID compact** | Mostly redundant with 1.1–1.3 and 4.1, and 179 MB. Freeze a Jersey-filtered subset only, as a cross-check. | 1 large GET + filter |
| **11** | **3.2 essential-worker page, 3.3 round-2 pages, 6.5 notifiable list** | HTML scrapes recording *what was and was not published*. Low data value, high provenance value for the non-existence findings above. | 4 GETs |

**Snapshot mechanics.** For every `www.gov.je` URL set a browser User-Agent or you get a WAF
HTTP 500. Record for each artefact: retrieval timestamp, HTTP status, content-type, byte count,
and SHA-256. `opendata.gov.je` resource URLs carry stable dataset/resource UUIDs and should be
recorded alongside a `package_show` metadata capture, so licence and modification dates are
frozen with the data. Nothing here needs scraping except items in row 11; everything else is a
direct file URL. No FOI is required for any row above — FOI is only relevant to the two
non-existent artefacts (parish-level cases, the essential-worker full report), and both are
likely refusals.
