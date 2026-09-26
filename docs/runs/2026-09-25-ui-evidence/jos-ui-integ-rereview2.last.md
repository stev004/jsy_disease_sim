UI INTEGRATION RE-REVIEW 2: BLOCKED

**Finding — H1 remains open.** Compare now derives its line, band, and area legends from the marks it draws. The two Results legends still check band points independently of line points: [TabsBand.tsx](/home/steven/jos-ui-integ-rereview2-readonly/frontend/src/views/results/TabsBand.tsx:335) and [ResultsView.tsx](/home/steven/jos-ui-integ-rereview2-readonly/frontend/src/views/results/ResultsView.tsx:507). With one line point and two band points, [LineChart](/home/steven/jos-ui-integ-rereview2-readonly/frontend/src/components/LineChart.tsx:94) draws neither mark, while either Results legend shows “Replicate range.” This fails the amended requirement that every legend reflect rendered series.

| Item | Decision |
|---|---|
| H1; U1 finding 1 | **Open** on Results legend accuracy. Roles are present on every `LineChart` series; Compare’s legends are corrected. |
| H2 | Closed: visible bars and PNG export use the same resolver, including panel-local first-row opacity. |
| M1 | Closed: null age has no bar; zero has a zero-width bar. |
| M2 | Closed: difference-map tooltips retain the signed parish count, use `−`, and say unavailable when counts are missing. |
| M3 | Closed: the named controls have 44px targets. |
| L1–L3 | Closed: I checked the `--accent` inventory; teal is used for interface elements, infection bars use ember, and died-out styling is neutral. |
| U2 findings 2 / 4 / 5 | Closed / closed / closed. |

The supplied [mirror log](/home/steven/jos-ui-integfix2-mirror.log) records 15 passed, 6 skipped, with typecheck and build passing; I did not rerun it. The corrective diff changes two files (58 insertions, 18 deletions), and `git diff --check` passed. Final SHA: `1460f2e988d13216283e5c496c6846e024e2a527`. `git status --porcelain` was empty; no clone files were edited.