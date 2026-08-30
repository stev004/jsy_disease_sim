# M10 interactive application — UI/UX design

Status: design specification (no frontend implementation). Verified backend
baseline: `93b316a` (M9.2). Interactive mockup:
<https://claude.ai/code/artifact/bbcad36a-b4bf-4936-a6a3-d5bf84a359b1>
(source snapshot kept alongside the design session; the mockup uses
deterministic fake data and no backend).

Design objective: **make a complex epidemiological simulator feel simple,
clear, visual, and easy to use.** The engine is sophisticated; the interface
must not feel sophisticated to operate. Every screen answers one of five user
questions: *define a scenario → run it → watch what happens → understand why →
compare it with another scenario.*

---

## 1. Product information architecture

Three primary destinations plus one modal work surface:

| Destination | Purpose | Backing API |
| --- | --- | --- |
| **Home** | First-run orientation: see Jersey, start a scenario, reopen recent results | `GET /jobs` (recent), `GET /capabilities` |
| **Simulate** (scenario builder) | Define/edit a scenario; validate continuously; submit | `POST /scenarios/validate`, `POST /jobs` |
| **Results** (workspace) | Explore one succeeded run: map, time, curves, routes, ages, travel, interventions | `GET /jobs/{id}/datasets/*` |
| **Compare** | Matched baseline-vs-treated deltas | `scenario_compare` job datasets (`matched_seed_comparison`, per-arm tables) |
| **Runs** | Job history, live status, cancellation, error inspection | `GET /jobs`, `GET /jobs/{id}`, `/events`, `/cancel` |
| **Assumptions & sources** (drawer, global) | Provenance, hashes, verification, claim boundary | `GET /jobs/{id}` + `/artifacts` + `GET /capabilities` |

Everything else (parish detail, route attribution, travel analysis,
intervention timeline, job monitor) is a *state* inside these surfaces, not a
page. Total primary navigation: 5 rail items + the Model drawer.

## 2. Core navigation

- **Left icon rail (76 px)**: Home, Simulate, Results, Compare, Runs; bottom
  anchor "Model" opens the provenance drawer. Labels always visible (no
  icon-only mystery meat).
- **Top bar (56 px)**: product mark + permanent one-line claim boundary
  ("Synthetic research simulation — not a forecast"); current scenario context
  (name, run kind, state chip); global actions (Model info, Compare, New
  scenario).
- **Right context panel** and **drawer** carry detail; the center is always the
  main visual (map or form). Navigation cost is one click between any two core
  activities.

## 3. Main screen layouts

### Results workspace (default composition, 1440 px)

```text
┌────────────────────────────────────────────────────────────────────┐
│ topbar: scenario · kind · state          Model info  Compare  New  │
├──────┬─────────┬───────────────────────────────┬───────────────────┤
│ rail │ metric  │                               │ 4 headline metrics│
│      │ picker  │        JERSEY MAP             │ (with ranges)     │
│      │ layers  │   parish choropleth + legend  │ drivers panel OR  │
│      │         │                               │ parish detail     │
│      ├─────────┴───────────────────────────────┤                   │
│      │ ◀ ▶ ▶  Day 34 · 9 Feb  ━━━●━━━━━━━━━━  │                   │
│      │ intervention strip under the scrubber   │                   │
│      ├─────────────────────────────────────────┴───────────────────┤
│      │ tabs: Epidemic curve · Routes · Ages · Travel · Interventions│
│      │ [active tab content]                                        │
└──────┴──────────────────────────────────────────────────────────────┘
```

The map is the largest element on screen at all times; charts live in one
tabbed band, never stacked simultaneously.

### Scenario builder
Single centered column of six cards (Name, Population, Disease, Initial
outbreak & duration, Interventions, Travel, Uncertainty) + a sticky right
summary rail with live validation, scenario hash, and the **Run simulation**
CTA. No page-level tabs; no giant form.

### Job monitor
One centered card: state chip, elapsed time, seven-phase checklist, honesty
note, Cancel / Open results.

### Compare
Delta cards row → paired curve + route shifts (left) and comparison map +
burden card (right) → claim-boundary footnote.

### Runs
Filter chips + one card of rows (state chip, name, kind, meta line, actions).

