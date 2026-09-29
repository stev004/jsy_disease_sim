import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from jersey_outbreak.cli import app

ROOT = Path(__file__).resolve().parents[1]


def _build_structure(seed: int, output_dir: Path) -> dict[str, Any]:
    result = CliRunner().invoke(
        app,
        [
            "structure",
            "generate",
            "--mode",
            "ci",
            "--seed",
            str(seed),
            "--output-dir",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    artifact = json.loads(result.stdout)
    diagnostics_path = Path(artifact["artifact_directory"]) / "diagnostics.json"
    return json.loads(diagnostics_path.read_text(encoding="utf-8"))


def test_destination_reassignment_fallback_is_disclosed_only_when_used(tmp_path: Path) -> None:
    fallback = _build_structure(34, tmp_path / "seed-34")
    fallback_record = fallback["geography"]["destination_reassignment_fallback"]
    assert fallback_record["before_shares"]["St Helier"] == 965 / 1438
    assert abs(fallback_record["after_shares"]["St Helier"] - 0.66) <= 0.01
    st_helier_check = next(
        check for check in fallback["checks"] if check["name"] == "destination_share_St Helier"
    )
    assert st_helier_check["status"] == "passed"
    assert (
        abs(st_helier_check["actual"] - st_helier_check["expected"]) <= st_helier_check["tolerance"]
    )

    base_passing = _build_structure(123, tmp_path / "seed-123")
    assert "destination_reassignment_fallback" not in base_passing["geography"]
