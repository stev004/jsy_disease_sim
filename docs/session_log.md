# Session log

Newest first. History only — current truth lives in the docs named by
`.claude/CLOSEOUT.md`.

## 2026-09-01 (evening) — V1.2 carry-ins run closed; DIRECTOR refreshed; branch awaiting G7 merge

**Summary.** Foreman run `v12-carry-ins` (director Fable 5.1, executor Codex luna, auditor Codex terra). Predicate: DIRECTOR.md free of pre-release rules + the three release-cycle carry-ins landed with suite and GitHub CI green at one SHA. Met in 4 iterations / 5 of 6 Codex runs; every unit accepted first iteration. Steven's opening ask was an audit of "where we're at"; findings were that the release claims all verified but DIRECTOR.md still carried frozen-main/candidate rules and a wrong "no AGENTS.md" note.

**Changes.** `main` (state layer only): DIRECTOR.md hard rules rewritten to the released state + forward-scope authority + M04 replicate rule + both evidence dirs; two new lessons (CI verdict read-before-log; no assertions on rich-rendered CLI output); GATES G3 removed from Open, **G7** (merge `codex/v1.2-carry-ins` @ `9711b8e3937b3ff18aec86523ed4769ff78cfd4c`, `--no-ff`, Steven) and **G8** (M04: ≥40 replicates on the desktop, default) parked; FRONTIER rewritten; five executor/audit reports + the real-artifact self-test transcript filed in `docs/runs/`. Branch `codex/v1.2-carry-ins` (5 commits, CI run 33556105665 green, suite 235): travel-ensemble diagnostics status derived from three named predicates (hash proven unchanged) · CI now the full release gate (lock check, compileall, real-CLI M7 generate→relocate→verify via `scripts/ci_relocation_check.py` with a pre-existing-artifact guard, diff check, clean-tree assertion, frontend job) · `jos verify bundle-selftest` writes a bundle-level machine-readable relocation transcript (status derived from steps; refuses in-artifact writes).

**Verified.** Director re-ran every unit's tests + ruff/mypy/compileall; bundle self-test run against the immutable V1.1 release artifact with the transcript to scratch (PASS, hashes agree with the R4 note); CI green at U1, U2b and final tips with job conclusions read. Terra trail audit: 6 flags (1 blocking = the CI failure at `28067d8`, fixed by U2b; 5 should-fix all closed). Director error self-caught and superseded in the trail: a PASS row logged before reading a CI conclusion that was actually failure.

**Open threads / resume points.** (1) **G7** — Steven merges `9711b8e` into `main` (procedure in GATES). (2) **G8** then **P4** desktop transfer + full-scale ensemble; machine analysis in FRONTIER (desktop ~12 parallel replicates, GPU irrelevant, Mac showed memory pressure). (3) V1.2 evidence foundation per Sol Pro §9. (4) Performance: R6 prototypes deferred to V1.2.1. Worktree `/private/tmp/jsy_v12_carryins` left in place on the branch.

**User needs to run.** The G7 merge block in `.claude/GATES.md` (SHA-first, `--no-ff`, smoke, push).

## 2026-09-01 — V1.1 RELEASED (`jos-v1.1.0`); foreman autonomous loop built and piloted here

**Summary.** Two-day thread (2026-08-31 → 09-01). The manual Sol-chat↔Codex loop was replaced by the `foreman` skill (director = Claude, executor = Codex, memory = repo state files). Repo reconciled from Sol's cold-start handoff; V1.1 taken from "integration branch, audit pending" to a twice-audited release in ~32 h. Nine autonomous units, every implementation accepted first-iteration.

**Decisions (Steven, in chat).** Launch the independent audit before the EMA (G1) · run the full-scale baseline on the Mac (G2) · run the Sol Pro release-repair immediately (G6) · **"merge it for me"** — the `jos-v1.1.0` merge/tag was executed by the agent as a one-time explicit instruction; future merges stay Steven-gated (G3 record). Roadmap authority moved to the Sol Pro refined scope (audit §9–§11): V1.2 evidence foundation → V1.2.1 identifiability gate → V1.3 first Jersey calibration → V1.3.1 → V1.4 → V2.

**Changes.** `main`: `9e9ce3a` → **`e502ebfd366743db8ecbb65f580159bfa1d2a70c`** (78 files, +5,224/−761: V1.1 hardening + B01 portable artifact paths + B02 cohort ascertainment + B03 truthful `/capabilities` + M01 version 1.1.0 + M02 travel diagnostics). Backend suite 214 → 229 tests. New branch `docs/frontier` (tip `67c6139`) carries the state layer (`.claude/FRONTIER|DIRECTOR|GATES|RUN.md`, `decisions.tsv`), `docs/handoff/`, four audits in `docs/audits/`, all run reports in `docs/runs/`. All 26+ branches and both tags pushed to origin (was: 2 branches). Two full-scale evidence dirs created (`run-20260831T145052Z` pre-repair exhibit, `run-20260901T131226Z` release evidence).

