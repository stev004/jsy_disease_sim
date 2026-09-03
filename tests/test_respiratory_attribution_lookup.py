from __future__ import annotations

from collections import defaultdict
from struct import pack

import numpy as np
import pytest


class _RawValues:
    def __init__(self, values: np.ndarray) -> None:
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
    indices_by_pair: dict[tuple[int, int], list[int]] = defaultdict(list)
    cursors_by_pair: dict[tuple[int, int], int] = defaultdict(int)
    for i, (source, target) in enumerate(zip(src, trg, strict=True)):
        indices_by_pair[(int(source), int(target))].append(i)
    for target, source in zip(target_uids, source_uids, strict=True):
        pair = (int(source), int(target))
        i = indices_by_pair[pair][cursors_by_pair[pair]]
        cursors_by_pair[pair] += 1
        probability = float(rel_trans.raw[pair[0]] * rel_sus.raw[pair[1]] * beta_per_dt[i])
        candidates_by_target[pair[1]].append(
            {
                "route_id": route_id,
                "network_index": network_index,
                "source": pair[0],
                "hazard": max(0.0, min(1.0, probability)),
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
