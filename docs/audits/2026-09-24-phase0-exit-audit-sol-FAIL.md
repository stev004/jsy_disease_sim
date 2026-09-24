JOS V1.3 PHASE-0 EXIT GATE: FAIL

The failure is determinate: **P0-1 selects inoculation day offset at a grid boundary for 2 of 5 targets**, exceeding the frozen maximum of 1 of 5. The published FAIL agrees with independent recomputation. No threshold was changed.

| Arm | Published software / scientific status | Recomputed software / scientific status |
|---|---|---|
| P0-1 recovery | PASS / FAIL | PASS / **FAIL** |
| P0-2A wrong delay | PASS / PASS | PASS / PASS |
| P0-2B wrong ascertainment | PASS / PASS | PASS / PASS |
| P0-3 negative control | PASS / PASS | PASS / PASS |

### Findings by severity

- **Gate blocking, scientific:** P0-1 selected offset `0` for seed `42001` and `4` for `42005`; both are boundaries of `[0, 2, 4]`. Its boundary rate is **2/5**, above **1/5**. All other checked P0-1 aggregate predicates passed. Zero mean bias and 5/5 descriptive tolerance hits do not override this separate predicate.
- **Published-status discrepancies:** None.
- **Evidence limitation:** The 15 retained blind records, their hashes, and the reviewed code path support persistence and read-back before truth evaluation. The [manifest](/home/steven/jos-phase0-campaign-20260924T030959Z/bundle/blind_estimate_manifest.json) correctly says runtime event order and timestamps were **not recorded**. Latent-call and build totals rely on retained measured counters and provenance; observed-table counts can be checked directly.

### Recomputation evidence

`sha256sum -c SHA256SUMS` passed for **all 632 listed files**; the checksum file’s digest is `72cd9a568598530923e08ce20b013d60eb7a3b26553b87c31685ad623f3faa80`. All **64** [input hashes](/home/steven/jos-phase0-campaign-20260924T030959Z/bundle/input_hashes.json) match the clone or retained controls. The config, predeclaration, and G29 digests match the frozen values; the [seed ledger](/home/steven/jos-phase0-campaign-20260924T030959Z/bundle/seed_ledger.json) contains exactly the declared five target and three disjoint candidate seed pairs. The config declares zero retries and no replacement seeds; the ledger and campaign log show no replacement.

Independent arithmetic from the 599 retained observed tables reproduced **all 990 published objective values**: 405 P0-1, 405 P0-2A, 135 P0-2B, and 45 P0-3. The tables substantiate 599 transforms; [measured work](/home/steven/jos-phase0-campaign-20260924T030959Z/bundle/campaign_summary.json) reports **198 cells, 59 latent calls, 599 transforms, eight builds, `ci` mode, and 30 days**.

For P0-1, each target had a unique global minimum and all four profiles met the 5% identification rule. The selected offsets were **`0, 2, 2, 2, 4`**; minima were **`0.466815, 0.227230, 0.258376, 0.235586, 0.932256`**. Every dimension had **5/5** descriptive tolerance hits, joint hits were **5/5**, and all four mean biases were **zero**. Raw [truth diagnostics](/home/steven/jos-phase0-campaign-20260924T030959Z/bundle/p0_1_truth_diagnostics.json) showed ten acquisitions per target, 1,717–2,093 secondary infections, reports in both channels, 26–29 nonzero report dates, and passing chronology and conservation checks. The boundary predicate alone failed.

For P0-2A, recomputed \(R_i\) values were **2.730, 7.491, 7.246, 9.610, 3.050**. For P0-2B they were **1.864, 4.188, 3.524, 4.662, 1.034**, with \(E_i\) **0.848, 0.848, 1.029, 1.275, 1.461**. Every target in both arms is **TRUE** under G29: **D=5, U=0, [D,D+U]=[5,5]**. No tied minimum required an UNKNOWN ruling.

For P0-3, every factor’s beta argmin was **`0.16` at `0.5`, `0.08` at `1.0`, and `0.04` at `2.0`**, giving shifts **`+0.08, 0, −0.04`**. All three 204-element ridge vectors agreed exactly; objective spread was **0** for each target, and their target-independent prediction hash was identical. The six predicates passed, classification was `NON_IDENTIFIED_STRUCTURAL`, and `factor_estimate` was null with no precision fields.

### Phase 1 and attestation

Preparatory era and holdout synthesis can be developed as a written, model-owner-ruled specification. This verdict **does not license fitting real Jersey data**, treating these dimensions as having passed synthetic recovery, or advancing a Jersey calibration driver on that premise. If a later joint cases/tests/positivity/serology objective materially differs, the declaration also requires a new deterministic fixture and synthetic-recovery check before real fitting. These five-seed hit rates are descriptive, not confidence intervals; this is neither Jersey calibration nor named-pathogen validation.

Audited immutable bundle at the digest above against clone **`925838ac0077dbc66243cc4934aa1eb5c5b67b04`**. The clone remained clean. Audit arithmetic was written only under `/tmp`; no bundle or clone edits, simulations, observations, commits, or pushes were made.