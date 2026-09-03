import importlib.util
import json
from datetime import date
from pathlib import Path

from jersey_outbreak import hashing

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bench_dynamic_routes.py"
FIXTURE = ROOT / "benchmarks" / "ci-fingerprint-fixture.json"
SPEC = importlib.util.spec_from_file_location("bench_dynamic_routes", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
bench_dynamic_routes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bench_dynamic_routes)


def _run(output: Path, destination: Path) -> dict:
    assert (
        bench_dynamic_routes.main(
            [
                "--mode",
                "ci",
                "--seed",
                "101",
                "--start",
                "2025-01-06",
                "--days",
                "2",
                "--out",
                str(output),
                "--dest",
                str(destination),
            ]
        )
        == 0
    )
    return json.loads(output.read_text(encoding="utf-8"))


def _fingerprints(result: dict) -> tuple:
    return tuple(
        (
            route_id,
            tuple(
                (
                    day["date"],
                    day["n_edges"],
                    day["fingerprint"],
                    day["array_fingerprint"],
                )
                for day in route["per_day"]
            ),
        )
        for route_id, route in sorted(result["per_route"].items())
    )


def test_ci_runs_have_identical_route_fingerprints_and_compare(tmp_path, capsys) -> None:
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first = _run(first_path, tmp_path / "first-m4")
    second = _run(second_path, tmp_path / "second-m4")

    assert first["meta"]["route_ids"] == sorted(first["per_route"])
    assert _fingerprints(first) == _fingerprints(second)
    assert all(
        "array_fingerprint" in day
        for route in first["per_route"].values()
        for day in route["per_day"]
    )
    assert bench_dynamic_routes.main(["--compare", str(first_path), str(second_path)]) == 0
    assert "fingerprints identical" in capsys.readouterr().out


def test_compare_rejects_tampered_fingerprint(tmp_path, capsys) -> None:
    source_path = tmp_path / "source.json"
    tampered_path = tmp_path / "tampered.json"
    _run(source_path, tmp_path / "m4")
    tampered = json.loads(source_path.read_text(encoding="utf-8"))
    route_id = sorted(tampered["per_route"])[0]
    tampered["per_route"][route_id]["per_day"][0]["fingerprint"] = "0" * 64
    tampered_path.write_text(json.dumps(tampered), encoding="utf-8")

    assert bench_dynamic_routes.main(["--compare", str(source_path), str(tampered_path)]) == 2
    output = capsys.readouterr().out
    assert "mismatches:" in output
    assert "fingerprint" in output


def test_compare_rejects_declared_route_missing_from_one_file_and_both(tmp_path) -> None:
    source_path = tmp_path / "source.json"
    one_missing_path = tmp_path / "one-missing.json"
    both_missing_path = tmp_path / "both-missing.json"
    _run(source_path, tmp_path / "m4")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    route_id = source["meta"]["route_ids"][0]

    one_missing = json.loads(source_path.read_text(encoding="utf-8"))
    del one_missing["per_route"][route_id]
    one_missing_path.write_text(json.dumps(one_missing), encoding="utf-8")
    assert bench_dynamic_routes.main(["--compare", str(source_path), str(one_missing_path)]) == 2

    both_missing = json.loads(source_path.read_text(encoding="utf-8"))
    del both_missing["per_route"][route_id]
    source_without_route = json.loads(source_path.read_text(encoding="utf-8"))
    del source_without_route["per_route"][route_id]
    both_missing_path.write_text(json.dumps(both_missing), encoding="utf-8")
    source_path.write_text(json.dumps(source_without_route), encoding="utf-8")
    assert bench_dynamic_routes.main(["--compare", str(source_path), str(both_missing_path)]) == 2


def test_ci_fixture_round_trip(tmp_path) -> None:
    generated = _run(tmp_path / "generated.json", tmp_path / "m4")
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["meta"]["route_ids"] == generated["meta"]["route_ids"]
    assert fixture["meta"]["dates"] == generated["meta"]["dates"]
    assert _fingerprints(fixture) == _fingerprints(generated)


def test_stable_int_counter_flag() -> None:
    assert hashing.STABLE_INT_COUNTER is None
    hashing.stable_int(101, "counter-disabled")
    counter = [0]
    hashing.STABLE_INT_COUNTER = counter
    try:
        hashing.stable_int(101, "counter-enabled")
        hashing.stable_int(101, "counter-enabled-again")
    finally:
        hashing.STABLE_INT_COUNTER = None
    assert counter == [2]


def test_term_boundary_window_is_inclusive() -> None:
    dates = bench_dynamic_routes._dates_for_window("term-boundary", date(2025, 1, 6), 1)
    assert dates[0].isoformat() == "2025-02-10"
    assert dates[-1].isoformat() == "2025-03-02"
    assert len(dates) == 21
