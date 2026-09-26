**Verdict: PASS — U3 is implemented and the requested gates pass.**

- **Layout:** Added the question headline, arm pills, four change cards, dual-arm tide gauge with day slider, zero-centred route-shift bars, and a 2×2 baseline/intervention/difference map grid with legends, signed parish differences, and attribution. The Compare footnote remains verbatim.
- **Behaviour and data:** Kept job loading and arm selection intact; `compareData.ts` is unchanged. Missing values remain unavailable, and identical demo arms display neutral differences.
- **Motion:** Baseline and intervention use their semantic line roles. Curves remount when their data changes, the second arm uses the existing 0.4-second delay, and averted/added areas fade in. Reduced motion displays the areas immediately.
- **Themes and tokens:** The view uses theme tokens; no hard-coded hex remains in Compare CSS or the `views.css` comparison section. The intervention legend uses the same token as its rendered line.
- **Gates:** `npm ci`, tests (15 passed, 6 skipped), typecheck, build, disclaimer greps, and `git diff --check` passed. The mock Vite root and Compare CSS module returned HTTP 200; the server was stopped afterward. Evidence is saved at [/tmp/jos-ui-u3-evidence.log](/tmp/jos-ui-u3-evidence.log).

I couldn’t do a rendered screenshot review because no browser binary is available here; theme support was checked in the token-based styles and the served module.

Files changed: [CompareView.tsx](/home/steven/jos-ui-u3-wt/frontend/src/views/compare/CompareView.tsx), [compare.css](/home/steven/jos-ui-u3-wt/frontend/src/views/compare/compare.css), [LineChart.tsx](/home/steven/jos-ui-u3-wt/frontend/src/components/LineChart.tsx), and [views.css](/home/steven/jos-ui-u3-wt/frontend/src/styles/views.css).

Diff: **4 files changed, 538 insertions, 301 deletions.** No commits or pushes.

**U5 note:** `LineChart`’s new `comparisonAreas` prop is optional and defaults off, so other views can keep using it unchanged.