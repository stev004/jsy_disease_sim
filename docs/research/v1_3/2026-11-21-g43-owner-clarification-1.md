*Filed verbatim by the director (Claude Opus 5.5) from the read-only Codex run: brief docs/runs/2026-11-21-g43-clarification1-brief.md.txt; clone HEAD 412e0c020427ff0bebdd230feb04f7c263a61499; gpt-6.2-sol @ high; 59,415 tokens; rc=0; session 01a20053-ab88-7f01-821f-946d678714ec. Everything below this line is the owner's text, unedited.*

---

gpt-6.2-sol @ high  
G43 OWNER CLARIFICATION 1: §7.3’s reporting sentence applies only to intact campaigns. A3 takes precedence for VOID.

This ruling applies to the frozen G43 predeclaration at `fc16adcb3f8817eb2630ae5a31cd0508990bebd2`. I verified its committed-bytes SHA-256 as `67c3c7c03c1ec0f6176e430098c702a913368de51a9e8793c145094255b71094`. The working-tree and staged diff stats were empty.

**§7.3, line 201**

> There is **no study-level gate, no study-level PASS/FAIL token and no k-of-L cut**. The study reports the six verdicts, k, and exactly one class word, selected by the first matching row.

**§7.3, line 203 (A3)**

> A campaign exception, an established departure from the declaration, or any false P1, P9 or P10 component makes the campaign VOID. A VOID campaign has no library verdict lines, counts `k`, `k′`, `m`, or `m_ℓ`, class, or reading. Seal the available evidence.

**§7.3, line 207, row 1 result**

> **VOID** (campaign status; no class, no reading)

Apply line 201’s first sentence universally and its second sentence only to intact campaigns. Check row 1 before selecting a class. For VOID, record the campaign status and cause, seal the available evidence, and omit the scientific outputs named in A3. For an intact campaign, select the first matching row among rows 2–5 and report all six verdicts, `k`, and the selected class. An intact shared P2 or P3 failure remains NO-READING with cause `shared_panel`, all failed target conditions, six FAIL verdicts, `k = 0`, and the declared descriptive counts.

**Other wording governed by the same precedence**

**§7.3, line 217, and §7.4, line 248**

> A library's count margin is reported (§7.9, D1) and cannot change the class.

> The R = 3 reference disclosure sentences (§7.8) are written after the reading under their own key.

Report margins in the intact scientific output. The ordering instruction applies when §7.8 emits a sentence. Available underlying evidence is retained on VOID.

**§7.8, lines 324 and 331**

> Both are reported beside k′, and each m_ℓ is shown beside its parent library's verdict.

> The count of libraries with `recovery_met_ℓ` false and m_ℓ ≥ 1 is reported as `libraries_not_met_with_a_batch_met`, without a sentence.

Both reporting instructions apply only to intact campaigns. Line 331 also governs the trigger bullets at lines 328–329. S1 and S2 are eligible only for CONSISTENT-PASS, MIXED and CONSISTENT-FAIL, in that order when both fire. NO-READING retains the counts and emits neither sentence. VOID emits neither sentence and reports none of these counts.

**§7.11, line 378, and §12, line 683**

> The G43 tokens are final only after the exit audit returns CONFIRMED; until then state files append "(exit audit pending)" outside the phrase.

> Only after CONFIRMED do the G43 tokens become final.

These finality clauses govern the six intact-campaign tokens. For a VOID campaign, use the line 376 suffix `; G43: VOID` once at campaign level. An audit finding VOID records VOID and its cause.

**§10, lines 631, 648, 649 and 652, and §12, line 683**

> It must let the exit audit recompute every predicate, every reference evaluation, k, k′, m and the class from raw tables with the Python standard library only.

> **`g43_across_library.json`:** the six verdicts, k, k′, m, every m_ℓ, the S1 and S2 trigger values, the class word, the NO-READING cause record if any, and the reading text.

> **`campaign_summary.json`:** the §1 lineage block; a `seats` block naming the implementer, the reviewer and any substitution under §12 with the stopped attempt's token count or `not applicable` (fixes O3); `software_status`; the six `scientific_status` values; the class and reading; the S1/S2 sentences under their own key; the status phrase; measured-versus-planned work; and the disclosures.

> The exit audit writes `G43 LIBRARY <1…6> RECOVERY GATE: PASS|FAIL` six times, then `G43 ACROSS-LIBRARY READING: CONSISTENT-PASS|MIXED|CONSISTENT-FAIL|NO-READING (k = <k> of 6)`, then the §7.4 reading and any §7.8 sentence.

> It recomputes every predicate, k, k′, m and the class from the raw bundle with the Python standard library only, checks the reading and the S1/S2 sentences against §7.4 and §7.8, confirms that no descriptive feeds a verdict, and returns `JOS G43 CAMPAIGN EXIT AUDIT: CONFIRMED | DISCREPANCY | VOID`.

Complete scientific output and full recomputation apply to the intact path. Seal available evidence on VOID and omit the across-library results payload and scientific summary fields from the VOID report. The auditor uses available evidence to establish or substantiate VOID and writes the audit verdict and cause. DISCREPANCY retains its §12 meaning for unresolved verification without an established departure.

I found no further inconsistency of this kind in the named sections.

**Standing.** This interpretive ruling is issued under §12, line 705. The frozen predeclaration stays byte-for-byte intact. This clarification changes no grid, threshold, seed, objective, level, predicate or reading class. Any further inconsistency is a new stop under the same provision.