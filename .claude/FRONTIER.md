# FRONTIER — the single current-state pointer for JOS

*Snapshot, not history. Rewritten each time the frontier moves. Lives on `main` (folded from `docs/frontier` 2026-09-01; that branch is now historical). Cold-start: read this, then `docs/handoff/2026-08-31-sol-handoff.md` for deep history.*

**Updated:** 2026-09-01 (V1.2 carry-ins run closed) · **Updated by:** Fable (foreman)

## Where the project is

**Tier: V1.1 RELEASED.** `main` = tag **`jos-v1.1.0`** = `e502ebfd366743db8ecbb65f580159bfa1d2a70c`, fast-forwarded, smoked, and pushed 2026-09-01 (merge executed by the agent on Steven's explicit chat instruction — trail row of same date). V1.0 remains tagged `jos-v1.0.0` at `9e9ce3ab...`.

Release provenance, in order (`docs/audits/`): independent RC audit BLOCKED (O2) → O2 fix delta-re-audit PASS → Sol Pro deep audit BLOCKED (contract defects B01–B04 + majors; science explicitly cleared, P2 satisfied) → R0–R5 repair → release-corrections re-audit **PASS**. Release evidence: `~/Documents/JOS_v1_1_full_scale_evidence/run-20260901T131226Z/` — verified in place AND from a relocated copy; trajectory hash-identical to the pre-repair run, so the V1.0↔V1.1 comparison (`docs/runs/2026-09-01-p1-v1-v11-comparison.md`, "no release concern") applies verbatim. Both full-scale evidence dirs + the V1 pilot dir are immutable comparators.

## The one next action

**Merge the V1.2 carry-ins branch (G7, Steven, SHA-first), then start P4.** Run `v12-carry-ins` closed 2026-09-01 with predicate met: `codex/v1.2-carry-ins` @ **`9711b8e3937b3ff18aec86523ed4769ff78cfd4c`** (5 commits on `main`'s code, CI run 33556105665 green on both jobs, suite 235) carries all three release-cycle carry-ins plus two audit-driven fixes — travel-ensemble diagnostics status derived from named predicates (Sol Pro §12.8) · full release gate in CI: `uv lock --check`, compileall, real-CLI M7 generate→copy→delete-original→verify, `git diff --check`, clean-tree assertion, frontend job (M03 / §12.3) · `jos verify bundle-selftest` writing a machine-readable relocation transcript at bundle level (§12.6; exhibit against the real release artifact filed at `docs/runs/2026-09-01-v12-release-artifact-bundle-selftest.json`). DIRECTOR.md hard rules refreshed to the released state. Trail audit (terra): 6 flags, all closed (`docs/runs/2026-09-01-v12-carry-ins-trail-audit-terra.md`).

**Then, in order (roadmap authority = Sol Pro audit §9–§11):**
1. **P4 — desktop transfer + full-scale ensemble.** Clone at `main` post-merge, desktop smoke, then the replicate run with the **M04 decision (G8) made explicitly**: ≥40 successful replicates for 2.5/97.5 bands per the n·min(q,1−q)≥1 rule, or N=30 reporting median/IQR + labelled extrema only. Bands are stochastic replicate variation, never confidence intervals. Machine note (2026-09-01): the sim is CPU-bound numpy, single process per replicate, 1.8 GB peak; the desktop (5800X/32 GB) fits ~12 parallel replicates via `jos ensemble run --workers`, the M4/16 GB Mac ~6 and its release run showed memory pressure (half its wall time idle). GPU is irrelevant to this workload.
2. **V1.2 proper — evidence + observation foundation:** immutable Jersey source snapshots (cases/tests/serology/vaccination/denominators), canonical epidemiology tables with full provenance columns, observation-time correctness (suppression like `<5` never silently zeroed), data-quality diagnostics. Exit gate: a cold-start auditor reproduces every calibration input from frozen snapshots. Calibration is excluded from this milestone.
3. **Performance (R6 prototypes) is deferred to V1.2.1**, where thousands of short synthetic runs make the per-run fixed cost matter; `docs/research/v1_1/R6_PERFORMANCE_PROFILE.md` is the ready brief (dynamic-route edge materialisation, attribution lookup, Starsim init graph) and every change needs its exact-equivalence gates.
Then V1.2.1 → V1.3 (first named-pathogen Jersey calibration, COVID era, predeclared holdouts, serology-constrained) → V1.3.1 → V1.4 → V2. §11's cut list is binding.

## Branch index (verified 2026-09-01)

**Live:** `main` (= `jos-v1.1.0` `e502ebf` + state layer + run reports) · **`codex/v1.2-carry-ins` @ `9711b8e`** (V1.2 carry-ins, CI green, awaiting G7 merge) · `docs/jos-v1-scientific-review` @ `b8aeb8b` (Claude Science V1 reports).
**Historical, preserve (handoff §7.6):** `docs/frontier` (state layer, folded) · `codex/v1.1-release-corrections` (released tip) · `codex/v1.1-o2-denominator` · `codex/v1.1-integration` · the seven `codex/v1.1-*` lanes · all earlier `codex/m*`/`codex/c*` milestone branches · `codex/codex/m8.2-final-travel-closure` (typo, harmless). All pushed to origin.

## Off-repo assets

- `~/Documents/JOS_v1_full_scale_evidence/` (V1 pilot) and `~/Documents/JOS_v1_1_full_scale_evidence/run-20260831T145052Z` (pre-repair, retained as the B01 exhibit) and `run-20260901T131226Z` (release evidence) — all immutable.
- Desktop transfer: **not done** — first step of P4 after G7; origin holds everything needed.

## Doc authority map

1. This file — current frontier. 2. `docs/handoff/2026-08-31-sol-handoff.md` — deep history, conventions, prohibitions. 3. `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md` §9–§11 — forward roadmap authority. 4. On `main`: `docs/research/v1_1/V1_1_SCIENTIFIC_DESIGN_SYNTHESIS.md` — V1.1 design authority; `V1_1_IMPLEMENTATION_STATUS.md` + `docs/progress.md` — claims, never audit evidence. 5. `docs/jos-v1-scientific-review` branch — V1.0 scientific verdict.
