# G42-B2 consult panel — comparison (director note, NOT a ruling)

*Director: Claude Opus 5.5, 2026-11-20. Three independent consultants, one identical brief (`docs/runs/2026-11-20-g42-b2-consult-brief.md.txt`, main `6708ad2`), all at high effort, none saw the others. Reports filed verbatim: `2026-11-20-g42-b2-consult-fable52.md` (Claude Fable 5.2; 159,120 tokens), `2026-11-20-g42-b2-consult-astra62.md` (gpt-6.2-astra; 76,404), `2026-11-20-g42-b2-consult-sol62.md` (gpt-6.2-sol; 116,238). No provider classifier stopped any consult. This note summarises; it chooses nothing.*

## Headline

There are **two designs, not three**. Astra 6.2 and Sol 6.2 converged independently, almost number for number, on a **reliability test**. Fable 5.2 proposed a **descriptive draw-sensitivity study**. The split is over what question the study answers.

## Side by side

| Item | Fable 5.2 | Astra 6.2 | Sol 6.2 |
|---|---|---|---|
| Question | Does the verdict depend on which library was drawn? (all / some / none) | Is the library pass probability on this panel above 0.80? | Same as Astra ("conditional gate reliability") |
| Libraries L | **6** (range 5–8) | **22** | **22** |
| Targets N | 20, shared, fraction-preserving (16/12/≤4) | 20, shared, same thresholds | 20, shared, same thresholds |
| Per-library gate | Frozen P1–P10 unchanged | Same | Same |
| Across-library rule | No study-level gate. Classes: CONSISTENT-PASS (k = L), MIXED, CONSISTENT-FAIL (k = 0), NO-READING. Rejects any k-of-L cut as an invented number. | Exact binomial at 0.80, ≤ 5% each way: **21–22 Yes · 14–20 Can't tell · 0–13 No** | Identical table and tail values to Astra |
| New threshold introduced? | None (says this is its point) | Yes: 0.80 reliability + 5% error + one-exception allowance (flagged as owner's judgment) | Yes: same three choices, same flag |
| How L was chosen | Smallest L where a coin-flip design (π = 0.5) looks unanimous ≤ ~3% (2·0.5^L) | Smallest L tolerating one failure with ≤ 5% false "yes" at p = 0.80 | Same derivation as Astra |
| Chance of a positive reading if the true pass rate is 0.9 | Unanimity at L = 6: 0.53 (MIXED 47%) | 0.339 | ~0.34 (0.70 at 0.95) |
| R = 3 reference | 24 batches, descriptive; two integer-triggered disclosure sentences (4k ≤ m; m = 4L) | 88 batches, descriptive only, paired with parents | 88 batches, descriptive only |
| Extras | Pooled R = 72 reference (descriptive; flags as possible scope creep); target-block descriptive | Target × library matrix of joint hits and offsets | Same matrix; notes R can shift the *expected* loss ordering, not just scatter |
| Common-cause failure (e.g. a target fails P2) | NO-READING class | Frozen wording: shared target forced every verdict | "Can't tell about library dependence" |
| Builds / latent / transforms | 92 / 1,820 / 45,020 | 284 / 6,620 / 165,020 | 284 / 6,620 / 165,020 |
| Wall time (exploratory estimate) | ~2 h | ~7 h serial | ~7 h serial |
| Bundle (estimate) | 0.5–0.8 GB | not given | a few GiB |
| Should it run? | Yes, but says STOP is equally defensible if only CONSISTENT-PASS would change Steven's mind | Yes; owner must accept the wide inconclusive band | Yes; settle panel-generalisation needs first |

## Where all three agree

- One fresh target panel, N = 20, byte-shared across all libraries; the frozen arm-(i) gate unchanged per library at fraction-preserving thresholds.
- Libraries fully independent (fresh process and observation seeds, four fixed batches of three), seed pools disjoint from all earlier sets including the never-built G41 series; builds-only pre-check after the ruling commit; per-library reserves.
- R = 3 batches descriptive only, never a second gate.
- No pooled recovery gate, no best-library selection, no re-partitioning, no early stopping, one fixed campaign.
- Retain target latent truth so the exit audit can recompute P2/P3 (fixes O4).
- New standalone module reusing the G35-B scoring functions; real-data fitting stays STOPPED; readings conditional on this one panel.

## The real decision

1. **Which question.** Fable: "can the draw flip the verdict?" — answerable cheaply and without a new threshold, but a CONSISTENT-PASS at L = 6 cannot rule out a 20–30% library failure rate. Astra/Sol: "is recovery reliable at ≥ 80%?" — a stronger claim, but it introduces a new study-level standard (0.80, 5%) that the owner must rule, costs ~3.5× more compute, and is likely to land in "can't tell" unless the true rate is very high.
2. **Whether a new study-level threshold is acceptable.** Fable argues any k-of-L cut is an invented parameter (DIRECTOR hard rule territory); Astra/Sol argue it is an explicit, declared judgment authorised by Steven's B2 choice, which the owner ruling §5 said changes "same pass/fail rules" at study level.
3. **Seat note.** The owner seat has been Fable (5.1). Fable 5.2 is now a consultant on this design; if the owner ruling also goes to a Fable model, that should be disclosed, or the ruling routed to a different seat.
