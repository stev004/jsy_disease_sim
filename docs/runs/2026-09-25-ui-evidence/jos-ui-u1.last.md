**PARTIAL — the U1 changes and frontend gates pass; one theme fallback remains outside the allowed files.**

`ThemeProvider.tsx` still treats a non-dark `prefers-color-scheme` result as light. Because that file wasn’t in the edit allowlist, the requested dark default when no system preference is reported is not encoded.

### Acceptance evidence

- **Tokens:** the required spec tokens are defined in all three theme blocks, with three declarations each. The light and Harbour values match the spec; no `--seq*`, `--epi` or `--div-*` token equals the accent.
- **Shell:** the rail is removed and every route uses the 64px top bar. The five required nav labels, active states, mock-only Demo chip, scenario menu below 1440px, detail toggle, labelled theme icon, Model info and New scenario are present. Nav targets are at least 44px, focus rings are visible, and the 1180px minimum width remains.
- **Fonts and components:** Newsreader, Instrument Sans and IBM Plex Mono are loaded. Shared components use the token palette; JerseyMap has three coast contours and optional pulse props, while LineChart has additive hatch-window support and a median cursor dot. No hard-coded hex or RGB colors were found in component files.
- **Motion:** `motion.css` contains the specified transitions and keyframes, plus reduced-motion rules that disable animation and transitions and draw curves immediately.
- **Disclaimer greps:** under `frontend/src`, the claim boundary, drawer paragraph, ensemble and single-seed notes, band-note fragments, Compare footnote, full multiline phase note, “No real people”, died-out notice, risk-strata note and OSM attribution all matched. Each checked phrase or fragment matched once; the full multiline drawer, phase and Compare body matches also counted once.

### Gates

`npm ci` first hit a read-only default cache (`EROFS`); `npm ci --cache /tmp/jos-ui-u1-npm-cache` then succeeded, adding 111 packages. It reported 7 audit findings.

- `npm run typecheck` — exit 0
- `npm test` — 15 passed, 6 skipped
- `npm run build` — exit 0; Vite transformed 81 modules
- `git diff --check` — exit 0

The command output is saved in [`/tmp/jos-ui-u1-evidence.log`](/tmp/jos-ui-u1-evidence.log).

### Files and tokens

Changed the allowed frontend files: [`index.html`](/home/steven/jos-ui-u1-wt/frontend/index.html), [`AppShell.tsx`](/home/steven/jos-ui-u1-wt/frontend/src/app/AppShell.tsx), shared components, [`base.css`](/home/steven/jos-ui-u1-wt/frontend/src/styles/base.css), [`tokens.css`](/home/steven/jos-ui-u1-wt/frontend/src/styles/tokens.css), and new [`motion.css`](/home/steven/jos-ui-u1-wt/frontend/src/styles/motion.css). No views, tests, package files or files outside `frontend/` were changed.

Added tokens: `--ink-4`, `--seq5`, `--epi`, `--epi-soft`, `--base-line`, `--hatch` and `--radius-lg`. Updated the surface, ink, accent, map, status, sequential, diverging, shadow, radius and intervention-family values; legacy `--band` now aliases `--epi-soft`.

`git diff --stat` reports 9 tracked files, 472 insertions and 274 deletions; the new motion file adds 55 lines. The branch remains `ui/u1-foundation` at `1f5c347c2c64093aba2ffe2f33874051c9e3e4e8`; no commit was made.

### Follow-up for later units

- U2: `seqColor` in [`geometry.ts`](/home/steven/jos-ui-u1-wt/frontend/src/map/geometry.ts:67) still selects five bins (`--seq0..4`). It contains no hard-coded color values. Results also has export fallback hex colors in [`exporters.ts`](/home/steven/jos-ui-u1-wt/frontend/src/views/results/exporters.ts:84), a white hatch color in [`results.css`](/home/steven/jos-ui-u1-wt/frontend/src/views/results/results.css:46), and a 140ms playback interval in [`ResultsView.tsx`](/home/steven/jos-ui-u1-wt/frontend/src/views/results/ResultsView.tsx:45), versus the spec’s 500ms/day.
- U3: [`views.css`](/home/steven/jos-ui-u1-wt/frontend/src/styles/views.css:159) still has a dark-mode `#7FB1EE` comparison color.
- U4: the existing completed-phase node still uses verification green in [`views.css`](/home/steven/jos-ui-u1-wt/frontend/src/styles/views.css:64); the spec calls for the accent.