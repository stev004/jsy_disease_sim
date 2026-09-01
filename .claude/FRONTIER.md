# FRONTIER — the single current-state pointer for JOS

*Snapshot, not history. Rewritten each time the frontier moves. Lives on the `docs/frontier` branch because `main` is frozen at the V1 release commit until V1.1 ships (Sol handoff §2.1). If you are cold-starting: read this file, then `docs/handoff/2026-08-31-sol-handoff.md` for full depth.*

**Updated:** 2026-09-01 (post Sol Pro deep audit) · **Updated by:** Fable (foreman)

## Where the project is

**Tier: V1.1 release repair — Sol Pro deep audit returned BLOCKED (2026-09-01); four bounded blockers to close, then regenerate evidence at the new SHA and re-audit.** The core V1.1 science is NOT in question — the audit explicitly endorses the mechanisms, defaults, and the P1 trajectory ("no numerical release concern"). The blockers are contract-truth defects: **B01** artifact manifest paths break portable/recursive verification (writer records repo-root/absolute paths; verifier resolves artifact-relative) · **B02** daily `ascertainment_fraction` divides detection-date events by infection-date cohorts · **B03** `/capabilities` advertises 4 of 5 stale schema versions · **B04** release-control docs pointed at the superseded branch (fixed in this state layer 2026-09-01). Majors to close same cycle: M01 version identity (0.1.0 everywhere + stale README) · M02 travel diagnostic overclaims · M03 CI doesn't encode the full release gate · M04 the 30-replicate plan can't emit 95% bands under the project's own n·min(q,1−q)≥1 rule (need ≥40 or report median/IQR). Full report: `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md`.

- **V1.0 released and frozen:** `main` = tag `jos-v1.0.0` = `9e9ce3abc4201cd8303c723015462d21ca237800` (verified 2026-08-31). Immutable until the V1.1 release gate completes.
- **Candidate lineage — there is currently NO releasable SHA:** `461bf038` (integration tip) superseded 2026-08-31 (O2 defect) → `e3609ff2` (`codex/v1.1-o2-denominator`) passed the bounded delta re-audit 2026-08-31 but is now **BLOCKED by the Sol Pro deep audit** (contract defects B01–B03, not science). The next candidate = final SHA of `codex/v1.1-release-corrections` (branch off `e3609ff2`, to be created at R0) after its bounded re-audit passes. Audit trail in order: `2026-08-31-v1.1-rc-audit-BLOCKED.md` → `2026-08-31-o2-delta-reaudit-PASS.md` → `2026-09-01-solpro-deep-audit-BLOCKED.md` (all in `docs/audits/`). Merge rule is SHA-first — see GATES G3.

## The one next action

**P1 COMPLETE (2026-08-31/09-01): full-scale baseline run + verification + comparison all done.** Run: 180d, 104,540 agents, seed 123, scientific verification PASS, artifact `jos-intervention-m7-full-seed-123-f0b18d64a083` in `~/Documents/JOS_v1_1_full_scale_evidence/run-20260831T145052Z/` (immutable comparator pair with the V1 evidence dir). Comparison verdict: **`P1 OBSERVATION: NO RELEASE CONCERN`** (`docs/runs/2026-09-01-p1-v1-v11-comparison.md`). Headline: waning removal collapses reinfection (2.97 → exactly 1.00 episodes/infected), single wave, extinction 2025-03-27, 77.85% ever infected, conservation exact, generation interval unchanged. Runtime +27% (operational note, partially thermal/contention), peak RSS lower.

