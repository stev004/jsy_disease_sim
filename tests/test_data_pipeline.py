import csv
from pathlib import Path

from jersey_outbreak.data_pipeline import build_canonical
from jersey_outbreak.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_build_reconciles_controls_and_is_repeatable(tmp_path: Path) -> None:
    output_dir = tmp_path / "processed"
    first = build_canonical(ROOT, output_dir)
    first_bytes = {path.name: path.read_bytes() for path in output_dir.iterdir() if path.is_file()}
    second = build_canonical(ROOT, output_dir)
    second_bytes = {path.name: path.read_bytes() for path in output_dir.iterdir() if path.is_file()}

    assert first["build_status"] == second["build_status"] == "passed"
    assert first_bytes == second_bytes
    assert len(first["tables"]) == 14
    assert {check["status"] for check in first["checks"]} >= {"passed", "warning"}

    with (output_dir / "household_types.csv").open(newline="", encoding="utf-8") as handle:
        household_rows = list(csv.DictReader(handle))
    assert sum(int(row["households"]) for row in household_rows) == 44583

    with (output_dir / "workplace_sizes.csv").open(newline="", encoding="utf-8") as handle:
        workplace_rows = list(csv.DictReader(handle))
    censored = [row for row in workplace_rows if row["censoring"] == "positive_less_than"]
    assert censored
    assert all(row["count"] == "" and row["upper_bound"] == "5" for row in censored)

    with (output_dir / "commute_modes.csv").open(newline="", encoding="utf-8") as handle:
        commute_rows = list(csv.DictReader(handle))
    suppressed = [row for row in commute_rows if row["censoring"] == "positive_less_than"]
    assert suppressed
    assert all(row["workers"] == "" and row["upper_bound"] == "10" for row in suppressed)
    assert sha256_file(output_dir / "quality_report.json")
