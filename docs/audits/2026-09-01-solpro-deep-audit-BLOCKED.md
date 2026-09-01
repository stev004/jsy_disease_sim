# Independent deep audit — Jersey Outbreak Simulator V1.1

**Audit date:** 1 September 2026  
**Candidate audited:** `e3609ff288b33444456de960db9e7c6560d0b898`  
**Frozen comparison release:** `jos-v1.0.0` / `9e9ce3abc4201cd8303c723015462d21ca237800`  
**Audit role:** independent release review plus refined V1.x/V2 scope  
**Overall verdict:** **BLOCKED — do not merge or tag this candidate**

---

## 1. Executive conclusion

V1.1 is scientifically much stronger than V1.0. The principal hardening work is real: duration distributions are represented without inventing a non-zero generic default; the generic disease no longer silently resets all immunity after 30 days; natural-history timing owns symptom onset; adherence and contact activity are stable agent traits; institutional/community overlap is reduced; output denominators are substantially clearer; and the full-population comparison behaves coherently under those changed assumptions.

The one-line O2 denominator correction at `e3609ff2` is correct, narrow, and regression-tested. The exact candidate also passed the backend CI suite under the pinned Python environment.

However, this is **not yet a trustworthy release artifact**. I found four release-blocking defects:

1. **Portable scientific verification is broken.** M5/M6 writers and the verifier disagree about the base directory for manifest paths. Normal in-repository output can be unverifiable, and copied/relocated evidence can fail even when every copied file is intact. The supplied V1.1 evidence bundle demonstrates the defect: all eight nested M5 files match their recorded hashes and sizes locally, but all eight manifest paths point to Steven’s original absolute Mac directory and are therefore missing and outside the copied artifact root.
2. **The daily M6 `ascertainment_fraction` is semantically false.** It divides detections occurring on a calendar date by infections acquired on that same date. Those are different cohorts whenever detection is delayed. The aggregate ascertainment diagnostic is coherent; the daily field is not.
3. **The public API advertises stale artifact-schema versions.** Four of its five values disagree with the schemas the candidate actually writes.
4. **The release-control documents direct Steven toward the superseded, known-bad branch.** Following `GATES.md` literally would merge `codex/v1.1-integration` at `461bf038`, not the corrected candidate at `e3609ff2`.

These findings do **not** show that the V1.1 epidemic trajectory is numerically corrupt. They show that the candidate cannot yet satisfy its own standards for portable evidence, truthful outputs, API contracts, and exact-commit release control.

The right response is a bounded correction cycle, not a redesign. Repair the output/provenance contracts, version the altered observation schema, correct the release state, rerun the exact gates, regenerate the final comparison evidence under the corrected SHA, then perform a bounded independent re-audit.

---

## 2. Scope, method, and evidence basis

### 2.1 Material reviewed

I followed the audit bundle’s prescribed order and reviewed:

- `.claude/FRONTIER.md`, `DIRECTOR.md`, `GATES.md`, `decisions.tsv`, `RUN.md`, and `CLOSEOUT.md`;
- `AGENTS.md` and the root project documentation;
- `docs/handoff/2026-08-31-sol-handoff.md`;
- both prior V1.1 audit reports;
- the P1 V1.0↔V1.1 full-scale comparison report;
- the R1–R6 V1.1 research dossiers and scientific synthesis;
- the current implementation, schemas, artifact writers, verifiers, API, frontend consumers, and tests;
- the copied V1.1 full-population evidence artifact and both nested manifests;
- the connected GitHub repository for ancestry, branch state, exact-commit diff, and CI evidence.

### 2.2 Independent checks performed

- Confirmed the connected repository contains the exact candidate.
- Confirmed `e3609ff2` is the direct child of the originally blocked candidate `461bf038`.
- Confirmed its code delta is exactly the O2 metadata correction plus its staggered-arrival regression test.
- Confirmed frozen V1 is the merge base and the candidate is 19 commits ahead, zero behind.
- Confirmed the corrective branch points exactly to `e3609ff2` and the old integration branch still points to `461bf038`.
- Inspected the exact GitHub Actions run for `e3609ff2` and its raw job log.
- Ran local syntax compilation over `src` and `tests` with the available interpreter.
- Independently recomputed SHA-256 hashes and file sizes for the copied M7 and nested M5 evidence records using only the standard library.
- Traced manifest-path generation through writer, default CLI, and recursive verifier code.
- Traced infection, symptom, detection, and report-date semantics through M6 event scheduling and daily aggregation.
- Compared API-advertised versions against live schema defaults/constants.
- Reviewed the V1.1 scientific mechanisms against the project’s own “mechanism support versus default activation” rules.

### 2.3 Environment limitation

The uploaded archive contains tracked files but no `.git` directory. The local audit runner had Python 3.13 rather than the pinned Python 3.12.13 environment and could not reconstruct the locked environment from the archive. I therefore did **not** represent the local runner as a successful full-suite execution.

That gap is closed by the exact candidate’s connected GitHub Actions run: it checked out `e3609ff2`, used Python 3.12.13 through the lockfile, collected 215 tests, and passed all 215. Lint, formatting, the configured CI mypy scope, the Starsim demo, and CI-scale population/structure/network generation also passed.

