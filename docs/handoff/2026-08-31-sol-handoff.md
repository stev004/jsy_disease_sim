# Jersey Outbreak Simulator (JOS) — Cold-Start Project Handoff

**Date:** 31 August 2026  
**Purpose:** Replace the current assistant/chat as the operational source of truth for the next agent.  
**Repository (Mac):** `/Users/stevenmatson/Documents/jsy_disease_sim`  
**Project:** Jersey Outbreak Simulator (JOS)  
**Current development tier:** **V1.1 scientific hardening — final independent release-candidate audit pending**  
**Frozen V1 release tag:** `jos-v1.0.0`  
**Frozen V1 release commit:** `9e9ce3abc4201cd8303c723015462d21ca237800`  
**Current V1.1 release-candidate commit:** `461bf0387f4bb91db216b783c19f947f8583b4b8`  
**Current V1.1 integration branch:** `codex/v1.1-integration`

---

# 0. Executive state summary

JOS V1.0 is **finished, independently audited, fast-forwarded to `main`, smoke-tested, and tagged `jos-v1.0.0`**. The exact V1 release commit is:

`9e9ce3abc4201cd8303c723015462d21ca237800`

A separate Claude Science review of the frozen V1 release produced three scientific documents:

- `docs/reports/JOS_V1_SCIENTIFIC_AUDIT.md`
- `docs/reports/JOS_V1_SCIENTIFIC_TECHNICAL_REPORT.md`
- `docs/reports/JOS_V1_SCIENTIFIC_ROADMAP.md`

Those reports concluded:

- 26 **VALIDATED / COHERENT** findings
- 57 **MINOR LIMITATIONS**
- 45 **MAJOR LIMITATIONS**
- 0 **SCIENTIFIC BLOCKERS**
- verdict: **SCIENTIFIC REVIEW: SUITABLE WITH MAJOR DISCLOSURES**

A full-population frozen-V1 scientific pilot was then executed on the user's Mac:

- 104,540 resident agents
- 180 simulated days
- seed 123
- scientific verification: **PASS**
- total wall time: ~9,959 s (~2 h 46 min)
- peak RSS: ~2.16 GiB
- local infection episodes: 294,555
- total infection episodes including seeds: 294,565
- unique ever infected: 99,041 (94.74%)
- peak daily local infections: 7,234 on 2025-02-03
- peak infectious: 28,479 (27.24%) on 2025-03-30
- final infectious: 20,380
- cumulative infection episodes per resident: 2.818
- trajectory showed recurrent waves / strong reinfection; the 180-day horizon did **not** reach extinction
- the pilot therefore demonstrated real full-scale execution and exposed V1 scientific limitations rather than behaving like a neat one-wave epidemic

The project then moved into a **parallel V1.1 scientific-hardening programme** based on the Claude Science audit and roadmap. Research lanes R1–R6, a correctness-foundation lane, a scientific design synthesis, and four implementation trains M11-A through M11-D were completed and integrated.

The current V1.1 candidate is:

`461bf0387f4bb91db216b783c19f947f8583b4b8`

It is implementation-verified but **has not yet received the final independent Sol audit**.

That is the exact frontier.

**Next action:** run a fresh GPT-5.6 Sol High independent audit of commit `461bf038...` from a clean detached worktree. Do **not** run the 180-day V1.1 baseline or merge/tag V1.1 until that audit passes.

---

# 1. Exact current frontier

## 1.1 Current milestone / tier

The project is no longer on the original M0–M10 build sequence. That sequence culminated in the frozen `jos-v1.0.0` release.

The current tier is:

> **V1.1 — scientific hardening**

The V1.1 implementation programme has reached:

> **Final release-candidate audit gate**

The intended V1.1 sequence is:

1. scientific audit of V1.0 — **DONE**
2. full-scale V1.0 pilot — **DONE**
3. parallel V1.1 research — **DONE**
4. correctness foundation — **DONE + verified**
5. scientific design synthesis — **DONE**
6. M11-A natural-history/observation train — **DONE + lane verified**
7. M11-B contact/behaviour train — **DONE + lane verified**
8. M11-C structure train — **DONE + lane verified, with S1 deliberately deferred**
9. M11-D semantics/ensemble/provenance train — **DONE + lane verified**
10. integrated V1.1 verification — **DONE**
11. final V1.1 independent audit — **NOT YET RUN**
12. full-population 180-day V1.1 baseline — **NOT YET RUN**
13. V1.0 ↔ V1.1 scientific comparison — **NOT YET RUN**
14. Claude Science review of the V1.1 change — **NOT YET RUN**
15. V1.1 release decision / merge / tag — **NOT YET DONE**
16. 30-replicate full-population ensemble on desktop — **DEFERRED UNTIL AFTER V1.1 SCIENCE IS FROZEN**

## 1.2 What is fully done and independently verified

### Frozen V1 release

`main` and `jos-v1.0.0` both point to:

`9e9ce3abc4201cd8303c723015462d21ca237800`

V1 was independently audited before release. The final M10.2 audit passed all 26 targeted release-candidate gates and ended with:

`JOS PASS — RELEASE CANDIDATE APPROVED`

Release integration then:

- fast-forwarded `main`
- created no merge commit
- ran backend smoke: 20 passed
- ran frontend tests: 15 passed, 6 live-only skipped
- TypeScript: passed
- production build: passed
- `git diff --check`: passed
- confirmed audited-commit diff empty
- tagged `jos-v1.0.0` exactly at `9e9ce3...`
- preserved historical branches

### Claude Science frozen-V1 scientific review

The review was read-only against the frozen release. It produced a methods-style audit, technical report, and scientific roadmap.

The review explicitly treated JOS V1 as:

> a synthetic-population, multi-route contact-network, agent-based stochastic epidemic simulator with an explicit observation model, used as a scenario-experimentation environment

and explicitly **not** as:

- a forecasting model
- a Jersey-calibrated epidemiological model
- a validated intervention-effectiveness model
- a named-pathogen model

### Frozen-V1 full-scale pilot

This was executed and scientifically verified. The pilot is now the historical V1 baseline against which V1.1 should be compared.

Persistent evidence directory used by the pilot:

`/Users/stevenmatson/Documents/JOS_v1_full_scale_evidence/`

The pilot itself was run from a detached worktree pinned to the V1 release, not from a moving development branch.

## 1.3 What is done and internally verified, but still unaudited independently

Everything in the current V1.1 candidate falls into this category.

Final candidate:

`461bf0387f4bb91db216b783c19f947f8583b4b8`

Reported integrated verification:

- backend: **214 passed**
- four known warnings
- backend runtime: 714.17 s
- frontend: **15 passed**, 6 live-only skipped
- TypeScript: passed
- production Vite build: passed
- full-mode institutional regression: **1 passed**
- Ruff lint: passed
- Ruff format check: passed
- targeted mypy: passed
- lock check: passed
- compileall: passed
- final `git diff --check`: passed
- integration, main, and all M11 worktrees reported clean

The V1.1 implementation programme reports no finding classified `FAILED`.

However, these claims must be treated as **implementation-thread assertions until independently audited**.

## 1.4 What is in flight right now

No model implementation is currently known to be actively running.

The current in-flight task is conceptual rather than computational:

> **The final independent V1.1 audit has been prepared but not yet executed.**

The primary repository may remain on `main` because `codex/v1.1-integration` is held by a temporary worktree. The audit should therefore use a **new detached audit worktree pinned directly to the immutable candidate commit**.

## 1.5 Current blocking issue / operational nuisance

Attempting to click/switch to `codex/v1.1-integration` in the primary worktree fails because the branch is already checked out by a temporary V1.1 integration worktree.

This is **not a project defect**.

Do not force-remove or clean that worktree just to run the audit.