## 4. Scenario-builder interaction model

**Progressive disclosure in three tiers:**

1. **Tier 0 (visible, ~5 decisions)**: name, population preset (Full
   104,540 / Scaled 15,000 / Quick test 3,000 — from
   `capabilities.population_presets`), fixed disease chip, "Start with N
   infections on DATE", duration slider, Run.
2. **Tier 1 (opt-in cards)**: intervention cards via "+ Add intervention"
   picker (the 9 M7 families + travel measures, each with a one-line plain
   description); Travel segmented Default / Off / Custom (maps to
   `TravelConfig.mode`); Uncertainty segmented Single run / Ensemble (maps to
   job kind + `replicate_seeds`).
3. **Tier 2 (`Advanced` disclosure per card)**: real engine parameters —
   β, latent/infectious/immunity periods, import schedule, per-route
   multipliers (11 resident + 7 travel), observation model, explicit seeds.
   Every advanced value carries its provenance badge inline.

**Template picker**: the builder opens with a single compact "Start from"
chip row — nine templates derived from the repository's demo configs
(`configs/scenarios/`, `configs/travel/`): blank, winter baseline, school
closure, isolation + quarantine, working from home, community reduction,
care-home protection, vaccination campaign, and high-season travel with
arrival testing. Selecting a chip pre-fills the scenario (name, intervention
cards, travel mode) and shows the template's one-line description beneath the
row; everything stays editable, values are synthetic demo assumptions, and
scientific mode appends the source config filename. Deliberately chips, not
a tile gallery — one glance, zero learning curve, no wall of choices before
the form. Home links here via a "Browse templates" action.

**Simple / Scientific switch** (global, top bar, persisted per user): one
control that moves the whole application between two detail levels without
changing layout or navigation.

- *Simple* (default): human concepts only — friendly parameter names,
  rounded values, provenance badges, no hashes or engine identifiers.
- *Scientific*: additive, never a different UI. Advanced disclosures open
  automatically; parameters gain their engine field names, exact values,
  distributions and valid ranges (`beta = 0.08 · fixed · valid [0, 1]`);
  intervention cards show their composed route multipliers and lifecycle
  rules; the builder summary shows mode, explicit seed list and engine
  identity; headline metrics gain a replicate-quantile definition note;
  route charts append canonical route IDs; the results workspace gains a
  scenario/latent/bundle-hash and dataset provenance strip; the job monitor
  shows request hash, idempotency key and worker PID.

Everything scientific-mode reveals is one toggle away, so the default
experience stays clean while a scientist never has to leave the workspace to
see the exact contract values.

**Intervention cards** show only human concepts on their face (Start,
Duration, Strength, Scope, Adherence); route multipliers appear only inside
the card's Edit → Advanced. Detection-triggered families (case isolation,
household quarantine) show "Trigger: on detection" instead of a start date,
mirroring `ActivationRule`.

