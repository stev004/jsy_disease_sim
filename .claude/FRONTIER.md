# FRONTIER — the single current-state pointer for JOS

*Snapshot, not history. Rewritten each time the frontier moves. Lives on the `docs/frontier` branch because `main` is frozen at the V1 release commit until V1.1 ships (Sol handoff §2.1). If you are cold-starting: read this file, then `docs/handoff/2026-08-31-sol-handoff.md` for full depth.*

**Updated:** 2026-08-31 (post-corrective) · **Updated by:** Fable (foreman corrective run)

## Where the project is

**Tier: V1.1 scientific hardening — candidate audited PASS (P0 complete); full-scale baseline (P1) next, gated on Steven.**

- **V1.0 released and frozen:** `main` = tag `jos-v1.0.0` = `9e9ce3abc4201cd8303c723015462d21ca237800` (verified 2026-08-31). Immutable until the V1.1 release gate completes.
- **V1.1 release candidate: `e3609ff288b33444456de960db9e7c6560d0b898`** — tip of `codex/v1.1-o2-denominator` (pushed to origin), parent = the originally audited `461bf038`. **P0 independent audit: COMPLETE and PASSED** — full audit 2026-08-31 returned BLOCKED on one defect (O2 false denominator metadata); minimal corrective (1-line fix + staggered-arrival regression test) implemented, reviewed, and passed a bounded delta re-audit the same day. Reports: `docs/audits/2026-08-31-v1.1-rc-audit-BLOCKED.md` + `docs/audits/2026-08-31-o2-delta-reaudit-PASS.md`. Backend suite is now 215 tests. `codex/v1.1-integration` (`461bf03`) is superseded as candidate; do not merge the fix into it — the corrective branch IS the candidate line.

## The one next action

**P1 COMPLETE (2026-08-31/09-01): full-scale baseline run + verification + comparison all done.** Run: 180d, 104,540 agents, seed 123, scientific verification PASS, artifact `jos-intervention-m7-full-seed-123-f0b18d64a083` in `~/Documents/JOS_v1_1_full_scale_evidence/run-20260831T145052Z/` (immutable comparator pair with the V1 evidence dir). Comparison verdict: **`P1 OBSERVATION: NO RELEASE CONCERN`** (`docs/runs/2026-09-01-p1-v1-v11-comparison.md`). Headline: waning removal collapses reinfection (2.97 → exactly 1.00 episodes/infected), single wave, extinction 2025-03-27, 77.85% ever infected, conservation exact, generation interval unchanged. Runtime +27% (operational note, partially thermal/contention), peak RSS lower.

**Next: P2 — Claude Science delta review** of the V1→V1.1 change (bounded: candidate diff + finding closures + the comparison report; not a from-scratch 1,600-line audit). A GPT-5.6 Sol Pro deep audit + refined forward scope is also queued by Steven (bundle prepared 2026-09-01) — treat its output as input to P2/P5 planning. Then: P3 release decision/merge/tag (Steven; likely `jos-v1.1.0`) → P4 desktop + N=30 ensemble → P5 V1.x calibration → P6 V2.

## Branch index (verified against git 2026-08-31)

**Live:**
| Branch | Tip | Role |
|---|---|---|
| `main` | `9e9ce3a` | frozen V1 release — do not move |
| `codex/v1.1-integration` | `461bf03` | V1.1 release candidate — immutable while audit pending |
| `docs/jos-v1-scientific-review` | `b8aeb8b` | Claude Science V1 reports (audit/tech report/roadmap) |
| `docs/frontier` | this branch | frontier pointer + handoff + foreman state |

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