Instead:

- stay on `main`
- inspect `git worktree list`
- create a new detached worktree from `461bf038...`
- audit the commit directly

Preferred detached audit path:

`/private/tmp/jsy-v11-final-audit`

If occupied, use a numbered variant rather than deleting unknown contents.

---

# 2. Frozen V1 scientific baseline that must remain immutable

## 2.1 Release identity

Tag:

`jos-v1.0.0`

Commit:

`9e9ce3abc4201cd8303c723015462d21ca237800`

`main` must remain at this commit until V1.1 has passed the independent audit, full-scale scientific comparison, and release decision.

## 2.2 V1 scientific classification

The independent scientific audit found V1:

> **SCIENTIFIC REVIEW: SUITABLE WITH MAJOR DISCLOSURES**

No scientific blocker was found because JOS V1 was unusually disciplined about what it did and did not claim.

The core strengths identified were:

- source provenance and evidence classification
- artifact-level scientific verification
- exact separation of latent infections from observed/reported cases
- route separability
- event-time visitor identity binding under slot reuse
- deterministic reproducibility
- clean intervention counterfactual semantics
- explicit declaration of assumptions rather than disguised precision

The dominant scientific weaknesses were:

- fixed / highly regular individual contact structure
- deterministic disease-stage durations
- intervention semantics that tend optimistic
- limited uncertainty quantification
- no Jersey epidemiological calibration
- no retrospective validation
- no prospective validation

## 2.3 Important V1 pilot numbers

Machine:

- MacBook Air
- Apple M4
- 10 CPU cores (4 performance + 6 efficiency)
- 16 GB RAM
- macOS 26.5.2
- Python 3.12.13
- Starsim 3.5.2

Run:

- exact commit: `9e9ce3...`
- seed: 123
- 180 dated output points
- 2025-01-06 through 2025-07-04 inclusive
- no interventions
- no explicit M8 travel layer
- generic import rate = 0
- generic respiratory demo config
- generic observation demo config

Full population inventory:

| Item | Value |
|---|---:|
| Resident agents | 104,540 |
| Private households | 45,133 |
| Communal residents | 2,105 |
| Communal settings | 164 |
| Pupils | 13,991 |
| Schools | 48 |
| Classes | 703 |
| Workers / primary jobs | 58,045 |
| Workplaces | 8,770 |
| All jobs | 62,108 |
| Unique school staff | 1,972 |
| Care staff | 448 |
| Route families | 11 |
| Baseline M4 edges | 856,050 |

Runtime:

| Phase | Seconds |
|---|---:|
| M2 | 239.38 |
| M3 | 319.02 |
| M4 | 32.81 |
| disease/observation/baseline execution | 9,260.28 |
| parent load + writing + CLI residual | 101.83 |
| primary wall time | 9,953.31 |
| scientific verification | 5.51 |
| total | 9,958.82 |

This established a critical operational fact:

> For long full-scale runs, the disease/observation loop dominates runtime. Parent construction is not the main bottleneck.

Peak resident memory:

~2.16 GiB

Zero swap.

Scientific behavior:

| Metric | Result |
|---|---:|
| Initial seeds | 10 |
| First local transmission | 2025-01-08 |
| Peak daily local infections | 7,234 |
| Peak daily local date | 2025-02-03 |
| Peak infectious | 28,479 |
| Peak infectious share | 27.24% |
| Peak infectious date | 2025-03-30 |
| Local infection episodes | 294,555 |
| Imported episodes | 0 |
| Total episodes incl. seeds | 294,565 |
| Episodes per resident | 2.818 |
| Unique ever infected | 99,041 |
| Ever infected fraction | 94.74% |
| Final S | 51,025 |
| Final E | 9,675 |
| Final I | 20,380 |
| Final R | 23,460 |

The run did **not** finish a clean wave. It showed recurrent dynamics and ended during a high-incidence upswing.

The main interpretation is:

- V1 can execute at full island scale
- V1 scientific verification survives a real long-horizon epidemic
- the frozen V1 generic assumptions generate extremely rapid recurrent infection
- 30-day immunity with return to full susceptibility makes reinfection central
- the result is a scientific characterization of V1 assumptions, not Jersey epidemiology

Route-attributed local infections:

| Simulated pathway | Count | Share |
|---|---:|---:|
| household | 80,586 | 27.36% |
| community_indoor | 65,464 | 22.22% |
| workplace_team | 58,410 | 19.83% |
| school_class | 46,808 | 15.89% |
| workplace_transient | 17,254 | 5.86% |
| community_outdoor | 12,027 | 4.08% |
| school_cross_class | 5,794 | 1.97% |
| bus | 3,679 | 1.25% |
| care_resident | 1,869 | 0.63% |
| care_staff | 1,576 | 0.54% |
| shared_vehicle | 1,088 | 0.37% |

Candidate-route ambiguity:

- >1 successful candidate route: 10,166 infections
- 3.45% of local infections

Realised simulated generation interval:

- N = 294,555
- mean 3.652 d
- median 3.0 d
- SD 1.384 d
- IQR 2–5 d
- min 2
- max 6

Selected-snapshot contact-opportunity diagnostic:

- mean 12.16
- median 9
- P90 23
- P95 31
- P99 42
- max 66

These V1 pilot outputs are **historical baseline evidence**. Do not overwrite or reinterpret them as V1.1 outputs.

---

# 3. Branches and worktrees known to this handoff

This section distinguishes branches whose names are known from branches/commits whose exact branch names were not captured.

## 3.1 `main`

**Purpose:** Stable released code.

**Current known commit:**

`9e9ce3abc4201cd8303c723015462d21ca237800`

**Status:** Frozen V1 release. Must not move until V1.1 release process is complete.

**Tag at same commit:**

`jos-v1.0.0`

## 3.2 `docs/jos-v1-scientific-review`

**Purpose:** Preserve the Claude Science scientific review documents without altering the frozen V1 release/tag.

Contains:

- `JOS_V1_SCIENTIFIC_AUDIT.md`
- `JOS_V1_SCIENTIFIC_TECHNICAL_REPORT.md`
- `JOS_V1_SCIENTIFIC_ROADMAP.md`

**Status:** Exists and was confirmed readable during V1.1 orchestration.

**Commit hash:** Not captured in this chat handoff. Determine with Git if needed.

**Important:** Do not treat the frozen V1 tag as containing these reports unless Git shows they were later merged. The original decision was explicitly to keep the frozen release unchanged.

## 3.3 `codex/m10.2-comparison-sync`

**Purpose:** Final M10.2 comparison-horizon correction and V1 release-candidate branch.

**Final commit:**

`9e9ce3abc4201cd8303c723015462d21ca237800`

This became the audited V1 release commit and was later fast-forwarded to `main`.

**Status:** Historical; preserve.

## 3.4 `codex/m10.1-scientific-truth`

**Purpose:** M10.1 correction branch after the first M10 scientific/UI audit exposed truthfulness problems.

Known important checkpoint:

`4ae6008871922bf7f1d820bf04294d477c55c14c`

Later normal merge of M9.4 into this line:

`2dc29b5d7bcee8430b00c94928070172095e17d5`

First release candidate after M10.1 + M9.4:

`1688106ad490abce46c86a0483aaa6c4f8fa948a`

That candidate failed only on two comparison synchronization gates, which led to M10.2.

**Status:** Historical; preserve.

## 3.5 `codex/m9.4-calendar-finalization-clean`

**Purpose:** Correct the strict JSON-mode calendar-date round-trip defect in M9 finalization.

Created from exact verified M9 baseline:

`93b316a119fee9284735eb562dbe1f157cf98281`

Fix commit:

`37af56ea9a368b599f3c89bbbb399b13b465f8f2`

**Status:** Passed independent audit as part of the V1 release chain; historical, preserve.

