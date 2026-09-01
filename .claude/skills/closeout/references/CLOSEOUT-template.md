# CLOSEOUT config template

Copy this structure into the repo's `.claude/CLOSEOUT.md`, filling every section with the repo's actual files and domains. Keep it under ~60 lines — it's read at the start of every closeout.

```markdown
# Closeout config — <repo name>

<One line: what this repo is and what its docs are for.>

## Doc map

Fact changed → file that owns it. If a fact matches no row, use the closest doc and propose a new row.

| Fact changed | Owning file |
|---|---|
| <e.g. Architecture / key flows> | <e.g. docs/ARCHITECTURE.md> |
| <e.g. Feature status / roadmap> | <e.g. docs/ROADMAP.md> |
| <e.g. Setup, commands, env> | <e.g. README.md> |
| <e.g. Open loops / todos> | <e.g. docs/OPEN_ITEMS.md> |

## State snapshot (optional — MANDATORY if this repo is in StevOS's sync registry)

<Path to a STATE.md-style file if this repo keeps one, plus its required sections. It holds current truth only — delete done items, keep it under ~55 lines. Omit this section only if the repo doesn't need one AND is not registered in `~/Documents/StevOS/os/sync/REGISTRY.yaml` — a registered repo must have this file at the exact path the registry names, per the contract in `~/Documents/StevOS/os/sync/projects/README.md`.>

## Session log

Path: <e.g. docs/SESSION_LOG.md>
Entry format: `## YYYY-MM-DD — <one-line summary>` then bullets: decisions · changes · open threads with resume points · user actions needed. Newest first.

## Git policy

- Commit: <e.g. commit all changes with a one-line session summary>
- Push: <e.g. push to origin / commit only, never push>
- Protected: <e.g. never force-push main; work happens on feature branches>

## Quality bar (repo-specific examples)

- Slop: "<vague example in this repo's domain>"
- Record: "<concrete example: file path, hash, exact next action>"

## Never

- <Repo-specific exclusions: gitignored secret dirs, generated files not to edit, docs owned by another repo, etc.>
```

Bootstrap guidance:

- Every row in the doc map should point at a file that exists or that you create during bootstrap with a stub header. A map row pointing at nothing sends the next closeout hunting.
- The session log is the one file nearly every repo lacks — create it with its first entry being this bootstrap session.
- Write the quality-bar examples in the repo's own domain (an iOS app's example mentions builds and simulators; a data pipeline's mentions runs and row counts). Generic examples don't calibrate anyone.