I did not rerun the 104,540-agent, 180-day simulation in this audit. The full-scale numerical interpretation therefore rests on the supplied immutable tables, their content hashes, the run manifests, and the filed comparison analysis—not on a second independent long simulation.

---

## 3. Release gate matrix

| Gate | Result | Audit conclusion |
|---|---:|---|
| Exact candidate identity | **PASS** | Candidate exists at `e3609ff2`; corrective branch points exactly there. |
| Frozen V1 ancestry | **PASS** | V1 `9e9ce3a` is the merge base; candidate is 19 commits ahead and zero behind. |
| O2 correction boundedness | **PASS** | One metadata line plus one focused regression test; no hidden model change. |
| Exact backend CI | **PASS** | 215/215 tests under Python 3.12.13; lint, format, CI mypy, and smoke generation passed. |
| Core V1.1 scientific direction | **PASS WITH EXPLICIT DEFERRALS** | Mechanisms/defaults broadly match the design authority and avoid unsupported precision. |
| Full-scale P1 behaviour | **NO NUMERICAL RELEASE CONCERN FOUND** | The change is coherent with removal of complete 30-day waning; not evidence of empirical fit. |
| Copied evidence file integrity | **PASS** | All 14 top-level M7 records and all 8 locally copied M5 files match recorded hashes/sizes. |
| Portable/recursive scientific verification | **FAIL — BLOCKER B01** | Nested M5 manifest contains eight stale absolute paths; writer/verifier contracts conflict. |
| Daily observation semantics | **FAIL — BLOCKER B02** | Daily ascertainment divides different calendar cohorts and is not an ascertainment fraction. |
| API schema-version truth | **FAIL — BLOCKER B03** | Four of five advertised versions are stale. |
| Release branch/state instructions | **FAIL — BLOCKER B04** | Current gate text names the superseded failed branch as the merge target. |
| Release/package identity | **MAJOR** | Project/API/frontend still identify as `0.1.0` while preparing `jos-v1.1.0`. |
| Travel diagnostic truthfulness | **MAJOR** | One invariant is mislabelled; overall travel status is unconditionally `passed`. |
| Durable release CI breadth | **MAJOR** | Exact backend CI is strong, but frontend and several release checks are not encoded in the workflow. |
| Overall release decision | **BLOCKED** | Correct blockers, regenerate evidence, and re-audit before merge/tag. |

---

## 4. Release blockers

## B01 — Scientific artifact path contract is internally inconsistent and non-portable

**Severity:** release blocker  
**Affected tier:** M5 and M6 writers directly; nested M7 verification transitively  
**Primary files:**

- `src/jersey_outbreak/outbreak_artifacts.py:50–54, 67–80, 239–246`
- `src/jersey_outbreak/scientific_verification.py:52–75, 218–236, 553–560`
- `src/jersey_outbreak/cli.py:375–419`
- same helper pattern in `observation_artifacts.py:50–54, 242–248`, `ensemble_artifacts.py:58–85`, and `calibration_artifacts.py:49–53, 157–163`

### What the writer does

The M5 writer records each output path relative to the **repository root** when the output is inside the repository:

```python
def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
```

If the artifact is outside the repository, it records an **absolute path** instead.

### What the verifier assumes

The scientific verifier interprets every non-absolute manifest path relative to the **artifact directory**, then requires the resolved result to remain inside that artifact directory:

```python
candidate = Path(str(record["path"]))
if not candidate.is_absolute():
    candidate = artifact_directory / candidate
candidate = _inside(candidate, artifact_directory)
```

Those are incompatible path bases.

### Failure under the normal CLI default

The default M5 CLI destination is `outputs/outbreaks` inside the repository. A file can therefore be recorded as something equivalent to:

```text
outputs/outbreaks/<artifact-id>/daily_epidemic.parquet
```

The verifier then prepends `<artifact-directory>/`, looking for:

```text
<artifact-directory>/outputs/outbreaks/<artifact-id>/daily_epidemic.parquet
```

That path does not exist. A standard, successful, default-location run can thus create an artifact that its own scientific verifier cannot verify.

### Failure after relocation

When output is written outside the repository, the manifest records absolute machine-specific paths. Verification can work in the original location, but copying the artifact to another directory or another machine fails the verifier’s confinement rule—even when every copied file is intact.

### The supplied evidence bundle proves the portability defect

For the copied V1.1 P1 artifact:

| Layer | Records | Absolute paths | Recorded paths present | Hash/size match at recorded path | Same-name local file hash/size match |
|---|---:|---:|---:|---:|---:|
| M7 | 14 | 0 | 14 | 14 | n/a for nested records |
| Nested M5 | 8 | 8 | 0 | 0 | **8** |

Every nested M5 manifest path begins with Steven’s original directory:

```text
/Users/stevenmatson/Documents/JOS_v1_1_full_scale_evidence/run-20260831T145052Z/...
```

All eight paths are absent and outside the copied artifact root. Yet all eight copied local files have exactly the recorded SHA-256 and size. The evidence content survived; the manifest’s location contract did not.

Because `verify_m7_artifact()` recursively invokes `verify_m5_artifact()` on the nested latent bundle, a copied M7 artifact cannot be independently verified to completion.

