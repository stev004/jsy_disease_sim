# GATES — decisions parked on Steven

*One entry per open human decision: question · options · default on no answer. Agents route work around open gates instead of stalling on them. Resolved gates move to the bottom with the ruling.*

## Open

### G3 — V1.1 merge + tag (P3) — **SHA-first, rewritten 2026-09-01 per Sol Pro B04**
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

### G6 — Launch the V1.1 release-repair run (R0–R3)
- **Question:** start the foreman run implementing Sol Pro's four blockers (B01 portable artifact paths, B02 daily ascertainment cohort semantics, B03 API schema versions, B04 already fixed in state) + majors M01/M02 on a new `codex/v1.1-release-corrections` branch off `e3609ff2`?
- **Options:** launch now · hold (EMA due 3 Sept noon)
- **Default:** hold until Steven says go. Bounded correction cycle, no model changes; then R4 (regenerate P1 evidence at the new SHA) + R5 (bounded re-audit).

### G4 — Doc commits on frozen `main`
- **Question:** Sol's freeze rule keeps even doc fixes off `main`, so the frontier lives on `docs/frontier`. Accept that until V1.1 ships, then fold frontier/handoff/stale-doc fixes into the release integration?
- **Options:** accept (preserves fast-forward release) · relax (allow doc-only commits on main, release becomes a merge)
- **Default:** accept.

### G5 — Branch cleanup
- **Question:** 20+ historical branches (now all pushed to origin). Prune any?
- **Default:** preserve all (handoff §7.6). Revisit only after V1.1 is secure.

## Resolved

### G2 — V1.1 full-scale baseline — RESOLVED 2026-08-31 (Steven, in chat: "keep it going"): approved, Mac
Run completed 2026-08-31 (run-20260831T145052Z, verification PASS, comparison filed 2026-09-01). *Bookkeeping note: this gate was left open in this file until 2026-09-01 despite the chat ruling — flagged by Sol Pro B04; lesson encoded in DIRECTOR.md.*

### G1 — Launch the independent V1.1 audit — RESOLVED 2026-08-31 (Steven, in chat): launch now
Overrode the after-EMA default. Audit launched same day via foreman pilot run (Sol@high, read-only, detached worktree at the candidate).
