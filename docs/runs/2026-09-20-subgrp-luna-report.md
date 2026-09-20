Implemented ruling 4 without touching `data/raw`, registry entries, simulation code, or committing.

- Added 22-row canonical `covid_vaccination_subgroups` table.
- Added provenance locators, denominator-band validation, dictionary rows, and explicit gaps/exclusions.
- Rebuild: `byte_identical_rebuild=1`.
- Gates: 67 tests passed; Ruff and pinned 15-module mypy passed.
- `raw_changed_files=0`, `registry_changed_files=0`.
- No full/scaled simulations run.

Report: [jos-subgrp.last.md](/home/steven/jos-subgrp-wt/jos-subgrp.last.md)

The requested `~/jos-subgrp.last.md` path was not writable in this sandbox.