**Verdict: PASS — U2 implemented on `ui/u2-results`; no commit or push.**

The Results page now has the Harbour header, map and tide gauge, 420px right rail, and tabs below the main layout. Playback uses 500ms/day; the map pulse follows the parish with the most published new infections that day and is absent for zero or missing values. The map uses six sequential bins. Single-seed runs show no replicate band and retain the single-seed note. Missing values remain unavailable rather than being drawn as zero.

The existing loading, metric and layer controls, parish selection, keyboard shortcuts, PNG/CSV exports, and died-out text are retained. Intervention windows use the existing timeline builder. View colors use tokens; exporter fallbacks are documented and match Notebook token values.

**Acceptance evidence**

- `npm test`: 15 passed, 6 skipped. Typecheck and production build passed.
- Spec disclaimer phrase checks and `git diff --check` passed.
- Mock Vite server returned the app successfully and was stopped.
- No browser binary or browser tool was available for a visual check in both themes; that review remains for the director.

Evidence is saved in [`/tmp/jos-ui-u2-evidence.log`](/tmp/jos-ui-u2-evidence.log).

**Files and diff stat**

Changed [ResultsView.tsx](/home/steven/jos-ui-u2-wt/frontend/src/views/results/ResultsView.tsx), [TabsBand.tsx](/home/steven/jos-ui-u2-wt/frontend/src/views/results/TabsBand.tsx), [results.css](/home/steven/jos-ui-u2-wt/frontend/src/views/results/results.css), [exporters.ts](/home/steven/jos-ui-u2-wt/frontend/src/views/results/exporters.ts), and [geometry.ts](/home/steven/jos-ui-u2-wt/frontend/src/map/geometry.ts).

`5 files changed, 864 insertions(+), 327 deletions(-)`

**For U3/U5:** `LineChart` already supports day markers and intervention hatch windows; no dual-arm changes were made, and `divColor` is unchanged. `seqColor` now uses six bins. Styling changes are scoped to Results; no shared components or other views were modified. `npm ci` reported 7 vulnerabilities in the installed dependency set; this unit made no dependency changes.