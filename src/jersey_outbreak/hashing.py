"""Stable hashing helpers for configs and generated artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pydantic import BaseModel

STABLE_INT_COUNTER: list[int] | None = None
_STREAMED_CONTAINER_KEYS = frozenset(("memberships", "snapshots", "structural_edges"))


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON-compatible data with stable ordering and separators."""

    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def iter_canonical_json_chunks(value: Any, *, frame_depth: int = 0) -> Iterator[bytes]:
    """Yield the canonical JSON encoding without materialising large containers.

    The top-level M4 containers named in _STREAMED_CONTAINER_KEYS are framed
    recursively.  Their leaf records, and all other values, use
    canonical_json_bytes directly.  Iterator values are encoded as one-shot JSON
    arrays so callers can provide lazy array contents.  frame_depth is the
    recursion state for those selected containers.
    """

    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, dict):
        assert all(isinstance(key, str) for key in value)
        yield b"{"
        for index, key in enumerate(sorted(value)):
            if index:
                yield b","
            yield canonical_json_bytes(key)
            yield b":"
            child = value[key]
            should_frame = isinstance(child, Iterator) or (
                frame_depth == 0 and key in _STREAMED_CONTAINER_KEYS
            )
            if frame_depth > 0 and isinstance(child, (dict, list, tuple)):
                should_frame = True
            if frame_depth > 0 and key == "edges":
                should_frame = True
            if should_frame:
                yield from iter_canonical_json_chunks(child, frame_depth=frame_depth + 1)
            else:
                yield canonical_json_bytes(child)
        yield b"}"
    elif isinstance(value, (list, tuple)) or isinstance(value, Iterator):
        yield b"["
        for index, item in enumerate(value):
            if index:
                yield b","
            if isinstance(item, Iterator) or (isinstance(item, dict) and "edges" in item):
                yield from iter_canonical_json_chunks(item, frame_depth=frame_depth + 1)
            else:
                yield canonical_json_bytes(item)
        yield b"]"
    else:
        yield canonical_json_bytes(value)


def sha256_of_canonical_stream(value: Any) -> str:
    """Hash the canonical JSON encoding while consuming it incrementally."""

    digest = hashlib.sha256()
    for chunk in iter_canonical_json_chunks(value):
        digest.update(chunk)
    return digest.hexdigest()


def stable_int(seed: int, *parts: object) -> int:
    """Return the frozen integer derived from a seed and stable key parts."""

    if STABLE_INT_COUNTER is not None:
        STABLE_INT_COUNTER[0] += 1
    payload = "|".join(str(part) for part in (seed, *parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def stable_int_suffix(prefix_bytes: bytes, *suffix_parts: object) -> int:
    """Return ``stable_int`` for a key whose invariant prefix is already encoded."""

    if STABLE_INT_COUNTER is not None:
        STABLE_INT_COUNTER[0] += 1
    suffix = "|".join(str(part) for part in suffix_parts).encode("utf-8")
    payload = prefix_bytes + b"|" + suffix
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
