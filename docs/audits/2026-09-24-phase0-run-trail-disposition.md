# Disposition of the 2026-09-24 Phase-0 run trail audit (gpt-5.5)

Audit report: `docs/audits/2026-09-24-phase0-run-trail-audit-gpt55.md`. Verdict: `TRAIL AUDIT: ATTENTION (7 items)`. Auditor: gpt-5.5, Codex family, session `01a0d16e-5329-7163-baa9-60664086f53c`; the director was Claude. The auditor verified the following as clean: column counts and `[skip ci]` on every row; token columns against the log trailers; mirror PASS filed before each review launch; ls-remote receipts; `[skip ci]` on the pushed heads; the bundle digest; and a fair statement of G31.

| # | Sev | Item | Disposition |
|---|---|---|---|
| 1 | HIGH | P0-2 PASS filed in git after the push | **Acknowledged: deviation from the letter of the rule.** The Sol re-review PASS was durable on disk before the push: `/home/steven/jos-p02-rereview.last.md` mtime `2026-09-24T00:02:38Z`, push receipt `00:03:31Z`. The director read it and then pushed. It was committed to git in `7db68bcfb4b664ebb89c10d9f6d057a35258d94e` at `00:03:48Z`, 17 s after the push. The pushed SHA equals the reviewed SHA, so there is no integrity impact. New DIRECTOR lesson: file and commit the PASS before pushing. |
| 2 | HIGH | P0-3 PASS filed in git after the push | **Acknowledged, same pattern.** `/home/steven/jos-allarms-rereview2.last.md` mtime `03:09:29Z`; push `03:09:45Z`; committed in `c4cf3a1e58485399fa8b2620b0f966f097a2460f` at `03:10:53Z`. Same lesson. |
| 3 | MED | Campaign log copy cited but not tracked | **Fixed.** The file existed in the working tree, but the commit's glob `phase0-campaign-*` missed `phase0-campaign.log`. It is now committed in this disposition commit. The primary copy remains `/home/steven/jos-phase0-campaign.log`. |
| 4 | MED | Stale live state | **Fixed or explained.** The FRONTIER header "G29 pending" was a stale fragment and has been removed. The audit clone was taken before the `phase0-trail-audit-launch` row by design: the row is written 60 s after the launch, once the process is confirmed alive. That row exists as trail row 315. |
| 5 | MED | P0-3 retry-1 timebox drift undisclosed | **Acknowledged.** Launch `02:19:59` to report `03:02:55` BST is 42 m 56 s against a 40-minute cap, an overrun of about 3 minutes that the `phase0-p03-retry1-kept` row did not disclose. The worker finished with a full report; nothing was cut short. |
| 6 | LOW | Failed first launch of P0-3 retry 1 not durable | **Attested here.** The first detached launch (`/tmp/p03-r1-launch.sh`) exited before codex started, with no log and no session. Cause: its `git pull` raced the concurrent `aa-log2.sh` trail commit, and `set -e` aborted the script. The worktree was verified clean at `29f43d1` and the launch was repeated, giving session `01a0d0ff-68ee-78b1-840e-06b9c67a4d3d`. No executor work was lost, and no budget attempt was consumed by the aborted launch. RUN.md at `ba0638f` recorded this. A stale first watcher was ignored. |
| 7 | LOW | Abbreviated SHAs and a placeholder path in evidence cells | **Supplemented.** Full SHAs are below. The actual bundle path is `/home/steven/jos-phase0-campaign-20260924T030959Z/bundle`, which the `phase0-campaign-complete` row already cites. |

Full SHAs for the abbreviated filing commits:
- `f86eca0` = `f86eca050917cab3cf5e6f885377f6ef30d56ec6`
- `67e964b` = `67e964bd7a1ff36270a0bf6364f89cca8708b53e`
- `7ddbbe9` = `7ddbbe9ae8deaf674b440262c8f34d3df0509f91`
- `f9b819f` = `f9b819ff4f4b8b75081a3bb24fe14e49d1b5020a`
- `5eae3e1` = `5eae3e12f84ff2e82744c1656622f3dbaefc1c3b`

Also disclosed by the director and absent from the auditor's scope: the trail audit's own first launch aborted because it reused the stem `~/jos-phase0-trail` from the 2026-09-22 run. The guard prevented an overwrite, and the old files are untouched. It was relaunched as `~/jos-run0924-trail`, and a DIRECTOR lesson was encoded in `413db50`.