## 3.6 `codex/m9.4-calendar-finalization`

**Purpose:** Accidental first attempt at M9.4.

**Problem:** Created from the M10.1 checkpoint rather than exact M9 baseline.

**Decision:** Left untouched. Do not reset/delete merely because it is obsolete.

**Status:** Historical accidental branch; preserve unless later deliberately cleaned.

## 3.7 `codex/m10-interactive-app`

**Purpose:** Initial M10 frontend / interactive application implementation.

Initial implementation commit:

`2ea60608fca0e5507214321c3def1a7c2a160370`

Closeout/docs descendant:

`bf7669eb5f0b3a315a227a3194726dfafe0ae32c`

The independent M10 audit failed on scientific/UI truth issues, not visual quality.

**Status:** Historical; preserve.

## 3.8 `codex/v1.1-correctness-foundation`

**Purpose:** Implement only bounded, unambiguous V1.1 correctness fixes that did not require new scientific parameter choices.

Commit:

`7bcdab19d4d175c9c754e371766e4286738d8ca8`

Reported verification before commit:

- 70 targeted protected tests passed
- all 202 backend tests passed
- Ruff passed
- formatting passed
- targeted mypy passed
- diff checks passed

Main changes covered:

- S3 / POP-07 parish no-car residual allocation
- S4 / T-11 in-horizon resident absence runtime application
- S5 / T-12 repeat resident return collision-safe identity
- V1 / X-01 measured/invariant diagnostic corrections
- V4 / N-26 calendar-to-timestep regression coverage
- O3 / T-20 / P-02 travel route-weight provenance surface
- other low-risk provenance corrections only where intent was unambiguous

**Status:** PASS; integrated into V1.1 line.

## 3.9 V1.1 research lane(s)

Exact branch names for every research worktree were not captured in the chat, but the research outputs and commits are known.

R1–R5 combined research docs complete in:

`68770f3` (short hash as reported)

R6 performance profile complete in:

`d2e57d8b985755ac2f2e28c40f1211db147251b7`

Research docs:

- `docs/research/v1_1/R1_NATURAL_HISTORY_OBSERVATION.md`
- `docs/research/v1_1/R2_CONTACT_HETEROGENEITY.md`
- `docs/research/v1_1/R3_JERSEY_STRUCTURE_EVIDENCE.md`
- `docs/research/v1_1/R4_TRAVEL_BEHAVIOUR_UNCERTAINTY.md`
- `docs/research/v1_1/R5_JERSEY_EPIDEMIOLOGICAL_DATA.md`
- `docs/research/v1_1/R6_PERFORMANCE_PROFILE.md`

There was also an adversarial research-QA pass.

**Status:** Complete and incorporated into the synthesis.

## 3.10 Scientific design synthesis

Synthesis commit:

`bde889565854d99f81eb81fe3f7e539e291a4e2b`

Authoritative design document:

`docs/research/v1_1/V1_1_SCIENTIFIC_DESIGN_SYNTHESIS.md`

**Purpose:** Prevent implementation lanes from making their own scientific decisions. It resolves contradictions between roadmap, literature research, repo behavior, and available evidence.

**Status:** Complete; treat as authoritative V1.1 scientific design intent during audit.

Important synthesis decisions are summarized later in this handoff.

## 3.11 `codex/v1.1-performance`

**Purpose:** Profile V1 full-scale performance and only implement optimizations if they are demonstrated semantics-preserving.

Known profile/doc commit:

`d2e57d8b985755ac2f2e28c40f1211db147251b7`

**Result:** No optimization was approved or implemented.

**Reason:** No optimization met the bar for strong evidence of fixed-seed scientific equivalence / low scientific risk within this programme.

**Status:** Documentation-only performance evidence. Future optimization remains open.

## 3.12 `codex/v1.1-m11a-natural-history`

**Purpose:** V1.1 natural-history and observation hardening.

Lane commit:

`ccf9d4f50f58e403b140c671129cc5a984187eeb`

Reported result:

**PASS**

Implementation scope included synthesis-approved natural-history distribution architecture and observation chronology changes while preserving pathogen neutrality and V1 constant-mode compatibility.

This lane initially encountered a safety/execution-policy interruption during prognosis rewriting. The orchestrator continued only with synthesis-approved bounded changes and returned the lane to verification.

**Status:** PASS; merged into integration.

## 3.13 `codex/v1.1-m11b-contact-behaviour`

**Purpose:** Contact-activity architecture, care/medical community-route correction, and adherence hardening.

Lane commit:

`2143255a5de24b5215dbd669e3255fc74fd0dd94`

Reported result:

**PASS**

Important design distinction:

- mechanism for contact activity heterogeneity exists
- shipped activity CV remains zero
- no unsupported non-zero pathogen-neutral dispersion was invented

**Status:** PASS; merged into integration.

## 3.14 `codex/v1.1-m11c-structure`

**Purpose:** School / institutional structural corrections.

Lane commit:

`dc6870245056e0ccaa5120c8389d26c0aedadf2f`

Reported result:

**PASS with S1 deliberately deferred**

S1 = school-type age-allocation correction requiring authoritative year-group evidence.

S2 = school geography truthfulness was addressed.

V3 = full-mode institutional regression coverage addressed.

**Status:** PASS with explicit science/data deferral; merged into integration.

## 3.15 `codex/v1.1-m11d-semantics`

**Purpose:** Output semantics, ensemble honesty, provenance/UI semantic cleanup.

Lane commit:

`0d40c8a0aa89481ea91e4f4b219dffce926d4140`

Reported result:

**PASS**

Important areas:

- unique-person ever-infected fraction
- cumulative episode-incidence semantics
- deprecated legacy `attack_rate` alias
- travel present-population compartments/denominators
- travel scaling context
- realised employment rates
- paired matched-seed difference distribution summaries
- small-ensemble quantile guard
- no fabricated uncertainty / failed replicate zeroing

**Status:** PASS; merged into integration.

## 3.16 `codex/v1.1-integration`

**Purpose:** Integrate all verified V1.1 lanes.

Integration base:

`b844cd064b644376a3a6d1624daa02fb33e14885`

Merge order and merge commits:

| Lane | Merge commit |
|---|---|
| M11-A | `17dcb5934e506912fb20c0dc53c84d2803705e32` |
| M11-B | `dc80fe31191883038f5e0ff6d30e0753aaa5c2ea` |
| M11-C | `e779271b6a35276ab2f67318a5a0506b168d9cf0` |
| M11-D | `a570f4b55588e3f5721f2a09b55b0cf871d513ab` |

Closeout commit:

`d71c79a483d4489aaa9f0985605ebc2c57851f21`

Final tip after non-semantic Markdown hygiene:

`461bf0387f4bb91db216b783c19f947f8583b4b8`

This final tip is the current:

`FINAL_JOS_V1_1_RELEASE_CANDIDATE`

**Status:** Implementation-verified, clean, **independent final audit pending**.

**Worktree:** The integration branch is held by a temporary worktree. The detailed-status paths reported under:

`/private/tmp/jsy_v11_integration/...`

strongly indicate this is the integration worktree path. Confirm with `git worktree list` before relying on the exact path.

Do not force-remove it merely to switch branches.

## 3.17 Temporary audit worktree

Not yet known to exist.

Preferred future path:

`/private/tmp/jsy-v11-final-audit`

It should be a detached worktree pinned exactly to:

`461bf0387f4bb91db216b783c19f947f8583b4b8`

This is the recommended audit mechanism.

---

# 4. Historical milestone lineage and key commits

This is primarily for forensic context. The current agent should not restart these milestones.

## M0–M6

