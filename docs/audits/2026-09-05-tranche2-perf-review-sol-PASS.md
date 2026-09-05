# JOS tranche-2 independent review

- Candidate: `ac04bbb50aaea1070a4fbd5d645062e7470c4f3c`
- Base: `8f806f13e5c2531dea87d2765ef8616c748b4f11`
- Clone: `/tmp/jos-tranche2-review`
- Date: 2026-09-05
- Model: OpenAI Codex (GPT-5)
- Role: independent read-only auditor

## Findings

MINOR — [hashing.py](/tmp/jos-tranche2-review/src/jersey_outbreak/hashing.py:38): the new generic streaming helper is not equivalent outside its stated string-keyed JSON domain.

- `{1: "x"}` was serialized by the old encoder but now raises `AssertionError`.
- A nested Pydantic `BaseModel` inside a streamed container can now serialize where the old monolithic encoder raised `TypeError`.
- Iterators are intentionally one-shot; hashing the same iterator payload twice produces an empty array the second time.

These cases cannot occur in the supported M4 payload: route specs and records are normalized plain dictionaries/lists with string keys, and each snapshot generator is created and consumed exactly once. Actual M4 eager-byte equality is tested directly. No protected output is affected.

MINOR — [starsim_adapter.py](/tmp/jos-tranche2-review/src/jersey_outbreak/starsim_adapter.py:30): `PlainMetadataBoundary` is not pickleable because it stores a local lambda; `deepcopy` succeeds but retains the original closure-owned mapping.

There is no current serialization or deepcopy path for these objects:

- Starsim is constructed with `copy_inputs=False`.
- Ensemble jobs contain M2/M3 inputs and configuration; workers regenerate M4 and construct networks/schedulers locally.
- M9 workers cross the process boundary using job identifiers and persisted JSON.
- The required live spawn-pool test completed with two workers.

## Step 1 — diff and behavioural review

Command:

```text
git diff 8f806f1 ac04bbb -- src
git diff --stat 8f806f1 ac04bbb -- src tests scripts
```

Trimmed result:

```text
10 files changed, 1102 insertions(+), 76 deletions(-)
```

The source changes are confined to the three declared units.

### PERF-3

Potential differences reviewed:

- Dictionary framing, sorting, escaping, floats, `NaN`/infinity, tuples and nested `edges`.
- Non-string keys and nested `BaseModel` leaves.
- One-shot iterator consumption.
- Deferred snapshot generation and LRU-cache order.

For supported values, independently tested `NaN`, infinities, Unicode, tuples, negative zero and nested `edges` all produced byte-identical output. The old and new snapshot traversals are both sorted route-major/configured-date-minor. Nothing accesses the snapshot cache between generator creation and consumption, and [route_snapshot](/tmp/jos-tranche2-review/src/jersey_outbreak/network_generator.py:125) is a deterministic function of route/date; its cache only memoizes and evicts results.

Coverage:

- Random JSON byte equality: [test_hashing.py](/tmp/jos-tranche2-review/tests/test_hashing.py)
- Actual M4 payload eager-byte equality and golden hash: [test_m4_hash_stream.py](/tmp/jos-tranche2-review/tests/test_m4_hash_stream.py)
- CI/scaled golden M4 hashes and independent seed-124 base comparison.

### PERF-2

The transformations are exact:

- More than one remaining workplace implies every unused candidate has at least one non-primary slot.
- With one workplace, `counter[primary] < len(remaining_slots)` is true exactly when that workplace differs from the candidate’s primary workplace.
- With zero workplaces, both implementations reject because eligibility is empty.
- Removing a selected unique agent from `available_candidates` preserves the original shuffled order and therefore the next eligible-list order.
- Generated agent IDs are already strings; dropping `str(...)` changes no value.
- Generated structures have exactly one primary job per worker, so the index selects the same record as the former `next(...)`.

The oracle is a verbatim copy of the base loop and compares jobs, slots, secondary workers and final PCG64 state for seeds 123 and 124.