**Verified.** Independent RC audit (BLOCKED→fixed→PASS) · P1 baseline + comparison (no release concern) · Sol Pro deep audit (BLOCKED→repair) · R5 re-audit (**PASS**) · relocation verification of copied evidence (PASS) · trajectory hash identity across the repair · CI green at the release SHA. Full gate table in `docs/progress.md`.

**Open threads / resume points.** (1) ~~Fold `docs/frontier` into `main`~~ — DONE same evening on Steven's instruction (merge `ef84701`'s parent, router `CLAUDE.md` added, `fm.sh` in-place mode, G4 resolved); **sessions now open in this repo, `CLAUDE.md` is the router**. (2) **V1.2 cycle** — opening slate in FRONTIER.md: carry-ins (travel.py:3099 relabel, M03 CI breadth, charter/README pointers, evidence-transcript retention) → P4 desktop transfer + ensemble with the ≥40-replicate decision → V1.2 evidence foundation. Next run predicate suggestion: "carry-ins closed, CI encodes the full release gate, all green at one SHA". Owner: agent via `/foreman`, when Steven says go. (3) Desktop transfer not started (origin holds everything).

**User needs to run.** Nothing. Next: open Claude Code in this repo → "run foreman, done means the V1.2 carry-ins are closed and CI encodes the full release gate".

## 2026-08-30 — M10.2 comparison horizon and synchronization closure

**Scope.** Frontend-only corrective work on the required clean M10.1 base
`1688106ad490abce46c86a0483aaa6c4f8fa948a` and branch
`codex/m10.2-comparison-sync`. Backend/scientific code, M9.4, namespaced
loading, provenance, missing-value semantics and the difference-map contract
remain protected.

**Root cause.** `CompareView` used `model.days - 1` for cumulative infections
and attack rate. The global date union includes the observation tail through
2025-01-15, while the real matched latent comparison endpoints end on
2025-01-13.

**Correction.** `compareData.ts` now builds paired metric points from the same
persisted date, resolves the latest point at or before the selected/latest
global date, and exposes each metric's horizon, actual date and availability
status. `CompareView.tsx` displays the metric's actual as-of date and selected
date when they differ. No zero fill or frontend carry-forward was added.

**Verification.** The focused M10.2 fixture and full frontend tests pass;
TypeScript and the production build pass. Real job
`97211bc8-3f2f-44aa-ac64-a9a6d8283e4d` reached `SUCCEEDED` with request hash
`2e32ef6f1430d1f68c0f200e46689d83c2f063446394612493b33ab103262335`, baseline
artifact `afad384684e0ba0d78a14c0f279927e864b062ef561c40fac3fd974ca7671ecf`,
treated artifact `90e99de251443e179863477ace030f2612c7b2f1e66070d5bcf4f08349ebda7a`,
and matched comparison artifact `d57a8ccf63d0f3e6dcc622332dcd04734a0e402a3a02e9d16869555112ab5ea8`.
Its persisted endpoints reconcile to cumulative `85 -> 63 / -22` and attack
rate `0.028333333333333332 -> 0.021 / -0.007333333333333331`, both as of
2025-01-13, with global latest date 2025-01-15.

**Status.** M10.2 implementation PASS; final independent audit pending. No
release approval, merge to `main`, tag, or branch cleanup is recorded.

## 2026-08-30 — M9.4 closure and final M10.1 implementation verification

**History preserved.** The M10 implementation was independently audited and
failed. The frontend-only M10.1 correction was checkpointed at
`4ae6008871922bf7f1d820bf04294d477c55c14c` after 63 of 64 gates passed; its
remaining real School-closure gate exposed a protected backend calendar-date
reload defect, so that checkpoint deliberately did not claim PASS.

**M9.4 correction.** A clean branch from the verified M9 baseline fixed the
authoritative JSON deserialization mismatch without weakening Python-mode or
malformed-date validation. Commit
`37af56ea9a368b599f3c89bbbb399b13b465f8f2` preserves exact School `0 / 0`
multipliers and calendar activation semantics across persistence and verifier
reload. Real job `2c4191e8-b732-41a8-9072-bc989a7385a9` reached verified
`SUCCEEDED`; focused and protected backend regressions passed.

