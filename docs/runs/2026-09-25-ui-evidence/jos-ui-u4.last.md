**PASS — U4 implemented** on `ui/u4-evidence`, based on `7d5b0dec43c87adb87380c68f13280015e12194f`. No commit or push.

- **Layout and content:** Added the 400px live-job and recent-runs column, plus provenance, artifact details, engine/API contract lines, and static validation cards. Phase labels use `PHASE_LINES`; filters and existing run actions are present.
- **Existing behavior:** Retained 2-second polling while jobs are active, finish/fail toasts, cancellation, error display, and job selection via `?job=`. `jobText.ts` and its `stateNote` / `failedPhaseName` behavior are unchanged.
- **Motion:** Current pipeline nodes pulse; hash connectors flow only for a `RUNNING` job. The shared reduced-motion rules apply.
- **Accessibility and themes:** Copy controls are real labeled buttons with 44px-minimum targets. Styling uses theme tokens. Disclaimer-string checks matched, and `git diff --check` passed.
- **Verification:** `npm ci --cache /tmp/jos-ui-u4-npm`, `npm test`, `npm run typecheck`, and `npm run build` all passed. Tests: 15 passed, 6 skipped. Full output: [/tmp/jos-ui-u4-evidence.log](/tmp/jos-ui-u4-evidence.log). A visual browser check was not run; no local browser or Playwright was available.
- **Artifacts API:** The client exposes `getJobArtifacts`; the page renders returned role/type/id/verification/size records and reports the job’s artifact count when details are unavailable.

Changed files: [RunsView.tsx](/home/steven/jos-ui-u4-wt/frontend/src/views/runs/RunsView.tsx), [runs.css](/home/steven/jos-ui-u4-wt/frontend/src/views/runs/runs.css), [ProvenanceChain.tsx](/home/steven/jos-ui-u4-wt/frontend/src/components/ProvenanceChain.tsx), [components/index.ts](/home/steven/jos-ui-u4-wt/frontend/src/components/index.ts), [validation.ts](/home/steven/jos-ui-u4-wt/frontend/src/content/validation.ts), and [views.css](/home/steven/jos-ui-u4-wt/frontend/src/styles/views.css).

Diff stat including new files: **6 files changed, 1,215 insertions, 131 deletions**.