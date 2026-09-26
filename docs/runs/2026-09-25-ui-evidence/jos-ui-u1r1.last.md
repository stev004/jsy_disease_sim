**PASS — the shell layout fix is in place.** The requested gates pass, and port 5199 remains available for the director’s visual re-check.

- [AppShell.tsx](/home/steven/jos-ui-u1-wt/frontend/src/app/AppShell.tsx): split the bar into four zones, moved the verbatim disclaimer below the brand, combined scenario name/kind/state into one chip, and added the “Current run” menu trigger below 1440px.
- [base.css](/home/steven/jos-ui-u1-wt/frontend/src/styles/base.css): set the 64px flex row, 20px horizontal padding and 16px zone gap; added shrink and truncation rules plus compact layouts. The existing ThemeProvider and token changes were left intact.

**Gates:** typecheck PASS; tests PASS (15 passed, 6 skipped); build PASS; disclaimer grep PASS; `git diff --check` PASS. Output is saved at [jos-ui-u1r1-evidence.log](/tmp/jos-ui-u1r1-evidence.log).

**Diff stat:** requested files: 2 changed, 241 insertions, 167 deletions. Full dirty worktree, including the kept U1 changes: 10 files changed, 509 insertions, 277 deletions. No browser screenshot check was run here; port 5199 returned HTTP 200.