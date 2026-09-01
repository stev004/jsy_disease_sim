# Dev-delegate lessons — cross-project pipeline rules

Binding rules distilled from failures. Format: `date · symptom → root cause → RULE`. One line each, newest first. When one bites twice, promote it into SKILL.md at the step where it applies and tag it `[GRADUATED]`.

Seeded from the Regulate dev-team's history (these already graduated there):

- 2026-07-15 · codex run produced no diff and no error → launched without `--sandbox workspace-write`, silently read-only → RULE: the sandbox flag is part of the invocation, never optional. [GRADUATED — step 4]
- 2026-07-15 · codex hung forever on "Reading additional input from stdin…" → non-interactive launch with piped stdin → RULE: always `< /dev/null`. [GRADUATED — step 4]
- 2026-07-11 · 9-hour codex hang, zero writes → wedged run left unattended → RULE: zero file writes after ~20 min = kill and relaunch. [GRADUATED — step 4]
- 2026-07-11 · build shipped empty env keys → untracked `.env` doesn't carry into worktrees → RULE: Codex implements without env files; copy in only for reviewer-run verification, never stage. [GRADUATED — step 3]
- 2026-07-13 · user met a red conflicts banner on a "ready" branch → default branch moved after review → RULE: integrate origin/<default> and rerun gates before handing off. [GRADUATED — step 7]
- 2026-07-09 · `position:relative` bug survived implementation, died in review → implementer can't see own blind spots → RULE: reviewer reads the FULL diff, always. [GRADUATED — step 5]
