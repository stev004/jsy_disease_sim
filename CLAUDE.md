# CLAUDE.md — Jersey Outbreak Simulator (JOS) router

Synthetic-population, multi-route contact-network, agent-based epidemic simulator for Jersey (Starsim 3.5.2; Python backend + React frontend). **Research software: synthetic and scenario-based, never a validated forecast of Jersey.** Current release: `jos-v1.1.0`.

## Start here, every session
1. **`.claude/FRONTIER.md`** — where the project is, the one next action, branch index, doc authority. Read it first; it supersedes every status claim in older docs.
2. `.claude/RUN.md` — is an autonomous run in flight? If yes, its resume recipe is authoritative.
3. `.claude/GATES.md` — decisions waiting on Steven, each with a default.
4. `.claude/DIRECTOR.md` — standing orders + hard rules + encoded lessons (binding for any agent driving work here).

## New machine?
If this checkout has never run the loop here (no `desktop-transfer` row in `.claude/decisions.tsv` for this hostname), execute `docs/desktop-setup.md` §1 yourself before anything else — it is an agent runbook, not user instructions.

## How work happens here
- Multi-iteration work runs through the **`/foreman`** skill (vendored in `.claude/skills/`, installed to `~/.claude/skills/` by `scripts/install_skills.sh` — new machine: `docs/desktop-setup.md`): a director (Claude via `/foreman`, or GPT-6 Astra via `$foreman` in a `codex -m gpt-6-astra` session opened in this repo) drives luna@xhigh executors; memory = the `.claude/` state files above. Trail = `.claude/decisions.tsv` (append-only). State ops via `fm.sh log|sync|exec` — state lives on `main`, so it operates in place.
- Single ad-hoc changes: `/dev-delegate`. Session end: `/closeout` (doc map in `.claude/CLOSEOUT.md`).
- **Codex's constitution is `AGENTS.md`.** Implementation briefs must be self-contained (Codex sees nothing but the brief + worktree).

## Hard rules (detail in DIRECTOR.md + the handoff)
Release merges are SHA-first and Steven's call · tags `jos-v1.0.0` / `jos-v1.1.0` and all evidence dirs under `~/Documents/JOS_v1*_full_scale_evidence/` are immutable · mechanism support and default activation are assessed separately · explicit unknown beats false precision — never invent parameters, CVs, catchments, or year groups · ensemble bands are stochastic replicate variation, never confidence intervals · `docs/progress.md` and implementation-status docs are claims to verify, never audit evidence.

## Deep history
`docs/handoff/2026-08-31-sol-handoff.md` (conventions, prohibitions, M0→V1.0 lineage) · `docs/audits/` (every independent audit) · `docs/runs/` (run reports, comparisons) · roadmap authority for V1.2→V2 = `docs/audits/2026-09-01-solpro-deep-audit-BLOCKED.md` §9–11.
