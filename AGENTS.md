# AGENTS.md - Jersey Outbreak Simulator (JOS)

## What this is
Synthetic-population, multi-route contact-network, agent-based epidemic simulator for Jersey (Starsim 3.5.2; Python backend, React frontend). Research software: synthetic and scenario-based, never a validated forecast of Jersey. Released state and forward scope live in `.claude/FRONTIER.md`; hard rules and encoded lessons in `.claude/DIRECTOR.md`; roadmap authority is `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md` sections 9 to 11.

If you are directing a `$foreman` run: read `.claude/RUN.md`, `FRONTIER.md`, `GATES.md`, then `DIRECTOR.md` in full before anything else. If you are an executor launched from a brief: the brief is complete and this file is your contract; do not go looking for more context.

## How to verify work
- Python: `uv run pytest <path>` for the tests the brief names; the full suite is `uv run pytest`. If the sandbox blocks the default cache, set `UV_CACHE_DIR=/tmp/uv-cache`.
- Frontend: `npm run typecheck` and `npm test` from `frontend/`.
- Never run the 180-day full wave or the 30-replicate ensemble inside a task or audit; those are gated in `FRONTIER.md`.
- A green suite is evidence, not proof: read the implementation you changed before claiming done. For a reproduced bug, the first acceptance criterion is a test that fails on the base and passes on your branch.
- CLI error paths use plain `typer.echo(..., err=True)` plus `typer.Exit(code)`; tests assert on exit code and plain message, never on rich or ANSI output.
- Report per-criterion evidence with the real command output, files changed, and a diff stat. Do not git commit; the director commits.

## What goes wrong here
- Inventing numbers. Never fabricate school year groups, catchments, pathogen-neutral CVs, or any unsupported default. Explicit unknown beats false precision. Scientific parameter choices come from a written spec, never from an implementation agent.
- Touching protected contracts. Scientific semantics, hashes, artifact schemas, lifecycle ordering, identity, persistence and provenance rules are verified; change one only when the brief names it. If the task needs a break, stop and report the conflict.
- Vocabulary drift. Ensemble bands are stochastic replicate variation, never confidence intervals. Episode incidence is not ever-infected fraction. Gates are PASS/FAIL; scientific findings are CLOSED / PARTIALLY CLOSED BY DESIGN / DEFERRED / FAILED. Nothing is "calibrated" or "validated" before a predeclared held-out validation passes.
- Status docs as evidence. `docs/progress.md` and implementation-status docs are claims to verify, never audit evidence.
- Scope creep. Smallest root-cause change; no compatibility layers, second implementations, new dependencies, speculative abstractions, or unrelated test coverage. Stop when the acceptance criteria pass.
- Destructive git. No `reset --hard`, `git clean`, force-checkout, branch deletion or history rewriting. Never touch the existing `/private/tmp/jsy_*` worktrees or the evidence directories under `~/Documents/JOS_v1*_full_scale_evidence/`. Tags `jos-v1.0.0` and `jos-v1.1.0` are immutable.
- Performance "wins" without a measured hotspot and a fixed-seed scientific-equivalence proof.
