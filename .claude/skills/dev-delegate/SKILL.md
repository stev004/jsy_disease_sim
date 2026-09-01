---
name: dev-delegate
description: The engineering pipeline for any project OUTSIDE the Regulate space — assess whether a change is worth making, spec it, delegate implementation to Codex in an isolated worktree, review against shell-checkable criteria, and hand the user a ready-to-merge branch. Use for any bug fix, feature, or refactor request in personal/side projects (ClaudePet, DevDock, new experiments, client work). For anything Regulate (app, web, hivemind) use /dev-team instead — that team has its own routing, logs, and approval queue.
---

# Dev Delegate — spec → delegate → review → hand off

You are the **orchestrator**. You spec, consult, and review; **Codex implements. You never implement large changes yourself** — a one-line obvious fix is fine to do directly, anything more goes through the pipeline. The value of the split: the spec forces clarity before code, the worktree isolates risk, and review by a different pair of eyes catches what the implementer can't see.

## Repo config — read first, bootstrap if missing

Read `<repo>/.claude/DEVTEAM.md`. It defines: **gates** (the commands that must pass — build/typecheck/lint/test), **merge policy** (default: you push the branch, the user merges), **protected branches**, **no-touch paths** (secrets, generated files, vendored code), and any repo quirks Codex must be told. If it's missing, infer gates from the repo (package.json scripts, Makefile, pyproject, CI config), draft the file, show the user the gates you inferred, and write it — like `/closeout`'s bootstrap, this makes every future job consistent. Also read the repo's `CLAUDE.md` and any architecture/context doc it points to — no agent works from memory of a repo.

Also read [LESSONS.md](LESSONS.md) in this skill's directory — cross-project pipeline lessons; they are binding rules, not suggestions.

## The loop

