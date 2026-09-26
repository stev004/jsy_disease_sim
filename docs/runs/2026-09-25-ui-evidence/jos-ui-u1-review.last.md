UI U1 REVIEW: BLOCKED

### Findings

- **High — chart colours misidentify data.** [LineChart.tsx](/home/steven/jos-ui-u1-review-readonly/frontend/src/components/LineChart.tsx:155) assigns the intervention colour to every second series. The Compare intervention line and the Results travel series now disagree with their existing legends ([CompareView.tsx](/home/steven/jos-ui-u1-review-readonly/frontend/src/views/compare/CompareView.tsx:373), [TabsBand.tsx](/home/steven/jos-ui-u1-review-readonly/frontend/src/views/results/TabsBand.tsx:460)). Give series explicit semantic roles and make each legend use the rendered line token.

- **High — the six-bin infection scale is not in use.** [seqColor](/home/steven/jos-ui-u1-review-readonly/frontend/src/map/geometry.ts:66) still maps to five bins, and the [Results legend](/home/steven/jos-ui-u1-review-readonly/frontend/src/views/results/ResultsView.tsx:428) shows five swatches. `--seq5` never represents the highest map magnitude. Update the mapper and legend together.

- **Medium — “no preference” produces mixed themes.** [tokens.css](/home/steven/jos-ui-u1-review-readonly/frontend/src/styles/tokens.css:60) and [ThemeProvider.tsx](/home/steven/jos-ui-u1-review-readonly/frontend/src/app/ThemeProvider.tsx:34) correctly choose dark, but the dark nav, shadow and bar rules in [base.css](/home/steven/jos-ui-u1-review-readonly/frontend/src/styles/base.css:45) require an explicit dark media match. Use the same selection condition for those rules.

- **Medium — missing-value tooltips do not reach Results tiles.** [MetricTile.tsx](/home/steven/jos-ui-u1-review-readonly/frontend/src/components/MetricTile.tsx:16) recognizes only null values; [ResultsView.tsx](/home/steven/jos-ui-u1-review-readonly/frontend/src/views/results/ResultsView.tsx:449) passes formatted `"—"` strings. Pass null with an availability note so the required tooltip appears.

- **Medium — PNG bars no longer match visible bars.** [HBar.tsx](/home/steven/jos-ui-u1-review-readonly/frontend/src/components/HBar.tsx:46) gives the first bar `--epi` and later bars theme dependent colours, while [exporters.ts](/home/steven/jos-ui-u1-review-readonly/frontend/src/views/results/exporters.ts:136) still exports unoverridden bars in `--accent`. Align export colours with HBar.

- **Medium — the persistent disclaimer lacks the specified placement and accessible exposure.** [AppShell.tsx](/home/steven/jos-ui-u1-review-readonly/frontend/src/app/AppShell.tsx:64) puts it inside the brand link, whose `aria-label="JOS home"` replaces descendant text for its accessible name. Render the verbatim disclaimer as a separate right-side pill.

- **Low — the token-only and target-size checks fail.** [base.css](/home/steven/jos-ui-u1-review-readonly/frontend/src/styles/base.css:221) retains a literal `rgba()` outside tokens; its [close button](/home/steven/jos-ui-u1-review-readonly/frontend/src/styles/base.css:202) is below 44px. Move the colour into a token and size the icon target to 44px.

### Contrast on `--panel`

| Theme | `--ink` | `--ink-2` | `--ink-3` |
|---|---:|---:|---:|
| Notebook | 15.21:1 | 7.30:1 | 5.20:1 |
| Harbour | 14.38:1 | 10.00:1 | 6.54:1 |

All three meet the §2.2 thresholds.

### Acceptance decisions

1. **Tokens:** Exact specified surface and semantic values are present in all three blocks; the two dark blocks match, no existing variable was removed, and no data colour equals the accent. **Partial** because the six-bin scale is unused and no-preference styling is inconsistent.
2. **Contrast:** **Pass.**
3. **Shell:** Four zones, routes, 64px bar, 44px shell controls, mock-only Demo chip, and Simple/Scientific behaviour are present. **Fail** on disclaimer placement and accessibility. The director’s stated visual checks cover overlap at the specified sizes.
4. **Components and exports:** JerseyMap and LineChart props are additive; exported symbols remain. **Fail** on colour semantics, PNG fidelity, missing-value tooltip and the literal colour in base.css.
5. **Motion:** Required motion rules and reduced-motion override are present. **Pass** for the U1 foundation.
6. **Verbatim disclaimers:** **Pass** for source wording; the shell accessibility issue above remains.
7. **U2–U5 readiness and accessibility:** **Fail.** The chart’s index-based colour rule and five-bin mapper must be corrected before page work builds on them.

The supplied clean-clone mirror reports **15 tests passed, 6 skipped; typecheck and build passed**. This review made no edits. Final SHA: `7d5b0dec43c87adb87380c68f13280015e12194f`; `git status --porcelain` was empty.