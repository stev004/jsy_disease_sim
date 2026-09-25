UI INTEGRATION RE-REVIEW: BLOCKED

Two findings remain under the amended spec:

- **H1 — legends from rendered data: open.** `LineChart` omits a series with fewer than two points, but the band-legend check can still show “Replicate range” for that omitted series. Compare also always shows both averted and added area swatches, even when the chart draws neither area. See [LineChart.tsx](/home/steven/jos-ui-integ-rereview-readonly/frontend/src/components/LineChart.tsx:70) and [CompareView.tsx](/home/steven/jos-ui-integ-rereview-readonly/frontend/src/views/compare/CompareView.tsx:420). Every `LineChart` use now supplies a role.
- **M2 — signed difference tooltips: open.** The difference-map tooltip divides a known parish count difference by the *island* population and rounds to one decimal. A difference of 1 with a population of 100,000 appears as `+0.0 per 1,000`; an equal result appears as `+0.0`. If population is missing, the tooltip says unavailable even when both parish counts are present. The tooltip should retain the actual signed parish difference. See [CompareView.tsx](/home/steven/jos-ui-integ-rereview-readonly/frontend/src/views/compare/CompareView.tsx:324).

| Item | Decision |
|---|---|
| H2: shared visible/PNG bar colours, including first row and opacity per panel | Closed |
| M1: null age has no bar; zero has a zero-width bar | Closed |
| M3: named 44px targets | Closed |
| L1–L3: interface teal, ember-only infection bars, neutral died-out styling | Closed; I checked the `--accent` inventory |
| U1 finding 1 | Open on legend accuracy; roles are fixed |
| U2 findings 2 / 4 / 5 | Closed / closed / closed |

The supplied mirror log for this SHA reports **15 passed, 6 skipped**, with typecheck and build passing. I read it and did not rerun it. The corrective diff has no whitespace errors. No edits were made; `git status --porcelain` is empty. Final SHA: `3b687a2803e90017948cffd9663d43dbe88fcc17`.