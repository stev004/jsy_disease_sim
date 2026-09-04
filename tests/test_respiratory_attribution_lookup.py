from __future__ import annotations

import inspect
from collections import defaultdict
from struct import pack
from typing import Any

import numpy as np
import pytest

import jersey_outbreak.respiratory as respiratory
from jersey_outbreak.respiratory import RespiratorySEIRS, _match_success_hazards


class _RawValues:
    def __init__(self, values: Any) -> None:
        self.raw = values


def _old_lookup(
    rel_trans: _RawValues,
    rel_sus: _RawValues,
    src: np.ndarray,
    trg: np.ndarray,
    beta_per_dt: np.ndarray,
    target_uids: np.ndarray,
    source_uids: np.ndarray,
    route_id: str = "route",
    network_index: int = 0,
) -> dict[int, list[dict[str, float | int | str]]]:
    """Reference implementation copied from the pre-Stage-2 attribution block."""
    candidates_by_target: dict[int, list[dict[str, float | int | str]]] = defaultdict(list)
    probability_by_pair: dict[tuple[int, int], list[float]] = defaultdict(list)
    for source, target, probability in zip(src, trg, beta_per_dt, strict=True):
        pair = (int(source), int(target))
        probability_by_pair[pair].append(
            float(rel_trans.raw[pair[0]] * rel_sus.raw[pair[1]] * probability)
        )
    for target, source in zip(target_uids, source_uids, strict=True):
        pair = (int(source), int(target))
        probabilities = probability_by_pair[pair]
        probability = probabilities.pop(0)
        candidates_by_target[pair[1]].append(
            {
                "route_id": route_id,
                "network_index": network_index,
                "source": pair[0],
                "hazard": max(0.0, min(1.0, probability)),
            }
        )
    return candidates_by_target


def _indexed_lookup(
    rel_trans: _RawValues,
    rel_sus: _RawValues,
    src: np.ndarray,
    trg: np.ndarray,
    beta_per_dt: np.ndarray,
    target_uids: np.ndarray,
    source_uids: np.ndarray,
    route_id: str = "route",
    network_index: int = 0,
) -> dict[int, list[dict[str, float | int | str]]]:
    candidates_by_target: dict[int, list[dict[str, float | int | str]]] = defaultdict(list)
    for pair, probability in _match_success_hazards(
        src,
        trg,
        beta_per_dt,
        rel_trans.raw,
        rel_sus.raw,
        target_uids,
        source_uids,
    ):
        candidates_by_target[pair[1]].append(
            {
                "route_id": route_id,
                "network_index": network_index,
                "source": pair[0],
                "hazard": probability,
            }
        )
    return candidates_by_target


def _run_directions(lookup, fixture: dict) -> dict[int, list[dict]]:
    candidates_by_target: dict[int, list[dict]] = defaultdict(list)
    for direction in fixture["directions"]:
        candidates = lookup(
            fixture["rel_trans"],
            fixture["rel_sus"],
            direction["src"],
            direction["trg"],
            direction["beta"],
            direction["targets"],
            direction["sources"],
            direction["route_id"],
            direction["network_index"],
        )
        for target, target_candidates in candidates.items():
            candidates_by_target[target].extend(target_candidates)
    return candidates_by_target


def _assert_equivalent(old: dict[int, list[dict]], new: dict[int, list[dict]]) -> None:
    assert list(old) == list(new)
    for target in old:
        assert len(old[target]) == len(new[target])
        for old_candidate, new_candidate in zip(old[target], new[target], strict=True):
            assert {key: value for key, value in old_candidate.items() if key != "hazard"} == {
                key: value for key, value in new_candidate.items() if key != "hazard"
            }
            assert pack("d", old_candidate["hazard"]) == pack("d", new_candidate["hazard"])


@pytest.fixture
def lookup_fixture() -> dict:
    return {
        "rel_trans": _RawValues(np.array([0.25, 0.5, 1.0, np.nextafter(0.0, 1.0)])),
        "rel_sus": _RawValues(np.array([0.125, 0.75, 1.0, np.finfo(float).tiny])),
        "directions": [],
    }


def _direction(
    route_id: str,
    network_index: int,
    src: list[int],
    trg: list[int],
    beta: list[float],
    successes: list[tuple[int, int]],
) -> dict:
    return {
        "route_id": route_id,
        "network_index": network_index,
        "src": np.array(src, dtype=np.int64),
        "trg": np.array(trg, dtype=np.int64),
        "beta": np.array(beta, dtype=float),
        "targets": np.array([target for target, _source in successes], dtype=np.int64),
        "sources": np.array([source for _target, source in successes], dtype=np.int64),
    }