### Why this blocks release

JOS presents hashed, relocatable scientific artifacts as a core provenance property. A verifier that depends on the author’s original absolute directory is not an independent verifier. This is not cosmetic metadata; it breaks the promised release-evidence workflow and can make otherwise intact results appear invalid.

### Required correction

1. Record every portable output path relative to **its own artifact directory**, never relative to the repository root.
2. Reject absolute manifest paths and parent traversal (`..`) for portable scientific output records.
3. Preserve repository provenance separately through `git_commit`, source identifiers, and parent artifact hashes—not through filesystem paths.
4. Apply one centralized path-recording contract to M5, observation, ensemble, calibration, M7, and M8 writers.
5. Decide explicitly whether parent/nested artifact references are embedded bundles or external references. An embedded bundle must be self-contained and artifact-relative.

### Mandatory regression tests

- Default in-repository M5 output verifies successfully.
- M5 written outside the repository verifies successfully in place.
- A copied M5 directory verifies after its original is removed.
- A copied M7 directory recursively verifies its embedded M5 after the original is removed.
- M6 observation/ensemble/calibration artifacts verify in place and after copying.
- Absolute paths and `../` traversal are rejected by schema or verifier.
- Hash, size, missing-file, and duplicate-record failures remain detected.

### Evidence consequence

The P1 numerical files are not shown to be wrong. They are shown to be **packaged under a broken portability contract**. The strongest release action is to regenerate or repackage the evidence under corrected manifests and then verify a second copied instance from a different root. Because the final candidate SHA will change, rerunning the final P1 comparator under that exact SHA is preferable to relying on an administrative rewrap.

---

## B02 — Daily `ascertainment_fraction` divides different cohorts

**Severity:** release blocker  
**Affected tier:** M6 observation output contract  
**Primary files:**

- `src/jersey_outbreak/observation.py:151–187`
- `src/jersey_outbreak/observation_scheduler.py:228–269`
- `src/jersey_outbreak/observation_artifacts.py:108–121`
- `tests/test_observation.py:141–162`

### Current calculation

The daily table counts:

- `latent_infections` by **infection date**;
- `detected_infections` by **detection date**;
- `reported_cases` by **report date**.

It then calculates:

```python
ascertainment_fraction = detected_by_date[date] / latent_by_date[date]
```

This ratio compares events from different cohorts.

### Why the mismatch is guaranteed in ordinary use

For symptomatic infections, the scheduler anchors detection at symptom onset. In the generic model, symptom onset equals infectious start, which occurs after a positive latent duration. A further detection delay can then be added. Asymptomatic detection uses infection date as its anchor. Reporting is delayed again from detection.

Consequently, detections on 10 January generally belong to infections acquired on earlier dates, while the denominator is infections acquired on 10 January. The field can:

- exceed 1;
- become null on a day with detections but no new infections;
- fall because incidence rose, even when detection behaviour is unchanged;
- rise because incidence fell, even when detection behaviour is unchanged.

It is therefore neither a cohort ascertainment fraction nor a stable calendar-day surveillance rate.

### What remains valid

The overall diagnostic at `observation.py:258–268` divides total detected infections by total infections across the analysis horizon. With a sufficiently extended tail, that aggregate is coherent. The defect is specifically the daily field and analogous parish/age interpretations where different event dates are mixed under one apparent fraction.

### Why this blocks release

The V1.1 design explicitly prioritizes truthful time semantics and denominator metadata. A field named `ascertainment_fraction` carries a strong scientific interpretation. Publishing a mathematically valid number with the wrong cohort meaning is exactly the category of output-truth defect that previously blocked O2.

### Required correction

Preferred contract:

1. Preserve separate calendar-incidence fields:
   - infections by infection date;
   - detections by detection date;
   - reports by report date.
2. Calculate cohort ascertainment by infection date:
   - numerator = infections acquired on date *d* that are eventually detected within the declared analysis horizon;
   - denominator = all infections acquired on date *d*.
3. Name and document censoring explicitly near the right boundary.
4. If a calendar-date ratio is retained for diagnostics, give it a non-causal descriptive name and do not call it a fraction of infections ascertained.
5. Bump the observation table/manifest schema and its scientific hash contract rather than silently changing the meaning of an existing field.

### Mandatory regression tests

- A delayed symptomatic detection is attributed to the original infection cohort for cohort ascertainment.
- Detection-calendar incidence remains on the actual detection date.
- Report-calendar incidence remains on the actual report date.
- A constructed delayed-detection example cannot produce cohort ascertainment above 1.
- Right-censoring state is explicit when the tail is intentionally inadequate or truncated.
- Aggregate totals reconcile across infection, detection, and report views.

### P1 consequence

The P1 comparison is an M7 latent/intervention baseline, not a calibrated M6 surveillance analysis. This defect does not explain or invalidate the supplied V1.1 epidemic trajectory. It blocks release because the candidate ships the false M6 field as a scientific output.

---

## B03 — `/capabilities` advertises obsolete artifact-schema versions

**Severity:** release blocker  
**Affected tier:** public API compatibility and frontend integration  
**Primary files:**

