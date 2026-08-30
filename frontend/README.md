# JOS M10 frontend

React/Vite implementation of the M10 interactive application, built to the
design in [`../docs/m10_ui_design.md`](../docs/m10_ui_design.md) ("Survey
Instrument" visual direction). It drives the M9 local API; it changes no
scientific behavior and claims no forecast validity.

## Run

```bash
# terminal 1 — the real engine API (optional)
uv run jos api serve

# terminal 2
cd frontend
npm install
npm run dev        # http://localhost:5173
```

The app uses a deterministic **demo-data mode** only when `VITE_JOS_MOCK=1`.
Without that explicit setting it stays on the real API; an API outage is shown
as an error and never silently changes the data source. A "Demo data" chip
appears in demo mode. Set `VITE_JOS_API` to use a non-default API.

`npm run typecheck` runs strict tsc; `npm run build` typechecks then builds.

## Stack and layout

Vite + React 18 + TypeScript + react-router; no other runtime
dependencies — charts and the parish map are hand-rolled SVG.

- `src/api/` — typed M9 client, explicit demo implementation, session proxy
- `src/app/` — shell, routing, theme / Simple–Scientific / drawer providers
- `src/components/` — shared primitives (JerseyMap, LineChart, HBar, chips…)
- `src/map/geometry.ts` — parish geometry (OpenStreetMap, ODbL; attribution
  is rendered in the app)
- `src/styles/` — design tokens (both themes) and component styles
- `src/views/{home,simulate,results,compare,runs,drawer}/` — feature views

## Known constraints (mirrors design doc §14)

- The builder constrains start dates to 1 Jan–31 Dec 2025 because that is the
  current engine calendar; the frontend does not silently clamp dates.
- Dataset shapes vary by job kind. Ensemble results use persisted
  `ensemble_summary`/replicate artifacts; single-run travel outputs may lack
  parish and age tables, which the UI marks unavailable. Local route displays
  use `daily_route.new_local_infections` or explicitly local event rows.
- Comparison uses the current M9 namespaced arm datasets and
  `comparison:matched_seed_comparison`; if those artifacts are absent, the UI
  reports that comparison data are unavailable and never synthesizes an arm.
- The API has no scenario display-name field or worker-log endpoint. The UI
  uses the persisted scenario identifier and labels worker-log access as
  unavailable.
- The current M9 finalizer rejects calendar-intervention artifacts after
  writing them because strict scenario verification does not accept the
  serialized ISO `start_date`; this is a backend lifecycle gap outside the
  frontend-only milestone.
