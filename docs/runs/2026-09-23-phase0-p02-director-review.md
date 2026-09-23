# P0-2 director implementation review: KEEP (pending mirror + Sol review)

This is an implementation acceptance, not a scientific Phase-0 verdict. No campaign arm has run.

- **Candidate:** `4df879d2f4357614148f6932e22e0c80fe760025` on `codex/v13-p0-2-misspecification`. The parent is the reviewed P0-1 head `367f0324685437c4d2ed4aa0ae4878229da09839`. The director committed it; it is not pushed.
- **Executor:** gpt-6-luna @ xhigh, attempt 1 of 3, session `01a0d04e-13bb-7781-9ff1-5cb59232440a`, **475,035 tokens**, finished in about 42 minutes against a 45-minute timebox. Report: `docs/runs/2026-09-23-phase0-p02-luna-report.md`. Evidence log: `...-p02-evidence.log`.
- **Scope:** three authorized files, +1378/−35. The YAML adds only the ruling path/hash, the declared `misspecification` block and `implemented_arms`. No protected module was touched.
- **File SHA-256:**
  - source `c8174bdada2f0792fba9f581bd94aed561ed0f96a19d025e8ccd4d5298b2779d`
  - tests `420a8c2b01429c0be8d35cbb294e43ee2a02b283fa3631ae62c77a40381fd0f0`
  - config `299303df1899dc1dd04c367082ca469d385bf285e6b33d51937ff1a877d6b59b`

## Full source diff read, checked against the brief and the G29 ruling

- **Arms:**
  - P0-2A reuses the P0-1 81-cell grid and forces the observation `reporting_delay` to (0,). Seeds and the config id are unchanged, so the common-random-number namespace is unchanged.
  - P0-2B uses beta × inoculation × common probability (0.25/0.50/0.75), with symptomatic = asymptomatic, for 27 cells.
  - Transforms guarded before dispatch: 243 + 81. No latent calls; the arms reuse `candidate_latents`, which is now exposed on `P01CampaignResult`.
- **Ties:** P0-1 `fit_blind` (used for P0-2A) and the new `fit_p02_blind` (P0-2B) both return `selected=None` when more than one minimizer lies within tau = 1e-12·max(1, L_min). `evaluate_p02_target` rejects any mismatch between a selection and its tie record. On a tie every selected-candidate clause is None; R_i ≥ 0.25 still yields TRUE. Otherwise the state is UNKNOWN, with null estimates, errors and E_i. No tie-breaking rule exists anywhere in the code.
- **Formulas:**
  - R_i uses the max(L_correct, 1e-9) denominator.
  - E_i uses the mean of the three replicate channel totals of the selected wrong candidate and max(1, N_target). It compares with plain inclusive `>=` and no epsilon.
  - Tolerance clauses use the exact-decimal helpers from G30.
- **Aggregate:** fixed five targets and seeds are asserted. D ≥ k gives PASS, D+U < k gives FAIL, and anything else gives null with reason `indeterminate_tied_minima`. Overall P0-2 is PASS only when both arms pass; any FAIL makes it FAIL; otherwise it is indeterminate.
- **Blind boundary:** the estimate is persisted and its hash re-checked before `evaluate_p02_target` receives truth and the correct-arm minimum.
- **Provenance:** the ruling path and SHA-256 are frozen in the config. `--ruling` verification applies to dry-run, execute and the bundle, and execute and the bundle refuse to run without it. The bundle copies the ruling and writes `g29_ruling.sha256`, `p0_2_misspecification.csv` (nulls serialized as `null`), `p0_2_loss_surfaces.json` and `p0_2_provenance.json`, including per-replicate config, namespace and table hashes.

## Director probes (`docs/runs/2026-09-23-phase0-p02-director-probes.txt`)

- `dry-run --ruling` with the real accepted file reports `g29_ruling_verified: true`: implemented 189 cells / 32 latent calls / 572 transforms, planned 198 / 59 / 599.
- A tampered ruling is rejected with a SHA-256 mismatch (exit 1).
- `execute` with a verified ruling is still blocked on `p0_3` (exit 1), and no output directory is created.
- Focused Phase-0 suite: 38 passed.

## Points passed to the independent review (not defects)

1. **R_i/E_i boundary semantics.** R_i and E_i are compared with plain float inclusive `>=`, as the brief directed. Together with the open P0-1 profile-gap question, this is the all-arms review's question about how boundaries on computed quantities should behave.
2. **P0-1 input hashes.** `_p01_hash_config_payload` strips the G29 and misspecification metadata so that P0-1 input hashes stay equal to the accepted P0-1 hashes. P0-2 cell hashes use the same stripped declaration but include the actual per-replicate observation configs. Confirm that this cannot let two different arms collide.
3. **Error handling.** An arm failure raises an exception instead of recording `software_status=FAIL`. That is fail-closed, since no PASS can be produced, but it means an arm is never serialized with FAIL status.

## Next steps

Director clean-clone CI mirror at `4df879d`, then an independent gpt-6-sol @ high bounded review, then a push only after PASS, with an ls-remote receipt.
