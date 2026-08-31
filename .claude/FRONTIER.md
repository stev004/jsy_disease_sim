# FRONTIER — the single current-state pointer for JOS

*Snapshot, not history. Rewritten each time the frontier moves. Lives on the `docs/frontier` branch because `main` is frozen at the V1 release commit until V1.1 ships (Sol handoff §2.1). If you are cold-starting: read this file, then `docs/handoff/2026-08-31-sol-handoff.md` for full depth.*

**Updated:** 2026-08-31 · **Updated by:** Fable (frontier reconciliation session)

## Where the project is

**Tier: V1.1 scientific hardening — final independent audit pending.**

- **V1.0 released and frozen:** `main` = tag `jos-v1.0.0` = `9e9ce3abc4201cd8303c723015462d21ca237800` (verified 2026-08-31). Immutable until the V1.1 release gate completes.
- **V1.1 release candidate:** `461bf0387f4bb91db216b783c19f947f8583b4b8`, tip of `codex/v1.1-integration`. All lanes (correctness foundation, R1–R6 research, synthesis, M11-A/B/C/D) merged and implementation-verified (214 backend tests, frontend/tsc/build, full-mode regression — implementation-thread claims, not audit evidence).
- **The audit worktree already exists:** `/private/tmp/jsy-v11-final-audit`, detached at the candidate (verified 2026-08-31). Note all `/private/tmp` worktrees vanish on reboot — recreate with `git worktree add --detach /private/tmp/jsy-v11-final-audit 461bf038...` if gone.

## The one next action

**P0: independent V1.1 audit of exact commit `461bf038...`** — fresh Sol@high thread, read-only, detached worktree, methodology per handoff §10, verdict exactly `JOS V1.1 RELEASE-CANDIDATE PASS` or `... BLOCKED`. Steven launches it. Nothing else is unblocked before this.

Then in order (handoff §8): P1 full-population 180-day V1.1 baseline (Steven approves the ~3h run) → P2 Claude Science delta review → P3 release decision/merge/tag (likely `jos-v1.1.0`, not invented before approval) → P4 desktop transfer + N=30 ensemble → P5 V1.x calibration → P6 V2.

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
