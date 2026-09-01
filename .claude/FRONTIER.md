# FRONTIER — the single current-state pointer for JOS

*Snapshot, not history. Rewritten each time the frontier moves. Lives on the `docs/frontier` branch (kept separate so release ancestry stays clean; revisit folding into `main` during V1.2). Cold-start: read this, then `docs/handoff/2026-08-31-sol-handoff.md` for deep history.*

**Updated:** 2026-09-01 (post-release) · **Updated by:** Fable (foreman)

## Where the project is

**Tier: V1.1 RELEASED.** `main` = tag **`jos-v1.1.0`** = `e502ebfd366743db8ecbb65f580159bfa1d2a70c`, fast-forwarded, smoked, and pushed 2026-09-01 (merge executed by the agent on Steven's explicit chat instruction — trail row of same date). V1.0 remains tagged `jos-v1.0.0` at `9e9ce3ab...`.

Release provenance, in order (`docs/audits/`): independent RC audit BLOCKED (O2) → O2 fix delta-re-audit PASS → Sol Pro deep audit BLOCKED (contract defects B01–B04 + majors; science explicitly cleared, P2 satisfied) → R0–R5 repair → release-corrections re-audit **PASS**. Release evidence: `~/Documents/JOS_v1_1_full_scale_evidence/run-20260901T131226Z/` — verified in place AND from a relocated copy; trajectory hash-identical to the pre-repair run, so the V1.0↔V1.1 comparison (`docs/runs/2026-09-01-p1-v1-v11-comparison.md`, "no release concern") applies verbatim. Both full-scale evidence dirs + the V1 pilot dir are immutable comparators.

## The one next action

**The V1.2 cycle** (roadmap authority = Sol Pro audit §9–§11, superseding the old flat P5 list). Its opening slate, roughly in order:
1. **Release-cycle carry-ins (small):** derive/relabel travel-ensemble summary booleans (`travel.py:3099`) · M03 — encode the full release gate in CI (frontend jobs, lock/compileall, artifact generate+relocate+verify, capability contract) · fix `JERSEY_OUTBREAK_SIMULATOR_PROJECT.md` header (still claims "through M6" on main) and the README `.claude/FRONTIER.md` link (resolves only on this branch) · evidence-transcript retention in release bundles (Sol Pro §12.6).
2. **P4 — desktop transfer + full-scale ensemble:** clone at `jos-v1.1.0`, desktop smoke, then the replicate run with the **M04 decision made explicitly**: ≥40 successful replicates for 2.5/97.5 bands per the project's own n·min(q,1−q)≥1 rule, or N=30 reporting median/IQR + labelled extrema only. Bands are stochastic replicate variation, never confidence intervals.
3. **V1.2 proper — evidence + observation foundation:** immutable Jersey source snapshots (cases/tests/serology/vaccination/denominators), canonical epidemiology tables with full provenance columns, observation-time correctness (suppression like `<5` never silently zeroed), data-quality diagnostics. Exit gate: a cold-start auditor reproduces every calibration input from frozen snapshots.
Then V1.2.1 (synthetic recovery/identifiability, 3–5 fitted dimensions max) → V1.3 (first named-pathogen Jersey calibration, COVID era, predeclared holdouts, serology-constrained) → V1.3.1 (decomposed-uncertainty ensembles) → V1.4 (structural validation) → V2 (only after held-out validation passes). §11's cut list is binding.

## Branch index (verified 2026-09-01)

**Live:** `main` @ `e502ebf` (= `jos-v1.1.0`) · `docs/frontier` (this state layer) · `docs/jos-v1-scientific-review` @ `b8aeb8b` (Claude Science V1 reports).
**Historical, preserve (handoff §7.6):** `codex/v1.1-release-corrections` (released tip) · `codex/v1.1-o2-denominator` · `codex/v1.1-integration` · the seven `codex/v1.1-*` lanes · all earlier `codex/m*`/`codex/c*` milestone branches · `codex/codex/m8.2-final-travel-closure` (typo, harmless). All pushed to origin.

## Off-repo assets

- `~/Documents/JOS_v1_full_scale_evidence/` (V1 pilot) and `~/Documents/JOS_v1_1_full_scale_evidence/run-20260831T145052Z` (pre-repair, retained as the B01 exhibit) and `run-20260901T131226Z` (release evidence) — all immutable.
- Desktop transfer: **not done** — first step of P4; origin holds everything needed.

## Doc authority map

1. This file — current frontier. 2. `docs/handoff/2026-08-31-sol-handoff.md` — deep history, conventions, prohibitions. 3. `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md` §9–§11 — forward roadmap authority. 4. On `main`: `docs/research/v1_1/V1_1_SCIENTIFIC_DESIGN_SYNTHESIS.md` — V1.1 design authority; `V1_1_IMPLEMENTATION_STATUS.md` + `docs/progress.md` — claims, never audit evidence. 5. `docs/jos-v1-scientific-review` branch — V1.0 scientific verdict.
