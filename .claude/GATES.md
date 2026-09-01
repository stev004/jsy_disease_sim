# GATES — decisions parked on Steven

*One entry per open human decision: question · options · default on no answer. Agents route work around open gates instead of stalling on them. Resolved gates move to the bottom with the ruling.*

## Open

### ~~G3 — V1.1 merge + tag~~ — RESOLVED 2026-09-01: see Resolved section
*(procedure retained below for the record)*
### G3 (historical) — SHA-first merge procedure
- **Question:** merge the final audited release candidate into `main` and tag `jos-v1.1.0`?
- **Rule:** the merge target is an **exact SHA, never a branch name**. **The releasable SHA (re-audit PASS 2026-09-01): `e502ebfd366743db8ecbb65f580159bfa1d2a70c`.**
- **ACTIONABLE — Steven's hands only, exact procedure:**
  ```
  cd ~/Documents/jsy_disease_sim
  git fetch origin
  git merge --ff-only e502ebfd366743db8ecbb65f580159bfa1d2a70c
  git rev-parse HEAD    # MUST print e502ebfd366743db8ecbb65f580159bfa1d2a70c
  uv run --locked jos demo --seed 123   # smoke
  git tag jos-v1.1.0 e502ebfd366743db8ecbb65f580159bfa1d2a70c
  git push origin main --tags
  ```
- **Default:** waits for Steven. Never merged by an agent.


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
