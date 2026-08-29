# Milestone 9/M9.1 local API and jobs

M9 provides a local application bridge around the verified M5–M8 engine. It
does not change epidemiological behavior and it does not make the synthetic
model a validated forecast. HTTP routes accept typed inline JSON only; they do
not accept Python, shell commands, import names, SQL, or arbitrary paths.

## Start the server

```bash
uv run jos api serve
uv run jos api serve --port 8001 --state-dir /path/to/jos-state
```

The server binds to `127.0.0.1` by default. `--host` accepts only
`127.0.0.1`, `::1`, or `localhost`; non-loopback binding is rejected. The
default port is 8000. Local browser development origins can be configured with
`JOS_CORS_ORIGINS`, a comma-separated allow-list; the default allow-list is
`http://localhost:3000,http://localhost:5173`. Every configured origin must be
an explicit HTTP(S) loopback origin; wildcard, `null`, credentialed, and
non-loopback origins are rejected.

The generated OpenAPI document is available at `/docs` and `/openapi.json`.
Application routes are versioned under `/api/v1` and use schema identifier
`m9-1.0`.

## State and execution

Runtime state is outside the Git worktree by default. `JOS_STATE_DIR` or
`--state-dir` overrides the per-user location. The directory contains:

```text
state/
  jobs.sqlite
  jobs/<opaque-uuid>/
    request.json
    result_candidate.json
    result_manifest.json
    logs/worker.stdout.log
    logs/worker.stderr.log
    parents/
    artifacts/
```

SQLite schema version 1 uses WAL mode, foreign keys, and atomic write
transactions. Every request is canonically serialized and hashed separately
from scientific scenario, latent-outcome, and artifact-bundle hashes. The
canonical request is stored both in SQLite and `request.json`.

The scheduler is deterministic FIFO and defaults to one API scientific job at
a time. An API job is one isolated subprocess launched with `sys.executable`
and the fixed internal entrypoint `python -m jersey_outbreak.job_worker`.
Ensembles retain their existing internal worker bound; API concurrency and
ensemble concurrency are separate controls. Increasing API concurrency is an
advanced local resource decision.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Cheap liveness/registry check |
| GET | `/api/v1/capabilities` | API, engine, route, intervention, travel, dataset, and scheduler metadata |
| POST | `/api/v1/scenarios/validate` | Synchronous typed scenario validation; never runs the epidemic |
| POST | `/api/v1/jobs` | Submit `scenario_run`, `scenario_compare`, or `ensemble`; returns 202 |
| GET | `/api/v1/jobs` | Bounded newest-first listing with state/kind filters |
| GET | `/api/v1/jobs/{job_id}` | Status, phase, identities, error summary, worker diagnostics |
| POST | `/api/v1/jobs/{job_id}/cancel` | Idempotent queued/running cancellation |
| GET | `/api/v1/jobs/{job_id}/events` | Append-only application event stream |
| GET | `/api/v1/jobs/{job_id}/artifacts` | Job-owned verified scientific artifact metadata |
| GET | `/api/v1/jobs/{job_id}/datasets` | Manifest-known dataset metadata and schemas |
| GET | `/api/v1/jobs/{job_id}/datasets/{dataset_name}` | Bounded, paginated, filtered Parquet records |

Job submission supports an optional `Idempotency-Key`. The same key and
canonical request returns the existing job; reusing it for another request is
a 409 conflict. Without a key, intentionally repeated scientific requests
create separate jobs.

## States and restart behavior

Legal states are `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`,
`CANCEL_REQUESTED`, `CANCELLED`, and `INTERRUPTED`. A scientific job becomes
`SUCCEEDED` only through the M9.1 finalizer. The worker's
`result_candidate.json` contains only artifact roles and manifest paths. The
finalizer reloads the canonical request, enforces the exact job-kind/role/type
contract, independently verifies content-derived M5--M8 scientific identities,
checks request and Git provenance, writes and rereads the M9 result manifest,
then atomically publishes artifact rows, ordered events, and `SUCCEEDED` in one
SQLite transaction. The generic state machine cannot publish success. Failed
or partial output is not exposed as a verified successful result.

Queued jobs survive an API restart. API-owned active jobs are terminated on
graceful shutdown and become `INTERRUPTED`; a later process never silently
reruns them. On startup, a persisted result candidate whose database transition
was interrupted is passed through that same finalizer; an existing result
manifest is never trusted as proof of success. Otherwise stale active jobs
become `INTERRUPTED` and are never silently rerun.

Cancellation sends `SIGTERM` to the worker's dedicated POSIX process group and
uses `SIGKILL` only if necessary. It never targets unrelated processes. A
cancelled job is not promoted to `SUCCEEDED`, even if a cancellation races
with final output registration. Worker logs are retained as bounded tails.

Progress is intentionally coarse: `queued`, `validating`, `preparing`,
`running`, `writing_artifacts`, `verifying`, `finalizing`, and `complete`. Fractional
progress is null because Starsim does not expose a truthful run fraction at
this boundary.

## Results and provenance

The M9 `result_manifest.json` is an application manifest, separate from each
scientific artifact manifest. It records the job ID/kind, API version/schema,
request hash, worker-observed engine commit, dirty-worktree flag, artifact roles, scientific
scenario/latent/bundle hashes, and summary metadata. The provenance chain is:

```text
HTTP request
  -> canonical request hash
  -> scientific scenario/run identity
  -> latent outcome identity
  -> verified scientific artifact bundle
  -> M9 result manifest
```

Dataset names are derived from allow-listed scientific manifest outputs. Reads
support date and selected dimensions such as parish, route, age band,
intervention, scope, metric, key, and seed, plus an optional repeated `columns`
projection. Arrow applies projection and predicates while scanning and stops
materializing after one look-ahead row beyond the requested page. Unfiltered
totals come from Parquet metadata; filtered `total` is `null` so a tiny page
does not trigger a second whole-dataset count scan, while `has_more` and
`next_offset` remain available. Responses default to 1,000 rows and have a
hard maximum of 10,000 rows. Pagination preserves each scientific writer's
canonical row order. JSON serialization converts non-finite numeric values to
`null`.

M9 currently defers raw artifact download, retention cleanup, remote access,
authentication, WebSockets/SSE, fractional progress, and all frontend/UI
work. Full-island timing is dominated by repeated deterministic M2--M4 parent
construction, not application finalization; verified parent reuse remains a
post-M9/pre-M10 performance item. The direct `jos` scientific CLI remains
independent and supported.
