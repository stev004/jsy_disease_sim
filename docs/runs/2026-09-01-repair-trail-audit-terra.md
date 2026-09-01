The repair code trail is coherent: `e502ebf` descends directly from the blocked SHA through four bounded commits; the 33-file diff contains no core scientific-mechanism change (only travel diagnostics). The regenerated evidence is present: all 38 manifest records are relative, present, and hash/size-valid; its M7/M5 manifests carry `e502ebf` and the claimed identity hashes.

## ATTENTION-FLAGS

- **B04 is not fully closed.** Final `docs/frontier/.claude/GATES.md` still lists G6 as **Open** with “hold until Steven says go,” despite the approved, completed run. `FRONTIER.md` also retains “currently NO releasable SHA / branch to create at R0” alongside release-ready status. The re-audit missed this stale state contradiction.

- **Verification evidence is weaker than claimed.** The exact-SHA gate/re-audit reports cite ephemeral `/private/tmp` paths that no longer exist; no raw gate or re-audit transcript is retained. R4’s `run-console.log` proves the run occurred, but contains neither verifier nor relocation-verifier output. Current manifest integrity supports the result, but not the claimed execution records.

- **Release README link will be dead after the prescribed fast-forward.** Candidate README links relatively to `.claude/FRONTIER.md`, but that file and the audit records live only on the separate `docs/frontier` lineage; G3 fast-forwards only `e502ebf` into `main`.

- **Known accepted debt:** `travel.py:3099` still sets an ensemble-summary status to unconditional `"passed"`. The re-auditor reasonably scoped it non-blocking, but it remains a misleading status pattern and should not be forgotten in V1.2.