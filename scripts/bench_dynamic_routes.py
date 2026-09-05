"""Benchmark and fingerprint every configured date-sensitive route."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import tempfile
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

import numpy as np

from jersey_outbreak import hashing
from jersey_outbreak.cli import _build_m4_for_m6
from jersey_outbreak.starsim_adapter import _edge_arrays, _load_starsim, agent_uid_mapping

TERM_BOUNDARY_START = date(2025, 2, 10)
TERM_BOUNDARY_END = date(2025, 3, 2)
Mode = Literal["ci", "full"]


def _positive_days(value: str) -> int:
    days = int(value)
    if days < 1:
        raise argparse.ArgumentTypeError("days must be at least 1")
    return days


def _fingerprint(edges: Sequence[dict[str, Any]]) -> str:
    """Hash every edge field in its existing order using the benchmark contract."""

    serialized = "".join(repr(tuple(sorted(edge.items()))) for edge in edges)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _array_fingerprint(arrays: Mapping[str, Any]) -> str:
    """Hash adapter arrays, including field order, dtype, shape, order, and bytes."""

    digest = hashlib.sha256()
    for name in ("p1", "p2", "beta", "dur"):
        array = arrays[name]
        if array.flags.c_contiguous:
            array_order = "C"
        elif array.flags.f_contiguous:
            array_order = "F"
        else:
            array_order = "other"
        header = f"{name}\0{str(array.dtype)}\0{array.shape!r}\0{array_order}\0".encode()
        digest.update(header)
        digest.update(array.tobytes())
    return digest.hexdigest()


def _git_commit(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _dates_for_window(window: str, start: date, days: int) -> list[date]:
    if window == "term-boundary":
        return [
            TERM_BOUNDARY_START + timedelta(days=index)
            for index in range((TERM_BOUNDARY_END - TERM_BOUNDARY_START).days + 1)
        ]
    return [start + timedelta(days=index) for index in range(days)]


def _adapter_array_fingerprint(
    starsim: Any,
    uid_by_agent_id: Mapping[str, int],
    snapshot: Any,
) -> str:
    arrays = _edge_arrays(starsim, snapshot, uid_by_agent_id)
    # This is the exact assignment made by JOSDynamicNetworkMixin._replace_edges.
    arrays["dur"] = np.ones(len(snapshot), dtype=float)
    return _array_fingerprint(arrays)


def _timed_snapshots(
    generated: Any,
    route_ids: Sequence[str],
    dates: Sequence[date],
    *,
    date_major: bool,
    starsim: Any,
    uid_by_agent_id: Mapping[str, int],
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, float]]:
    timed: dict[tuple[str, str], dict[str, Any]] = {}
    route_wall = {route_id: 0.0 for route_id in route_ids}
    generated._snapshot_cache.clear()
    accesses = (
        ((route_id, snapshot_date) for snapshot_date in dates for route_id in route_ids)
        if date_major
        else ((route_id, snapshot_date) for route_id in route_ids for snapshot_date in dates)
    )
    for route_id, snapshot_date in accesses:
        if not date_major:
            generated._snapshot_cache.clear()
        started = time.perf_counter()
        snapshot = generated.route_snapshot(route_id, snapshot_date)
        wall_s = time.perf_counter() - started
        array_fingerprint = _adapter_array_fingerprint(starsim, uid_by_agent_id, snapshot)
        key = (route_id, snapshot_date.isoformat())
        timed[key] = {
            "date": snapshot_date.isoformat(),
            "wall_s": wall_s,
            "n_edges": len(snapshot.edges),
            "fingerprint": _fingerprint(snapshot.edges),
            "array_fingerprint": array_fingerprint,
        }
        route_wall[route_id] += wall_s
    return timed, route_wall


def _count_snapshots(
    generated: Any,
    route_ids: Sequence[str],
    dates: Sequence[date],
    *,
    date_major: bool,
) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    generated._snapshot_cache.clear()
    counter = [0]
    previous_counter = hashing.STABLE_INT_COUNTER
    hashing.STABLE_INT_COUNTER = counter
    try:
        accesses = (
            ((route_id, snapshot_date) for snapshot_date in dates for route_id in route_ids)
            if date_major
            else ((route_id, snapshot_date) for route_id in route_ids for snapshot_date in dates)
        )
        for route_id, snapshot_date in accesses:
            if not date_major:
                generated._snapshot_cache.clear()
            before = counter[0]
            generated.route_snapshot(route_id, snapshot_date)
            counts[(route_id, snapshot_date.isoformat())] = counter[0] - before
    finally:
        hashing.STABLE_INT_COUNTER = previous_counter
    return counts


def _measure(
    generated: Any, route_ids: Sequence[str], dates: Sequence[date], *, date_major: bool
) -> tuple[dict[str, Any], float, int, int]:
    starsim = _load_starsim()
    uid_by_agent_id = agent_uid_mapping(generated)
    timed, route_wall = _timed_snapshots(
        generated,
        route_ids,
        dates,
        date_major=date_major,
        starsim=starsim,
        uid_by_agent_id=uid_by_agent_id,
    )
    counts = _count_snapshots(generated, route_ids, dates, date_major=date_major)

    per_route: dict[str, Any] = {}
    total_stable_int_calls = 0
    for route_id in route_ids:
        per_day: list[dict[str, Any]] = []
        route_stable_int_calls = 0
        for snapshot_date in dates:
            key = (route_id, snapshot_date.isoformat())
            day = timed[key]
            stable_int_calls = counts[key]
            route_stable_int_calls += stable_int_calls
            per_day.append({**day, "stable_int_calls": stable_int_calls})
        per_route[route_id] = {
            "total_wall_s": route_wall[route_id],
            "total_stable_int_calls": route_stable_int_calls,
            "per_day": per_day,
        }
        total_stable_int_calls += route_stable_int_calls

    return (
        per_route,
        sum(route_wall.values()),
        total_stable_int_calls,
        len(generated._snapshot_cache),
    )


def _run_one_window(
    *,
    generated: Any,
    root: Path,
    mode: Mode,
    seed: int,
    window: str,
    start: date,
    days: int,
    date_major: bool,
) -> dict[str, Any]:
    dates = _dates_for_window(window, start, days)
    route_ids = sorted(generated.route_specs)
    per_route, total_wall, total_stable_int_calls, cache_length = _measure(
        generated, route_ids, dates, date_major=date_major
    )
    return {
        "meta": {
            "route_ids": route_ids,
            "mode": mode,
            "seed": seed,
            "window": window,
            "start": dates[0].isoformat(),
            "days": len(dates),
            "dates": [snapshot_date.isoformat() for snapshot_date in dates],
            "date_major": date_major,
            "git_commit": _git_commit(root),
            "python": platform.python_version(),
            "utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
        "per_route": per_route,
        "totals": {
            "wall_s": total_wall,
            "stable_int_calls": total_stable_int_calls,
            "final_snapshot_cache_length": cache_length,
        },
    }


def _run_benchmark(
    *,
    root: Path,
    mode: Mode,
    seed: int,
    start: date,
    days: int,
    window: str,
    date_major: bool,
    out: Path,
    dest: Path | None,
) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)

    if dest is None:
        with tempfile.TemporaryDirectory(prefix="jos-dynamic-routes-") as temporary_directory:
            return _run_benchmark_with_dest(
                root,
                mode,
                seed,
                start,
                days,
                window,
                date_major,
                out,
                Path(temporary_directory),
            )
    dest.mkdir(parents=True, exist_ok=True)
    return _run_benchmark_with_dest(root, mode, seed, start, days, window, date_major, out, dest)


def _run_benchmark_with_dest(
    root: Path,
    mode: Mode,
    seed: int,
    start: date,
    days: int,
    window: str,
    date_major: bool,
    out: Path,
    dest: Path,
) -> int:
    generated = _build_m4_for_m6(root, mode, seed, dest)
    windows = ("standard", "term-boundary") if window == "both" else (window,)
    results = {
        selected_window: _run_one_window(
            generated=generated,
            root=root,
            mode=mode,
            seed=seed,
            window=selected_window,
            start=start,
            days=days,
            date_major=date_major,
        )
        for selected_window in windows
    }
    result: dict[str, Any]
    if window == "both":
        result = {"schema_version": 2, "windows": results}
    else:
        result = {"schema_version": 2, **results[window]}
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _snapshot_index(result: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (route_id, day["date"]): day
        for route_id, route in result.get("per_route", {}).items()
        for day in route.get("per_day", [])
    }


def _window_results(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    windows = result.get("windows")
    if isinstance(windows, dict):
        return windows
    return {str(result.get("meta", {}).get("window", "standard")): result}


def _compare_window(first: dict[str, Any], second: dict[str, Any], label: str) -> list[str]:
    mismatches: list[str] = []
    first_meta = first.get("meta", {})
    second_meta = second.get("meta", {})
    first_route_ids = first_meta.get("route_ids")
    second_route_ids = second_meta.get("route_ids")
    if first_route_ids != second_route_ids:
        mismatches.append(
            f"{label}: route_ids differ: A={first_route_ids!r} B={second_route_ids!r}"
        )
        return mismatches
    if not isinstance(first_route_ids, list):
        mismatches.append(f"{label}: missing or invalid declared route_ids")
        return mismatches
    first_dates = first_meta.get("dates")
    second_dates = second_meta.get("dates")
    if first_dates != second_dates:
        mismatches.append(f"{label}: dates differ: A={first_dates!r} B={second_dates!r}")
    if not isinstance(first_dates, list):
        mismatches.append(f"{label}: missing or invalid declared dates")

    first_routes = first.get("per_route", {})
    second_routes = second.get("per_route", {})
    if not isinstance(first_routes, dict) or not isinstance(second_routes, dict):
        mismatches.append(f"{label}: missing or invalid per_route data")
        return mismatches
    for side, route_data in (("A", first_routes), ("B", second_routes)):
        missing = sorted(set(first_route_ids) - set(route_data))
        if missing:
            mismatches.append(f"{label}: {side} missing declared routes: {missing}")
        extra = sorted(set(route_data) - set(first_route_ids))
        if extra:
            mismatches.append(f"{label}: {side} has undeclared routes: {extra}")

    first_days = _snapshot_index(first)
    second_days = _snapshot_index(second)
    for route_id, snapshot_date in sorted(set(first_days) | set(second_days)):
        left = first_days.get((route_id, snapshot_date))
        right = second_days.get((route_id, snapshot_date))
        if left is None or right is None:
            present = "A" if left is not None else "B"
            mismatches.append(f"{label}: {route_id} {snapshot_date}: missing from {present}")
            continue
        for field in ("n_edges", "fingerprint", "array_fingerprint"):
            if left.get(field) != right.get(field):
                mismatches.append(
                    f"{label}: {route_id} {snapshot_date} {field}: "
                    f"A={left.get(field)!r} B={right.get(field)!r}"
                )
    return mismatches


def _compare(first_path: Path, second_path: Path) -> int:
    first = json.loads(first_path.read_text(encoding="utf-8"))
    second = json.loads(second_path.read_text(encoding="utf-8"))
    first_windows = _window_results(first)
    second_windows = _window_results(second)
    mismatches: list[str] = []
    if set(first_windows) != set(second_windows):
        mismatches.append(
            f"windows differ: A={sorted(first_windows)!r} B={sorted(second_windows)!r}"
        )
    for window in sorted(set(first_windows) | set(second_windows)):
        if window not in first_windows or window not in second_windows:
            continue
        mismatches.extend(_compare_window(first_windows[window], second_windows[window], window))

    if mismatches:
        print("mismatches:")
        print("\n".join(mismatches))
        return 2

    print("fingerprints identical")
    for window in sorted(first_windows):
        first_result = first_windows[window]
        second_result = second_windows[window]
        for route_id in first_result["meta"]["route_ids"]:
            first_wall = first_result["per_route"][route_id]["total_wall_s"]
            second_wall = second_result["per_route"][route_id]["total_wall_s"]
            ratio = first_wall / second_wall if second_wall else float("inf")
            print(f"{window} {route_id}: A_wall/B_wall={ratio:.6f}")
        first_wall = first_result["totals"]["wall_s"]
        second_wall = second_result["totals"]["wall_s"]
        ratio = first_wall / second_wall if second_wall else float("inf")
        print(f"{window} total: A_wall/B_wall={ratio:.6f}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("ci", "full"), default="ci")
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--start", type=date.fromisoformat, default=date(2025, 1, 6))
    parser.add_argument("--days", type=_positive_days, default=30)
    parser.add_argument(
        "--window",
        choices=("standard", "term-boundary", "both"),
        default="standard",
        help="date window; 'both' writes standard and term-boundary results together",
    )
    parser.add_argument(
        "--date-major", action="store_true", help="use production date-major access"
    )
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
        window=args.window,
        date_major=args.date_major,
        out=out,
        dest=args.dest,
    )


if __name__ == "__main__":
    raise SystemExit(main())
