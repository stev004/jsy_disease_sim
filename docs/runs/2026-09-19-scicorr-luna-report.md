# JOS scicorr — DISEASE-4 / ROUTE-6 / ROUTE-7

Date: 2026-09-19
Worktree: /home/steven/jos-scicorr-wt

## Result and flagged question

All three ruled corrections are implemented. Replicate-level latent, M4, and observation identity is unchanged in the required base/head A/B. M6 summary/manifest identity changes through schema version 1.5 to 1.6.

Changing emitted workplace metadata from inert persistence_days=7 to truthful daily 1 would otherwise change the frozen M4 hash. scientific_hashes.m4_identity_edge() therefore retains the old value only while projecting the M4 identity payload; generated route edges and artifacts emit 1. This is the narrowest way to satisfy both ROUTE-7 and the hard replicate-identity invariant. The route spec keeps its existing generic periodically_refreshed enum to avoid an additional M4 route-spec identity change; the scientific route documentation states the actual daily weekday refresh explicitly.

## DISEASE-4 — no fabricated incidence tail zeros

Changed:

- ensemble.py: incidence cells are structural zeroes only between the first and last observed dates for that metric. Missing dates beyond the metric horizon are value=None, cell_semantic=outside_metric_horizon, and non-contributing.
- ensemble_schemas.py and scientific_hashes.py: M6 schema/config/hash default version 1.5 -> 1.6.
- Added tests/test_ensemble_band_horizon.py; updated C3/C4 contract assertions.
- Updated ensemble semantics in docs/architecture.md, docs/progress.md, and docs/scientific_scope.md.

Base regression evidence:

    $ PYTHONPATH=/tmp/jos-scicorr-base2/src .venv/bin/pytest tests/test_ensemble_band_horizon.py -q -ra
    F                                                                        [100%]
    E       assert short_tail["value"] is None
    E       assert 0.0 is None
    1 failed in 0.19s

Head evidence:

    $ UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_ensemble_band_horizon.py -q -ra
    .                                                                        [100%]
    1 passed in 0.05s

## ROUTE-6 — activity_cv only where it acts

Tracing showed _activity_weighted_participants() is called only by community builders. It was inert for school_cross_class and workplace_transient, whose expected participant count equals the eligible pool. CONTACT_ACTIVITY_ROUTES now declares only community_indoor and community_outdoor. The inert routes were not wired to the mechanism. tests/test_networks.py asserts their snapshots are unchanged when activity_cv changes and checks the diagnostic allow-list.

Declaration/call-site evidence:

    CONTACT_ACTIVITY_ROUTES = (
        "community_indoor",
        "community_outdoor",
    )
    _activity_weighted_participants() calls: community builder only

