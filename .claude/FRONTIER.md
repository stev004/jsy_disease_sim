# FRONTIER — the single current-state pointer for JOS

*Snapshot, not history. Rewritten each time the frontier moves. Lives on the `docs/frontier` branch because `main` is frozen at the V1 release commit until V1.1 ships (Sol handoff §2.1). If you are cold-starting: read this file, then `docs/handoff/2026-08-31-sol-handoff.md` for full depth.*

**Updated:** 2026-09-01 (post Sol Pro deep audit) · **Updated by:** Fable (foreman)

## Where the project is

**Tier: V1.1 RELEASE-READY — awaiting Steven's merge + tag (P3, gate G3).** The releasable SHA is **`e502ebfd366743db8ecbb65f580159bfa1d2a70c`** (`codex/v1.1-release-corrections`): all four Sol Pro blockers + M01/M02 closed, bounded re-audit **PASS** 2026-09-01 (`docs/audits/2026-09-01-release-corrections-reaudit-PASS.md`), gates green locally + GitHub CI, release evidence regenerated at the SHA with relocation verification PASS and hash-identical trajectory (`docs/runs/2026-09-01-r4-evidence-regeneration.md`). Follow-up carried to the V1.2 cycle: derive/relabel the travel-ensemble summary booleans (travel.py:3099, ruled non-blocking) + M03 CI breadth + M04 ≥40-replicate decision for P4.

Historical context of the repair (superseded): The core V1.1 science is NOT in question — the audit explicitly endorses the mechanisms, defaults, and the P1 trajectory ("no numerical release concern"). The blockers are contract-truth defects: **B01** artifact manifest paths break portable/recursive verification (writer records repo-root/absolute paths; verifier resolves artifact-relative) · **B02** daily `ascertainment_fraction` divides detection-date events by infection-date cohorts · **B03** `/capabilities` advertises 4 of 5 stale schema versions · **B04** release-control docs pointed at the superseded branch (fixed in this state layer 2026-09-01). Majors to close same cycle: M01 version identity (0.1.0 everywhere + stale README) · M02 travel diagnostic overclaims · M03 CI doesn't encode the full release gate · M04 the 30-replicate plan can't emit 95% bands under the project's own n·min(q,1−q)≥1 rule (need ≥40 or report median/IQR). Full report: `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md`.

- **V1.0 released and frozen:** `main` = tag `jos-v1.0.0` = `9e9ce3abc4201cd8303c723015462d21ca237800` (verified 2026-08-31). Immutable until the V1.1 release gate completes.
- **Candidate lineage — the releasable SHA is `e502ebfd366743db8ecbb65f580159bfa1d2a70c`** (tip of `codex/v1.1-release-corrections`): `461bf038` superseded 2026-08-31 (O2) → `e3609ff2` delta-re-audit PASS then BLOCKED by the Sol Pro deep audit (contract defects, not science) → 5 correction commits → `e502ebf`, bounded re-audit **PASS** 2026-09-01. Audit trail in `docs/audits/`, in order: `2026-08-31-v1.1-rc-audit-BLOCKED` → `2026-08-31-o2-delta-reaudit-PASS` → `2026-09-01-solpro-deep-audit-BLOCKED` → `2026-09-01-release-corrections-reaudit-PASS`. Merge rule SHA-first — GATES G3 has the exact procedure.

## The one next action

**P1 COMPLETE (2026-08-31/09-01): full-scale baseline run + verification + comparison all done.** Run: 180d, 104,540 agents, seed 123, scientific verification PASS, artifact `jos-intervention-m7-full-seed-123-f0b18d64a083` in `~/Documents/JOS_v1_1_full_scale_evidence/run-20260831T145052Z/` (immutable comparator pair with the V1 evidence dir). Comparison verdict: **`P1 OBSERVATION: NO RELEASE CONCERN`** (`docs/runs/2026-09-01-p1-v1-v11-comparison.md`). Headline: waning removal collapses reinfection (2.97 → exactly 1.00 episodes/infected), single wave, extinction 2025-03-27, 77.85% ever infected, conservation exact, generation interval unchanged. Runtime +27% (operational note, partially thermal/contention), peak RSS lower.

**R0–R5 recovery sequence: COMPLETE 2026-09-01** (all units accepted first-iteration; one lockfile fixup caught by the exact-SHA gate). **Next: P3 — Steven merges and tags** per G3's SHA-first procedure (fast-forward `main` to `e502ebf...`, verify HEAD, smoke, tag `jos-v1.1.0`, push). The Sol Pro audit satisfied P2 (science explicitly cleared, §6/§7).

**Forward roadmap authority CHANGED 2026-09-01:** the Sol Pro refined scope (audit §9–§11) supersedes the old flat P5 list: **V1.2** evidence+observation foundation → **V1.2.1** synthetic recovery/identifiability gate (3–5 fitted dimensions max) → **V1.3** first named-pathogen Jersey calibration (COVID era, predeclared holdouts, serology-constrained) → **V1.3.1** calibrated ensembles with decomposed uncertainty (≥40 replicates for 95% bands per M04) → **V1.4** structural validation + selective enrichment → **V2** only after a calibration passes held-out validation. §11's cut list is binding: no route-multiplier mass-fitting, no invented CV defaults, no 30-run 95% bands, no severity forecasting before denominators exist. Then P4 (desktop ensemble) slots after R5 with the ≥40-replicate decision made explicitly.

## Branch index (verified against git 2026-08-31)

**Live:**
| Branch | Tip | Role |
|---|---|---|
| `main` | `9e9ce3a` | frozen V1 release — do not move |
| `codex/v1.1-release-corrections` | `e502ebf` | **the releasable candidate** (re-audit PASS 2026-09-01) — merge target per G3 |
| `codex/v1.1-o2-denominator` | `e3609ff` | historical: base of the corrections branch (superseded) |
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
