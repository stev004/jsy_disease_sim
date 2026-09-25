# JOS UI redesign — "Harbour / Notebook" design system (spec)

**Status:** design authority for the 2026 UI redesign. Approved direction (Steven, 2026-09-25): Harbour becomes the dark theme and Field Notebook the light theme of one system, and Evidence is a new page. Pages must be cohesive. Mocks: https://claude.ai/artifact/Tav8SdSnyN8EMP1oCkXTNY (artboards Main/Harbour, Notebook, Evidence). This spec supersedes `docs/m10_ui_design.md` §11 (visual design) only. That document's information architecture, data semantics and API contract remain authoritative.

Author: Claude (Opus), director. It was written directly because the Fable taste seat was rate-limited, and it follows the approved mocks.

## 1. Principles

1. **Map-first and alive, but honest.** Motion shows only data the run actually published: day playback, fills changing and curves drawing in. Nothing is animated that implies data we don't have, such as fake progress, invented flows or synthetic particles.
2. **One vocabulary.** A colour means the same thing on every page and in both themes (§2.3). Cohesion comes from shared semantics, shared components and one type system, not from identical layouts.
3. **Uncertainty is shown as spread, never as confidence.** Bands are replicate quantiles, every disclaimer is verbatim (§8), and missing data is never drawn as zero.
4. **Research instrument, not a dashboard.** Numbers use tabular mono type, and the editorial serif is reserved for headlines and headline numbers.

## 2. Tokens

### 2.1 Themes and selection
- Dark = **Harbour**. Light = **Notebook**.
- The theme follows `prefers-color-scheme` by default. The explicit toggle keeps the existing `jos.theme` storage and `data-theme` attribute mechanism. With no preference and no stored choice, use **dark**.
- Keep the existing CSS-variable architecture in `frontend/src/styles/tokens.css`: `:root` = light, `@media (prefers-color-scheme: dark) :root:not([data-theme="light"])` = dark, and `:root[data-theme="dark"]` = dark. Keep every existing variable name so views keep working. The values below replace the old ones, and the new names are additions.

### 2.2 Surface and ink tokens

| Token | Notebook (light) | Harbour (dark) | Use |
|---|---|---|---|
| `--ground` | `#F3F0E8` | `#0B1215` | app ground |
| `--panel` | `#FBFAF6` | `#0F1D22` | raised surfaces, cards, map panel |
| `--panel-2` | `#EFEBE2` | `#13252B` | inset (bar tracks, inputs) |
| `--line` | `#E0DACC` | `#1C2B31` | hairlines |
| `--line-strong` | `#C9C2B3` | `#2A3B42` | control borders |
| `--ink` | `#1D2327` | `#E4ECEE` | primary text |
| `--ink-2` | `#4F5552` | `#B9C8CC` | secondary |
| `--ink-3` | `#6B6A63` | `#8FA3A9` | muted/captions (≥4.5:1 on panel) |
| `--ink-4` | `#8A877E` | `#5D737A` | non-text decoration only (axis ticks, attribution ≥10px) |
| `--water` | `#E7EEF1` | `#0F1D22` | map water |
| `--coast` | `#8FA6AE` | `#1E3A42` | coast/contour strokes |
| `--map-border` | `#FBFAF6` | `#0B1215` | parish hairlines |
| `--shadow` | `0 1px 2px rgba(29,35,39,.06), 0 8px 28px rgba(29,35,39,.07)` | `0 1px 2px rgba(0,0,0,.35), 0 10px 30px rgba(0,0,0,.35)` | |
| `--radius` / `--radius-lg` | `10px` / `14px` | same | |

Contrast (checked against `--panel`): `--ink` ≥ 14:1, `--ink-2` ≥ 7:1, and `--ink-3` ≥ 4.6:1 in both themes. `--ink-4` must never carry body text.

### 2.3 The shared semantic vocabulary (the cohesion contract)

