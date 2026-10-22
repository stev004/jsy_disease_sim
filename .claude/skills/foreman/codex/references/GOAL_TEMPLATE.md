# /goal template for a foreman run

Paste as one message after cold-start. Fill every angle bracket; a bracket you cannot fill is a predicate you have not scoped.

    /goal <predicate: checkable end state, e.g. "V1.2 units E1-E4 merged to branch v12-evidence with verifier PASS at each head SHA">
    verified by <evidence: the exact commands or artifacts, e.g. "uv run pytest tests/v12 exits 0 at the branch head; docs/runs/<stem>.last.md filed per unit">
    while preserving <constraints: DIRECTOR.md hard rules; no protected-branch writes; no new dependencies unless a brief names them>.
    Budget: <N> iterations, 3 implementation runs and 2 consults per unit.
    Between iterations: re-read .claude/DIRECTOR.md, log one decisions.tsv row via fm.sh log, rewrite RUN.md, run the staleness sweep, fm.sh sync.
    Delegate implementation to gpt-6-luna at xhigh in fresh worktrees (Class: numerical units to gpt-6.1-sol at high; effort explicit on every launch); verify behavioral units with the verifier agent; never grade your own work.
    If blocked or no valid paths remain: stop, park the question in GATES.md with a default, and report the attempted paths, the evidence, and the input needed. Reaching the budget is not completion - say so.

Launch: `cd <repo> && codex -p astra`, then `$foreman`, then this goal. Controls while it runs: `/status` (session tokens) · `/goal` (view) · `/goal pause` · `/goal resume` · `/goal clear` · Enter to steer the current turn · Tab to queue for the next turn · `/agent` to inspect worker threads.
