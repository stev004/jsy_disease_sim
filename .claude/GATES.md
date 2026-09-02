# GATES — decisions parked on Steven

*One entry per open human decision: question · options · default on no answer. Agents route work around open gates instead of stalling on them. Resolved gates move to the bottom with the ruling.*

## Open

### G5 — Branch cleanup
- **Question:** 20+ historical branches (now all pushed to origin). Prune any?
- **Default:** preserve all (handoff §7.6). Revisit only after V1.1 is secure.

## Resolved

### G8 — M04: replicate count and machine for the P4 full-scale ensemble — RESOLVED 2026-09-02 (Steven, in chat: "go with the default")
Ruling = the default: ≥40 successful replicates on the desktop (DESKTOP-KQTC6VL, WSL2 mode per the 2026-09-02 transfer), `--workers 12`, launched after the desktop smoke/gate passed (it did — see `docs/runs/2026-09-02-desktop-transfer-wsl.md`). Bands labelled "stochastic replicate quantile", never confidence intervals. Launched as 44 seeds (101–144) so ≥40 successes survive replicate failures; 44 costs the same wall time as 40 at 12 workers (4 waves).

### G7 — Merge V1.2 carry-ins into `main` — RESOLVED 2026-09-01 (Steven, in chat: "merge all"): executed by agent, `--no-ff` merge of exact SHA `9711b8e3937b3ff18aec86523ed4769ff78cfd4c` → merge commit `9a2d984f265aca2e8edfcc10de6bb45b2519f140`; smoke (6 v12 tests + demo) green; pushed. Second one-time agent-executed merge on explicit instruction (after G3); still not a standing authorization.

### G4 — Doc commits on frozen `main` — RESOLVED 2026-09-01 (Steven: "fold it into main"): `docs/frontier` merged into `main` (`--no-ff`) after the V1.1 release; state layer now lives on `main`, sessions open in the repo.

### G6 — V1.1 release-repair run — RESOLVED 2026-09-01 (Steven, in chat: "run the repair and keep going"): launched same day
Run completed 2026-09-01: re-audit PASS at `e502ebf...`. *(Closed late — caught by the terra trail audit, same failure class as G2/B04.)*

### G2 — V1.1 full-scale baseline — RESOLVED 2026-08-31 (Steven, in chat: "keep it going"): approved, Mac
Run completed 2026-08-31 (run-20260831T145052Z, verification PASS, comparison filed 2026-09-01). *Bookkeeping note: this gate was left open in this file until 2026-09-01 despite the chat ruling — flagged by Sol Pro B04; lesson encoded in DIRECTOR.md.*

### G1 — Launch the independent V1.1 audit — RESOLVED 2026-08-31 (Steven, in chat): launch now
Overrode the after-EMA default. Audit launched same day via foreman pilot run (Sol@high, read-only, detached worktree at the candidate).

### G3 — V1.1 merge + tag — RESOLVED 2026-09-01 (Steven, in chat: "merge it for me"): executed by agent per exact SHA-first procedure
ff to e502ebf verified via rev-parse, smoke green, tag jos-v1.1.0 pushed. Agent-executed merge was a one-time explicit instruction, not a standing authorization - future merges remain Steven-gated by default.