1. **Assess (every request, before any code).** Two to five lines, honestly argued: value × effort × risk × does-it-fit-what-this-project-is-for. Verdicts: **do-now · do-later (note it in the repo's todo/roadmap doc) · won't-do (say why) · needs-user** (scope, taste, money). Personal projects don't need a committee — but writing the verdict down is what stops scope creep and half-motivated features. Only **do-now** proceeds.

2. **Spec.** Tight and self-contained — Codex sees nothing but this text plus the worktree, so quote any context it needs (relevant code, patterns to follow, constraints). Include: what/why, exact files if known, what NOT to touch (always include the config's no-touch paths), acceptance criteria, and `Risk: low | high` (high = auth, data persistence, payments, native config, anything user-visible-in-production; high risk demands an end-to-end verification before handoff, not just green gates). **Acceptance criteria are shell-checkable — adjectives are banned.** Every non-visual criterion is a command that exits 0 (a compile, a test, a grep, a curl). Visual criteria get a fresh-evidence check in review instead (new screenshot, not the one from earlier). Ambiguity in = garbage out.
   **Failing-test-first (logic/non-visual bugs):** where the repo has a test runner, acceptance criterion #1 for any reproducible bug is a test that FAILS on the default branch and PASSES on the branch — that is the proof the *cause* was fixed and not the symptom, and it satisfies the standing-check rule (step 7a) for free. Where the repo has no test runner yet, spec an exact manual reproduction-and-verification recipe instead.
   **Dependency gate:** if the change needs a new package, the spec names it and justifies it (what the existing stack can't already do). **Codex may not add dependencies the spec didn't name** — an unnamed package in a lockfile diff fails review outright.

3. **Worktree — isolate every job, branch from fresh default-branch.**
   ```
   git -C <repo> fetch origin
   git -C <repo> worktree add /tmp/<reponame>-<slug>-wt -b <type>/<slug> origin/<default-branch>
   ```
   (`<type>` = feature/fix/refactor.) Parallel jobs get parallel worktrees. Untracked files (`.env`, local configs) do NOT carry into worktrees — Codex implements without them, by design; if a gate genuinely needs one, copy it in AFTER Codex's run finishes and verify `git status` shows it unstaged before any push.

4. **Delegate to Codex.** Routing (update this block when the fleet changes — routing here is intentionally independent of Regulate's MODEL_ROUTING.md; review this block whenever the fleet routing changes; Regulate moved to luna@max 08-04; orchestrator/consultant seat = Fable 5.1 by default since 09-01 — if you are not Fable, taste/design/architecture calls go to a `model: "fable"` subagent): **gpt-5.6-luna @ high** is the implementation workhorse — `medium` for mechanical renames/boilerplate, `xhigh` for geometry/animation/algorithm-heavy work. **gpt-5.6-sol @ high** is the peer engineering consultant and escalation tier. **gpt-5.6-terra** = second opinion only.
   > **Known-good invocation:** `cd <worktree> && codex exec --sandbox workspace-write -m gpt-5.6-luna -c model_reasoning_effort="high" "<spec>" < /dev/null`
   > `--sandbox workspace-write` is REQUIRED — without it the run is silently read-only: no error, no diff. `< /dev/null` is REQUIRED for any non-interactive launch — with piped stdin, codex blocks forever on "Reading additional input from stdin…". Codex **cannot git-commit in worktrees**; committing is yours.
   > **Watchdog:** zero file writes after ~20 minutes = wedged. Kill and relaunch (a killed zero-write wedge doesn't count against the run budget).

5. **Review — this is where real bugs die.** Read the **full diff**, not a summary.
   **Scope check first.** Every hunk must trace to the spec or an acceptance criterion. Unrequested refactors, reformatting, renamed variables and "improved" adjacent code are review **FAILURES** sent back for removal — not merged as a bonus. A `package.json`/lockfile diff adding a package the spec didn't name fails outright.
   **Then scan for the four named failure modes:** *Kitchen Sink* (restructuring beyond the task) · *Wrong Abstraction* (abstracting on first use) · *Optimistic Path* (error and edge paths ignored) · *Runaway Refactor* (the fix cascading across files).
   Run the config's gates, then run every non-visual acceptance criterion as one block of commands — a criterion nobody ran is a criterion that didn't pass. Check the test diff specifically: reject any weakening of existing assertions done merely to get green. Failure → send Codex the original spec + current diff + the exact failing output + your finding (a fresh CLI run has no memory — always re-brief in full). **Escalation order = effort before model:** retry ≤2 at same seat/effort → raise effort one notch (luna@high → xhigh) → then escalate one model (→ sol@high). After the same substantive failure repeats once, do NOT retry unchanged — the spec is the problem; revise it.

5b. **Re-verify — triggered by the surface that changed, not by every job.** If the change touched pixels, layout, geometry, animation, timing or haptics, one review pass is not enough: do a second, independent check of every acceptance criterion against **fresh evidence** (a new screenshot or recording, not the one from step 5), frame-by-frame where motion is involved. Keep the proof file — it goes in the handoff. Non-visual logic changes skip this; their gate is the failing-test-first criterion.

6. **Budget.** Max **3 implementation runs** and **2 peer consults** per job unless the user extends. Consults fire on behavior, not vibes: two failed attempts the same way, or a review round repeating a finding. For engineering judgment, consult Sol: `codex exec -m gpt-5.6-sol -c model_reasoning_effort="high" "<self-contained brief>" < /dev/null` — Sol can't see your session, so quote the code, options, and constraints. Budget exhausted and not green = spec problem — stop and report honestly.

7. **Commit, push, hand off.** Commit in the worktree with a clear message, push the branch. If the default branch moved since you branched, merge it in, resolve, and **rerun the gates after integrating** — reviewed-code ≠ merged-code. Never merge to a protected branch yourself unless the config or the user in this chat explicitly allows it. If the repo has CI, confirm it's green **on the pushed SHA** — "pending" is not "green". **Never delete a remote branch while its PR is open** — deleting the head closes the PR. Then report: what changed, evidence the criteria pass, and the exact merge command, e.g. `git -C <repo> merge --no-ff fix/<slug> && git -C <repo> push`. End the report with one disposition line: done (branch pushed, gates green) | blocked (budget exhausted/needs-user) | nothing-to-do (verdict wasn't do-now) | error. Clean up: `git -C <repo> worktree remove /tmp/<...>-wt` once pushed.

7a. **Leave a standing check (every fix).** A goal verified once is an assumption with a timestamp. Every fix leaves behind either a **regression test** (preferred — CI re-runs it forever) or, for visual/feel fixes a test can't hold, its **verification recipe written into the repo** (the todo/QA doc, or `.claude/DEVTEAM.md`) so the next pass re-runs it. A fix with neither is not done.

8. **Learn (every job something went sideways).** If anything was caught after implementation — a review-round defect, a spec ambiguity Codex tripped on, a wedge, an escalation — distill each into ONE line in this skill's [LESSONS.md](LESSONS.md) (`symptom → root cause → RULE`). Repo-specific quirks go in that repo's `.claude/DEVTEAM.md` instead. Nothing caught = write nothing. When a lesson bites a second time, promote it into this SKILL.md at the step where it applies.

## Rules

- Never let Codex touch secrets, `.env` files, credentials, or the config's no-touch paths — and never write a secret value into a spec, log, or commit.
- Every acceptance criterion must be falsifiable and name its evidence — a grep that can't fail is not a check. Never hand off past a failing gate: a red check is a finding, not an obstacle.
- One request may be several jobs — split into parallel worktrees rather than one mega-spec.
- If the request is really a design/product question in disguise ("should this app…?"), answer it as orchestrator first, build second.
- Keep specs stable-prefix for prompt caching: no timestamps or run-ids at the top.
- Requires: Codex CLI (`/opt/homebrew/bin/codex`, auth in `~/.codex`). Invocable from any directory — resolve the target repo first; if ambiguous, ask once.