- `src/jersey_outbreak/api.py:419–425`
- `src/jersey_outbreak/outbreak_schemas.py:203`
- `src/jersey_outbreak/observation_schemas.py:183`
- `src/jersey_outbreak/ensemble_schemas.py:84`
- `src/jersey_outbreak/intervention_artifacts.py:25`
- `src/jersey_outbreak/travel_artifacts.py:21–27`
- `frontend/src/api/mock.ts`

### Advertised versus actual

| Artifact | API advertises | Candidate writes/defaults to | Result |
|---|---:|---:|---|
| M5 outbreak | `1.0` | `1.1` | stale |
| M6 observation | `1.1` | `1.2` | stale |
| M6 ensemble | `1.2` | `1.3` | stale |
| M7 intervention | `2.0` | `2.0` | correct |
| M8 travel | `2.0` | `2.1` | stale |

Four of five values are wrong.

### Why this blocks release

`/capabilities` is the machine-readable declaration of what the running backend supports and emits. False schema versions can cause client compatibility decisions, fixture selection, migrations, or result interpretation to use the wrong contract. This is a public truth error, not stale prose.

### Required correction

- Define schema-version constants once in the owning schema/artifact modules.
- Import those constants into the API and frontend-generated/mock capability data.
- Add tests asserting `/capabilities` equals the current writer defaults/constants.
- Decide whether the endpoint reports “current write version,” “accepted read versions,” or both; those are different concepts and should not share one ambiguous string.
- Include package/release version separately from artifact schema versions.

---

## B04 — Release instructions name the superseded failed branch

**Severity:** release-control blocker  
**Affected tier:** P2/P3 owner procedure  
**Primary files:**

- `.claude/GATES.md:7–15`
- `.claude/FRONTIER.md:9–18, 20–30`

### Current contradiction

`FRONTIER.md` correctly states that:

- `e3609ff2` on `codex/v1.1-o2-denominator` is the corrected candidate;
- `codex/v1.1-integration` at `461bf038` is superseded;
- the fix should not be merged back into the old integration branch.

Yet its branch table still labels the old integration branch as the release candidate, and `GATES.md` asks Steven to merge:

```text
codex/v1.1-integration → main
```

The connected repository confirms that the old branch still points to `461bf038`, the commit whose O2 metadata failed the prior audit. Following the gate literally would omit the correction.

`GATES.md` also leaves the already completed P1 baseline approval gate open, while `FRONTIER.md` simultaneously says P1 is “next” and later says P1 is complete.

### Why this blocks release

The project uses exact branch/SHA control as part of scientific provenance. An owner-only release command that identifies the wrong branch is an immediate operational hazard. A correct implementation is not releasable through an incorrect release procedure.

### Required correction

- Close G2 as completed with the exact run identifier and date.
- Replace every branch-only release instruction with an exact candidate SHA check.
- Name the corrected branch or create a new clean `codex/v1.1-release` branch at the final repaired SHA.
- Require `git rev-parse HEAD` to equal the audited SHA immediately before merge/tag.
- Rewrite the live branch table so only one branch is labelled current candidate.
- Remove the stale “P1 next” sentence.
- After the new blocker corrections, do not continue calling `e3609ff2` the candidate; establish and audit the new exact SHA.

---

## 5. Major non-blocking findings that should be closed in the same release cycle

## M01 — Project and API version identity remains `0.1.0`

The package metadata, Python `__version__`, and frontend package remain `0.1.0`; the Python package docstring still says “Milestone 0.” The intended release tag is `jos-v1.1.0`, and the API exposes package metadata.

This may reflect an undeclared distinction between product release version and package version, but no such distinction is documented. Before release, either align all user-visible product/package versions to `1.1.0` or define separate version domains explicitly and expose them without ambiguity.

The root README is also materially stale: it says there is no frontend/UI and that M10 is still in progress, despite the completed interactive application and prior V1 release.

## M02 — Travel diagnostics overclaim two integrity checks

At `travel.py:2692`, the diagnostic called `resident_ids_unchanged` evaluates:

```python
generated.agent_ids == sorted(generated.agent_ids)
```

That tests whether IDs are sorted, not whether they remained unchanged. The implementation appears to preserve resident identity, and travel tests exercise important identity behaviour, but this particular diagnostic does not prove its label.

In addition, the top-level travel diagnostics set `"status": "passed"` unconditionally while embedding an `inactive_slot_audit` containing multiple booleans. If one of those predicates were false without an earlier exception, the artifact could still publish passed status.

Required closure:

- snapshot resident IDs before temporary-agent operations and compare exact sequence/set afterward;
- derive status from all declared invariant predicates or raise immediately on failure;
- add mutation/failure-injection tests;
- have the verifier independently recompute or validate the critical invariants it claims to trust.

## M03 — Release CI does not durably encode the full release gate

The exact candidate’s backend CI is real and strong. However, the workflow does not currently make the whole release procedure durable. The prior manual audit reports successful frontend tests, TypeScript checking, production build, lock validation, compilation, and a broader mypy scope, but those are not all enforced on every candidate push by the current CI workflow.

Add required jobs for:

