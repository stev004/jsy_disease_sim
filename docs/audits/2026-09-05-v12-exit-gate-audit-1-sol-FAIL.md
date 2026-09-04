<!-- IMMUTABLE AUDIT RECORD. Independent cold-start auditor: Codex gpt-5.6-sol@high (self-reports as "OpenAI Codex (GPT-5)"), read-only, fresh clone /tmp/jos-exit-audit at 9ac9d20872559ad4e2a0dc00bc1b73fc792048ab, brief ~/jos-v12-exit-audit-brief.md, launched 2026-09-05 00:49 local via fm.sh exec, report written 00:52. Filed verbatim by the director. Verdict: FAIL (4 blocking findings). -->

# Independent V1.2 exit-gate audit

- Audited SHA: `9ac9d20872559ad4e2a0dc00bc1b73fc792048ab`
- Clone: `/tmp/jos-exit-audit`
- Date: 2026-09-05
- Model: OpenAI Codex (GPT-5)
- Mode: cold-start, read-only
- Worktree after audit: clean; no tracked files modified

## Step 1 — Registry, snapshot integrity, rebuild tests

Exact prescribed command:

```text
$ uv run --locked pytest -q tests/test_data_sources.py tests/test_data_pipeline.py
error: Could not acquire lock
  Caused by: Could not create temporary file
  Caused by: Read-only file system (os error 30) at path "/home/steven/.cache/uv/.tmpaAifMJ"
```

Equivalent retry with only caches redirected outside the repository:

```text
$ UV_CACHE_DIR=/tmp/jos-audit-uv-cache PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked pytest -p no:cacheprovider -q \
  tests/test_data_sources.py tests/test_data_pipeline.py
.................                                                        [100%]
17 passed in 10.40s
```

Result: the relevant tests pass. This does not cure the independent blocking failures below.

## Step 2 — Reproducibility of committed tables

The exact command encountered the same environment-only cache restriction:

```text
$ uv run jos data build --output-dir /tmp/jos-audit-rebuild-exact
error: Could not acquire lock
  Caused by: Could not create temporary file
  Caused by: Read-only file system (os error 30) at path "/home/steven/.cache/uv/.tmplp9KMb"
```

Cache-redirected execution:

```text
$ UV_CACHE_DIR=/tmp/jos-audit-uv-cache PYTHONDONTWRITEBYTECODE=1 \
  uv run jos data build --output-dir /tmp/jos-audit-rebuild
{"build_status": "passed", "quality_report": "/tmp/jos-audit-rebuild/quality_report.json", "table_count": 23, "warning_count": 11}
```

Required comparison:

```text
$ diff -rq /tmp/jos-audit-rebuild data/processed
Files /tmp/jos-audit-rebuild/quality_report.json and data/processed/quality_report.json differ
Files /tmp/jos-audit-rebuild/quality_report.md and data/processed/quality_report.md differ
Files /tmp/jos-audit-rebuild/table_manifest.json and data/processed/table_manifest.json differ
```

Representative diff:

```diff
- "path": "data/processed/population_totals.csv",
+ "path": "tmp/jos-audit-rebuild/population_totals.csv",
```

All 23 table payload hashes match, but the protocol explicitly requires an empty directory diff. `src/jersey_outbreak/data_pipeline.py:334` embeds the output location in generated artifacts:

```python
"path": str(path.relative_to(output_dir.parent.parent)),
```

Result: FAIL. The rebuild is destination-dependent.

## Step 3 — Row-level traceability

The gate definition needed to identify the enumerated seven-table set is absent:

```text
$ git cat-file -e HEAD:docs/research/v1_2/V1_2_EXIT_GATE.md
fatal: path 'docs/research/v1_2/V1_2_EXIT_GATE.md' does not exist in 'HEAD'
```

Repository search found only:

```text
docs/research/v1_2/2026-09-03-jersey-data-source-inventory.md
```

The higher-authority origin at `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md:577-629` states the general exit gate but does not enumerate the seven tables or supply the sampling protocol.

One independently checked source hash agrees:

