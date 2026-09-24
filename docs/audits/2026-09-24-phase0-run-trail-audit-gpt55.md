TRAIL AUDIT: ATTENTION (7 items)

Auditor: Codex (GPT-5, Codex family).

1. **HIGH — `phase0-p02-accepted` — push ordering**
   Evidence: push receipt is `2026-09-24T00:03:31Z`; filing commit `7db68bc` containing the Sol PASS report and receipt is `2026-09-24T01:03:48+01:00` (`00:03:48Z`). Filed review PASS did not predate the push in git.
   Suggested reconciliation: file an erratum/disposition: either provide durable pre-push proof of the PASS, or acknowledge “review PASS before push, filing after push.”

2. **HIGH — `phase0-p03-accepted` — push ordering**
   Evidence: push receipt is `2026-09-24T03:09:45Z`; filing commit `c4cf3a1` containing the all-arms re-review 2 PASS and receipt is `2026-09-24T04:10:53+01:00` (`03:10:53Z`). Filed review PASS did not predate the push in git.
   Suggested reconciliation: same as above; encode that push gates require the PASS document filed before push if that remains the rule.

3. **MEDIUM — `phase0-campaign-complete` — missing filed log copy**
   Evidence: row and `RUN.md` cite `docs/runs/2026-09-24-phase0-campaign.log`, but it is absent from the clone and `git ls-files`. The WSL primary log exists at `/home/steven/jos-phase0-campaign.log`.
   Suggested reconciliation: file the campaign log copy or amend the evidence cell/state to cite only the retained WSL log plus the filed summary/SHA256SUMS.

4. **MEDIUM — state files — stale/contradictory live state**
   Evidence: `RUN.md` says “see trail row phase0-trail-audit-launch,” but `decisions.tsv` stops at `phase0-exit-FAIL` in this clone. `FRONTIER.md` header also still says “G29 pending” while later text and `GATES.md` correctly say G29 accepted.
   Suggested reconciliation: fix the stale state phrases after this audit is filed.

5. **MEDIUM — `phase0-p03-retry1-kept` — possible undisclosed timebox drift**
   Evidence: retry-1 brief says `TIMEBOX: 40 minutes`; launch/log mtimes run from `02:19:59` to `03:02:55` local, about 43 minutes, and the trail row does not disclose this. By contrast, P0-2 retry and P0-3 attempt 1 overruns are disclosed.
   Suggested reconciliation: document whether the true codex-start time makes this within cap, or acknowledge a small overrun.

6. **LOW — `phase0-allarms-BLOCKED` / P0-3 retry-1 launch — disclosed failed first launch not durable in trail**
   Evidence: I found only `/home/steven/jos-p0-3-r1-launch.log` and the successful log/session; the disclosed first detached launch death/stale waiter is not represented in rows 304–305 or a durable artifact I found.
   Suggested reconciliation: add a short attestation if this operational deviation matters for the record.

7. **LOW — multiple mirror-review rows — evidence hygiene**
   Evidence: evidence cells use abbreviated filing commits (`f86eca0`, `67e964b`, `7ddbbe9`, `f9b819f`, `5eae3e1`) despite the “full SHA” rule. They resolve locally, but are not full SHAs. Row `phase0-campaign-launch` also uses placeholder path `/home/steven/jos-phase0-campaign-<ts>/bundle`.
   Suggested reconciliation: replace or supplement with full 40-char SHAs and the actual bundle path once known.

Verified clean: rows 292–314 all have 7 columns and `[skip ci]`; all main candidate SHAs resolve; mirror PASS filings predate their review-launch rows; nonzero token columns match `tokens used` trailers in the WSL logs; G29 ruling and predeclaration hashes match; current `ls-remote` matches both pushed branch receipts; pushed head commits `ae88529` and `925838a` include `[skip ci]`; bundle `SHA256SUMS` digest matches `72cd9a56…`; G31 options/default HOLD are fairly stated and do not imply authorization.