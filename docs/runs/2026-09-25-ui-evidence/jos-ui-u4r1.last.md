**PASS — all four review findings are fixed.** The requested frontend gates pass.

- **Validation arms:** Added the specified Phase 0 results and four Phase 0b `NOT RUN` arms, with verdict colors. The as-of date, citations, and note are unchanged. [validation.ts](/home/steven/jos-ui-u4-wt/frontend/src/content/validation.ts), [RunsView.tsx](/home/steven/jos-ui-u4-wt/frontend/src/views/runs/RunsView.tsx), [runs.css](/home/steven/jos-ui-u4-wt/frontend/src/views/runs/runs.css)
- **Recent runs:** Succeeded and Failed request up to 100 jobs for their selected state. Active remains locally filtered, as it was before U4. The live panel continues using the unfiltered latest list. [RunsView.tsx](/home/steven/jos-ui-u4-wt/frontend/src/views/runs/RunsView.tsx)
- **Provenance layout:** Reduced nodes to 128px and let the chain wrap, removing its horizontal scroll behavior. [runs.css](/home/steven/jos-ui-u4-wt/frontend/src/views/runs/runs.css)
- **Connectors:** Dashes now persist in every state; flow animation remains RUNNING-only. [motion.css](/home/steven/jos-ui-u4-wt/frontend/src/styles/motion.css)

**Gates:** typecheck passed; tests passed (15 passed, 6 skipped); build passed; `git diff --check` passed. Full output is saved in [/tmp/jos-ui-u4r1-evidence.log](/tmp/jos-ui-u4r1-evidence.log).

**Diff stat:** 4 files changed, 135 insertions, 18 deletions. Branch and HEAD remain `ui/u4-evidence` at `6dec41063930c5018e8336cd1383917743ab2a87`; only the four authorized files are modified. No commit or push.