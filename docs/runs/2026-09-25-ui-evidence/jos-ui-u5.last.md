**Verdict: PASS for implementation and requested gates.** Home, Simulate, and the provenance drawer are restyled with shared theme tokens. No browser renderer was available for a rendered screenshot review.

- **Layouts:** Home has a full-width neutral parish map, population line, actions, step panels, recent-run rows, and footer. Simulate has a two-column form and sticky summary, with numeric values in mono. Drawer styling uses the 440px panel and shared tokens.
- **Logic preserved:** `isSupportedStartDate` is byte-for-byte unchanged. `request.ts`, `templates.ts`, and `interventions.ts` have no diff. The preview imports `deriveInterventions`; detection-triggered lanes show untimed notes without implying a calendar window.
- **Verbatim strings:** Greps passed for all four required strings: the Home footer sentence, drawer paragraph, top-bar disclaimer, and OSM attribution.
- **Gates:** `npm ci` passed; `npm test` passed (15 passed, 6 skipped); typecheck passed; build passed (81 modules). Mock-mode Vite served the app entry and Home, Simulate, and Drawer modules with HTTP 200, then was stopped.
- **Evidence:** [jos-ui-u5-evidence.log](/tmp/jos-ui-u5-evidence.log)

Files changed: [HomeView.tsx](/home/steven/jos-ui-u5-wt/frontend/src/views/home/HomeView.tsx), [SimulateView.tsx](/home/steven/jos-ui-u5-wt/frontend/src/views/simulate/SimulateView.tsx), [ProvenanceContent.tsx](/home/steven/jos-ui-u5-wt/frontend/src/views/drawer/ProvenanceContent.tsx), [views.css](/home/steven/jos-ui-u5-wt/frontend/src/styles/views.css), and [drawer.css](/home/steven/jos-ui-u5-wt/frontend/src/views/drawer/drawer.css).

Diff stat: **5 files changed, 294 insertions, 60 deletions.** No commit or push.