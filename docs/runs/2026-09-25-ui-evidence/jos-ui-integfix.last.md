**PASS — all review findings are addressed.** HEAD remains `54b376a683ba2ee605b5d4f66b08e5e944b17e26` on `ui/integration`; no commit or push was made.

### Findings

- **H1:** Every Results and Compare line series now carries a semantic role. Visitor counts use neutral ink; infection curves use `epi`. Legends filter to series and bands that `LineChart` actually draws. See [LineChart.tsx](/home/steven/jos-ui-integ-wt/frontend/src/components/LineChart.tsx:70), [ResultsView.tsx](/home/steven/jos-ui-integ-wt/frontend/src/views/results/ResultsView.tsx:338), [TabsBand.tsx](/home/steven/jos-ui-integ-wt/frontend/src/views/results/TabsBand.tsx:239), and [CompareView.tsx](/home/steven/jos-ui-integ-wt/frontend/src/views/compare/CompareView.tsx:415).

- **H2:** [rankedBarColor.ts](/home/steven/jos-ui-integ-wt/frontend/src/components/rankedBarColor.ts:9) supplies the shared color and opacity rule: infection bars use `--epi` at full opacity for the first row and 55% thereafter; neutral bars use `--ink-2`. HBar and the PNG exporter use it, and route export resets the rank for each visible panel. Age and parish rankings also use the infection rule. See [HBar.tsx](/home/steven/jos-ui-integ-wt/frontend/src/components/HBar.tsx:33), [exporters.ts](/home/steven/jos-ui-integ-wt/frontend/src/views/results/exporters.ts:116), and [TabsBand.tsx](/home/steven/jos-ui-integ-wt/frontend/src/views/results/TabsBand.tsx:442).

- **M1:** Missing age values omit the bar and retain the “not available” text; genuine zero values retain a zero-width bar. See [TabsBand.tsx](/home/steven/jos-ui-integ-wt/frontend/src/views/results/TabsBand.tsx:452).

- **M2:** The Difference map now supplies each parish’s signed tooltip, using a true minus sign and the published population denominator. Missing parish values or denominator produce an unavailable tooltip. See [JerseyMap.tsx](/home/steven/jos-ui-integ-wt/frontend/src/components/JerseyMap.tsx:19) and [CompareView.tsx](/home/steven/jos-ui-integ-wt/frontend/src/views/compare/CompareView.tsx:323).

- **M3:** Results layer labels, Shortcuts, died-out actions, export items, and both Results sliders meet the 44px minimum. The audit also raised the Runs back button, Simulate disclosure summary, and shared range controls to 44px. See [results.css](/home/steven/jos-ui-integ-wt/frontend/src/views/results/results.css:178), [views.css](/home/steven/jos-ui-integ-wt/frontend/src/styles/views.css:58), and [runs.css](/home/steven/jos-ui-integ-wt/frontend/src/views/runs/runs.css:22).

- **L1–L3:** The Compare slider uses `--accent`; the died-out callout uses neutral surfaces and ink; ranked infection bars use only the ember `--epi` token. No remaining `--accent` matches in the requested grep paths are data marks.

### `--accent` inventory

Every match from `grep -rn "var(--accent)" src/views src/components` is interface or provenance styling:

- `drawer.css:112,115` — copy-link hover and focus.
- `compare.css:103` — slider control.
- `results.css:94–95,157,161,189,296–297,532` — selected metric, playback state/control, checkbox control, selected tab.
- `runs.css:179–180,185,198,389` — pipeline state and hash-chain hover.
- `ProvenanceChain.tsx:68` — provenance connector.

The additional scan of shared `src/styles` found only focus, shell, button, slider, selection, hover, toast, and pipeline-state styling.

### Verification

- `npm run typecheck` — passed.
- `npm test` — 15 passed, 6 skipped.
- `npm run build` — passed.
- Disclaimer greps and `git diff --check` — passed.

Full command output and inventories are saved in [jos-ui-integfix-evidence.log](/tmp/jos-ui-integfix-evidence.log).

**Diff stat:** 14 files changed, 239 insertions, 127 deletions, including the 12-line new resolver.