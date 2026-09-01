# R4 evidence regeneration — delta note

**Date:** 2026-09-01 · **Candidate:** `e502ebfd366743db8ecbb65f580159bfa1d2a70c` · **Evidence:** `~/Documents/JOS_v1_1_full_scale_evidence/run-20260901T131226Z/` (supersedes `run-20260831T145052Z` as release evidence; the older dir is retained as the B01-defect exhibit).

## Trajectory delta: NONE — proven by hash identity

The regenerated 180-day run (same seed 123, same configs, corrected SHA) produced **bit-identical scientific content** to the 2026-08-31 run: artifact id `jos-intervention-m7-full-seed-123-f0b18d64a083`, latent logical hash `ca4570849d0f...`, bundle hash `f0b18d64a083...` all unchanged. The B01/B02/B03/M01/M02 corrections altered packaging contracts only, exactly as required ("no unrelated scientific change"). The filed V1.0↔V1.1 comparison (`2026-09-01-p1-v1-v11-comparison.md`) therefore applies verbatim to the new candidate.

## Packaging delta: the B01 fix demonstrated on full-scale evidence

- Manifest schema 2.1 (was 2.0), `git_commit` = `e502ebf`, nested M5 schema 1.2.
- All output paths artifact-relative; nested M5 self-contained (paths relative to its own root); zero absolute paths.
- **In-place verification: PASS.**
- **Relocation verification: PASS** — artifact copied to a fresh directory, original hidden, copy verified recursively (M7 → embedded M5). This exact check failed on the 2026-08-31 bundle (Sol Pro B01 exhibit).

Runtime 14,098s (thermal/contention variance; content-identical output makes runtime immaterial). Verification performed from the repair worktree at the candidate SHA.