- M0: PASS
- M1: PASS; commit `eec1bc1` (prefix captured)
- M2/M3: eventually corrected and passed; exact final commits not captured in this handoff
- M4.1 staffing closure: `2f28b491...`
- M5 occupational double-count fix: `b3651e6...`
- M5 milestone: `e8269a9...`
- M6 initial: `fc1198d...`

Independent M6 audit found structural defects, leading to corrective chain:

- C1 first: `d211d9b...`
- C1 final: `1e501db...`
- C2: `4dade85...`
- C3 implementation: `0f66677...`
- C3 verification hardening: `658364c7f02cf44f9392116e7db44c94bdb3175a`
- C4: `fd5fac4a977c46fda522b79f038899b05e3c81e9`

C4 opened M7.

## M7

Initial M7:

`1a4521e9c0537190d1da306ce295817867176807`

Independent audit failed on neutral-manager equivalence, provenance, horizon, care targeting, state metrics, vaccination semantics, etc.

C5 closure:

`7290a7cc44c1a2d2e2ed2319cf6cb4a19efa6915`

Verdict:

`C5 PASS — M7 PASS — SAFE TO BEGIN M8`

## M8

Initial M8:

`5768398760d9822ca3e875367dcbd9a42d8c174d`

Failed independent audit.

M8.1:

`c95fb7fd662a7693e68eedeecce1843bbcc9f4a3`

M8.2:

`1b083e4a94223e3fcf42e3b7ea872c254fee172c`

Final verdict:

`M8.2 PASS — M8 PASS — SAFE TO BEGIN M9`

## M9

Initial:

`5e915ed08fadcb8a0758639d658c55afa1d96b3c`

M9.1:

`d6cec02e530084913c421a1c712afefe50e0dede`

AGENTS update ancestor:

`4a6a48d136a7218202131ee51342d24771e47c13`

M9.2 provenance hardening:

`5be3bbf494f5ae85d7f9c3181fc9bcc73212294a`

M9.3 durable evidence/docs closure:

`93b316a119fee9284735eb562dbe1f157cf98281`

Final verdict:

`M9 PASS — SAFE TO BEGIN M10`

M9.4 later fixed calendar finalization:

`37af56ea9a368b599f3c89bbbb399b13b465f8f2`

## M10 / V1 release

Initial implementation:

`2ea60608fca0e5507214321c3def1a7c2a160370`

Closeout audit target:

`bf7669eb5f0b3a315a227a3194726dfafe0ae32c`

Initial M10 audit:

`M10 FAIL — APPLICATION NOT READY`

M10.1 scientific-truth checkpoint:

`4ae6008871922bf7f1d820bf04294d477c55c14c`

M9.4 merged into M10.1:

`2dc29b5d7bcee8430b00c94928070172095e17d5`

First V1 release candidate:

`1688106ad490abce46c86a0483aaa6c4f8fa948a`

Independent audit:

62/64 gates passed; comparison delta correctness and time synchronization failed.

M10.2 fixed those two final gates.

Final release commit:

`9e9ce3abc4201cd8303c723015462d21ca237800`

Independent audit:

all 26 final comparison/release gates passed.

Release:

`jos-v1.0.0`

---

# 5. V1.1 research programme — what was decided

The V1.1 programme intentionally used **parallel research first, then scientific synthesis, then parallel implementation**.

The research lanes were:

- R1 — natural history + observation + interventions
- R2 — contact network heterogeneity + mixing
- R3 — Jersey population + institutions
- R4 — travel + behaviour + uncertainty
- R5 — future Jersey epidemiological evidence
- R6 — performance profiling

A QA lane then challenged contradictions and implementation ambiguities.

## 5.1 R1 conclusions that matter operationally

Key decisions:

- support explicit natural-history duration-distribution architecture
- do not invent a non-zero pathogen-neutral duration CV merely to satisfy H4
- observation onset should consume coherent natural-history timing
- do not invent a presymptomatic infectiousness profile as a generic default
- the frozen 30-day full-susceptibility waning is not an evidence-based generic natural-history default
- keep pathogen neutrality
- separate mechanism capability from default parameter activation

## 5.2 R2 conclusions that matter operationally

Key decisions:

- do **not** exclude every communal resident from community mixing
- the correct scope is the evidence-supported care/medical resident predicate
- hotels, staff accommodation, shelters, detention, etc. must not be indiscriminately removed
- support persistent individual activity/contact heterogeneity architecture
- do not invent an unsupported non-zero generic dispersion
- preserve route separability
- do not wholesale import an external contact matrix without accounting for routes JOS already models separately

## 5.3 R3 conclusions that matter operationally

- authoritative school year-group evidence sufficient to close S1 was not secured
- therefore S1 was deliberately deferred rather than “fixed” using invented structure
- false geographic precision is worse than explicit unknown/non-geographic school geography
- Jersey official sources should dominate; UK proxies must be labelled as proxies
- larger structural enrichment belongs mainly to V1.x rather than the bounded V1.1 hardening release

## 5.4 R4 conclusions that matter operationally

- resident absence and repeat-trip defects were real correctness issues and should be fixed now
- travel scaling and visitor behavior require broader empirical work
- parameter uncertainty is not the same as stochastic replicate variation
- small-ensemble quantile reporting needs honesty/guardrails
- matched-seed comparisons should summarize the distribution of paired differences rather than leave all inference to the consumer

## 5.5 R5 conclusions that matter operationally

The research found reproducibly registrable Jersey epidemiological sources for future V2 work, especially around:

- COVID cases/testing
- serology
- vaccination

It did **not** find a defensible public care-home outbreak series.

This lane is forward-looking. It does not make V1.1 “validated”.

## 5.6 R6 performance conclusion

No performance optimization was approved.

The performance evidence remains documentation-only.

This was an intentional decision, not a failure to finish.

Reasoning:

- full-scale disease execution dominates runtime
- optimization must be profiled, semantics-preserving, deterministic, and demonstrably equivalent
- no change met that threshold during the V1.1 programme
- parent-artifact caching remains useful future work but will not transform a ~154-minute disease loop into a short run by itself

---

# 6. V1.1 finding-status conventions and current claimed status

The V1.1 programme uses four scientific status labels:

- **CLOSED** — the actual scientific/structural problem is corrected, not merely given an interface
- **PARTIALLY CLOSED BY DESIGN** — an architecture/mechanism is implemented, but a scientifically unsupported default or unresolved evidence-dependent part is intentionally not activated
- **DEFERRED TO V1.x** — intentionally outside V1.1 because the necessary empirical evidence or larger redesign is not yet justified
- **FAILED** — intended V1.1 correction did not succeed or introduced unacceptable regression

Current implementation-thread classification:

| Finding | Claimed status | Meaning |
|---|---|---|
| H1 | CLOSED | care/medical community-route membership corrected |
| H2 | CLOSED | observation/onset chronology hardened |
| H3 | PARTIALLY CLOSED BY DESIGN | activity heterogeneity mechanism supported; shipped activity CV remains zero |
| H4 | PARTIALLY CLOSED BY DESIGN | duration-distribution architecture supported; no invented non-zero duration CV |
| H5 | CLOSED | adherence identity corrected |
| S1 | DEFERRED TO V1.x | authoritative school year-group evidence missing |
| S2 | CLOSED | school geography semantics made truthful |
| S3 | CLOSED | parish no-car allocation corrected |
| S4 | CLOSED | in-horizon resident absences applied at runtime |
| S5 | CLOSED | repeat resident travel episode identity corrected |
| V1 | CLOSED | diagnostics/invariants corrected |
| V3 | CLOSED | full-mode institutional regression coverage |
| V4 | CLOSED | calendar-to-timestep regression |
| O1 | CLOSED | misleading attack-rate semantics addressed |
| O2 | CLOSED | mixed travel compartment semantics addressed |
| O3 | CLOSED | travel route weights in provenance/config surface |
| O4 | PARTIALLY CLOSED BY DESIGN | broader provenance cleanup remains |
| O5 | CLOSED | paired-difference summaries |
| O6 | CLOSED | small-ensemble quantile guard |
| O7 | CLOSED | realised employment rates surfaced |
| O8 | CLOSED | travel scaling context surfaced |