| Role | Meaning everywhere | Notebook | Harbour |
|---|---|---|---|
| **System accent** (`--accent`, `--accent-ink`, `--accent-soft`, `--on-accent`) | interface: nav selection, primary buttons, focus ring, links, running state, provenance chain | `#1B6670` / `#0F474E` / `#DDEEEF` / `#FFFFFF` | `#7CC7CF` / `#A9E0E6` / `#16323A` / `#0B1215` |
| **Infection magnitude** (`--seq0..--seq5`, 6 bins, lightness-monotone toward salience) | maps, epidemic curve, band, day cursor | `#F4EDE4 #F2D3B0 #E9A866 #D9773A #B24A26 #7A2A18` (darker = more) | `#1A2A30 #3A3326 #7A5A2E #B98A3A #EFB85C #FFE3A3` (brighter = more) |
| **Infection line** (`--epi`, `--epi-soft`) | the median curve and its band | `#B24A26`, band `rgba(178,74,38,.14)` | `#EFB85C`, band `rgba(239,184,92,.16)` |
| **Comparison: fewer** (`--div-neg`, `--div-neg-soft`) | intervention minus baseline < 0; the intervention arm line | `#1F5E8C`, `#AFC0CC` | `#5EA3D6`, `#1E3A55` |
| **Comparison: more** (`--div-pos`, `--div-pos-soft`) | intervention minus baseline > 0 | `#C9651F`, `#F1D5BD` | `#F0A35E`, `#4A3120` |
| **Comparison: same** (`--div-mid`) | ≈0 | `#EFEBE2` | `#1A2A30` |
| **Baseline line** (`--base-line`) | the baseline arm in comparisons | `--ink` | `--ink-2` |
| **Verification** (`--good`, `--bad`, `--warn` and `-soft`) | pass/fail/warn states ONLY (gates, hashes, job outcome) | `#2E6B45`/`#DCEFE3`, `#B3261E`/`#F6E1DE`, `#8A6116`/`#F5EBD6` | `#6FCF97`/`#173325`, `#F2877F`/`#3D2220`, `#E0B45A`/`#3A2F17` |
| **Intervention window** (`--hatch`) | days an intervention is active (hatch pattern) | `#D6CFBF` | `#2F4750` |
| **Intervention families** (`--iv-*`) | chips, timeline bars and legend swatches only, never map fills | keep the existing hues; darken any below 3:1 on `--panel` | keep the existing dark values |

Rules:
- Amber/ember never means "interface". Teal never encodes data magnitude. Green/red never encode epidemiology.
- Diverging blue/orange differ in lightness as well as hue, so they stay colour-blind safe.
- Sequential maps show a 6-swatch legend labelled "fewer → more" plus the metric name and unit.

## 3. Typography

- **Display:** *Newsreader* (Google Fonts, opsz 6..72, weights 400/600) in both themes. Use it only for page headlines, headline numbers in change cards and the gate verdict, and the section titles of the Compare and Evidence narrative. Fraunces is dropped.
- **UI:** *Instrument Sans* 400/500/600/700, unchanged.
- **Numerals and data:** *IBM Plex Mono* 400/500 for all numbers, dates, hashes and axes, with `font-variant-numeric: tabular-nums`.
- **Scale (px):** 11 caption, 12 meta, 13 control, 14 body (base), 16 lead, 22 section, 26 tile value (mono), 40 headline number (Newsreader), 44 page headline (Newsreader). Line-height 1.45 for body and 1.1 for display.
- **Eyebrow labels:** 12px, uppercase, letter-spacing .14em, `--ink-3` or `--accent` (dark).

## 4. Shell and layout

- **One 64px top bar replaces the 56px bar and the 76px rail on every page.**
  - Left: the JOS mark (ring + dot in `--accent`), "JOS", and "Jersey Outbreak Simulator" in `--ink-3`.
  - Centre-left: primary nav tabs **Home · Simulate · Results · Compare · Runs & evidence**. The active tab uses `--accent` as a pill fill (dark) or a 2px underline (light), the rest `--ink-2`. Targets are at least 44px tall.
  - Right: the disclaimer pill "Synthetic research simulation — not a forecast" (verbatim), the Demo data chip (mock mode only; `--accent` fill), the current scenario chip with its kind and job-state chip, the Simple/Scientific segmented toggle, the Theme toggle (icon button with `aria-label`), the Model info button (opens the drawer) and a **New scenario** primary button.
  - Below 1440px the scenario chip collapses into a menu before anything else does.
- **Routes are unchanged:** `/`, `/simulate`, `/results[/:jobId]`, `/compare[/:jobId]`, `/runs`. The `/runs` nav label becomes "Runs & evidence".
- **Page padding** is 28px on the sides and 22px at the top. The content max width is unconstrained, and the minimum width stays 1180px.
- The Simple/Scientific toggle and its `.sci-only` behaviour are unchanged.
- Keyboard shortcuts are unchanged; `?` opens the overlay.

## 5. Components

