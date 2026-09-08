from __future__ import annotations

import random

from jersey_outbreak import hashing
from jersey_outbreak.hashing import stable_int_prefixed, stable_int_suffix


def test_prefixed_suffix_matches_string_suffix_for_10000_random_keys() -> None:
    generator = random.Random(20260908)
    for _ in range(10_000):
        prefix = bytes(generator.randrange(256) for _ in range(generator.randrange(1, 64)))
        agent_id = f"agent-{generator.randrange(1_000_000):07d}"
        contact_index = generator.randrange(64)

        assert isinstance(agent_id, str)
        assert isinstance(contact_index, int)
        assert agent_id.encode("utf-8") == str(agent_id).encode("utf-8")
        assert f"{agent_id}|{contact_index}".encode() == (
            "|".join(str(part) for part in (agent_id, contact_index)).encode("utf-8")
        )
        assert stable_int_prefixed(
            prefix, f"{agent_id}|{contact_index}".encode()
        ) == stable_int_suffix(prefix, agent_id, contact_index)
        assert stable_int_prefixed(prefix, agent_id.encode("utf-8")) == stable_int_suffix(
            prefix, agent_id
        )


def test_prefixed_and_string_suffix_each_increment_counter_once() -> None:
    prefix = b"20260908|community-age-target|community_indoor|regular"
    suffix = b"agent-0000123|7"
    counter = [0]
    previous_counter = hashing.STABLE_INT_COUNTER
    hashing.STABLE_INT_COUNTER = counter
    try:
        stable_int_prefixed(prefix, suffix)
        assert counter == [1]
        stable_int_suffix(prefix, "agent-0000123", 7)
        assert counter == [2]
        stable_int_prefixed(prefix, b"agent-0000123")
        assert counter == [3]
        stable_int_suffix(prefix, "agent-0000123")
        assert counter == [4]
    finally:
        hashing.STABLE_INT_COUNTER = previous_counter
