"""Benchmark and fingerprint the date-sensitive M4 route builders."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import tempfile
import time
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from jersey_outbreak import network_generator
from jersey_outbreak.cli import _build_m4_for_m6


def _positive_days(value: str) -> int:
    days = int(value)
    if days < 1:
        raise argparse.ArgumentTypeError("days must be at least 1")
    return days


def _fingerprint(edges: Sequence[dict[str, Any]]) -> str:
    """Hash every edge field in its existing order using the benchmark contract."""

    serialized = "".join(repr(tuple(sorted(edge.items()))) for edge in edges)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _git_commit(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _measure(
    generated: Any, route_ids: Sequence[str], dates: Sequence[date]
) -> tuple[dict[str, Any], float, int]:
    per_route: dict[str, Any] = {}
    total_wall = 0.0
    total_stable_int_calls = 0
    original_stable_int = network_generator._stable_int

    for route_id in route_ids:
        per_day: list[dict[str, Any]] = []
        route_wall = 0.0
        route_stable_int_calls = 0
        for snapshot_date in dates:
            generated._snapshot_cache.clear()
            stable_int_calls = 0

            def counting_stable_int(seed: int, *parts: object) -> int:
                nonlocal stable_int_calls
                stable_int_calls += 1
                return original_stable_int(seed, *parts)

            network_generator._stable_int = counting_stable_int
            try:
                started = time.perf_counter()
                snapshot = generated.route_snapshot(route_id, snapshot_date)
                wall_s = time.perf_counter() - started
            finally:
                network_generator._stable_int = original_stable_int

            n_edges = len(snapshot.edges)
            per_day.append(
                {
                    "date": snapshot_date.isoformat(),
                    "wall_s": wall_s,
                    "stable_int_calls": stable_int_calls,
                    "n_edges": n_edges,
                    "fingerprint": _fingerprint(snapshot.edges),
                }
            )
            route_wall += wall_s
            route_stable_int_calls += stable_int_calls

        per_route[route_id] = {
            "total_wall_s": route_wall,
            "total_stable_int_calls": route_stable_int_calls,
            "per_day": per_day,
        }
        total_wall += route_wall
        total_stable_int_calls += route_stable_int_calls

    return per_route, total_wall, total_stable_int_calls


def _run_benchmark(
    *, root: Path, mode: str, seed: int, start: date, days: int, out: Path, dest: Path | None
) -> int:
    dates = [start + timedelta(days=index) for index in range(days)]
    out.parent.mkdir(parents=True, exist_ok=True)

    if dest is None:
        with tempfile.TemporaryDirectory(prefix="jos-dynamic-routes-") as temporary_directory:
            return _run_benchmark_with_dest(
                root, mode, seed, start, days, dates, out, Path(temporary_directory)
            )
    dest.mkdir(parents=True, exist_ok=True)
    return _run_benchmark_with_dest(root, mode, seed, start, days, dates, out, dest)


def _run_benchmark_with_dest(
    root: Path,
    mode: str,
    seed: int,
    start: date,
    days: int,
    dates: Sequence[date],
    out: Path,
    dest: Path,
) -> int:
    generated = _build_m4_for_m6(root, mode, seed, dest)
    route_ids = sorted(generated._dynamic_builders)
    per_route, total_wall, total_stable_int_calls = _measure(generated, route_ids, dates)
    result = {
        "meta": {
            "mode": mode,
            "seed": seed,
            "start": start.isoformat(),
            "days": days,
            "git_commit": _git_commit(root),
            "python": platform.python_version(),
            "utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
        "per_route": per_route,
        "totals": {"wall_s": total_wall, "stable_int_calls": total_stable_int_calls},
    }
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _snapshot_index(result: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (route_id, day["date"]): day
        for route_id, route in result["per_route"].items()
        for day in route["per_day"]
    }


def _compare(first_path: Path, second_path: Path) -> int:
    first = json.loads(first_path.read_text(encoding="utf-8"))
    second = json.loads(second_path.read_text(encoding="utf-8"))
    first_days = _snapshot_index(first)
    second_days = _snapshot_index(second)
    mismatches: list[str] = []
    for route_id, snapshot_date in sorted(set(first_days) | set(second_days)):
        left = first_days.get((route_id, snapshot_date))
        right = second_days.get((route_id, snapshot_date))
        if left is None or right is None:
            present = "A" if left is not None else "B"
            mismatches.append(f"{route_id} {snapshot_date}: missing from {present}")
            continue
        for field in ("n_edges", "fingerprint"):
            if left[field] != right[field]:
                mismatches.append(
                    f"{route_id} {snapshot_date} {field}: A={left[field]!r} B={right[field]!r}"
                )

    if mismatches:
        print("mismatches:")
        print("\n".join(mismatches))
        return 2

    print("fingerprints identical")
    for route_id in sorted(set(first["per_route"]) | set(second["per_route"])):
        first_wall = first["per_route"].get(route_id, {}).get("total_wall_s", 0.0)
        second_wall = second["per_route"].get(route_id, {}).get("total_wall_s", 0.0)
        ratio = first_wall / second_wall if second_wall else float("inf")
        print(f"{route_id}: A_wall/B_wall={ratio:.6f}")
    first_wall = first["totals"]["wall_s"]
    second_wall = second["totals"]["wall_s"]
    ratio = first_wall / second_wall if second_wall else float("inf")
    print(f"total: A_wall/B_wall={ratio:.6f}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("ci", "full"), default="ci")
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--start", type=date.fromisoformat, default=date(2025, 1, 6))
    parser.add_argument("--days", type=_positive_days, default=30)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--dest", type=Path, help="M4 scratch directory")
    parser.add_argument("--compare", nargs=2, type=Path, metavar=("A", "B"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.compare is not None:
        return _compare(*args.compare)
    out = args.out or Path(f"benchmarks/routes-{args.mode}-seed{args.seed}-{args.days}d.json")
    root = Path(__file__).resolve().parents[1]
    return _run_benchmark(
        root=root,
        mode=args.mode,
        seed=args.seed,
        start=args.start,
        days=args.days,
        out=out,
        dest=args.dest,
    )


if __name__ == "__main__":
    raise SystemExit(main())