This table is **not yet independently audited**. The final Sol audit must reproduce or overturn these classifications.

---

# 7. Decisions made in chat / operations that may not be fully captured in repository docs

The following decisions came from project orchestration and must survive even if they are not fully written into repository documentation. A cold-start agent should verify whether each has since been copied into `V1_1_IMPLEMENTATION_STATUS.md` or other docs, but must not lose them.

## 7.1 Do not run the 30-replicate V1 ensemble

Original plan was to run ~30 full-population replicates after the V1 pilot.

This was explicitly changed after the V1 pilot measured:

- ~2 h 46 min per 180-day replicate on the M4 MacBook Air
- recurrent epidemic behavior dominated by V1 assumptions
- 2.818 infection episodes per resident
- 94.74% ever infected
- 30-day full-susceptibility waning central to behavior

Decision:

> Do **not** spend tens of compute-hours characterizing the frozen V1 assumptions more precisely. Use the single verified V1 pilot as the historical baseline, harden the science first, then run the ensemble on V1.1.

Reasoning:

A 30-run V1 ensemble would precisely characterize assumptions already known to be scientifically provisional. The compute is more valuable after V1.1.

## 7.2 The V1.1 full-scale baseline must happen before V1.1 release tagging

After the final independent V1.1 audit passes:

1. run one full-population 180-day V1.1 baseline
2. compare directly to the frozen V1 pilot
3. inspect scientific changes
4. have Claude Science review the V1 → V1.1 change
5. only then decide to merge/tag V1.1

Reasoning:

V1.0 has a real full-scale baseline. V1.1 should demonstrate that its changes behave coherently at the same regime before being called released.

## 7.3 The 30-run ensemble belongs after V1.1 scientific freeze

The ensemble target remains approximately:

`N = 30`

But it should happen only after:

- V1.1 implementation audit passes
- V1.1 full-scale baseline runs and verifies
- V1 ↔ V1.1 change is reviewed
- V1.1 science is considered stable

Use the desktop rather than the fanless MacBook Air for the 30-run ensemble.

Reasoning:

The Mac pilot established that memory is modest but CPU time is large. A desktop with active cooling and 32 GB RAM is operationally better suited to multi-worker long-running ensembles.

## 7.4 Do not interpret ensemble bands as total uncertainty

Even after V1.1:

ensemble bands must not be called:

- confidence intervals
- credible intervals
- prediction intervals
- total uncertainty intervals

unless parameter/structural uncertainty is genuinely incorporated.

For the current architecture they are:

> stochastic replicate variation

The cold-start agent must preserve that language.

## 7.5 Use a detached audit worktree instead of fighting branch ownership

When a branch is already checked out in a temporary worktree:

- do not force-remove it
- do not force-checkout
- do not clean/reset
- do not move the primary worktree merely for convenience

For audits:

- stay on a safe branch such as `main`
- create a new detached worktree pinned to the exact candidate commit
- audit the immutable commit directly

This is now the preferred audit workflow.

## 7.6 V1 historical branches should be preserved

Do not squash away or casually delete milestone/corrective branches.

Reasoning:

The correction/audit history is scientifically useful because it documents:

- defects found
- fixes made
- independent verification
- provenance of the eventual release

Branch cleanup, if ever done, should be a separate reviewed operation after releases are secure.

## 7.7 Science design and mechanical implementation should remain separated

During V1.1 orchestration, a safety/execution-policy interruption occurred around natural-history prognosis changes.

Operational decision if similar blocks recur:

- use science-specialized review/research to produce a bounded written scientific specification
- ask the implementation agent to implement the mechanical contract
- do not ask an implementation agent to improvise biological parameter values

This also happens to be good scientific architecture.

## 7.8 No unsupported pathogen-neutral numeric defaults

Do not invent:

- contact-activity CV
- duration CV
- presymptomatic infectiousness weight
- named-pathogen timing
- test-sensitivity curve

just to “complete” an architecture.

Mechanism support and default activation must be reported separately.

This is why H3/H4 are partial by design rather than forced to CLOSED.

## 7.9 Explicit unknown is preferable to false precision

For school geography and similar evidence gaps:

- if evidence does not support a real geographic allocation, emit explicit unknown/non-geographic semantics
- do not preserve a convenient but false all-St-Helier field
- do not fabricate catchments

This is a general JOS scientific principle, not just a school-specific fix.

## 7.10 Performance work must prove scientific equivalence

Optimization acceptance requires:

- measured hotspot
- before/after runtime
- deterministic fixed-seed comparison
- no unintended scientific output change
- reproducibility retained

No optimization should be merged merely because it “looks faster”.

This is why R6 produced no performance implementation.

## 7.11 Parent-artifact caching is no longer considered the dominant performance solution

Before the full V1 pilot, parent construction was thought to dominate runtime.

The 180-day pilot disproved that for the real full-wave workload.

Measured rough split:

- M2 + M3 + M4: ~10 minutes
- disease/observation: ~154 minutes

Therefore caching is still useful, especially for ensembles, but it is not the central full-wave performance solution.

## 7.12 V1 pilot evidence must remain preserved

Do not overwrite:

`/Users/stevenmatson/Documents/JOS_v1_full_scale_evidence/`

It is the frozen pre-hardening comparator.

If eventually brought into Git, include only report/manifest/lightweight evidence; do not dump large generated artifacts into the repository unless an explicit artifact-storage policy is created.

## 7.13 Scientific reports should not mutate the frozen release retroactively

The Claude Science reports were intentionally placed on a separate documentation branch rather than altering the already-audited `jos-v1.0.0`.

Future reports should follow the same principle:

- frozen release remains immutable
- review/report commits can live on documentation or future release branches
- do not rewrite a historical tag to “include” later review documents

---

# 8. Open items and priority

## P0 — immediate: final independent V1.1 audit

This is the only current release blocker.

Audit exact commit:

`461bf0387f4bb91db216b783c19f947f8583b4b8`

Do not audit the moving branch name.

Use a detached worktree.

Expected final verdict syntax:

`JOS V1.1 RELEASE-CANDIDATE PASS`

or:

`JOS V1.1 RELEASE-CANDIDATE BLOCKED`

If BLOCKED:

- do not merge
- do not tag
- isolate the exact defect
- create the smallest corrective branch
- rerun the bounded audit

## P1 — after audit PASS: full-population 180-day V1.1 baseline

Use same or directly comparable conditions to V1 pilot wherever scientifically appropriate.

Key comparison targets:

- establishment/fadeout
- peak incidence
- peak infectious prevalence
- total episode incidence
- unique ever infected
- reinfection intensity
- route shares
- generation interval
- contact-opportunity distribution / heterogeneity
- calendar modulation
- final state
- runtime
- memory
- verifier result

The point is not to “beat” V1 numerically. The point is to demonstrate the consequences of the scientific hardening.

## P2 — Claude Science V1 → V1.1 review

After the V1.1 full-scale run:

ask Claude Science to review:

- candidate implementation changes
- finding closure
- full-scale change in behavior
- whether any new scientific caveat emerged
- whether V1.1 remains “synthetic research simulator” rather than validated Jersey model

This should be a bounded delta review, not a repeat 1,600-line audit from scratch unless needed.

## P3 — release decision

Only after P0–P2:

- determine whether V1.1 is release-worthy
- fast-forward / merge `main` only with reviewed ancestry
- smoke
- tag an explicit V1.1 version
- preserve V1 and V1.1 audit history