- frontend unit tests;
- TypeScript checking;
- production frontend build;
- `uv lock --check`;
- `python -m compileall`;
- the documented full mypy target list;
- default-location scientific artifact generation and verification;
- relocation verification;
- API capability/schema consistency.

A green backend workflow should not be described as the entire release gate until it is.

## M04 — The planned “30-replicate 95% band” conflicts with JOS’s own quantile rule

The V1.1 implementation correctly requires:

```text
n × min(q, 1 − q) ≥ 1
```

For 2.5% and 97.5% empirical quantiles, at least **40 successful replicates** are required. Thirty successful runs cannot emit the requested 95% stochastic replicate interval under the project’s own rule.

P4 must therefore choose one of the following deliberately:

- run at least 40 successful replicates, preferably more after checking estimate stability; or
- retain 30 and report median/IQR plus explicitly labelled sample extrema, with no 2.5/97.5 band.

These are stochastic replicate quantiles, not confidence intervals. Later posterior-predictive or parameter-draw intervals must be labelled separately from process-seed variation.

---

## 6. Scientific implementation assessment

The release is blocked by output and control contracts, **not by a finding that the core V1.1 model redesign is scientifically backwards**. The following distinctions matter.

| Area | Assessment | Reasoning |
|---|---|---|
| Episode duration architecture | **PASS** | Constant and gamma mechanisms exist; gamma draws are deterministic per episode/seed; zero-CV behaviour is exact. Distribution shape matters in epidemic dynamics, so support is valuable. |
| Generic duration defaults | **PASS BY DESIGN** | The generic demo does not invent unsupported non-zero CVs. Mechanism support is not misrepresented as evidence-backed activation. |
| Immunity waning | **PASS WITH DISCLOSURE** | Complete 30-day reset is removed from the generic V1.1 default. A frozen comparator preserves V1 behaviour. This avoids an unjustified generic reinfection engine. |
| Symptom timing | **PASS** | Natural history owns symptom onset; generic symptomatic onset equals infectious start. No unsupported presymptomatic infectiousness profile is silently invented. |
| Stable adherence | **PASS** | Agent-level adherence is persistent across days rather than redrawn independently each day. |
| Vaccine uptake separation | **PASS** | Uptake and general NPI adherence are not conflated into one latent trait. |
| Contact heterogeneity mechanism | **PASS / DEFAULT NEUTRAL** | Persistent mean-one gamma activity exists with an exact zero-CV bypass; shipped generic default remains neutral. |
| Community/institution overlap | **PASS** | Care/medical residents are excluded from the general community pool where intended; legitimate staff/community participation remains possible. |
| School geography | **PASS WITH S1 DEFERRED** | Synthetic school placement is labelled non-geographic. Single-year/site-level fidelity is deferred rather than fabricated. |
| Travel identity lifecycle | **SUBSTANTIVELY PASS** | Preallocated slots, event-time identity, repeat-return handling, and inactive-slot exclusion are well tested. Diagnostic proof labels still need M02 closure. |
| Output denominator redesign | **MOSTLY PASS** | Resident/present and arrived-visitor denominators are much clearer; the O2 correction is valid. B02 shows the same scrutiny was not applied consistently to daily observation cohorts. |
| Source-episode attribution | **APPROPRIATELY DEFERRED** | Exact causal source identity is not overclaimed. Route attribution remains a model event classification, not causal epidemiological proof. |
| Performance work | **PASS AS A DECISION NOT TO OPTIMIZE** | R6 correctly avoids a risky rewrite without equivalence evidence. Performance should follow calibration and profiling, not precede scientific validity. |

### Scientific bottom line

V1.1 should continue to be described as a **synthetic, research-grade outbreak simulator with Jersey-informed population structure**, not a validated forecasting model of Jersey. The current mechanisms are useful for experimentation. They do not, by themselves, establish that default biological, behavioural, travel, or route parameters match any named pathogen or historical Jersey outbreak.

---

## 7. Assessment of the full-population V1.0↔V1.1 comparison

### 7.1 Supplied result

The filed P1 run uses:

- 104,540 resident agents;
- seed 123;
- 180 dated output days;
- no explicit interventions or travel/import stream in the comparison scenario;
- the corrected V1.1 candidate line as documented by the run package.

The report records, for V1.1:

- 81,384 infection episodes;
- 81,384 uniquely infected people;
- 77.85% ever infected;
- exact one episode per infected person;
- extinction on 27 March 2025;
- broadly stable route composition;
- mean realised generation interval 3.667 days versus 3.652 in V1;
- approximately 27% longer runtime, with lower recorded peak RSS.

### 7.2 Interpretation

The dominant change is unsurprising and internally coherent: V1’s complete 30-day waning allowed repeated infection, whereas the V1.1 generic default does not return recovered agents to susceptibility during the horizon. The episode-per-person ratio falling from roughly 2.97 to exactly 1.00 is therefore evidence that the waning change took effect—not evidence that V1.1 is empirically calibrated.

The stable generation interval and modest route-share movement suggest the natural-history and structural changes did not create an obvious timing or routing discontinuity in this single-seed scenario. The 27% runtime increase is an engineering signal for profiling, not a scientific blocker.

### 7.3 What the P1 run can and cannot establish

It supports:

