TRAIL AUDIT: ATTENTION

- Live handoff wording is stale: [RUN.md](/home/steven/jos-g30-trail-readonly/.claude/RUN.md:1) says “G30 correction preparing,” and the current plan says the already-completed extension “is released for one Luna correction and one Sol review” at [v13 plan](/home/steven/jos-g30-trail-readonly/docs/research/v1_3/2026-09-21-v13-plan.md:16). Both contradict their own recorded G30 outcome and could invite an unauthorized retry. Update them to state the extension is complete/spent and the next stop is G29 HOLD.

Corroborated:

- Authorization was exactly one extra Luna attempt and one Sol review; both spent. The Luna interruption is transparent: 25-minute cap exceeded, no final report or token tally; worker tokens remain unknown, not zero.
- All resumed G30 trail rows 283–289 have seven columns; retained cited files and both cited commit objects resolve.
- Candidate is `367f0324685437c4d2ed4aa0ae4878229da09839`, parent `b5ef032…`; scope is exactly `phase0_campaign.py` and `test_phase0_campaign.py`, 168 insertions/15 deletions. Retained behavioral evidence is 5 base failures versus 12 candidate passes.
- Mirror evidence precedes review and push: raw exact-SHA mirror is `1 failed, 443 passed, 4 skipped`, with the sole timing failure reproduced unchanged on base; remainder logged PASS at uv 0.11.30. This is a qualified local gate, not all-green proof.
- Sol review was filed before publication. The GitHub receipt records `https://github.com/stev004/jsy_disease_sim.git` and `367f… refs/heads/codex/v13-p01-numeric-fix`; this is valid publication evidence. Local `origin` is `/home/steven/jsy_disease_sim` and was not used as GitHub proof.
- The retained remote snapshot shows only prior runs at its capture time; it supports no new observed run then, not an assertion about later external activity. All 18 resumed state/candidate commits carry `[skip ci]`; the prior 12 unintended runs are disclosed.
- Main state has no `src`, `tests`, or `configs` changes from `3ff37348…`; candidate is not merged into state HEAD. Frozen predeclaration SHA-256 remains `ef67fe…104` and has the identical blob in base and candidate. G29 is correctly HOLD; no campaign, scientific PASS, or code merge is claimed.

Attestation: start/end `HEAD` = `8db15366d0ad5d0342f17a2a00cbe8bd16fbd564`; `git status --porcelain` was empty both times. No tests, builds, external actions, or edits were performed.