# Session log

Newest first. History only — current truth lives in the docs named by
`.claude/CLOSEOUT.md`.

## 2026-08-30 — M10.1 corrective milestone implementation

**Scope.** Frontend-only corrective work on `codex/m10.1-scientific-truth`,
based on M9 commit `bf7669eb5f0b3a315a227a3194726dfafe0ae32c`. Backend
scientific behavior, artifact writers, lifecycle ordering and identity rules
remain protected and unchanged.

**Corrections in progress.** Replaced silent missing-value zeros with explicit
unavailable values; preferred `cumulative_total_infections`; removed synthetic
comparison arms and geometric uncertainty bands; mapped ensembles to persisted
M6 summaries; constrained dates to 2025; corrected intervention payloads,
inclusive dates and detection-triggered timeline wording; bound provenance to
the displayed job; made mock data unmistakably demo/session-only; and corrected
the M9 API-gap documentation.

**Verification status.** The relevant backend suite passed (`76 passed`); the
frontend typecheck, 11 focused tests and production build passed. Live baseline
reconciliation, M6 ensemble loading, M8 travel loading and current namespaced
comparison loading passed. The corrected school payload validated and was
persisted with both school multipliers at zero, but the protected M9 worker
failed finalization because strict artifact verification rejects the serialized
calendar `start_date`. M10.1 therefore remains FAIL with no commit claimed.

## 2026-08-29 → 2026-08-30 — M10 design and frontend implementation

**Summary.** Designed the M10 interactive application end to end, then
implemented it as a working React/Vite frontend against the live M9 API.
All work on `codex/m10-interactive-app`, pushed to
`github.com/stev004/jsy_disease_sim` (private repo created this session —
the repo previously had no git remote).

**Decisions.**
- Visual direction: "Survey Instrument" (chosen over Journal / Console /
  Civic Atlas alternatives). Map treatment: "Survey Coral" (chosen from
  four options). Real OSM parish geometry (ODbL, attribution required).
- Template picker is a chip row, not a tile gallery; structural spacing on
  a 4px grid; global Simple/Scientific detail switch.
- Frontend stack: Vite + React 18 + TS, no runtime deps beyond
 react/react-router; mock data layer (the pre-M10.1 implementation auto-fell
 back when the API was down). Frontend default start date pinned to 2025-01-06
 (engine calendar).
- M10 gate NOT claimed — implementation exists; gate has not been run.

**Changes.** Commits 70b0dcb → 2ea6060 (all pushed): `docs/m10_ui_design.md`
(design spec + API-gap punch list), `frontend/` (scaffold 7ddf3fa, feature
views 2ea6060). Design artifacts (private claude.ai pages, linked in the
design doc): interactive mockup bbcad36a…, map treatments e92d61f2…,
design directions b68cf5f1….

**Verified.** Full end-to-end against the real engine: UI-submitted
scenario_run (ci mode, 2 interventions, travel) executed to SUCCEEDED;
Results renders real data (cumulative 2,009 = transmission_events rows;
routes/ages/travel cross-checked against independent API probes). Two bugs
found and fixed in the loop: 2026 default date (worker-killing), silent-zero
cumulative fallback (false fizzle callout).

**Open threads / resume points.**
- **M9.x API punch list** — owner: user decides when; spec lives in
  `docs/m10_ui_design.md` §14 items 9–14 (date-range validation at
  submission, per-arm compare datasets, populated breakdowns for travel
  artifacts, scenario display-name field, worker-log endpoint, wrong
  `dataset` echo field in dataset responses).
- **Frontend follow-ups** — parish choropleth for travel runs blocked on
  per-parish denominators (`observation_events` has `home_parish` counts
  but no denominators); intervention card "Edit" non-functional; travel
  "Custom" exposes no TravelConfig knobs yet; ExportMenu duplicated in
  results/compare views (dedupe when convenient).
- **Merge to main** — user's call: PR or merge `codex/m10-interactive-app`.
- **Pre-existing perf item** — verified M2–M4 parent caching (post-M9,
  pre-M10-gate), unchanged this session.
- Local test residue: ~10 throwaway jobs in
  `~/Library/Application Support/JerseyOutbreakSimulator/` from live
  bisection (harmless; M9 has no deletion endpoint).

**User needs to run.** Nothing mandatory. To use the app:
`uv run jos api serve` + `cd frontend && npm install && npm run dev`.
