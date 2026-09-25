UI U4 REVIEW: BLOCKED

**Blocking findings**

- **Medium — validation arm panels are absent.** [validation.ts](/home/steven/jos-ui-u4-review-readonly/frontend/src/content/validation.ts:27) supplies no `arms` for either gate, so the conditional renderer in [RunsView.tsx](/home/steven/jos-ui-u4-review-readonly/frontend/src/views/runs/RunsView.tsx:630) never shows the per-arm mini-panels required by §5. Populate them from the cited audit and predeclaration, using NOT RUN for Phase 0b arms.
- **Medium — Succeeded and Failed filters lose older runs.** [RunsView.tsx](/home/steven/jos-ui-u4-review-readonly/frontend/src/views/runs/RunsView.tsx:112) fetches only the latest 100 jobs, then filters that subset locally. The previous view requested up to 100 jobs *per selected state*, so older matching runs disappear after 100 total jobs. Restore state-filtered API requests for those filters while retaining the unfiltered list for the live panel.

**Other findings**

- **Low — the chain scrolls horizontally at 1440px.** Five fixed 138px nodes, four 28px links, and the verification chip exceed the panel’s roughly 934px inner width ([runs.css](/home/steven/jos-ui-u4-review-readonly/frontend/src/views/runs/runs.css:372)). This is a layout defect, not an evidence-integrity issue. Reducing the five node widths to about 128px is the smallest fix for 1440px.
- **Low — idle connectors become solid.** The dash pattern is applied only with `.running` in [motion.css](/home/steven/jos-ui-u4-review-readonly/frontend/src/styles/motion.css:16). Keep the connector dashed in all states and apply only the flow animation while RUNNING.

The review found no fabricated hashes: null values display “not published.” The validation section identifies itself as static and hand-maintained, shows its as-of date, and both citation paths exist. Polling is limited to active jobs; copy feedback, reduced-motion handling, phase text, and the verbatim phase note are present. The supplied frontend mirror reports 15 tests passed, typecheck passed, and build passed; I did not rerun it.

Final SHA: `6dec41063930c5018e8336cd1383917743ab2a87`. The base is an ancestor, and `git status --porcelain=v1 -uall` was empty. No files were changed.