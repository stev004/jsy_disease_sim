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

## Rules

- Scientific-claim discipline is absolute: never write that a milestone
  gate passed unless the repo's verification actually ran; `docs/progress.md`
  is a gate ledger, not a diary.
- Design artifacts (interactive mockup, map treatments, design directions)
  are linked from `docs/m10_ui_design.md`; do not duplicate their content.
- Git: commit with a one-line summary, push to `origin` (private repo
  `stev004/jsy_disease_sim`). Feature work stays on its branch; merging to
  `main` is the user's call.
- Not registered in the StevOS sync registry (checked 2026-08-30).