- **Panel:** `--panel` fill, 1px `--line` border, `--radius-lg`, no shadow on dark and `--shadow` on light.
- **Metric tile:** a caption label (12px `--ink-3`), a value (26px mono `--ink`) and a sub line (11px `--ink-3`, e.g. "range a–b" or "3-day reporting lag"). A missing value shows "—" plus a tooltip with the availability note, never 0.
- **Chip/pill:** 999px radius, 12px text, 6–10px padding. Variants: neutral (`--line-strong` border), accent, and state (`--good/-bad/-warn` soft fill with strong ink). Job states use the existing labels.
- **Segmented toggle / metric buttons:** 44px-min pills. Selected = `--accent` fill + `--on-accent`; unselected = transparent + `--line-strong` border.
- **Buttons:** primary (`--accent` fill), secondary (border), ghost. Every icon-only button has an `aria-label`. The focus ring is 2px `--accent` with a 2px offset.
- **Map (`JerseyMap`):** water panel with 3 faint concentric coast contours (`--coast`), parish fills from `--seq*` bins, parish borders `--map-border` 1.2px, and labels 11px with a 3px paint-order halo in `--ground`.
  - Legend: bottom-left, 6 swatches plus the metric name.
  - Attribution: bottom-right, verbatim.
  - **Pulse:** a two-ring ripple in `--seq5` on the parish with the highest *new infections on the current day* (from `ParishPoint.newInfections`). There is no pulse when that value is 0 or unavailable.
  - The died-out banner is kept, verbatim.
- **Epidemic curve ("tide gauge", `LineChart`):**
  - Median line `--epi` 2.2px, and replicate band `--epi-soft` between `bandLow`/`bandHigh` (single-seed runs draw no band and show the single-seed note).
  - Intervention windows as `--hatch` 45° hatch behind the data, with the family colour as a thin 3px strip at the top.
  - Day cursor: 1px `--seq5` line plus a 5px dot on the median.
  - Axis labels mono 11px `--ink-4`.
  - Dual-arm mode (Compare): baseline `--base-line` 2px, intervention `--div-neg` 2.4px, and the area where the intervention is below the baseline shaded `--div-neg` at .14 and labelled "infections averted (simulated)" in italic Newsreader. The area above is shaded `--div-pos` at .14 and labelled "added (simulated)".
- **Ranked bars (`HBar`):** a 10px track `--panel-2`. The first bar is `--epi`, the rest `--accent` at 70% (dark) or `--ink-2` (light). Values are mono and right-aligned.
- **Route-shift diverging bars:** a centre rule `--ink`, negative bars `--div-neg` to the left and positive `--div-pos` to the right, with values signed using the true minus sign "−".
- **Change card (Compare):** a 2px `--ink` top rule, a 13px `--ink-3` label, a 40px Newsreader value (colour `--div-neg` or `--div-pos` by sign, `--ink` when neutral) and a mono sub line.
- **Job phase pipeline:** a vertical list of the real phases (queued → validating → preparing → running → writing_artifacts → verifying → finalizing).
  - Each row has a 20px node: done = `--accent` fill with a check; current = `--accent` ring with a pulse; pending = `--line-strong` ring.
  - Labels come from `jobText.ts` `PHASE_LINES`, with the mono phase code on the right.
  - The verbatim note "Phases are real checkpoints…" sits beneath. No percentage is shown.
- **Provenance hash chain:** a horizontal line of nodes joined by a dashed `--accent` connector (flow animation). Each node is a 44px button showing a label and a short hash (first 8 … last 4). Clicking copies the full hash, and a toast confirms.
  - Node sources for a job: `scenario_hash`, `latent_hash`, `bundle_hash`, `result_manifest_hash` and `engine_git_commit`, followed by the `verification_status` chip.
  - A null value renders "not published" in `--ink-3`, never a placeholder hash.
- **Validation-gate card:** an eyebrow, a Newsreader verdict (PASS in `--good`, FAIL in `--bad`, NOT RUN in `--ink-3`), one plain-language sentence and per-arm mini-panels. The data comes from the static content file (§7.5).
- **Drawer:** a right-hand sheet, `--panel`, 440px wide, with the existing provenance content restyled with these tokens.

## 6. Motion

| What | How | Duration / easing |
|---|---|---|
| Day playback | existing play/scrub; the map and cursor update per day | default 500 ms/day |
| Map fill change | `transition: fill` | 450 ms ease |
| Bar width change | `transition: width` | 450 ms ease |
| Curve draw-in | `stroke-dasharray`/`dashoffset`, once per data load (not on every day tick) | 1.4 s ease-out; second arm delayed 0.4 s |
| Averted/added area | fade in after the draw-in | 1.0 s, delay 1.2 s |
| Seed-parish pulse | two rings, `r` 6→46, opacity .75→0, staggered 1.3 s | 2.6 s ease-out, infinite while playing, one static ring when paused |
| Pipeline current node | box-shadow pulse | 1.6 s ease-in-out |
| Hash-chain connector | dashed `stroke-dashoffset` flow | 1.1 s linear; runs only while the job is RUNNING, otherwise static |
| Page/view entry | none | — |