**M10.1 integration.** The exact M9.4 commit was merged without squashing;
merge commit `2dc29b5d7bcee8430b00c94928070172095e17d5` retains the checkpoint and
backend correction as ancestors. Fresh real baseline, School, M6 ensemble,
scenario comparison and M8 travel jobs all reached verified `SUCCEEDED` and
were reconciled with the rendered frontend. The School job
`442edefa-5855-4fbb-93bf-a0f9114c376e` retained its requested, normalized and
persisted `0 / 0` multipliers. All 64 M10.1 implementation gates now pass.

**Status.** M10.1 implementation PASS; independent final audit pending. This
does not record release approval, a merge to `main`, or a release tag.

## 2026-08-30 — M10.1 corrective milestone implementation

**Scope.** Frontend-only corrective work on `codex/m10.1-scientific-truth`,
based on M9 commit `bf7669eb5f0b3a315a227a3194726dfafe0ae32c`. Backend
scientific behavior, artifact writers, lifecycle ordering and identity rules
remain protected and unchanged.

**Corrections in progress.** Replaced silent missing-value zeros with explicit
unavailable values; preferred `cumulative_total_infections`; removed synthetic
comparison arms and geometric uncertainty bands; mapped ensembles to persisted
M6 summaries; constrained dates to 2025; corrected intervention payloads,
inclusive dates and detection-triggered timeline wording; bound provenance to
the displayed job; made mock data unmistakably demo/session-only; and corrected
the M9 API-gap documentation.

**Verification status.** The relevant backend suite passed (`76 passed`); the
frontend typecheck, 11 focused tests and production build passed. Live baseline
reconciliation, M6 ensemble loading, M8 travel loading and current namespaced
comparison loading passed. The corrected school payload validated and was
persisted with both school multipliers at zero, but the protected M9 worker
failed finalization because strict artifact verification rejects the serialized
calendar `start_date`. M10.1 therefore remains FAIL with no commit claimed.

## 2026-08-29 → 2026-08-30 — M10 design and frontend implementation

**Summary.** Designed the M10 interactive application end to end, then
implemented it as a working React/Vite frontend against the live M9 API.
All work on `codex/m10-interactive-app`, pushed to
`github.com/stev004/jsy_disease_sim` (private repo created this session —
the repo previously had no git remote).

**Decisions.**
- Visual direction: "Survey Instrument" (chosen over Journal / Console /
  Civic Atlas alternatives). Map treatment: "Survey Coral" (chosen from
  four options). Real OSM parish geometry (ODbL, attribution required).
- Template picker is a chip row, not a tile gallery; structural spacing on
  a 4px grid; global Simple/Scientific detail switch.
- Frontend stack: Vite + React 18 + TS, no runtime deps beyond
 react/react-router; mock data layer (the pre-M10.1 implementation auto-fell
 back when the API was down). Frontend default start date pinned to 2025-01-06
 (engine calendar).
- M10 gate NOT claimed — implementation exists; gate has not been run.

**Changes.** Commits 70b0dcb → 2ea6060 (all pushed): `docs/m10_ui_design.md`
(design spec + API-gap punch list), `frontend/` (scaffold 7ddf3fa, feature
views 2ea6060). Design artifacts (private claude.ai pages, linked in the
design doc): interactive mockup bbcad36a…, map treatments e92d61f2…,
design directions b68cf5f1….

**Verified.** Full end-to-end against the real engine: UI-submitted
scenario_run (ci mode, 2 interventions, travel) executed to SUCCEEDED;
Results renders real data (cumulative 2,009 = transmission_events rows;
routes/ages/travel cross-checked against independent API probes). Two bugs
found and fixed in the loop: 2026 default date (worker-killing), silent-zero
cumulative fallback (false fizzle callout).

**Open threads / resume points.**
- **M9.x API punch list** — owner: user decides when; spec lives in
  `docs/m10_ui_design.md` §14 items 9–14 (date-range validation at
  submission, per-arm compare datasets, populated breakdowns for travel
  artifacts, scenario display-name field, worker-log endpoint, wrong
  `dataset` echo field in dataset responses).
- **Frontend follow-ups** — parish choropleth for travel runs blocked on
  per-parish denominators (`observation_events` has `home_parish` counts
  but no denominators); intervention card "Edit" non-functional; travel
  "Custom" exposes no TravelConfig knobs yet; ExportMenu duplicated in
  results/compare views (dedupe when convenient).
- **Merge to main** — user's call: PR or merge `codex/m10-interactive-app`.
- **Pre-existing perf item** — verified M2–M4 parent caching (post-M9,
  pre-M10-gate), unchanged this session.
- Local test residue: ~10 throwaway jobs in
  `~/Library/Application Support/JerseyOutbreakSimulator/` from live
  bisection (harmless; M9 has no deletion endpoint).

**User needs to run.** Nothing mandatory. To use the app:
`uv run jos api serve` + `cd frontend && npm install && npm run dev`.