Exact tag name has not yet been formally set in chat, but likely `jos-v1.1.0`. Do not invent the tag before release approval.

## P4 — desktop transfer / 30-replicate ensemble

The desktop has 32 GB RAM and active cooling.

The repo is not yet known to have been transferred to the desktop during this current sequence.

When ready:

- make GitHub/private remote the clean handoff point if not already done
- clone exact release candidate/release onto desktop
- verify commit and tags
- install environment
- run one desktop smoke
- run `N=30` full-population ensemble with bounded parallelism

Parallelism should be selected from measured desktop CPU/memory, not guessed.

## P5 — V1.x empirical calibration work

After V1.1:

priority data/model hardening includes:

- contact-structure plausibility vs POLYMOD/CoMix or justified proxy
- collapse redundant route/transmission parameterization
- household size/age structure evidence
- care-home age and size distributions
- workplace size tail / hospital representation
- use already-ingested sector-by-size cross-tab
- worker age/sex controls
- partial/sector-specific remote work
- broader institutional staffing
- further education
- observed travel seasonality
- consistent travel scaling
- volume-responsive visitor mixing
- incubation-sensitive border-test model
- visitor behavior evidence
- parameter uncertainty propagation
- global sensitivity analysis
- better statistical calibration likelihoods

## P6 — V2 validated disease-specific modelling

This is later and requires registered Jersey epidemiological data.

High-level target:

- named pathogen parameter sets with literature provenance
- Jersey surveillance series
- retrospective reconstruction
- Bayesian / likelihood-free calibration
- out-of-sample validation
- severity / hospitalization / healthcare-capacity pathways
- partial immunity / vaccination history
- behavioral substitution and adherence dynamics

Do not jump to V2 before V1.1/V1.x structure is stable; otherwise calibration will absorb structural error.

---

# 9. Things currently waiting on the user

The cold-start agent should not pretend background work is pending. The following need user action/approval.

## Immediate

The user needs to launch the **independent V1.1 audit** in a fresh Sol High thread.

The user can remain on `main`; the audit should create its own detached worktree.

No branch switch to `codex/v1.1-integration` is necessary.

## After audit PASS

The user needs to approve/start the expensive V1.1 full-scale 180-day run.

Likely machine choice:

- Mac is scientifically capable, proven by V1
- desktop is operationally better for the eventual 30-run ensemble

The single V1.1 comparator can run on Mac if desired for continuity; the ensemble should move to desktop.

## Later

The user will need to make the desktop repo available / clone the project there before the 30-run ensemble.

If GitHub remote state is not already configured, that needs to be handled before desktop execution.

---

# 10. Audit methodology and gate conventions

This section is intended to let a cold-start agent regenerate an audit without this chat.

## 10.1 Core audit principle: immutable commit, not branch tip

Every release audit should name one exact commit.

For current V1.1:

`461bf0387f4bb91db216b783c19f947f8583b4b8`

Do not audit:

`codex/v1.1-integration` “whatever HEAD is now”.

Instead:

1. verify commit exists
2. verify expected ancestry
3. create detached worktree pinned exactly to commit
4. verify clean worktree
5. run audit read-only
6. verify HEAD and cleanliness again at end

## 10.2 Audit independence

Implementation-thread statements are not evidence.

Files such as:

- `V1_1_IMPLEMENTATION_STATUS.md`
- `docs/progress.md`

are **claims to be verified**, not ground truth.

The auditor must inspect material code and artifacts directly.

Passing tests alone are not proof.

## 10.3 No repair during audit

The independent audit should not:

- edit code
- edit docs
- commit
- merge
- tag
- rebase
- reset
- clean
- force-checkout
- silently fix defects

If a defect is found, return BLOCKED with precise evidence.

Fixes happen in a separate corrective implementation thread.

## 10.4 Protected contracts

Unless an explicit V1.1 finding authorizes a change, audits protect:

- resident identity
- population counts
- household identity
- M2/M3 identity continuity
- deterministic construction
- seed determinism
- route separability
- nested-route exclusion
- scientific artifact hashes
- parent hash verification
- immutable provenance
- lifecycle ordering
- observation/latent-truth separation
- non-retrocausal intervention action
- visitor event-time identity
- travel slot-reset semantics
- failed replicate preservation
- no missing→zero coercion
- no fabricated uncertainty
- result-manifest authority
- legacy artifact verification where promised
- V1 frozen tag immutability
- `main` immutability until release gate

## 10.5 Gate-list status conventions

For implementation/release gates:

- **PASS** — acceptance criterion independently satisfied
- **FAIL** — criterion not satisfied

For scientific finding closure:

- **CLOSED**
- **PARTIALLY CLOSED BY DESIGN**
- **DEFERRED TO V1.x**
- **FAILED**

Do not conflate these systems.

A lane can “PASS” while a finding is “PARTIALLY CLOSED BY DESIGN” if the design explicitly says the correct scientific behavior is to implement a mechanism without inventing an unsupported default.

## 10.6 H3/H4 special rule

For H3 contact heterogeneity and H4 duration distributions, always assess two distinct things:

1. **architecture / mechanism support**
2. **shipped default activation**

Do not mark CLOSED simply because the interface exists.

Current intended state:

- H3 mechanism: supported
- H3 non-zero shipped activity CV: intentionally not invented
- H4 distribution architecture: supported
- H4 non-zero shipped duration CV: intentionally not invented

Therefore the implementation-thread status is:

`PARTIALLY CLOSED BY DESIGN`

The independent audit may change this if implementation does not match the synthesis.

## 10.7 S1 special rule

S1 should not be classified FAILED merely because it is not implemented if:

- the synthesis explicitly deferred it
- authoritative evidence was insufficient
- the limitation remains explicit
- the code does not fabricate a replacement

Expected current status:

`DEFERRED TO V1.x`

## 10.8 Minimum V1.1 audit test surface

Run, at minimum:

### Backend / science

- complete backend test suite
- scientific verification suites
- travel tests
- observation tests
- intervention tests
- network tests
- compatibility / legacy artifact tests
- full-mode institutional regression

### Frontend

- frontend unit/focused tests
- TypeScript check
- production Vite build

### Static / repository

- Ruff lint
- Ruff format check
- targeted mypy
- dependency/lock check
- compileall
- `git diff --check`

Do not run the 180-day full-wave inside the independent code audit.

Do not run the 30-replicate ensemble inside the audit.

## 10.9 Why full-mode regression is required

CI mode (~3,000 agents) deletes or collapses important institutional categories.

The frozen audit found CI does not exercise:

- nursing-home structure
- detention
- some communal categories
- meaningful multi-school behavior

Therefore full-mode structure needs at least one targeted regression independent of normal CI suites.

## 10.10 Current V1.1 audit checklist

The auditor must independently inspect:

### Repository / ancestry

- exact candidate commit
- frozen V1 ancestor
- correctness-foundation ancestor
- synthesis ancestor
- M11-A/B/C/D ancestors
- merge graph
- changed files
- clean worktree

### H1 care / community

- correct care/medical predicate
- no blanket removal of unrelated communal populations
- route conservation

### H2 observation chronology

- symptom-onset ownership
- no impossible chronology under revised contract
- online/offline agreement
- next-day action
- non-retrocausality

### H3 activity architecture

- mean-one behavior
- exact zero-CV bypass
- approved route scope
- determinism
- route separability
- default still neutral unless evidence-supported

### H4 duration architecture

- constant mode
- approved alternative distribution mode
- mean/CV semantics
- seeded deterministic draws
- daily ceiling transition semantics
- V1 compatibility projection

### H5 adherence

- stable per intervention-version/person identity
- route-independent personal adherence where intended
- vaccine uptake separate
- reproducibility