`@media (prefers-reduced-motion: reduce)`: disable every keyframe animation and transition, and draw curves immediately. Playback still advances days, just without transitions.

## 7. Pages

### 7.1 Home
- **Hero:** a Newsreader headline and the population line, over a full-width static parish map in the current theme (no pulse; sequential fill off, neutral land).
- **Controls:** the primary New scenario button, plus Open last results and Browse templates.
- **Content:** the three step cards restyled as panels, then Recent runs (`listJobs({limit:5})`) as chip rows.
- **Footer:** the disclaimer, "No real people are modelled." and the attribution, all verbatim.

### 7.2 Simulate
- The builder logic, fields, validation and `submitJob` flow are unchanged.
- Visuals: two columns. Left: templates as pill chips and form cards (panels). Right: the sticky summary panel with mono values, the scenario-hash chip in Scientific mode, and the primary "Run simulation" button.
- Interventions render as a **timeline composer** preview: horizontal lanes per intervention, bars coloured by `--iv-*` family over the duration axis, reusing the existing `interventions.ts` timeline builder. It is display-only; editing stays in the cards.

### 7.3 Results (Harbour layout)
- The page header is the eyebrow (scenario · kind · population), then the headline "Day NN" (mono numerals in `--seq5`/`--epi`) and the date in `--ink-3`, with the map-metric pills on the right.
- **Main column:** the map panel (flex-grow) with its legend, attribution, a "Playing/Paused" indicator and the died-out banner, then the tide-gauge panel (≈196px): play/pause icon button (44px circle), title, legend line, day slider (existing), curve and the date-range footer.
- **Right rail (420px):**
  - the 2×2 metric tiles (Active infectious with replicate range, Cumulative, Detected, Ever infected %);
  - "What's driving transmission" (top routes, day window), or the parish detail when a parish is selected;
  - "Parishes by ever-infected share" (top 6);
  - the ensemble/single-seed disclaimer (verbatim).
- The existing tabs band (Epidemic curve / Transmission routes / Ages / Travel / Interventions) moves **below the fold** and is reached by scrolling. Its charts adopt the new components, and the exports are kept.
- Layers, parish selection and keyboard behaviour are unchanged.

### 7.4 Compare (Notebook layout)
- **Header:** eyebrow ("Scenario comparison · matched seeds ×N · population"), a Newsreader question-style headline built from the arm names ("What changes with <intervention name>?"), and the Baseline pill (neutral) vs the Intervention pill (`--div-neg` fill).
- **Row 1:** four change cards (Cumulative infections, Peak active infectious, Peak date shift, Ever infected), using the existing `compareData.ts` builders.
- **Row 2, left (560px):** the dual-arm tide gauge with the averted/added areas and a day slider, then the route-shift diverging bars.
- **Row 2, right:** a 2×2 grid of Baseline map, Intervention map and Difference map (diverging scale), plus a legend/explanation cell with the attribution.
- **Footer:** the Compare disclaimer, verbatim. The "Intervention burden" list is kept in Scientific mode.

### 7.5 Runs & evidence (new page at `/runs`)
- **Left column (400px):** the **live job** panel (the selected or most recent active job: name, state chip, phase pipeline and the verbatim note), then **Recent runs** with filters (All/Active/Succeeded/Failed as a segmented toggle) and rows (state chip, name + meta, action link: Open results / Open comparison / View status / View error / Cancel / Re-run). The existing toasts are unchanged.
- **Right column:**
  1. **Provenance** for the selected job: the hash chain (§5), the artifacts list (`GET /jobs/{id}/artifacts`: role, type, id, verification chip, size) and engine/API contract lines.
  2. **Model validation** card(s) from `frontend/src/content/validation.ts`. This is a static, versioned, hand-maintained module exporting `{asOf, gates:[{id, title, verdict:'PASS'|'FAIL'|'NOT RUN', summary, arms:[…], citations:[repo-relative paths]}]}` and rendered with an "as of <date>" label and the citation paths. Initial content:
     - Gate "V1.3 Phase 0 — synthetic recovery", verdict FAIL (2026-09-24). Summary: the inoculation-day estimate hit a grid edge for 2 of 5 targets (limit 1); P0-2 detection PASS (10/10); P0-3 NON_IDENTIFIED_STRUCTURAL PASS. Citations: `docs/audits/2026-09-24-phase0-exit-audit-sol-FAIL.md`.
     - Gate "V1.3 Phase 0b", verdict NOT RUN, citing `docs/research/v1_3/2026-09-25-phase0b-predeclaration.md`.
     - A one-line note: "No real Jersey data are fitted until a Phase-0 gate passes."
     - The card must never read like live or automated data.