- conservation and identity reconciliation for this run;
- coherent removal of short complete waning;
- absence of an obvious one-seed catastrophic regression;
- a frozen comparator for subsequent engineering and scientific checks.

It does not establish:

- fit to Jersey cases, tests, serology, admissions, deaths, or travel prevalence;
- calibrated route-specific transmission;
- predictive accuracy;
- uncertainty coverage;
- robustness across seeds or parameters;
- causal correctness of route attribution;
- superiority over V1 against observed outcomes.

### 7.4 Evidence-package conclusion

The copied tables are content-intact against their recorded hashes. The package is not portable under its own recursive verifier because of B01. Therefore the correct wording is:

> **No numerical release concern was identified in the supplied P1 comparison, but its copied scientific-evidence package does not satisfy independent relocatable verification.**

---

## 8. Required V1.1 recovery sequence

Do not open broad V2 development while fixing this. Use a small, auditable release-repair branch.

### R0 — Establish one new exact correction line

Create a new branch from `e3609ff2`, for example `codex/v1.1-release-corrections`. Record the starting SHA. Do not mutate the old candidate branch or revive the superseded integration branch.

### R1 — Correct scientific output contracts

Implement, in one bounded sequence:

1. artifact-directory-relative paths across M5/M6 and all embedded artifacts;
2. strict rejection of absolute/traversing portable records;
3. relocation/default-output/nested verification tests;
4. cohort-correct daily ascertainment semantics;
5. M6 schema and scientific-hash version bump;
6. API capability values sourced from live schema constants;
7. travel invariant/status diagnostic corrections.

Avoid unrelated model changes.

### R2 — Correct release identity and operating state

- Set or document product/package/frontend/API versions coherently.
- Rewrite README current status.
- Close completed gates.
- identify one release branch and one exact candidate SHA.
- Replace branch-only merge directions with SHA checks.

### R3 — Run the complete exact-SHA gate

At the new candidate SHA, require:

- locked Python 3.12.13 environment;
- all backend tests;
- frontend tests, typecheck, and production build;
- Ruff lint and format;
- full documented mypy scope;
- lockfile check and compileall;
- default CLI artifact generation;
- in-place verifier pass;
- copied/relocated verifier pass after deleting or making the original inaccessible;
- recursive M7→M5 relocation verification;
- API capability/version contract tests;
- clean worktree and exact HEAD attestation.

### R4 — Regenerate final release evidence

Because the release candidate SHA changes, rerun the full 180-day V1.1 comparator under the corrected exact SHA. The fixes should not materially alter the latent epidemic trajectory, but exact-commit provenance is stronger than claiming equivalence across candidates.

Package the resulting M7/M5 bundle, copy it to a second arbitrary directory, and verify the copy. Preserve both the command transcript and verifier output. Refile the V1↔V1.1 comparison, explicitly distinguishing any schema-only/output-only delta from trajectory delta.

### R5 — Independent bounded re-audit

The re-audit should verify:

- all four blockers closed;
- no unrelated scientific change;
- schema migrations/versioning are explicit;
- old artifact read support is deliberate rather than accidental;
- exact-SHA gates and relocated evidence pass;
- current release instructions point to that exact SHA.

Only then should Steven merge the exact audited candidate into `main` and create `jos-v1.1.0`.

---

## 9. Refined V1.x scope: the minimum path to a defensible calibrated tier

The current P5 list is too broad to treat as one milestone. Calibration should be earned through staged evidence, observation semantics, recoverability, and held-out validation. The first calibrated tier should be intentionally narrow.

## V1.2 — Evidence and observation foundation

### Objective

Make Jersey observations reproducible and semantically compatible with the simulator before estimating transmission parameters.

### Include

1. **Immutable official source snapshots**
   - cases by specimen/test/report date where available;
   - tests and positivity;
   - community serology rounds with sample universe and uncertainty;
   - intervention and vaccination timeline;
   - population denominator revisions;
   - documented reporting-regime changes.

2. **Canonical epidemiology tables**
   Every measure should carry:
   - source ID and immutable hash;
   - extraction date and revision/version;
   - event-date definition;
   - geography and population universe;
   - units and denominator;
   - suppression/bounds semantics;
   - reporting regime;
   - known exclusions and caveats.

3. **Observation-time correctness**
   - infection, symptom, test, detection, report, admission, and death dates remain distinct;
   - delayed and right-censored outcomes are explicit;
   - suppression such as `<5` is not silently converted to zero or a midpoint;
   - tests and ascertainment are modelled jointly rather than cases alone.

4. **Data-quality diagnostics**
   - duplicate/revision checks;
   - missing-date and regime-boundary flags;
   - reconciliation against published totals;
   - machine-readable disclosure report.

### Exclude

- automated live scraping as a runtime dependency;
- record-level personal or facility reconstruction;
- unofficial estimates filling official data gaps without a separate scenario label;
- calibration during the same milestone.

### Exit gate

A cold-started auditor can reproduce every calibration input from frozen source snapshots and explain exactly what each row measures.

---

## V1.2.1 — Synthetic recovery and identifiability gate

### Objective

Prove the calibration machinery can recover known parameters under controlled conditions before fitting Jersey data.

### Include

