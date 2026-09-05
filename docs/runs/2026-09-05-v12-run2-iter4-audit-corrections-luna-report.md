# V1.2 foreman run 2, iteration 4 — exit-gate audit-1 corrections: executor report (Codex gpt-5.6-luna@xhigh, fm.sh exec, 1 run, 2026-09-05 00:55→01:19 local)

*Verbatim `~/jos-v12-iter4.last.md`. Landed as `03ed6bc05961c199cb64a181a9bf98c4475122c9` on `feat/v12-denominators-dictionary` (after merging `origin/main` for the gate doc). Director gate: relocated build byte-identical, 25 focused + 9 golden-hash tests, ruff/mypy clean; Codex full suite 299 passed; M2 golden logical hash unchanged (`28a6d90a…`).*

Implemented the three findings without changing scientific identity.

Verification:

1. Relocated build: passed. `diff -rq /tmp/jos-it4-rebuild data/processed` output: empty.
2. Focused tests: `25 passed`.
3. Full suite: `299 passed, 5 warnings`.
4. Ruff: passed; 162 files formatted.
5. Mypy: `Success: no issues found in 15 source files`.
6. M2 hash:
   - CLI: `28a6d90a96454d11dcd6ad9d4531d69f9e4ec4396b802780084d3ae598c839a0`
   - Golden: `28a6d90a96454d11dcd6ad9d4531d69f9e4ec4396b802780084d3ae598c839a0`
7. Scope/status:
   - Raw diff count: `1`
   - Status exclusion count: `0`

The raw diff is the explicitly required fixture edit. Existing fixture fields changed only `geography` and `source_locator` across 44 rows; columns changed 12 → 13 by adding `source_id`.

`git diff --stat`:

```text
9 files changed, 181 insertions(+), 102 deletions(-)
```

No commit was created. The named audit file was absent from this checkout. Question: should criterion 7 exclude the explicitly required fixture file?