### 7.6 Provenance drawer
The content and verbatim disclaimer are unchanged, restyled with the tokens. The badges keep their meanings.

## 8. Hard constraints (every unit)

- **Dependencies:** no new runtime dependencies; SVG stays hand-drawn. Fonts load from Google Fonts in `index.html`: Newsreader, Instrument Sans, IBM Plex Mono.
- **Exports and behaviour:** keep every exported symbol and behaviour the tests import. That means `request.ts` (`buildScenario`, `buildRequest`, `travelConfig`), `SimulateView.isSupportedStartDate`, the builders in `data.ts`, `compareData.ts` and `interventions.ts`, and `jobText.ts` (`stateNote`, `failedPhaseName`). `npm test`, `npm run typecheck` and `npm run build` must all pass.
- **Disclaimers stay byte-identical:**
  - "Synthetic research simulation — not a forecast"
  - the drawer's synthetic-simulation paragraph
  - the ensemble/single-seed notes
  - the band notes
  - the Compare footnote
  - "Phases are real checkpoints from the engine — it does not report a percentage, so none is shown."
  - "No real people are modelled."
  - the died-out note
  - "Risk strata are targeting metadata — no clinical severity is modelled"
  - "Map data © OpenStreetMap contributors, ODbL"

  A grep for each must still hit.
- **Data honesty:** missing data is never drawn as 0, and bands are never called confidence intervals. The demo chip appears only in mock mode (`VITE_JOS_MOCK=1`).
- **Accessibility:** real `<button>`/`<a>`/`<input>` with labels; focus visible; 44px targets; text contrast as in §2.2; colour is never the only encoding (chips carry text; diverging maps carry a legend and signed values in tooltips).

## 9. Implementation units (dependency order)

- **U1 — Tokens, shell, shared components.** Files: `styles/tokens.css`, `styles/base.css`, `index.html` (fonts), `app/AppShell.tsx` (top bar replaces the rail), `components/*.tsx`, and a new `styles/motion.css`. The views must still render; only their layout CSS may need minimal fixes.
  - Acceptance: typecheck, test and build pass; the disclaimer greps pass; the `--seq0..5`, `--epi`, `--div-*` and `--accent` tokens exist in both themes; the reduced-motion block exists.
  - Visual check (director, browser, `VITE_JOS_MOCK=1`): every page renders in both themes with the new bar.
- **U2 — Results (Harbour).** Files: `views/results/*` (not `data.ts` semantics), `components/JerseyMap.tsx` / `LineChart.tsx` additions if needed.
  - Acceptance: the same gates; the pulse is driven by `newInfections`; the tabs band is still reachable; the exports still work.
  - Visual: playback animates fills and the cursor; the single-seed and ensemble notes render.
- **U3 — Compare (Notebook).** Files: `views/compare/*` and dual-arm support in `LineChart`.
  - Acceptance: the gates plus the Compare footnote grep; the difference map uses the `--div-*` tokens.
- **U4 — Runs & evidence.** Files: `views/runs/*`, the new `content/validation.ts`, the new provenance-chain component, the nav label.
  - Acceptance: the gates; the pipeline uses `PHASE_LINES`; the chain shows "not published" for null hashes; the validation card shows "as of" and its citations; the copy-hash toast works.
- **U5 — Home, Simulate, drawer polish.** Files: `views/home/*`, `views/simulate/*` (visual only; builder logic untouched), `views/drawer/*`.
  - Acceptance: the gates and `isSupportedStartDate` unchanged; the timeline preview reuses the existing builder.

Each unit is a gpt-6-luna @ xhigh brief in its own worktree off the previous accepted unit, followed by director review (full diff plus a browser check in both themes with `VITE_JOS_MOCK=1`), a clean-clone frontend mirror (`npm ci && npm test && npm run typecheck && npm run build`) and a gpt-6-sol review for U1 and U4, then a push. Merges to `main` are Steven's call.
