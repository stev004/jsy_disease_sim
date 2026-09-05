Implemented corrective 4 within scope.

Changed:

- Added five exact census blank-cell quality warnings to the build and regression test.
- Corrected all seven audit findings in the measure dictionary.
- Regenerated `data/processed/`.
- Updated the fixture SHA to `7b831ce2f3a21d5597c23548394ce19e6b9bedb661df2162398f6b079d7b713a`.

Files:

- [data_pipeline.py](/home/steven/jos-v12-corr3-wt/src/jersey_outbreak/data_pipeline.py:1575)
- [measure_dictionary.csv](/home/steven/jos-v12-corr3-wt/data/raw/epi_measure_dictionary_manual_fixture/measure_dictionary.csv)
- [sources.yaml](/home/steven/jos-v12-corr3-wt/data/sources.yaml:484)
- [test_v12_corr4_dictionary.py](/home/steven/jos-v12-corr3-wt/tests/test_v12_corr4_dictionary.py)

Validation:

- F1 baseline: `1 failed`; final: `1 passed`.
- Targeted tests: `27 passed`.
- Full suite: `310 passed, 5 warnings`.
- `ruff check .`: passed.
- `ruff format --check .`: passed.
- CI mypy set: `Success: no issues found in 15 source files`.
- `git diff --check`: passed.
- Split-column count: `0`; placeholder count: `0`.
- Count-measure rule: `[]`.
- Locator-rule check: `[]`.
- Eligible population: `132` rows, constant `107800`.
- Rebuild diff: no output from `diff -rq`.
- Quality report contains all five new warnings.

The extra mypy check on `data_pipeline.py` still reports seven pre-existing typing errors outside the permitted change area; the exact CI-listed 15-module check is clean.

### Per-finding corrections

| Finding | Correction |
|---|---|
| F1 | Dictionary suppression semantics now describe the five blank cells, publisher silence, build omission, and `unknown` blank meaning. Warnings cite each exact source, row, and column. |
| F2 | Population flow dates now cite PDF pages 18/19; all Jersey population rows cite rounding; total population cites the provisional estimate on page 3. |
| F3 | Density denominator now cites frozen CSV column `2021 density (person/km2)`. |
| F4 | Eligible population and bedroom conflict denominators are `not applicable`; eligible reporting states constant `107,800` across 132 rows. |
| F5 | Labour jobs/workplace universes, suppression legend, and manpower-return exclusion now cite pages 11/13. |
| F6 | Serosurvey weighting cites page 5; sample/result cites page 6; weighted row locator is `pdf_page_5;pdf_page_6`; response rates cite page 5. |
| F7 | All 11 daily-surveillance rows now use their actual direct frozen columns and `reporting_regime = unknown`; no canonical measure derives from the prior/since split columns. |

### F1 pipeline diff

The housing builder now receives a warnings list, appends the exact warning before each `continue`, and passes those warnings into the final quality report. No housing row behavior changed.

### Full 92-row semantic sweep

`E/P/D/R/K` = event date, population universe, denominator, reporting regime, known exclusions.

`unknown` is an honest unknown; `N/A` is not applicable; `found-on-cited-locator` is retained supported content; `fixed:` identifies the corrected supporting locator.