Independent NumPy 2.5.2 probe:

```text
PASS numpy=2.5.2 seeds=257
lengths=(1, 2, 63, 64, 1000, 50000)
choices_and_subsequent_PCG64_state_identical
```

### PERF-1

Repository-wide grep found:

- No outside reader of the dynamic-network `_uid_by_agent_id` mapping other than the new proof test.
- No setter for the scheduler properties.
- Existing mutation through `scheduler.agent_id_by_uid[...]` remains valid because the property returns the same mutable dictionary.
- No production pickle/deepcopy call for networks or schedulers.

Pinned sciris 3.3.0 `IterObj` traverses an object’s `__dict__` or declared slots. It sees the stored callable but does not inspect closure cells. Starsim 3.5.2 therefore continues ordinary Dist/Rate discovery without visiting the hidden mappings.

The independent base-vs-branch harness reported:

```text
ordered_distribution_and_rate_paths_equal: true
distribution_seeds_and_rng_states_equal: true
initialized_arrays_bit_equal: true
all_route_and_array_fingerprints_equal: true
all_scientific_hashes_equal: true
lifecycle_and_consumer_order_equal: true
route_test_exit_code: 0
```

The measured-hotspot prerequisite is present in the specified independent [Astra performance audit](/tmp/jos-tranche2-review/docs/audits/2026-09-05-astra-performance-audit.md:222): PERF-1 discovery, PERF-2’s secondary-job loop, and PERF-3’s transient M4 hash allocation were all measured before implementation.

## Step 2 — prescribed test surface

Command: the exact 16-file `uv run pytest -q ...` command from the protocol, with `UV_CACHE_DIR=/tmp/uv-cache` because the default cache was read-only.

Result:

```text
146 passed, 4 warnings in 537.36s (0:08:57)
```

Warnings were one Starlette deprecation and three expected one-day Starsim timeline warnings. No failure occurred.

## Step 3 — independent equivalence probes

Base was created exactly from `git archive` and synchronized frozen:

```text
git archive 8f806f13e5c2531dea87d2765ef8616c748b4f11 |
  tar -x -C /tmp/jos-review-base
UV_CACHE_DIR=/tmp/uv-cache uv sync --frozen
```

CI seed 124, M2→M3→M4 plus 30-day online outbreak:

| Protected result | Base and candidate |
|---|---|
| M2 | `bc0f0ddc2cd883a8045c30c05ae89faeec07c39bc36b7384e9e2fa605182ff48` |
| M3 | `a137e9a303ee15bb3180009c6eaeb346fc4f86392be4030462f90efc8abd9a4f` |
| M4 | `02b3819d22343edf3fc07e4580852f4c3d4cdb5fd44f04a986405d5f162b1cd6` |
| Latent | `539fdd431cee3b700e90a141305d16a051b29b504a12d243137b80a3761bb669` |
| Latent outcome | `5d98808fd39309808c21558ce09d59e832613813fedac3eb38ab2ec512062240` |
| Observation | `437ad45ef12959671244007b56f7f0686e35e8876f23b682c5e3790c7de87f1a` |
| Transmission events | `2174` |

Process-boundary smoke:

```text
pool execution_mode: process_pool_spawn
pool actual_workers: 2
sequential execution_mode: sequential
sequential actual_workers: 1
replicate_records_protected_fields_equal: True
```

Both seeds 124 and 125 matched on status, M4 hash, latent hash, observation hash, scenario hash, intervention hashes and error state.

## Step 4 — conclusion

Base ancestry was verified (`ancestor_exit=0`). Final state:

```text
## HEAD (no branch)
ac04bbb50aaea1070a4fbd5d645062e7470c4f3c
```

`git diff --exit-code` passed and `git status --short` showed no tracked or untracked changes. The two minor generic-wrapper caveats have no reachable path to a protected scientific output. All exact-equivalence gates exercised here passed.

TRANCHE-2 REVIEW: PASS