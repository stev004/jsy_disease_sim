import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bench_dynamic_routes.py"
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


def test_ci_runs_have_identical_route_fingerprints_and_compare(tmp_path, capsys) -> None:
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first = _run(first_path, tmp_path / "first-m4")
    second = _run(second_path, tmp_path / "second-m4")

    first_fingerprints = {
        (route_id, day["date"]): (day["n_edges"], day["fingerprint"])
        for route_id, route in first["per_route"].items()
        for day in route["per_day"]
    }
    second_fingerprints = {
        (route_id, day["date"]): (day["n_edges"], day["fingerprint"])
        for route_id, route in second["per_route"].items()
        for day in route["per_day"]
    }
    assert first_fingerprints == second_fingerprints
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
