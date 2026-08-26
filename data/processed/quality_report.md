# Milestone 1 data-quality report

Build status: **passed**

## Source snapshots

| Source | Status | Acquisition | SHA-256 | Snapshot |
|---|---|---|---|---|
| jersey_population_2024_total_pdf | passed | automated | a21ab32f0117ee10334197f496b92348a70bed75677a500855092c3b73191ab3 | data/raw/jersey_population_2024_total_pdf/population_2024_total.pdf |
| census_2021_report_pdf | passed | automated | e4f8c38e96330fc60af584b8fae75d3011d29f4992bb2d8031e8baa192a91095 | data/raw/census_2021_report_pdf/R.45-2023.pdf |
| census_2021_age_gender_csv | passed | automated | c0c1c2f211737129a8ec8f3db52442baf5ad0d85dd8f627e3f833314e9f9dabc | data/raw/census_2021_age_gender_csv/2021-census-age-gender.csv |
| census_2021_parish_population_density_csv | passed | automated | e46abd1eac1c13087fa92a3ecba9bb049b179d94868b7b9c967224f5127818ab | data/raw/census_2021_parish_population_density_csv/2021-census-parish-population-density.csv |
| census_2021_parish_age_sex_csv | passed | automated | 532eb6d7a9a76b682ab056ba45f09f129bd768b71d45f7f7b0d587af95d8ff39 | data/raw/census_2021_parish_age_sex_csv/2021-census-parish-by-age-and-sex.csv |
| census_2021_household_type_tenure_csv | passed | automated | 5404e3ccb551b5e27b4bd5edf1f628f9e52bf733cd495150746ecd7b6b059e66 | data/raw/census_2021_household_type_tenure_csv/2021-census-householdtype-tenure.csv |
| census_2021_household_property_type_csv | passed | automated | 498ed541367041ebe9e9a038995e608940b58588fdbfa4211349027a812c0569 | data/raw/census_2021_household_property_type_csv/2021-census-householdtype-propertytype.csv |
| census_2021_housing_persons_bedrooms_csv | passed | automated | 0f79666e06d28f896dee4cdd173dc6c8e8bdab125864950cf4ee10a2b5339236 | data/raw/census_2021_housing_persons_bedrooms_csv/2021-census-persons-bedrooms-tenure.csv |
| census_2021_overcrowding_csv | passed | automated | 4882a98d8765f5ffad760cecfdb38c5972097b25bb91c04580d8f77fc0b967ae | data/raw/census_2021_overcrowding_csv/proportion-of-overcrowded-households-by-tenurepercent-census2021.csv |
| census_2021_commute_mode_csv | passed | automated | 991a92f1eba7ac05751eac0376a3eabeb3ecb1eee5cfcbe3336545257cb031d6 | data/raw/census_2021_commute_mode_csv/2021-census-modeoftravel-parish.csv |
| census_2021_industry_sex_csv | passed | automated | fa5771d6a2b5ab80e8764d20596d3d0cf1f5b66b2da02dac82e00bd208850dbb | data/raw/census_2021_industry_sex_csv/industry-by-sex-2021-census.csv |
| labour_market_june_2025_pdf | passed | automated | 647cdf53997f66faa36f41036ec9fd904ae729d8bbccc01a97eb23cb5e398fe0 | data/raw/labour_market_june_2025_pdf/R-Labour-Market-June-2025.pdf |
| education_students_by_school_type_csv | passed | automated | 922812ce877bb573a6e5164c11d80d30a274ced1c6a571e2d3c0076497fea35e | data/raw/education_students_by_school_type_csv/total-students-by-school-type.csv |
| education_staff_2024_foi_html | passed | automated | 59f3fa721f96400fc380125fe3adaf629228d73067e6ddbfdb5560328a8b1f1c | data/raw/education_staff_2024_foi_html/official_page.html |
| education_staff_2025_foi_html | passed | automated | e789838a2a378b54e2bd171780d078f743e9a82b44b42f43dff42303e2b07a2f | data/raw/education_staff_2025_foi_html/official_page.html |
| care_commission_accommodation_standards_2026_pdf | passed | automated | 6965c37f45b1a90b92aa99e88bcd6e5bf2e07baa7abec35b00d3e0945ca40d0e | data/raw/care_commission_accommodation_standards_2026_pdf/official_standard.pdf |
| passenger_arrivals_total_csv | passed | automated | da0fc97a508256ad44c88637573d5ff69de4b612f3a7702cde97a21602a8d194 | data/raw/passenger_arrivals_total_csv/total-arrivals.csv |
| jersey_population_2024_manual_fixture | passed | manual | a9590787131d349f18392243f11c0082944289b0473782428b3714f2b966d3fa | data/raw/jersey_population_2024_manual_fixture/population_2024_summary.csv |
| census_2021_report_manual_fixture | passed | manual | 7a1e567cccc81a3814ef1020ad954e6caf51fe980066937917bdfb8d6b16af05 | data/raw/census_2021_report_manual_fixture/census_2021_manual_controls.csv |
| labour_market_june_2025_manual_fixture | passed | manual | f2254ce92420ec96c9cc27b2282c0528a0a551c8a8db390720870cec305dca27 | data/raw/labour_market_june_2025_manual_fixture/labour_market_manual_controls.csv |

