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

With no API running the app auto-falls back to a deterministic **demo-data
mode** (a "Demo data" chip appears in the top bar). Force it with
`VITE_JOS_MOCK=1`; point at a non-default API with `VITE_JOS_API`.

`npm run typecheck` runs strict tsc; `npm run build` typechecks then builds.

## Stack and layout

Vite + React 18 + TypeScript + react-router; no other runtime
dependencies — charts and the parish map are hand-rolled SVG.

- `src/api/` — typed M9 client, mock implementation, auto-fallback proxy
- `src/app/` — shell, routing, theme / Simple–Scientific / drawer providers
- `src/components/` — shared primitives (JerseyMap, LineChart, HBar, chips…)
- `src/map/geometry.ts` — parish geometry (OpenStreetMap, ODbL; attribution
  is rendered in the app)
- `src/styles/` — design tokens (both themes) and component styles
- `src/views/{home,simulate,results,compare,runs,drawer}/` — feature views

## Known constraints (mirrors design doc §14)

- Scenario start dates must lie in the engine's 2025 calendar; the API
  accepts later dates but the worker fails.
- Travel-composed runs publish empty `daily_parish`/`daily_age`; the UI
  shows honest "not published by this run" states and derives route
  attribution from `transmission_events`.
- The Compare screen derives its intervention arm (with a declared
  assumption banner) until the API serves per-arm datasets.
