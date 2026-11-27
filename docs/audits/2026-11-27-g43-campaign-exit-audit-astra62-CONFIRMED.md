*Filed verbatim by the director from /home/steven/jos-g50-exit-astra62.last.md (fresh gpt-6.2-astra @ high, frozen G43 §12 seat 7; read-only clone at 2a464e8dd63eb3850997200c40a55c808b3ae08e; brief docs/runs/2026-11-27-g50-exit-audit-brief.md.txt; 116,761 tokens).*

---

gpt-6.2-astra @ high  
JOS G43 CAMPAIGN EXIT AUDIT: CONFIRMED

| Scope | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | Verdict | m_ℓ |
|---|---|---|---|---|---|---|---|---|---|---|---|---:|
| Shared panel | ✓ | ✓ | ✓ | — | — | — | — | — | ✓ | ✓ | — | — |
| L1 | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | FAIL | 0 |
| L2 | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✓ | FAIL | 0 |
| L3 | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | FAIL | 0 |
| L4 | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | FAIL | 0 |
| L5 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS | 0 |
| L6 | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | FAIL | 0 |

**k = 1, k′ = 1, m = 0.** All 24 R = 3 batches fell short of at least one recovery criterion. MIXED is eligible for both disclosure sentences. S1 is false because `m > 0` is false. S2 is false because `m == 24` is false. The published sentence list is empty, as required. `libraries_not_met_with_a_batch_met` is 0.

```text
G43 LIBRARY 1 RECOVERY GATE: FAIL
G43 LIBRARY 2 RECOVERY GATE: FAIL
G43 LIBRARY 3 RECOVERY GATE: FAIL
G43 LIBRARY 4 RECOVERY GATE: FAIL
G43 LIBRARY 5 RECOVERY GATE: PASS
G43 LIBRARY 6 RECOVERY GATE: FAIL
G43 ACROSS-LIBRARY READING: MIXED (k = 1 of 6)
```

**§7.4 reading, reproduced verbatim**

> 1 of six independently drawn R = 12 candidate libraries passed the frozen G35-B arm-(i) recovery gate and 5 failed it, on byte-identical targets. On this target panel the gate verdict depended on which candidate library was drawn. This is a direct observation, not a statistical inference. Four-dimensional recovery under this gate is therefore not shown to be a property of the level R = 12 on this panel. The observed count is 1 of six. The library pass probability on this panel remains unknown. Failing libraries and their failed predicates: L1: P5 (beta=19/20, inoculation_day_offset=15/20, symptomatic_detection_probability=14/20, asymptomatic_detection_probability=18/20), P6 (11/20 joint hits); L2: P5 (beta=19/20, inoculation_day_offset=13/20, symptomatic_detection_probability=18/20, asymptomatic_detection_probability=15/20), P8 (beta=0/20, inoculation_day_offset=5/20, symptomatic_detection_probability=2/20, asymptomatic_detection_probability=1/20); L3: P5 (beta=18/20, inoculation_day_offset=14/20, symptomatic_detection_probability=17/20, asymptomatic_detection_probability=17/20); L4: P5 (beta=15/20, inoculation_day_offset=13/20, symptomatic_detection_probability=13/20, asymptomatic_detection_probability=13/20), P6 (10/20 joint hits), P8 (beta=0/20, inoculation_day_offset=5/20, symptomatic_detection_probability=1/20, asymptomatic_detection_probability=0/20); L6: P5 (beta=19/20, inoculation_day_offset=15/20, symptomatic_detection_probability=14/20, asymptomatic_detection_probability=18/20), P6 (11/20 joint hits), P8 (beta=0/20, inoculation_day_offset=5/20, symptomatic_detection_probability=1/20, asymptomatic_detection_probability=0/20). Smallest count margin among the passing libraries: 1 target(s). The G35-B arm-(i) PASS remains a screening result only.

**§7.11 status phrase**

```text
Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); G35-B: B FAIL, i PASS, ii FAIL, iii FAIL; G43: L1 FAIL, L2 FAIL, L3 FAIL, L4 FAIL, L5 PASS, L6 FAIL
```

**Discrepancies.** None. My independent standard-library calculation matched the sealed bundle on every predicate, verdict, reference evaluation, count and trigger. Both published copies of the reading matched the filled frozen template exactly. The repository recomputation also exited 0 and agreed.

**Observations**