### S1–S5

- S1 explicit evidence-based deferral
- S2 truthful school geography semantics
- S3 no-car allocation
- S4 in-horizon travel absence
- S5 repeat trip identity

### V1/V3/V4

- diagnostics are measured or explicitly invariant
- full-mode institutional regression
- calendar/timestep alignment

### O1–O8

- episode incidence vs unique ever infected
- legacy attack-rate semantics
- UI field use
- mixed-population travel denominators
- provenance/scaling context
- paired difference distribution
- quantile floor guard
- failed replicate behavior
- realised employment rates
- O4 partial provenance status

### Travel regression

- resident absence lifecycle
- repeat returns
- visitor identity binding
- route weights
- scaling context
- mixed resident/visitor outputs
- no M8 regression

### Ensemble regression

- matched seed pairing
- difference distributions
- successful-replicate-only quantiles
- 39/40 threshold/floor behavior if applicable
- null preservation
- coupling caveat
- no fabricated uncertainty

### Artifacts / versions

- schema versions
- hashes
- immutable verification
- legacy manifest verification
- V1 projection boundary
- no accidental invalidation of V1 artifacts

### Performance

- R6 evidence read
- no unapproved optimization
- no unsupported equivalence claim

## 10.11 Current audit final verdict convention

The final line must be exactly one of:

`JOS V1.1 RELEASE-CANDIDATE PASS`

or:

`JOS V1.1 RELEASE-CANDIDATE BLOCKED`

Nothing should be merged or tagged during the audit.

---

# 11. Exact current independent audit setup

The primary worktree can stay on:

`main`

Expected `main` HEAD:

`9e9ce3abc4201cd8303c723015462d21ca237800`

The branch `codex/v1.1-integration` is likely already checked out in a temporary worktree.

Audit commit:

`461bf0387f4bb91db216b783c19f947f8583b4b8`

Recommended audit procedure:

```bash
cd /Users/stevenmatson/Documents/jsy_disease_sim

git status --porcelain
git rev-parse main
git rev-parse 'jos-v1.0.0^{}'
git worktree list --porcelain
git show --no-patch --oneline 461bf0387f4bb91db216b783c19f947f8583b4b8
```

Then choose a free path:

```bash
git worktree add --detach \
  /private/tmp/jsy-v11-final-audit \
  461bf0387f4bb91db216b783c19f947f8583b4b8
```

Inside audit worktree:

```bash
cd /private/tmp/jsy-v11-final-audit

git rev-parse HEAD
git status --porcelain
git branch --show-current
```

Expected:

- detached HEAD
- exact commit `461bf038...`
- clean worktree

At audit end:

- HEAD must still be exact candidate
- worktree must still be clean

Do not remove the integration worktree to perform this audit.

---

# 12. Scientific claims that remain allowed / prohibited

These boundaries come from the frozen scientific audit and remain binding unless V1.1 explicitly earns a stronger claim.

## Allowed style

JOS may be described as:

- a synthetic agent-based epidemic simulation framework
- a multi-route contact-network simulator
- a scenario-experimentation platform
- a provenance-anchored reproducible research simulator
- a model that can compare scenarios under controlled assumptions
- a model that distinguishes latent infections from observed cases
- a model that can report simulated transmission pathways
- a framework with explicit travel/importation mechanisms
- a framework supporting stochastic replicate analysis

Use wording such as:

- “under the specified assumptions”
- “within the synthetic population”
- “the simulation suggests”
- “simulated transmission pathway”
- “scenario comparison”
- “stochastic replicate variation”

## Still prohibited unless future validation changes the status

Do not claim:

- prediction of Jersey cases
- forecast accuracy
- real intervention effectiveness
- real-world causal route attribution
- real-world R or Rt estimates
- total scientific uncertainty
- validated border-policy effectiveness
- named-pathogen conclusions from the generic config
- actual historical transmission reconstruction
- that passenger movements are unique tourists
- that synthetic agents are real Jersey residents/households

V1.1 hardening does not automatically change this epistemic boundary.

---

# 13. Key scientific-review documents

## Frozen V1 review

On the scientific-review branch:

- `docs/reports/JOS_V1_SCIENTIFIC_AUDIT.md`
- `docs/reports/JOS_V1_SCIENTIFIC_TECHNICAL_REPORT.md`
- `docs/reports/JOS_V1_SCIENTIFIC_ROADMAP.md`

Important frozen-V1 review verdict:

> SCIENTIFIC REVIEW: SUITABLE WITH MAJOR DISCLOSURES

Important conceptual conclusion:

> JOS is strong where the question is structural and weak where the question is distributional.

Strong:

- which routes exist
- how settings interlock
- provenance
- reconciliation
- reproducibility
- artifact integrity

Weak:

- individual heterogeneity
- tails / overdispersion
- full uncertainty
- empirical calibration
- external validation

## V1.1 research / implementation docs

Expected in the V1.1 candidate:

- `docs/research/v1_1/R1_NATURAL_HISTORY_OBSERVATION.md`
- `docs/research/v1_1/R2_CONTACT_HETEROGENEITY.md`
- `docs/research/v1_1/R3_JERSEY_STRUCTURE_EVIDENCE.md`
- `docs/research/v1_1/R4_TRAVEL_BEHAVIOUR_UNCERTAINTY.md`
- `docs/research/v1_1/R5_JERSEY_EPIDEMIOLOGICAL_DATA.md`
- `docs/research/v1_1/R6_PERFORMANCE_PROFILE.md`
- `docs/research/v1_1/V1_1_SCIENTIFIC_DESIGN_SYNTHESIS.md`
- `docs/research/v1_1/V1_1_IMPLEMENTATION_STATUS.md`
- `docs/progress.md`

The synthesis is the design authority.

The implementation-status and progress files are **not audit authority**.

---

# 14. Current V1.1 implementation results in detail

## Correctness foundation

Commit:

`7bcdab19d4d175c9c754e371766e4286738d8ca8`

Resolved unambiguous defects before scientifically ambiguous lanes began.

Important nuance discovered during travel correction:

`trip_id` is shared by all people in a travel party, so it is not a globally unique person-episode key.

The implemented minimal collision-safe runtime identity used compound identity rather than casually changing party semantics.

This is an example of the rule:

> preserve existing domain identity contracts; fix the collision at the correct level.

## M11-A

Commit:

`ccf9d4f50f58e403b140c671129cc5a984187eeb`

Reported PASS.

The safety interruption during development does **not** mean the lane is incomplete. The orchestration resumed and finished.

The final audit must nevertheless verify:

- natural-history draws
- constant/gamma semantics
- mean/CV handling
- daily ceiling transitions
- onset ownership
- chronology
- waning defaults
- constant-mode/V1 compatibility projection

A compatibility-projection boundary defect was actually exposed during final integrated testing and corrected before the complete 214-test backend rerun.

That correction is already inside the final candidate, but the auditor should inspect it closely.

## M11-B

Commit:

`2143255a5de24b5215dbd669e3255fc74fd0dd94`

Reported PASS.

The critical scientific nuance is not to confuse:

- support for activity heterogeneity

with:

- activation of an arbitrary heterogeneity default

Zero-CV bypass is part of the intended design.

## M11-C

Commit:

`dc6870245056e0ccaa5120c8389d26c0aedadf2f`

Reported PASS with S1 deferred.

Do not “finish” S1 by inventing a year-group allocation after the fact.

The current scientific posture is that an explicit evidence gap is better than a plausible-looking unsupported allocation.

## M11-D

Commit:

`0d40c8a0aa89481ea91e4f4b219dffce926d4140`

Reported PASS.

This lane is central to preventing scientific misinterpretation.

Audit emphasis:

- unique-person ever-infected fraction must be mathematically distinct from cumulative episode incidence
- deprecated aliases must not silently drive the UI
- travel present-population fields must be explicit
- small-N quantile behavior must be honest
- paired differences must preserve matched-seed meaning

---

# 15. Performance status

## Known V1 bottleneck

The full V1 180-day pilot measured disease/observation execution at:

~9,260 seconds

This is ~51.4 seconds per simulated day on the M4 MacBook Air for the frozen V1 full-scale configuration.

That dwarfed M2/M3/M4 construction.

## No V1.1 optimization currently merged

This is deliberate.

The performance branch/doc should be treated as:

- evidence
- profiling
- future design input

not as an unfinished task blocking the V1.1 audit.

## Future performance work

Recommended order after scientific behavior is stable:

1. reprofile V1.1 with short full-population runs (7/14/30 days)
2. identify measured daily-loop hotspots
3. isolate semantics-preserving optimization candidates
4. demonstrate fixed-seed equivalence
5. measure before/after runtime
6. merge only independently verified optimization
7. then choose ensemble worker count

Potential areas previously identified for profiling include:

- dynamic-network regeneration
- Starsim edge handling
- route array copying/conversion
- intervention manager
- observation scheduler
- attribution
- event accumulation
- DataFrame / Arrow construction
- daily diagnostics
- hashing/artifact creation

Do not assume any of those is a bottleneck without measurement.

---

# 16. Desktop / ensemble plan

The user has a desktop with 32 GB RAM.

The Mac full-scale pilot demonstrated that one replicate is memory-light enough (~2.16 GiB) but very CPU-time heavy.

The desktop is therefore intended primarily for:

- sustained CPU throughput
- active cooling
- bounded parallel full-scale replicates

not because a single JOS run requires enormous RAM.

## Ensemble target

Initial target:

`N = 30`

Use unique deterministic seeds.

Report at minimum:

- successful / failed replicate counts
- establishment probability
- extinction probability where meaningful
- median
- IQR
- min/max
- empirical stochastic replicate quantiles if N supports them
- peak incidence distribution
- peak-date distribution
- peak infectious prevalence
- cumulative episode incidence
- unique ever infected if supported
- route-share distributions
- candidate-route ambiguity
- age-band distributions

Do not silently replace failed replicates.

Do not call the bands total uncertainty.

## Machine transfer

A GitHub/private-repo handoff prompt was discussed but the current chat does not contain confirmation that the repo was actually pushed/cloned to the desktop.

Therefore:

> Desktop transfer status is UNKNOWN / NOT CONFIRMED.

Check before planning the ensemble.

---

# 17. Release procedure conventions

## V1 precedent

The correct release pattern is:

1. independent audit exact candidate
2. verify ancestry
3. fast-forward `main` if possible
4. verify `main` exact audited commit
5. lightweight smoke on `main`
6. tag exact commit
7. leave historical branches intact

Do not squash scientific/corrective/audit history.

## V1.1 difference from V1

For V1.1, an extra scientific gate was intentionally added:

1. independent code/science audit
2. **full-population V1.1 baseline**
3. **V1 ↔ V1.1 scientific comparison**
4. **Claude Science delta review**
5. release decision
6. main integration / smoke / tag
7. ensemble

The full-scale run is therefore not merely post-release benchmarking; it is part of the V1.1 release confidence process.

---

# 18. Things a cold-start agent must not do

Do not:

- restart V1.1 research from scratch
- rerun R1–R6 unless evidence is missing
- rebuild the correctness foundation
- reimplement M11 lanes merely because the final audit has not yet run
- assume the safety interruption means M11-A is unfinished
- merge `codex/v1.1-integration` to `main` yet
- tag V1.1 yet
- run the 30-replicate ensemble yet
- run another 180-day full-scale simulation before the audit passes
- force-remove active worktrees just to free a branch
- `git clean`
- `git reset --hard`
- force-checkout
- rewrite / squash milestone history
- fabricate school year-group data
- fabricate catchments
- fabricate pathogen-neutral CVs
- invent literature-based defaults without provenance
- call V1.1 calibrated or validated
- conflate cumulative infection episodes with ever-infected fraction
- call stochastic replicate quantiles confidence intervals
- treat `docs/progress.md` as independent audit evidence
- casually optimize the daily loop without fixed-seed scientific-equivalence evidence

---

# 19. Recommended immediate cold-start checklist

1. `cd /Users/stevenmatson/Documents/jsy_disease_sim`
2. inspect `git status --porcelain`
3. inspect `git worktree list --porcelain`
4. verify:
   - `main` = `9e9ce3...`
   - `jos-v1.0.0^{}` = `9e9ce3...`
   - candidate `461bf038...` exists
5. identify the current integration worktree path
6. do **not** try to switch primary worktree to `codex/v1.1-integration`
7. create detached audit worktree at candidate
8. read R1–R6, synthesis, implementation status
9. run independent V1.1 audit
10. return exact verdict
11. if PASS, prepare the full-scale V1.1 comparison run
12. if BLOCKED, isolate and fix only the blocker, then reaudit

---

# 20. Short-form source-of-truth state

If only one paragraph survives:

> JOS V1.0 is complete, independently audited, on `main`, and tagged `jos-v1.0.0` at `9e9ce3abc4201cd8303c723015462d21ca237800`; Claude Science subsequently reviewed the frozen release and found it suitable as a synthetic research simulator with major disclosures and zero scientific blockers, and a verified 104,540-agent 180-day V1 pilot established the historical full-scale baseline. V1.1 scientific hardening has since completed parallel research R1–R6, correctness foundation `7bcdab19...`, synthesis `bde88956...`, M11-A `ccf9d4f...`, M11-B `2143255...`, M11-C `dc6870...`, M11-D `0d40c8...`, and integration to final candidate `461bf0387f4bb91db216b783c19f947f8583b4b8`; integrated verification reports 214 backend tests passing, frontend/typecheck/build passing, full-mode institutional regression passing, and no failed target finding, but the candidate has **not yet received the final independent Sol audit**. The immediate next action is a read-only detached-worktree audit of exact commit `461bf038...`; only after audit PASS should the project run the full-population 180-day V1.1 comparator, compare against frozen V1, obtain a Claude Science delta review, decide release/merge/tag, and finally run the 30-replicate ensemble on the desktop.

---

# 21. Known uncertainty in this handoff

The following details were not explicitly reported back in chat and should be resolved from Git rather than guessed:

- exact commit hash of `docs/jos-v1-scientific-review`
- exact branch names used for all R1–R5 research worktrees
- whether the old `/private/tmp/jsy-release-main` V1 release worktree still exists; it was expected to be removed to free `main`, and later `main` was usable, but verify with `git worktree list`
- exact current path of the `codex/v1.1-integration` worktree; `/private/tmp/jsy_v11_integration` is strongly implied by report paths but should be confirmed
- whether GitHub remote/private repo setup and desktop clone have actually been completed
- whether the V1 full-scale pilot report/figures have since been committed to any documentation branch; the evidence directory exists outside the repo, but repository inclusion was intentionally deferred

Where this handoff says “reported”, the statement came from an implementation/audit agent response and should be independently checked at the next formal gate.

---

# 22. Canonical next verdict

The project should not be described as “V1.1 released” yet.

The next legitimate state transition is only:

**Current:**  
`V1.1 RELEASE CANDIDATE — IMPLEMENTATION VERIFIED, INDEPENDENT AUDIT PENDING`

→ if audit passes:

`V1.1 RELEASE CANDIDATE — INDEPENDENT AUDIT PASSED, FULL-SCALE SCIENTIFIC COMPARISON PENDING`

→ after full-scale comparison and science review:

`V1.1 RELEASE APPROVED`

→ only then:

`main` integration + V1.1 tag.

---

*End of handoff.*
