MODEL-OWNER CLARIFICATION (G35-B) 1: ISSUED

<!-- Filed verbatim by the director (Claude Opus 5.5) on 2026-10-22 (HTML entities decoded). Author: Fable 5.1 model-owner subagent under Steven's 2026-10-22 delegation, issued under condition 5 of docs/research/v1_3/2026-10-22-g35b-owner-ruling-ACCEPTED.md, in response to the gpt-6-astra trail audit docs/audits/2026-10-22-g35b-trail-audit-astra.md. The frozen predeclaration is unchanged. -->

**Authority.** Steven's 2026-10-22 delegation; condition 5 of `docs/research/v1_3/2026-10-22-g35b-owner-ruling-ACCEPTED.md`. Scope: the two inconsistencies found by the gpt-6-astra trail audit in the frozen predeclaration `docs/research/v1_3/2026-10-22-g35b-predeclaration.md` (commit `3972190bd7cde523860fe303b41427c1c95c57eb`, committed-bytes sha256 `2e8358abd9e275a5cf04a58b4ad76313c10964f2da06d46cd0f8a7190733216e`). The frozen file stays byte-unchanged. This ruling is interpretive only.

**Owner verification (read-only, performed before ruling).**
- `git show 3972190:docs/research/v1_3/2026-09-29-phase0b-ridge-diagnostic-EXPLORATORY.md | sha256sum` = `8cf4c76612434cbd90c5de4ca9dfd1326422b94a72bd4a63ccff71e95f34908a`.
- The same committed bytes with every line ending normalised to CRLF (`\r?\n` → `\r\n`) = `de13913b85afa3578f3fcea2e460448909132133a30735eb3cae2609780079d6`, identical to the Windows working copy (`core.autocrlf=true`). The two hashes therefore differ only by line endings; content is identical.
- The ridge diagnostic has not changed since it was filed (`f102a6d`); the frozen predeclaration hashes to the stated `2e8358ab…`.
- Frozen §10 (line 413) reads "…These are disclosures and never gate or subset, and measured counters."

**Item 1 — ridge-diagnostic lineage hash (§1 lineage table).**
(a) Authoritative reading: the §1 row identifies the ridge diagnostic by content, not by platform-specific bytes. The binding lineage digest is the committed-bytes SHA-256 `8cf4c76612434cbd90c5de4ca9dfd1326422b94a72bd4a63ccff71e95f34908a` (blob at `3972190`, path `docs/research/v1_3/2026-09-29-phase0b-ridge-diagnostic-EXPLORATORY.md`). The cited `de13913b…` is read as the CRLF working-copy rendering of the same content and is accepted as a non-binding alias of the same document, never as evidence of a different document.
(b) Changes no grid, threshold, seed, objective, level or predicate. The lineage table records provenance only; no parameter of the study is derived from it.
(c) U1 must: carry `8cf4c766…` as the binding ridge-diagnostic lineage digest; compute every SHA-256 it asserts (the frozen predeclaration's own `2e8358ab…` included) from committed bytes via `git show <sha>:<path>`, never from a working copy; record this ruling as the source of the corrected digest; and treat a mismatch of the committed-bytes digest (not of the CRLF alias) as the stop condition.

**Item 2 — §10 trailing clause after A10.**
(a) Authoritative reading: the A10 ruled text ends at "These are disclosures and never gate or subset." The residual ", and measured counters" is the draft's continuation, orphaned when the ruled sentence's period was merged into it. §10 is read as: "…plus per-target columns `population_fallback_m2` and `population_fallback_m3` (TRUE/FALSE from the build diagnostics), measured counters, and a per-arm descriptive count of fallback-built targets and candidates. These are disclosures and never gate or subset." The dangling clause adds no artefact, column, or obligation beyond "measured counters" as already present in the draft list; nothing in it gates, subsets, or feeds any predicate.
(b) Changes no grid, threshold, seed, objective, level or predicate. The disclosure-only status of all §10 per-arm outputs stands exactly as A10 ruled.
(c) U1 must: implement §10 per the reading in (a); emit the fallback columns, the measured counters and the descriptive count as disclosures only, with no code path that reads them into gating, subsetting, or predicate evaluation; and cite this ruling, not a re-punctuated predeclaration, wherever §10 is quoted.

**Standing.** Both items are clarifications under condition 5. The frozen predeclaration, its commit, its committed-bytes hash, and every grid, threshold, seed, objective, level and predicate in it remain in force unchanged. Any further inconsistency is a new stop under the same condition.
