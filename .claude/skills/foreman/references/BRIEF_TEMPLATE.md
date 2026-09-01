# Foreman brief template

Fill every field or rescope — a field you cannot fill is a unit you have not scoped. Collapse the whole thing to a paragraph for trivial one-command units. Executor sees ONLY this text plus the worktree: paste upstream results in full, quote the code it needs.

    ROLE: <who the executor is for this unit: implementer / independent auditor / researcher. Auditors: "implementation claims are things to verify, not evidence">
    GOAL: <one sentence, the outcome, executable by a stranger with no chat access>
    SCOPE: <exact worktree path + branch/SHA; paths it MAY touch; paths it may NOT>
    CONTEXT: <the defect/feature with file:line quotes; upstream reports pasted in full; which repo docs to read and their authority level>
    ACCEPTANCE: <shell-checkable criteria, one per line, adjectives banned. Logic bugs: criterion #1 = failing-test-first (fails on base, passes on branch, both directions demonstrated)>
    VERIFY: <exact commands, incl. env quirks (e.g. UV_CACHE_DIR=/tmp/... because the sandbox blocks the default cache)>
    TIMEBOX: <cap; on expiry return partial findings and stop. If the fix needs scope beyond SCOPE, STOP and report why — never expand>
    FORBIDDEN: <repo hard rules + no unnamed dependencies + no reformatting/renames/adjacent "improvements" + git commit (director commits) + unit-specific bans>
    REPORT: <what to print: changes+why, per-criterion evidence with actual command outputs, diff stat. Audits: findings with file:line, exact verdict line syntax>
    STANDING: <the repo's DIRECTOR.md hard-rules section, pasted verbatim>

Launch (backgrounded by the harness, log + clean final report):

    ~/.claude/skills/foreman/scripts/fm.sh exec <workdir> <model> <effort> <brief-file> <log-stem>

Model routing: implementation = gpt-5.6-luna @ xhigh (Steven's standing preference) · audit/research/consult = gpt-5.6-sol @ high · trail-audit = whichever family did neither the directing nor the work (typically gpt-5.6-terra). Read `<stem>.last.md` for the report; `<stem>.log` only when debugging the run itself.