- generate synthetic observations from known parameters;
- recover those parameters across multiple process seeds;
- test coverage/bias under the intended observation model;
- inject plausible misspecification and show where recovery fails;
- inspect parameter trade-offs with profile likelihoods, posterior geometry, or equivalent sensitivity views;
- negative controls where a parameter should remain unidentifiable;
- deterministic fixtures for objective-function and likelihood calculations.

### Initial fitted dimensions

Keep the first problem small. A reasonable ceiling is three to five effective dimensions:

- one global transmission scale;
- initial prevalence or seeding timing;
- broad import pressure if the chosen era requires it;
- one or two ascertainment/testing-regime parameters.

Keep route multipliers, detailed behavioural effects, and most disease-natural-history parameters fixed to declared evidence or scenario assumptions until data can identify them.

### Exit gate

The pipeline recovers synthetic truth within predeclared tolerances and exposes non-identifiability rather than returning falsely precise estimates.

---

## V1.3 — First named-pathogen Jersey calibration

### Recommended target

Use a bounded historical COVID-19 era because Jersey has the richest public combination of cases, testing, intervention history, vaccination information, and community antibody surveys. Select the era only after the data inventory establishes stable definitions and a defensible observation model.

### Design rules

- Predeclare training and holdout windows.
- Treat testing/reporting regimes as explicit observation regimes.
- Fix or strongly constrain biological timing with external evidence rather than estimating everything from Jersey aggregate cases.
- Fit only the small identifiable parameter set proven in synthetic recovery.
- Use serology to constrain cumulative infection, not merely case-curve shape.
- Jointly compare cases, tests/positivity, and serology where definitions permit.
- Separate imported infections from local transmission where data can support only a broad import process.
- Document every fixed parameter and every inferred parameter distinctly.

### Validation

A model should not earn “calibrated” status solely by matching its training curve. Require:

- held-out temporal prediction;
- held-out or cross-check serology;
- parish/age comparisons only when not already used for fitting and when denominators are sound;
- residual checks around reporting-regime changes;
- baseline comparison against a simpler model;
- sensitivity to alternative plausible observation assumptions.

### Exit gate

The calibrated model beats a declared simple baseline on held-out targets, maintains reconciliation/conservation, and presents parameter and model uncertainty without claiming unsupported Jersey-specific precision.

---

## V1.3.1 — Calibrated ensembles and uncertainty decomposition

Do not collapse all uncertainty into one band.

Report separately:

1. **Process uncertainty:** different stochastic seeds at fixed parameters.
2. **Parameter uncertainty:** posterior or accepted parameter draws.
3. **Observation uncertainty:** reporting, testing, delay, and measurement processes.
4. **Scenario uncertainty:** alternative defensible structural assumptions.
5. **Model discrepancy:** residual mismatch the model does not explain.

For 2.5/97.5 empirical process quantiles, require at least 40 successful replicates under the existing rule; use more if quantile estimates remain unstable. Determine final replicate count through convergence/stability diagnostics rather than treating 40 as a precision guarantee.

Use labels such as:

- “stochastic replicate quantile” for seed variation;
- “parameter-draw outcome interval” for parameter uncertainty;
- “posterior predictive interval” only when it genuinely integrates the declared posterior and observation process.

Never relabel these automatically as confidence intervals.

---

## V1.4 — Structural validation and only then selective enrichment

Add structural detail only where it changes a decision-relevant result and has frozen evidence.

Priority candidates:

- single-year ages and authoritative school/site inventory;
- household and communal-resident age validation;
- worker age/sex and sector distributions;
- workplace size heavy tail;
- parish-level population and commuting controls;
- car access or mobility constraints by parish;
- travel volume, residence status, length of stay, and broad composition;
- reciprocal age/contact mixing diagnostics;
- care and medical staffing/contact validation.

For each addition, require:

- an immutable source;
- a measurable target;
- a before/after validation report;
- a declared fallback when data are absent;
- evidence that added complexity improves held-out behaviour or a necessary structural metric.

Do not infer causal route shares from matching aggregate cases.

---

## 10. V2 scope: only after the calibrated tier passes

V2 should mean **validated named-pathogen modelling**, not merely more mechanisms.

Potential V2 capabilities, in order of scientific dependency:

1. **Named-pathogen infectiousness profile**
   - presymptomatic and time-since-infection infectiousness;
   - generation-interval validation;
   - explicit relation between latent, incubation, and infectious periods.

2. **Partial and waning immunity**
   - reinfection susceptibility rather than complete reset;
   - variant or antigenic-era handling where data justify it;
   - vaccination and prior infection as distinct protection states.

3. **Severity pathway**
   - symptomatic severity, admission, ICU, death, and recovery delays;
   - only with defensible outcome definitions and denominators;
   - age/risk effects declared as evidence-backed or uncertain.

4. **Infected traveller state**
   - imported prevalence by time/route;
   - backdated infection stage at arrival;
   - returning-resident versus visitor semantics;
   - uncertainty in passenger movements and length of stay.

5. **Richer institutions and mobility**
   - schools, workplaces, care, healthcare, and transport topology only where Jersey evidence exists;
   - geographically meaningful movement rather than proxy geography presented as fact.