1. **Integrity and software status.** `SHA256SUMS` covered all 45,804 other files exactly once. Every digest matched. The manifest’s own SHA-256 was `a8c51550490a1fdd956d7615fdd93408b558d19737efb0299e333711c104fdc3`, identical to the filed launch copy. All files and directories lacked write bits. The authoritative sealed summary and the external marker both reported software PASS, and the launch log recorded `execute rc=0`. [Manifest](/home/steven/jos-g43-campaign-20261127/bundle/SHA256SUMS) · [Campaign summary](/home/steven/jos-g43-campaign-20261127/bundle/campaign_summary.json) · [Launch log](/home/steven/jos-g50-campaign-20261127.log)
2. **Frozen inputs and provenance.** All five frozen inputs matched committed bytes. The predeclaration at `fc16adcb3f8817eb2630ae5a31cd0508990bebd2` had the specified SHA-256 `67c3c7c03c1ec0f6176e430098c702a913368de51a9e8793c145094255b71094`. All 94 tracked source/config digests matched merge `c0821180d73b258ad29fa5578b1fbf5643a4b8cb`. The scoped diff to audit HEAD `2a464e8dd63eb3850997200c40a55c808b3ae08e` was empty. I checked all 92 frozen seed positions, including the three pre-freeze replacements, their observation pairings and namespaces, M2/M3/M4 hashes, dates, fixed settings and the 625-cell Cartesian grid. Audit files changed: 0. [Seed ledger](/home/steven/jos-g43-campaign-20261127/bundle/seed_ledger.json)
3. **Shared panel.** Each of the 20 targets had 30 latent days, 34 observation dates and exactly 10 inoculation acquisitions. Local secondary counts ranged from 1,646 to 2,122, symptomatic reports from 758 to 972, asymptomatic reports from 141 to 224, and nonzero combined-report dates from 25 to 29. I rebuilt both daily channels from observation events. All four P3 checks passed independently from transmission events, daily compartment counts and population size, observation-event chronology, and daily latent incidence minus the observation-event count. [Target evidence](/home/steven/jos-g43-campaign-20261127/bundle/targets)
4. **Scoring and blinding.** All 450,000 independently recomputed objectives matched their retained values exactly. I recomputed profile minima, ties, identification, integer counts and exact `Decimal` errors and biases. L5 had 20/17/17/17 hits, 13 joint hits and 0/3/1/0 boundary selections. Each of the 720 blind records matched its file hash, estimate hash and shared target hash. The last blind-file modification was at 20:51:50.706 UTC, before the first retained truth file at 20:52:04.989 UTC. The merge source requires a successful read-back of every blind record before the first truth join. The bundle retains file-write ordering but no separate timestamp for an in-memory truth access. I obtained all six verdicts and the class without using descriptive results. [Read-back barrier](/home/steven/jos-g50-exit-ro/src/jersey_outbreak/g43_multilibrary.py:1527) · [First truth join](/home/steven/jos-g50-exit-ro/src/jersey_outbreak/g43_multilibrary.py:1610)
5. **Work and timing.** `campaign_summary.json.measured_work` is the only retained operational ledger. Shared, per-library and total counts each equalled §9. Totals were 92 builds, 1,820 latent calls, 45,020 transforms, 3,750 candidate cells, 75,000 gate and 375,000 descriptive loss evaluations, 120 gate and 600 descriptive blind records, and zero serosurvey samples. Independent enumeration found 20 target tables, 45,000 candidate tables and 625 scored rows in every blind record. Distinct seed/latent-tuple counts agreed with the ledger and all 1,820 latent runtime entries. Campaign wall time was 6,853.078370187985 seconds. All campaign timing disclosures came from `campaign_summary.json.disclosures`. [Campaign summary](/home/steven/jos-g43-campaign-20261127/bundle/campaign_summary.json)
6. **Language and independence.** The published spread label was `stochastic_replicate_variation`. I found no claim of calibration, validation or interval coverage. Sol held the owner and implementation seats. Opus held the director and implementation-review seats. This fresh Astra exit audit shares the OpenAI family with Sol and the model designation of the earlier Astra rival-design consult. The recorded substitutions field was `not applicable`.

**Lineage block** (copied verbatim into `campaign_summary.json` and the exit audit, kept apart from G43 results). SHA-256 values marked † were recomputed by this draft from committed bytes at HEAD `3e44979a6c87dfdc3d393527c4e3cf15c4070b9b` (`git show HEAD:<path> | sha256sum`). The others are carried from the frozen G35-B §1 and the CONFIRMED exit audit and were not recomputed here.

