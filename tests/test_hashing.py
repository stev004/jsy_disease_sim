from __future__ import annotations

import random
from itertools import product
from typing import Any

from jersey_outbreak.hashing import (
    canonical_json_bytes,
    iter_canonical_json_chunks,
    sha256_bytes,
    sha256_of_canonical_stream,
    stable_int,
    stable_int_suffix,
)


def _random_json_value(generator: random.Random, depth: int = 0) -> Any:
    if depth >= 3 or generator.random() < 0.35:
        return generator.choice(
            [
                None,
                True,
                False,
                generator.randint(-(2**40), 2**40),
                generator.choice((0.1, 1e-7, -0.0, -12.5, 3.141592653589793)),
                generator.choice(
                    (
                        "",
                        'quotes " and backslashes \\',
                        "control\n\t\r\x00",
                        "unicode—Jersey café 🚲 東京",
                    )
                ),
            ]
        )
    if generator.random() < 0.5:
        return [_random_json_value(generator, depth + 1) for _ in range(generator.randrange(5))]
    return {
        f"key-{index}-{generator.choice(('ascii', 'é', '"', '\\\\'))}": _random_json_value(
            generator, depth + 1
        )
        for index in range(generator.randrange(5))
    }


def test_canonical_json_stream_matches_encoder_for_random_json_values() -> None:
    edge_cases: list[Any] = [
        0.1,
        1e-7,
        -0.0,
        0,
        -(2**63),
        True,
        False,
        None,
        "",
        'quotes " and backslashes \\',
        "control\n\t\r\x00",
        "unicode—Jersey café 🚲 東京",
        {},
        [],
    ]
    generator = random.Random(20260905)
    values = edge_cases + [_random_json_value(generator) for _ in range(500)]
    for value in values:
        expected = canonical_json_bytes(value)
        streamed = b"".join(iter_canonical_json_chunks(value))
        assert streamed == expected
        assert sha256_of_canonical_stream(value) == sha256_bytes(expected)


def test_stable_int_pinned_digests() -> None:
    cases = [
        ((0, ()), 6912158355717386040),
        ((123, ("ascii", "key")), 2556498705402965926),
        ((-7, ("negative", -42, 0)), 386558410571936835),
        ((20260903, ("non-ASCII—Jersey café 🚲",)), 9906179252781507235),
        ((1, ("embedded|pipe", "value")), 9622697863196822082),
        ((99, (None, True, False)), 654262473249404730),
        ((42, ("2026-09-03",)), 11698466556155071195),
        ((2**31 - 1, (("mixed", -1, None, "é"),)), 4988465208837458588),
        ((-(2**63), (("tuple", (1, -2, "東京"), "tail"),)), 141093745993429750),
        ((2**32, ("same", "1|2", (3, False))), 7875473347658007522),
    ]
    for (seed, parts), expected in cases:
        assert stable_int(seed, *parts) == expected


def test_stable_int_suffix_matches_reference_over_generated_keyspace() -> None:
    values = [
        "ascii",
        "non-ASCII—Jersey café 🚲",
        "embedded|pipe",
        None,
        True,
        False,
        -42,
        -(2**63),
        0,
        2**31 - 1,
        "",
        ("tuple", -1, "東京"),
    ]
    seeds = (-7, 0, 101, 2**32)
    for index, parts in enumerate(product(values, repeat=3)):
        seed = seeds[index % len(seeds)]
        invariant = (seed, *parts[:2])
        suffix = (parts[2], values[(index * 7) % len(values)])
        prefix = "|".join(str(part) for part in invariant).encode("utf-8")
        assert stable_int_suffix(prefix, *suffix) == stable_int(
            invariant[0], *(invariant[1:] + suffix)
        )