**Next: the R0–R5 recovery sequence** (Sol Pro audit §8, gated on Steven — GATES G6): **R0** new branch `codex/v1.1-release-corrections` off `e3609ff2` → **R1** fix output contracts (B01 artifact-relative paths + relocation tests, B02 cohort-correct ascertainment + schema bump, B03 API versions from schema constants, M02 travel diagnostics) → **R2** release identity (M01 versions, README, this state layer) → **R3** full exact-SHA gate incl. relocation verification → **R4** regenerate the 180-day P1 evidence at the new SHA (~3.5h run) → **R5** bounded independent re-audit → then P3 merge/tag per G3 (SHA-first). The Sol Pro audit **satisfies P2** (independent science delta review — its §6/§7 explicitly clear the science).

**Forward roadmap authority CHANGED 2026-09-01:** the Sol Pro refined scope (audit §9–§11) supersedes the old flat P5 list: **V1.2** evidence+observation foundation → **V1.2.1** synthetic recovery/identifiability gate (3–5 fitted dimensions max) → **V1.3** first named-pathogen Jersey calibration (COVID era, predeclared holdouts, serology-constrained) → **V1.3.1** calibrated ensembles with decomposed uncertainty (≥40 replicates for 95% bands per M04) → **V1.4** structural validation + selective enrichment → **V2** only after a calibration passes held-out validation. §11's cut list is binding: no route-multiplier mass-fitting, no invented CV defaults, no 30-run 95% bands, no severity forecasting before denominators exist. Then P4 (desktop ensemble) slots after R5 with the ≥40-replicate decision made explicitly.

## Branch index (verified against git 2026-08-31)

**Live:**
| Branch | Tip | Role |
|---|---|---|
| `main` | `9e9ce3a` | frozen V1 release — do not move |
| `codex/v1.1-o2-denominator` | `e3609ff` | latest candidate line — BLOCKED by Sol Pro audit; base for the release-corrections branch |
| `codex/v1.1-release-corrections` | (to create at R0) | will carry the next candidate SHA |
| `docs/jos-v1-scientific-review` | `b8aeb8b` | Claude Science V1 reports (audit/tech report/roadmap) |
| `docs/frontier` | this branch | frontier pointer + handoff + foreman state |

*(`codex/v1.1-integration` @ `461bf03` moved to historical: superseded 2026-08-31, never a merge target — Sol Pro B04.)*

**Historical, preserve (handoff §7.6 — never squash/delete casually):** `codex/v1.1-{correctness-foundation,research,performance,m11a-natural-history,m11b-contact-behaviour,m11c-structure,m11d-semantics}` (V1.1 lanes, all merged into integration) · `codex/m10.2-comparison-sync`, `codex/m10.1-scientific-truth`, `codex/m10-interactive-app`, `codex/m9.4-calendar-finalization[-clean]` and all earlier `codex/m*`/`codex/c*` milestone branches · `codex/codex/m8.2-final-travel-closure` (double-prefix typo, harmless).

## Off-repo assets

- **V1 pilot evidence (immutable comparator):** `/Users/stevenmatson/Documents/JOS_v1_full_scale_evidence/` — never overwrite (handoff §7.12).
- Desktop transfer status: **not done** (verified: origin holds all branches as of this reconciliation, so the clone path is ready).

## Stale-doc warning

On `main` (frozen, can't be fixed in place): `JERSEY_OUTBREAK_SIMULATOR_PROJECT.md` header claims "through M6"; `README.md` says "M10 in progress". Both are years behind this file. **This FRONTIER.md supersedes every status claim in those docs.** Fix them in the V1.1 release integration, not before.

## Doc authority map (which file wins)

1. This file — current frontier.
2. `docs/handoff/2026-08-31-sol-handoff.md` — full state, decisions, audit methodology, prohibitions (binding).
3. On the candidate: `docs/research/v1_1/V1_1_SCIENTIFIC_DESIGN_SYNTHESIS.md` — V1.1 design authority · `V1_1_IMPLEMENTATION_STATUS.md` + `docs/progress.md` — claims to verify, never audit evidence (handoff §10.2).
4. On `docs/jos-v1-scientific-review`: the three `docs/reports/JOS_V1_*.md` — V1 scientific verdict + roadmap.
