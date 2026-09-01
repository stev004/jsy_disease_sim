---
name: closeout
description: Close out a work session in any repo — summarize the chat, record decisions and outcomes, sync the repo's markdown docs per its .claude/CLOSEOUT.md doc map, commit + push, and hand back anything the user still needs to run. Use when the user says "close out", "closeout", "wrap up", "end of session", "log this session", or a work thread is finishing. If the repo has no .claude/CLOSEOUT.md yet, bootstrap one first — that is part of this skill, not a reason to skip it.
---

# Closeout — end-of-session sync (any repo)

You are closing out a work session. The contract: **the next session — any model, cold start, zero shared context — must be able to pick up perfectly from the repo's docs alone.** The chat is ephemeral; the repo is the record. Be token-efficient: you already know what happened this session, so do not re-read files you didn't touch.

**Quality bar:** concrete facts only — file paths, commit hashes, dates, amounts, exact next actions. "Made progress on the parser" is slop; "Parser handles nested arrays (src/parse.ts:88), fuzz test added, edge case X still open" is a record. Every line you write must be actionable or deletable by the next reader.

Each repo defines *where* facts live in `.claude/CLOSEOUT.md`. Your first move is always:

```
Locate the repo root (git rev-parse --show-toplevel, or the project directory), then read .claude/CLOSEOUT.md
```

- Config exists → go to **Closeout**.
- Config missing → do **Bootstrap** first, then continue into Closeout in the same run.

## Bootstrap (first run in a repo)

The config exists so closeouts are consistent across sessions and models — without it every closeout invents its own filing system and the docs drift into contradiction. Build it from what the repo already has, don't impose a structure:

1. **Scan the repo's existing docs** — README, CLAUDE.md, `docs/`, any top-level or domain `*.md`. Note what each one owns. Prefer mapping facts to files that already exist; propose new files only for fact types that clearly have no home (a session log usually needs creating).
2. **Draft the config** using the template in [references/CLOSEOUT-template.md](references/CLOSEOUT-template.md). The doc map is the heart of it: a table from "kind of fact that changed" to "file that owns it", specific to this repo's actual domains.
2b. **If this repo is registered in StevOS's sync registry** (`~/Documents/StevOS/os/sync/REGISTRY.yaml`), the state snapshot is **not optional**: it must exist at the exact path the registry names, in the shape the contract describes (`~/Documents/StevOS/os/sync/projects/README.md`). Renaming it later means updating that registry in the same session, or the vault's mirror silently freezes.
3. **Show the user the proposed doc map and ask for corrections** — they know which docs are load-bearing. If you're running unattended and can't ask, write your best guess and flag prominently in your final reply that the config is unreviewed.
4. Write it to `.claude/CLOSEOUT.md` and proceed to Closeout.

## Closeout

1. **Inventory the WHOLE conversation, not just the last thread.** List: decisions made, code/doc changes (what + why), statuses changed, blockers found or cleared, things created (files, accounts, PRs, spend), and **things the user still needs to run or do**. Two traps:
   - **Verbal rulings count.** Users decide in passing ("yeah let's go with option B", "feel free to merge", "skip that for now") — each is a real decision; capture it with the same weight as an explicit one.
   - **In-flight threads need a resume point.** For EVERY thread not fully closed, the docs must name: what it is · exact next action · who moves next (user / agent / external) · what it's waiting on · the owning doc. "X ongoing" is a defect; "X: waiting on API key from vendor, then run scripts/import.sh per docs/PIPELINE.md" is a handoff.

2. **Sync docs per the config's doc map — touched areas only, targeted edits, never full rewrites of files you didn't change.** If the config names a state/status file, keep it a snapshot of current truth (delete done items rather than marking them done); history belongs in the session log and git. If a fact has no owning file in the map, put it in the closest existing doc — never leave it only in chat — and propose a new doc-map row in your final reply.

3. **Staleness sweep (cheap, targeted — do not skip).** For each fact this session changed or invalidated (a date, a status, a plan, a number), grep the repo for the old value and fix every stale mention: `grep -rn "old value" --include="*.md" .` History/log files are exempt — they record what was true then. This is what keeps multiple docs from carrying conflicting state.

4. **Append the session log** at the path the config names, newest first, one dated entry: summary · decisions · changes · open threads with resume points · what the user needs to run. Use a real timestamp from the `date` command.

5. **Commit + push** per the config's git policy (default: `git add -A && git commit -m "<one-line session summary>"`, push if a remote exists). Respect any protected-branch rules in the config. Verify the push succeeded; if it fails, say so — never report a sync that didn't happen.

6. **Reply to the user**, 3–8 lines: done / changed in docs / **anything they need to run or decide**, each as an exact command or concrete action. If nothing needs them, say "Nothing needed from you."

## Rules

- Never write a secret value into any doc, log, or commit. If a secret was handled this session, record *where it lives* (e.g. "token in 1Password / .env, gitignored"), never the value.
- Contradiction between docs found mid-closeout? Fix the stale one and note it in the commit message.
- If the session did no real work in this repo (pure Q&A, exploration with nothing decided), say so and stop — do not manufacture a closeout.
- If the doc map itself proved wrong or incomplete this session, update `.claude/CLOSEOUT.md` as part of the closeout — the config is a living doc, maintained the same way.
- Not in a git repo at all? Sync the docs and session log anyway, skip the git steps, and tell the user there's no version control backing the record.