| Row | E | P | D | R | K |
|---|---|---|---|---|---|
| covid_daily_surveillance / daily_new_confirmed_cases / covid19_daily_surveillance_csv | unknown | unknown | N/A | fixed: CSV `CasesDailyNewConfirmedCases` | found-on-cited-locator |
| covid_daily_surveillance / cumulative_confirmed_cases / covid19_daily_surveillance_csv | unknown | unknown | N/A | fixed: CSV `CasesTotalConfirmedPositiveCases` | found-on-cited-locator |
| covid_daily_surveillance / symptomatic_cases / covid19_daily_surveillance_csv | unknown | unknown | N/A | fixed: CSV `CasesSymptomatic` | found-on-cited-locator |
| covid_daily_surveillance / asymptomatic_cases / covid19_daily_surveillance_csv | unknown | unknown | N/A | fixed: CSV `CasesAsymptomatic` | found-on-cited-locator |
| covid_daily_surveillance / current_known_active_cases / covid19_daily_surveillance_csv | unknown | unknown | N/A | fixed: CSV `CasesCurrentKnownActiveCases` | found-on-cited-locator |
| covid_daily_surveillance / seven_day_rate_per_100k / covid19_daily_surveillance_csv | unknown | unknown | unknown | fixed: CSV `CasesSeven7DayNumberper100000` | found-on-cited-locator |
| covid_daily_surveillance / cumulative_tests / covid19_daily_surveillance_csv | unknown | unknown | N/A | fixed: CSV `TestsTotaltests` | found-on-cited-locator |
| covid_daily_surveillance / tests_reason_symptomatic / covid19_daily_surveillance_csv | unknown | unknown | N/A | fixed: CSV `TestsReasonfortestseekinghealthcaresymptomatic` | found-on-cited-locator |
| covid_daily_surveillance / tests_reason_inbound_travel / covid19_daily_surveillance_csv | unknown | unknown | N/A | fixed: CSV `TestsReasonforTestInboundTravel` | found-on-cited-locator |
| covid_daily_surveillance / tests_reason_on_island_screening / covid19_daily_surveillance_csv | unknown | unknown | N/A | fixed: CSV `TestsReasonforTestOnIslandSurveillanceScreening` | found-on-cited-locator |
| covid_daily_surveillance / cumulative_deaths / covid19_daily_surveillance_csv | unknown | unknown | N/A | fixed: CSV `MortalityTotalDeaths` | found-on-cited-locator |
| covid_current_summary / cumulative_tests / covid19_current_summary_csv | unknown | unknown | N/A | unknown | found-on-cited-locator |
| covid_current_summary / cumulative_confirmed_cases / covid19_current_summary_csv | unknown | unknown | N/A | unknown | found-on-cited-locator |
| covid_current_summary / seven_day_rate_per_100k / covid19_current_summary_csv | unknown | unknown | unknown | unknown | found-on-cited-locator |
| covid_current_summary / cumulative_deaths / covid19_current_summary_csv | unknown | unknown | N/A | unknown | found-on-cited-locator |
| covid_jhu_daily / cumulative_confirmed_cases / jhu_csse_confirmed_global_csv | unknown | unknown | N/A | unknown | unknown |
| covid_jhu_daily / cumulative_deaths / jhu_csse_deaths_global_csv | unknown | unknown | N/A | unknown | unknown |
| covid_jhu_daily / daily_new_confirmed_cases / jhu_csse_confirmed_global_csv | unknown | unknown | N/A | unknown | unknown |
| covid_serosurvey_2020 / estimated_population_prevalence_percent / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | found-on-cited-locator | fixed: PDF pages 6/7 | unknown | fixed: PDF page 1 |
| covid_serosurvey_2020 / estimated_population_prevalence_ci95_half_width_percent / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | found-on-cited-locator | fixed: PDF pages 6/7 | unknown | fixed: PDF page 1 |
| covid_serosurvey_2020 / observed_unweighted_prevalence_percent / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | fixed: PDF page 1 | fixed: PDF page 6 | unknown | fixed: PDF page 1 |
| covid_serosurvey_2020 / weighted_unadjusted_prevalence_percent / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | fixed: PDF page 1 | fixed: PDF page 6 | fixed: PDF pages 5/6 | fixed: PDF page 1 |
| covid_serosurvey_2020 / households_tested / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | found-on-cited-locator | N/A | unknown | fixed: PDF page 1 |
| covid_serosurvey_2020 / individuals_tested / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | found-on-cited-locator | N/A | unknown | fixed: PDF page 1 |
| covid_serosurvey_2020 / response_rate_households_percent / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | found-on-cited-locator | fixed: PDF page 5 | unknown | fixed: PDF page 1 |
| covid_serosurvey_2020 / response_rate_individuals_percent / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | found-on-cited-locator | fixed: PDF page 5 | unknown | fixed: PDF page 1 |
| covid_serosurvey_2020 / assumed_test_sensitivity_percent / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | found-on-cited-locator | unknown | unknown | unknown |
| covid_serosurvey_2020 / assumed_test_sensitivity_ci95_low_percent / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | found-on-cited-locator | unknown | unknown | unknown |
| covid_serosurvey_2020 / assumed_test_sensitivity_ci95_high_percent / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | found-on-cited-locator | unknown | unknown | unknown |
| covid_serosurvey_2020 / assumed_test_specificity_percent / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | found-on-cited-locator | unknown | unknown | unknown |
| covid_serosurvey_2020 / minimum_age_years / sars_cov2_serosurvey_2020_manual_fixture | found-on-cited-locator | found-on-cited-locator | N/A | unknown | fixed: PDF page 1 |
| covid_weekly_vaccination / dose_1:cumulative_doses / covid19_weekly_vaccination_csv | unknown | unknown | N/A | unknown | unknown |
| covid_weekly_vaccination / dose_1:percent_population / covid19_weekly_vaccination_csv | unknown | unknown | found-on-cited-locator | unknown | unknown |
| covid_weekly_vaccination / dose_2:cumulative_doses / covid19_weekly_vaccination_csv | unknown | unknown | N/A | unknown | unknown |
| covid_weekly_vaccination / dose_2:percent_population / covid19_weekly_vaccination_csv | unknown | unknown | found-on-cited-locator | unknown | unknown |
| covid_weekly_vaccination / dose_3:cumulative_doses / covid19_weekly_vaccination_csv | unknown | unknown | N/A | unknown | unknown |
| covid_weekly_vaccination / dose_3:percent_population / covid19_weekly_vaccination_csv | unknown | unknown | found-on-cited-locator | unknown | unknown |
| covid_weekly_vaccination / dose_4:cumulative_doses / covid19_weekly_vaccination_csv | unknown | unknown | N/A | unknown | unknown |
| covid_weekly_vaccination / dose_4:percent_population / covid19_weekly_vaccination_csv | unknown | unknown | found-on-cited-locator | unknown | unknown |
| covid_weekly_vaccination / autumn_2022_booster:cumulative_doses / covid19_weekly_vaccination_csv | unknown | unknown | N/A | unknown | unknown |
| covid_weekly_vaccination / autumn_2022_booster:percent_population / covid19_weekly_vaccination_csv | unknown | unknown | found-on-cited-locator | unknown | unknown |
| covid_weekly_eligible_population / eligible_population / covid19_weekly_vaccination_csv | unknown | unknown | fixed: not applicable; CSV `EligiblePopulation` | fixed: CSV `EligiblePopulation`, 132 rows | unknown |
| population_estimates_annual / count / annual_population_estimates_by_age_sex_csv | unknown | unknown | N/A | unknown | unknown |
| population_denominators_by_age_band / count / annual_population_estimates_by_age_sex_csv | unknown | unknown | N/A | unknown | unknown |
| population_totals / age_16_to_64 / jersey_population_2024_manual_fixture | found-on-cited-locator | unknown | N/A | fixed: PDF p8/p18/p19 | unknown |
| population_totals / age_65_plus / jersey_population_2024_manual_fixture | found-on-cited-locator | unknown | N/A | fixed: PDF p8/p18/p19 | unknown |
| population_totals / age_under_16 / jersey_population_2024_manual_fixture | found-on-cited-locator | unknown | N/A | fixed: PDF p8/p18/p19 | unknown |
| population_totals / natural_change / jersey_population_2024_manual_fixture | fixed: PDF page 18 | unknown | N/A | fixed: PDF p8/p18/p19 | unknown |
| population_totals / net_migration / jersey_population_2024_manual_fixture | fixed: PDF pages 18/19 | unknown | N/A | fixed: PDF p8/p18/p19 | unknown |
| population_totals / population_total / jersey_population_2024_manual_fixture | fixed: PDF page 3 | unknown | N/A | fixed: PDF p3/p8/p18/p19 | unknown |
| population_totals / population_total / census_2021_parish_population_density_csv | found-on-cited-locator | unknown | N/A | unknown | unknown |
| population_totals / sex_female / jersey_population_2024_manual_fixture | found-on-cited-locator | unknown | N/A | fixed: PDF p8/p18/p19 | unknown |
| population_totals / sex_male / jersey_population_2024_manual_fixture | found-on-cited-locator | unknown | N/A | fixed: PDF p8/p18/p19 | unknown |
| age_sex / count / census_2021_age_gender_csv | found-on-cited-locator | unknown | N/A | unknown | unknown |
| age_sex / count / jersey_population_2024_manual_fixture | found-on-cited-locator | unknown | N/A | fixed: PDF p8/p18/p19 | unknown |
| parish_population / population / census_2021_parish_population_density_csv | found-on-cited-locator | unknown | N/A | unknown | unknown |
| parish_population / density_person_km2 / census_2021_parish_population_density_csv | found-on-cited-locator | unknown | fixed: frozen CSV column `2021 density (person/km2)` | unknown | unknown |
| parish_age_sex / count / census_2021_parish_age_sex_csv | found-on-cited-locator | unknown | N/A | unknown | unknown |
| household_types / households / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | N/A | unknown | unknown |
| housing_controls / households / census_2021_household_type_tenure_csv | found-on-cited-locator | unknown | N/A | unknown | unknown |
| housing_controls / households / census_2021_housing_persons_bedrooms_csv | found-on-cited-locator | unknown | N/A | unknown | unknown |
| housing_controls / households / census_2021_household_property_type_csv | found-on-cited-locator | unknown | N/A | unknown | unknown |
| housing_controls / households_without_car_or_van / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | found-on-cited-locator | unknown | unknown |
| housing_controls / mean_bedrooms_per_private_dwelling / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | found-on-cited-locator | unknown | unknown |
| housing_controls / mean_persons_per_private_dwelling / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | found-on-cited-locator | unknown | unknown |
| housing_controls / occupied_dwellings_that_are_flats / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | found-on-cited-locator | unknown | unknown |
| housing_controls / occupied_dwellings_that_are_houses / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | found-on-cited-locator | unknown | unknown |
| housing_controls / occupied_private_dwellings / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | N/A | unknown | unknown |
| housing_controls / persons_in_private_dwellings / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | N/A | unknown | unknown |
| housing_controls / st_helier_households_without_car_or_van / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | found-on-cited-locator | unknown | unknown |
| housing_controls / under_occupied_households / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | found-on-cited-locator | unknown | unknown |
| housing_controls / mean_bedrooms_per_household / census_2021_housing_persons_bedrooms_csv | found-on-cited-locator | unknown | found-on-cited-locator | unknown | unknown |
| housing_controls / mean_persons_per_bedroom / census_2021_housing_persons_bedrooms_csv | found-on-cited-locator | unknown | found-on-cited-locator | unknown | unknown |
| housing_controls / mean_persons_per_household / census_2021_housing_persons_bedrooms_csv | found-on-cited-locator | unknown | found-on-cited-locator | unknown | unknown |
| housing_controls / overcrowded_households / census_2021_overcrowding_csv | found-on-cited-locator | unknown | unknown | unknown | unknown |
| housing_controls / overcrowded_households / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | found-on-cited-locator | unknown | unknown |
| housing_controls / persons / census_2021_housing_persons_bedrooms_csv | found-on-cited-locator | unknown | N/A | unknown | unknown |
| employment_sectors / jobs / labour_market_june_2025_manual_fixture | found-on-cited-locator | fixed: PDF page 13 Table 9 | N/A | fixed: PDF p11 fn13; p13 fn14 | unknown |
| employment_sectors / resident_workers / census_2021_industry_sex_csv | found-on-cited-locator | unknown | N/A | unknown | unknown |
| workplace_sizes / count / labour_market_june_2025_manual_fixture | found-on-cited-locator | fixed: PDF page 11 | N/A | unknown | fixed: PDF p11 fn13 |
| workplace_destination / workplace_destination / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | found-on-cited-locator | found-on-cited-locator | found-on-cited-locator |
| commute_modes / workers / census_2021_commute_mode_csv | found-on-cited-locator | unknown | N/A | unknown | unknown |
| school_students / students / education_students_by_school_type_csv | found-on-cited-locator | unknown | N/A | unknown | unknown |
| communal_settings / establishments / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | N/A | unknown | found-on-cited-locator |
| communal_settings / residents / census_2021_report_manual_fixture | found-on-cited-locator | found-on-cited-locator | N/A | unknown | found-on-cited-locator |
| passenger_arrivals / passengers / passenger_arrivals_total_csv | found-on-cited-locator | unknown | N/A | unknown | unknown |
| derived_controls / average_daily_arrivals / passenger_arrivals_total_csv | found-on-cited-locator | unknown | found-on-cited-locator | unknown | unknown |
| derived_controls / commute_mode_share / census_2021_commute_mode_csv | found-on-cited-locator | unknown | found-on-cited-locator | unknown | unknown |
| derived_controls / household_type_share / census_2021_report_manual_fixture | found-on-cited-locator | unknown | found-on-cited-locator | unknown | unknown |
| derived_controls / mean_bedrooms_conflict / census_2021_housing_persons_bedrooms_csv | found-on-cited-locator | unknown | fixed: not applicable; compared table named in reference | unknown | unknown |
| derived_controls / population_share / census_2021_parish_population_density_csv | found-on-cited-locator | unknown | found-on-cited-locator | unknown | unknown |
| derived_controls / student_type_share / education_students_by_school_type_csv | found-on-cited-locator | unknown | found-on-cited-locator | unknown | unknown |

`docs/audits/2026-09-05-v12-exit-gate-audit-4-sol-FAIL.md` and the cited corrective-3b report were absent from this checkout; no documentation files were modified. No commit was created.