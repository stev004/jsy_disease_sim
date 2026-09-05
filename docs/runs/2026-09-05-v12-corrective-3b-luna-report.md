Implemented the four specified cell corrections and regenerated `data/processed/`.

Before → after:

- `communal_settings,establishments,denominator`: narrative → `not applicable`
- `communal_settings,residents,denominator`: `resident population (page 46)` → `not applicable`
- `household_types,households,denominator`: narrative → `not applicable`
- `workplace_destination,population_universe`: `workers 61 in the Island (page 81)` → `workers in the Island (page 81; footnote 61 states the exclusions)`

Verification:

- Fixture SHA: `90051c1448a98cd05c25d7c3903b81d4ac82a99c701c0c4ad6d973ec417534b3`
- Manifest hash matches: `yes`
- Rebuild: passed; 23 tables, 14 warnings
- `/tmp` comparison: silent (`diff -rq`)
- Tests: `26 passed in 20.14s`
- Ruff: `All checks passed!`
- Format: `174 files already formatted`
- Invariant one-liner: `[]`
- `git diff --check`: clean

Changed files are limited to the specified fixture, `data/sources.yaml`, and regenerated processed files. No commit made.