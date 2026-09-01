# GATES — decisions parked on Steven

*One entry per open human decision: question · options · default on no answer. Agents route work around open gates instead of stalling on them. Resolved gates move to the bottom with the ruling.*

## Open

### G7 — Merge the V1.2 carry-ins branch into `main`
- **Question:** merge `codex/v1.2-carry-ins` at exact SHA **`9711b8e3937b3ff18aec86523ed4769ff78cfd4c`** into `main`? (CI run 33556105665 green on both jobs; suite 235; terra trail audit flags all closed; no science defaults, schema or version constants changed — diff is diagnostics-derivation, CI, a verify subcommand, a CI script, tests.)
- **Rule:** SHA-first; `main` has moved since the branch point (state-layer commits only), so this is a `--no-ff` merge, not a fast-forward.
- **ACTIONABLE — Steven's hands:**
  ```
  cd ~/Documents/jsy_disease_sim
  git fetch origin
  git merge --no-ff 9711b8e3937b3ff18aec86523ed4769ff78cfd4c -m "Merge V1.2 carry-ins (codex/v1.2-carry-ins @ 9711b8e)"
  uv run --locked pytest -q tests/test_v12_carry_ins.py tests/test_v12_bundle_selftest.py   # smoke
  git push origin main
  ```
- **Default:** waits for Steven. No tag (not a release).

### G8 — M04: replicate count and machine for the P4 full-scale ensemble
- **Question:** run ≥40 successful replicates (2.5/97.5 stochastic-replicate quantiles allowed by the project's n·min(q,1−q)≥1 rule) or N=30 (median/IQR + labelled extrema only)? And on the desktop (5800X/32 GB, ~12 parallel, est. 15–20 h wall for 40) or the Mac (~6 parallel, 25–35 h, laptop unusable)?
- **Default:** ≥40 on the desktop, launched only after G7 merges and the desktop smoke passes. Bands labelled "stochastic replicate quantile", never confidence intervals.

### G5 — Branch cleanup
- **Question:** 20+ historical branches (now all pushed to origin). Prune any?
- **Default:** preserve all (handoff §7.6). Revisit only after V1.1 is secure.

## Resolved

### G4 — Doc commits on frozen `main` — RESOLVED 2026-09-01 (Steven: "fold it into main"): `docs/frontier` merged into `main` (`--no-ff`) after the V1.1 release; state layer now lives on `main`, sessions open in the repo.

### G6 — V1.1 release-repair run — RESOLVED 2026-09-01 (Steven, in chat: "run the repair and keep going"): launched same day
Run completed 2026-09-01: re-audit PASS at `e502ebf...`. *(Closed late — caught by the terra trail audit, same failure class as G2/B04.)*

### G2 — V1.1 full-scale baseline — RESOLVED 2026-08-31 (Steven, in chat: "keep it going"): approved, Mac
Run completed 2026-08-31 (run-20260831T145052Z, verification PASS, comparison filed 2026-09-01). *Bookkeeping note: this gate was left open in this file until 2026-09-01 despite the chat ruling — flagged by Sol Pro B04; lesson encoded in DIRECTOR.md.*

### G1 — Launch the independent V1.1 audit — RESOLVED 2026-08-31 (Steven, in chat): launch now
Overrode the after-EMA default. Audit launched same day via foreman pilot run (Sol@high, read-only, detached worktree at the candidate).

### G3 — V1.1 merge + tag — RESOLVED 2026-09-01 (Steven, in chat: "merge it for me"): executed by agent per exact SHA-first procedure
ff to e502ebf verified via rev-parse, smoke green, tag jos-v1.1.0 pushed. Agent-executed merge was a one-time explicit instruction, not a standing authorization - future merges remain Steven-gated by default.
