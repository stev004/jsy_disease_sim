# GATES — decisions parked on Steven

*One entry per open human decision: question · options · default on no answer. Agents route work around open gates instead of stalling on them. Resolved gates move to the bottom with the ruling.*

## Open

### G2 — Approve the V1.1 full-scale 180-day baseline run (P1, after audit PASS)
- **Question:** run the ~3h full-population comparator, and on which machine?
- **Options:** Mac (continuity with V1 pilot) · desktop (after transfer)
- **Default:** Mac, overnight, after audit PASS. Ensemble stays desktop-only regardless.

### G3 — V1.1 merge + tag (P3)
- **Question:** merge `codex/v1.1-integration` → `main` and tag `jos-v1.1.0`?
- **Options:** only after P0–P2 all pass (Sol's release procedure §17)
- **Default:** blocked until P0–P2 complete. Never merged by an agent — Steven's hands only.

### G4 — Doc commits on frozen `main`
- **Question:** Sol's freeze rule keeps even doc fixes off `main`, so the frontier lives on `docs/frontier`. Accept that until V1.1 ships, then fold frontier/handoff/stale-doc fixes into the release integration?
- **Options:** accept (preserves fast-forward release) · relax (allow doc-only commits on main, release becomes a merge)
- **Default:** accept.

### G5 — Branch cleanup
- **Question:** 20+ historical branches (now all pushed to origin). Prune any?
- **Default:** preserve all (handoff §7.6). Revisit only after V1.1 is secure.

## Resolved

### G1 — Launch the independent V1.1 audit — RESOLVED 2026-08-31 (Steven, in chat): launch now
Overrode the after-EMA default. Audit launched same day via foreman pilot run (Sol@high, read-only, detached worktree at the candidate).