```text
$ sha256sum data/raw/covid19_daily_surveillance_csv/covid19_daily.csv
ea51daa689a851af6fedb45e1520abfc235bc350113cbde1cd49b880d7aa512b  data/raw/covid19_daily_surveillance_csv/covid19_daily.csv
```

This matches `data/sources.yaml:301`, but it cannot substitute for three samples from every undefined table. No seed or row indices are reported because selecting a set would require inventing the missing gate definition.

Result: protocol step could not be completed.

## Step 4 — Measure dictionary

The higher-authority origin requires every measure to carry extraction date and revision/version (`docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md:597-606`).

The common row contract at `src/jersey_outbreak/canonical_schemas.py:20-30` is:

```text
schema_version
source_id
source_sha256
evidence_source_id
reference_period
observation_status
source_locator
transformation_id
```

It carries neither extraction date nor source revision/version. `retrieved_at` exists only in the separate registry.

A representative direct source check also found an unsupported dictionary assertion. `data/processed/measure_dictionary.csv:2` asserts geography `Jersey (island-wide)`, but its cited locator points only to CSV columns:

```text
covid19_daily_surveillance_csv:Date;CasesDailyNewConfirmedCases;
TestsTotalsamplestestedpriorto1July2020;
TestsTotalsamplestestedsince1July2020
```

Opening those cited columns shows dates and measures, not a statement establishing the asserted geography. Under the protocol, that cell must be `unknown` unless supported by the cited frozen location.

Because the gate file is missing, the required authoritative row contract cannot be read, and exhaustive validation of all 44 rows cannot be completed without guessing.

Result: protocol step incomplete, with independently observed contract violations.

## Step 5 — Known gaps

Bounded search:

```text
$ rg -n -i 'npi|non.?pharmaceutical|intervention timeline|lockdown|school closure|negative.?tests|TestsTotalNegativeTests' ...
src/jersey_outbreak/data_pipeline.py:979: "covid daily surveillance anomaly: TestsTotalNegativeTests is excluded because "
docs/research/v1_2/2026-09-03-jersey-data-source-inventory.md:473:
  NPI-timing series — NPI dates must be reconstructed from gov.je news pages by hand.
data/processed/quality_report.md:126:
  TestsTotalNegativeTests is excluded because 917 of 917 cells use SharePoint calculated-field rendering...
```

The processed-table listing contains no NPI/intervention timeline. The negative-tests field is excluded and warned as requested.

However, the full “explicitly NOT available” list exists only in the missing gate file, so the remaining required gap checks cannot be identified or completed.

Result: the two named checks pass; the full protocol step is incomplete.

## Step 6 — Decision

The audit must fail because the authoritative gate definition is absent, required protocol steps 3–5 therefore cannot be completed, and the required rebuild diff is independently non-empty.

## Findings

1. **BLOCKING** — `docs/research/v1_2/V1_2_EXIT_GATE.md:1` (missing): the audited SHA does not contain the gate definition, seven-table calibration-input enumeration, row contract, audit protocol, or complete unavailable-data list. A cold-start auditor cannot know what must be audited.

2. **BLOCKING** — `src/jersey_outbreak/data_pipeline.py:334`: generated manifests and quality reports embed the selected output directory. Consequently, the mandated `/tmp` rebuild cannot reproduce `data/processed` byte-for-byte.

3. **BLOCKING** — `src/jersey_outbreak/canonical_schemas.py:20-30`, against `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md:597-606`: canonical rows omit the required extraction date and source revision/version.

4. **BLOCKING** — `data/processed/measure_dictionary.csv:2`: `geography=Jersey (island-wide)` is asserted even though that fact is not supported by the cited frozen CSV columns. The protocol requires unsupported semantics to be `unknown`.

## What a stranger would still not understand

A stranger cannot determine which seven tables constitute the calibration inputs, what authoritative row contract applies, or which unavailable inputs must remain gaps. Even outside that missing definition, they would still have to guess several observation semantics: most daily event-date definitions and population universes are `unknown`, vaccination percentage denominators are unstated, and the canonical rows omit source acquisition/revision metadata.

V1.2 EXIT GATE: FAIL — the audited SHA does not contain `docs/research/v1_2/V1_2_EXIT_GATE.md`, so the authoritative gate and required protocol cannot be executed completely.