**Continuous validation**: every edit debounces into
`POST /api/v1/scenarios/validate`; the summary rail shows "Scenario valid ✓"
plus the returned `scenario_config_hash`, or inline errors anchored to the
offending card (the endpoint's error paths map onto card fields). Run is
disabled only while invalid. Submitting uses an `Idempotency-Key` so a
double-click cannot create duplicate jobs.

## 5. Results-workspace interaction model

- **Time is the master control.** One scrubber (play / pause / step / slider,
  plus ← → and space keyboard bindings) drives every synchronized surface:
  map fills, headline metrics, "what's driving transmission" panel, epicurve
  day marker, intervention-timeline cursor, travel stats. An intervention
  strip sits directly under the slider so cause and time never separate.
- **Map metric picker** (left): Active infectious, Cumulative, Detected,
  Attack rate, Visitor-linked — each a `daily_parish`/travel dataset column,
  normalized per 1,000 residents where applicable.
- **Parish selection**: click (or keyboard-activate) a parish → the right
  panel swaps from island drivers to parish detail: active count, attack
  rate, mini epicurve with band, top routes, and a "vs Jersey average" line.
  Deselect restores island view. No separate page.
- **Analysis tabs** (one visible at a time): Epidemic curve (metric toggle +
  ensemble band), Transmission routes (ranked bars, resident and travel
  columns, "up to day" vs "day only"), Ages (four band cards with counts,
  attack rate, bar), Travel & visitors, Interventions (Gantt vs. case
  sparkline).
- **Data loading**: on open, the client pages `daily_epidemic`,
  `daily_parish`, `daily_route`, `daily_age` (and travel tables when present)
  through the bounded dataset endpoint into memory; all scrubbing is then
  client-side and instant. 366 days × 12 parishes × ~18 routes stays well
  under the 10,000-row page cap with a few requests.

## 6. Comparison UX

- Built on the `scenario_compare` job kind (matched seeds). Header names both
  arms and the seed pairing.
- **Four delta cards** lead: cumulative infections (absolute + %), peak
  infectious, peak date shift, attack rate — each with the underlying
  "A → B" values in small text. Decreases render in the diverging blue,
  increases in the diverging red; direction is also carried by sign and
  wording, never color alone.
- Paired epicurve: baseline dashed neutral, treated accent, both with bands.
- **Route shifts**: overlaid base/treated bars with absolute change and
  percent — absolute counts always accompany shares (a share can rise while
  counts fall).
- **Map modes**: Baseline / Intervention (sequential scale) / Difference
  (diverging scale, "fewer ↔ more under intervention").
- **Intervention burden** card: agent-days, setting-days, doses — reported
  separately from health outcomes, as M7 does.
- Permanent footnote: "Simulated differences under the declared model
  assumptions — not predictions of real policy effectiveness."

## 7. Map visualization system

- **Real 12-parish choropleth**: OpenStreetMap administrative boundaries
  (ODbL — the implementation must carry OSM attribution), mainland ring only,
  Douglas-Peucker simplified to ~1,200 points total and equirectangularly
  projected. The mockup embeds this geometry; the implementation should
  regenerate it from a pinned OSM extract with the same simplification. No
  agent dots, ever — individual-agent rendering is out of scope for M10.
- Five-bin sequential fill; bins recomputed per metric against the
  run's own maximum so playback shows spread, not flicker; legend shows the
  scale extent numerically.
- Parish labels use a halo (paint-order stroke) so they stay legible on any
  bin; parishes are focusable buttons with visible focus states.
- Difference maps switch to the five-bin diverging scale with a neutral
  midpoint.
- Water/panel surface distinguishes the island from the app ground in both
  themes.

## 8. Chart / visualization system

- **Epicurve**: median line + replicate-range band (never labelled
  "confidence interval"); day marker synced to the scrubber; metric switching
  instead of stacked series; one y-axis always.
- **Route attribution**: ranked horizontal bars showing absolute count and
  share side by side; resident and travel routes in separate columns; no pie
  charts. The right-panel "What's driving transmission" is the same component
  cut to the current day's top 5.
- **Ages**: per-band cards (count, attack rate, bar) — counts and rates
  together, no severity implication; note that risk strata are targeting
  metadata only.
- **Travel**: six stat tiles (arrivals today, active visitors, returning
  residents, travel-linked acquisitions, visitor→resident,
  resident→visitor), a two-series arrivals/visitors line, and a
  cross-population transmission bar set. Deliberately epidemiological, not a
  flight tracker.
- **Intervention timeline**: Gantt bars (calendar families solid,
  detection-triggered families hatched — meaning carried by texture, not
  color alone) under an active-infectious sparkline sharing the same x-axis.
- Numerals are tabular; grids/axes recessive; direct labels on bars; legends
  whenever two series share a plot.
- **Export**: the epicurve, route, and comparison charts carry a compact
  Export menu — "Chart as PNG" (client-side canvas render of the SVG) and
  "Data as CSV" (the visible slice, fetched through the existing bounded
  dataset endpoint and named after the canonical dataset, e.g.
  `daily_route`). No backend change required.

## 9. Run / job states

Phases come straight from the M9 contract; the UI renders them as a
checklist with plain-language descriptions:

| API phase | UI line |
| --- | --- |
| `queued` | Queued — one scientific job runs at a time |
| `validating` | Validating scenario |
| `preparing` | Building Jersey population & contact networks (the long part) |
| `running` | Running outbreak |
| `writing_artifacts` | Writing results |
| `verifying` | Verifying results |
| `finalizing` | Finalizing — only verified results are published |

- **No fake progress**: `progress_fraction` is null, so no percentage or
  indeterminate progress bar pretending otherwise; instead phase + elapsed
  time + a visible honesty note. Long `preparing` phases are normal and the
  copy says why (deterministic M2–M4 reconstruction).
- Status by polling `GET /jobs/{id}` (~2 s) and `/events` for the phase log.
- **States**: QUEUED (position note), RUNNING (pulse chip), SUCCEEDED
  (green, "Open results"), FAILED (error summary from `error`, worker-log
  access, "Duplicate & edit"), CANCELLED (who/when), INTERRUPTED ("the server
  stopped mid-run; it is never silently re-run" + Re-run action),
  CANCEL_REQUESTED renders as Cancelling…. Cancellation available whenever
  queued/running.
- State chip colors: green/teal/neutral/red/amber, always paired with the
  state word.
- **Completion notification**: when a job reaches a terminal state the app
  raises a toast (state-colored edge, "Open results" action, auto-dismiss)
  and, if the user is elsewhere, a badge dot on the Runs rail item that
  clears on visit. The implementation should additionally request browser
  `Notification` permission (opt-in, from Settings) so long full-island runs
  can be left unattended.
- **Fizzle is a first-class result**: a run whose outbreak dies out early is
  not an error state. The results workspace shows a calm callout ("The
  outbreak died out by day N — X residents infected; with these assumptions
  stochastic die-out is common"), honest small headline numbers, the
  near-empty map, and two forward actions (duplicate with stronger seeding;
  return to another run). No red, no empty-chart placeholders.

## 10. Provenance / assumption UX

- **Claim boundary**: one calm line permanently in the top bar; repeated in
  drawer and comparison footnote. Professional, not alarming.
- **Provenance badges** everywhere a parameter appears: `Observed`,
  `Derived`, `Literature prior`, `Calibrated`, `Scenario assumption` — the
  exact engine statuses, with a legend in the drawer. Sliders never imply
  empirical knowledge.
- **Assumptions & sources drawer** (one click from anywhere): synthetic-model
  note; verification block (finalizer status, engine commit + dirty flag,
  Starsim version, request/scenario/latent/bundle hashes, truncated with
  copy); parameter provenance table; badge legend. Hashes are one click away,
  never ambient.

## 11. Visual design system

- **Direction**: scientific instrument × survey chart. Calm, high-information,
  map-first.
- **Type**: Instrument Sans (UI, 400–700); IBM Plex Mono (numerals, dates,
  hashes, axes). Tabular numerals for all metrics. Base 14 px; headline
  metrics 23–24 px; no sub-10 px text.
- **Neutrals** (cool, blue-biased): ground `#EEF1F2`, panel `#FBFCFC`, ink
  `#1C2326`, secondary `#4C5B62`, muted `#77878E`, hairline `#D6DDE0`, water
  `#E2E9EB`. Dark theme: ground `#131719`, panel `#1C2225`, ink `#E6ECEE`.
- **Accent**: petrel teal `#20707B` (dark: `#4FA6B1`) — CTAs, active states,
  the single-series epicurve.
- **Map treatment — "Survey Coral"** (chosen from a four-option exploration):
  tidal-water panel `#E4EDEF` (dark `#16232A`) with a faint 86 px graticule
  `#D3E0E3` / `#1E313A`; a two-ring offshore shallows halo `#CFDEE2` /
  `#1D2F38` behind the island; coastline stroke `#7E99A3` / `#4E6874`;
  parish hairlines `#FDFEFE` / `#101B20`; haloed labels; a small 2-mile
  scale bar.
- **Sequential (infection intensity)**: 5 luminous coral bins
  `#FBF3EE → #F5CDB8 → #EC9C7E → #D5644C → #9E2F28` (dark:
  `#33261F → #6E3C2C → #A5573C → #D97C55 → #F7B08A`), lightness-monotonic
  per surface.
- **Diverging (comparison)**: `#2a78d6 ↔ #C33B37` around a neutral midpoint.
- **Intervention identity** (fixed categorical order, CVD-validated set):
  isolation `#2a78d6`, school `#eb6834`, WFH `#1baf7a`, vaccination
  `#e87ba4`, community `#eda100`, care `#4a3aa7`, quarantine `#e34948`,
  travel `#008300`; consistent across builder cards, timeline strip, Gantt.
  Timeline bars always carry direct labels; hatching distinguishes
  detection-triggered families.
- **Status**: good green / warn amber / bad red soft-chip pairs, always with
  words, never reused as series colors.
- Radius 8 px, single soft shadow level; no gradients, no glassmorphism.
- **Spacing scale**: structural spacing (card padding, section gaps, margins)
  sits on a 4 px grid — 8 / 12 / 16 / 20 / 24 / 28 / 32. Micro spacing
  inside components (chip padding, icon gaps, 2–7 px) is optical and exempt.
  Audited across the whole mockup; nothing structural is off-grid.

## 12. Responsive / accessibility behavior

- **Desktop-first at ~1440 px**; app frame holds a 1180 px minimum. Below
  1180 px the workspace stacks (map → metrics → time → tabs) and the layer
  rail folds away — a tablet fallback, not a redesign. The desktop
  experience is never compromised for mobile.
- Keyboard: parishes, tabs, segmented controls and scrubber are focusable
  with visible focus rings; ←/→ step days, space plays/pauses; Esc closes
  the drawer. A `?` overlay (also reachable from a "Shortcuts" button in the
  time bar) lists the bindings; shortcuts never fire while typing in a
  field.
- Non-color meaning everywhere: state words on chips, hatching for
  detection-triggered bars, signs and wording on deltas, direct labels on
  bars, sequential bins ordered by lightness.
- `prefers-reduced-motion` disables playback autostep animation and pulses.
- Both themes are designed (token-level), not auto-inverted.

## 13. Interactive mockup

Published artifact:
<https://claude.ai/code/artifact/bbcad36a-b4bf-4936-a6a3-d5bf84a359b1>.
Covers all twelve required screens/states: home, builder, running job
(simulated phase progression + cancel), results workspace, parish selection,
intervention timeline, route attribution, travel analysis, comparison
(including difference map), run history (all seven states), provenance
drawer, and failed/cancelled jobs. Includes a light/dark toggle. All data is
deterministic fake data; no API calls.

## 14. M10 UI NEEDS API SUPPORT

Features the design keeps, defers, or flags because M9 does not serve them:

1. **Push status** — M9 has no SSE/WebSockets; M10 v1 polls `GET /jobs/{id}`.
   Server-sent events would remove polling but are *not required*.
2. **Named/saved scenario library** — the API stores requests per job only.
   M10 v1 implements "Saved scenarios" client-side (localStorage /
   duplicate-from-run). A server-side scenario store is future API work.
3. **Run deletion / retention controls** — deferred in M9; the Runs screen
   therefore has no Delete action.
4. **Raw artifact download** — deferred in M9; the UI links to manifest
   metadata only, not file downloads.
5. **Cross-job comparison of two already-completed runs** — comparison is a
   `scenario_compare` job (both arms re-run matched); the UI's "Compare"
   action from history submits a new compare job rather than diffing two
   existing result sets. True post-hoc diffing of arbitrary completed jobs
   would need API support (or client-side dataset joining, acceptable for
   identical-horizon runs).
6. **Fractional progress** — intentionally absent; the design embraces
   phases and must not regress into fake percentages if partial progress is
   ever added.
7. **Arrival-points map layer** — needs per-day terminal-entry aggregates;
   `travel_episodes` provides raw episodes, so this is client-side
   aggregation (fine) but flagged as potentially heavy for large streams.
8. **Age × parish cross-tabulation** — `daily_age` and `daily_parish` are
   separate tables; the UI does not promise an age-by-parish view.

None of these block the M10 v1 flows; every primary screen maps onto
existing endpoints and datasets.

---

### First-run acceptance check

A user who knows nothing about the architecture can: open JOS → see Jersey →
New scenario → accept defaults → Run → watch honest phases → Open results →
scrub time on the map, read the four headline numbers, and see the ranked
routes answer "what's driving this?" — without documentation. An advanced
user can reach every real parameter, provenance label, and hash within two
clicks. That is the bar the implementation must preserve.
