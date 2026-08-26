# Milestone 1 data layers

This directory contains only the aggregate evidence foundation. It does not
contain individual synthetic residents or simulation routes.

```text
data/raw/<source_id>/       immutable downloaded bytes and labelled manual fixtures
data/interim/               source-specific interpreted data, if needed
data/processed/*.csv        validated canonical aggregate CSVs
data/processed/             deterministic table manifest and quality reports
```

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
Markdown data-quality reports.