## Canonical tables

| Table | Rows | SHA-256 |
|---|---:|---|
| data/processed/population_totals.csv | 9 | 51c7c9a0c9d2ff72339f365f5e2094936d84170064e1938bdd09ed76540325dc |
| data/processed/age_sex.csv | 293 | 5d5feccead68e94c2e49b86c563e17075c17f94233857b2a74684fd9c917db58 |
| data/processed/parish_population.csv | 12 | 87f95bd5de4b4fa378813ead05e276017f0538371eeb7ce3b22d8033575f8ac2 |
| data/processed/parish_age_sex.csv | 702 | 8cdfe7676462740285679a98d66708097e38b9b06b1c5b5bd8e712a4129831be |
| data/processed/household_types.csv | 11 | a5addfd1587d94d5450e65c2df677ca860be6d6841d5fa186769223873f95a71 |
| data/processed/housing_controls.csv | 166 | d1b3f077e7ed240038682245d37b27b6b8b3e1a28e20823badb8f917dd35a0fb |
| data/processed/employment_sectors.csv | 48 | 3deac4b00bb8852dc3af7c3dc880082f5d943000fadd399e3dd78125af8c3e1f |
| data/processed/workplace_sizes.csv | 66 | faae918d31273d6f7016ea1a97d58f5f96e4e6ca0c82726f97bf9761d456750b |
| data/processed/workplace_destination.csv | 8 | d07a9f9c96480ca52919e88ca1f71aaeab4a65c6d0b413166ca21314b49e5df2 |
| data/processed/commute_modes.csv | 91 | e3d239f843a7966f163dc72bfd11e707dee0d0c901d8c2ac9acade4ee910e5c9 |
| data/processed/school_students.csv | 6 | 1eb7ff460c93c3d9c5b2bf5460ba60a18abd2d23a5c93e130739086b321f746f |
| data/processed/communal_settings.csv | 17 | 6001fa22ccd27a975c1611aa946fe7fcdb8292c4401d9cc75ffb5a12fc81cb23 |
| data/processed/passenger_arrivals.csv | 3 | 92ad95faf52b969ad168f1d59001a4a2de56c9e250d3ee503e05c1a870517c4c |
| data/processed/derived_controls.csv | 37 | 7681d0dca40a84cc2850fa9c147a780bf179a984c65b96c40f9c5c433684d135 |

## Validation and reconciliation

- **passed** `parish_population_sum`: actual=103267, expected=103267, difference=0. 
- **passed** `2021_age_gender_sum`: actual=103267, expected=103267, difference=0. 
- **passed** `2024_broad_age_sum`: actual=104540, expected=104540, difference=0. 
- **passed** `2024_sex_sum`: actual=104540, expected=104540, difference=0. 
- **passed** `household_type_sum`: actual=44583, expected=44583, difference=0. 
- **passed** `2021_employment_sector_sum`: actual=57338, expected=57338, difference=0. 
- **warning** `2025_private_sector_jobs_sum`: actual=55360, expected=55370, difference=-10. 
- **passed** `2025_workplace_size_band_sum`: actual=8500, expected=8500, difference=0. 
- **passed** `2021_commute_mode_sum`: actual=57340, expected=57340, difference=0. 
- **warning** `2021_commute_report_rounding_difference`: actual=57340, expected=57338, difference=2. 
- **passed** `2024_student_components_sum`: actual=13991, expected=13991, difference=0. 
- **passed** `2025_arrivals_components_sum`: actual=917465, expected=917465, difference=0. 
- **warning** `housing_mean_bedrooms_source_conflict`: actual=2.57, expected=2.47, difference=0.1. conflict is retained as a quality warning; no silent normalization

## Pipeline

1. immutable raw snapshot
1. source-specific CSV/PDF extraction
1. canonical long-form aggregate table
1. validation and reconciliation
1. derived controls and data-quality report

## Limitations and evidence notes

- 2024 population source provides broad age bands and broad sex totals; detailed 2024 age-by-sex is not inferred from 2021 data.
- 2021 commuting and workplace-destination controls describe the census reference period and include pandemic-era work-from-home effects.
- The 2025 labour-market sector values are jobs, not unique employees; they are not reconciled to 2021 resident workers.
- The housing CSV all-row mean bedrooms value (2.57) conflicts with the official report value (2.47); the report value is the canonical manual control and the conflict is flagged.
- Published CSV tables include rounded counts and suppressed small cells in places; raw values and suppression notes are preserved rather than imputed.
