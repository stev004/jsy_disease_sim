# REPO-MAP — orientation for any incoming director/agent

*A navigation map, not documentation. Module contracts live in `docs/architecture.md`; scientific scope in `docs/scientific_scope.md`. Written 2026-09-21 (code baseline `3ff3734`).*

**Current pickup:** P0-2 accepted 2026-09-24 (ae88529, pushed); P0-3 implementation in flight (gpt-6-luna @ xhigh). RUN/GATES own live status.

## Top level

| path | what it is |
|---|---|
| `.claude/` | **State layer** (lives on `main`, moves with every closeout): `FRONTIER.md` (current state, read first) · `RUN.md` (in-flight runs + machine facts) · `GATES.md` (Steven's decisions) · `DIRECTOR.md` (binding standing orders + lessons) · `decisions.tsv` (append-only trail, write via `fm.sh log`) · `CLOSEOUT.md` (doc map) · this file · vendored skills in `skills/` |
| `src/jersey_outbreak/` | the entire Python package (flat module layout, see below) |
| `tests/` | pytest suite (~470 tests); named `test_<module>` or `test_<contract>`; `test_c3/c4_contracts` = cross-module contracts; goldens pinned in `benchmarks/` |
| `data/raw/` | **frozen source snapshots — immutable, `-text` gitattribute; never touch** |
| `data/processed/` | canonical epi tables (CSV) + `measure_dictionary.csv` + `table_manifest.json` + quality reports — rebuilt deterministically by the data pipeline; byte-identical rebuild is a gate |
| `docs/` | see docs layout below |
| `configs/` | versioned parameter YAMLs (disease parameter sets, observation configs) — a "disease" plugs in here |
| `benchmarks/` | CI fingerprint fixture + bench scripts (exact-equivalence gates for perf work) |
| `frontend/` | React frontend (test+build in CI mirror; rarely touched) |
| `scripts/` | repo utilities incl. `install_skills.sh` |
| `outputs/` | default artifact output root (gitignored, disposable) |
| `AGENTS.md` | Codex executors' constitution (binding on every brief) |
| `CLAUDE.md` | session router — the canonical "start here" |

## The pipeline (milestone naming used everywhere: artifacts, hashes, docs)

M1 evidence (frozen tables) → **M2** population (`population_*`) → **M3** daytime structure incl. jobs/schools (`population_structure_*`, `staffing_*`) → **M4** contact networks, 11 routes (`network_generator.py` — the biggest module; `network_schemas/artifacts`) → **M5** latent outbreak run (Starsim SEIRS: `outbreak_*`, `respiratory.py`, `starsim_adapter/compat`) → **M6** ensembles + bands (`ensemble*`) → **M7** interventions/scenarios (`intervention*`, `interventions.py`, `scenario.py`) → **M8** travel boundary (`travel*`) → observation model on top of M5/M6 (`observation*`). Each stage writes a versioned artifact with a manifest + `logical_content_hash`.

## src/ module groups

- **Identity & provenance (the sacred layer):** `hashing.py` (canonical JSON/SHA-256, `_stable_int`) · `scientific_hashes.py` (per-milestone logical-hash payloads; `m4_identity_edge` legacy-token shim) · `provenance.py` · `scientific_verification.py`, `verification_archive.py`, `bundle_selftest.py` (verifiers) · `contracts.py`. Any change here is hash-migration territory — declared, never smuggled.
- **Generators:** `population_generator.py`, `population_structure_generator.py`, `network_generator.py`, `outbreak_runner.py`, `ensemble.py`, `travel.py`, `observation.py`/`observation_scheduler.py`.
- **Schemas & artifacts:** every stage has `<stage>_schemas.py` (pydantic, strict, versioned) + `<stage>_artifacts.py` (write/load/verify). Schema version bumps = declared migrations.
- **Calibration (V1.3's home):** `calibration.py` (objective, held-out gate, 2-D identifiability profiles), `calibration_schemas.py`, `calibration_artifacts.py`.
- **Data pipeline (M1):** `data_pipeline.py` (frozen snapshot → canonical tables; `parse_published_value` suppression semantics), `canonical_schemas.py`, `artifact_catalog.py`.
- **Jobs/API:** `api.py`, `api_schemas.py`, `job_{manager,registry,worker,finalizer}.py`, `execution_adapter.py`, `parent_build.py` (one parent build + verified reuse).
- **Entry point:** `cli.py` — `jos` CLI (`outbreak run`, `ensemble run`, `intervention …`, `travel …`, `calibration …`, `data build`, `api serve`, `verification …`). `demo.py` = smoke.

## docs/ layout

- `docs/audits/` — every independent audit/review, `YYYY-MM-DD-<subject>-<auditor>-<VERDICT>.md`; the forward-scope authority is `2026-09-01-solpro-deep-audit-BLOCKED.md` §9–11.
- `docs/runs/` — run/executor reports (same date-prefix convention).
- `docs/research/v1_1|v1_2|v1_3/` — design syntheses and model-owner rulings; **`v1_3/2026-09-21-v13-plan.md` is the live plan.**
- `docs/handoff/2026-08-31-sol-handoff.md` — deep history/conventions (binding).
- `docs/architecture.md`, `docs/scientific_scope.md` — module boundaries, scientific claims/limits.
- `docs/roadmap.md` — living backlog · `docs/performance-history.md` — the perf story · `docs/progress.md` — claims, never evidence · `docs/desktop-setup.md` — machine bootstrap.

## Where things run

Loop home = WSL Ubuntu `~/jsy_disease_sim` (executors, runs, `fm.sh`); Windows checkout `C:\Users\StevBeast\Documents\jsy_disease_sim` (separate clone of the same repository, used by desktop sessions; both share GitHub origin — pull before writing). Evidence dirs: WSL `~/Documents/JOS_v1_2_full_scale_evidence/` (+ immutable V1/V1.1 dirs per hard rules) and kept measurement dirs `~/jos-astra-perf-*`, `~/jos-validation-20260919/`. No GitHub CI (billing) — the local mirror of the verify job is the gate.
