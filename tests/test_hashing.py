from __future__ import annotations

from itertools import product

from jersey_outbreak.hashing import stable_int, stable_int_suffix


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