def test_fixture_cases_preserve_fifo_candidates(lookup_fixture: dict) -> None:
    cases = [
        [_direction("no-success", 0, [0, 1], [1, 0], [0.4, 0.6], [])],
        [_direction("single", 0, [0], [1], [0.4], [(1, 0)])],
        [
            _direction(
                "duplicate",
                0,
                [0, 0],
                [1, 1],
                [0.1, 0.9],
                [(1, 0), (1, 0)],
            )
        ],
        [
            _direction("route-a", 0, [0, 1], [1, 0], [0.2, 0.3], [(1, 0)]),
            _direction("route-b", 1, [0], [1], [0.8], [(1, 0)]),
            _direction("reverse", 2, [1, 0], [0, 1], [0.4, 0.6], [(0, 1), (1, 0)]),
        ],
        [
            _direction(
                "repeated-successes",
                0,
                [0, 0, 0],
                [1, 1, 1],
                [0.05, 0.35, 0.95],
                [(1, 0), (1, 0), (1, 0)],
            )
        ],
    ]
    for directions in cases:
        lookup_fixture["directions"] = directions
        _assert_equivalent(
            _run_directions(_old_lookup, lookup_fixture),
            _run_directions(_indexed_lookup, lookup_fixture),
        )

    duplicate = cases[2][0]
    lookup_fixture["directions"] = [duplicate]
    duplicate_candidates = _run_directions(_indexed_lookup, lookup_fixture)[1]
    hazards = [candidate["hazard"] for candidate in duplicate_candidates]
    assert hazards == [0.018750000000000003, 0.16875]


def test_packing_supports_uids_just_below_the_bound() -> None:
    bound = 2**32
    source = bound - 2
    target = bound - 1
    fixture = {
        "rel_trans": _RawValues({source: 0.5}),
        "rel_sus": _RawValues({target: 0.25}),
        "directions": [
            _direction(
                "near-bound",
                0,
                [source],
                [target],
                [0.8],
                [(target, source)],
            )
        ],
    }
    _assert_equivalent(
        _run_directions(_old_lookup, fixture),
        _run_directions(_indexed_lookup, fixture),
    )
    assert _run_directions(_indexed_lookup, fixture)[target][0]["hazard"] == 0.1


def test_success_sequence_can_be_permuted_relative_to_edge_order(lookup_fixture: dict) -> None:
    direction = _direction(
        "permuted",
        4,
        [10, 11, 10, 12],
        [20, 21, 20, 22],
        [0.1, 0.2, 0.9, 0.4],
        [(22, 12), (20, 10), (21, 11), (20, 10)],
    )
    permuted_fixture = {
        "rel_trans": _RawValues({10: 0.25, 11: 0.5, 12: 1.0}),
        "rel_sus": _RawValues({20: 0.125, 21: 0.75, 22: 1.0}),
        "directions": [direction],
    }
    _assert_equivalent(
        _run_directions(_old_lookup, permuted_fixture),
        _run_directions(_indexed_lookup, permuted_fixture),
    )


def test_zero_successes_on_large_edge_set_do_not_construct_candidates() -> None:
    size = 100_000
    direction = _direction(
        "large-empty",
        5,
        list(range(size)),
        list(range(1, size + 1)),
        [0.25] * size,
        [],
    )
    large_fixture = {
        "rel_trans": _RawValues(np.ones(size, dtype=float)),
        "rel_sus": _RawValues(np.ones(size + 1, dtype=float)),
        "directions": [direction],
    }
    _assert_equivalent(
        _run_directions(_old_lookup, large_fixture),
        _run_directions(_indexed_lookup, large_fixture),
    )


def test_more_than_threshold_successes_on_large_edge_set_match_oracle() -> None:
    size = 100_000
    success_count = 128
    direction = _direction(
        "large-many-successes",
        6,
        list(range(size)),
        list(range(1, size + 1)),
        [0.25] * size,
        [(index + 1, index) for index in reversed(range(success_count))],
    )
    large_fixture = {
        "rel_trans": _RawValues(np.ones(size, dtype=float)),
        "rel_sus": _RawValues(np.ones(size + 1, dtype=float)),
        "directions": [direction],
    }
    _assert_equivalent(
        _run_directions(_old_lookup, large_fixture),
        _run_directions(_indexed_lookup, large_fixture),
    )


def _mutated_lookup(mutant: str):
    source = inspect.getsource(_match_success_hazards)
    replacements = {
        "small-packing": ("K = 2**32", "K = 2**16"),
        "pop": ("popleft()", "pop()"),
        "no-isin": (
            "hit_indices = np.flatnonzero(np.isin(edge_keys, success_keys))",
            "hit_indices = np.arange(len(src))",
        ),
    }
    old, new = replacements[mutant]
    assert old in source
    namespace = vars(respiratory).copy()
    exec(compile(source.replace(old, new), "<mutated_lookup>", "exec"), namespace)
    return namespace["_match_success_hazards"]