6. **Behavioural response**
   - risk perception, fatigue, voluntary distancing, and testing behaviour only if informed by data or explicit scenario distributions;
   - stable traits and dynamic state kept separate.

7. **Formal model discrepancy and decision analysis**
   - alternative structural models;
   - transparent scenario comparison;
   - decision metrics that retain uncertainty decomposition.

8. **Performance engineering**
   - profile the calibrated workload;
   - optimize the dominant bottleneck;
   - require exact or bounded scientific-equivalence tests before replacing algorithms.

V2 should not begin until V1.x has at least one named-pathogen calibration with synthetic-recovery evidence and held-out validation. Otherwise added biological detail will mostly increase the number of unconstrained degrees of freedom.

---

## 11. Features to cut or defer

The following should not enter the immediate roadmap unless new evidence changes the case:

- non-zero pathogen-neutral CV defaults merely because gamma support exists;
- additional generic duration families without a named use case;
- fitting all 11 route multipliers to aggregate case counts;
- fitting every intervention multiplier simultaneously;
- exact causal source-person claims from stochastic route attribution;
- causal interpretation of model route shares;
- bus-network or school/care topology calibrated from proxies alone;
- person-level or facility-level reconstruction from unavailable data;
- live data ingestion as a requirement for reproducible historical calibration;
- severity/hospital forecasting before outcome definitions and denominators are secured;
- dynamic behavioural feedback without behavioural observations;
- non-zero generic seasonality or infected-traveller defaults without named-pathogen evidence;
- surrogate/emulator complexity before the small direct calibration problem is profiled;
- major performance rewrites before scientific equivalence is pinned;
- “30-run 95% uncertainty bands”;
- UI polish that implies validation before the model has earned it.

---

## 12. Recommended project-control changes

These are secondary to the scientific fixes but will prevent recurrence.

1. **One canonical release-state file.** Generate branch/SHA/gate summaries elsewhere from it or validate them for contradiction.
2. **SHA-first release commands.** Branch names are convenient pointers, not immutable release identities.
3. **Portable-artifact contract test in CI.** Generate, copy, delete original, verify copy.
4. **Schema constants as code authority.** API and frontend consume them rather than duplicating strings.
5. **Semantic output tests.** Test cohort meaning and denominator membership, not only column presence and aggregate reconciliation.
6. **Evidence bundle self-test.** The final release archive should include a machine-readable verification transcript produced from the copied archive itself.
7. **Explicit version domains.** Product, Python package, frontend package, API, and artifact schema versions should be distinct only when intentionally documented.
8. **No automatic “passed” diagnostic.** Status must be derived from named predicates or from a verifier that recomputes them.

---

## 13. What is already good enough to preserve

Do not throw away the architecture in response to these findings. Preserve:

- one-to-one resident identity;
- deterministic seeded generation and event streams;
- explicit synthetic/non-geographic labels;
- separation of natural history, observation, intervention, and travel layers;
- immutable artifact IDs and content hashes;
- frozen V1 comparator semantics;
- mechanism/default separation;
- neutral defaults when evidence is absent;
- explicit output denominator metadata;
- paired-seed comparison machinery and caveats;
- the decision not to optimize before equivalence can be proven.

The project’s strongest trait is its growing refusal to hide uncertainty behind plausible-looking defaults. The blockers found here are failures to apply that same standard consistently to paths, daily cohorts, API declarations, and release instructions.

---

## 14. External scientific checkpoints used for the forward scope

These sources informed the calibration and uncertainty recommendations; they did not determine the repository-code findings:

- A. L. Lloyd (2001), **“Realistic distributions of infectious periods in epidemic models: changing patterns of persistence and dynamics.”**
- H. J. Wearing, P. Rohani, and M. J. Keeling (2005), **“Appropriate Models for the Management of Infectious Diseases.”**
- D. Champredon, J. Dushoff, and D. J. D. Earn (2015), work distinguishing intrinsic and realised generation intervals.
- A. Hazelbag and colleagues (2020), **“Calibration of individual-based models to epidemiological data: a systematic review.”**
- M. Horii and colleagues (2024), **“Calibration verification for stochastic agent-based disease spread models.”**
- D. P. Lizarralde-Bejarano and colleagues (2020), **“Sensitivity, uncertainty and identifiability analyses to define a dengue transmission model with real data.”**
- Government of Jersey open data for COVID-19 cases, PCR tests, rates, and deaths.
- Statistics Jersey/Government of Jersey community antibody survey reports from May and June 2020, including their population-universe and test-performance caveats.

---

## 15. Final decision

The candidate is close in implementation scope but not close enough in release-contract quality. The corrections are bounded and should not require revisiting the core V1.1 science. Nevertheless, merging now would knowingly ship:

- evidence that cannot be independently verified after copying;
- a daily observation statistic with a false scientific name;
- a public API that lies about four schema versions; and
- owner instructions that point to the superseded failed commit.

That is incompatible with JOS’s stated standard of truthful, reproducible scientific software.

**Required next state:** one corrected exact SHA, all four blockers closed, complete CI and relocation gates green, regenerated exact-SHA P1 evidence, and a bounded independent re-audit.

# JOS V1.1 RELEASE-CANDIDATE BLOCKED
