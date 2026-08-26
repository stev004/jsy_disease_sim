# Milestone 1 aggregate data layer

This directory contains only the aggregate evidence foundation. It does not
contain individual synthetic residents, schools, workplaces, contacts or
simulation routes. Milestones 2 and 3 consume these canonical controls to build
separate synthetic artifacts outside the `data/` tree.

```text
data/raw/<source_id>/       immutable downloaded bytes and labelled manual fixtures
data/interim/               source-specific interpreted data, if needed
data/processed/*.csv        validated canonical aggregate CSVs
data/processed/             deterministic table manifest and quality reports
```

The downstream boundary is explicit:

```text
canonical aggregate tables + hashes
              |
              +--> Milestone 2 synthetic residents/households/settings
              |
              +--> Milestone 3 synthetic schools/workplaces/commutes
```

The M3 structure generator uses the school rolls, 2021 resident-worker sector
totals, workplace size bands, workplace destination controls and commute-mode
tables. Their different reference periods and statistical universes remain
visible in the generated provenance and diagnostics; they are not silently
treated as one individual-level dataset.

Raw downloads are not cleaned in place. Every source is registered in
[`sources.yaml`](sources.yaml), including its official URL, reference period,
acquisition method, local snapshot and SHA-256. Manual fixtures are explicitly
labelled and include the source PDF page/table from which the values were
transcribed.

Build the canonical layer with:

```bash
uv run jos data build
```

The builder validates source records and hashes before reading any input. It
emits canonical tables, a deterministic table manifest and both JSON and
Markdown data-quality reports. Warnings in those reports, including commute
rounding and workplace-control reconciliation limitations, are retained rather
than imputed.