Required grep output:

    $ grep -rn --exclude-dir=__pycache__ "activity_cv" src/
    src/jersey_outbreak/network_generator.py:406:    activity_cv: float,
    src/jersey_outbreak/network_generator.py:411:    if activity_cv == 0:
    src/jersey_outbreak/network_generator.py:413:    variance = activity_cv * activity_cv
    src/jersey_outbreak/network_generator.py:442:            float(config.activity_cv),
    src/jersey_outbreak/network_generator.py:2371:        if config.activity_cv == 0:
    src/jersey_outbreak/network_generator.py:2409:            if config.activity_cv == 0:
    src/jersey_outbreak/network_generator.py:2573:            float(config.activity_cv),
    src/jersey_outbreak/network_generator.py:2579:    realised_activity_cv = (
    src/jersey_outbreak/network_generator.py:2683:            "distribution": "constant" if config.activity_cv == 0 else "gamma",
    src/jersey_outbreak/network_generator.py:2685:            "activity_cv": float(config.activity_cv),
    src/jersey_outbreak/network_generator.py:2688:            "realised_cv": realised_activity_cv,
    src/jersey_outbreak/network_generator.py:2695:            "zero_cv_exact_bypass": config.activity_cv == 0,
    src/jersey_outbreak/network_generator.py:2698:                "activity_cv": {
    src/jersey_outbreak/network_generator.py:2699:                    "value": float(config.activity_cv),
    src/jersey_outbreak/network_generator.py:2706:                    "sensitivity_required": config.activity_cv != 0,
    src/jersey_outbreak/network_generator.py:2716:                        "Gamma(shape=1/activity_cv^2, scale=activity_cv^2); constant one "
    src/jersey_outbreak/network_generator.py:2717:                        "when activity_cv=0"
    src/jersey_outbreak/network_schemas.py:110:    activity_cv: StrictFloat = Field(default=0.0, ge=0)

## ROUTE-7 — workplace daily metadata and travel determination

Changed:

- network_generator.py: workplace transient edges carry persistence_days=1; the call is documented as daily regeneration with Starsim receiving dur=1.
- architecture.md and scientific_scope.md: workplace transient active sets and bounded rings are regenerated on every weekday snapshot, with no weekly workplace persistence.
- tests/test_networks.py: every generated workplace-transient edge is asserted to have persistence_days == 1.
- ci-fingerprint-fixture.json: the two affected workplace runtime fingerprints changed because emitted metadata changed. Array fingerprints, edge counts, and stable-int call counts were unchanged.
- test_m4_hash_stream.py: eager M4 identity payload construction uses the same explicit identity projection as production.

Persistence grep (generic plumbing remains; no emitted workplace 7 claim remains in the generator/artifact schema):

    $ grep -rn --exclude-dir=__pycache__ "persistence_days" src/jersey_outbreak/network_generator.py src/jersey_outbreak/network_artifacts.py
    src/jersey_outbreak/network_generator.py:522:    p1: str, p2: str, weight: float, persistence_days: int = 1
    src/jersey_outbreak/network_generator.py:531:        "persistence_days": int(persistence_days),
    src/jersey_outbreak/network_artifacts.py:225:            ("persistence_days", pa.int64()),
    src/jersey_outbreak/network_artifacts.py:304:            ("persistence_days", pa.int64()),

Travel determination: travel.py is a separate live M8 temporary-edge mechanism. Its route_edges and temporary_edge_rows use travel edge persistence_days/duration_days for visitor accommodation, host household, transit, and related temporary travel provenance. starsim_adapter.py maps the dynamic travel edge table to its daily dur representation. No travel code was changed.

## Required A/B proof

Commands:

    $ PYTHONPATH=/tmp/jos-scicorr-base/src .venv/bin/jos ensemble run --mode ci --seeds 101,102,103 --duration-days 30 --ensemble-id scicorr-ab --output-dir /tmp/scicorr-base
    artifact: /tmp/scicorr-base/jos-ensemble-m6-scicorr-ab-281fb74142ea
    manifest schema: 1.5

    $ PYTHONPATH=/home/steven/jos-scicorr-wt/src .venv/bin/jos ensemble run --mode ci --seeds 101,102,103 --duration-days 30 --ensemble-id scicorr-ab --output-dir /tmp/scicorr-head
    artifact: /tmp/scicorr-head/jos-ensemble-m6-scicorr-ab-33f1bba8fc6b
    manifest schema: 1.6

Final comparison output:

    base_manifest_schema_version= 1.5
    head_manifest_schema_version= 1.6
    latent_run_logical_content_hash_identical= True
    m4_logical_content_hash_identical= True
    observation_logical_content_hash_identical= True
    base_m6_logical_content_hash= 281fb74142ea16a8b424e322223a3136dae46a7dc8d17ad5fcaf7c5966ee0f7e
    head_m6_logical_content_hash= 33f1bba8fc6b3982936fec1152c54aed2196ae7ce077b7ce05876363ba999fdd
    m6_logical_content_hash_differs= True

## Gates and evidence

    $ UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_ensemble_band_horizon.py tests/test_c3_contracts.py tests/test_c4_contracts.py tests/test_networks.py tests/test_m4_hash_stream.py tests/test_bench_dynamic_routes.py -q -ra
    61 passed in 72.18s (0:01:12)

    $ UV_CACHE_DIR=/tmp/uv-cache uv run mypy --ignore-missing-imports src/jersey_outbreak/population_structure_schemas.py src/jersey_outbreak/population_structure_controls.py src/jersey_outbreak/population_structure_artifacts.py src/jersey_outbreak/population_structure_generator.py src/jersey_outbreak/network_schemas.py src/jersey_outbreak/network_generator.py src/jersey_outbreak/network_artifacts.py src/jersey_outbreak/intervention_schemas.py src/jersey_outbreak/interventions.py src/jersey_outbreak/intervention_artifacts.py src/jersey_outbreak/intervention_analysis.py src/jersey_outbreak/scenario.py src/jersey_outbreak/staffing_evidence.py src/jersey_outbreak/staffing_generator.py src/jersey_outbreak/starsim_adapter.py
    Success: no issues found in 15 source files

    $ UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .
    All checks passed!
    $ UV_CACHE_DIR=/tmp/uv-cache uv run ruff format --check .
    242 files already formatted

Full suite:

    $ UV_CACHE_DIR=/tmp/uv-cache uv run pytest
    394 passed, 4 skipped, 1 failed, 9 warnings in 843.38s (0:14:03)
    FAILED tests/test_prov_job_ordering.py::test_missing_head_request_fails_alone_and_scheduler_continues

The failed test passes in isolation:

    $ UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_prov_job_ordering.py::test_missing_head_request_fails_alone_and_scheduler_continues -q -ra
    .                                                                        [100%]
    1 passed in 3.85s

No full-mode or scaled-mode ensemble/benchmark was launched. No data/, raw inputs, frozen snapshots, or evidence directories were changed. No commit was created.

## Files changed

    benchmarks/ci-fingerprint-fixture.json
    docs/architecture.md
    docs/progress.md
    docs/scientific_scope.md
    src/jersey_outbreak/ensemble.py
    src/jersey_outbreak/ensemble_schemas.py
    src/jersey_outbreak/network_generator.py
    src/jersey_outbreak/scientific_hashes.py
    tests/test_c3_contracts.py
    tests/test_c4_contracts.py
    tests/test_ensemble_band_horizon.py
    tests/test_m4_hash_stream.py
    tests/test_networks.py
