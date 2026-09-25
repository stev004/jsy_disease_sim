UI INTEGRATION REVIEW: BLOCKED

The redesign is substantially integrated, but the remaining chart colour wiring, PNG mismatch, and §8 accessibility and data-honesty gaps should be corrected before it is offered for merge.

### Findings

**High**

- **U1 finding 1 remains open.** The Results tide, parish, and intervention curves omit a semantic role, so `LineChart` renders them in teal; the tide legend says ember. The travel series also omit roles: their rendered teal/muted strokes disagree with the ember/baseline legend, which shows both entries even when only one series exists. See [ResultsView.tsx](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/ResultsView.tsx:333), [ResultsView.tsx](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/ResultsView.tsx:347), [TabsBand.tsx](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/TabsBand.tsx:218), [TabsBand.tsx](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/TabsBand.tsx:255), and [LineChart.tsx](/home/steven/jos-ui-integ-review-readonly/frontend/src/components/LineChart.tsx:63). **Fix:** assign a role or explicit token to every series and derive each legend from the series actually rendered. Use neutral ink for visitor counts; reserve ember for infections.
- **U2 finding 5 remains open.** The visible first ranked bar is `--epi`, while the PNG builder defaults uncoloured rows to `--accent`; later bars also lose the visible theme styling and opacity. See [HBar.tsx](/home/steven/jos-ui-integ-review-readonly/frontend/src/components/HBar.tsx:46), [base.css](/home/steven/jos-ui-integ-review-readonly/frontend/src/styles/base.css:199), [TabsBand.tsx](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/TabsBand.tsx:135), and [exporters.ts](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/exporters.ts:138). **Fix:** use one colour resolver for visible and exported bars, including each panel’s first row and opacity.

**Medium**

- **Missing age data becomes a zero-width bar.** A null age value is converted with `?? 0`, making missing and genuine zero visually identical. See [TabsBand.tsx](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/TabsBand.tsx:405) and [TabsBand.tsx](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/TabsBand.tsx:419). **Fix:** omit the bar when its value is null; retain the “not available” text.
- **The Compare difference map lacks signed tooltips.** Its parish SVG titles contain only names; signed differences appear in a separate list. See [JerseyMap.tsx](/home/steven/jos-ui-integ-review-readonly/frontend/src/components/JerseyMap.tsx:87) and [CompareView.tsx](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/compare/CompareView.tsx:494). **Fix:** pass parish-specific tooltip text to the difference map.
- **Several controls are below the required 44px target:** Results layer labels, the Shortcuts button and died-out actions, plus the export-menu items. See [results.css](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/results.css:178), [results.css](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/results.css:336), [results.css](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/results.css:261), and [views.css](/home/steven/jos-ui-integ-review-readonly/frontend/src/styles/views.css:257). **Fix:** give these interactive targets a 44px minimum height.

**Low — §2.3 cohesion**

- The Compare day slider uses infection `--seq5` for an interface control. Use `--accent`. [compare.css](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/compare/compare.css:103)
- The died-out outcome uses verification `--warn`. Use neutral styling. [results.css](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/results.css:237)
- Secondary ranked infection bars use teal, as §5 explicitly directs, but that conflicts with §2.3’s “teal never encodes data magnitude” rule. This affects [base.css](/home/steven/jos-ui-integ-review-readonly/frontend/src/styles/base.css:200) and the parish ranking in [results.css](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/results/results.css:497). The design authority needs one consistent rule before changing those bars.

The director-noted **Compare baseline swatch is correct**: `--base-line` in [compare.css](/home/steven/jos-ui-integ-review-readonly/frontend/src/views/compare/compare.css:92) matches the chart’s baseline role.

### Decisions 1–6

1. **U1 finding 1: Open.** Compare’s two arms and the Results tab’s epidemic curve are wired correctly; the remaining Results uses above are not.
2. **Cross-page vocabulary: Fail.** The travel chart, Compare slider and died-out callout violate §2.3; ranked teal bars expose an internal §2.3/§5 conflict.
3. **U2 findings 2/4/5: Closed / closed / open.** The six-bin mapper and legend agree; Results tiles pass null plus availability notes; PNG colours still differ.
4. **§8 hard constraints: Partial.** Verbatim disclaimers, mock-only Demo chip, unchanged builders/tests, labels, and reduced-motion rules are present. Missing-age rendering, signed map tooltips and 44px targets fail.
5. **Merge resolutions: Sensible.** [components/index.ts](/home/steven/jos-ui-integ-review-readonly/frontend/src/components/index.ts:9) retains exports and adds the new ones. The page styles override legacy rules in `views.css`, including the Results tabs grid reset; no conflict markers remain.
6. **Combined implementation: Blocked by the findings above.** Home, Simulate, Runs & evidence, and the drawer show no separate integration break in this source review.

The supplied [frontend mirror log](/home/steven/jos-ui-integ-mirror.log) reports **15 passed, 6 skipped**, with typecheck and build passing. This review made no edits. Final SHA: `54b376a683ba2ee605b5d4f66b08e5e944b17e26`; `git status --porcelain` was empty.