| Item | Value |
|---|---|
| Phase-0 verdict / audit | `phase0_verdict: FAIL` · `docs/audits/2026-09-24-phase0-exit-audit-sol-FAIL.md` |
| Phase-0 bundle `SHA256SUMS` digest | `72cd9a568598530923e08ce20b013d60eb7a3b26553b87c31685ad623f3faa80` |
| Phase-0 predeclaration SHA-256 | `ef67fe49903c3984ca98679eb0470878bc25523baca3bc23a63e4ae7d983a104` |
| Phase-0b verdict / audit | `phase0b_verdict: FAIL` · `docs/audits/2026-09-26-phase0b-exit-audit-sol-FAIL.md` |
| Phase-0b bundle `SHA256SUMS` digest | `a319c5557ffa77c56baebb8341b5fc2e1432f367bdb9d0b34169aa079659032a` |
| Phase-0b predeclaration SHA-256 | `ec8df64630dd50c83b0866a096fba4980453c34232d18114129587274f257451` |
| Ridge diagnostic SHA-256 (binding, committed bytes; G35-B clarification 1) | `8cf4c76612434cbd90c5de4ca9dfd1326422b94a72bd4a63ccff71e95f34908a` |
| G35-B predeclaration | `docs/research/v1_3/2026-10-22-g35b-predeclaration.md`, commit `3972190bd7cde523860fe303b41427c1c95c57eb`, SHA-256 † `2e8358abd9e275a5cf04a58b4ad76313c10964f2da06d46cd0f8a7190733216e` |
| G35-B owner ruling | `docs/research/v1_3/2026-10-22-g35b-owner-ruling-ACCEPTED.md`, SHA-256 † `f84738a9594312f3371f4bb469c5cfaafed265dc5d233ee34f1f0be564d99643` |
| G35-B clarification 1 / 2 | SHA-256 † `2b1d4a5ee6bbab965a32e2abcdc4d00cab769d7d994a015fcf3bf5b0df0346d5` / † `ccae8721871b78b22d84451202ff541cb5836f06f402e176fe97308e296215e0` |
| G35-B harness code SHA | `0c9c3711b4e1be3fa90e9ef7f1e8e883dbdb48d8`. `g35b_design_study.py` † `f133ff3af74395955ad01d8e7f70e8474a020c4addcfd26135ec1b586d3f27f0`; `g35b_constants.py` † `bc766a31ce85e57f824a48ea046adeb0efad148c26133c268ba5f78e5923c494`; `configs/calibration/v13_g35b_design_study.yaml` † `4259c45f01cf122521f6853dba5059415a0ca6317a02d3f883be18e3263105d0` |
| G35-B bundle | `/home/steven/jos-g35b-campaign-20261022T234254Z` (immutable, read-only), `SHA256SUMS` digest `e6649a4b32289ad32cec7862ed79ea75a5123d0231178bebf0db78f0fd54c8fc` |
| G35-B exit audit | `docs/audits/2026-11-19-g35b-campaign-exit-audit-opus-CONFIRMED.md`, last changed at commit `141295f`, SHA-256 † `cf758f26a50986f04c7549ffbb855387d515230739f4f0cd9a27372bec617595`; verdict `JOS G35-B CAMPAIGN EXIT AUDIT: CONFIRMED` |
| G35-B results (final) | B FAIL (P5, P8), i PASS, ii FAIL (P5, P6), iii FAIL (P5, P8) |
| G35-B arm-(i) counts | hits beta/offset/sym/asym 10/8/8/10; joint 6/10; boundary 0/2/0/0; four-batch offset agreement 0/10 (descriptive). Four counts sit exactly at their inclusive thresholds (exit audit O5) |
| G41 rejected draft | `docs/research/v1_3/2026-11-19-g41-confirmatory-design-opus-DRAFT.md`, commit `e8a2401`, SHA-256 † `d46c46a92790934bd9dd19b31e619c2dae016a4ebe8036a8aa2306bd357c033e`. Never frozen; its seed series were never built |
| G41 owner ruling | `docs/research/v1_3/2026-11-20-g41-owner-ruling.md`, SHA-256 † `211646270378a45c83f54ed72350c13b371a92472e5d108455d0b6a6e9c77d`; verdict `G41 OWNER RULING: REJECT`; §4 binds successors |
| G42 consults | `2026-11-20-g42-b2-consult-fable52.md` † `691b567d078f2062257b12029427c963352e622c0306f01f4f7c5664d146fd73`; `…-astra62.md` † `361f7f015e707c52f75f07cbd65f0b3799cc25a13c65884076c753be37e38ab9`; `…-sol62.md` † `58c075a467e00026b761060c82aa6c524e800fc693fd2075fece9304cebf57b6`; `…-comparison.md` † `30896351a8114431ad33d8ad5bcabee10e80174ca5c3b28f5ef507df82208de1` (all in `docs/research/v1_3/`, commit `47e90bd`) |
| G42 / G43 resolutions | G42 = B2, Steven, chat, 2026-11-20 (trail row `g42-B2`). G43 = F, director under Steven's delegation, 2026-11-20 (trail row `g43-F`, commits `55c03c9`, `3e44979`) |
| Owner ruling on this draft | `docs/research/v1_3/2026-11-20-g43-owner-ruling.md`, commit `f2062d524c53a52d16837c2c7fe2ca8be6715510`, committed-bytes SHA-256 `ba442e94e4791d9c0a502d4656e580c591c4eed2c8ece50fbaecd6a655cd117c`; gpt-6.2-sol @ high; verdict `G43 OWNER RULING: ACCEPT WITH AMENDMENTS`; no substitution under §12 |