@pytest.mark.parametrize("mutant", ["small-packing", "pop", "no-isin"])
def test_lookup_mutations_are_caught(
    mutant: str,
    lookup_fixture: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if mutant == "small-packing":
        bound = 2**32
        src = np.array([bound - 2], dtype=np.int64)
        trg = np.array([bound - 1], dtype=np.int64)
        beta = np.array([0.8], dtype=float)
        target_uids = trg.copy()
        source_uids = src.copy()
        rel_trans_raw: Any = {bound - 2: 0.5}
        rel_sus_raw: Any = {bound - 1: 0.25}
        with pytest.raises(AssertionError):
            _mutated_lookup(mutant)(
                src,
                trg,
                beta,
                rel_trans_raw,
                rel_sus_raw,
                target_uids,
                source_uids,
            )
        return

    if mutant == "pop":
        src = np.array([0, 0], dtype=np.int64)
        trg = np.array([1, 1], dtype=np.int64)
        beta = np.array([0.1, 0.9], dtype=float)
        target_uids = np.array([1, 1], dtype=np.int64)
        source_uids = np.array([0, 0], dtype=np.int64)
        expected = _match_success_hazards(
            src,
            trg,
            beta,
            lookup_fixture["rel_trans"].raw,
            lookup_fixture["rel_sus"].raw,
            target_uids,
            source_uids,
        )
        actual = _mutated_lookup(mutant)(
            src,
            trg,
            beta,
            lookup_fixture["rel_trans"].raw,
            lookup_fixture["rel_sus"].raw,
            target_uids,
            source_uids,
        )
        assert actual != expected
        return

    calls = 0
    original_isin = respiratory.np.isin

    def tracking_isin(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        return original_isin(*args, **kwargs)

    monkeypatch.setattr(respiratory.np, "isin", tracking_isin)
    size = 100_000
    src = np.arange(size, dtype=np.int64)
    trg = np.arange(1, size + 1, dtype=np.int64)
    real = _match_success_hazards(
        src,
        trg,
        np.ones(size, dtype=float),
        lookup_fixture["rel_trans"].raw,
        lookup_fixture["rel_sus"].raw,
        np.empty(0, dtype=np.int64),
        np.empty(0, dtype=np.int64),
    )
    assert real == []
    assert calls == 1
    calls = 0
    mutant_result = _mutated_lookup(mutant)(
        src,
        trg,
        np.ones(size, dtype=float),
        lookup_fixture["rel_trans"].raw,
        lookup_fixture["rel_sus"].raw,
        np.empty(0, dtype=np.int64),
        np.empty(0, dtype=np.int64),
    )
    assert mutant_result == real
    assert calls == 0


def _reference_attribution(
    candidates: list[dict[str, float | int | str]], seed: int, ti: int, target: int
) -> tuple[dict[str, float | int | str], dict[str, Any]]:
    ordered = sorted(
        candidates,
        key=lambda candidate: (
            candidate["route_id"],
            candidate["source"],
            candidate["network_index"],
        ),
    )
    total_hazard = sum(float(candidate["hazard"]) for candidate in ordered)
    draw = (
        int.from_bytes(respiratory._stable_key(seed, "attribution", ti, target)[:8], "big")
        / 2**64
        * total_hazard
    )
    cumulative = 0.0
    selected = ordered[-1]
    for candidate in ordered:
        cumulative += float(candidate["hazard"])
        if draw < cumulative:
            selected = candidate
            break
    routes = sorted({str(candidate["route_id"]) for candidate in ordered})
    evidence = {
        "successful_candidate_route_count": len(routes),
        "successful_candidate_routes": routes,
        "successful_candidate_edge_count": len(ordered),
        "successful_candidate_edge_routes": [candidate["route_id"] for candidate in ordered],
        "successful_candidate_hazards": [float(candidate["hazard"]) for candidate in ordered],
        "attributed_route_id": selected["route_id"],
    }
    return selected, evidence


def test_production_oracle_matches_reference_candidates_draw_and_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import starsim as ss  # type: ignore[import-untyped]

    class FixedNetwork(ss.Network):
        def step(self):
            return None

    networks = [
        FixedNetwork(
            name=route_id,
            p1=ss.uids(np.array([0], dtype=np.int64)),
            p2=ss.uids(np.array([1], dtype=np.int64)),
            beta=np.ones(1),
            label=route_id,
        )
        for route_id in ("route_b", "route_a")
    ]
    disease = RespiratorySEIRS(
        route_betas={"route_a": 0.8, "route_b": 0.4},
        initial_seed_count=0,
        waning_enabled=False,
    )
    sim = ss.Sim(
        n_agents=3,
        start="2025-01-06",
        stop="2025-01-08",
        dt=ss.days(1),
        rand_seed=123,
        networks=networks,
        diseases=disease,
        verbose=0,
        copy_inputs=False,
    )
    sim.init()
    disease.infected[0] = True
    disease.susceptible[1] = True
    disease.susceptible[2] = True

    candidates: list[dict[str, float | int | str]] = [
        {"route_id": "route_a", "network_index": 1, "source": 0, "hazard": float(np.float32(0.8))},
        {"route_id": "route_b", "network_index": 0, "source": 0, "hazard": float(np.float32(0.4))},
    ]
    expected_selected, expected_evidence = _reference_attribution(
        candidates, 123, int(disease.ti), 1
    )
    stable_key_calls: list[tuple[int, tuple[object, ...]]] = []
    original_stable_key = respiratory._stable_key

    def recording_stable_key(seed: int, *parts: object) -> bytes:
        stable_key_calls.append((seed, parts))
        return original_stable_key(seed, *parts)

    monkeypatch.setattr(respiratory, "_stable_key", recording_stable_key)
    cases, sources, _network_indices = disease._order_invariant_infect()

    actual_evidence = disease._last_attribution_evidence[1]
    assert tuple(int(case) for case in cases) == (1,)
    assert tuple(int(source) for source in sources) == (expected_selected["source"],)
    assert [
        {
            "route_id": route_id,
            "network_index": index,
            "source": 0,
            "hazard": hazard,
        }
        for route_id, index, hazard in zip(
            actual_evidence["successful_candidate_edge_routes"],
            (1, 0),
            actual_evidence["successful_candidate_hazards"],
            strict=True,
        )
    ] == sorted(
        candidates,
        key=lambda candidate: (
            candidate["route_id"],
            candidate["source"],
            candidate["network_index"],
        ),
    )
    assert actual_evidence == expected_evidence
    assert stable_key_calls == [(123, ("attribution", int(disease.ti), 1))]


@pytest.mark.parametrize("dtype", [np.float64, np.float32])
def test_randomized_float_hazards_are_bit_identical(lookup_fixture: dict, dtype) -> None:
    rng = np.random.RandomState(20260903)
    rel_trans = rng.random_sample(64).astype(dtype)
    rel_sus = rng.random_sample(64).astype(dtype)
    rel_trans[:4] = [
        np.nextafter(dtype(0), dtype(1)),
        dtype(0),
        dtype(1),
        np.finfo(dtype).tiny,
    ]
    rel_sus[:4] = [
        dtype(1),
        np.nextafter(dtype(0), dtype(1)),
        dtype(0),
        np.finfo(dtype).tiny,
    ]
    lookup_fixture["rel_trans"] = _RawValues(rel_trans)
    lookup_fixture["rel_sus"] = _RawValues(rel_sus)
    src = rng.randint(0, 64, size=4096, dtype=np.int64)
    trg = rng.randint(0, 64, size=4096, dtype=np.int64)
    src[:4] = np.arange(4)
    trg[:4] = np.arange(1, 5)
    beta = rng.random_sample(4096).astype(dtype)
    beta[:4] = [
        np.nextafter(dtype(0), dtype(1)),
        dtype(0),
        dtype(1),
        np.finfo(dtype).tiny,
    ]
    pair_counts: dict[tuple[int, int], int] = defaultdict(int)
    for source, target in zip(src, trg, strict=True):
        pair_counts[(int(source), int(target))] += 1
    required_pairs = {
        (int(source), int(target)) for source, target in zip(src[:4], trg[:4], strict=True)
    }
    successes: list[tuple[int, int]] = [
        (int(target), int(source)) for source, target in zip(src[:4], trg[:4], strict=True)
    ]
    for (source, target), count in pair_counts.items():
        reserved = int((source, target) in required_pairs)
        successes.extend([(target, source)] * int(rng.randint(0, count - reserved + 1)))
    rng.shuffle(successes)
    lookup_fixture["directions"] = [
        {
            "route_id": "randomized",
            "network_index": 7,
            "src": src,
            "trg": trg,
            "beta": beta,
            "targets": np.array([target for target, _source in successes], dtype=np.int64),
            "sources": np.array([source for _target, source in successes], dtype=np.int64),
        }
    ]
    _assert_equivalent(
        _run_directions(_old_lookup, lookup_fixture),
        _run_directions(_indexed_lookup, lookup_fixture),
    )
