# Closeout config — jsy_disease_sim

Contract: a cold-start session must be able to resume from the repo docs
alone. Facts live where this map says; the session log carries history.

## Doc map

| Kind of fact | Owning file |
| --- | --- |
| Current milestone status, repo overview, quick start | `README.md` |
| Quantitative milestone gate records (edit ONLY when a gate actually passes) | `docs/progress.md` |
| M9 API contract | `docs/api.md` |
| M10 UI/UX design, visual system, frontend decisions, API-gap punch list | `docs/m10_ui_design.md` |
| Frontend dev/run instructions, stack, structure | `frontend/README.md` |
| Scientific claim rules | `docs/scientific_scope.md` |
| Architecture boundaries | `docs/architecture.md` |
| Intervention runtime contract | `docs/interventions.md` |
| Session history (newest first) | `docs/session_log.md` |
| **Current frontier / next action / branch index** (the cold-start pointer) | `.claude/FRONTIER.md` — on branch `docs/frontier` |
| Director standing orders + encoded lessons (foreman) | `.claude/DIRECTOR.md` — `docs/frontier` |
| Decisions waiting on Steven (question · options · default) | `.claude/GATES.md` — `docs/frontier` |
| Decision trail (append-only TSV, one row per iteration) | `.claude/decisions.tsv` — `docs/frontier` |
| In-flight autonomous-run state + resume recipe | `.claude/RUN.md` — `docs/frontier` |
| Independent audit reports (immutable) | `docs/audits/` — `docs/frontier` |
| Executor reports, gate transcripts, comparison/delta notes | `docs/runs/` — `docs/frontier` |
| Cold-start handoff from the original Sol chat (deep history, conventions) | `docs/handoff/2026-08-31-sol-handoff.md` — `docs/frontier` |

## Rules

- Scientific-claim discipline is absolute: never write that a milestone
  gate passed unless the repo's verification actually ran; `docs/progress.md`
  is a gate ledger, not a diary.
- Design artifacts (interactive mockup, map treatments, design directions)
  are linked from `docs/m10_ui_design.md`; do not duplicate their content.
- Git: commit with a one-line summary, push to `origin` (private repo
  `stev004/jsy_disease_sim`). Feature work stays on its branch; merging to
  `main` is the user's call.
- **Foreman state layer (2026-08-31):** the `.claude/{FRONTIER,DIRECTOR,GATES,RUN}.md` + `decisions.tsv` files and `docs/{handoff,audits,runs}/` live on branch `docs/frontier` (kept off `main` during the V1.1 release so the release fast-forward stayed clean). `git config foreman.branch docs/frontier` is set; all state ops go through `~/.claude/skills/foreman/scripts/fm.sh` (`state|log|sync|exec`). **Folding `docs/frontier` into `main` is Steven's call** (additive docs only) — until then, a cold start on `main` must `git show docs/frontier:.claude/FRONTIER.md` or use `fm.sh state`.
- Release merges are SHA-first (see GATES G3 history): `git rev-parse HEAD` must equal the audited SHA before any tag.
- **Registered in the StevOS sync registry 2026-09-01** (`id: jsy-disease-sim`, state_file `.claude/FRONTIER.md`, also `docs/session_log.md`). The FRONTIER mirror stays empty until the fold above happens.
